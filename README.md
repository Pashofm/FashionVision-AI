# FashionVision AI

**Sistema Inteligente de Reconocimiento de Prendas y Análisis Predictivo**

FashionVision AI es una solución tecnológica diseñada para pequeñas y medianas tiendas de ropa. Automatiza el control de inventario y facilita el proceso de venta mediante visión por computadora (YOLO) y análisis de datos.

---

## Tabla de Contenidos

- [Stack Tecnológico](#stack-tecnológico)
- [Requisitos Previos](#requisitos-previos)
- [Instalación Rápida](#instalación-rápida)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Modos de Uso](#modos-de-uso)
- [Documentación](#documentación)
- [Endpoints de la API](#endpoints-de-la-api)

---

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Frontend | React 19 + Vite | 19.2.0 / 7.3.1 |
| Backend | Python 3.12 + FastAPI | 0.115.0 |
| Base de Datos | PostgreSQL 16 | - |
| Modelo IA | YOLO (Ultralytics) | 8.3.40 |
| ORM | SQLAlchemy + Alembic | 2.0.35 / 1.18.4 |
| Contenedores | Docker + Docker Compose | - |

---

## Requisitos Previos

| Software | Versión | Notas |
|----------|---------|-------|
| Docker Desktop | 4.0+ | Para base de datos PostgreSQL + pgAdmin |
| Git | Any | Para clonar repositorio |
| Sudo/Admin | - | Para instalar dependencias del sistema |

### Dependencias del Sistema Operativo

**Antes de ejecutar el proyecto**, necesitas instalar las dependencias del sistema. Consulta [docs/SYSTEM_REQUIREMENTS.md](./docs/SYSTEM_REQUIREMENTS.md) para instrucciones completas.

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y \
    build-essential libffi-dev python3-dev libjpeg-dev libpq-dev git curl docker.io docker-compose
```

**Verificación crítica** (después de instalar dependencias):
```bash
python3 -c "import _ctypes" && echo "OK: _ctypes funciona"
```

**Importante:** Python 3.12 y Node.js 18+ se instalan automáticamente por los scripts de setup. No necesitas instalarlos manualmente.

---

## Instalación Rápida

### Paso 1: Clonar el repositorio

```bash
git clone <repo-url> FashionVision-AI
cd FashionVision-AI
```

### Paso 2: Instalar dependencias del sistema

```bash
sudo apt-get update && sudo apt-get install -y build-essential libffi-dev python3-dev libjpeg-dev libpq-dev git curl docker.io docker-compose
```

### Paso 3: Ejecutar setup (primera vez)

```bash
./scripts/setup.sh
```

> **Nota:** La primera ejecución puede tardar **10-20 minutos** porque instala pyenv, Python 3.12, nvm, Node.js 18, y compila paquetes como torch.

### Paso 4: Iniciar servicios (sesiones siguientes)

```bash
./scripts/dev-start.sh
```

### Paso 5: Iniciar backend y frontend

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## Arquitectura del Sistema

### Modo Desarrollo (Local + Docker)

```
┌─────────────────────────────────────────────────────────────┐
│                    Tu Equipo de Desarrollo                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│   │   Frontend   │   │   Backend    │   │     DB       │   │
│   │    Local     │   │    Local     │   │   Docker     │   │
│   │   :5173      │   │   :8000      │   │   :5432      │   │
│   │  (Vite)      │   │  (HotReload) │   │              │   │
│   └──────────────┘   └──────────────┘   └──────────────┘   │
│                                              │              │
│                                              ▼              │
│                                       ┌──────────────┐     │
│                                       │   pgAdmin    │     │
│                                       │   Docker     │     │
│                                       │   :5050      │     │
│                                       └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Modo Producción (Docker Completo)

```bash
# Todo en contenedores Docker
docker compose up -d
```

---

## Modos de Uso

### Modo A: Desarrollo (Hot-Reload Activo)

Para desarrollo activo cuando necesitas iterar rápido.

```bash
# 1. Iniciar base de datos + pgAdmin en Docker
docker compose up -d db pgadmin

# 2. Backend con hot-reload
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# 3. Frontend con hot-reload
cd frontend
npm run dev
```

**Acceso:**
| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

---

### Modo B: Testing / Demo (Docker Completo)

Para testing, demos a clientes, o cuando no necesitas hot-reload.

```bash
# Todo en Docker (comando único)
docker compose up -d
```

**Acceso:**
| Servicio | URL |
|----------|-----|
| App | http://localhost |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [QUICKSTART.md](./QUICKSTART.md) | Guía rápida para nuevos desarrolladores |
| [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) | Guía completa de desarrollo |
| [docs/SYSTEM_REQUIREMENTS.md](./docs/SYSTEM_REQUIREMENTS.md) | Dependencias del sistema y solución de problemas |
| [docs/DOCKER_ENVIRONMENT.md](./docs/DOCKER_ENVIRONMENT.md) | Entorno Docker con migraciones |
| [docs/INSTALACION_LINUX.md](./docs/INSTALACION_LINUX.md) | Instalación para Linux |
| [docs/INSTALACION_WINDOWS.md](./docs/INSTALACION_WINDOWS.md) | Instalación para Windows |
| [docs/COMANDOS.md](./docs/COMANDOS.md) | Comandos importantes del proyecto |
| [docs/GUIAS_PGADMIN.md](./docs/GUIAS_PGADMIN.md) | Guía de pgAdmin |

---

## Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del servidor y base de datos |
| GET | `/api/categories` | Listar categorías |
| GET | `/api/products` | Listar productos |
| POST | `/api/detect` | Detectar prendas en imagen (YOLO) |
| POST | `/api/auth/login` | Iniciar sesión |
| POST | `/api/carts` | Crear carrito |
| POST | `/api/carts/{id}/items` | Agregar item al carrito |
| GET | `/api/orders` | Listar órdenes |

### Detección de Prendas (YOLO)

```bash
curl -X POST "http://localhost:8000/api/detect" \
  -F "file=@imagen.jpg"
```

**Respuesta:**
```json
{
  "detections": [
    {
      "class": "gorra-roja-lacoste",
      "confidence": 0.95,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "image_size": [640, 480]
}
```

---

## Gestión de Base de Datos (Migraciones)

El sistema usa **Alembic** para gestionar cambios en el schema de forma versionada.

```bash
# Ver estado de migraciones
./scripts/migrate.sh status

# Ver historial
source backend/venv/bin/activate
export PYTHONPATH=$PWD
alembic history

# Crear nueva migración
alembic revision --autogenerate -m "descripcion_del_cambio"
```

**Flujo de trabajo:**
1. Modificar modelos en `backend/app/models/`
2. Crear migración: `alembic revision --autogenerate -m "mensaje"`
3. Commit y push
4. Otros desarrolladores ejecutan `./scripts/dev-start.sh` y las migraciones se aplican automáticamente

---

## Estructura del Proyecto

```
FashionVision-AI/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuración
│   │   ├── database.py      # Conexión a DB
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Schemas Pydantic
│   │   └── services/        # Servicios (auth, detection, etc)
│   ├── alembic/             # Migraciones de base de datos
│   ├── models/              # Modelo YOLO (best.pt)
│   ├── database/            # SQL scripts (schema.sql, seed.sql)
│   └── requirements.txt     # Dependencias Python
├── frontend/
│   ├── src/
│   │   ├── pages/           # Páginas React
│   │   ├── components/      # Componentes reutilizables
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # Servicios API
│   │   └── styles/          # Estilos CSS
│   └── package.json         # Dependencias npm
├── docker/                  # Dockerfiles
├── scripts/                 # Scripts de ayuda
├── docs/                    # Documentación
└── docker-compose.yml       # Orquestación Docker
```

---

## Scripts de Ayuda

| Script | Uso | Descripción |
|--------|-----|-------------|
| `dev-start.sh` | `./scripts/dev-start.sh` | Inicia modo desarrollo completo |
| `dev-stop.sh` | `./scripts/dev-stop.sh` | Detiene servicios Docker |
| `docker-start.sh` | `./scripts/docker-start.sh` | Inicia todo en Docker |
| `migrate.sh` | `./scripts/migrate.sh` | Control de migraciones |
| `pgadmin-start.sh` | `./scripts/pgadmin-start.sh` | Inicia pgAdmin |
| `pgadmin-stop.sh` | `./scripts/pgadmin-stop.sh` | Detiene pgAdmin |
| `db-reset.sh` | `./scripts/db-reset.sh` | Reinicia la base de datos |

---

## Credenciales

| Servicio | Usuario | Contraseña | Puerto |
|----------|---------|------------|--------|
| pgAdmin | `admin@fashionvision.com` | `admin123` | 5050 |
| PostgreSQL | `fashionvision_ai_user` | `fashionvision_ai_pass` | 5432 |
| Login (desarrollo) | `admin@tienda.com` | `admin123` | - |

---

## Comandos de Desarrollo

```bash
# Frontend
cd frontend
npm run dev          # Desarrollo
npm run build        # Build producción
npm run lint         # ESLint
npm run test         # Tests

# Backend
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Docker
docker compose up -d          # Iniciar todo
docker compose ps             # Ver estado
docker compose logs -f        # Ver logs
docker compose down           # Detener todo
```

---

## Verificación del Sistema

```bash
# 1. Health check del backend
curl http://localhost:8000/health

# 2. Verificar frontend
curl http://localhost:5173 | head -20

# 3. Verificar pgAdmin
curl http://localhost:5050

# 4. Ver estado de migraciones
source backend/venv/bin/activate
export PYTHONPATH=$PWD
cd backend
alembic current
```

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named '_ctypes'`

**Causa:** Python fue compilado sin `libffi-dev`.

```bash
# Solución:
sudo apt-get install -y libffi-dev python3-dev
rm -rf ~/.pyenv/versions/3.12.0
~/.pyenv/bin/pyenv install 3.12.0
rm -rf backend/venv
./scripts/setup.sh
```

Para más detalles, ver [docs/SYSTEM_REQUIREMENTS.md](./docs/SYSTEM_REQUIREMENTS.md).

### Error: `ModuleNotFoundError: No module named 'backend'`

```bash
export PYTHONPATH=$PWD
# Ejecutar desde la raíz del proyecto
```

### Error: `alembic: command not found`

```bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
alembic upgrade head
```

### Error: `connection refused` en PostgreSQL

```bash
# Verificar que Docker está corriendo
docker compose ps db

# Reiniciar si es necesario
docker compose restart db
```

### Error: Puerto en uso

```bash
# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Próximos Pasos

1. Revisar [QUICKSTART.md](./QUICKSTART.md) para configuración inicial
2. Revisar [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) para flujo de trabajo
3. Revisar [docs/DOCKER_ENVIRONMENT.md](./docs/DOCKER_ENVIRONMENT.md) para gestión de migraciones
4. Explorar la API en http://localhost:8000/docs