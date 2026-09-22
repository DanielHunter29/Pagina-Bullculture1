"""
Configuración de PRODUCCIÓN.

DEBUG está desactivado y se activan las cabeceras de seguridad. La SECRET_KEY,
los hosts permitidos y las credenciales deben venir SIEMPRE del entorno.
"""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# En producción es obligatorio definir hosts explícitos (sin comodines).
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# Falla el arranque si la SECRET_KEY sigue siendo el valor de desarrollo.
SECRET_KEY = env("DJANGO_SECRET_KEY")

# --- Cabeceras y transporte seguro (endurecimiento final en M10) ---
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# HSTS
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Otras cabeceras
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# --- Logging de eventos críticos ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
