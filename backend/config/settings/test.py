"""Configuración para ejecutar la suite de pruebas.

Usa SQLite en memoria para que los tests corran rápido y sin depender de
PostgreSQL/Docker. Las migraciones son agnósticas del motor.
"""
from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Hasher rápido (solo pruebas).
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# django-axes desactivado en pruebas (evita interferir con el login de tests).
AXES_ENABLED = False
ADMIN_2FA_ENABLED = False

# Sin llamadas de red a WOMPI en la suite (los tests que la cubren la simulan).
WOMPI_VERIFY_WITH_API = False
