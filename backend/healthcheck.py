"""Healthcheck del contenedor (docker-compose): GET /api/health/ local.

Se envía el Host de producción y X-Forwarded-Proto=https para que Django no
rechace el host ni redirija a HTTPS. Sale con 0 si la API responde 200.
"""
import os
import sys
import urllib.request

host = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")[0].strip() or "localhost"
request = urllib.request.Request(
    "http://127.0.0.1:8000/api/health/",
    headers={"Host": host, "X-Forwarded-Proto": "https"},
)
try:
    with urllib.request.urlopen(request, timeout=5) as resp:
        sys.exit(0 if resp.status == 200 else 1)
except Exception:
    sys.exit(1)
