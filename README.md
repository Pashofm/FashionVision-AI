# FashionVision AI

**Sistema Inteligente de Reconocimiento de Prendas y Análisis Predictivo**

FashionVision AI es una solución tecnológica diseñada para pequeñas y medianas tiendas de ropa. Automatiza el control de inventario y facilita el proceso de venta mediante visión por computadora (YOLO) y análisis de datos.

---

## Tabla de Contenidos

- [Stack Tecnológico](#stack-tecnológico)
- [Requisitos Previos](#requisitos-previos)
- [Formas de instalación](#formas-de-instalación)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Modos de Uso](#modos-de-uso)
- [Flujo funcional](#flujo-funcional)
- [Documentación](#documentación)
- [Endpoints de la API](#endpoints-de-la-api)

---

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Frontend | React 19 + Vite | 19.2.0 / 7.3.1 |
| Backend | Python 3.12 + FastAPI | 0.115.0 |
| Base de Datos | PostgreSQL 16 + pgvector | — |
| Modelo IA | YOLO (Ultralytics) + CLIP | 8.3.40 |
| ORM | SQLAlchemy + Alembic | 2.0.35 / 1.13.3 |
| Proxy | Nginx | 1.25 |
| Contenedores | Docker + Docker Compose | — |

---

## Requisitos Previos

| Software | Versión | Notas |
|----------|---------|-------|
| Docker | 24.0+ | Con el plugin `compose` (incluido en Docker Desktop) |
| Git | 2.40+ | Para clonar el repositorio |
| Espacio en disco | 10 GB libres | Las imágenes Docker y dependencias de IA ocupan varios GB |

> **Nota:** No necesitas instalar Python ni Node.js en tu máquina. Todo corre dentro de contenedores Docker.

---

## Formas de instalación

El sistema se ejecuta con Docker en los tres entornos siguientes. No necesitas instalar Python, Node.js ni PostgreSQL en el host.

| Entorno | Método | Guía |
|---|---|---|
| Linux | Docker Engine nativo | [Instalación Linux](./docs/INSTALLATION.md#linux) |
| Windows 10/11 | Docker Desktop y PowerShell | [Windows nativo](./docs/INSTALLATION.md#windows-nativo) |
| Windows 10/11 | Docker Desktop y Ubuntu en WSL2 | [Windows con WSL2](./docs/WINDOWS_WSL2.md) |

**Windows con WSL2 es el método recomendado para desarrollar**, ya que ofrece mejor rendimiento de volúmenes y hot reload que trabajar en el filesystem de Windows.

Después de preparar Docker y Git según tu plataforma, ejecuta el flujo de demo:

```bash
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
docker compose up -d --build --wait
```

En Linux y WSL2 carga los datos demo con `make seed`. En Windows nativo, o si no tienes `make`, usa el comando equivalente de [COMANDOS.md](./docs/COMANDOS.md#datos-iniciales-y-migraciones).

**Acceso inmediato:**

| Servicio | URL |
|----------|-----|
| App | http://localhost |
| Backend API | http://localhost/api |
| API Docs (Swagger) | http://localhost/docs |
| pgAdmin | http://localhost:5050 (`docker compose --profile tools up -d pgadmin`) |

Consulta [docs/INSTALLATION.md](./docs/INSTALLATION.md) para instalación, reinicio completo, puertos y diagnóstico por plataforma.

**Usuarios de prueba:**

| Email | Rol | Contraseña |
|-------|-----|------------|
| admin@tienda.com | admin | admin123 |
| cajero@tienda.com | cashier | admin123 |
| cliente@demo.com | client | admin123 |

Para conocer el flujo completo de administrador, cliente y cajero consulta la [Guía de Usuario](./docs/USER_GUIDE.md).

---

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                        HOST (tu máquina)                         │
│                                                                  │
│   Puerto 80 ──────────────────────────────────────────────┐      │
│                                                            │      │
└────────────────────────────────────────────────────────────│──────┘
                                                             │
┌────────────────────────────────────────────────────────────│──────┐
│                     DOCKER: pos-network                     │      │
│                                                            ▼      │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │                     NGINX (:80)                          │    │
│   │   Reverse Proxy — único punto de entrada al sistema      │    │
│   │   /api/* → backend:8000    /* → frontend:5173            │    │
│   └──────────┬───────────────────────────────┬───────────────┘    │
│              │                               │                    │
│              ▼                               ▼                    │
│   ┌──────────────────────┐    ┌──────────────────────────────┐   │
│   │   BACKEND (:8000)    │    │   FRONTEND (:5173)            │   │
│   │   FastAPI + YOLO     │    │   React 19 + Vite             │   │
│   │   + CLIP + Alembic   │    │   Hot reload en desarrollo    │   │
│   └──────────┬───────────┘    └──────────────────────────────┘   │
│              │                                                    │
│              ▼                                                    │
│   ┌──────────────────────┐                                       │
│   │   DB (:5432)          │    ┌──────────────────────────┐      │
│   │   PostgreSQL 16       │    │   PGADMIN (:5050)         │      │
│   │   + pgvector          │    │   (perfil tools opcional)  │      │
│   └──────────────────────┘    └──────────────────────────┘      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Modos de Uso

### Modo Desarrollo (Docker con hot reload)

```bash
make up-build    # Construye y levanta todos los servicios con volúmenes de código
make seed        # Carga los datos demo
```

Los cambios en `backend/` y `frontend/src/` se reflejan instantáneamente gracias a los volúmenes montados y hot reload (uvicorn --reload + Vite HMR).

### Modo Producción

```bash
cp .env.example .env
# Editar .env con secretos, dominios reales y ENVIRONMENT=production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Sin volúmenes de código, sin hot reload, backend con gunicorn + 4 workers uvicorn, restart always.

## Flujo funcional

FashionVision AI se utiliza con tres perfiles:

1. **Administrador**: configura catálogo, variantes, imágenes, inventario y consulta reportes.
2. **Cliente**: usa el kiosco, permite el acceso a la cámara, identifica una prenda, selecciona una variante y envía el carrito.
3. **Cajero**: revisa el carrito, confirma disponibilidad, procesa el pago simulado y genera el recibo.

La venta completada actualiza el inventario de la variante correspondiente. El terminal POS incluido es un mock para desarrollo: no realiza cobros reales ni se conecta a hardware bancario.

Consulta la [Guía de Usuario](./docs/USER_GUIDE.md) para el flujo detallado por rol.

---

## Comandos Principales

```bash
make help            # Lista todos los comandos disponibles
make up              # Levanta servicios (sin reconstruir)
make up-build        # Reconstruye imágenes y levanta
make down            # Detiene contenedores
make logs            # Logs de todos los servicios
make logs-backend    # Solo logs del backend
make shell-backend   # Shell interactiva en backend
make shell-db        # Cliente psql en la base de datos
make migrate         # alembic upgrade head
make migrate-status  # Ver estado de migraciones
make seed            # Cargar datos de prueba
make test-backend    # Requiere una BD de pruebas separada; ver testing/TESTING_GUIDE.md
make test-frontend   # vitest en el contenedor frontend
make clean           # Eliminar todo (contenedores + volúmenes)
```

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [QUICKSTART.md](./QUICKSTART.md) | Guía rápida para nuevos desarrolladores |
| [docs/INDEX.md](./docs/INDEX.md) | Índice de documentación por audiencia |
| [docs/USER_GUIDE.md](./docs/USER_GUIDE.md) | Flujo funcional por rol |
| [docs/CONFIGURATION.md](./docs/CONFIGURATION.md) | Variables de entorno y configuración |
| [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) | Guía completa de desarrollo |
| [docs/DOCKER_ENVIRONMENT.md](./docs/DOCKER_ENVIRONMENT.md) | Entorno Docker y migraciones |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Arquitectura del sistema |
| [docs/INSTALLATION.md](./docs/INSTALLATION.md) | Instalación para todos los SO |
| [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) | Guía de despliegue en producción |
| [docs/COMANDOS.md](./docs/COMANDOS.md) | Referencia completa de comandos |

---

## Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del servidor y base de datos |
| GET | `/api/categories` | Listar categorías |
| GET | `/api/products` | Listar productos |
| POST | `/api/detect` | Detectar prendas en imagen (YOLO + CLIP) |
| POST | `/api/auth/login` | Iniciar sesión |
| POST | `/api/carts` | Crear carrito |
| POST | `/api/carts/{id}/items` | Agregar item al carrito |
| GET | `/api/orders` | Listar órdenes |

### Detección de Prendas

```bash
curl -X POST "http://localhost/api/detect" \
  -F "file=@imagen.jpg"
```

---

## Gestión de Base de Datos (Migraciones)

El sistema usa **Alembic** para gestionar cambios en el schema de forma versionada.

```bash
make migrate          # Aplicar migraciones pendientes
make migrate-status   # Ver estado actual
make migrate-history  # Ver historial
make migrate-down     # Revertir última migración
```

**Flujo de trabajo para crear una nueva migración:**

```bash
# 1. Modificar modelos en backend/app/models/
# 2. Entrar al contenedor
make shell-backend

# 3. Dentro del contenedor:
cd /app/backend
alembic revision --autogenerate -m "descripcion_del_cambio"

# 4. El archivo se crea en backend/alembic/versions/
# 5. Commit y push
```

---

## Verificación del Sistema

```bash
# Health check del backend
curl http://localhost/health

# Login de prueba
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tienda.com","password":"admin123"}'

# Verificar frontend
curl -I http://localhost

# Verificar migraciones
make migrate-status
```

---

## Troubleshooting

### Error: `port is already allocated`

```bash
docker compose down
lsof -i :80    # Linux/Mac
# netstat -ano | findstr :80   # Windows
kill -9 <PID>
make up
```

### Error: `connection refused` en PostgreSQL

```bash
docker compose ps db           # Verificar que db está corriendo
docker compose restart db      # Reiniciar si es necesario
make logs-db                   # Ver logs
```

### Error: migraciones no aplicadas

```bash
make migrate-status            # Ver estado
make migrate                   # Forzar aplicación
```

### Acceso a PostgreSQL

La base de datos no publica un puerto en el host para evitar conflictos con instalaciones locales. Usa `make shell-db` o pgAdmin para administrarla.

---
