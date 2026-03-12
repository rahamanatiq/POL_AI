"""
models.py - Database Architecture for POL AI Tracking
======================================================
This file defines the SQL tables where we store product and marketplace data.
The Gemini AI directly reads these schemas to learn how to search for information.

InventoryItem -> Used by Lilian AI (Internal Inventory)
MarketplaceItem -> Used by Marie AI (External Selling/Buying)
"""

from django.db import models
from datetime import date, timedelta


class InventoryItem(models.Model):
    """
    Represents a single inventory product entry.
    Maps directly to the columns visible in the frontend Inventory table.
    """

    # Status choices matching the frontend badges (Healthy / Expired)
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('expired', 'Expired'),
        ('near_expiry', 'Near Expiry'),
    ]

    # Type choices for product classification
    TYPE_CHOICES = [
        ('petroleum', 'Petroleum'),
        ('lubricant', 'Lubricant'),
        ('chemical', 'Chemical'),
        ('gas', 'Gas'),
        ('other', 'Other'),
    ]

    brand = models.CharField(
        max_length=255,
        help_text="Product brand name, e.g., 'High-Grade Diesel'"
    )
    part_number = models.CharField(
        max_length=100,
        help_text="Unique part identifier, e.g., 'PD - 100'"
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        help_text="Product category type, e.g., 'Petroleum'"
    )
    usage_rate = models.CharField(
        max_length=100,
        help_text="Consumption rate, e.g., '500Liters'"
    )
    batch_number = models.CharField(
        max_length=100,
        help_text="Manufacturing batch ID, e.g., 'B-001'"
    )
    shelf_life = models.CharField(
        max_length=50,
        help_text="Expected shelf life duration, e.g., '5 years'"
    )
    expiry_date = models.DateField(
        help_text="Product expiration date"
    )
    company = models.CharField(
        max_length=255,
        help_text="Supplier/manufacturer company, e.g., 'Global Fuels Ltd'"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='healthy',
        help_text="Current product status: healthy, expired, or near_expiry"
    )

    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['expiry_date']
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'

    def __str__(self):
        return f"{self.brand} ({self.part_number}) - Expires: {self.expiry_date}"

    # ──────────────────────────────────────────────
    #  Helper properties used by the AI service
    # ──────────────────────────────────────────────

    @property
    def is_expired(self):
        """Check if the product has passed its expiry date."""
        return self.expiry_date < date.today()

    @property
    def is_near_expiry(self):
        """Check if the product expires within the next 30 days."""
        today = date.today()
        threshold = today + timedelta(days=30)
        return today <= self.expiry_date <= threshold

    @property
    def days_until_expiry(self):
        """Returns days until expiry. Negative means already expired."""
        return (self.expiry_date - date.today()).days

    def auto_update_status(self):
        """
        Automatically update the status field based on current date.
        Called by the AI service and can also be triggered via a cron job.
        """
        if self.is_expired:
            self.status = 'expired'
        elif self.is_near_expiry:
            self.status = 'near_expiry'
        else:
            self.status = 'healthy'
        self.save(update_fields=['status', 'updated_at'])
        return self.status


class MarketplaceItem(models.Model):
    """
    Represents an item listed on the marketplace for buying or selling.
    """
    CATEGORY_CHOICES = [
        ('petroleum', 'Petroleum'),
        ('oil', 'Oil'),
        ('lubricant', 'Lubricant'),
        ('other', 'Other'),
    ]

    TRANSACTION_CHOICES = [
        ('sell', 'Sell Only'),
        ('buy', 'Buy Only'),
    ]

    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    quantity = models.CharField(max_length=100)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    inventory_details = models.TextField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES, default='sell')
    status = models.CharField(max_length=20, default='Active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} - {self.price_per_unit}"

class AIConversationLog(models.Model):
    """
    Stores conversation history between users and Lilian AI.
    Useful for analytics and improving AI responses over time.
    """
    user_query = models.TextField(help_text="The question the user asked Lilian")
    ai_response = models.TextField(help_text="Lilian's response")
    intent_detected = models.CharField(
        max_length=100,
        blank=True,
        help_text="The intent category detected by the AI"
    )
    assistant_name = models.CharField(
        max_length=50,
        default='lilian',
        help_text="Which AI assistant handled this query (e.g., 'lilian' or 'marie')"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Q: {self.user_query[:50]}... | Intent: {self.intent_detected}"


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'), ('in_progress', 'In Progress'), 
        ('resolved', 'Resolved'), ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    admin_notes = models.TextField(blank=True)
    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            super().save(*args, **kwargs)
            self.ticket_id = f"TKT-{self.pk:04d}"
            self.save(update_fields=['ticket_id'])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.ticket_id}] {self.name} - {self.status}"
