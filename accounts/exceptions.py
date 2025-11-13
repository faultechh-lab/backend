# myproject/exceptions.py
from rest_framework.views import exception_handler
from django.utils.translation import gettext_lazy as _

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, Exception):
        if response.status_code == 429:
            wait = getattr(exc, 'wait', None)
            response.data['detail'] = (
                _("Too many requests. Please try again in {wait} seconds.")
                .format(wait=wait) if wait else _("Too many requests. Please try again later.")
            )

    return response
