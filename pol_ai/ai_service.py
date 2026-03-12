"""
ai_service.py - The Core AI Engine for POL Tracking System
===========================================================
This file contains the "brains" for our two AI assistants: Lilian and Marie.

How the Text-to-SQL Architecture Works:
1. The user asks a question in plain English (e.g. "What products are expired?").
2. The AI reads our database schema (e.g. `SchemaBuilder.get_schema()`).
3. The AI translates the English question into a valid, read-only SQLite query.
4. Django executes that query (`execute_readonly_sql`) securely against our database.
5. The AI takes the database results (the raw data) and formats a nice, human-readable summary.

This approach allows the AI to accurately search thousands of products without hallucinating!
"""

import os
import json
import re
from datetime import date
from django.db import connection
from google import genai
from google.genai import types
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

class SchemaBuilder:
    @staticmethod
    def get_schema():
        brands = "'High-Grade Diesel'"
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT DISTINCT brand FROM pol_ai_inventoryitem LIMIT 5')
                fetched = [f"'{row[0]}'" for row in cursor.fetchall() if row[0]]
                if fetched: brands = ", ".join(fetched)
        except Exception:
            pass
            
        return f"""
Table: pol_ai_inventoryitem
Description: Stores all inventory products and their metadata.
Columns:
- id (Integer, Primary Key)
- brand (String): Product brand name (Known brands in DB: {brands})
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

*CRITICAL INSTRUCTION FOR EXPIRY DATES*:
The backend server rigidly calculates whether a product is "expired", "near_expiry", or "healthy" and saves that explicitly as a string in the `status` column. 
Whenever the user asks about expired products, healthy products, or products nearing expiration, you MUST query the `status` column rather than writing your own SQL date-math.
"""

class MarketplaceSchemaBuilder:
    @staticmethod
    def get_schema():
        product_names = "'Surplus Aviation Fuel'"
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT DISTINCT product_name FROM pol_ai_marketplaceitem LIMIT 5')
                fetched = [f"'{row[0]}'" for row in cursor.fetchall() if row[0]]
                if fetched: product_names = ", ".join(fetched)
        except Exception:
            pass

        return f"""
Table: pol_ai_marketplaceitem
Description: Stores marketplace items for buying and selling.
Columns:
- id (Integer, Primary Key)
- product_name (String): Name of the product (Known products in DB: {product_names})
- category (String): Product category (petroleum, oil, lubricant, other)
- quantity (String): Quantity available (e.g., '5000 Gal')
- price_per_unit (Decimal): Price per unit (e.g., 2.10)
- location (String): Storage location (e.g., 'Hangar 4')
- inventory_details (String): Additional details about the item
- transaction_type (String): Whether it is for 'sell' or 'buy'
- status (String): Current status (e.g., 'Active')
- created_at (DateTime)
- updated_at (DateTime)

Current Date: {date.today().isoformat()}

CRITICAL QUERY INSTRUCTIONS:
1. Always use `LIKE` instead of `=` for `product_name` or `inventory_details` (e.g., `product_name LIKE '%Jet-A%'`).
2. If looking for the "best" or "cheapest" seller or price, search where `transaction_type = 'sell'` and `ORDER BY price_per_unit ASC LIMIT 1`.
3. If looking for a buyer who wants a product, search where `transaction_type = 'buy'`.
4. When searching for a product category, use `LIKE` (e.g. `category LIKE '%petroleum%'`).
"""

def execute_readonly_sql(query: str):
    """Executes a strictly read-only SQL query against the database."""
    query = query.strip()
    
    # 1. Text-based filtering (First line of defense)
    upper_query = query.upper()
    if not upper_query.startswith('SELECT'):
        return {"error": "Only SELECT queries are allowed for security reasons."}
        
    forbidden = ['INSERT ', 'UPDATE ', 'DELETE ', 'DROP ', 'ALTER ', 'TRUNCATE ', 'EXEC ', 'CREATE ', 'REPLACE ']
    for kw in forbidden:
        if kw in upper_query:
            return {"error": f"The '{kw.strip()}' keyword is forbidden in read-only mode."}

    # 2. Database-level execution
    try:
        with connection.cursor() as cursor:
            # If using SQLite, strictly enforce query_only PRAGMA mode for this transaction
            if connection.vendor == 'sqlite':
                cursor.execute('PRAGMA query_only = ON;')
                
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
            # Reset PRAGMA just in case connection is reused
            if connection.vendor == 'sqlite':
                cursor.execute('PRAGMA query_only = OFF;')
                
            # Convert rows to a list of dicts
            return [dict(zip(columns, row)) for row in rows]
            
    except Exception as e:
        # Guarantee PRAGMA is reset even on failure
        try:
            if connection.vendor == 'sqlite':
                with connection.cursor() as cursor:
                    cursor.execute('PRAGMA query_only = OFF;')
        except:
            pass
        return {"error": str(e)}


class LilianAI:
    """
    Lilian is the AI assistant for the main Inventory Tracking page.
    She knows about the `pol_ai_inventoryitem` table (products, shelf life, usage rates).
    """
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

        try:
            # Step 1 & 2: Generate and Execute SQL with Auto-Correction Retry Loop
            max_retries = 3
            attempt = 0
            sql_query = ""
            intent = "general_inquiry"
            data_result = []
            error_history = ""

            while attempt < max_retries:
                prompt1 = f"""
You are Lilian, a helpful AI inventory assistant handling a database query. 
Translate the following user question into a safe, read-only SQL SELECT query based on the SQLite schema below.

{schema}

User Question: "{user_query}"

If the question is completely unrelated to inventory (e.g. "how are you"), do not generate SQL. Just return a JSON with empty sql text.
If the question asks a broad question like "how many items", answer via SQL count or select.
Respond ONLY with a valid JSON object in this exact format (no markdown blocks around it):
{{
    "sql_query": "SELECT * FROM pol_ai_inventoryitem LIMIT 15",
    "intent": "general_inquiry"
}}
{error_history}
"""
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

                if not sql_query:
                    # Not a database-related question or no SQL generated. Break out.
                    data_result = []
                    break

                # Execute SQL
                db_result = execute_readonly_sql(sql_query)
                
                if isinstance(db_result, dict) and "error" in db_result:
                    # We hit an error (e.g. column not found, typo in SQL)
                    error_msg = db_result["error"]
                    error_history += f"\n\nERROR ON PREVIOUS ATTEMPT: You generated this SQL: `{sql_query}` which failed with error: `{error_msg}`. Please correct your SQL syntax or column names and try again. DO NOT output the same broken SQL."
                    data_result = db_result # Keep the error in case we run out of retries
                    attempt += 1
                else:
                    # Success!
                    data_result = db_result
                    break

            # Step 3: Ask Gemini to format the final answer
            # We decouple the data to avoid token limits by only showing the length and a tiny sample
            total_items = len(data_result) if isinstance(data_result, list) else 0
            sample_data = data_result[:5] if isinstance(data_result, list) else data_result
            
            prompt2 = f"""
You are Lilian, a highly efficient AI inventory manager.
You just ran a database query to answer the user's question.

User Question: "{user_query}"
SQL Query Executed: {sql_query}
Total Items Found in DB: {total_items}
Database Result Sample (first 5 items): {json.dumps(sample_data, default=str)}

Based on the Total Items Found and the Sample Data, provide a CONCISE and CLEAR summary answer to the user.
- The raw data will be displayed to the user in a beautiful table right next to your chat bubble.
- Therefore, DO NOT list out the individual products, brands, parts, or rows in your message.
- Instead, ONLY provide a high-level, single-sentence summary (e.g., "I found 3 expired petroleum products. Here they are:").
- Do NOT show the SQL query to the user.
- If the database result is empty, briefly state that no matching products were found.
- If the database result shows an error, concisely apologize and mention that a database error prevented you from finding the answer.
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

class MarieAI:
    """
    Marie is the AI broker for the Marketplace page.
    She knows about the `pol_ai_marketplaceitem` table (buyers, sellers, prices).
    """
    @classmethod
    def ask(cls, user_query: str) -> dict:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your-gemini-api-key':
            return {
                "message": "GEMINI_API_KEY is missing or invalid in the .env file. Please add your key to use Marie's Brain.",
                "data": [],
                "intent": "error"
            }

        client = genai.Client(api_key=api_key)
        schema = MarketplaceSchemaBuilder.get_schema()

        try:
            # Step 1 & 2: Generate and Execute SQL with Auto-Correction Retry Loop
            max_retries = 3
            attempt = 0
            sql_query = ""
            intent = "marketplace_inquiry"
            data_result = []
            error_history = ""

            while attempt < max_retries:
                prompt1 = f"""
You are Marie, an expert AI Marketplace broker. 
Translate the following user question into a safe, read-only SQL SELECT query based on the SQLite schema below.

{schema}

User Question: "{user_query}"

If the question is completely unrelated to the marketplace/buying/selling (e.g. "how are you"), do not generate SQL. Just return a JSON with empty sql text.
Respond ONLY with a valid JSON object in this exact format (no markdown blocks around it):
{{
    "sql_query": "SELECT * FROM pol_ai_marketplaceitem LIMIT 15",
    "intent": "marketplace_inquiry"
}}
{error_history}
"""
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
                    intent = parsed.get("intent", "marketplace_inquiry")
                except json.JSONDecodeError:
                    return {
                        "message": "I couldn't understand the database requirement for that query.",
                        "data": [],
                        "intent": "error"
                    }

                if not sql_query:
                    # Not a database-related question or no SQL generated. Break out.
                    data_result = []
                    break

                # Execute SQL
                db_result = execute_readonly_sql(sql_query)
                
                if isinstance(db_result, dict) and "error" in db_result:
                    # We hit an error
                    error_msg = db_result["error"]
                    error_history += f"\n\nERROR ON PREVIOUS ATTEMPT: You generated this SQL: `{sql_query}` which failed with error: `{error_msg}`. Please correct your SQL syntax or column names and try again. DO NOT output the same broken SQL."
                    data_result = db_result # Keep the error in case we run out of retries
                    attempt += 1
                else:
                    # Success!
                    data_result = db_result
                    break

            # Step 3: Ask Gemini to format the final answer
            # We decouple the data to avoid token limits by only showing the length and a tiny sample
            total_items = len(data_result) if isinstance(data_result, list) else 0
            sample_data = data_result[:5] if isinstance(data_result, list) else data_result
            
            prompt2 = f"""
You are Marie, a highly efficient AI marketplace broker.
You just ran a database query to answer the user's question about the marketplace.

User Question: "{user_query}"
SQL Query Executed: {sql_query}
Total Items Found in DB: {total_items}
Database Result Sample (first 5 items): {json.dumps(sample_data, default=str)}

Based on the Total Items Found and the Sample Data, provide a STRUCTURED and CLEAR summary answer to the user.

- The raw data will also be displayed to the user in a table right next to your chat bubble, so DO NOT list out the individual products, prices, or rows in your message.
- Instead, ONLY provide a high-level, single-sentence summary (e.g., "I found 3 matching products available for sale. Here they are:").
- Do NOT show the SQL query to the user.
- If the database result is empty, briefly state that no matching products were found on the marketplace.
- If the database result shows an error, concisely apologize and mention that a database error prevented you from searching the market.
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

class RAGService:
    """
    RAGService handles queries using Retrieval-Augmented Generation.
    It retrieves relevant context from the database and uses it to augment the AI prompt.
    This is less rigid than Text-to-SQL and better for fuzzy or descriptive queries.
    """
    @classmethod
    def ask(cls, user_query: str) -> dict:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return {"message": "API Key missing.", "data": [], "intent": "error"}

        client = genai.Client(api_key=api_key)
        
        try:
            # 1. RETRIEVAL (The "R" in RAG)
            # In a production system, you'd use a Vector DB (Chroma, Pinecone).
            # For this implementation, we use a broad keyword search to pull relevant context.
            keywords = user_query.split()
            query_filter = Q()
            for kw in keywords:
                if len(kw) > 2:
                    query_filter |= Q(brand__icontains=kw) | Q(type__icontains=kw) | Q(company__icontains=kw)
            
            # Fetch top 10 relevant items
            from .models import InventoryItem
            items = InventoryItem.objects.filter(query_filter)[:10]
            
            # If keyword search fails, fall back to recent items to provide some context
            if not items.exists():
                items = InventoryItem.objects.all().order_by('-created_at')[:5]

            # 2. AUGMENTATION (The "A" in RAG)
            context_data = []
            for item in items:
                context_data.append({
                    "brand": item.brand,
                    "type": item.type,
                    "status": item.status,
                    "expiry_date": str(item.expiry_date),
                    "company": item.company
                })

            context_text = json.dumps(context_data, indent=2)

            # 3. GENERATION (The "G" in RAG)
            prompt = f"""
You are an Inventory AI using RAG (Retrieval-Augmented Generation).
Use the provided DATABASE CONTEXT to answer the user's question. 

DATABASE CONTEXT:
{context_text}

USER QUESTION: "{user_query}"

INSTRUCTIONS:
- Answer ONLY based on the context provided above.
- If the answer isn't in the context, say "I don't have enough information in my current retrieval set to answer that accurately."
- Be helpful and concise.
"""
            response = client.models.generate_content(
                model='gemini-2.0-flash', # Using 2.0-flash for speed/efficiency
                contents=prompt,
            )

            return {
                "message": response.text.strip(),
                "data": context_data,
                "intent": "rag_query"
            }

        except Exception as e:
            return {
                "message": f"RAG Error: {str(e)}",
                "data": [],
                "intent": "error"
            }

class FaissManager:
    """
    Manages the FAISS vector index and metadata for semantic search.
    """
    INDEX_FILE = "vector_index.faiss"
    METADATA_FILE = "vector_metadata.json"

    @classmethod
    def get_client(cls):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return None
        return genai.Client(api_key=api_key)

    @classmethod
    def generate_embeddings(cls, texts):
        client = cls.get_client()
        if not client:
            return None
        
        # Use Gemini Embedding API
        response = client.models.embed_content(
            model='gemini-embedding-001',
            contents=texts,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return [item.values for item in response.embeddings]

    @classmethod
    def sync_index(cls):
        """Forces a rebuild of the FAISS index from the database."""
        from .models import InventoryItem
        items = InventoryItem.objects.all()
        if not items.exists():
            return "No items to index."

        # 1. Prepare texts for embedding
        texts = []
        metadata = []
        for item in items:
            text = f"Brand: {item.brand}, Type: {item.type}, Company: {item.company}, Status: {item.status}, Part: {item.part_number}"
            texts.append(text)
            metadata.append({
                "id": item.id,
                "brand": item.brand,
                "type": item.type,
                "company": item.company,
                "status": item.status,
                "expiry_date": str(item.expiry_date)
            })

        # 2. Get embeddings
        embeddings = cls.generate_embeddings(texts)
        if not embeddings:
            return "Failed to generate embeddings."

        # 3. Build FAISS index
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings).astype('float32'))

        # 4. Save index and metadata
        faiss.write_index(index, cls.INDEX_FILE)
        with open(cls.METADATA_FILE, 'w') as f:
            json.dump(metadata, f)

        return f"Successfully indexed {len(texts)} items."

    @classmethod
    def search(cls, query, k=5):
        """Searches the FAISS index for the top k similar items."""
        if not os.path.exists(cls.INDEX_FILE) or not os.path.exists(cls.METADATA_FILE):
            return []

        client = cls.get_client()
        if not client:
            return []

        # 1. Embed the query
        query_embedding = client.models.embed_content(
            model='gemini-embedding-001',
            contents=[query],
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        ).embeddings[0].values

        # 2. Search FAISS
        index = faiss.read_index(cls.INDEX_FILE)
        D, I = index.search(np.array([query_embedding]).astype('float32'), k)

        # 3. Load Metadata
        with open(cls.METADATA_FILE, 'r') as f:
            metadata = json.load(f)

        results = []
        for idx in I[0]:
            if idx != -1 and idx < len(metadata):
                results.append(metadata[idx])
        
        return results

class FaissRAGService:
    """
    RAGService using FAISS for semantic similarity search.
    """
    @classmethod
    def ask(cls, user_query: str) -> dict:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return {"message": "API Key missing.", "data": [], "intent": "error"}

        client = genai.Client(api_key=api_key)

        try:
            # 1. SEMANTIC RETRIEVAL via FAISS
            context_data = FaissManager.search(user_query, k=10)
            
            if not context_data:
                # Fallback to keyword search if FAISS index is empty
                return RAGService.ask(user_query)

            context_text = json.dumps(context_data, indent=2)

            # 2. AUGMENTED GENERATION
            prompt = f"""
You are an Inventory AI using FAISS Semantic RAG.
Use the provided SEMANTIC CONTEXT to answer the user's question.

SEMANTIC CONTEXT (Most relevant items):
{context_text}

USER QUESTION: "{user_query}"

INSTRUCTIONS:
- Answer ONLY based on the semantic context provided.
- If the answer isn't in the context, say "I couldn't find semantically similar items to answer that."
- Mention that you are using Semantic Search in your response.
"""
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )

            return {
                "message": response.text.strip(),
                "data": context_data,
                "intent": "faiss_rag_query"
            }

        except Exception as e:
            return {
                "message": f"FAISS RAG Error: {str(e)}",
                "data": [],
                "intent": "error"
            }
