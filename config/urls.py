from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("api/token/", obtain_auth_token, name="api-token"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="jwt-token"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include("apps.api.urls")),
    path("api/", include("apps.sync.urls")),
    path("offline/", include("apps.sync.offline_urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.crm.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
