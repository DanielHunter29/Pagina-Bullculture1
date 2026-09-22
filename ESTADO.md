# ESTADO.md — Memoria de trabajo BULLCULTURE

## Módulo actual: M1 — Modelo de datos y admin base
## Estado: pendiente (esperando confirmación para iniciar)

## Hitos completados
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

## Pendientes / deuda técnica
- Ejecutar `docker compose up --build` con Docker Desktop abierto para validación
  end-to-end en vivo (config ya validada estáticamente).
- ESLint 10 usa flat config; `.eslintrc.json` podría requerir migrar a
  `eslint.config.mjs` al usar `npm run lint` (no bloquea el build). Revisar en M3.
- `next lint` está deprecado en Next 16; migrar a ESLint CLI cuando toque.

## Próximo paso
- M1: modelar el dominio (Categoría, Producto, Lote con vencimiento,
  ReglaDescuentoPorVolumen, Pedido, ItemPedido…), dinero con `Decimal`,
  migraciones limpias y registro en Django admin.
