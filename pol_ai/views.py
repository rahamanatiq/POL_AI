"""
views.py - REST API Endpoints
=============================
This file bridges the gap between the React frontend and the backend AI engines.
The frontend sends HTTP requests here, and Django responds with JSON data.

Endpoints:
──────────
POST /api/ai/chat/                → Lilian AI chat (Inventory queries)
POST /api/ai/marketplace-chat/    → Marie AI chat  (Marketplace queries)
GET  /api/ai/marketplace-chat/    → Fetches Marie's welcome greeting before chat starts.
GET  /api/ai/history/<assistant>/ → Gets previous AI conversations for 'lilian' or 'marie'
"""

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .ai_service import LilianAI, MarieAI, RAGService, FaissRAGService
from .serializers import (
    AIQuerySerializer,
    AIResponseSerializer,
    AIConversationLogSerializer,
    SupportTicketSerializer,
    TicketStatusUpdateSerializer,
)
from .models import AIConversationLog, InventoryItem, SupportTicket

from datetime import date, timedelta
from django.db.models import Q


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 1: Main Chat API (The primary integration point)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@method_decorator(csrf_exempt, name='dispatch')
class AIChatView(APIView):
    """
    POST /api/ai/chat/

    The main endpoint for interacting with Lilian AI.
    Frontend sends a natural language query, and Lilian responds
    with analysis, product lists, and inventory insights.

    Request Body:
        {
            "query": "What products are expired?"
        }

    Response:
        {
            "success": true,
            "message": "I found 3 expired products...",
            "data": [...],          // product list or summary
            "intent": "expired_products",
            "count": 3,
            "query": "What products are expired?",
            "extracted_dates": {},
            "extracted_keywords": {"status": "expired"}
        }
    """
    permission_classes = [AllowAny]  # Change to [IsAuthenticated] in production
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai_chat'

    def post(self, request):
        # Step 1: Validate the request
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'Invalid request',
                    'details': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = serializer.validated_data['query']

        try:
            # Step 2: Process query through Lilian AI
            ai_response = LilianAI.ask(query)

            # Step 3: Log the conversation
            AIConversationLog.objects.create(
                user_query=query,
                ai_response=ai_response['message'],
                intent_detected=ai_response['intent'],
                assistant_name='lilian',
            )

            # Step 4: Serialize dates in data (convert date objects to strings)
            data = ai_response.get('data')
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, date):
                                item[key] = value.isoformat()

            # Step 5: Return the response
            return Response(
                {
                    'success': True,
                    **ai_response,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'AI processing error',
                    'details': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 1.5: RAG Chat API (Semantic Retrieval-Augmented)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@method_decorator(csrf_exempt, name='dispatch')
class RAGChatView(APIView):
    """
    POST /api/ai/rag-chat/

    The primary RAG endpoint using FAISS for semantic similarity.
    This provides 'fuzzy' intelligence based on meaning rather than just exact keywords.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai_chat'

    def post(self, request):
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'error': 'Invalid request', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data['query']

        try:
            # Use the advanced FAISS Semantic Service
            ai_response = FaissRAGService.ask(query)
            
            # Log the conversation (using assistant_name='lilian_rag')
            AIConversationLog.objects.create(
                user_query=query,
                ai_response=ai_response['message'],
                intent_detected=ai_response['intent'],
                assistant_name='lilian_rag',
            )

            return Response({'success': True, **ai_response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 2: Marketplace Chat API (Marie)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@method_decorator(csrf_exempt, name='dispatch')
class MarketplaceChatView(APIView):
    """
    POST /api/ai/marketplace-chat/
    GET /api/ai/marketplace-chat/ (Initial welcome message)

    The endpoint for interacting with Marie AI on the marketplace.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai_chat'

    def get(self, request):
        """Returns Marie's initial greeting before any conversation starts."""
        return Response({
            "success": True,
            "message": "I am Marie I can help you to find best buyers/ sellers for any specific product.",
            "data": [],
            "intent": "greeting"
        }, status=status.HTTP_200_OK)

    def post(self, request):
        # Step 1: Validate the request
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'Invalid request',
                    'details': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = serializer.validated_data['query']

        try:
            # Step 2: Process query through Marie AI
            ai_response = MarieAI.ask(query)

            # Step 3: Log the conversation (reusing the same log model)
            AIConversationLog.objects.create(
                user_query=query,
                ai_response=ai_response['message'],
                intent_detected=ai_response['intent'],
                assistant_name='marie',
            )

            # Step 4: Serialize dates in data (convert date objects to strings) if needed
            data = ai_response.get('data')
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, date):
                                item[key] = value.isoformat()

            # Step 5: Return the response
            return Response(
                {
                    'success': True,
                    **ai_response,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'AI processing error',
                    'details': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENDPOINT 3: Conversation History
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIConversationHistoryView(ListAPIView):
    """
    GET /api/ai/history/<assistant>/

    Returns the last 50 conversation entries for a specific assistant ('lilian' or 'marie').
    Supports query parameter filtering:
        ?intent=expired_products  → filter by intent
        ?limit=20                 → limit results
    """
    permission_classes = [AllowAny]
    serializer_class = AIConversationLogSerializer

    def get_queryset(self):
        assistant = self.kwargs.get('assistant')
        qs = AIConversationLog.objects.filter(assistant_name=assistant)

        intent = self.request.query_params.get('intent')
        if intent:
            qs = qs.filter(intent_detected=intent)

        limit = self.request.query_params.get('limit', 50)
        try:
            limit = int(limit)
        except ValueError:
            limit = 50

        return qs[:limit]


@method_decorator(csrf_exempt, name='dispatch')
class SupportTicketCreateView(APIView):
    """
    POST /api/ai/tickets/
    Public-facing. Users submit issues from the Contact Me form.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = SupportTicketSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        ticket = serializer.save()
        return Response({
            'success': True,
            'message': f'Ticket submitted successfully. Your reference ID is {ticket.ticket_id}.',
            'ticket_id': ticket.ticket_id,
            'data': SupportTicketSerializer(ticket).data,
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class AdminTicketView(APIView):
    """
    GET   /api/ai/tickets/admin/           → List all tickets (filter by ?status= ?priority= ?category=)
    PATCH /api/ai/tickets/admin/<id>/      → Update status and admin notes
    """
    permission_classes = [AllowAny]  # Change to IsAdminUser in production

    def get(self, request, ticket_id=None):
        if ticket_id:
            try:
                ticket = SupportTicket.objects.get(ticket_id=ticket_id)
                return Response({'success': True, 'data': SupportTicketSerializer(ticket).data})
            except SupportTicket.DoesNotExist:
                return Response({'success': False, 'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        qs = SupportTicket.objects.all()
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params.get('status'))
        serializer = SupportTicketSerializer(qs, many=True)
        return Response({'success': True, 'count': qs.count(), 'data': serializer.data})

    def patch(self, request, ticket_id=None):
        try:
            # Note: We now look up by the public ticket_id string (e.g. 'TKT-0001')
            ticket = SupportTicket.objects.get(ticket_id=ticket_id)
        except SupportTicket.DoesNotExist:
            return Response({'success': False, 'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TicketStatusUpdateSerializer(ticket, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({
            'success': True,
            'message': f'Ticket {ticket.ticket_id} updated.',
            'data': SupportTicketSerializer(ticket).data,
        })
