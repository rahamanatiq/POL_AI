"""
admin.py - Django Admin Configuration
========================================
Registers models in the admin panel for easy management and debugging.
"""

from django.contrib import admin
from .models import InventoryItem, AIConversationLog


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = [
        'brand', 'part_number', 'type', 'expiry_date',
        'status', 'company', 'batch_number',
    ]
    list_filter = ['status', 'type', 'company']
    search_fields = ['brand', 'part_number', 'company', 'batch_number']
    list_editable = ['status']
    ordering = ['expiry_date']
    date_hierarchy = 'expiry_date'


@admin.register(AIConversationLog)
class AIConversationLogAdmin(admin.ModelAdmin):
    list_display = ['user_query_short', 'intent_detected', 'created_at']
    list_filter = ['intent_detected', 'created_at']
    search_fields = ['user_query', 'ai_response']
    readonly_fields = ['user_query', 'ai_response', 'intent_detected', 'created_at']

    def user_query_short(self, obj):
        return obj.user_query[:80] + '...' if len(obj.user_query) > 80 else obj.user_query
    user_query_short.short_description = 'User Query'
