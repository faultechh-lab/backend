from django.db.models.signals import pre_save
from django.dispatch import receiver
from .services import translate_model_instance
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

@receiver(pre_save)
def auto_translate_handler(sender, instance, **kwargs):
    if sender in TRANSLATABLE_MODELS:
        translate_model_instance(instance)
