"""
urls.py - AI API URL Configuration
=====================================
Maps API endpoints to their view handlers.

URL Structure:
──────────────
/api/ai/chat/            → POST  → Main Lilian AI chat
/api/ai/status/          → GET   → Quick inventory status
/api/ai/refresh-status/  → POST  → Batch status update
/api/ai/history/         → GET   → Conversation history
/api/ai/health/          → GET   → Service health check
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
