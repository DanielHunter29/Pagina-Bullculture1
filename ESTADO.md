# ESTADO.md — Memoria de trabajo BULLCULTURE

## Módulo actual: M4 — Catálogo y detalle de producto (SSR)
## Estado: pendiente (esperando confirmación para iniciar)

## Hitos completados
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
- navLinks/CTAs apuntan a /catalogo(?category=) que se implementa en M4.

## Próximo paso
- M4: Catálogo y detalle de producto con SSR — página /catalogo (filtros/búsqueda
  contra la API M2) con tarjetas de producto y microinteracciones; /producto/[slug]
  con fotos, descripción, precio, stock y relacionados; render del lado del servidor.
