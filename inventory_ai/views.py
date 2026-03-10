"""
views.py - API Views (Endpoints)
==================================
These are the REST API endpoints that the frontend/backend integrates with.

Endpoints:
──────────
POST /api/ai/chat/          → Main chat endpoint (send query, get AI response)
GET  /api/ai/status/         → Quick inventory status check
POST /api/ai/refresh-status/ → Batch update all product statuses
GET  /api/ai/history/        → Get conversation history
GET  /api/ai/health/         → Health check for the AI service
"""

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .ai_service import LilianAI
from .serializers import (
    AIQuerySerializer,
    AIResponseSerializer,
    AIConversationLogSerializer,
)
from .models import AIConversationLog, InventoryItem

from datetime import date, timedelta
from django.db.models import Q


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 1: Main Chat API (The primary integration point)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@method_decorator(csrf_exempt, name='dispatch')
class AIChatView(APIView):
    """
    POST /api/ai/chat/

    The main endpoint for interacting with Lilian AI.
    Frontend sends a natural language query, and Lilian responds
    with analysis, product lists, and inventory insights.

    Request Body:
        {
            "query": "What products are expired?"
        }

    Response:
        {
            "success": true,
            "message": "I found 3 expired products...",
            "data": [...],          // product list or summary
            "intent": "expired_products",
            "count": 3,
            "query": "What products are expired?",
            "extracted_dates": {},
            "extracted_keywords": {"status": "expired"}
        }
    """
    permission_classes = [AllowAny]  # Change to [IsAuthenticated] in production

    def post(self, request):
        # Step 1: Validate the request
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'Invalid request',
                    'details': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = serializer.validated_data['query']

        try:
            # Step 2: Process query through Lilian AI
            ai_response = LilianAI.ask(query)

            # Step 3: Log the conversation
            AIConversationLog.objects.create(
                user_query=query,
                ai_response=ai_response['message'],
                intent_detected=ai_response['intent'],
            )

            # Step 4: Serialize dates in data (convert date objects to strings)
            data = ai_response.get('data')
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, date):
                                item[key] = value.isoformat()

            # Step 5: Return the response
            return Response(
                {
                    'success': True,
                    **ai_response,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'AI processing error',
                    'details': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 2: Quick Status Overview
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIStatusView(APIView):
    """
    GET /api/ai/status/

    Returns a quick snapshot of inventory health.
    Useful for dashboard widgets and status indicators.

    Response:
        {
            "success": true,
            "total": 150,
            "healthy": 120,
            "near_expiry": 20,
            "expired": 10,
            "near_expiry_products": [...],
            "recently_expired": [...]
        }
    """
    permission_classes = [AllowAny]

    def get(self, request):
        today = date.today()
        threshold = today + timedelta(days=30)

        total = InventoryItem.objects.count()
        expired = InventoryItem.objects.filter(
            Q(status='expired') | Q(expiry_date__lt=today)
        ).count()
        near_expiry = InventoryItem.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=threshold
        ).count()
        healthy = InventoryItem.objects.filter(
            expiry_date__gt=threshold
        ).count()

        # Get the 5 most urgent near-expiry products
        near_expiry_products = list(
            InventoryItem.objects.filter(
                expiry_date__gte=today,
                expiry_date__lte=threshold
            ).order_by('expiry_date')[:5].values(
                'id', 'brand', 'part_number', 'expiry_date', 'company'
            )
        )

        # Get 5 most recently expired products
        recently_expired = list(
            InventoryItem.objects.filter(
                expiry_date__lt=today
            ).order_by('-expiry_date')[:5].values(
                'id', 'brand', 'part_number', 'expiry_date', 'company'
            )
        )

        # Serialize dates
        for products in [near_expiry_products, recently_expired]:
            for p in products:
                if isinstance(p.get('expiry_date'), date):
                    p['expiry_date'] = p['expiry_date'].isoformat()

        return Response({
            'success': True,
            'total': total,
            'healthy': healthy,
            'near_expiry': near_expiry,
            'expired': expired,
            'near_expiry_products': near_expiry_products,
            'recently_expired': recently_expired,
        })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 3: Batch Status Refresh
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@method_decorator(csrf_exempt, name='dispatch')
class AIRefreshStatusView(APIView):
    """
    POST /api/ai/refresh-status/

    Triggers a batch update of all inventory statuses.
    Products are re-evaluated based on current date:
    - expiry_date < today → status = 'expired'
    - expiry_date within 30 days → status = 'near_expiry'
    - expiry_date > 30 days away → status = 'healthy'

    Call this periodically (e.g., daily cron) or on-demand.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            result = LilianAI.refresh_statuses()
            return Response({
                'success': True,
                'message': 'Inventory statuses refreshed successfully.',
                **result,
            })
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 4: Conversation History
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIConversationHistoryView(ListAPIView):
    """
    GET /api/ai/history/

    Returns the last 50 conversation entries with Lilian.
    Supports query parameter filtering:
        ?intent=expired_products  → filter by intent
        ?limit=20                 → limit results
    """
    permission_classes = [AllowAny]
    serializer_class = AIConversationLogSerializer

    def get_queryset(self):
        qs = AIConversationLog.objects.all()

        intent = self.request.query_params.get('intent')
        if intent:
            qs = qs.filter(intent_detected=intent)

        limit = self.request.query_params.get('limit', 50)
        try:
            limit = int(limit)
        except ValueError:
            limit = 50

        return qs[:limit]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 5: Health Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIHealthCheckView(APIView):
    """
    GET /api/ai/health/

    Simple health check to verify the AI service is running.
    Returns service status and basic stats.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            product_count = InventoryItem.objects.count()
            conversation_count = AIConversationLog.objects.count()

            return Response({
                'success': True,
                'service': 'Lilian AI',
                'status': 'operational',
                'version': '1.0.0',
                'stats': {
                    'total_products_tracked': product_count,
                    'total_conversations': conversation_count,
                },
            })
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'service': 'Lilian AI',
                    'status': 'error',
                    'error': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
