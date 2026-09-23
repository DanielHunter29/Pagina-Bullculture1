# Despliegue de BULLCULTURE

Backend + PostgreSQL en **Docker**; frontend en **Vercel**.

## 1. Variables de entorno (producción)

Copia `.env.example` a `.env` y define valores reales. Claves críticas:

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<64+ chars aleatorios>
DJANGO_ALLOWED_HOSTS=api.bullculture.co
CORS_ALLOWED_ORIGINS=https://bullculture.co
FRONTEND_URL=https://bullculture.co
ADMIN_URL=<ruta-aleatoria>/           # p.ej. panel-9f3ax7/
ADMIN_2FA_ENABLED=True
POSTGRES_DB=... POSTGRES_USER=... POSTGRES_PASSWORD=<fuerte>
WOMPI_PUBLIC_KEY=... WOMPI_PRIVATE_KEY=... WOMPI_EVENTS_SECRET=... WOMPI_INTEGRITY_SECRET=...
EMAIL_HOST=smtp.resend.com EMAIL_HOST_USER=resend EMAIL_HOST_PASSWORD=<API key>
DEFAULT_FROM_EMAIL=BULLCULTURE <no-reply@bullculture.co>
CLOUDINARY_URL=cloudinary://...
ADMIN_2FA_ENABLED=True es OBLIGATORIO: prod no arranca sin él
TRUSTED_PROXY_COUNT=1                 # proxies delante del backend (nginx/traefik)
STAFF_ALERT_EMAILS=operaciones@bullculture.co   # alertas de pedidos por revisar
# REDIS_URL la define docker-compose.prod.yml (redis://redis:6379/0)
```

Genera la SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 2. Backend + DB (Docker)

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_2fa <usuario>   # enrola 2FA
```

- `collectstatic` corre al construir la imagen; `migrate` corre en el servicio
  `migrate` (una vez por despliegue) y `backend`/`scheduler` arrancan solo si
  terminó bien. Para un despliegue nuevo basta con
  `docker compose -f docker-compose.prod.yml up -d --build`.
- Workers de gunicorn: `GUNICORN_CMD_ARGS` en `.env` (por defecto 3 workers;
  recomendado 2 × núcleos del VPS + 1).
- `GET /api/health/` comprueba base de datos y Redis (503 si falla alguno); el
  contenedor `backend` lo usa como healthcheck (`docker compose ps`).
- Errores a Sentry (opcional): define `SENTRY_DSN`. Nunca se envía PII.
- El servicio `scheduler` ejecuta `run_maintenance` cada 15 min: reintenta los
  correos de confirmación fallidos (hasta `EMAIL_RETRY_MAX_AGE_DAYS`) y marca
  como `expirado` los pedidos pendientes con más de `PENDING_ORDER_TTL_HOURS`.
  Un pedido expirado se aprueba igual si WOMPI confirma un pago tardío.
- El backend necesita **salida HTTPS a `production.wompi.co`** (o `sandbox.`):
  cada webhook se confirma contra la API de WOMPI y la página de resultado
  concilia el pago si el webhook tarda. Si la API no responde, se aplica el
  evento firmado (queda en el log).
- Los estáticos del admin se sirven con **whitenoise**.
- Pon un proxy TLS (nginx/traefik/plataforma) delante del backend: **HTTPS obligatorio**.
- El proxy debe **añadir** la IP del cliente a `X-Forwarded-For` (nginx:
  `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`) y enviar
  `X-Forwarded-Proto`. Si hay más de un proxy en cadena (p. ej. CDN + nginx),
  ajusta `TRUSTED_PROXY_COUNT`; de ello dependen el rate limiting y el bloqueo
  de axes.
- **Redis** (servicio `redis`) es la caché compartida del rate limiting;
  `config.settings.prod` no arranca sin `REDIS_URL` (compose ya la define).
- **Backups**: el servicio `db_backup` genera a diario un `pg_dump` en formato
  custom (`.dump`, comprimido) en el volumen `db_backups`, **verificado** con
  `pg_restore --list` antes de rotar (retención de 14). Un fallo no borra los
  backups anteriores. Restaurar:
  ```bash
  docker compose -f docker-compose.prod.yml exec -T db \
    pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists < bullculture_YYYYmmdd_HHMMSS.dump
  ```
  Recomendado: copiar periódicamente el volumen `db_backups` fuera del servidor
  (S3/Backblaze); hoy los backups viven en el mismo host que la base.

## 3. Frontend (Vercel)

- Importa el repo, root del proyecto: `frontend/`.
- Variables: `NEXT_PUBLIC_API_URL=https://api.bullculture.co/api`,
  `NEXT_PUBLIC_SITE_URL=https://bullculture.co`.
- Vercel provee HTTPS y CDN. Las cabeceras de seguridad (CSP, etc.) están en
  `next.config.mjs`.

## 4. WOMPI

- Configura el webhook de eventos a `https://api.bullculture.co/api/webhooks/wompi/`.
- El backend verifica el checksum de cada evento con `WOMPI_EVENTS_SECRET`.

## 5. Post-despliegue

- [ ] `https://bullculture.co/sitemap.xml` y `/robots.txt` accesibles.
- [ ] Rich Results Test (Google) valida el JSON-LD de un producto.
- [ ] Lighthouse: SEO y Core Web Vitals en móvil.
- [ ] Pago de prueba WOMPI → correo de confirmación recibido.

---

## Checklist OWASP Top 10 (repaso)

| # | Riesgo | Mitigación en BULLCULTURE |
|---|--------|----------------------------|
| A01 | Control de acceso roto | Admin staff-only; dashboard/reportes con `staff_member_required`; pedidos accesibles solo por referencia no adivinable; sin endpoints de listado de pedidos públicos. |
| A02 | Fallos criptográficos | HTTPS + HSTS; cookies `Secure`/`HttpOnly`; firmas WOMPI (integridad + checksum) con SHA256 y `hmac.compare_digest`; secretos solo en env. |
| A03 | Inyección | ORM de Django (sin SQL crudo); serializers DRF validan tipo/longitud/formato; React escapa el contenido; JSON-LD escapa `<`. |
| A04 | Diseño inseguro | Precios/descuentos/totales calculados solo en backend; idempotencia de pedido/cobro/stock/correo; revalidación de stock antes del pago. |
| A05 | Mala configuración | `DEBUG=False`; cabeceras (CSP, X-Frame-Options DENY, nosniff, Referrer-Policy, Permissions-Policy); URL de admin no predecible; CORS restringido. |
| A06 | Componentes vulnerables | `pip-audit` y `npm audit` sin vulnerabilidades; dependencias en versiones parcheadas. |
| A07 | Fallos de identificación/autenticación | Contraseñas fuertes (validadores, min 10); **2FA (TOTP)**; **bloqueo tras 5 intentos** (django-axes); rate limiting en checkout/carrito. |
| A08 | Integridad de datos/software | Firma de integridad WOMPI; verificación de checksum de webhooks (se rechaza lo no verificado); validación de monto vs total. |
| A09 | Fallos de logging/monitoreo | Logs de pagos, inventario y accesos al admin (señales de login + axes); auditoría de webhooks (`WebhookEvent`). |
| A10 | SSRF | El backend no hace fetch de URLs provistas por el usuario; imágenes por URL controlada (Cloudinary). |

Otros: **Habeas Data (Ley 1581/2012)** — casilla obligatoria en checkout con
fecha de aceptación; los errores en producción no exponen trazas (`DEBUG=False`).
