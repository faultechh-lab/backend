import time
import os
import json
import google.generativeai as genai
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

class Command(BaseCommand):
    help = 'Translates database content from Turkish to all supported languages using Gemini API'

    def handle(self, *args, **options):
        api_key = config('GEMINI_API_KEY', default=None)
        if not api_key:
            self.stdout.write(self.style.ERROR('GEMINI_API_KEY not found in .env file.'))
            return

        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash for speed and cost efficiency
        #model = genai.GenerativeModel('gemini-2.5-flash')
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Target languages mapping (code -> name)
        # Source is always 'tr'
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
            query = Q()
            for field in fields:
                for lang_code in TARGET_LANGUAGES.keys():
                    field_lang = build_localized_fieldname(field, lang_code)
                    # Check for None or Empty string
                    query |= Q(**{f"{field_lang}__isnull": True}) | Q(**{f"{field_lang}": ""})
            
            objects = ModelClass.objects.filter(query).distinct()
            count = objects.count()
            self.stdout.write(f'Found {count} objects in {model_name} needing translation.')

            for obj in objects:
                obj_updated = False
                
                for field in fields:
                    field_tr = build_localized_fieldname(field, 'tr')
                    
                    # Get source text (Turkish)
                    source_text = getattr(obj, field_tr, None)
                    if not source_text:
                        # Fallback to base field if specific TR field is empty
                        source_text = getattr(obj, field, None)

                    # Skip if source is empty or too short (unless it's a code)
                    if not source_text or (len(str(source_text).strip()) < 2 and field != 'code'):
                        continue

                    # Identify which languages need translation
                    # We translate ONLY if the target field is empty or None
                    langs_to_translate = []
                    for lang_code in TARGET_LANGUAGES.keys():
                        field_lang = build_localized_fieldname(field, lang_code)
                        current_val = getattr(obj, field_lang, None)
                        
                        # Sadece boşsa çeviri listesine ekle (str kontrolü ile)
                        if current_val is None or (isinstance(current_val, str) and not current_val.strip()):
                            langs_to_translate.append(lang_code)

                    if not langs_to_translate:
                        continue

                    self.stdout.write(f'Translating {field} for {model_name} ID {obj.id} to {langs_to_translate}...')

                    try:
                        # Construct the prompt for batch translation
                        target_list_str = ", ".join([f"{code}" for code in langs_to_translate])
                        
                        # Check for max_length constraint
                        max_len_instruction = ""
                        simplify_instruction = "Do not simplify or shorten.\n"
                        
                        model_field = ModelClass._meta.get_field(field)
                        if hasattr(model_field, 'max_length') and model_field.max_length:
                            # If there's a limit, ask to fit within it
                            max_len_instruction = f"IMPORTANT: Each translation MUST be shorter than {model_field.max_length} characters. Summarize/abbreviate if necessary to fit, but keep the meaning.\n"
                            simplify_instruction = "" # Remove "Do not shorten" if we have a length limit

                        prompt = (
                            "You are a professional technical translator.\n"
                            f"Translate the following text from Turkish to these languages: {target_list_str}.\n"
                            f"{max_len_instruction}"
                            "Preserve formatting, HTML tags, headings, bullet points, and units exactly.\n"
                            f"{simplify_instruction}"
                            "Use formal technical terminology suitable for boiler/HVAC maintenance.\n"
                            "Return ONLY a valid JSON object where keys are the language codes and values are the translations.\n"
                            "Example format: {\"en\": \"Translated text...\", \"de\": \"...\"}\n"
                            f"Text to translate: {source_text}"
                        )

                        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                        
                        if response.text:
                            try:
                                translations = json.loads(response.text)
                                
                                for lang_code, translated_text in translations.items():
                                    if lang_code in langs_to_translate and translated_text:
                                        # Clean up if necessary
                                        if isinstance(translated_text, str):
                                            translated_text = translated_text.strip()
                                        
                                        field_lang = build_localized_fieldname(field, lang_code)
                                        setattr(obj, field_lang, translated_text)
                                        obj_updated = True
                                        total_translated_count += 1
                                
                            except json.JSONDecodeError:
                                self.stdout.write(self.style.ERROR(f'Failed to decode JSON response for {model_name} ID {obj.id}'))
                                # Fallback or retry logic could go here
                        
                        # Rate limiting - simple sleep
                        time.sleep(2.5) 

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error translating {field} for {model_name} ID {obj.id}: {e}'))
                        time.sleep(5)

                if obj_updated:
                    obj.save()

        self.stdout.write(self.style.SUCCESS(f'Translation complete! Total fields translated: {total_translated_count}'))
