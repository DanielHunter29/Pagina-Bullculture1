"""Rutas raíz del proyecto BULLCULTURE."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    """Endpoint simple para verificar que la API responde."""
    return JsonResponse({"status": "ok", "service": "bullculture-api"})


urlpatterns = [
    # La URL del admin se hará no predecible en M8 (vía variable de entorno).
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    # Catálogo (M2): /api/categories/ y /api/products/
    path("api/", include("apps.catalog.urls")),
    # Carrito (M5): /api/cart/quote/
    path("api/", include("apps.orders.urls")),
]
