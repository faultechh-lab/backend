from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from threading import Thread
from .services import translate_model_instance_async
from .models import (
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video
)
from orders.models import Product
from config.models import OnboardModel
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname
import time

TRANSLATABLE_MODELS = [
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video,
    Product, OnboardModel
]


@receiver(pre_save)
def track_changes_handler(sender, instance, **kwargs):
    """
    Kaydetmeden önce eski değerleri instance üzerinde sakla.
    Bu sayede post_save'de hangi alanların değiştiğini bilebiliriz.
    """
    if sender not in TRANSLATABLE_MODELS:
        return
    
    if not instance.pk:
        # Yeni kayıt - tüm alanlar çevrilmeli
        instance._translation_changed_fields = '__all__'
        return
    
    try:
        options = translator.get_options_for_model(sender)
    except:
        return
    
    if not options:
        return
    
    # Mevcut veritabanı değerlerini al
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._translation_changed_fields = '__all__'
        return
    
    changed_fields = []
    for field_name in options.fields:
        field_tr = build_localized_fieldname(field_name, 'tr')
        
        new_val = getattr(instance, field_tr, None) or getattr(instance, field_name, None)
        old_val = getattr(old_instance, field_tr, None) or getattr(old_instance, field_name, None)
        
        if new_val != old_val:
            changed_fields.append(field_name)
    
    instance._translation_changed_fields = changed_fields if changed_fields else None


@receiver(post_save)
def auto_translate_handler(sender, instance, created, **kwargs):
    """
    Çeviri işlemini arka plan thread'inde çalıştırır.
    Süre bilgisiyle birlikte Notification oluşturur.
    """
    if sender not in TRANSLATABLE_MODELS:
        return
    
    changed_fields = getattr(instance, '_translation_changed_fields', None)
    
    # Değişiklik yoksa çeviri yapma
    if changed_fields is None:
        return
    
    # Nesne bilgisini al
    try:
        object_display = str(instance)[:100]
    except:
        object_display = f"{sender.__name__}"
    
    # Başlangıç zamanını kaydet
    start_time = time.time()
    
    # Arka plan thread'inde çeviri yap
    thread = Thread(
        target=translate_model_instance_async,
        args=(instance, changed_fields, start_time, object_display)
    )
    thread.daemon = True
    thread.start()
