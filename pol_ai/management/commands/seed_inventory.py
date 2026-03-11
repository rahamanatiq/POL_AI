from django.core.management.base import BaseCommand
from pol_ai.models import InventoryItem
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Seeds the database with mock inventory data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old mock data...")
        InventoryItem.objects.all().delete()

        today = date.today()
        
        # Scenarios to match the screenshot and allow complex queries
        mock_data = [
            # Petroleum - Global Fuels Ltd
            {"brand": "High-Grade Diesel", "part_number": "PD - 100", "type": "petroleum", "usage_rate": "500Liters", "batch_number": "B-001", "shelf_life": "5 years", "expiry_date": today + timedelta(days=100), "company": "Global Fuels Ltd"},
            {"brand": "High-Grade Diesel", "part_number": "PD - 101", "type": "petroleum", "usage_rate": "500Liters", "batch_number": "B-002", "shelf_life": "5 years", "expiry_date": today - timedelta(days=10), "company": "Global Fuels Ltd"},
            {"brand": "Unleaded Petrol", "part_number": "UP - 200", "type": "petroleum", "usage_rate": "800Liters", "batch_number": "B-003", "shelf_life": "3 years", "expiry_date": today + timedelta(days=15), "company": "Global Fuels Ltd"},
            
            # Lubricants - SynthOil Corp
            {"brand": "SynthoLube Gear Oil", "part_number": "SL - G10", "type": "lubricant", "usage_rate": "50Liters", "batch_number": "S-991", "shelf_life": "10 years", "expiry_date": today + timedelta(days=500), "company": "SynthOil Corp"},
            {"brand": "SynthoLube Motor Oil", "part_number": "SL - M20", "type": "lubricant", "usage_rate": "200Liters", "batch_number": "S-992", "shelf_life": "8 years", "expiry_date": today - timedelta(days=50), "company": "SynthOil Corp"},

            # Chemicals - ChemWorks Inc
            {"brand": "Industrial Degreaser", "part_number": "CW - D50", "type": "chemical", "usage_rate": "20Liters", "batch_number": "C-111", "shelf_life": "2 years", "expiry_date": today + timedelta(days=400), "company": "ChemWorks Inc"},
            {"brand": "Hydraulic Fluid", "part_number": "CW - HF1", "type": "chemical", "usage_rate": "100Liters", "batch_number": "C-112", "shelf_life": "5 years", "expiry_date": today + timedelta(days=5), "company": "ChemWorks Inc"},

            # Gas - AeroGas Ltd
            {"brand": "Aviation Fuel", "part_number": "AF - JetA", "type": "gas", "usage_rate": "1000Liters", "batch_number": "A-500", "shelf_life": "1 year", "expiry_date": today + timedelta(days=200), "company": "AeroGas Ltd"},
            {"brand": "Propane Tank", "part_number": "PT - 50", "type": "gas", "usage_rate": "50kg", "batch_number": "A-501", "shelf_life": "15 years", "expiry_date": today - timedelta(days=100), "company": "AeroGas Ltd"},
        ]

        # Bulk create items
        items_to_create = []
        for data in mock_data:
            item = InventoryItem(**data)
            items_to_create.append(item)
            
        InventoryItem.objects.bulk_create(items_to_create)

        # Run the auto_update_status to set healthy/expired/near_expiry properly based on dates
        for item in InventoryItem.objects.all():
            item.auto_update_status()

        self.stdout.write(self.style.SUCCESS(f'Successfully injected {len(mock_data)} mock inventory items!'))
