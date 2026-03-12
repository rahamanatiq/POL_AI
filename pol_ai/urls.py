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
    MarketplaceChatView,
    AIConversationHistoryView,
    SupportTicketCreateView,
    AdminTicketView,
)

app_name = 'pol_ai'

urlpatterns = [
    # Primary chat endpoint — the frontend chatbox hits this
    path('chat/', AIChatView.as_view(), name='ai-chat'),

    # Marketplace chat endpoint — Marie AI
    path('marketplace-chat/', MarketplaceChatView.as_view(), name='marketplace-chat'),

    # Conversation log
    path('history/<str:assistant>/', AIConversationHistoryView.as_view(), name='ai-history'),

    # Support Tickets
    path('tickets/', SupportTicketCreateView.as_view(), name='ticket-create'),
    path('tickets/admin/', AdminTicketView.as_view(), name='ticket-admin-list'),
    path('tickets/admin/<str:ticket_id>/', AdminTicketView.as_view(), name='ticket-admin-detail'),
]
