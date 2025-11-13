from django.utils import translation
from django.conf import settings


def _normalize_lang(value: str) -> str:
    if not value:
        return ""
    # e.g. "tr-TR,tr;q=0.9,en;q=0.8" -> "tr"
    first = value.split(",")[0].strip()
    first = first.split(";")[0].strip()
    base = first.split("-")[0].strip().lower()
    return base or ""


class LanguageMiddleware:
    """
    Configurable language middleware.
    Reads language from configured headers or query param, falls back to default.
    Settings (optional):
      - LANGUAGE_HEADER_KEYS: list[str] (default ["X-Language", "Accept-Language"])
      - LANGUAGE_QUERY_PARAM: str (default "lang")
      - LANGUAGE_DEFAULT: str (default settings.LANGUAGE_CODE or "tr")
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.header_keys = getattr(
            settings,
            "LANGUAGE_HEADER_KEYS",
            ["X-Language", "Accept-Language"],
        )
        self.query_param = getattr(settings, "LANGUAGE_QUERY_PARAM", "lang")
        self.default_lang = getattr(
            settings,
            "LANGUAGE_DEFAULT",
            getattr(settings, "LANGUAGE_CODE", "tr"),
        )

    def __call__(self, request):
        lang = None
        # Try headers in order
        for key in self.header_keys:
            val = request.headers.get(key)
            if val:
                lang = _normalize_lang(val)
                if lang:
                    break
        # Try query param
        if not lang:
            qp = request.GET.get(self.query_param)
            lang = _normalize_lang(qp)
        # Fallback default
        if not lang:
            lang = _normalize_lang(self.default_lang) or "tr"

        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response
