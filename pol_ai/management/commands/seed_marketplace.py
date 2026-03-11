from django.core.management.base import BaseCommand
from pol_ai.models import MarketplaceItem

class Command(BaseCommand):
    help = 'Seeds the database with mock marketplace data for Marie AI testing'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old marketplace data...")
        MarketplaceItem.objects.all().delete()

        mock_data = [
            # Sellers (Petroleum/Fuel)
            {"product_name": "Premium Aviation Fuel Jet-A", "category": "petroleum", "quantity": "5000 Gal", "price_per_unit": 2.15, "location": "Hangar 4 - West Coast", "inventory_details": "Excess inventory from Q3, stored in compliant tanks.", "transaction_type": "sell"},
            {"product_name": "Standard Jet Fuel", "category": "petroleum", "quantity": "2000 Gal", "price_per_unit": 2.50, "location": "Texas AFB", "inventory_details": "Standard overstock.", "transaction_type": "sell"},
            {"product_name": "Diesel Grade 2", "category": "petroleum", "quantity": "10000 Gal", "price_per_unit": 3.10, "location": "Depot North", "inventory_details": "Bulk seller, willing to negotiate.", "transaction_type": "sell"},
            
            # Buyers (Looking to purchase Petroleum/Fuel)
            {"product_name": "Aviation Fuel Jet-A", "category": "petroleum", "quantity": "4000 Gal", "price_per_unit": 2.20, "location": "Nevada Base", "inventory_details": "Need Jet-A by next month. Willing to pay up to 2.20/gal.", "transaction_type": "buy"},
            {"product_name": "Bulk Diesel", "category": "petroleum", "quantity": "15000 Gal", "price_per_unit": 3.00, "location": "East Coast Depot", "inventory_details": "Looking for the cheapest bulk diesel supplier.", "transaction_type": "buy"},

            # Sellers (Oils/Lubricants)
            {"product_name": "Hydraulic Fluid Drum", "category": "oil", "quantity": "50 Barrels", "price_per_unit": 120.00, "location": "Storage B", "inventory_details": "Unopened drums, expiry 2026.", "transaction_type": "sell"},
            {"product_name": "Premium Hydraulic Fluid", "category": "oil", "quantity": "20 Barrels", "price_per_unit": 180.00, "location": "Storage A", "inventory_details": "High grade, temperature resistant.", "transaction_type": "sell"},
            {"product_name": "Used Engine Oil", "category": "lubricant", "quantity": "200 Liters", "price_per_unit": 0.50, "location": "Maintenance Bay", "inventory_details": "Requires filtration. Available for immediate pickup.", "transaction_type": "sell"},
            {"product_name": "Transmission Fluid X", "category": "lubricant", "quantity": "150 Gallons", "price_per_unit": 12.50, "location": "Storage A", "inventory_details": "Unopened containers. Expiry 2027.", "transaction_type": "sell"},

            # Buyers (Looking for Oils/Lubricants)
            {"product_name": "Hydraulic Fluid", "category": "oil", "quantity": "10 Barrels", "price_per_unit": 130.00, "location": "Base C", "inventory_details": "Need standard hydraulic fluid quickly.", "transaction_type": "buy"},
            {"product_name": "Transmission Fluid", "category": "lubricant", "quantity": "100 Gallons", "price_per_unit": 11.00, "location": "Base D", "inventory_details": "Looking for any brand of transmission fluid under $12.", "transaction_type": "buy"},

            # Other
            {"product_name": "Industrial Solvent 500", "category": "other", "quantity": "10 Drums", "price_per_unit": 85.00, "location": "West Wing", "inventory_details": "Surplus solvent sitting in warehouse.", "transaction_type": "sell"},
            {"product_name": "Antifreeze Bulk", "category": "other", "quantity": "500 Gallons", "price_per_unit": 5.00, "location": "North Wing", "inventory_details": "Winter overstock.", "transaction_type": "sell"},
            {"product_name": "Solvents", "category": "other", "quantity": "5 Drums", "price_per_unit": 90.00, "location": "South Wing", "inventory_details": "Need solvents for cleaning.", "transaction_type": "buy"},
        ]

        items_to_create = []
        for data in mock_data:
            item = MarketplaceItem(**data)
            items_to_create.append(item)
            
        MarketplaceItem.objects.bulk_create(items_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully injected {len(mock_data)} mock marketplace items!'))
