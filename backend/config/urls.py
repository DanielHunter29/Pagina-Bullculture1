"""Rutas raíz del proyecto BULLCULTURE."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.common.health import health

# 2FA del admin: si está habilitado, se refuerza el sitio de admin con OTP.
if settings.ADMIN_2FA_ENABLED:
    from django_otp.admin import OTPAdminSite

    admin.site.__class__ = OTPAdminSite

admin.site.site_header = "BULLCULTURE · Administración"
admin.site.site_title = "BULLCULTURE"
admin.site.index_title = "Gestión de la tienda"


urlpatterns = [
    # Panel operativo (dashboard + reportes), bajo el prefijo no predecible.
    path(f"{settings.ADMIN_URL}panel/", include("apps.backoffice.urls")),
    # Admin de Django en una URL no predecible (config vía ADMIN_URL).
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/health/", health, name="health"),
    # Catálogo (M2): /api/categories/ y /api/products/
    path("api/", include("apps.catalog.urls")),
    # Carrito y checkout (M5/M6): /api/cart/quote/, /api/checkout/, /api/webhooks/...
    path("api/", include("apps.orders.urls")),
]
