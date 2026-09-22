# ESTADO.md — Memoria de trabajo BULLCULTURE

## Módulo actual: — PROYECTO COMPLETO (M0–M10)
## Estado: listo para revisión / despliegue

## Hitos completados
- [x] M10 Hardening final, QA y despliegue — 2026-09-22
      - Cabeceras de seguridad: middleware propio (`apps/common/middleware.py`)
        con CSP + Permissions-Policy + COOP + nosniff en el backend; en el
        frontend, CSP + HSTS + X-Frame-Options + Referrer/Permissions-Policy en
        `next.config.mjs` (verificadas en vivo). HSTS/SSL/cookies seguras en prod.
      - whitenoise para servir estáticos del admin en el contenedor
        (CompressedManifestStaticFilesStorage en prod).
      - Logs de eventos críticos: pagos e inventario (services), accesos al admin
        (señales user_logged_in/failed en `backoffice/signals.py`), axes; loggers
        configurados en prod.
      - Backups automáticos: `scripts/backup_db.sh` (pg_dump + gzip + retención 14)
        y servicio `db_backup` en `docker-compose.prod.yml`.
      - `docker-compose.prod.yml` (db + backend gunicorn con collectstatic/migrate
        + db_backup) y `DEPLOY.md` (pasos Vercel/Docker + checklist OWASP Top 10).
      - Puntos de control M10 (verificados):
        - `check --deploy` (prod) → 0 issues; DEBUG off; secretos en env.
        - Cabeceras presentes en backend y frontend (curl); errores sin trazas.
        - Suite 66 tests OK; `pip-audit` y `npm audit` sin vulnerabilidades.
        - compose de prod y script de backup validados; CSP no rompe el render.


- [x] M9 SEO técnico y rendimiento — 2026-09-22
      - Metadatos: layout con OpenGraph/Twitter/keywords/canonical; catálogo con
        `generateMetadata` dinámico (título por categoría/búsqueda + canonical);
        detalle con canonical.
      - JSON-LD (`components/seo/JsonLd` + `lib/schema.ts`): Store/Organization
        (con dirección Bogotá + areaServed Colombia) en el layout; Product+Offer
        y BreadcrumbList en el detalle.
      - `app/sitemap.ts` (estáticas + categorías + todos los productos vía API,
        revalidate 1h) y `app/robots.ts` (bloquea /checkout, apunta al sitemap).
      - `app/opengraph-image.tsx`: imagen OG 1200×630 con `next/og`.
      - Imágenes: `lib/images.ts::optimizedImage` (Cloudinary `f_auto,q_auto,w_`)
        aplicado en tarjetas, galería y carrito; `loading="lazy"` + `decoding="async"`.
      - Puntos de control M9 (verificados en vivo):
        - sitemap.xml accesible con 25 URLs; robots.txt correcto.
        - JSON-LD válido (Product/Offer/Organization/Breadcrumb) confirmado en el
          HTML; Offer con precio/COP/InStock.
        - OG image 200 image/png. `npm run build` OK (rutas SEO generadas).
      - Nota: Rich Results Test y Lighthouse/Core Web Vitals deben ejecutarse con
        el sitio desplegado (no hay tooling en este entorno); se aplicaron buenas
        prácticas (canonical, OG, WebP/lazy, sin CLS por aspect-ratio, font swap).


- [x] M8 Admin operativo — 2026-09-22
      - App `accounting`: Expense y SupplierInvoice + admin (migración 0001).
      - App `backoffice` (sin modelos): reports.py (sales_summary, product_
        profitability, expenses_summary, low_stock_products, dashboard_metrics),
        vista de **dashboard** staff-only + template responsivo (ventas hoy/mes,
        pedidos por preparar, alertas de stock bajo, pedidos recientes) y
        **exportes Excel (openpyxl) y PDF (reportlab)** por rango de fechas.
      - Comandos: `check_low_stock` (alerta) y `setup_2fa <usuario>` (enrola TOTP).
      - Admin de Django como panel: Order (cambio de estado), inventario
        (Product/Batch), reglas de descuento, contabilidad — todo registrado.
      - Seguridad: **URL de admin no predecible** (ADMIN_URL env, default /gestion/);
        **django-axes** (bloqueo tras 5 intentos, cooloff 1h); **2FA TOTP**
        (django-otp; OTPAdminSite activable por ADMIN_2FA_ENABLED para no bloquear
        dev); rate limiting de checkout/carrito ya en M5/M6.
      - Puntos de control M8 (7 tests + verificación en vivo):
        - Permisos: dashboard/exports requieren staff (anónimo y no-staff → 302).
        - Exports: Excel con 3 hojas (parseable), PDF válido (%PDF).
        - Alertas de stock: low_stock_products correcto; visible en dashboard.
        - Rentabilidad por producto correcta (ingresos−costo).
        - En vivo (logueado como jefe): dashboard con datos reales del pedido
          aprobado; admin en /gestion/ (URL no predecible); dashboard responsivo
          escritorio/móvil. Suite total 66 OK; pip-audit limpio.


- [x] M7 Correos transaccionales — 2026-09-22
      - `apps/orders/emails.py::send_order_confirmation`: idempotente vía
        reclamación atómica del flag (`filter(email_sent=False).update(email_sent=True)`),
        revierte si el envío falla (permite reintento). Enganchado en la vista del
        webhook DESPUÉS de la transacción (no retiene el lock durante el SMTP).
      - Plantillas `templates/emails/order_confirmation.{html,txt}`: HTML responsivo
        (tablas + estilos inline, max-width 600) con encabezado de marca, ítems,
        totales, descuento y dirección de envío.
      - Settings: `TEMPLATES DIRS`, `DEFAULT_FROM_EMAIL`; prod usa SMTP (Resend
        o SendGrid) por env; dev = consola, tests = locmem.
      - Puntos de control M7 (verificados con 4 tests): un correo por pago
        aprobado; webhook duplicado NO envía otro; pago rechazado no envía;
        `send_order_confirmation` idempotente. Plantilla renderizada OK (sin tags
        sin resolver). Suite total 59 OK.


- [x] M6 Checkout invitado + WOMPI + webhooks — 2026-09-22
      - Modelo: Order + idempotency_key, stock_deducted, email_sent; nuevo
        WebhookEvent (auditoría). Migración 0002.
      - `apps/orders/wompi.py`: firma de integridad (SHA256) y verificación de
        checksum de eventos (hmac.compare_digest, tiempo constante).
      - `services.py`: check_stock, create_order (idempotente por clave),
        deduct_stock (FEFO, select_for_update), process_wompi_transaction
        (idempotente, valida monto vs total, máquina de estados).
      - Endpoints: POST /api/checkout/ (valida datos + Ley 1581, revalida stock
        → 409, crea pedido, firma integridad), POST /api/webhooks/wompi/
        (verifica firma; 401 si inválida), GET /api/orders/<ref>/ (estado, sin PII).
        Vistas con authentication_classes=[] (sin CSRF de sesión).
      - Frontend: /checkout (formulario responsivo + casilla Ley 1581 + resumen
        del backend → redirige al Web Checkout de WOMPI; idempotency_key por
        intento; botón deshabilitado hasta aceptar datos) y /checkout/resultado
        (consulta estado por referencia, limpia carrito si aprobado).
      - Puntos de control M6 (verificados en tests + EN VIVO):
        - Firma inválida → rechazada (401). Duplicado/doble → NO duplica pedido,
          cobro ni stock (idempotencia por clave + estado + flag).
        - En vivo: checkout BC-... total 256.215 (3×creatina −5%) → webhook
          aprobado descontó 40→37; webhook repetido dejó 37; firma mala → 401.
        - 13 tests nuevos (firmas, webhooks dup/inválidos, monto, stock, Ley 1581,
          idempotencia). Suite total 55 OK. Responsivo (escritorio/móvil) OK.


- [x] M5 Carrito + descuento por volumen — 2026-09-22
      - Backend: `apps/orders/services.py::quote_cart` (fuente de verdad de
        importes, Decimal) + endpoint `POST /api/cart/quote/` (AllowAny, throttle
        anon). El navegador solo envía {product, quantity}; precios y descuento
        salen de la BD/reglas. Fusiona líneas duplicadas; marca `exceeds_stock`.
      - `seed_demo` ahora crea 3 reglas de descuento (3+→5%, 5+→10%, 10+→15%).
      - Frontend: `lib/cart.ts` (localStorage + fetchQuote), `CartProvider`
        (estado + persistencia + quote con debounce/abort), `CartButton` (badge
        animado), `CartDrawer` (cajón animado con resumen del backend),
        `AddToCartButton` conectado (abre el cajón = animación al agregar).
      - Puntos de control M5 (verificados):
        - Descuento SOLO en backend: test `test_endpoint_ignores_price_sent_by
          _browser` (precio malicioso ignorado); verificado en vivo (3× Creatina
          → subtotal 269.700, desc. 5% −13.485, total 256.215).
        - Persiste al recargar: localStorage conserva el carrito; header muestra
          "(3)" tras recargar (verificado en navegador).
        - Pruebas unitarias del cálculo: 10 tests (umbral, mejor regla, Decimal
          quantizado, validaciones, merge, exceeds_stock). Suite total 42 OK.
      - Nota: las capturas del navegador dejaron de refrescarse (ventana detrás de
        otra); la verificación se hizo por DOM/JS (fiable) + tests.


- [x] M4 Catálogo y detalle de producto (SSR) — 2026-09-22
      - `lib/api.ts` (cliente tipado, fetch `no-store` = SSR), `lib/format.ts`
        (COP) y `lib/catalog.ts` (goals/orderings).
      - Página `/catalogo` (Server Component, `force-dynamic`): lee searchParams
        → API M2; sidebar de filtros (CatalogFilters, cliente: categoría, precio,
        objetivo, in_stock, búsqueda debounced, orden) que actualiza la URL;
        grilla de ProductCard (microinteracciones CSS) + Pagination que preserva
        filtros. Estados de error y vacío.
      - Página `/producto/[slug]` (SSR + `generateMetadata` con Open Graph):
        galería (cliente, miniaturas), precio, stock, presentación, breadcrumb,
        AddToCartButton (UI lista; carrito real en M5) y relacionados.
      - `loading.tsx` (skeletons) y `not-found.tsx` con estilo de marca.
      - Backend: `config.settings.dev_sqlite` (correr sin Docker) y comando
        `seed_demo` (9 categorías, 14 productos, lotes e imágenes demo).
      - Puntos de control M4 (verificados):
        - **SSR real**: curl a /catalogo y /producto/... muestra nombres, precios
          y "Descripción/relacionados" en el HTML crudo (sin ejecutar JS).
        - Filtros/orden/búsqueda contra la API; paginación preserva filtros.
        - Responsivo: escritorio (sidebar + grilla 3 col) y móvil (filtros
          apilados + grilla 2 col) verificados en el navegador.
        - `tsc --noEmit` 0 errores; 32 tests backend OK.


- [x] M3 Frontend base + design system — 2026-09-21
      - Layout global con Header + Footer + botón flotante de WhatsApp.
      - `components/brand`: BullMark (arte OFICIAL del toro del usuario) y Logo
        horizontal. Variantes "dark" (cara #F8FAFB, fondos oscuros) y "light"
        (cara #3B5875, secciones claras); cuernos/acentos #6C93B6 con brillo
        #88BEDF opcional. Paths en `bullArtwork.ts` (generados desde los SVG del
        usuario, metadata C2PA removida). Favicon `app/icon.svg` (toro sobre
        fondo oscuro redondeado) y copias limpias en `public/brand/`.
      - `components/layout/Header`: sticky con estado "scrolled" (blur+borde),
        nav de escritorio y **menú hamburguesa** animado en móvil (bloquea scroll).
      - `components/layout/Footer`: enlaces a Instagram, TikTok (icono propio) y
        correo; navegación y datos de contacto.
      - `components/layout/WhatsAppButton`: flotante, animado (spring).
      - `components/sections`: Hero (entrada de titular y toro, **parallax** del
        toro al scroll, cuernos con brillo pulsante), CategoryHighlights (4
        categorías con reveal al scroll), ScienceSection (ancla #ciencia).
      - `lib/site.ts`: config central (WhatsApp, redes, correo, navLinks).
      - Puntos de control M3 (verificados en navegador integrado):
        - Escritorio 1440, tablet 768 y **móvil 375** correctos (capturas).
        - En móvil el toro pasa a **fondo atenuado** (opacity 0.14) y el nav a
          hamburguesa (probado: abre/cierra con links + Comprar).
        - `prefers-reduced-motion`: media query global que anula animaciones +
          `useReducedMotion` en cada componente animado.
        - `npm run build` OK (TypeScript sin errores).
      - Bug corregido: Framer sobreescribía la opacidad/translate de Tailwind del
        toro → se separó posicionamiento (CSS wrapper) de animación (motion hijo).


- [x] M2 API de catálogo (DRF) — 2026-09-21
      - `django-filter` 26.1 añadido; `DEFAULT_FILTER_BACKENDS` (filtros + búsqueda
        + orden) en settings base.
      - `apps/catalog`: serializers (Category, ProductList, ProductDetail),
        `ProductFilter` (categoría, price_min/max, objetivo, featured, in_stock),
        ViewSets de solo lectura (lookup por slug) montados en `/api/`:
        `/api/categories/` y `/api/products/`.
      - Stock anotado en el queryset (`Coalesce(Sum(batches__quantity))`) → evita
        N+1; `select_related`/`prefetch_related` para categoría e imágenes.
      - Detalle con `available_stock`, imágenes y hasta 4 productos relacionados
        (misma categoría). NO expone `cost` ni `low_stock_threshold`.
      - Puntos de control M2 (verificados con 16 tests de API):
        - Filtros/orden/búsqueda funcionan; paginación = 12 (PAGE_SIZE).
        - No se exponen campos sensibles (tests explícitos).
        - CORS: origen del frontend autorizado; origen desconocido bloqueado (tests).
        - Producto inactivo → 404; lista excluye inactivos.
      - Suite total: 32 tests OK; `django check` 0 issues; `pip-audit` limpio.


- [x] M1 Modelo de datos y admin base — 2026-09-21
      - 3 apps bajo `apps/`: **catalog** (Category, Product, ProductImage, Batch),
        **discounts** (VolumeDiscountRule), **orders** (Order, OrderItem).
      - Base común `apps/common`: `TimeStampedModel` abstracto y `money.py`
        (dinero con `Decimal`, `quantize_money` a 2 decimales).
      - Stock derivado de lotes (Batch) con FEFO; `available_stock`/`is_low_stock`.
      - Order con datos de invitado, aceptación Ley 1581, estados de pago y envío,
        referencia única `BC-...` (idempotencia M6) y `recalculate_totals()`.
      - Migraciones 0001 para las 3 apps; todo registrado en Django admin con
        inlines (imágenes + lotes en Producto; ítems en Pedido) y recálculo de
        totales al guardar en el admin.
      - Puntos de control M1 (verificados):
        - `makemigrations --check` → sin cambios pendientes (migraciones limpias).
        - `django check` → 0 issues.
        - 16 tests OK: validaciones (no-negativos, %≤100, vencimiento>recepción),
          stock por lotes, descuentos (best_for_quantity), totales con Decimal
          quantizado, y **humo de admin** (altas de categoría/producto+lote).


- [x] M0 Cimientos e infraestructura — 2026-09-21
      - Monorepo con git inicializado (rama `main`).
      - Backend Django 6.1.1 + DRF 3.18.1 + psycopg 3.3.6; settings divididos
        base/dev/prod; `DEBUG` off y cabeceras de seguridad (HSTS, SSL, cookies
        seguras, X-Frame-Options DENY) en prod; endpoint `/api/health/`.
      - Frontend Next.js 16 (App Router, SSR) + React 19 + Tailwind 3 con
        TODOS los tokens de la paleta 4.1 + shadcn/ui (Button) + Framer Motion.
      - `docker-compose.yml` (Postgres 16 + backend) validado con `compose config`.
      - `.env.example` + `.env` (gitignored) con SECRET_KEY generada.

## Puntos de control M0 (verificados)
- [x] `django check` (dev) → 0 issues; `check --deploy` (prod) solo advierte por
      SECRET_KEY corta de prueba (las cabeceras de seguridad están OK).
- [x] `docker compose config` → sintaxis y variables válidas.
      (Nota: `docker compose up` en vivo pendiente de abrir Docker Desktop —
       el demonio no estaba corriendo durante el build.)
- [x] `npm run build` → compila sin errores; TypeScript OK; 3 rutas.
- [x] `pip-audit` → "No known vulnerabilities found".
- [x] `npm audit` → "found 0 vulnerabilities".
- [x] Ningún secreto en el código; `.env`, `node_modules`, `.venv` ignorados por git
      (29 archivos de fuente rastreables, ninguno sensible).
- [x] Página base responsiva (grid 2→3→6 col) que respeta `prefers-reduced-motion`
      (CSS media query + `useReducedMotion` de Framer Motion).

## Decisiones clave
- **Versiones**: se subió de las versiones del brief a las últimas parcheadas por
  seguridad (Django 5.1→6.1.1, DRF→3.18.1, Next 15→16.3.x, React→19.3, ESLint→10)
  porque `pip-audit`/`npm audit` reportaban CVEs. Punto de control lo exigía.
- **Settings divididos**: `config.settings.{base,dev,prod}` seleccionados por
  `DJANGO_SETTINGS_MODULE`. Producción falla si falta SECRET_KEY/ALLOWED_HOSTS.
- **Tema dark-first**: `<html class="dark">`; `:root` = tema claro (secciones ivory),
  `.dark` = tema oscuro por defecto. Tokens semánticos shadcn en HSL + tokens
  `brand.*` con los hex exactos de la paleta.
- **Frontend fuera de compose**: se desplegará en Vercel; en dev corre con `npm run dev`.
- **URL admin no predecible / 2FA / rate limiting**: se implementan en M8 (login seguro).
- **Stock por lotes (M1)**: el stock disponible NO se almacena en Product; se deriva
  de la suma de `Batch.quantity` (fuente de verdad para inventario y vencimientos).
  El descuento de stock atómico (FEFO + `select_for_update`) se hará en M6.
- **Imágenes (M1)**: `ProductImage.image_url` (URLField) por ahora; se migrará a
  Cloudinary en M9 (evita depender de Pillow/almacenamiento local ahora).
- **Objetivo del producto**: `goal` como choice único (filtro simple en M2).
- **Config de tests**: `config/settings/test.py` con SQLite en memoria para correr
  la suite sin depender de PostgreSQL/Docker.

## Pendientes / deuda técnica
- Ejecutar `docker compose up --build` con Docker Desktop abierto para validación
  end-to-end en vivo (config ya validada estáticamente).
- ESLint 10 usa flat config; `.eslintrc.json` podría requerir migrar a
  `eslint.config.mjs` al usar `npm run lint` (no bloquea el build). Revisar en M3.
- `next lint` está deprecado en Next 16; migrar a ESLint CLI cuando toque.

## API disponible para el frontend (M2)
- GET /api/categories/  ·  GET /api/categories/{slug}/
- GET /api/products/    ·  GET /api/products/{slug}/
  Query params: ?category={slug} &price_min= &price_max= &goal= &in_stock=true
                &featured=true &search= &ordering=price|-price|name|created_at
                &page=

## Pendientes / deuda técnica (añadido en M3)
- Toro OFICIAL integrado (arte del usuario). Variante "light" (cara azul) lista
  para cuando existan secciones ivory.
- Lighthouse NO se ejecutó (sin tooling en este entorno); correrlo en M9/M10 con
  contenido real. Se aplicaron buenas prácticas (HTML semántico, aria-labels,
  font-display swap, sin CLS por dimensiones fijas, rel=noopener en externos).
- navLinks/CTAs apuntan a /catalogo(?category=) — ya implementado en M4.
- Imágenes de producto vía <img> (URLField); migrar a next/image + Cloudinary
  (WebP/lazy) en M9. Datos demo usan picsum como placeholder.
- Sin tests e2e de frontend (SSR verificado con curl + navegador); evaluar
  Playwright en M10.
- Para correr sin Docker: backend con `DJANGO_SETTINGS_MODULE=config.settings.dev_sqlite`
  (migrate + seed_demo + runserver) y frontend `npm run dev` (usa NEXT_PUBLIC_API_URL
  / API_URL, con fallback a http://localhost:8000/api).

## Notas M6 / deuda técnica
- `select_for_update` es no-op en SQLite (dev/tests); bloquea de verdad en
  PostgreSQL (prod/Docker). Correr con Docker para validar concurrencia (M10).
- El webhook no tiene throttle (lo llama WOMPI; evitar bloquear reintentos).
  Considerar allowlist de IP de WOMPI en M10.
- Correo transaccional al aprobar: pendiente M7 (ya existe flag email_sent y el
  hook en process_wompi_transaction).
- Para simular pagos localmente hay secretos WOMPI de PRUEBA en .env (gitignored).

## Notas M8 / deuda técnica
- La URL del admin ahora es /gestion/ por defecto (antes /admin/). En prod,
  definir ADMIN_URL con un valor aleatorio propio.
- 2FA desactivado por defecto (ADMIN_2FA_ENABLED=False) para no bloquear dev;
  activarlo en prod y enrolar con `manage.py setup_2fa <usuario>`.
- Superusuario local de prueba: jefe / BullAdmin2026! (solo en la BD sqlite local,
  no versionada).
- Rentabilidad usa el costo ACTUAL del producto (no snapshot al vender); revisar
  si se requiere costo histórico.

## Próximo paso
- Proyecto completo (M0–M10). Antes de producción: (1) `docker compose up` en vivo
  con Docker Desktop para validar concurrencia (select_for_update en Postgres);
  (2) claves reales de WOMPI, Cloudinary y SMTP; (3) Rich Results Test + Lighthouse
  con el sitio desplegado; (4) activar ADMIN_2FA_ENABLED y enrolar 2FA.
