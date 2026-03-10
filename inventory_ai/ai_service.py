"""
ai_service.py - Lilian AI Engine
==================================
This is the core intelligence layer of Lilian, the AI assistant for the
POL Tracking inventory system.

HOW IT WORKS (Pipeline):
─────────────────────────
1. User sends a natural language query (e.g., "What products expire in June?")
2. IntentClassifier detects the INTENT (e.g., "expiry_by_date")
3. EntityExtractor pulls out DATE entities & keywords from the query
4. QueryBuilder constructs a Django ORM query based on intent + entities
5. ResponseGenerator formats the database results into a human-readable answer

This approach does NOT require an external LLM API — it uses rule-based NLP.
If you want to upgrade to OpenAI/Claude API later, you only replace this file.
"""

import re
from datetime import date, datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Count
from .models import InventoryItem


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SECTION 1: Intent Classification
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class IntentClassifier:
    """
    Classifies user queries into predefined intent categories.
    Uses keyword matching with priority ordering.

    Supported Intents:
    ─────────────────
    - expired_products      → "What products are expired?"
    - near_expiry           → "Which items are expiring soon?"
    - healthy_products      → "Show me healthy products"
    - expiry_on_date        → "What expires on 2025-06-01?"
    - expiry_before_date    → "What expires before March?"
    - expiry_after_date     → "What expires after July 2025?"
    - expiry_between_dates  → "Products expiring between Jan and June"
    - product_search        → "Tell me about High-Grade Diesel"
    - inventory_summary     → "Give me an overview of inventory"
    - status_count          → "How many expired products?"
    - brand_query           → "What brands do we have?"
    - company_query         → "Products from Global Fuels Ltd"
    - help                  → "What can you do?"
    """

    # Each intent maps to a list of trigger phrases (checked in order)
    INTENT_PATTERNS = {
        'expiry_between_dates': [
            r'between.*and', r'from.*to', r'range',
        ],
        'expiry_before_date': [
            r'expire[sd]?\s+before', r'expir(?:y|ing|es?)\s+before',
            r'before\s+\w+\s*\d*', r'earlier\s+than',
        ],
        'expiry_after_date': [
            r'expire[sd]?\s+after', r'expir(?:y|ing|es?)\s+after',
            r'after\s+\w+\s*\d*', r'later\s+than',
        ],
        'expiry_on_date': [
            r'expire[sd]?\s+on', r'expir(?:y|ing|es?)\s+on',
            r'expire[sd]?\s+in\s+\w+', r'expir(?:y|ing)\s+in\s+\w+',
            r'expire[sd]?\s+(?:on\s+)?(?:a\s+)?specific',
            r'on\s+\d{4}-\d{2}-\d{2}',
        ],
        'expired_products': [
            r'already\s+expired', r'are\s+expired', r'expired\s+product',
            r'which.*expired', r'list.*expired', r'show.*expired',
            r'what.*expired', r'\bexpired\b',
        ],
        'near_expiry': [
            r'near\s+expir', r'expiring\s+soon', r'about\s+to\s+expire',
            r'close\s+to\s+expir', r'almost\s+expired', r'soon\s+expir',
            r'within.*days', r'next.*days', r'upcoming.*expir',
        ],
        'healthy_products': [
            r'healthy', r'good\s+condition', r'not\s+expired',
            r'valid\s+products', r'active\s+products', r'safe\s+products',
        ],
        'status_count': [
            r'how\s+many', r'count', r'total\s+number', r'number\s+of',
        ],
        'product_search': [
            r'tell\s+me\s+about', r'information\s+(?:about|on)',
            r'details?\s+(?:of|about|for)', r'search\s+for',
            r'find\s+product', r'look\s+up',
        ],
        'brand_query': [
            r'what\s+brands?', r'list\s+brands?', r'which\s+brands?',
            r'all\s+brands?', r'available\s+brands?',
        ],
        'company_query': [
            r'from\s+company', r'supplied\s+by', r'products?\s+from',
            r'company', r'supplier', r'manufacturer',
        ],
        'inventory_summary': [
            r'overview', r'summary', r'dashboard', r'report',
            r'tell\s+me\s+everything', r'whole\s+inventory',
            r'all\s+products', r'inventory\s+status', r'general',
        ],
        'help': [
            r'help', r'what\s+can\s+you\s+do', r'capabilities',
            r'how\s+to\s+use', r'commands', r'features',
        ],
    }

    @classmethod
    def classify(cls, query: str) -> str:
        """
        Takes a user query string and returns the detected intent.
        Returns 'general_query' if no specific intent matches.
        """
        query_lower = query.lower().strip()

        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent

        return 'general_query'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SECTION 2: Entity Extraction (Dates, Keywords)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EntityExtractor:
    """
    Extracts structured entities from natural language queries.
    Focuses on: dates, date ranges, product names, companies, status keywords.
    """

    # Month name → number mapping for quick parsing
    MONTH_MAP = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12,
    }

    @classmethod
    def extract_dates(cls, query: str) -> dict:
        """
        Extract date(s) from the query. Returns dict with keys:
        - 'single_date': a single date (for on/before/after queries)
        - 'start_date' & 'end_date': date range (for between queries)
        - 'month' & 'year': when only a month is mentioned
        """
        result = {}
        query_lower = query.lower()

        # ── Pattern 1: Explicit ISO dates (2025-05-20) ──
        iso_dates = re.findall(r'\d{4}-\d{2}-\d{2}', query)
        if iso_dates:
            parsed = [datetime.strptime(d, '%Y-%m-%d').date() for d in iso_dates]
            if len(parsed) >= 2:
                result['start_date'] = min(parsed)
                result['end_date'] = max(parsed)
            else:
                result['single_date'] = parsed[0]
            return result

        # ── Pattern 2: Dates like "20 May 2025" or "May 20, 2025" ──
        verbose_pattern = re.findall(
            r'(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s*\d{4})', query
        )
        if verbose_pattern:
            try:
                parsed = [date_parser.parse(d).date() for d in verbose_pattern]
                if len(parsed) >= 2:
                    result['start_date'] = min(parsed)
                    result['end_date'] = max(parsed)
                else:
                    result['single_date'] = parsed[0]
                return result
            except (ValueError, TypeError):
                pass

        # ── Pattern 3: Month + Year (e.g., "June 2025" or "in March") ──
        month_year = re.findall(
            r'(january|february|march|april|may|june|july|august|'
            r'september|october|november|december|'
            r'jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)'
            r'\s*(\d{4})?',
            query_lower
        )
        if month_year:
            months_found = []
            for month_str, year_str in month_year:
                month_num = cls.MONTH_MAP.get(month_str)
                year_num = int(year_str) if year_str else date.today().year
                if month_num:
                    months_found.append((year_num, month_num))

            if len(months_found) >= 2:
                # Range: "between January and June"
                start = date(months_found[0][0], months_found[0][1], 1)
                end_month = months_found[1][1]
                end_year = months_found[1][0]
                # Last day of end month
                if end_month == 12:
                    end = date(end_year, 12, 31)
                else:
                    end = date(end_year, end_month + 1, 1) - timedelta(days=1)
                result['start_date'] = start
                result['end_date'] = end
            elif len(months_found) == 1:
                result['month'] = months_found[0][1]
                result['year'] = months_found[0][0]
            return result

        # ── Pattern 4: Relative dates ("next 30 days", "7 days") ──
        days_match = re.search(r'(\d+)\s*days?', query_lower)
        if days_match:
            num_days = int(days_match.group(1))
            result['start_date'] = date.today()
            result['end_date'] = date.today() + timedelta(days=num_days)
            return result

        # ── Pattern 5: "this month", "next month", "this year" ──
        if 'this month' in query_lower:
            today = date.today()
            result['month'] = today.month
            result['year'] = today.year
        elif 'next month' in query_lower:
            next_m = date.today() + relativedelta(months=1)
            result['month'] = next_m.month
            result['year'] = next_m.year
        elif 'this year' in query_lower:
            result['start_date'] = date(date.today().year, 1, 1)
            result['end_date'] = date(date.today().year, 12, 31)

        return result

    @classmethod
    def extract_keywords(cls, query: str) -> dict:
        """
        Extract non-date entities: product names, companies, status, types.
        """
        result = {}
        query_lower = query.lower()

        # Status keywords
        for status in ['healthy', 'expired', 'near_expiry', 'near expiry']:
            if status in query_lower:
                result['status'] = status.replace(' ', '_')

        # Type keywords
        for ptype in ['petroleum', 'lubricant', 'chemical', 'gas']:
            if ptype in query_lower:
                result['type'] = ptype

        # Number extraction (for "how many" queries)
        num_match = re.search(r'(\d+)\s*(products?|items?)', query_lower)
        if num_match:
            result['count'] = int(num_match.group(1))

        # Try to extract a company or brand name (heuristic: quoted or capitalized phrases)
        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', query)
        if quoted:
            result['search_term'] = quoted[0][0] or quoted[0][1]

        return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SECTION 3: Query Builder (Translates intent → ORM)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class QueryBuilder:
    """
    Builds Django ORM querysets based on the classified intent and extracted entities.
    """

    @staticmethod
    def build(intent: str, dates: dict, keywords: dict):
        """
        Returns a queryset of InventoryItem objects matching the intent.

        Parameters:
            intent (str): The classified intent string
            dates (dict): Extracted date entities
            keywords (dict): Extracted keyword entities

        Returns:
            QuerySet or dict (for summary/count queries)
        """
        qs = InventoryItem.objects.all()
        today = date.today()

        # ── Expired products ──
        if intent == 'expired_products':
            return qs.filter(
                Q(status='expired') | Q(expiry_date__lt=today)
            )

        # ── Near expiry (within 30 days) ──
        elif intent == 'near_expiry':
            threshold = today + timedelta(days=30)
            return qs.filter(
                expiry_date__gte=today,
                expiry_date__lte=threshold
            )

        # ── Healthy products ──
        elif intent == 'healthy_products':
            threshold = today + timedelta(days=30)
            return qs.filter(
                expiry_date__gt=threshold
            )

        # ── Expiry ON a specific date ──
        elif intent == 'expiry_on_date':
            if 'single_date' in dates:
                return qs.filter(expiry_date=dates['single_date'])
            elif 'month' in dates:
                return qs.filter(
                    expiry_date__month=dates['month'],
                    expiry_date__year=dates.get('year', today.year)
                )
            return qs.none()

        # ── Expiry BEFORE a date ──
        elif intent == 'expiry_before_date':
            if 'single_date' in dates:
                return qs.filter(expiry_date__lt=dates['single_date'])
            elif 'month' in dates:
                target = date(dates.get('year', today.year), dates['month'], 1)
                return qs.filter(expiry_date__lt=target)
            return qs.none()

        # ── Expiry AFTER a date ──
        elif intent == 'expiry_after_date':
            if 'single_date' in dates:
                return qs.filter(expiry_date__gt=dates['single_date'])
            elif 'month' in dates:
                year = dates.get('year', today.year)
                month = dates['month']
                if month == 12:
                    end = date(year, 12, 31)
                else:
                    end = date(year, month + 1, 1) - timedelta(days=1)
                return qs.filter(expiry_date__gt=end)
            return qs.none()

        # ── Expiry BETWEEN two dates ──
        elif intent == 'expiry_between_dates':
            if 'start_date' in dates and 'end_date' in dates:
                return qs.filter(
                    expiry_date__gte=dates['start_date'],
                    expiry_date__lte=dates['end_date']
                )
            return qs.none()

        # ── Count / "how many" queries ──
        elif intent == 'status_count':
            status_filter = keywords.get('status')
            if status_filter == 'expired':
                count = qs.filter(
                    Q(status='expired') | Q(expiry_date__lt=today)
                ).count()
                return {'count': count, 'label': 'expired'}
            elif status_filter == 'healthy':
                threshold = today + timedelta(days=30)
                count = qs.filter(expiry_date__gt=threshold).count()
                return {'count': count, 'label': 'healthy'}
            elif status_filter == 'near_expiry':
                threshold = today + timedelta(days=30)
                count = qs.filter(
                    expiry_date__gte=today, expiry_date__lte=threshold
                ).count()
                return {'count': count, 'label': 'near expiry'}
            else:
                # General count
                return {
                    'total': qs.count(),
                    'expired': qs.filter(
                        Q(status='expired') | Q(expiry_date__lt=today)
                    ).count(),
                    'near_expiry': qs.filter(
                        expiry_date__gte=today,
                        expiry_date__lte=today + timedelta(days=30)
                    ).count(),
                    'healthy': qs.filter(
                        expiry_date__gt=today + timedelta(days=30)
                    ).count(),
                }

        # ── Product search by name/keyword ──
        elif intent == 'product_search':
            search_term = keywords.get('search_term', '')
            if not search_term:
                # Try to find a product name in the query
                # Remove common question words
                cleaned = re.sub(
                    r'\b(tell|me|about|information|on|details?|of|for|'
                    r'search|find|product|look|up|the|what|is|are|can|you)\b',
                    '', query_lower := ''
                ).strip()
                search_term = cleaned if cleaned else ''

            if search_term:
                return qs.filter(
                    Q(brand__icontains=search_term) |
                    Q(part_number__icontains=search_term) |
                    Q(company__icontains=search_term)
                )
            return qs.none()

        # ── Brand listing ──
        elif intent == 'brand_query':
            return qs.values('brand').annotate(
                count=Count('id')
            ).order_by('brand')

        # ── Company query ──
        elif intent == 'company_query':
            search = keywords.get('search_term', '')
            if search:
                return qs.filter(company__icontains=search)
            return qs.values('company').annotate(
                count=Count('id')
            ).order_by('company')

        # ── Full inventory summary ──
        elif intent == 'inventory_summary':
            today = date.today()
            threshold = today + timedelta(days=30)
            return {
                'total_products': qs.count(),
                'expired': qs.filter(
                    Q(status='expired') | Q(expiry_date__lt=today)
                ).count(),
                'near_expiry': qs.filter(
                    expiry_date__gte=today, expiry_date__lte=threshold
                ).count(),
                'healthy': qs.filter(expiry_date__gt=threshold).count(),
                'types': list(qs.values('type').annotate(
                    count=Count('id')
                ).order_by('type')),
                'companies': list(qs.values('company').annotate(
                    count=Count('id')
                ).order_by('company')),
                'upcoming_expiries': list(
                    qs.filter(expiry_date__gte=today)
                    .order_by('expiry_date')[:5]
                    .values('brand', 'part_number', 'expiry_date', 'company')
                ),
            }

        # ── Default: return all products ──
        return qs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SECTION 4: Response Generator (Formats output)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ResponseGenerator:
    """
    Converts query results into friendly, structured responses
    that the frontend can display.
    """

    GREETING = "Hi! I'm Lilian, your inventory AI assistant. "

    @classmethod
    def generate(cls, intent: str, result, query: str) -> dict:
        """
        Generates a response dict with:
        - message: Human-readable text response
        - data: Structured data (list of products or summary stats)
        - intent: The detected intent (for frontend routing/display)
        - count: Number of results
        """

        # ── Help response ──
        if intent == 'help':
            return {
                'message': (
                    f"{cls.GREETING}Here's what I can help you with:\n\n"
                    "• **Expired Products** — Ask me which products are already expired.\n"
                    "• **Near Expiry** — I can show products expiring within the next 30 days.\n"
                    "• **Healthy Products** — See all products in good condition.\n"
                    "• **Expiry by Date** — Ask about products expiring on, before, or after a specific date.\n"
                    "• **Date Ranges** — Find products expiring between two dates.\n"
                    "• **Inventory Summary** — Get a complete overview of your inventory.\n"
                    "• **Product Search** — Look up specific products by name or part number.\n"
                    "• **Counts** — Ask 'how many expired products?' etc.\n\n"
                    "Try asking: 'What products expire before June 2025?'"
                ),
                'data': None,
                'intent': intent,
                'count': 0,
            }

        # ── Summary / dashboard response ──
        if intent == 'inventory_summary' and isinstance(result, dict):
            summary = result
            msg = (
                f"{cls.GREETING}Here's your inventory overview:\n\n"
                f"📦 **Total Products:** {summary['total_products']}\n"
                f"✅ **Healthy:** {summary['healthy']}\n"
                f"⚠️ **Near Expiry (within 30 days):** {summary['near_expiry']}\n"
                f"❌ **Expired:** {summary['expired']}\n"
            )
            if summary.get('upcoming_expiries'):
                msg += "\n📅 **Next 5 Upcoming Expiries:**\n"
                for item in summary['upcoming_expiries']:
                    msg += f"  - {item['brand']} ({item['part_number']}) → {item['expiry_date']} [{item['company']}]\n"

            return {
                'message': msg,
                'data': summary,
                'intent': intent,
                'count': summary['total_products'],
            }

        # ── Count response ──
        if intent == 'status_count' and isinstance(result, dict):
            if 'label' in result:
                return {
                    'message': (
                        f"There are **{result['count']}** {result['label']} "
                        f"products in your inventory."
                    ),
                    'data': result,
                    'intent': intent,
                    'count': result['count'],
                }
            else:
                msg = (
                    f"Here's the count breakdown:\n\n"
                    f"📦 Total: {result['total']}\n"
                    f"✅ Healthy: {result['healthy']}\n"
                    f"⚠️ Near Expiry: {result['near_expiry']}\n"
                    f"❌ Expired: {result['expired']}"
                )
                return {
                    'message': msg,
                    'data': result,
                    'intent': intent,
                    'count': result['total'],
                }

        # ── Brand listing ──
        if intent == 'brand_query' and not hasattr(result, 'model'):
            brands = list(result)
            if brands:
                brand_list = ', '.join(
                    f"{b['brand']} ({b['count']} items)" for b in brands
                )
                return {
                    'message': f"Here are the brands in your inventory: {brand_list}",
                    'data': brands,
                    'intent': intent,
                    'count': len(brands),
                }
            return {
                'message': "No brands found in the inventory.",
                'data': [],
                'intent': intent,
                'count': 0,
            }

        # ── Company listing ──
        if intent == 'company_query' and not hasattr(result, 'model'):
            companies = list(result)
            if companies:
                comp_list = ', '.join(
                    f"{c['company']} ({c['count']} items)" for c in companies
                )
                return {
                    'message': f"Companies supplying your inventory: {comp_list}",
                    'data': companies,
                    'intent': intent,
                    'count': len(companies),
                }

        # ── Queryset results (list of products) ──
        if hasattr(result, 'model'):
            products = list(result.values(
                'id', 'brand', 'part_number', 'type', 'usage_rate',
                'batch_number', 'shelf_life', 'expiry_date', 'company', 'status'
            ))
            count = len(products)

            if count == 0:
                return {
                    'message': cls._no_results_message(intent),
                    'data': [],
                    'intent': intent,
                    'count': 0,
                }

            # Build a contextual message based on intent
            msg = cls._product_list_message(intent, count, products)

            return {
                'message': msg,
                'data': products,
                'intent': intent,
                'count': count,
            }

        # ── Fallback ──
        return {
            'message': (
                f"{cls.GREETING}I'm not sure I understood your question. "
                "Try asking about expired products, expiry dates, or inventory status. "
                "Type 'help' to see what I can do!"
            ),
            'data': None,
            'intent': 'unknown',
            'count': 0,
        }

    @classmethod
    def _no_results_message(cls, intent: str) -> str:
        """Returns a friendly 'no results' message based on intent."""
        messages = {
            'expired_products': "Great news! No expired products found in your inventory.",
            'near_expiry': "No products are near expiry at the moment.",
            'healthy_products': "No healthy products found — you may want to check your inventory.",
            'expiry_on_date': "No products found expiring on that date.",
            'expiry_before_date': "No products found expiring before that date.",
            'expiry_after_date': "No products found expiring after that date.",
            'expiry_between_dates': "No products found in that date range.",
            'product_search': "No products matched your search criteria.",
        }
        return messages.get(intent, "No matching products found.")

    @classmethod
    def _product_list_message(cls, intent: str, count: int, products: list) -> str:
        """Builds a human-readable message for product list results."""
        intent_labels = {
            'expired_products': 'expired',
            'near_expiry': 'near expiry',
            'healthy_products': 'healthy',
            'expiry_on_date': 'matching',
            'expiry_before_date': 'matching',
            'expiry_after_date': 'matching',
            'expiry_between_dates': 'matching',
            'product_search': 'matching',
            'company_query': 'matching',
        }
        label = intent_labels.get(intent, '')

        msg = f"I found **{count}** {label} product(s):\n\n"

        # Show first 10 products in the message (full data is in 'data')
        for p in products[:10]:
            status_icon = {
                'healthy': '✅',
                'expired': '❌',
                'near_expiry': '⚠️',
            }.get(p.get('status', ''), '📦')

            msg += (
                f"{status_icon} **{p['brand']}** ({p['part_number']}) — "
                f"Expires: {p['expiry_date']} | {p['company']}\n"
            )

        if count > 10:
            msg += f"\n...and {count - 10} more. Full list is in the data below."

        return msg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SECTION 5: Main Lilian AI Class (Orchestrator)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LilianAI:
    """
    The main AI orchestrator. This is the single entry point
    that the API view calls.

    Usage:
        response = LilianAI.ask("What products are expired?")
    """

    @staticmethod
    def ask(query: str) -> dict:
        """
        Process a user query through the full AI pipeline.

        Pipeline:
        1. Classify intent
        2. Extract entities (dates + keywords)
        3. Build database query
        4. Generate human-readable response

        Returns:
            dict with keys: message, data, intent, count, query
        """
        # Step 1: Classify the intent
        intent = IntentClassifier.classify(query)

        # Step 2: Extract entities
        dates = EntityExtractor.extract_dates(query)
        keywords = EntityExtractor.extract_keywords(query)

        # Step 3: Build and execute query
        result = QueryBuilder.build(intent, dates, keywords)

        # Step 4: Generate response
        response = ResponseGenerator.generate(intent, result, query)

        # Add metadata
        response['query'] = query
        response['extracted_dates'] = {
            k: str(v) if isinstance(v, date) else v
            for k, v in dates.items()
        }
        response['extracted_keywords'] = keywords

        return response

    @staticmethod
    def refresh_statuses():
        """
        Batch job: Update all product statuses based on current date.
        Can be called via a management command or API endpoint.
        Returns summary of changes.
        """
        today = date.today()
        threshold = today + timedelta(days=30)

        # Update expired
        expired_count = InventoryItem.objects.filter(
            expiry_date__lt=today
        ).exclude(status='expired').update(status='expired')

        # Update near expiry
        near_count = InventoryItem.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=threshold
        ).exclude(status='near_expiry').update(status='near_expiry')

        # Update healthy
        healthy_count = InventoryItem.objects.filter(
            expiry_date__gt=threshold
        ).exclude(status='healthy').update(status='healthy')

        return {
            'updated_to_expired': expired_count,
            'updated_to_near_expiry': near_count,
            'updated_to_healthy': healthy_count,
            'timestamp': str(datetime.now()),
        }
