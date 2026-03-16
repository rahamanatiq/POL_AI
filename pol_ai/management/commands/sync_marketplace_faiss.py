from django.core.management.base import BaseCommand
from pol_ai.ai_service import FaissManager

class Command(BaseCommand):
    help = 'Synchronizes the FAISS vector index with current Marketplace items'

    def handle(self, *args, **options):
        self.stdout.write("Building FAISS index for Marketplace (this may take a few seconds)...")
        result = FaissManager.sync_index(index_type="marketplace")
        self.stdout.write(self.style.SUCCESS(result))
