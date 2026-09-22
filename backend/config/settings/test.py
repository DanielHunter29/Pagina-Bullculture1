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
