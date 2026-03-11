# Lilian AI - Integration Guide for POL Tracking
## Inventory Intelligence API

---

## 1. Overview

**Lilian** is the AI assistant for the POL Tracking inventory system. It provides natural language querying capabilities over inventory data, specifically focused on:

- Tracking expiry dates (expired, near-expiry, healthy)
- Answering date-based queries (on/before/after/between specific dates)
- Listing and filtering products by status, brand, company, type
- Providing inventory summaries and counts

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  Chat Widget / Inventory Page / Dashboard                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP POST/GET
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 DJANGO REST API (views.py)               │
│  /api/ai/chat/  |  /api/ai/status/  |  /api/ai/health/ │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              LILIAN AI ENGINE (ai_service.py)            │
│                                                          │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │    Intent     │  │    Entity      │  │   Query     │ │
│  │  Classifier   │→ │  Extractor     │→ │  Builder    │ │
│  └──────────────┘  └────────────────┘  └──────┬──────┘ │
│                                                │        │
│  ┌──────────────┐                              │        │
│  │  Response     │←────────────────────────────┘        │
│  │  Generator    │                                       │
│  └──────────────┘                                        │
└──────────────────────┬──────────────────────────────────┘
                       │ Django ORM
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   DATABASE (SQLite/PostgreSQL)            │
│              InventoryItem  |  AIConversationLog         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Setup Instructions

### 3.1 Install Dependencies

Add these to your `requirements.txt`:

```
djangorestframework>=3.14
python-dateutil>=2.8
```

Then run:
```bash
pip install -r requirements.txt
```

### 3.2 Add to INSTALLED_APPS

In `pol_tracking/settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps
    'rest_framework',
    'pol_ai',
]
```

### 3.3 Include URLs

In `pol_tracking/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing URLs
    path('api/ai/', include('pol_ai.urls')),
]
```

### 3.4 Run Migrations

```bash
python manage.py makemigrations pol_ai
python manage.py migrate
```

### 3.5 (Optional) Add CORS Headers

If the frontend runs on a different port:

```bash
pip install django-cors-headers
```

Add to `settings.py`:
```python
INSTALLED_APPS = [
    'corsheaders',
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

CORS_ALLOW_ALL_ORIGINS = True  # Restrict in production
```

---

## 4. API Endpoints Reference

### 4.1 POST `/api/ai/chat/` — Main Chat

**Request:**
```json
{
    "query": "What products are expired?"
}
```

**Response (200):**
```json
{
    "success": true,
    "message": "I found **3** expired product(s):\n\n❌ **High-Grade Diesel** (PD-100) ...",
    "data": [
        {
            "id": 1,
            "brand": "High-Grade Diesel",
            "part_number": "PD-100",
            "type": "petroleum",
            "usage_rate": "500Liters",
            "batch_number": "B-001",
            "shelf_life": "5 years",
            "expiry_date": "2025-05-20",
            "company": "Global Fuels Ltd",
            "status": "expired"
        }
    ],
    "intent": "expired_products",
    "count": 3,
    "query": "What products are expired?",
    "extracted_dates": {},
    "extracted_keywords": {"status": "expired"}
}
```

### 4.2 GET `/api/ai/status/` — Quick Status

**Response:**
```json
{
    "success": true,
    "total": 150,
    "healthy": 120,
    "near_expiry": 20,
    "expired": 10,
    "near_expiry_products": [...],
    "recently_expired": [...]
}
```

### 4.3 POST `/api/ai/refresh-status/` — Batch Refresh

### 4.4 GET `/api/ai/history/` — Conversation Log

### 4.5 GET `/api/ai/health/` — Health Check

---

## 5. Example Queries Lilian Understands

| Query | Detected Intent |
|-------|----------------|
| "What products are expired?" | expired_products |
| "Which items are expiring soon?" | near_expiry |
| "Show me healthy products" | healthy_products |
| "What expires on 2025-06-01?" | expiry_on_date |
| "Products expiring in June" | expiry_on_date |
| "What expires before March 2025?" | expiry_before_date |
| "Products expiring after July" | expiry_after_date |
| "Between January and June 2025" | expiry_between_dates |
| "How many expired products?" | status_count |
| "Give me an inventory overview" | inventory_summary |
| "What brands do we have?" | brand_query |
| "Products from Global Fuels" | company_query |
| "What can you do?" | help |

---

## 6. Frontend Integration Example (JavaScript)

```javascript
// Chat with Lilian
async function askLilian(query) {
    const response = await fetch('/api/ai/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
    });
    return await response.json();
}

// Example usage
const result = await askLilian("What products expire before June 2025?");
console.log(result.message);     // Lilian's text response
console.log(result.data);        // Array of matching products
console.log(result.count);       // Number of results
```

---

## 7. Daily Status Refresh (Cron)

```bash
# Add to crontab to auto-update statuses daily at midnight
0 0 * * * cd /path/to/POL_Tracking && python manage.py refresh_inventory_status
```

---

## 8. Important Notes for Backend Integration

1. **Model Sharing**: If the backend already has an `InventoryItem` model, update the import in `ai_service.py` to use the existing model instead of creating a new one.

2. **Authentication**: The views currently use `AllowAny` permissions. Change to `IsAuthenticated` and add token/session auth for production.

3. **Database**: The AI service queries the same database as the backend. No separate data store is needed.

4. **No External API Required**: Lilian uses rule-based NLP — no OpenAI/Claude API key needed. This can be upgraded later by replacing `ai_service.py`.
