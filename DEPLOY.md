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

- `collectstatic` y `migrate` corren automáticamente al iniciar.
- Los estáticos del admin se sirven con **whitenoise**.
- Pon un proxy TLS (nginx/traefik/plataforma) delante del backend: **HTTPS obligatorio**.
- **Backups**: el servicio `db_backup` genera un `pg_dump` comprimido diario en el
  volumen `db_backups` (retención de 14). Restaurar:
  ```bash
  gunzip -c bullculture_YYYYmmdd_HHMMSS.sql.gz | \
    docker compose -f docker-compose.prod.yml exec -T db psql -U $POSTGRES_USER $POSTGRES_DB
  ```

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
