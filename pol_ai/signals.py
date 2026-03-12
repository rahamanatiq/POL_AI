from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import InventoryItem
from .ai_service import FaissManager
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=InventoryItem)
@receiver(post_delete, sender=InventoryItem)
def auto_sync_faiss(sender, instance, **kwargs):
    """
    Automatically triggers a FAISS index sync whenever an InventoryItem 
    is created, updated, or deleted.
    """
    try:
        # Rebuild the index
        # Note: In a large production system, you'd offload this to a background worker (Celery)
        result = FaissManager.sync_index()
        logger.info(f"FAISS Auto-Sync: {result}")
    except Exception as e:
        logger.error(f"FAISS Auto-Sync Error: {str(e)}")
