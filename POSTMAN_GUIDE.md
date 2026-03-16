# Postman Guide: Lilian AI API

This guide provides step-by-step instructions on how to test the Lilian AI endpoints locally using Postman.

### Prerequisites
1. Ensure your Django server is running locally:
   ```bash
   python manage.py runserver
   ```
2. Your base URL will be: `http://127.0.0.1:8000`

---

### 🚀 API Endpoints Quick Reference
Here are all the endpoints available in the system, grouped together for easy access:

| Feature | Method | URL |
| :--- | :--- | :--- |
| **1. Lilian AI Chat (RAG)**      | `POST` | `http://127.0.0.1:8000/api/ai/chat/` |
| **2. Marie AI Chat (RAG)**       | `GET` / `POST` | `http://127.0.0.1:8000/api/ai/marketplace-chat/` |
| **3. Lilian Chat History**       | `GET`  | `http://127.0.0.1:8000/api/ai/history/lilian_rag/` |
| **4. Marie Chat History**        | `GET`  | `http://127.0.0.1:8000/api/ai/history/marie_faiss/` |
| **5. Submit Support Ticket**     | `POST` | `http://127.0.0.1:8000/api/ai/tickets/` |
| **6. Admin Ticket List**         | `GET`  | `http://127.0.0.1:8000/api/ai/tickets/admin/` |
| **7. Admin Ticket Detail/Update**| `GET` / `PATCH`| `http://127.0.0.1:8000/api/ai/tickets/admin/<ticket_id>/` |

---

## 1. Lilian AI Chat (FAISS RAG Powered)
*The main endpoint for inventory queries. Now exclusively uses FAISS for semantic similarity search.*

- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/ai/chat/`
- **Headers:** 
  - `Content-Type`: `application/json`
- **Body:** 
  ```json
  {
      "query": "I need products related to fuel maintenance."
  }
  ```

---

## 2. Marketplace Chat (Marie) - FAISS RAG Powered
*The main endpoint for marketplace discovery. Now exclusively uses FAISS for semantic similarity search.*

**(A) Initial Welcome Message**
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/ai/marketplace-chat/`

**(B) Semantic Product Discovery**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/ai/marketplace-chat/`
- **Body:** 
  ```json
  {
      "query": "Is there any Aviation fuel available for purchase?"
  }
  ```

---

## 3. Conversation History
*Fetches the log of past questions asked to the AIs and their responses.*

- **Method:** `GET`
- **URLs:** 
  - `http://127.0.0.1:8000/api/ai/history/lilian/` (For main inventory chat)
  - `http://127.0.0.1:8000/api/ai/history/marie/` (For marketplace chat)
- **Headers:** None required
- **Body:** None
- **Query Parameters (Optional):**
  - **Key:** `limit` | **Value:** `10` (To fetch only the last 10 logs)
- **Expected Status:** `200 OK`

---
 
---

## 4. Support Ticket System
*A Jira-inspired internal support ticketing system for users and admins.*

**(A) Submit a Ticket (Public)**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/ai/tickets/`
- **Body:** (Select **raw** and **JSON**)
  ```json
  {
      "name": "John Doe",
      "email": "john@example.com",
      "description": "I am experiencing delays when searching for lubricants."
  }
  ```
- **Expected Status:** `201 Created`

**(B) List or Fetch Tickets (Admin)**
- **Method:** `GET`
- **URL (List):** `http://127.0.0.1:8000/api/ai/tickets/admin/`
- **URL (Detail):** `http://127.0.0.1:8000/api/ai/tickets/admin/<ticket_id>/` (e.g., `TKT-0001`)
- **Query Parameters (for List only):**
  - `status`: `open` (optional)
- **Expected Status:** `200 OK`

**(C) Update Ticket Status (Admin)**
- **Method:** `PATCH`
- **URL:** `http://127.0.0.1:8000/api/ai/tickets/admin/<ticket_id>/` (e.g., `TKT-0001`)
- **Body:** (Select **raw** and **JSON**)
  ```json
  {
      "status": "resolved",
      "admin_notes": "Issue fixed by optimizing the search query."
  }
  ```
- **Expected Status:** `200 OK`

---

### Troubleshooting
- **404 Not Found:** Make sure you include the trailing slash `/` at the end of the URL depending on your Django settings (e.g., `/api/ai/chat/` not `/api/ai/chat`).
- **500 Server Error:** Check your terminal where `runserver` is running to see the Python error traceback.
