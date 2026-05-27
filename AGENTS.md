# Agent Guidelines for FashionVision-AI

React/Vite frontend + FastAPI backend. Detección de prendas con YOLO + matching visual con CLIP.

## Project Structure

```
FashionVision-AI/
├── docker/              - Docker files (Dockerfiles, nginx.conf)
├── docker-compose.yml   - Docker orchestration
├── frontend/            - React 19 + Vite (port 5173)
├── backend/             - FastAPI + YOLO + CLIP (port 8000)
├── docs/                - Documentation
├── scripts/             - Helper scripts (dev-start.sh, etc.)
└── prueba-yolo/         - Legacy/alternate implementation
```

## First Time Setup

```bash
# 1. Clonar e instalar dependencias
git clone <url>
cd FashionVision-AI
cp .env.template .env
# Editar .env: llenar POSTGRES_PASSWORD y SECRET_KEY
# Opcional: llenar CLOUDINARY_* para galería de imágenes

# 2. Base de datos
docker compose up -d db
cd backend && source venv/bin/activate && alembic upgrade head && cd ..

# 3. Backend (desde raíz del proyecto)
source backend/venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# 4. Frontend (otra terminal)
cd frontend && npm install && npm run dev

# 5. Verificar
curl http://localhost:8000/health
curl http://localhost:8000/api/clip/warmup
curl http://localhost:8000/api/detect/classes
# Esperado: {"classes":{"0":"accessories","1":"bags","2":"clothing","3":"shoes"}}
```

## Build/Lint/Test Commands

### Frontend (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Development
npm run dev          # Vite dev server (http://localhost:5173)
npm run build        # Production build to dist/
npm run lint         # ESLint on all files
npm run preview      # Preview production build
npm run test         # Vitest
npm run test:run     # Vitest (single run)
```

### Backend (FastAPI + YOLO + CLIP)

```bash
cd backend
source venv/bin/activate

# Run server (from project ROOT, not from backend folder)
cd /path/to/FashionVision-AI
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Run tests
cd backend && pytest

# Alembic migrations
cd backend && alembic upgrade head
```

## Detection System (YOLO + CLIP)

### Architecture

La detección usa dos capas:

```
1. YOLO (kesimeg/yolov8n-clothing-detection)
   → Detecta regiones (bbox) en la imagen
   → 4 clases genéricas: clothing, shoes, bags, accessories
   → Umbral de confianza: 0.50 (configurable)

2. CLIP (ViT-B-32, laion2b_s34b_b79k)
   → Recorta cada bbox de la imagen
   → Genera embedding de 512 floats
   → Compara contra catálogo de ProductEmbedding (cosine similarity)
   → Retorna el producto más similar (threshold: 0.25)
```

### Detection Flow

```
Cámara → YOLO detecta regiones (bbox) → recorta cada región →
  CLIP genera embedding → busca en catálogo de productos vectorizados →
  retorna catalog_match {product_id, similarity}
```

Si CLIP no encuentra match (similitud < 0.25), se muestra "Prenda no identificada".

### API Endpoints — Detección

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/detect` | Detecta prendas en imagen. YOLO + CLIP matching |
| GET | `/api/detect/product-by-id/{id}` | Datos de producto detectado (tallas, colores, stock) |
| GET | `/api/detect/classes` | Clases del modelo YOLO |
| GET | `/api/detect/health` | Salud del servicio de detección |
| POST | `/api/detect/match-catalog` | Matching CLIP contra catálogo (bbox + imagen) |

### API Endpoints — CLIP Catalog Matching

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/clip/warmup` | Precarga modelo CLIP (~350MB, ~30s primera vez) |
| GET | `/api/catalog/embedding-status` | Estado de vectorización de todos los productos |
| POST | `/api/products/{id}/generate-embedding` | Genera embedding CLIP para un producto |
| DELETE | `/api/products/{id}/embedding` | Elimina embedding de un producto |

### Trained Models

| Modelo | Ubicación | Clases |
|---|---|---|
| YOLO | `backend/models/best.pt` | `accessories, bags, clothing, shoes` (kesimeg/yolov8n-clothing-detection) |
| CLIP | Descarga automática | ViT-B-32, pesos laion2b_s34b_b79k (Apache 2.0) |

## CLIP Catalog Matching

### Product Vectorization

Para que un producto sea detectable por la cámara, necesita un embedding CLIP:

```
Admin → crea producto + sube 1-5 fotos → vectoriza →
  CLIP genera embedding de 512 floats → guarda en product_embeddings
```

#### Vías para vectorizar

| Vía | Ruta | Flujo |
|---|---|---|
| Auto-vectorizar | Inventory → "+ Nuevo Producto" | Al crear, selecciona fotos → "Crear y Vectorizar" |
| Manual | `/admin/catalog` → CatalogManager | Click en producto → subir fotos → "Vectorizar" |
| Con imágenes existentes | CatalogManager → "Vectorizar con imágenes existentes" | Usa URLs de Cloudinary ya guardadas |

#### Requisitos para vectorizar

- 1 a 5 fotos del producto (JPEG, PNG, WebP)
- Si no hay Cloudinary configurado: la vectorización funciona igual, pero sin galería de imágenes
- Threshold de similitud: 0.25 (configurable en `find_best_match`)

### ProductEmbedding Table

```sql
product_embeddings (
    product_id UUID FK → products.id,
    embedding  JSONB,          -- 512 floats
    images_used INTEGER,       -- cuántas fotos se usaron
    generated_at TIMESTAMPTZ
)
```

## Product Vectorization Flow

```
Admin crea producto:
  1. POST /api/products                           → crea en DB
  2. POST /api/products/{id}/images × N           → Cloudinary (galería)
  3. POST /api/products/{id}/generate-embedding   → CLIP embedding

Producto vectorizado = detectable por cámara. Sin reentrenar YOLO.
```

## Environment Variables

```bash
# REQUERIDO — Primer setup
cp .env.template .env

# REQUERIDO — Editar en .env
POSTGRES_PASSWORD=your_db_password_here
SECRET_KEY=your_secret_key_here

# OPCIONAL — Cloudinary (galería de imágenes)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# OPCIONAL — Sobrescribir sin commitear
cp .env .env.local    # editar .env.local con credenciales reales
```

El archivo `.env.local` tiene prioridad sobre `.env` y **nunca se commitea**.

### Frontend

Crear `.env.local` en `frontend/`:
- `VITE_API_URL` — Backend API endpoint (default: http://localhost:8000)
- Variables deben tener prefijo `VITE_`

## Code Style Guidelines

### JavaScript/React (Frontend)

**General**
- ES modules (`import`/`export`) — `type: "module"` en package.json
- Componentes funcionales con hooks
- `.jsx` para JSX, `.js` para utilidades
- 2-space indent, single quotes, semicolons
- Trailing commas en multi-line, max ~100 chars

**Imports** — React → externos → internos → relativos → CSS

**Naming**
- Componentes: PascalCase (`UserProfile`, `ButtonGroup`)
- Hooks: camelCase con `use` prefix (`useCamera`)
- API services: camelCase (`detectClothes`, `getEmbeddingStatus`)
- Files: kebab-case services/utils, PascalCase.jsx componentes

### ESLint

Flat config (`eslint.config.js`): `@eslint/js`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
- `no-unused-vars` ignora vars que empiezan con mayúscula (JSX components)

### Python (Backend)

- PEP 8, 4-space indent
- Type hints, snake_case funciones/variables
- PascalCase clases, UPPER_SNAKE_CASE constantes

## File Organization

```
frontend/src/
├── App.jsx              # Root routing
├── main.jsx             # Entry point
├── components/          # Reusable UI
├── pages/               # Route pages
│   ├── login.jsx        # Auth
│   ├── Dashboard.jsx    # Admin dashboard
│   ├── Inventory.jsx    # Product CRUD
│   ├── CatalogManager.jsx  # CLIP vectorization
│   ├── ClientDetection.jsx # Camera detection
│   ├── Cashier.jsx      # POS / cart management
│   └── Reportes.jsx     # Sales reports
├── hooks/               # Custom hooks
├── services/            # API clients (api.js, catalogService.js)
└── styles/              # CSS per page

backend/
├── app/
│   ├── main.py          # FastAPI app (all endpoints)
│   ├── config.py        # Settings / env vars
│   ├── database.py      # Async engine + session
│   ├── dependencies.py  # Auth guards
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic schemas
│   └── services/        # Business logic (detection, clip_matcher, cloudinary, etc.)
├── models/              # YOLO weights (best.pt)
├── alembic/             # DB migrations
└── tests/               # Pytest test suite
```

## Key Technologies

### Frontend
- React 19.2.0, React Router DOM 7.13.2, Recharts 3.8.1
- Vite 7.3.1, ESLint 9.39.1, Vitest 4.1.5

### Backend
- FastAPI + Uvicorn (async)
- Ultralytics YOLO (kesimeg/yolov8n-clothing-detection)
- Open CLIP (ViT-B-32, laion2b_s34b_b79k, Apache 2.0)
- SQLAlchemy 2.0 async + PostgreSQL 16 + Alembic
- Torch 2.5.1, Pillow, OpenCV headless
- Cloudinary SDK (image upload)

## Docker Deployment

### Services (docker-compose.yml)

| Service | Port | Description |
|---------|------|-------------|
| frontend | 80 | Nginx serving React build |
| backend | 8000 | FastAPI + YOLO + CLIP |
| db | 5432 | PostgreSQL 16 |

### Quick Docker

```bash
docker compose up -d              # Start all
docker compose logs -f backend    # View logs
docker compose down               # Stop all
```

### Development Mode

```bash
# DB (Docker) + Backend (local) + Frontend (local)
docker compose up -d db
cd /path/to/FashionVision-AI
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0
cd frontend && npm run dev
```
