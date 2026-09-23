"""
Configuración de PRODUCCIÓN.

DEBUG está desactivado y se activan las cabeceras de seguridad. La SECRET_KEY,
los hosts permitidos y las credenciales deben venir SIEMPRE del entorno.
"""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import ADMIN_2FA_ENABLED, REST_FRAMEWORK, env

DEBUG = False

# En producción es obligatorio definir hosts explícitos (sin comodines). Se
# comprueba el entorno directamente: la lectura de base.py trae un valor por
# defecto (localhost) que haría arrancar prod en silencio con hosts erróneos.
if not os.environ.get("DJANGO_ALLOWED_HOSTS", "").strip():
    raise ImproperlyConfigured("Define DJANGO_ALLOWED_HOSTS con los dominios reales de la API.")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS no puede contener '*' en producción.")

# Orígenes de confianza para el CSRF del admin (HTTPS detrás del proxy).
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[f"https://{host.lstrip('.')}" for host in ALLOWED_HOSTS],
)

# 2FA del admin obligatorio en producción. Escape explícito solo para el primer
# arranque o una emergencia: ALLOW_ADMIN_WITHOUT_2FA=True.
if not ADMIN_2FA_ENABLED and not env.bool("ALLOW_ADMIN_WITHOUT_2FA", default=False):
    raise ImproperlyConfigured(
        "ADMIN_2FA_ENABLED debe ser True en producción (enrola con `manage.py setup_2fa`)."
    )

# Falla el arranque si la SECRET_KEY sigue siendo el valor de desarrollo.
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Caché compartida obligatoria (throttling entre workers). Falla si falta.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "KEY_PREFIX": "bullculture",
    }
}

# Detrás del proxy TLS: por defecto 1 salto de confianza.
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=1)
REST_FRAMEWORK = {**REST_FRAMEWORK, "NUM_PROXIES": TRUSTED_PROXY_COUNT}

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

# --- Estáticos comprimidos y versionados (whitenoise) ---
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# --- Correo transaccional (SMTP: Resend o SendGrid) ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.resend.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
# Resend: usuario "resend" + API key como contraseña.
# SendGrid: usuario "apikey" + API key como contraseña.
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="resend")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default=env("RESEND_API_KEY", default=""))

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
        # Eventos críticos del negocio: pagos, inventario, etc.
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Accesos al admin y seguridad (señales de login, axes).
        "bullculture.security": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "axes": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
