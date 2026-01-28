import time
import os
import json
import logging
from google import genai
from google.genai import types
from decouple import config
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from faults.models import (
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video
)
from orders.models import Product
from config.models import OnboardModel
from modeltranslation.utils import build_localized_fieldname

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Translates database content from Turkish to all supported languages using Gemini API'

    def handle(self, *args, **options):
        api_key = config('GEMINI_API_KEY', default=None)
        if not api_key:
            self.stdout.write(self.style.ERROR('GEMINI_API_KEY not found in .env file.'))
            return

        try:
            # Client-level timeout (60 seconds for bulk operations)
            client = genai.Client(
                api_key=api_key,
                http_options={'timeout': 60000}
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize Gemini client: {e}'))
            return

        TARGET_LANGUAGES = {
            'en': 'English',
            'de': 'German',
            'fr': 'French',
            'ru': 'Russian',
            'es': 'Spanish',
            'it': 'Italian',
            'ar': 'Arabic',
        }

        # Models and fields to translate
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
            
            # Build filter for objects that have at least one missing translation
            # AND have valid source text in TR
            query = Q()
            for field in fields:
                field_tr = build_localized_fieldname(field, 'tr')
                source_present = Q(**{f"{field_tr}__isnull": False}) & ~Q(**{f"{field_tr}": ""})

                target_missing = Q()
                for lang_code in TARGET_LANGUAGES.keys():
                    field_lang = build_localized_fieldname(field, lang_code)
                    target_missing |= Q(**{f"{field_lang}__isnull": True}) | Q(**{f"{field_lang}": ""})
                
                query |= (source_present & target_missing)
            
            objects = ModelClass.objects.filter(query).distinct()
            count = objects.count()
            self.stdout.write(f'Found {count} objects in {model_name} needing translation.')

            for obj in objects:
                fields_to_translate = {}
                
                for field in fields:
                    field_tr = build_localized_fieldname(field, 'tr')
                    source_text = getattr(obj, field_tr, None)
                    if not source_text:
                        source_text = getattr(obj, field, None)

                    if not source_text or (len(str(source_text).strip()) < 2 and field != 'code'):
                        continue

                    langs_to_translate = []
                    for lang_code in TARGET_LANGUAGES.keys():
                        field_lang = build_localized_fieldname(field, lang_code)
                        current_val = getattr(obj, field_lang, None)
                        if current_val is None or (isinstance(current_val, str) and not current_val.strip()):
                            langs_to_translate.append(lang_code)

                    if langs_to_translate:
                        fields_to_translate[field] = {
                            'value': source_text,
                            'langs': langs_to_translate,
                            'field_obj': obj._meta.get_field(field)
                        }

                if not fields_to_translate:
                    continue

                try:
                    self.stdout.write(f'Translating object {obj.id} ({list(fields_to_translate.keys())})...')
                    
                    batch_data = []
                    for f_name, info in fields_to_translate.items():
                        batch_data.append({
                            "id": f_name,
                            "text": info['value'],
                            "targets": info['langs'],
                            "max_chars": getattr(info['field_obj'], 'max_length', None)
                        })

                    prompt = (
                        "You are a professional technical translator for HVAC/Boiler systems.\n"
                        "Translate each 'text' in the provided JSON array into its specific 'targets' languages.\n"
                        "Rules:\n"
                        "1. RETURN ONLY VALID JSON.\n"
                        "2. Preserve HTML, units, and technical terms exactly.\n"
                        "3. Respect 'max_chars' if specified.\n"
                        "4. Format response as: { \"field_id\": { \"lang_code\": \"translation\", ... }, ... }\n"
                        f"Data to translate: {json.dumps(batch_data, ensure_ascii=False)}"
                    )

                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )

                    if response.text:
                        all_translations = json.loads(response.text)
                        obj_updated = False
                        
                        for f_name, translations in all_translations.items():
                            if f_name in fields_to_translate:
                                model_field = fields_to_translate[f_name]['field_obj']
                                for lang_code, text in translations.items():
                                    if lang_code in fields_to_translate[f_name]['langs'] and text:
                                        f_lang = build_localized_fieldname(f_name, lang_code)
                                        
                                        # Safety truncation
                                        final_text = text.strip() if isinstance(text, str) else text
                                        if hasattr(model_field, 'max_length') and model_field.max_length:
                                            if len(final_text) > model_field.max_length:
                                                final_text = final_text[:model_field.max_length]

                                        setattr(obj, f_lang, final_text)
                                        obj_updated = True
                                        total_translated_count += 1
                        
                        if obj_updated:
                            obj.save()

                    # Small delay to avoid rate limits in bulk
                    time.sleep(1.0)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error translating object {obj.id}: {e}'))
                    time.sleep(2.0)

        self.stdout.write(self.style.SUCCESS(f'Translation complete! Total fields translated: {total_translated_count}'))