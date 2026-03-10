"""
Management Command: refresh_inventory_status
=============================================
Updates all inventory item statuses based on current date.
Run daily via cron: python manage.py refresh_inventory_status

Crontab example (runs daily at midnight):
    0 0 * * * cd /path/to/project && python manage.py refresh_inventory_status
"""

from django.core.management.base import BaseCommand
from inventory_ai.ai_service import LilianAI


class Command(BaseCommand):
    help = 'Refreshes inventory statuses (expired/near_expiry/healthy) based on current date'

    def handle(self, *args, **options):
        self.stdout.write('Starting inventory status refresh...')

        result = LilianAI.refresh_statuses()

        self.stdout.write(self.style.SUCCESS(
            f"Status refresh complete:\n"
            f"  → Updated to expired:    {result['updated_to_expired']}\n"
            f"  → Updated to near_expiry: {result['updated_to_near_expiry']}\n"
            f"  → Updated to healthy:     {result['updated_to_healthy']}\n"
            f"  → Timestamp: {result['timestamp']}"
        ))
