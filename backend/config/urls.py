"""Rutas raíz del proyecto BULLCULTURE."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health(_request):
    """Endpoint simple para verificar que la API responde."""
    return JsonResponse({"status": "ok", "service": "bullculture-api"})


urlpatterns = [
    # La URL del admin se hará no predecible en M8 (vía variable de entorno).
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    # Las rutas de catálogo, carrito, checkout, etc. se montan en M2+.
]
