"""Configuración de DESARROLLO. No usar en producción."""
from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK

DEBUG = True

# En dev permitimos cualquier host local para comodidad.
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "backend"]

# Interfaz navegable de DRF útil durante el desarrollo.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# Correo por consola en dev.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
