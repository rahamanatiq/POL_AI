"""
apps.py - App Configuration
"""

from django.apps import AppConfig


class PolAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pol_ai'
    verbose_name = 'Lilian AI - Inventory Intelligence'

    def ready(self):
        import pol_ai.signals
