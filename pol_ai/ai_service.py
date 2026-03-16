"""
ai_service.py - The Core AI Engine for POL Tracking System
===========================================================
This file contains the "brains" for our two AI assistants: Lilian and Marie.

Architecture: FAISS-based Retrieval-Augmented Generation (RAG)
1. The user asks a question in plain English.
2. The system retrieves relevant database context using FAISS semantic search.
3. The AI (Gemini) uses the retrieved context and conversation history to provide a concise answer.
"""

import os
import json
import re
from datetime import date
from django.db import connection
from django.db.models import Q
from google import genai
from google.genai import types
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

# Legacy RAG with keyword search (Internal fallback)
class RAGService:
    """
    RAGService handles queries using basic keyword retrieval.
    Useful as a lightweight fallback if FAISS is unavailable.
    """
    @classmethod
    def ask(cls, user_query: str) -> dict:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return {"message": "API Key missing.", "data": [], "intent": "error"}

        client = genai.Client(api_key=api_key)
        
        try:
            # RETRIEVAL: Basic keyword search
            keywords = user_query.split()
            query_filter = Q()
            for kw in keywords:
                if len(kw) > 2:
                    query_filter |= Q(product_name__icontains=kw) | Q(pol_type__icontains=kw) | Q(part_number__icontains=kw) | Q(description__icontains=kw)
            
            from .models import POLItem
            items = POLItem.objects.filter(query_filter)[:10]
            
            if not items.exists():
                items = POLItem.objects.all().order_by('-created_at')[:5]

            context_data = []
            for item in items:
                context_data.append({
                    "product_name": item.product_name,
                    "part_number": item.part_number,
                    "pol_type": item.pol_type,
                    "quantity": str(item.quantity),
                    "uom": item.uom,
                    "status": item.status,
                    "expiry": str(item.expiry),
                    "condition": item.condition,
                    "price_per_unit": float(item.price_per_unit),
                    "description": item.description,
                    "notes": item.notes
                })

            context_text = json.dumps(context_data, indent=2)

            prompt = f"""
You are an Inventory AI assistant (Lilian).
Use the provided context to answer the user's question. 

CONTEXT:
{context_text}

USER QUESTION: "{user_query}"

INSTRUCTIONS:
- Be helpful and concise.
- If the answer isn't in the context, politely state that you couldn't find relevant information.
"""
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )

            return {
                "message": response.text.strip(),
                "data": context_data,
                "intent": "keyword_rag_query"
            }

        except Exception as e:
            return {
                "message": f"Keyword RAG Error: {str(e)}",
                "data": [],
                "intent": "error"
            }

class FaissManager:
    """
    Manages the FAISS vector index and metadata for semantic search.
    """
    @classmethod
    def get_index_paths(cls, index_type="inventory"):
        if index_type == "marketplace":
            return "marketplace_vector_index.faiss", "marketplace_vector_metadata.json"
        return "inventory_vector_index.faiss", "inventory_vector_metadata.json"

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
    def sync_index(cls, index_type="inventory"):
        """Forces a rebuild of the FAISS index from the database for a specific type."""
        from .models import POLItem, Listing
        
        index_file, metadata_file = cls.get_index_paths(index_type)

        if index_type == "marketplace":
            items = Listing.objects.all()
        else:
            items = POLItem.objects.all()
            
        if not items.exists():
            return f"No {index_type} items to index."

        # 1. Prepare texts for embedding
        texts = []
        metadata = []
        for item in items:
            if index_type == "marketplace":
                text = (
                    f"Listing: {item.name}, Company: {item.company}, "
                    f"Type: {item.pol_type}, Category: {item.category}, "
                    f"Price: {item.price} {item.price_unit}, Quantity: {item.quantity} {item.quantity_unit}, "
                    f"Location: {item.location}, Brand: {item.brand}, Status: {item.status}, "
                    f"Description: {item.description}, Expiry: {item.expiry}, Rating: {item.rating}"
                )
                metadata.append({
                    "id": item.id,
                    "name": item.name,
                    "company": item.company,
                    "pol_type": item.pol_type,
                    "category": item.category,
                    "price": float(item.price) if item.price else 0,
                    "price_unit": item.price_unit,
                    "quantity": float(item.quantity),
                    "quantity_unit": item.quantity_unit,
                    "location": item.location,
                    "brand": item.brand,
                    "status": item.status,
                    "description": item.description,
                    "rating": float(item.rating) if item.rating else 0
                })
            else:
                text = (
                    f"Product: {item.product_name}, Part: {item.part_number}, "
                    f"Type: {item.pol_type}, UOM: {item.uom}, Quantity: {item.quantity}, "
                    f"Condition: {item.condition}, Expiry: {item.expiry}, "
                    f"Description: {item.description}, MilSpec: {item.mil_spec}, "
                    f"Source: {item.source}, Status: {item.status}, Notes: {item.notes}"
                )
                metadata.append({
                    "id": item.id,
                    "product_name": item.product_name,
                    "part_number": item.part_number,
                    "pol_type": item.pol_type,
                    "uom": item.uom,
                    "quantity": float(item.quantity),
                    "condition": item.condition,
                    "expiry": str(item.expiry),
                    "description": item.description,
                    "mil_spec": item.mil_spec,
                    "source": item.source,
                    "status": item.status,
                    "notes": item.notes,
                    "price_per_unit": float(item.price_per_unit)
                })
            texts.append(text)

        # 2. Get embeddings
        embeddings = cls.generate_embeddings(texts)
        if not embeddings:
            return "Failed to generate embeddings."

        # 3. Build FAISS index
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings).astype('float32'))

        # 4. Save index and metadata
        faiss.write_index(index, index_file)
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        return f"Successfully indexed {len(texts)} {index_type} items."

    @classmethod
    def search(cls, query, k=5, index_type="inventory"):
        """Searches the appropriate FAISS index for the top k similar items."""
        index_file, metadata_file = cls.get_index_paths(index_type)

        if not os.path.exists(index_file) or not os.path.exists(metadata_file):
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
        index = faiss.read_index(index_file)
        D, I = index.search(np.array([query_embedding]).astype('float32'), k)

        # 3. Load Metadata
        with open(metadata_file, 'r') as f:
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
                # Fallback to recent items if FAISS index is empty
                from .models import POLItem
                items = POLItem.objects.all().order_by('-created_at')[:5]
                context_data = [
                    {
                        "product_name": i.product_name, "part_number": i.part_number, 
                        "pol_type": i.pol_type, "quantity": float(i.quantity), 
                        "status": i.status, "expiry": str(i.expiry)
                    } for i in items
                ]

            context_text = json.dumps(context_data, indent=2)

            # Fetch Conversation History
            from .models import AIConversationLog
            recent_logs = AIConversationLog.objects.filter(assistant_name='lilian_rag').order_by('-created_at')[:5]
            history_text = "RECENT CONVERSATION HISTORY:\n"
            if recent_logs.exists():
                for log in reversed(recent_logs):
                    history_text += f"- User: {log.user_query}\n- You: {log.ai_response}\n\n"
            else:
                history_text += "No recent history.\n"

            # 2. AUGMENTED GENERATION
            prompt = f"""
You are Lilian, the Inventory AI using FAISS Semantic RAG.
Use the provided SEMANTIC CONTEXT and RECENT CONVERSATION HISTORY to answer the user's question.

SEMANTIC CONTEXT (Most relevant items):
{context_text}

{history_text}

USER QUESTION: "{user_query}"

INSTRUCTIONS:
- PRIORITY: If the user asks a follow-up question or refers to a previous topic (e.g., using "it", "them", "those", "that"), use the RECENT CONVERSATION HISTORY to identify what they are talking about.
- Answer the user's question directly using the provided SEMANTIC CONTEXT. Be smart about recognizing synonyms (e.g. "jet fuel" = "aviation fuel") and correcting typos.
- If the user is just saying hello or asking a general greeting, respond politely without using the context.
- If the user asks a yes/no question, confirm if it exists in the context and provide a brief detail.
- If the user asks ONLY for a count, ONLY provide the number without listing details.
- If asked to list products, do so in a clear, structured format.
- STRICTLY do not volunteer extra information not asked for (e.g., don't list products if they only asked "how many").
- Do NOT mention that you are using Semantic Search or any underlying search technology.
- If the context does not contain what the user asked for at all (even considering typos and synonyms), say "I couldn't find relevant items for that query."
"""
            response = client.models.generate_content(
                model='gemini-2.5-flash',
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

class MarketplaceFaissRAGService:
    """
    RAGService using FAISS tailored for Marie and the Marketplace.
    """
    @classmethod
    def ask(cls, user_query: str) -> dict:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return {"message": "API Key missing.", "data": [], "intent": "error"}

        client = genai.Client(api_key=api_key)

        try:
            # 1. SEMANTIC RETRIEVAL via FAISS
            context_data = FaissManager.search(user_query, k=10, index_type="marketplace")
            
            if not context_data:
                # Fallback to recent marketplace listings if context is empty
                from .models import Listing
                items = Listing.objects.all().order_by('-created_at')[:5]
                context_data = [
                    {
                        "id": i.id, "name": i.name, "company": i.company, "pol_type": i.pol_type,
                        "price": float(i.price) if i.price else 0, "quantity": float(i.quantity),
                        "category": i.category, "status": i.status
                    } for i in items
                ]

            context_text = json.dumps(context_data, indent=2)

            # Fetch Conversation History
            from .models import AIConversationLog
            recent_logs = AIConversationLog.objects.filter(assistant_name='marie_faiss').order_by('-created_at')[:5]
            history_text = "RECENT CONVERSATION HISTORY:\n"
            if recent_logs.exists():
                for log in reversed(recent_logs):
                    history_text += f"- User: {log.user_query}\n- You: {log.ai_response}\n\n"
            else:
                history_text += "No recent history.\n"

            # 2. AUGMENTED GENERATION
            prompt = f"""
You are Marie, a friendly and experienced Marketplace Assistant.
Your core goal is to help users find products for sale or analyze marketplace data using the SEMANTIC CONTEXT provided below.

SEMANTIC CONTEXT (Most relevant marketplace items):
{context_text}

{history_text}

USER QUESTION: "{user_query}"

INSTRUCTIONS:
- PRIORITY: If the user asks a follow-up question or refers back to something (e.g., "what about it?", "show me those"), look at the RECENT CONVERSATION HISTORY to understand the context.
- Answer the user's question directly based on the SEMANTIC CONTEXT provided. Be smart about Recognizing synonyms (e.g. "jet fuel" = "aviation fuel") and correcting typos.
- If the user is just saying hello or asking a general greeting, respond politely without using the context.
- CRITICAL MARKETPLACE LOGIC:
  * If the user says "I want to BUY" or "Looking for", you MUST find listings in the context where `category` is "sell" (these are the sellers).
  * If the user says "I want to SELL" or "Offering", you MUST find listings in the context where `category` is "buy" (these are the buyers).
- MATHEMATICAL COMPARISON:
  * If the user asks for the "best", "cheapest", "lowest price", or "best seller", do NOT look for these words in the text.
  * Instead, look at the `price` numbers of all valid matches in the context and identify which one has the lowest number.
  * Explicitly state the price and seller details for the best option found.
- If the user asks a yes/no question (e.g., "is there any X"), confirm if it exists in the valid context and provide a brief description.
- If the context does not contain what the user asked for (even considering synonyms), gracefully inform them that no matching buyers/sellers were found for that specific request.
- STRICTLY do not volunteer extra information not asked for.
- Do NOT mention that you are using Semantic Search or any underlying search technology.
"""
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )

            return {
                "message": response.text.strip(),
                "data": context_data,
                "intent": "marketplace_faiss_rag_query"
            }

        except Exception as e:
            return {
                "message": f"Marketplace FAISS Error: {str(e)}",
                "data": [],
                "intent": "error"
            }
