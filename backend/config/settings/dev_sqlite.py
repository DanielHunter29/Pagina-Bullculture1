"""
Configuración de desarrollo con SQLite (sin PostgreSQL/Docker).

Útil para correr el backend localmente y probar el frontend sin levantar
Docker. En producción SIEMPRE se usa PostgreSQL (config.settings.prod).
"""
from .dev import *  # noqa: F401,F403
from .base import BASE_DIR

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
