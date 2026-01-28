from django.db.models.signals import post_save
from django.dispatch import receiver
from threading import Thread
from .services import translate_model_instance_async
from .models import (
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video
)
# Import models from other apps if needed, or rely on explicit registration
from orders.models import Product
from config.models import OnboardModel

TRANSLATABLE_MODELS = [
    Category, Brand, Model, FaultCodes, Parameter, SparePartImage,
    BoilerRepairGuide, BoilerPart, SparePartsDefinitions,
    BoilerWorkingPrinciple, BoilerCardRepair, BoilerBoardRepairer,
    InstrumentUsage, RoomTermostat, Video,
    Product, OnboardModel
]

@receiver(post_save)
def auto_translate_handler(sender, instance, **kwargs):
    """
    Çeviri işlemini arka plan thread'inde çalıştırır.
    Model kaydı hemen tamamlanır, çeviri arka planda yapılır.
    """
    if sender in TRANSLATABLE_MODELS:
        # Arka plan thread'inde çeviri yap - ana isteği bloklamaz
        thread = Thread(target=translate_model_instance_async, args=(instance,))
        thread.daemon = True
        thread.start()

