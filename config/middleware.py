from django.conf import settings
from django.shortcuts import redirect, resolve_url


EXEMPT_PREFIXES = (
    "/accounts/login/",
    "/accounts/logout/",
    "/static/",
    "/media/",
)


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        login_url = resolve_url(getattr(settings, "LOGIN_URL", "/accounts/login/"))
        if request.user.is_authenticated or path.startswith(EXEMPT_PREFIXES) or path.startswith(login_url):
            return self.get_response(request)
        return redirect(f"{login_url}?next={path}")
