# BULLCULTURE — E-commerce de suplementación deportiva

Tienda de suplementos, ropa y equipamiento deportivo (Bogotá, Colombia).
Monorepo con **backend Django + DRF + PostgreSQL** y **frontend Next.js**.

> Construcción incremental por módulos. El progreso vive en [`ESTADO.md`](./ESTADO.md).

## Stack

| Capa       | Tecnología |
|------------|------------|
| Backend    | Django 6 · Django REST Framework · PostgreSQL 16 |
| Frontend   | Next.js 16 (App Router, SSR) · React 19 · TypeScript |
| Estilos    | Tailwind CSS 3 (tokens de marca) · shadcn/ui |
| Animación  | Framer Motion |
| Infra dev  | Docker Compose (backend + DB) |
| Despliegue | Backend + DB en Docker · Frontend en Vercel |

## Requisitos previos

- Docker Desktop (para backend + DB)
- Node.js 20+ (para el frontend)
- Python 3.13 (opcional, solo si corres el backend sin Docker)

## Puesta en marcha

```bash
# 1. Variables de entorno (copia y ajusta)
cp .env.example .env

# 2. Backend + base de datos (requiere Docker Desktop abierto)
docker compose up --build
#   API:   http://localhost:8000/api/health/
#   Admin: http://localhost:8000/admin/

# 3. Frontend (en otra terminal)
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
#   Web: http://localhost:3000
```

## Estructura

```
.
├── backend/            # API Django + DRF
│   ├── config/         # Proyecto (settings base/dev/prod, urls, wsgi, asgi)
│   └── apps/           # Apps de dominio (catálogo, pedidos… se agregan por módulo)
├── frontend/           # Next.js (App Router)
│   ├── app/            # Rutas y layout
│   ├── components/ui/  # Design system (shadcn/ui)
│   └── lib/            # Utilidades
├── docker-compose.yml
├── .env.example        # Plantilla de entorno (el .env real NO se versiona)
└── ESTADO.md           # Memoria de trabajo / progreso por módulos
```

## Seguridad

- Secretos solo en variables de entorno (`.env` está en `.gitignore`).
- `DEBUG` desactivado en producción; cabeceras de seguridad en `config/settings/prod.py`.
- CORS restringido al dominio del frontend.
- Dependencias auditadas con `pip-audit` y `npm audit` (0 vulnerabilidades).
