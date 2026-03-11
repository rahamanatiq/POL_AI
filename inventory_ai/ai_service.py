"""
ai_service.py - Lilian AI Engine
=================================
Powered by Google Gemini (Text-to-SQL Architecture).
Dynamically translates natural language into read-only SQL queries
to answer any question about the inventory database.
"""

import os
import json
import re
from datetime import date
from django.db import connection
from google import genai
from google.genai import types

class SchemaBuilder:
    @staticmethod
    def get_schema():
        return f"""
Table: inventory_ai_inventoryitem
Description: Stores all inventory products and their metadata.
Columns:
- id (Integer, Primary Key)
- brand (String): Product brand name (e.g., 'High-Grade Diesel')
- part_number (String): Unique part identifier (e.g., 'PD - 100')
- type (String): Category (petroleum, lubricant, chemical, gas, other)
- usage_rate (String): Consumption rate (e.g., '500Liters')
- batch_number (String): Manufacturing batch ID (e.g., 'B-001')
- shelf_life (String): Expected shelf life duration (e.g., '5 years')
- expiry_date (Date): Product expiration date format YYYY-MM-DD
- company (String): Supplier/manufacturer company (e.g., 'Global Fuels Ltd')
- status (String): Current product status (healthy, expired, near_expiry)
- created_at (DateTime)
- updated_at (DateTime)

Current Date: {date.today().isoformat()}
"""

def execute_readonly_sql(query: str):
    """Executes a strictly read-only SQL query against the database."""
    query = query.strip()
    # Security: Ensure it is a SELECT statement and doesn't contain destructive commands
    upper_query = query.upper()
    forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'EXEC', 'CREATE']
    
    # Very basic validation
    if not upper_query.startswith('SELECT'):
        return {"error": "Only SELECT queries are allowed for security reasons."}
        
    for kw in forbidden_keywords:
        if re.search(rf'\b{kw}\b', upper_query):
            return {"error": f"The '{kw}' keyword is forbidden in read-only mode."}

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            # Convert rows to a list of dicts
            result = [dict(zip(columns, row)) for row in rows]
            return result
    except Exception as e:
        return {"error": str(e)}


class LilianAI:
    @classmethod
    def ask(cls, user_query: str) -> dict:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your-gemini-api-key':
            return {
                "message": "GEMINI_API_KEY is missing or invalid in the .env file. Please add your key to use Lilian's Brain.",
                "data": [],
                "intent": "error"
            }

        client = genai.Client(api_key=api_key)
        schema = SchemaBuilder.get_schema()

        # Step 1: Ask Gemini to act as a SQL generator
        prompt1 = f"""
You are Lilian, a helpful AI inventory assistant handling a database query. 
Translate the following user question into a safe, read-only SQL SELECT query based on the SQLite schema below.

{schema}

User Question: "{user_query}"

If the question is completely unrelated to inventory (e.g. "how are you"), do not generate SQL. Just return a JSON with empty sql text.
If the question asks a broad question like "how many items", answer via SQL count or select.
Respond ONLY with a valid JSON object in this exact format (no markdown blocks around it):
{{
    "sql_query": "SELECT * FROM inventory_ai_inventoryitem LIMIT 15",
    "intent": "general_inquiry"
}}
"""
        
        try:
            # Generate the SQL via Gemini API
            response1 = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt1,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                )
            )
            
            resp_text = response1.text.strip()
            
            try:
                parsed = json.loads(resp_text)
                sql_query = parsed.get("sql_query", "")
                intent = parsed.get("intent", "general_inquiry")
            except json.JSONDecodeError:
                return {
                    "message": "I couldn't understand the database requirement for that query.",
                    "data": [],
                    "intent": "error"
                }

            # Step 2: Execute SQL (if provided)
            data_result = []
            if sql_query:
                db_result = execute_readonly_sql(sql_query)
                if isinstance(db_result, dict) and "error" in db_result:
                    data_result = db_result  # It's an error dict
                    sql_query = f"Error executing query: {db_result['error']}"
                else:
                    data_result = db_result
            
            # Step 3: Ask Gemini to format the final answer
            prompt2 = f"""
You are Lilian, a friendly and helpful AI inventory manager.
You just ran a database query to answer the user's question.

User Question: "{user_query}"
SQL Query Executed: {sql_query}
Database Result: {json.dumps(data_result, default=str)}

Based on the Database Result, answer the user's question naturally and conversationally. 
Do NOT show the SQL query to the user. Do NOT sound like a robot reading a table.
If the database result is empty, say that you couldn't find any products matching their criteria.
If the database result shows an error, apologize and say you encountered a SQL problem looking that up.
If there is no SQL query because it was a greeting or general chat, just respond normally and politely as an AI persona.
"""
            response2 = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt2,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                )
            )
            
            final_message = response2.text.strip()
            
            # If the data_result was an error dict, pass an empty list to frontend to avoid crashing React maps
            if isinstance(data_result, dict) and "error" in data_result:
                final_data = []
            else:
                final_data = data_result

            return {
                "message": final_message,
                "data": final_data,
                "intent": intent
            }

        except Exception as e:
            return {
                "message": f"I encountered an error connecting to my Gemini AI brain: {str(e)}",
                "data": [],
                "intent": "error"
            }
