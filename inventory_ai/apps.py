"""
apps.py - App Configuration
"""

from django.apps import AppConfig


class InventoryAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory_ai'
    verbose_name = 'Lilian AI - Inventory Intelligence'
