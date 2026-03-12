"""
serializers.py - API Serialization Layer
==========================================
Handles validation of incoming requests and formatting of outgoing responses.
"""

from rest_framework import serializers
from .models import InventoryItem, AIConversationLog, SupportTicket


class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Serializes InventoryItem model for API responses.
    Includes computed fields: is_expired, is_near_expiry, days_until_expiry.
    """
    is_expired = serializers.BooleanField(read_only=True)
    is_near_expiry = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'brand', 'part_number', 'type', 'usage_rate',
            'batch_number', 'shelf_life', 'expiry_date', 'company',
            'status', 'is_expired', 'is_near_expiry', 'days_until_expiry',
            'created_at', 'updated_at',
        ]


class AIQuerySerializer(serializers.Serializer):
    """
    Validates the incoming AI chat request.
    The frontend sends a JSON body like: { "query": "What products are expired?" }
    """
    query = serializers.CharField(
        max_length=1000,
        required=True,
        help_text="Natural language question for Lilian AI",
        error_messages={
            'required': 'Please provide a query for Lilian.',
            'blank': 'Query cannot be empty.',
            'max_length': 'Query is too long. Please keep it under 1000 characters.',
        }
    )


class AIResponseSerializer(serializers.Serializer):
    """
    Formats the AI response for the frontend.
    This is the structure the frontend will receive.
    """
    message = serializers.CharField(help_text="Lilian's text response")
    data = serializers.JSONField(
        allow_null=True,
        help_text="Structured data (products list or summary stats)"
    )
    intent = serializers.CharField(help_text="Detected intent category")
    count = serializers.IntegerField(help_text="Number of results")
    query = serializers.CharField(help_text="Original user query")
    extracted_dates = serializers.DictField(
        allow_empty=True,
        help_text="Dates extracted from the query"
    )
    extracted_keywords = serializers.DictField(
        allow_empty=True,
        help_text="Keywords extracted from the query"
    )


class AIConversationLogSerializer(serializers.ModelSerializer):
    """Serializer for conversation history."""
    class Meta:
        model = AIConversationLog
        fields = ['id', 'user_query', 'ai_response', 'intent_detected', 'created_at']
        read_only_fields = ['id', 'created_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_id', 'name', 'email', 'description',
            'status', 'admin_notes', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'ticket_id', 'status', 'admin_notes', 'created_at', 'updated_at'
        ]


class TicketStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ['status', 'admin_notes']
