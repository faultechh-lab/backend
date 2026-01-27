from django.core.management.base import BaseCommand
from django.apps import apps
from faults.models import (
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video
)
from orders.models import Product
from accounts.models import User

class Command(BaseCommand):
    help = 'Displays statistics about the database contents'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('--- SYSTEM STATISTICS REPORT ---'))

        # 1. Main Faults Models
        models_to_check = [
            (Category, "Categories"),
            (Brand, "Brands"),
            (Model, "Models"),
            (FaultCodes, "Fault Codes"),
            (Parameter, "Parameters"),
            (BoilerPart, "Boiler Parts"),
            (SparePartsDefinitions, "Spare Parts Definitions"),
            (BoilerRepairGuide, "Repair Guides"),
            (BoilerWorkingPrinciple, "Working Principles"),
            (BoilerCardRepair, "Card Repair Guides"),
            (BoilerBoardRepairer, "Repairers (Services)"),
            (InstrumentUsage, "Instrument Usage Guides"),
            (RoomTermostat, "Room Thermostats"),
            (Video, "Videos"),
        ]

        self.stdout.write(self.style.SUCCESS('\n[Content Statistics]'))
        total_content = 0
        for model_cls, label in models_to_check:
            count = model_cls.objects.count()
            
            # Count active if active field exists
            active_count = "N/A"
            if hasattr(model_cls, 'active'):
                active_c = model_cls.objects.filter(active=True).count()
                active_count = f"{active_c} active"
            
            self.stdout.write(f"- {label:<25}: {count:<6} ({active_count})")
            total_content += count
        
        self.stdout.write(self.style.WARNING(f"TOTAL CONTENT ITEMS      : {total_content}"))

        # 2. Users
        self.stdout.write(self.style.SUCCESS('\n[User Statistics]'))
        user_count = User.objects.count()
        
        # Check membership status instead of is_premium
        premium_users = User.objects.filter(membership_status='PREMIUM').count()
        verified_users = User.objects.filter(is_verified=True).count()
        
        self.stdout.write(f"- Total Users            : {user_count}")
        self.stdout.write(f"- Premium Users          : {premium_users}")
        self.stdout.write(f"- Verified Users         : {verified_users}")

        # 3. Products
        self.stdout.write(self.style.SUCCESS('\n[Order & Product Statistics]'))
        product_count = Product.objects.count()
        self.stdout.write(f"- Active Products        : {product_count}")

        # 4. Translation Check (Sample)
        self.stdout.write(self.style.SUCCESS('\n[Translation Coverage Check (Sample: FaultCodes)]'))
        fc_count = FaultCodes.objects.count()
        if fc_count > 0:
            # Check how many have English translation
            en_count = FaultCodes.objects.filter(fault_description_en__isnull=False).exclude(fault_description_en="").count()
            percent = (en_count / fc_count) * 100
            self.stdout.write(f"- Fault Codes Translated (EN): {en_count}/{fc_count} ({percent:.1f}%)")
        else:
            self.stdout.write("- No Fault Codes to check.")

        self.stdout.write(self.style.MIGRATE_HEADING('\n--- END REPORT ---'))
