# ==========================================================================
# BULLCULTURE — Imagen del backend (Django + DRF)
# ==========================================================================
FROM python:3.13-slim

# Buenas prácticas de Python en contenedor
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema mínimas para psycopg
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias primero (mejor cache de capas). Solo las de producción.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Código de la aplicación
COPY . .

# Estáticos del admin generados en el build (no en cada arranque). Los valores
# son de relleno: collectstatic no usa la BD, Redis ni secretos reales.
RUN DJANGO_SETTINGS_MODULE=config.settings.prod \
    DJANGO_SECRET_KEY=build-only-not-secret \
    DJANGO_ALLOWED_HOSTS=build.invalid \
    REDIS_URL=redis://build.invalid:6379/0 \
    ADMIN_2FA_ENABLED=True \
    python manage.py collectstatic --noinput

# Usuario sin privilegios (seguridad)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# gunicorn lee GUNICORN_CMD_ARGS: ajustable por entorno sin cambiar la imagen
# (p. ej. --workers según los núcleos del VPS: 2 × núcleos + 1).
ENV GUNICORN_CMD_ARGS="--bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile -"

HEALTHCHECK --interval=30s --timeout=6s --start-period=20s --retries=3 \
    CMD ["python", "healthcheck.py"]

CMD ["gunicorn", "config.wsgi:application"]
