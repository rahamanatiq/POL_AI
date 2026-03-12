# Postman Guide: Lilian AI API

This guide provides step-by-step instructions on how to test the Lilian AI endpoints locally using Postman.

### Prerequisites
1. Ensure your Django server is running locally:
   ```bash
   python manage.py runserver
   ```
2. Your base URL will be: `http://127.0.0.1:8000`

---

## 1. Main AI Chat
*This is the core endpoint where your frontend will send natural language text questions.*

- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/ai/chat/`
- **Headers:** 
  - `Content-Type`: `application/json`
- **Body:** (Select **raw** and **JSON**)
  ```json
  {
      "query": "Which products expire before June 2025 and are Petroleum?"
  }
  ```
- **Other queries to try (to test LLM Text-to-SQL logic):**
  - `"query": "How many total products do we have across all brands?"`
  - `"query": "List all products from Global Fuels Ltd."`
  - `"query": "Are there any items that have a usage rate of 500Liters?"`
  - `"query": "Group my products by their status and give me the count for each."`
- **Expected Status:** `200 OK` (It will return the conversational `message` and raw `data` list).

---

## 2. Marketplace Chat (Marie)
*This endpoint manages chat specifically for buying and selling products on the Marketplace page.*

**(A) Initial Welcome Message**
*Call this when the chatbox opens, before the user types anything.*
- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/ai/marketplace-chat/`
- **Expected Status:** `200 OK` (It will return her predefined introduction message).

**(B) Asking Questions**
- **Method:** `POST`
- **URL:** `http://127.0.0.1:8000/api/ai/marketplace-chat/`
- **Headers:** 
  - `Content-Type`: `application/json`
- **Body:** (Select **raw** and **JSON**)
  ```json
  {
      "query": "Is there any Aviation fuel available?"
  }
  ```
- **Other queries to try:**
  - `"query": "List all the oils you have for sale"`
  - `"query": "Where is the Industrial Solvent located?"`
  - `"query": "What is the cheapest product you have?"`
- **Expected Status:** `200 OK` (It will return Marie's message and the raw product data).

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
