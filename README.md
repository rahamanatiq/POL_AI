[README.md](https://github.com/user-attachments/files/27538357/README.md)
# POL AI Tracking System

> **An AI-powered Petroleum, Oil & Lubricants inventory and marketplace management platform** built with Django REST Framework, FAISS semantic search, and Google Gemini.

---

## ✨ Features

- **Lilian AI** — Intelligent inventory assistant that answers natural language questions about your POL stock, expiry dates, and product status using FAISS-powered semantic search.
- **Marie AI** — Marketplace assistant that helps users find the best buyers and sellers across petroleum, oil, and lubricant listings.
- **FAISS RAG Architecture** — Retrieval-Augmented Generation using Facebook AI Similarity Search for fast, context-aware responses.
- **Smart Expiry Tracking** — Auto-updates product statuses (healthy / near_expiry / expired) based on real-time date comparison.
- **Support Ticketing** — Built-in support ticket system with admin management and unique ticket IDs.
- **Conversation History** — Persistent logging of all AI conversations for analytics and context-aware follow-ups.
- **Auto FAISS Sync** — Django signals automatically rebuild the FAISS vector index on any inventory change.

---

## 🏗️ Architecture

```
User Query (Natural Language)
        │
        ▼
  Django REST API
        │
        ▼
  FAISS Semantic Search  ←──  Vector Index (Gemini Embeddings)
        │
        ▼
  Retrieved Context (Top-K similar items)
        │
        ▼
  Google Gemini (gemini-2.5-flash)  ←──  Conversation History
        │
        ▼
  Structured JSON Response → React Frontend
```

**Two AI Assistants, Two Indexes:**

| Assistant | Data Source | Index File |
|-----------|------------|------------|
| Lilian | `POLItem` (Internal Inventory) | `inventory_vector_index.faiss` |
| Marie | `Listing` (Marketplace) | `marketplace_vector_index.faiss` |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js (optional, for frontend)
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/pol-ai-tracking.git
cd pol-ai-tracking

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your keys:
# GEMINI_API_KEY=your_key_here
# DJANGO_SECRET_KEY=your_secret_key
# DJANGO_DEBUG=True

# 5. Run migrations
python manage.py migrate

# 6. Seed sample data (optional)
python manage.py seed_inventory
python manage.py seed_marketplace

# 7. Build FAISS vector indexes
python manage.py sync_faiss
python manage.py sync_marketplace_faiss

# 8. Start the server
python manage.py runserver
```

---

## 🔌 API Endpoints

### Lilian AI — Inventory Assistant

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ai/chat/` | Ask Lilian a question about inventory |
| `GET` | `/api/ai/history/lilian_rag/` | Get Lilian's conversation history |

**Example Request:**
```json
POST /api/ai/chat/
{
  "query": "Which products are expiring within 30 days?"
}
```

**Example Response:**
```json
{
  "success": true,
  "message": "I found 2 products expiring soon...",
  "data": [...],
  "intent": "faiss_rag_query"
}
```

### Marie AI — Marketplace Assistant

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ai/marketplace-chat/` | Get Marie's welcome greeting |
| `POST` | `/api/ai/marketplace-chat/` | Ask Marie about buyers/sellers |
| `GET` | `/api/ai/history/marie_faiss/` | Get Marie's conversation history |

### Support Tickets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ai/tickets/` | Submit a support ticket |
| `GET` | `/api/ai/tickets/admin/` | List all tickets (admin) |
| `PATCH` | `/api/ai/tickets/admin/<ticket_id>/` | Update ticket status (admin) |

---

## 🧠 How the RAG Pipeline Works

1. **Indexing** — When inventory or listings change, Django signals trigger a rebuild of the FAISS index. Each item is converted to a text document and embedded using `gemini-embedding-001`.

2. **Retrieval** — When a user sends a query, the query is embedded and compared against the FAISS index. The top-K most semantically similar items are retrieved.

3. **Generation** — The retrieved context, along with the last 5 conversation turns, is sent to `gemini-2.5-flash` with a role-specific system prompt. The model generates a grounded, context-aware response.

---

## 🗄️ Data Models

| Model | Purpose |
|-------|---------|
| `POLItem` | Internal inventory — tracked by Lilian |
| `Listing` | Marketplace listings — tracked by Marie |
| `InventoryItem` | Legacy inventory model |
| `MarketplaceItem` | Legacy marketplace model |
| `AIConversationLog` | Full conversation history for both assistants |
| `SupportTicket` | User-submitted support requests |

---

## ⚙️ Management Commands

```bash
# Rebuild FAISS index for inventory (POLItems)
python manage.py sync_faiss

# Rebuild FAISS index for marketplace (Listings)
python manage.py sync_marketplace_faiss

# Seed 20 sample inventory POL items
python manage.py seed_inventory

# Seed 20 sample marketplace listings
python manage.py seed_marketplace
```

---

## 🧪 Running Tests

```bash
python manage.py test pol_ai
```

The test suite covers:
- Intent classification accuracy
- Entity/date extraction
- Full AI pipeline integration
- All REST API endpoints

---

## ⚡ Rate Limiting

| Scope | Limit |
|-------|-------|
| Anonymous users | 100 requests / day |
| Authenticated users | 1000 requests / day |
| AI chat endpoints | 10 requests / minute |

---

## 🛠️ Tech Stack

- **Backend:** Django 6.0, Django REST Framework
- **AI:** Google Gemini (`gemini-2.5-flash`, `gemini-embedding-001`)
- **Vector Search:** FAISS (Facebook AI Similarity Search)
- **Database:** SQLite (development) — swap to PostgreSQL for production
- **Auth:** Django's built-in auth system

---

## 📁 Project Structure

```
pol-ai-tracking/
├── core/                   # Django project config (settings, urls, wsgi)
├── pol_ai/
│   ├── ai_service.py       # FAISS RAG engine (Lilian & Marie)
│   ├── models.py           # Database models
│   ├── views.py            # API endpoints
│   ├── serializers.py      # Request/response validation
│   ├── urls.py             # URL routing
│   ├── signals.py          # Auto FAISS sync on DB changes
│   ├── admin.py            # Django admin config
│   ├── migrations/         # Database migrations
│   └── management/
│       └── commands/       # seed_inventory, seed_marketplace, sync_faiss
└── manage.py
```

---

## 🔒 Security Notes

- Set `DJANGO_DEBUG=False` and configure `ALLOWED_HOSTS` in production.
- Change `permission_classes` from `AllowAny` to `IsAuthenticated` on sensitive endpoints.
- Store all secrets in `.env` — never commit API keys to version control.
- Consider offloading FAISS index rebuilds to a background worker (Celery) for production workloads.

---

## 📄 License

This project is licensed under the MIT License.
