"""
urls.py - AI API URL Configuration
=====================================
Maps API endpoints to their view handlers.

URL Structure:
──────────────
/api/ai/chat/            → POST  → Main Lilian AI (FAISS RAG Powered)
/api/ai/marketplace-chat/ → POST  → Main Marie AI (FAISS RAG Powered)
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
    # Primary chat endpoints (FAISS RAG Powered)
    path('chat/', AIChatView.as_view(), name='ai-chat'),
    path('marketplace-chat/', MarketplaceChatView.as_view(), name='marketplace-chat'),

    # Conversation log
    path('history/<str:assistant>/', AIConversationHistoryView.as_view(), name='ai-history'),

    # Support Tickets
    path('tickets/', SupportTicketCreateView.as_view(), name='ticket-create'),
    path('tickets/admin/', AdminTicketView.as_view(), name='ticket-admin-list'),
    path('tickets/admin/<str:ticket_id>/', AdminTicketView.as_view(), name='ticket-admin-detail'),
]
