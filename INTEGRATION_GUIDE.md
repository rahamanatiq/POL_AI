# POL Tracking - AI & Support System Integration Guide

This guide ensures the React frontend can seamlessly communicate with the **pol_ai** backend.

---

## 1. Core Endpoints Table

| Feature | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Lilian AI** | `POST` | `/api/ai/chat/` | Inventory queries, expiry checks, and summaries. |
| **Marie AI** | `GET` | `/api/ai/marketplace-chat/` | Fetches Marie's initial welcome message. |
| **Marie AI** | `POST` | `/api/ai/marketplace-chat/` | Marketplace queries (Buyers/Sellers). |
| **History** | `GET` | `/api/ai/history/{assistant}/` | Gets last 50 logs for `lilian` or `marie`. |
| **Tickets** | `POST` | `/api/ai/tickets/` | Public support ticket submission. |
| **Tkt Admin**| `GET` | `/api/ai/tickets/admin/` | List all tickets (Admin only). |
| **Tkt Admin**| `GET/PATCH`| `/api/ai/tickets/admin/{ticket_id}/` | Detail and Status updates by string ID (e.g. `TKT-0001`). |

---

## 2. API Security & Protection

### Rate Limiting (Throttling)
To protect Gemini API credits, the following limits are enforced:
- **AI Burst:** 10 requests/minute combined for Lilian/Marie.
- **Support Tickets:** 100 per day per IP.
- **Global Anon:** 100 requests/day for unauthenticated users.

---

## 3. Implementation Examples

### Chatting with Lilian/Marie (React)
```javascript
const askAI = async (endpoint, query) => {
  const response = await fetch(`/api/ai/${endpoint}/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  
  if (response.status === 429) {
    alert("Rate limit reached. Please wait a minute.");
    return;
  }
  
  return await response.json();
};
```

### Submitting a Support Ticket
```javascript
const submitTicket = async (formData) => {
  // formData = { name, email, description }
  const resp = await fetch('/api/ai/tickets/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  return await resp.json();
};
```

---

## 4. Response Format
All AI endpoints return a consistent JSON structure:
```json
{
  "success": true,
  "message": "AI generated response text (Markdown supported)",
  "data": [...], // Raw object array from database
  "intent": "detected_intent_name",
  "count": 5 // Number of items in data
}
```

---
*Note: Ensure your environment has the `GEMINI_API_KEY` set in the `.env` file before starting the server.*
