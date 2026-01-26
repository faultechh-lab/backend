import time
import json
import google.generativeai as genai
from decouple import config
from django.core.management.base import BaseCommand
from django.db.models import Q
from modeltranslation.utils import build_localized_fieldname

from faults.models import (
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video
)
from orders.models import Product
from config.models import OnboardModel


class Command(BaseCommand):
    help = 'Translate database content from Turkish using Gemini with length safety'

    def handle(self, *args, **options):
        api_key = config('GEMINI_API_KEY', default=None)
        if not api_key:
            self.stdout.write(self.style.ERROR('GEMINI_API_KEY not found'))
            return

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        TARGET_LANGUAGES = {
            'en': 'English',
            'de': 'German',
            'fr': 'French',
            'ru': 'Russian',
            'es': 'Spanish',
            'it': 'Italian',
            'ar': 'Arabic',
        }

        # 🔒 CharField olanlar için HARD LIMIT
        FIELD_MAX_LENGTHS = {
            'title': 100,
            'name': 100,
            'code': 50,
            'business_type': 100,
        }

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

        total = 0

        for ModelClass, fields in translation_map:
            self.stdout.write(self.style.MIGRATE_HEADING(f'{ModelClass.__name__}'))

            query = Q()
            for field in fields:
                for lang in TARGET_LANGUAGES:
                    f_lang = build_localized_fieldname(field, lang)
                    query |= Q(**{f"{f_lang}__isnull": True}) | Q(**{f"{f_lang}": ""})

            objects = ModelClass.objects.filter(query).distinct()

            for obj in objects:
                updated = False

                for field in fields:
                    field_tr = build_localized_fieldname(field, 'tr')
                    source_text = getattr(obj, field_tr, None) or getattr(obj, field, None)

                    if not source_text or len(str(source_text).strip()) < 2:
                        continue

                    langs = []
                    for lang in TARGET_LANGUAGES:
                        f_lang = build_localized_fieldname(field, lang)
                        val = getattr(obj, f_lang, None)
                        if not val or not str(val).strip():
                            langs.append(lang)

                    if not langs:
                        continue

                    max_len = FIELD_MAX_LENGTHS.get(field)

                    length_rule = ""
                    if max_len:
                        length_rule = (
                            f"- Output MUST be at most {max_len} characters (hard limit)\n"
                            "- If longer, shorten while preserving meaning\n"
                        )

                    prompt = (
                        "You are a professional technical translator.\n"
                        f"Translate the following Turkish text into these languages: {', '.join(langs)}.\n"
                        "Preserve meaning, terminology, units, and formatting.\n"
                        "Do NOT add explanations.\n"
                        f"{length_rule}"
                        "Return ONLY valid JSON.\n"
                        "Example: {\"en\": \"...\", \"de\": \"...\"}\n\n"
                        f"Text:\n{source_text}"
                    )

                    try:
                        response = model.generate_content(
                            prompt,
                            generation_config={"response_mime_type": "application/json"}
                        )

                        translations = json.loads(response.text)

                        for lang, text in translations.items():
                            if lang not in langs or not text:
                                continue

                            text = text.strip()

                            # 🛡️ SON DB EMNİYET KEMERİ
                            if max_len and len(text) > max_len:
                                text = text[:max_len]

                            f_lang = build_localized_fieldname(field, lang)
                            setattr(obj, f_lang, text)
                            updated = True
                            total += 1

                        time.sleep(2.5)

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error {ModelClass.__name__} ID {obj.id} field {field}: {e}'
                            )
                        )
                        time.sleep(5)

                if updated:
                    obj.save()

        self.stdout.write(self.style.SUCCESS(f'DONE ✅ Total translated fields: {total}'))
