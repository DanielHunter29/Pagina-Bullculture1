"""Health check real: comprueba base de datos y caché (Redis en producción)."""
import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health(_request):
    """200 si la API puede atender pedidos; 503 si falla una dependencia.

    No expone detalles del error (solo qué componente falló); el detalle va al log.
    """
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        logger.exception("Health check: base de datos no disponible")
        checks["database"] = "error"
    try:
        cache.set("health:ping", "1", timeout=10)
        checks["cache"] = "ok" if cache.get("health:ping") == "1" else "error"
    except Exception:
        logger.exception("Health check: caché no disponible")
        checks["cache"] = "error"

    healthy = all(v == "ok" for v in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "error", "service": "bullculture-api", "checks": checks},
        status=200 if healthy else 503,
    )
