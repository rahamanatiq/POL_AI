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
        blank=True,
        default='',
        help_text="Product brand name, e.g., 'High-Grade Diesel'"
    )
    part_number = models.CharField(
        max_length=100,
        help_text="Unique part identifier, e.g., 'PD - 100'"
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Short description of the product"
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        help_text="Product category type, e.g., 'Petroleum'"
    )
    uom = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Unit of measure, e.g., 'Gallon', 'Liter'"
    )
    stock = models.IntegerField(
        default=0,
        help_text="Current stock quantity"
    )
    usage_rate = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Consumption rate, e.g., '500Liters'"
    )
    shelf_life = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Expected shelf life duration, e.g., '5 years'"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Product expiration date"
    )
    condition = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Product condition, e.g., 'New', 'Used'"
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Unit price of the product"
    )
    product_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Full product name (may differ from brand)"
    )
    alt_part_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Alternate part number"
    )
    my_part_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Internal/custom part number"
    )
    mil_spec = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Military specification code (e.g., 'MIL-L-23699')"
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Serial number of the item"
    )
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Manufacturing batch ID, e.g., 'B-001'"
    )
    source = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Source or supplier name"
    )
    company = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Supplier/manufacturer company, e.g., 'Global Fuels Ltd'"
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Running balance or total value"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='healthy',
        help_text="Current product status: healthy, expired, or near_expiry"
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Optional notes about this item"
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
    admin_notes = models.TextField(null=True, blank=True)
    action_taken = models.TextField(null=True, blank=True, help_text="Specific actions taken by admin to resolve the ticket")
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


class POLItem(models.Model):
    STATUS_CHOICES = (
        ('healthy', 'Healthy'),
        ('expired', 'Expired'),
        ('low_stock', 'Low Stock'),
    )
    EXPIRY_STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('near_expiry', 'Near Expiry'),
    )
    TYPE_CHOICES = (
        ('petroleum', 'Petroleum'),
        ('oil', 'Oil'),
        ('lubricant', 'Lubricant'),
    )
    CONDITION_CHOICES = (
        ('new_pol', 'New POL'),
        ('leftover_pol', 'Leftover POL'),
        ('opened_pol', 'Opened POL'),
    )
    UOM_CHOICES = (
        ('QT', 'Quart'), ('OZ', 'Ounce'), ('LB', 'Pound'), ('RL', 'Roll'), 
        ('EA', 'Each'), ('GAL', 'Gallon'), ('ML', 'Millilitre'), ('PT', 'Pint'), 
        ('KT', 'Kit'), ('GM', 'Gram'), ('FT', 'Feet'), ('SQ ST', 'Square Feet'), 
        ('YD', 'Yard'), ('CC', 'Cubic Centimeter'),
    )
 
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='pol_items',
    )
 
    # Required fields
    part_number = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    pol_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='petroleum')
    uom = models.CharField(max_length=50, choices=UOM_CHOICES, default='GAL', help_text='Unit of Measurement')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Stock/Availability')
    shelf_life = models.CharField(max_length=50, help_text='e.g. 5 years')
    expiry = models.DateField()
    expiry_status = models.CharField(max_length=20, choices=EXPIRY_STATUS_CHOICES, default='active')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new_pol')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
 
    # Auto-computed
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='healthy')
 
    # Optional fields
    product_name = models.CharField(max_length=200, blank=True)
    alt_part_number = models.CharField(max_length=50, blank=True)
    manufacturer_part_number = models.CharField(max_length=50, blank=True)
    mil_spec = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=200, blank=True)
    balance = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
 
    image = models.ImageField(upload_to='pol_images/', blank=True, null=True)
    msds_file = models.FileField(upload_to='msds/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'POL Item'
        verbose_name_plural = 'POL Items'
 
    def __str__(self):
        return f"{self.product_name or self.description[:50]} - {self.part_number}"


class Listing(models.Model):
    TYPE_CHOICES = (
        ('petroleum', 'Petroleum'),
        ('oil', 'Oil'),
        ('lubricant', 'Lubricant'),
    )
    CATEGORY_CHOICES = (
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    )
    STATUS_CHOICES = (
        ('listed', 'Listed'),
        ('unlisted', 'Unlisted'),
        ('sold', 'Sold'),
    )
 
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='listings',
    )
    pol_item = models.ForeignKey(
        'POLItem',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='listings',
    )
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    pol_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='petroleum')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_unit = models.CharField(max_length=20, default='Liter')
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    expiry = models.DateField(null=True, blank=True)
    shelf_life = models.CharField(max_length=50, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_unit = models.CharField(max_length=20, default='Liter')
    sds_file = models.FileField(upload_to='sds/', null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='sell')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='listed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.name} - {self.company} ({self.category})"
