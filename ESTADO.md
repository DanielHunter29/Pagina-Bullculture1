# ESTADO.md — Memoria de trabajo BULLCULTURE

## Módulo actual: M2 — API de catálogo (DRF)
## Estado: pendiente (esperando confirmación para iniciar)

## Hitos completados
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

## Próximo paso
- M2: API de catálogo (DRF) — endpoints de categorías; lista de productos con
  filtros (categoría, precio, objetivo), orden y buscador; detalle con stock y
  relacionados; serializers con validación estricta; CORS ya restringido;
  paginación (PAGE_SIZE=12 ya configurado en base).
