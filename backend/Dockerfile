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

# Instalar dependencias primero (mejor cache de capas)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Código de la aplicación
COPY . .

# Usuario sin privilegios (seguridad)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Comando por defecto (compose lo sobreescribe en dev)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
