import os
import json
import time
import logging
from google import genai
from google.genai import types
from decouple import config
from django.db import transaction
from django.db.models.signals import pre_save
from django.core.files.base import ContentFile
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname

logger = logging.getLogger(__name__)

from .models import (
    Model as BoilerModel,
    Brand,
    FaultCodes,
    SparePartImage,
    Parameter,
    ParameterImage,
    BoilerPart,
    BoilerPartImage,
    BoilerCardRepair,
    BoilerCardRepairImage,
    Video,
    RoomTermostat,
    RoomTermostatImage,
    Category,
    BoilerRepairGuide,
    SparePartsDefinitions,
    BoilerWorkingPrinciple,
    BoilerBoardRepairer,
    InstrumentUsage
)

def translate_model_instance(instance):
    """
    Translates a model instance using Gemini API if it's registered for translation.
    Intended to be called from a pre_save signal.
    Uses batching to send all fields in a single API call with timeout protection.
    """
    # Check if model is registered for translation
    try:
        options = translator.get_options_for_model(instance.__class__)
    except Exception:
        return  # Not a translated model

    if not options:
        return

    # Setup Gemini with HTTP timeout
    api_key = config('GEMINI_API_KEY', default=None)
    if not api_key:
        logger.warning("GEMINI_API_KEY not found in env, skipping translation.")
        return

    try:
        # Create client with 20 second timeout to prevent Gunicorn worker kills
        http_options = types.HttpOptions(timeout=20000)  # 20 seconds in ms
        client = genai.Client(api_key=api_key, http_options=http_options)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
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

    # Fetch old instance to check for changes
    old_instance = None
    if instance.pk:
        try:
            old_instance = instance.__class__.objects.get(pk=instance.pk)
        except instance.__class__.DoesNotExist:
            pass

    # Collect all fields that need translation (batching)
    fields_to_translate = {}  # {field_name: {'value': str, 'langs': list, 'max_length': int|None}}
    
    for field_name in options.fields:
        # Source field (TR)
        field_tr = build_localized_fieldname(field_name, 'tr')
        
        # Get current value (check both field_tr and field_name)
        new_val = getattr(instance, field_tr, None)
        if not new_val:
            new_val = getattr(instance, field_name, None)

        # Skip if empty or too short
        if not new_val or (isinstance(new_val, str) and len(new_val.strip()) < 2 and field_name != 'code'):
            continue
            
        # Determine languages to translate
        langs_to_translate = []
        
        is_changed = False
        if not old_instance:
            is_changed = True
        else:
            old_val = getattr(old_instance, field_tr, None)
            if not old_val:
                old_val = getattr(old_instance, field_name, None)
            
            if new_val != old_val:
                is_changed = True

        if is_changed:
            # If changed, translate to ALL languages
            langs_to_translate = list(TARGET_LANGUAGES.keys())
        else:
            # If not changed, only fill missing languages
            for lang in TARGET_LANGUAGES.keys():
                f_lang = build_localized_fieldname(field_name, lang)
                val = getattr(instance, f_lang, None)
                if not val or (isinstance(val, str) and not val.strip()):
                    langs_to_translate.append(lang)
        
        if langs_to_translate:
            model_field = instance._meta.get_field(field_name)
            max_length = getattr(model_field, 'max_length', None)
            fields_to_translate[field_name] = {
                'value': new_val,
                'langs': langs_to_translate,
                'max_length': max_length
            }

    # If no fields need translation, return early
    if not fields_to_translate:
        return

    # Build a single batched prompt for all fields
    try:
        all_langs = set()
        for field_info in fields_to_translate.values():
            all_langs.update(field_info['langs'])
        
        target_list_str = ", ".join(sorted(all_langs))
        
        # Build fields description for prompt
        fields_desc = []
        for field_name, info in fields_to_translate.items():
            max_len_note = f" (max {info['max_length']} chars)" if info['max_length'] else ""
            fields_desc.append(f'"{field_name}"{max_len_note}: "{info["value"]}"')
        
        fields_json_str = "{\n  " + ",\n  ".join(fields_desc) + "\n}"

        prompt = (
            "You are a professional technical translator.\n"
            f"Translate the following fields from Turkish to these languages: {target_list_str}.\n"
            "IMPORTANT: If a max character limit is specified for a field, each translation for that field MUST be shorter than the limit. Summarize/abbreviate if necessary to fit, but keep the meaning.\n"
            "Preserve formatting, HTML tags, headings, bullet points, and units exactly.\n"
            "Use formal technical terminology suitable for boiler/HVAC maintenance.\n"
            "Return ONLY a valid JSON object where the structure is: {\"field_name\": {\"lang_code\": \"translation\", ...}, ...}\n"
            f"Fields to translate:\n{fields_json_str}"
        )

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        if response.text:
            translations = json.loads(response.text)
            
            for field_name, lang_translations in translations.items():
                if field_name not in fields_to_translate:
                    continue
                    
                field_info = fields_to_translate[field_name]
                max_length = field_info['max_length']
                
                if not isinstance(lang_translations, dict):
                    continue
                    
                for lang_code, translated_text in lang_translations.items():
                    if lang_code not in field_info['langs'] or not translated_text:
                        continue
                        
                    if isinstance(translated_text, str):
                        translated_text = translated_text.strip()
                    
                    # Apply max_length truncation as safety net
                    if max_length and len(translated_text) > max_length:
                        translated_text = translated_text[:max_length]

                    f_lang = build_localized_fieldname(field_name, lang_code)
                    setattr(instance, f_lang, translated_text)

    except Exception as e:
        # Log error but don't block save - translation is not critical
        logger.warning(f"Translation error for {instance.__class__.__name__}: {e}")
        print(f"DEBUG: Translation error: {e}")


def translate_model_instance_async(instance):
    """
    Arka plan thread'inde çalışacak çeviri fonksiyonu.
    Instance'ı veritabanından yeniden yükler, çeviriyi yapar ve sinyalleri 
    devre dışı bırakarak kaydeder (sonsuz döngüyü önlemek için).
    """
    import django
    django.setup()
    
    from django.db import connection
    from django.db.models.signals import post_save
    from .signals import auto_translate_handler
    
    try:
        # Veritabanı bağlantısını kapat ve yeniden aç (thread için gerekli)
        connection.close()
        
        # Instance'ı yeniden yükle
        model_class = instance.__class__
        pk = instance.pk
        
        if not pk:
            logger.warning(f"Cannot translate {model_class.__name__}: no pk")
            return
            
        try:
            fresh_instance = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            logger.warning(f"Cannot translate {model_class.__name__} pk={pk}: not found")
            return
        
        # Çeviriyi yap
        translate_model_instance(fresh_instance)
        
        # Sinyali geçici olarak devre dışı bırak (sonsuz döngüyü önle)
        try:
            post_save.disconnect(auto_translate_handler)
        except Exception:
            pass
        
        try:
            # Kaydet
            fresh_instance.save()
            logger.info(f"Translation completed for {model_class.__name__} pk={pk}")
        finally:
            # Sinyali tekrar bağla
            try:
                post_save.connect(auto_translate_handler)
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Async translation error for {instance.__class__.__name__}: {e}")
        print(f"DEBUG: Async translation error: {e}")

@transaction.atomic
def clone_model_with_children(source: BoilerModel, *, name_suffix: str = " (kopya)", make_inactive: bool = False, override_brand: Brand | None = None, _signals_disconnected: bool = False) -> BoilerModel:
    """
    Clone a Model and its children (FaultCodes with SparePartImage, Parameters with ParameterImage)
    - name_suffix: appended to the model name
    - make_inactive: set new model active field to False if True
    - _signals_disconnected: internal flag to prevent redundant signal disconnection
    """
    # Import here to avoid circular import
    from .signals import auto_translate_handler, TRANSLATABLE_MODELS
    
    # Disconnect translation signal to prevent timeouts during bulk copy
    should_disconnect = not _signals_disconnected
    if should_disconnect:
        try:
            pre_save.disconnect(auto_translate_handler)
        except Exception:
            pass
    # Prepare base fields for model clone
    model_fields = {
        "name": f"{getattr(source, 'name', '')}{name_suffix}",
        "category": source.category,
        "brand": override_brand if override_brand is not None else source.brand,
        "active": (False if make_inactive else getattr(source, "active", True)),
        "image": source.image and ContentFile(source.image.read(), name=os.path.basename(source.image.name)) if source.image else None,
    }
    # Also copy translated name_* fields if they exist on the model
    # name_suffix (kopya) sadece varsayılan dile (tr) eklendiği için
    # diğer dillerde (en, de vs.) orijinal ismi olduğu gibi kopyalıyoruz.
    LANGS = ("tr", "en", "es", "it", "fr", "ru", "de", "ar")
    for lang in LANGS:
        attr = f"name_{lang}"
        if hasattr(source, attr):
            val = getattr(source, attr) or ""
            # Eğer dil 'tr' (varsayılan) ise suffix'i burada ekleyebiliriz veya yukarıdaki 'name' zaten hallediyor.
            # Ancak modeltranslation 'name' alanını 'name_tr'ye eşlediği için,
            # name_tr alanına açıkça atama yaparsak, name alanındaki değişikliği ezebiliriz.
            # Bu yüzden sadece tr dışındaki dillerde orijinal değeri kopyalıyoruz.
            if lang != "tr":
                model_fields[attr] = f"{val}" if val else val
            else:
                # name_tr için de suffix ekli halini açıkça belirtelim ki tutarlı olsun
                model_fields[attr] = f"{val}{name_suffix}" if val else f"{name_suffix.strip()}"

    new_model = BoilerModel.objects.create(**model_fields)

    # Clone FaultCodes
    src_faults = FaultCodes.objects.filter(model=source)
    for fc in src_faults:
        # Base fields
        fc_kwargs = dict(
            category=fc.category,
            brand=new_model.brand,
            model=new_model,
            code=fc.code, # Varsayılan dil (TR) için code alanı (modeltranslation bunu code_tr'ye eşitler)
            fault_description=getattr(fc, "fault_description", None),
            active=fc.active,
            image=ContentFile(fc.image.read(), name=os.path.basename(fc.image.name)) if fc.image else None,
        )
        # Copy translated code_* and fault_description_* fields if present
        for lang in LANGS:
            code_attr = f"code_{lang}"
            if hasattr(fc, code_attr):
                val = getattr(fc, code_attr)
                # TR dışındaki dillerde orijinal değeri koru
                if lang != "tr":
                    fc_kwargs[code_attr] = val
                # TR için suffix eklenmiş hali (eğer code alanı suffixli gelmiyorsa buradan eklenebilir ama genelde gerekmez)
                
        for lang in LANGS:
            attr = f"fault_description_{lang}"
            if hasattr(fc, attr):
                val = getattr(fc, attr)
                if lang != "tr":
                    fc_kwargs[attr] = val

        new_fc = FaultCodes.objects.create(**fc_kwargs)

        # Clone SparePartImage for this fault
        spares = fc.spare_part_images.all()
        for sp in spares:
            sp_kwargs = dict(
                fault_code=new_fc,
                name=getattr(sp, "name", None),
                image=ContentFile(sp.image.read(), name=os.path.basename(sp.image.name)) if sp.image else None,
                active=sp.active,
            )
            # Copy translated name_* if present
            for lang in LANGS:
                nattr = f"name_{lang}"
                if hasattr(sp, nattr):
                    val = getattr(sp, nattr)
                    if lang != "tr":
                        sp_kwargs[nattr] = val
            SparePartImage.objects.create(**sp_kwargs)

    # Clone Parameters
    src_params = Parameter.objects.filter(model=source)
    for p in src_params:
        # Base fields
        p_kwargs = dict(
            name=(getattr(p, "name", None) or ""),
            category=p.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(p, "description", None),
            active=p.active,
        )
        # If translated name_* exists, copy
        for lang in LANGS:
            nattr = f"name_{lang}"
            if hasattr(p, nattr):
                val = getattr(p, nattr) or ""
                if lang != "tr":
                    p_kwargs[nattr] = val
        # Copy translated description_* if present
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(p, dattr):
                val = getattr(p, dattr)
                if lang != "tr":
                    p_kwargs[dattr] = val
        new_p = Parameter.objects.create(**p_kwargs)

        # Clone ParameterImage for this parameter
        pimages = p.images.all()
        for pi in pimages:
            img = ContentFile(pi.image.read(), name=os.path.basename(pi.image.name)) if pi.image else None
            ParameterImage.objects.create(parameter=new_p, image=img, active=pi.active)

    # Clone BoilerPart
    src_parts = BoilerPart.objects.filter(model=source)
    for bp in src_parts:
        bp_kwargs = dict(
            name=getattr(bp, "name", None) or "",
            category=bp.category,
            brand=new_model.brand,
            model=new_model,
            active=bp.active,
        )
        for lang in LANGS:
            nattr = f"name_{lang}"
            if hasattr(bp, nattr):
                val = getattr(bp, nattr)
                if lang != "tr":
                    bp_kwargs[nattr] = val
        new_bp = BoilerPart.objects.create(**bp_kwargs)

        # Clone BoilerPartImage
        bp_images = bp.boiler_part_images.all()
        for bpi in bp_images:
            img = ContentFile(bpi.image.read(), name=os.path.basename(bpi.image.name)) if bpi.image else None
            BoilerPartImage.objects.create(boiler_part=new_bp, image=img, active=bpi.active)

    # Clone BoilerCardRepair
    src_repairs = BoilerCardRepair.objects.filter(model=source)
    for br in src_repairs:
        br_kwargs = dict(
            title=getattr(br, "title", None) or "",
            category=br.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(br, "description", None),
            video_url=getattr(br, "video_url", None),
            active=br.active,
        )
        for lang in LANGS:
            tattr = f"title_{lang}"
            if hasattr(br, tattr):
                val = getattr(br, tattr)
                if lang != "tr":
                    br_kwargs[tattr] = val
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(br, dattr):
                val = getattr(br, dattr)
                if lang != "tr":
                    br_kwargs[dattr] = val
        new_br = BoilerCardRepair.objects.create(**br_kwargs)

        # Clone BoilerCardRepairImage
        repair_images = br.images.all()
        for ri in repair_images:
            img = ContentFile(ri.image.read(), name=os.path.basename(ri.image.name)) if ri.image else None
            BoilerCardRepairImage.objects.create(boiler_card_repair=new_br, image=img, active=ri.active)

    # Clone Video
    src_videos = Video.objects.filter(model=source)
    for v in src_videos:
        v_kwargs = dict(
            title=getattr(v, "title", None) or "",
            category=v.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(v, "description", None),
            video_url=getattr(v, "video_url", None),
            image=ContentFile(v.image.read(), name=os.path.basename(v.image.name)) if v.image else None,
            active=v.active,
        )
        for lang in LANGS:
            tattr = f"title_{lang}"
            if hasattr(v, tattr):
                val = getattr(v, tattr)
                if lang != "tr":
                    v_kwargs[tattr] = val
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(v, dattr):
                val = getattr(v, dattr)
                if lang != "tr":
                    v_kwargs[dattr] = val
        Video.objects.create(**v_kwargs)

    # Clone RoomTermostat
    src_rooms = RoomTermostat.objects.filter(model=source)
    for rt in src_rooms:
        rt_kwargs = dict(
            title=getattr(rt, "title", None) or "",
            category=rt.category,
            brand=new_model.brand,
            model=new_model,
            description=getattr(rt, "description", None),
            active=rt.active,
        )
        for lang in LANGS:
            tattr = f"title_{lang}"
            if hasattr(rt, tattr):
                val = getattr(rt, tattr)
                if lang != "tr":
                    rt_kwargs[tattr] = val
        for lang in LANGS:
            dattr = f"description_{lang}"
            if hasattr(rt, dattr):
                val = getattr(rt, dattr)
                if lang != "tr":
                    rt_kwargs[dattr] = val
        new_rt = RoomTermostat.objects.create(**rt_kwargs)

        # Clone RoomTermostatImage
        room_images = rt.images.all()
        for rti in room_images:
            img = ContentFile(rti.image.read(), name=os.path.basename(rti.image.name)) if rti.image else None
            RoomTermostatImage.objects.create(room_thermostat=new_rt, image=img, active=rti.active)

    # Reconnect translation signal if we disconnected it
    if should_disconnect:
        try:
            pre_save.connect(auto_translate_handler)
        except Exception:
            pass

    return new_model


@transaction.atomic
def clone_brand_with_children(source: Brand, *, name_suffix: str = " (kopya)", make_inactive: bool = False) -> Brand:
    # Import here to avoid circular import
    from .signals import auto_translate_handler, TRANSLATABLE_MODELS
    
    # Disconnect translation signal to prevent timeouts during bulk copy
    try:
        pre_save.disconnect(auto_translate_handler)
    except Exception:
        pass
    
    brand_fields = {
        "name": f"{getattr(source, 'name', '')}{name_suffix}",
        "category": source.category,
        "active": (False if make_inactive else getattr(source, "active", True)),
        "image": source.image and ContentFile(source.image.read(), name=os.path.basename(source.image.name)) if source.image else None,
    }
    LANGS = ("tr", "en", "es", "it", "fr", "ru", "de", "ar")
    for lang in LANGS:
        attr = f"name_{lang}"
        if hasattr(source, attr):
            val = getattr(source, attr) or ""
            if lang != "tr":
                brand_fields[attr] = f"{val}" if val else val
            else:
                brand_fields[attr] = f"{val}{name_suffix}" if val else f"{name_suffix.strip()}"

    new_brand = Brand.objects.create(**brand_fields)

    src_models = list(BoilerModel.objects.filter(brand=source))
    for m in src_models:
        clone_model_with_children(m, name_suffix=name_suffix, make_inactive=make_inactive, override_brand=new_brand, _signals_disconnected=True)

    # Reconnect translation signal
    try:
        pre_save.connect(auto_translate_handler)
    except Exception:
        pass

    return new_brand
