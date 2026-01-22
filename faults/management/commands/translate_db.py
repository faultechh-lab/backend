import time
import os
import google.generativeai as genai
from decouple import config
from django.core.management.base import BaseCommand
from django.conf import settings
from faults.models import (
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video
)
from orders.models import Product
from config.models import OnboardModel
from modeltranslation.utils import build_localized_fieldname

class Command(BaseCommand):
    help = 'Translates database content to Arabic using Gemini Pro API'

    def handle(self, *args, **options):
        api_key = config('GEMINI_API_KEY', default=None)
        if not api_key:
            self.stdout.write(self.style.ERROR('GEMINI_API_KEY not found in .env file.'))
            return

        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash as requested
        model = genai.GenerativeModel('gemini-2.5-flash')

        # List of models and their fields to translate
        # (ModelClass, [list of fields])
        # Note: We translate FROM 'tr' (default) TO 'ar'
        
        translation_map = [
            (Category, ['name']),
            (Brand, ['name']),
            (Model, ['name']),
            (FaultCodes, ['code', 'fault_description']),
            (Parameter, ['name', 'description']),
            (SparePartImage, ['name']),
            (BoilerRepairGuide, ['title', 'content']),
            (BoilerPart, ['name']),
            (SparePartsDefinitions, ['name', 'description']),
            (BoilerWorkingPrinciple, ['title', 'description']),
            (BoilerCardRepair, ['title', 'description']),
            (BoilerBoardRepairer, ['name', 'business_type']),
            (InstrumentUsage, ['title', 'content']),
            (RoomTermostat, ['title', 'description']),
            (Video, ['title', 'description']),
            (Product, ['title', 'description']),
            (OnboardModel, ['title', 'description']),
        ]

        total_translated_count = 0

        for ModelClass, fields in translation_map:
            model_name = ModelClass.__name__
            self.stdout.write(self.style.MIGRATE_HEADING(f'Processing model: {model_name}'))
            
            objects = ModelClass.objects.all()
            count = objects.count()
            self.stdout.write(f'Found {count} objects in {model_name}.')

            for obj in objects:
                updated = False
                for field in fields:
                    field_tr = build_localized_fieldname(field, 'tr')
                    field_ar = build_localized_fieldname(field, 'ar')

                    # Get source text (Turkish) - try localized first, then fallback to base
                    source_text = getattr(obj, field_tr, None)
                    if not source_text:
                        source_text = getattr(obj, field, None)

                    # Get current Arabic text
                    current_ar = getattr(obj, field_ar, None)

                    # Translate if source exists AND (Arabic is empty OR Arabic equals source)
                    # Note: When modeltranslation initializes, it might copy source to other langs
                    # So we check if current_ar is None, empty string, or same as source
                    if source_text and (not current_ar or current_ar == source_text):
                        try:
                            # Skip if source is very short/symbolic unless it's a name
                            if len(str(source_text).strip()) < 2 and field != 'code':
                                continue

                            self.stdout.write(f'Translating {field} for {model_name} ID {obj.id}...')
                            
                            prompt = (
                                "Translate the following technical service document to Arabic.\n"
                                "Preserve formatting, headings, bullet points, and units.\n"
                                "Do not simplify or shorten.\n"
                                "Use formal technical Arabic.\n"
                                "Do not add explanations.\n"
                                "Return ONLY the translated text.\n"
                                f"Text: {source_text}"
                            )
                            
                            response = model.generate_content(prompt)
                            
                            if response.text:
                                translated_text = response.text.strip()
                                # Clean up quotes if Gemini adds them
                                if translated_text.startswith('"') and translated_text.endswith('"'):
                                    translated_text = translated_text[1:-1]
                                
                                setattr(obj, field_ar, translated_text)
                                updated = True
                                total_translated_count += 1
                                # Free tier limit is ~15 RPM, so we need to sleep ~4 seconds
                                time.sleep(4.1)
                            else:
                                self.stdout.write(self.style.WARNING(f'Empty response for {field} ID {obj.id}'))

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error translating {field} for {model_name} ID {obj.id}: {e}'))
                            time.sleep(2) # Wait a bit more on error
                
                if updated:
                    obj.save()
                    # self.stdout.write(self.style.SUCCESS(f'Updated {model_name} {obj.id}'))

        self.stdout.write(self.style.SUCCESS(f'Translation complete! Total fields translated: {total_translated_count}'))
