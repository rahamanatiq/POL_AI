from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pol_ai.models import InventoryItem, POLItem
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Seeds the database with 20 RAG-optimized POL data items for testing'

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

        self.stdout.write("Deleting old mock data...")
        InventoryItem.objects.all().delete()
        POLItem.objects.all().delete()

        today = date.today()
        
        # --- Seeding 20 POLItem (RAG-Optimized) ---
        pol_mock_data = [
            {
                "user": user, "part_number": "POL-JET-001", "product_name": "Jet A-1 Aviation Fuel",
                "description": "Standard kerosene-type turbine fuel used in civilian and military aviation. High flash point and low freezing point (-47°C).",
                "pol_type": "petroleum", "uom": "GAL", "quantity": 10000.00, "shelf_life": "5 years",
                "expiry": today + timedelta(days=730), "condition": "new_pol", "price_per_unit": 2.50,
                "notes": "Stored in North Depot, Tank 12. Batch B449. Last inspection: 2 weeks ago."
            },
            {
                "user": user, "part_number": "POL-OIL-002", "product_name": "Mobil Jet Oil II",
                "description": "High-performance synthetic aircraft gas turbine lubricant. Formulated with stable synthetic base fluid and unique chemical additive package.",
                "pol_type": "oil", "uom": "QT", "quantity": 500.00, "shelf_life": "10 years",
                "expiry": today + timedelta(days=1825), "condition": "new_pol", "price_per_unit": 15.75,
                "notes": "Unopened crates in climate-controlled storage. Essential for turbine bearing lubrication."
            },
            {
                "user": user, "part_number": "POL-LUB-003", "product_name": "AeroShell Grease 33",
                "description": "Universal airframe grease designed for high load carrying capacity and corrosion resistance in aircraft components.",
                "pol_type": "lubricant", "uom": "LB", "quantity": 45.50, "shelf_life": "3 years",
                "expiry": today + timedelta(days=100), "condition": "new_pol", "price_per_unit": 12.00,
                "notes": "Used for landing gear and flight control surface pivots. Low temperature compliant."
            },
            {
                "user": user, "part_number": "POL-PET-004", "product_name": "Avgas 100LL",
                "description": "Low-lead aviation gasoline for reciprocating piston engines. Colored blue for easy identification during pre-flight checks.",
                "pol_type": "petroleum", "uom": "GAL", "quantity": 1200.00, "shelf_life": "2 years",
                "expiry": today - timedelta(days=20), "condition": "leftover_pol", "price_per_unit": 6.10,
                "expiry_status": "expired", "status": "expired",
                "notes": "Expired batch in Hangar 2. Fuel requires drainage and environmental disposal."
            },
            {
                "user": user, "part_number": "POL-OIL-005", "product_name": "Hydraulic Fluid MIL-PRF-5606",
                "description": "Mineral-based red hydraulic fluid for aircraft and missile systems. Known for excellent low-temperature viscosity.",
                "pol_type": "oil", "uom": "GAL", "quantity": 25.00, "shelf_life": "4 years",
                "expiry": today + timedelta(days=15), "condition": "opened_pol", "price_per_unit": 38.00,
                "expiry_status": "near_expiry", "status": "low_stock",
                "notes": "Partial drum. Nitrogen-blanketed to prevent oxidation. Critical for brake systems."
            },
            {
                "user": user, "part_number": "POL-LUB-006", "product_name": "Castrol Braycote 601EF",
                "description": "Perfluorinated polyether grease designed for high vacuum and extreme temperature environments (space and aerospace).",
                "pol_type": "lubricant", "uom": "OZ", "quantity": 10.00, "shelf_life": "20 years",
                "expiry": today + timedelta(days=5000), "condition": "new_pol", "price_per_unit": 125.00,
                "notes": "High-cost specialty grease. Chemically inert and non-flammable. Small inventory."
            },
            {
                "user": user, "part_number": "POL-JET-007", "product_name": "Jet B Fuel",
                "description": "Wide-cut aviation fuel used primarily in extremely cold climates. Blend of kerosene and gasoline.",
                "pol_type": "petroleum", "uom": "GAL", "quantity": 2000.00, "shelf_life": "3 years",
                "expiry": today + timedelta(days=400), "condition": "new_pol", "price_per_unit": 2.85,
                "notes": "Reserved for Arctic operations. Higher volatility than Jet A-1."
            },
            {
                "user": user, "part_number": "POL-OIL-008", "product_name": "Skydrol LD-4",
                "description": "Phosphate ester based fire-resistant hydraulic fluid for commercial jet aircraft. Low density and erosion resistant.",
                "pol_type": "oil", "uom": "GAL", "quantity": 150.00, "shelf_life": "5 years",
                "expiry": today + timedelta(days=800), "condition": "new_pol", "price_per_unit": 42.50,
                "notes": "Warning: Highly corrosive to paint and certain plastics. Handle with personal protective equipment."
            },
            {
                "user": user, "part_number": "POL-LUB-009", "product_name": "Molykote G-Rapid Plus",
                "description": "Solid lubricant paste with low friction coefficient for assembly and running-in of metal components.",
                "pol_type": "lubricant", "uom": "GM", "quantity": 250.00, "shelf_life": "5 years",
                "expiry": today + timedelta(days=300), "condition": "new_pol", "price_per_unit": 0.15,
                "notes": "Apply to splines and threaded connections to prevent galling. Contains MoS2."
            },
            {
                "user": user, "part_number": "POL-PET-010", "product_name": "Marine Diesel Fuel (MGO)",
                "description": "Clean-burning distillate fuel for high-speed marine engines. Low sulfur content for environmental compliance.",
                "pol_type": "petroleum", "uom": "GAL", "quantity": 50000.00, "shelf_life": "2 years",
                "expiry": today + timedelta(days=365), "condition": "new_pol", "price_per_unit": 1.95,
                "notes": "Bulk storage in Coastal Terminal 4. Suitable for standby generators."
            },
            {
                "user": user, "part_number": "POL-OIL-011", "product_name": "Shell Tellus S2 M 46",
                "description": "High-performance hydraulic oil that provides outstanding protection and performance in most manufacturing/mobile operations.",
                "pol_type": "oil", "uom": "GAL", "quantity": 200.00, "shelf_life": "6 years",
                "expiry": today + timedelta(days=1200), "condition": "new_pol", "price_per_unit": 9.50,
                "notes": "Industrial grade. Not for aviation hydraulic systems. For ground support equipment."
            },
            {
                "user": user, "part_number": "POL-LUB-012", "product_name": "Nyco Grease GN 22",
                "description": "Synthetic hydrocarbon grease for high-temperature applications in aircraft wheels and brakes.",
                "pol_type": "lubricant", "uom": "KT", "quantity": 5.00, "shelf_life": "5 years",
                "expiry": today + timedelta(days=450), "condition": "new_pol", "price_per_unit": 85.00,
                "notes": "Available in 1kg kits. Certified for Airbus and Boeing wheel bearing maintenance."
            },
            {
                "user": user, "part_number": "POL-PET-013", "product_name": "Kerosene (Heating Oil)",
                "description": "Refined petroleum distillate used for heating and as a solvent in various industrial processes.",
                "pol_type": "petroleum", "uom": "GAL", "quantity": 300.00, "shelf_life": "2 years",
                "expiry": today - timedelta(days=5), "condition": "leftover_pol", "price_per_unit": 3.20,
                "expiry_status": "expired", "status": "expired",
                "notes": "Leftover from winter season. Contamination check required before reuse."
            },
            {
                "user": user, "part_number": "POL-OIL-014", "product_name": "AeroShell Oil W100",
                "description": "Ashless dispersant oil for aircraft piston engines. Provides excellent protection against sludge and carbon deposits.",
                "pol_type": "oil", "uom": "QT", "quantity": 240.00, "shelf_life": "4 years",
                "expiry": today + timedelta(days=600), "condition": "new_pol", "price_per_unit": 8.90,
                "notes": "SAE 50 grade. Recommended for use in hot weather operations for radial engines."
            },
            {
                "user": user, "part_number": "POL-LUB-015", "product_name": "Krytox 240AC",
                "description": "Fluorinated grease for valves, bearings, and seals in oxygen-rich or high-temperature environments.",
                "pol_type": "lubricant", "uom": "OZ", "quantity": 2.00, "shelf_life": "15 years",
                "expiry": today + timedelta(days=3000), "condition": "new_pol", "price_per_unit": 210.00,
                "notes": "Extremely high stability. Non-reactive with aggressive chemicals. Lab-grade storage."
            },
            {
                "user": user, "part_number": "POL-JET-016", "product_name": "JP-8 Military Jet Fuel",
                "description": "Standard military jet fuel with additives for icing inhibition, thermal stability, and corrosion prevention.",
                "pol_type": "petroleum", "uom": "GAL", "quantity": 25000.00, "shelf_life": "5 years",
                "expiry": today + timedelta(days=1000), "condition": "new_pol", "price_per_unit": 2.65,
                "notes": "Military spec MIL-DTL-83133. Primary fuel for NATO airbases. High safety profile."
            },
            {
                "user": user, "part_number": "POL-OIL-017", "product_name": "Royco 756 Hydraulic Fluid",
                "description": "Red-dyed mineral oil-based hydraulic fluid for aircraft. Very high viscosity index and shear stability.",
                "pol_type": "oil", "uom": "GAL", "quantity": 60.00, "shelf_life": "4 years",
                "expiry": today + timedelta(days=25), "condition": "opened_pol", "price_per_unit": 40.00,
                "expiry_status": "near_expiry", "status": "low_stock",
                "notes": "Opened 2 months ago. Half drum remaining. Must be tested for moisture before flight use."
            },
            {
                "user": user, "part_number": "POL-LUB-018", "product_name": "Petro-Canada Peerless LLG",
                "description": "Premium multi-application grease for high temperature and long-life service in industrial equipment.",
                "pol_type": "lubricant", "uom": "LB", "quantity": 100.00, "shelf_life": "5 years",
                "expiry": today + timedelta(days=900), "condition": "new_pol", "price_per_unit": 6.50,
                "notes": "Good for conveyor bearings and high humidity environments. Water resistant."
            },
            {
                "user": user, "part_number": "POL-PET-019", "product_name": "White Spirit (Solvent)",
                "description": "Petroleum-derived clear liquid used as a common organic solvent in painting and degreasing.",
                "pol_type": "petroleum", "uom": "GAL", "quantity": 20.00, "shelf_life": "3 years",
                "expiry": today + timedelta(days=120), "condition": "new_pol", "price_per_unit": 14.00,
                "notes": "Flammable liquid. Keep away from heat sources. Used for cleaning metal surfaces."
            },
            {
                "user": user, "part_number": "POL-OIL-020", "product_name": "Texaco Ursa Super Plus 15W-40",
                "description": "Heavy-duty engine oil for naturally aspirated and turbocharged diesel and gasoline engines.",
                "pol_type": "oil", "uom": "GAL", "quantity": 400.00, "shelf_life": "5 years",
                "expiry": today + timedelta(days=1500), "condition": "new_pol", "price_per_unit": 11.20,
                "notes": "Ideal for fleet maintenance. High detergent properties. Stored in Hangar 5."
            }
        ]

        pol_items_to_create = [POLItem(**data) for data in pol_mock_data]
        POLItem.objects.bulk_create(pol_items_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully injected {len(pol_mock_data)} RAG-optimized POLItems!'))
