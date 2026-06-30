from django.conf import settings


class DefaultLanguageMiddleware:
    """Force the configured default language on a visitor's first page load.

    Django's ``LocaleMiddleware`` resolves the active language from the browser's
    ``Accept-Language`` header whenever no language cookie is present. That means
    a browser configured for English (or any other locale) shows GeoNode in that
    language even though ``LANGUAGE_CODE`` is ``"id"``. By rewriting the
    ``Accept-Language`` header to the configured default while the visitor has not
    yet explicitly chosen a language (no ``django_language`` cookie), the very
    first load defaults to Indonesian. Once the user switches languages through
    the language selector, the cookie is set and their choice continues to win.

    This middleware must run *before* ``django.middleware.locale.LocaleMiddleware``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LANGUAGE_COOKIE_NAME not in request.COOKIES:
            request.META["HTTP_ACCEPT_LANGUAGE"] = settings.LANGUAGE_CODE
        return self.get_response(request)
