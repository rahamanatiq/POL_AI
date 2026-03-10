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
    AIStatusView,
    AIRefreshStatusView,
    AIConversationHistoryView,
    AIHealthCheckView,
)

app_name = 'inventory_ai'

urlpatterns = [
    # Primary chat endpoint — the frontend chatbox hits this
    path('chat/', AIChatView.as_view(), name='ai-chat'),

    # Dashboard status widget
    path('status/', AIStatusView.as_view(), name='ai-status'),

    # Batch refresh (call daily or on-demand)
    path('refresh-status/', AIRefreshStatusView.as_view(), name='ai-refresh-status'),

    # Conversation log
    path('history/', AIConversationHistoryView.as_view(), name='ai-history'),

    # Health check
    path('health/', AIHealthCheckView.as_view(), name='ai-health'),
]
