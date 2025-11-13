from modeltranslation.translator import register, TranslationOptions
from .models import (Category, Brand, Model, FaultCodes, Parameter,SparePartImage,BoilerRepairGuide,BoilerPart,
SparePartsDefinitions,BoilerWorkingPrinciple,BoilerCardRepair,BoilerBoardRepairer,InstrumentUsage,Video,RoomTermostat)

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Model)
class ModelTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(FaultCodes)
class FaultCodesTranslationOptions(TranslationOptions):
    fields = ('code', 'fault_description')

@register(Parameter)
class ParameterTranslationOptions(TranslationOptions):
    fields = ('name','description')


@register(SparePartImage)
class SparePartImageTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(BoilerRepairGuide)
class BoilerRepairGuideTranslationOptions(TranslationOptions):
    fields = ('content','title')

@register(BoilerPart)
class BoilerPartTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(SparePartsDefinitions)
class SparePartsDefinitionsTranslationOptions(TranslationOptions):
    fields = ('name','description',)

@register(BoilerWorkingPrinciple)
class BoilerWorkingPrincipleTranslationOptions(TranslationOptions):
    fields = ('title','description')

@register(BoilerCardRepair)
class BoilerCardRepairTranslationOptions(TranslationOptions):
    fields = ('title','description')

@register(BoilerBoardRepairer)
class BoilerBoardRepairerTranslationOptions(TranslationOptions):
    fields = ('name','business_type')

@register(InstrumentUsage)
class InstrumentUsageTranslationOptions(TranslationOptions):
    fields = ('content','title')

@register(RoomTermostat)
class RoomTermostatTranslationOptions(TranslationOptions):
    fields = ('title','description')

@register(Video)
class VideoTranslationOptions(TranslationOptions):
    fields = ('title','description')
