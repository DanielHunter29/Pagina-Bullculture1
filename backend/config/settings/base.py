"""
Configuración base de BULLCULTURE compartida por todos los entornos.

Los valores sensibles (SECRET_KEY, credenciales de DB) SIEMPRE se leen de
variables de entorno; nunca se escriben en el código (ver .env.example).
"""
from pathlib import Path

import environ

# BASE_DIR apunta a /backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Lectura de variables de entorno ---
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
)

# Si existe un archivo .env en la raíz del repo, se carga (útil fuera de Docker).
_env_file = BASE_DIR.parent / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

# --- Seguridad base ---
SECRET_KEY = env("DJANGO_SECRET_KEY", default="inseguro-solo-para-arranque-local")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# --- Aplicaciones ---
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "corsheaders",
    "axes",  # bloqueo por intentos fallidos de login
    "django_otp",  # 2FA (TOTP)
    "django_otp.plugins.otp_totp",
]

# Apps propias del proyecto.
LOCAL_APPS = [
    "apps.catalog",
    "apps.discounts",
    "apps.orders",
    "apps.accounting",
    "apps.backoffice",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # antes de CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",  # tras autenticación (2FA)
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # AxesMiddleware debe ir al final.
    "axes.middleware.AxesMiddleware",
]

# --- Backends de autenticación (django-axes primero) ---
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de datos (PostgreSQL) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="bullculture"),
        "USER": env("POSTGRES_USER", default="bullculture"),
        "PASSWORD": env("POSTGRES_PASSWORD", default=""),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

# --- Validación de contraseñas ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalización (Bogotá, Colombia) ---
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos y media ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "120/min",
    },
}

# --- CORS: solo el dominio del frontend puede consumir la API ---
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

# --- URL pública del frontend (para redirecciones de pago) ---
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# --- Correo transaccional (M7) ---
# Dev usa consola (dev.py) y tests usan locmem (test.py). En producción se usa
# SMTP (Resend o SendGrid) configurado por variables de entorno en prod.py.
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="BULLCULTURE <no-reply@bullculture.co>"
)

# --- Admin operativo (M8) ---
# URL del admin NO predecible: definir en producción vía variable de entorno.
# Debe terminar en "/" y no empezar con "/".
ADMIN_URL = env("ADMIN_URL", default="gestion/")

# Umbral por defecto para alertas de stock bajo (además del de cada producto).
LOW_STOCK_THRESHOLD = env.int("LOW_STOCK_THRESHOLD", default=5)

# 2FA del admin (TOTP). Desactivado por defecto para no bloquear en desarrollo;
# actívalo en producción y enrola un dispositivo con `manage.py setup_2fa`.
ADMIN_2FA_ENABLED = env.bool("ADMIN_2FA_ENABLED", default=False)

# --- django-axes: bloqueo tras intentos fallidos de login ---
AXES_ENABLED = env.bool("AXES_ENABLED", default=True)
AXES_FAILURE_LIMIT = env.int("AXES_FAILURE_LIMIT", default=5)
AXES_COOLOFF_TIME = env.int("AXES_COOLOFF_HOURS", default=1)  # horas
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]

# --- Pasarela de pagos WOMPI (M6) ---
WOMPI = {
    "PUBLIC_KEY": env("WOMPI_PUBLIC_KEY", default=""),
    "PRIVATE_KEY": env("WOMPI_PRIVATE_KEY", default=""),
    "EVENTS_SECRET": env("WOMPI_EVENTS_SECRET", default=""),
    "INTEGRITY_SECRET": env("WOMPI_INTEGRITY_SECRET", default=""),
    "CURRENCY": "COP",
    # Web Checkout de WOMPI (redirección).
    "CHECKOUT_URL": env("WOMPI_CHECKOUT_URL", default="https://checkout.wompi.co/p/"),
}

# En dev el navegador puede renderizar la API; el renderer HTML se añade en dev.py
