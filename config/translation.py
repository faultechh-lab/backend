from modeltranslation.translator import register, TranslationOptions
from .models import OnboardModel

@register(OnboardModel)
class OnboardModelTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
