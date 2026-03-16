import os
import django
import json
from google import genai

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pol_ai.ai_service import FaissManager
from pol_ai.models import AIConversationLog

def debug_marie_prompt(user_query):
    api_key = os.getenv('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)
    
    context_data = FaissManager.search(user_query, k=10, index_type="marketplace")
    context_text = json.dumps(context_data, indent=2)
    
    recent_logs = AIConversationLog.objects.filter(assistant_name='marie_faiss').order_by('-created_at')[:3]
    history_text = "RECENT CONVERSATION HISTORY:\n"
    if recent_logs.exists():
        for log in reversed(recent_logs):
            history_text += f"- User: {log.user_query}\n- You: {log.ai_response}\n\n"
    else:
        history_text += "No recent history.\n"
        
    prompt = f"""
You are Marie, a friendly and experienced Marketplace Assistant.
Your core goal is to help users find products for sale or analyze marketplace data using the SEMANTIC CONTEXT provided below.

SEMANTIC CONTEXT (Most relevant marketplace items):
{context_text}

{history_text}

USER QUESTION: "{user_query}"

INSTRUCTIONS:
- If the user is just saying hello or asking a general greeting, you can respond politely without using the context.
- Answer the user's question directly based on the SEMANTIC CONTEXT provided. Be smart about Recognizing synonyms (e.g. "jet fuel" = "aviation fuel") and correcting typos.
- CRITICAL MARKETPLACE LOGIC:
  * If the user says "I want to BUY" or "Looking for", you MUST find listings in the context where `Type` is "sell" (these are the sellers).
  * If the user says "I want to SELL" or "Offering", you MUST find listings in the context where `Type` is "buy" (these are the buyers).
- MATHEMATICAL COMPARISON:
  * If the user asks for the "best", "cheapest", "lowest price", or "best seller", do NOT look for these words in the text.
  * Instead, look at the `price_per_unit` numbers of all valid matches in the context and identify which one has the lowest number.
  * Explicitly state the price and seller details for the best option found.
- If the user asks a yes/no question (e.g., "is there any X"), confirm if it exists in the valid context and provide a brief description.
- If the context does not contain what the user asked for (even considering synonyms), gracefully inform them that no matching buyers/sellers were found for that specific request.
- STRICTLY do not volunteer extra information not asked for.
- Do NOT mention that you are using Semantic Search or any underlying search technology.
"""
    print("--- PROMPT START ---")
    print(prompt)
    print("--- PROMPT END ---")
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
    )
    print("\n--- RESPONSE ---")
    print(response.text.strip())

debug_marie_prompt("i want to buy Transmission Fluid. give me best seller")
