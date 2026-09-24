"""
Configuración de desarrollo con SQLite (sin PostgreSQL/Docker).

Útil para correr el backend localmente y probar el frontend sin levantar
Docker. En producción SIEMPRE se usa PostgreSQL (config.settings.prod).
"""
from .dev import *  # noqa: F401,F403
from .base import BASE_DIR, env

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # SQLITE_PATH permite una base aparte (p. ej. la de los tests e2e).
        "NAME": env("SQLITE_PATH", default=str(BASE_DIR / "db.sqlite3")),
    }
}
