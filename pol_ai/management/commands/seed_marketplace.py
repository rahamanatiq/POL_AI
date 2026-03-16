from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pol_ai.models import Listing, POLItem, MarketplaceItem
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Seeds the database with 20 marketplace listings for AI testing'

    def handle(self, *args, **kwargs):
        # Ensure at least one user exists
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write("Created default user 'admin'")

        self.stdout.write("Deleting old marketplace data...")
        MarketplaceItem.objects.all().delete()
        Listing.objects.all().delete()

        today = date.today()
        pol_items = list(POLItem.objects.all())
        
        # --- Seeding 20 Listing records (RAG-Optimized) ---
        listings_data = [
            {
                "user": user, "name": "Bulk Jet A-1 Fuel Supply", "company": "Global Aviation Fuels Ltd",
                "pol_type": "petroleum", "price": 2.35, "price_unit": "Gallon", "location": "Houston, TX",
                "brand": "Shell Aviation", "batch_number": "SH-2026-X", "expiry": today + timedelta(days=500),
                "quantity": 50000, "quantity_unit": "Gallon", "category": "sell", "status": "listed",
                "description": "Offering 50,000 gallons of high-quality Jet A-1 fuel. Meets all international standards. Available for immediate delivery or scheduled pickup."
            },
            {
                "user": user, "name": "Premium Hydraulic Fluid MIL-PRF-5606H", "company": "Aerospace Fluids Corp",
                "pol_type": "oil", "price": 45.00, "price_unit": "Gallon", "location": "Seattle, WA",
                "brand": "Royco", "batch_number": "RY-9981", "expiry": today + timedelta(days=200),
                "quantity": 100, "quantity_unit": "Gallon", "category": "sell", "status": "listed",
                "description": "Red-dyed mineral oil based hydraulic fluid for aircraft. Excellent low-temperature characteristics. Stored in 55-gallon drums."
            },
            {
                "user": user, "name": "Seeking 500 Liters of Skydrol PD-5", "company": "Central Airline Services",
                "pol_type": "oil", "price": 55.00, "price_unit": "Liter", "location": "Denver, CO",
                "brand": "Eastman", "quantity": 500, "quantity_unit": "Liter", "category": "buy", "status": "listed",
                "description": "Looking for fire-resistant phosphate ester hydraulic fluid. Must have at least 1 year shelf life remaining."
            },
            {
                "user": user, "name": "Mobil Jet Oil II - Case discount", "company": "Elite Lubricants Inc",
                "pol_type": "lubricant", "price": 14.50, "price_unit": "Quart", "location": "Atlanta, GA",
                "brand": "Mobil", "quantity": 240, "quantity_unit": "Quart", "category": "sell", "status": "listed",
                "description": "Synthetic gas turbine lubricant. 10 cases (24 quarts per case) available. Sealed factory packaging."
            },
            {
                "user": user, "name": "AeroShell Grease 33 Surplus", "company": "Aero Parts Supply",
                "pol_type": "lubricant", "price": 10.00, "price_unit": "Tube", "location": "Miami, FL",
                "brand": "Shell", "quantity": 50, "quantity_unit": "Tube", "category": "sell", "status": "listed",
                "description": "Synthetic airframe grease. Excess inventory from maintenance project. Expiry end of next year."
            },
            {
                "user": user, "name": "Urgent: Need 10,000 Gallons Avgas 100LL", "company": "Regional Airport Authority",
                "pol_type": "petroleum", "price": 6.50, "price_unit": "Gallon", "location": "Phoenix, AZ",
                "quantity": 10000, "quantity_unit": "Gallon", "category": "buy", "status": "listed",
                "description": "Seeking immediate supply of 100LL aviation gasoline for charter operations. Will handle transport if needed."
            },
            {
                "user": user, "name": "Jet B Fuel - Cold Weather Ops", "company": "Arctic Logistics Group",
                "pol_type": "petroleum", "price": 3.10, "price_unit": "Gallon", "location": "Anchorage, AK",
                "brand": "Imperial Oil", "quantity": 15000, "quantity_unit": "Gallon", "category": "sell", "status": "listed",
                "description": "Specialized Jet B fuel optimized for extreme cold environments. High volatility and low freezing point."
            },
            {
                "user": user, "name": "Synthetic Transmission Fluid (Heavy Duty)", "company": "Fleet Maintenance Pro",
                "pol_type": "lubricant", "price": 120.00, "price_unit": "Pail", "location": "Chicago, IL",
                "brand": "Castrol", "quantity": 15, "quantity_unit": "Pail", "category": "sell", "status": "listed",
                "description": "Heavy-duty transmission fluid for ground support vehicles. 5-gallon pails available."
            },
            {
                "user": user, "name": "Castrol Braycote 601EF - Specialty Grease", "company": "High Altitude Tech",
                "pol_type": "lubricant", "price": 110.00, "price_unit": "2oz Syringe", "location": "Los Angeles, CA",
                "brand": "Castrol", "quantity": 10, "quantity_unit": "Syringe", "category": "sell", "status": "listed",
                "description": "Perfluorinated polyether grease for space/vacuum. Original sealed syringes. Long shelf life."
            },
            {
                "user": user, "name": "Looking for MIL-L-23699 Lubricant", "company": "Vintage Wings Repair",
                "pol_type": "lubricant", "price": 16.00, "price_unit": "Quart", "location": "Dallas, TX",
                "quantity": 48, "quantity_unit": "Quart", "category": "buy", "status": "listed",
                "description": "Need matching lubrication for older jet turbines. Prefer Exxon or Mobil brands."
            },
            {
                "user": user, "name": "Industrial Solvent Surpus (White Spirit)", "company": "CleanWork Solutions",
                "pol_type": "petroleum", "price": 8.50, "price_unit": "Gallon", "location": "Detroit, MI",
                "brand": "Standard Chemical", "quantity": 200, "quantity_unit": "Gallon", "category": "sell", "status": "listed",
                "description": "Effective degreasing solvent. Overstock from manufacturing line. Highly flammable, stored safely."
            },
            {
                "user": user, "name": "AeroShell Oil W100 - Bulk Discount", "company": "Piston Power Supply",
                "pol_type": "oil", "price": 7.80, "price_unit": "Quart", "location": "Orlando, FL",
                "brand": "Shell", "quantity": 360, "quantity_unit": "Quart", "category": "sell", "status": "listed",
                "description": "Ashless dispersant engine oil for radial engines. 15 cases available."
            },
            {
                "user": user, "name": "JP-8 Military Grade Fuel", "company": "Defense Fuel Contractors",
                "pol_type": "petroleum", "price": 2.75, "price_unit": "Gallon", "location": "San Diego, CA",
                "quantity": 100000, "quantity_unit": "Gallon", "category": "sell", "status": "listed",
                "description": "Contract surplus JP-8. Bulk availability. Complies with MIL-DTL-83133."
            },
            {
                "user": user, "name": "Royco 756 Hydraulic Fluid - 1 Gallon Cans", "company": "Quick Serv Aviation",
                "pol_type": "oil", "price": 38.00, "price_unit": "Gallon", "location": "Newark, NJ",
                "brand": "Anderol", "quantity": 25, "quantity_unit": "Gallon", "category": "sell", "status": "listed",
                "description": "Red aircraft hydraulic fluid in convenient 1-gallon cans. Batch expiry 2027."
            },
            {
                "user": user, "name": "Need Biodegradable Hydraulic Oil", "company": "Eco-Flight Services",
                "pol_type": "oil", "price": 50.00, "price_unit": "Gallon", "location": "Portland, OR",
                "quantity": 200, "quantity_unit": "Gallon", "category": "buy", "status": "listed",
                "description": "Seeking environmentally friendly hydraulic fluid options for ground equipment operating near wetlands."
            },
            {
                "user": user, "name": "Krytox 240AC - Limited Stock", "company": "Precision Bearings Ltd",
                "pol_type": "lubricant", "price": 195.00, "price_unit": "8oz Tube", "location": "Boston, MA",
                "brand": "Chemours", "quantity": 5, "quantity_unit": "Tube", "category": "sell", "status": "listed",
                "description": "Premium oxygen-compatible grease. Ideal for high-temp valve seals."
            },
            {
                "user": user, "name": "Marine Diesel (MGO) Surplus", "company": "Coastal Marine Fueling",
                "pol_type": "petroleum", "price": 1.85, "price_unit": "Gallon", "location": "New Orleans, LA",
                "quantity": 10000, "quantity_unit": "Gallon", "category": "sell", "status": "listed",
                "description": "Distillate fuel for marine engines. Low sulfur. Suitable for backup generators."
            },
            {
                "user": user, "name": "AeroShell Oil Sport Plus 4", "company": "Rotax Maintenance Depot",
                "pol_type": "oil", "price": 12.00, "price_unit": "Liter", "location": "San Jose, CA",
                "brand": "Shell", "quantity": 60, "quantity_unit": "Liter", "category": "sell", "status": "listed",
                "description": "Multi-grade oil specifically for light sport aircraft engines (4-stroke)."
            },
            {
                "user": user, "name": "Buying Refined Kerosene", "company": "Heat Well Heating Co",
                "pol_type": "petroleum", "price": 3.50, "price_unit": "Gallon", "location": "Minneapolis, MN",
                "quantity": 1000, "quantity_unit": "Gallon", "category": "buy", "status": "listed",
                "description": "Looking for k-1 kerosene for portable heater refilling services."
            },
            {
                "user": user, "name": "Nyco Grease GN 22 - Wheel Bearing", "company": "Global Wheel & Brake",
                "pol_type": "lubricant", "price": 55.00, "price_unit": "1kg Pail", "location": "Las Vegas, NV",
                "brand": "Nyco", "quantity": 20, "quantity_unit": "Pail", "category": "sell", "status": "sold",
                "description": "High-temperature wheel bearing grease. Note: This batch is currently reserved/sold."
            }
        ]

        listings_to_create = []
        for i, data in enumerate(listings_data):
            # Assign a POLItem if available (optional in model, but good for RAG testing)
            if pol_items:
                data["pol_item"] = pol_items[i % len(pol_items)]
            
            # Additional enrichment for RAG
            data["rating"] = random.choice([4.2, 4.5, 4.7, 4.8, 5.0, 3.8])
            
            listing = Listing(**data)
            listings_to_create.append(listing)
            
        Listing.objects.bulk_create(listings_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully injected {len(listings_data)} Listing records!'))
