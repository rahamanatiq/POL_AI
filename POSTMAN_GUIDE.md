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
      "query": "What products are expired?"
  }
  ```
- **Other queries to try:**
  - `"query": "Give me an inventory overview"`
  - `"query": "What expires next month?"`
  - `"query": "How many healthy products do we have?"`
  - `"query": "What can you do?"`
- **Expected Status:** `200 OK` (It will return the `message`, `data` list, and `intent`).

---

## 2. Conversation History
*Fetches the log of past questions asked to Lilian and her responses.*

- **Method:** `GET`
- **URL:** `http://127.0.0.1:8000/api/ai/history/`
- **Headers:** None required
- **Body:** None
- **Query Parameters (Optional):**
  - **Key:** `limit` | **Value:** `10` (To fetch only the last 10 logs)
- **Expected Status:** `200 OK`

---

### Troubleshooting
- **404 Not Found:** Make sure you include the trailing slash `/` at the end of the URL depending on your Django settings (e.g., `/api/ai/chat/` not `/api/ai/chat`).
- **500 Server Error:** Check your terminal where `runserver` is running to see the Python error traceback.
