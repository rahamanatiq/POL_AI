"""
urls.py - AI API URL Configuration
=====================================
Maps API endpoints to their view handlers.

URL Structure:
──────────────
/api/ai/chat/            → POST  → Main Lilian AI chat
/api/ai/history/         → GET   → Conversation history
"""

from django.urls import path
from .views import (
    AIChatView,
    AIConversationHistoryView,
)

app_name = 'inventory_ai'

urlpatterns = [
    # Primary chat endpoint — the frontend chatbox hits this
    path('chat/', AIChatView.as_view(), name='ai-chat'),

    # Conversation log
    path('history/', AIConversationHistoryView.as_view(), name='ai-history'),
]
