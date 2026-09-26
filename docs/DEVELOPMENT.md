# FashionVision-AI - Guía de Desarrollo en Equipo

Documentación para configurar el entorno de desarrollo en equipo con Docker.

## Índice

- [Arquitectura](#arquitectura)
- [Modos de Uso](#modos-de-uso)
- [Primeros Pasos](#primeros-pasos)
- [Comandos Makefile](#comandos-makefile)
- [Comandos Rápidos](#comandos-rápidos)
- [Migraciones con Alembic](#migraciones-con-alembic)
- [Solución de Problemas](#solución-de-problemas)

---

## Arquitectura

### Entorno de Desarrollo Activo

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Tu Equipo de Desarrollo                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐ │
│   │   Frontend   │   │   Backend    │   │     DB       │   │  Nginx   │ │
│   │   Docker     │   │   Docker     │   │   Docker     │   │  Docker  │ │
│   │   :5173      │   │   :8000      │   │   :5432      │   │  :80     │ │
│   │  (Vite HMR)  │   │  (HotReload) │   │  (pgvector)  │   │ (proxy)  │ │
│   └──────────────┘   └──────────────┘   └──────────────┘   └──────────┘ │
│         ↑                  ↑                   ↑                ↑        │
│         │                  │                   │                │        │
│         └──────────────────┴───────────────────┴────────────────┘        │
│                                    ↑                                     │
│                             make up / make up-build                      │
└──────────────────────────────────────────────────────────────────────────┘
```

### Entorno de Testing/Demo (Producción simulada)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## Modos de Uso

### Modo A: Desarrollo (hot-reload activo)

**Para desarrollo activo cuando necesitas iterar rápido. Hot reload en frontend y backend dentro de Docker.**

```bash
make up-build
```

Esto levanta los 4 servicios (db, backend, frontend, nginx) con el código fuente montado como volumen. Los cambios en el código local se reflejan instantáneamente gracias al hot reload de uvicorn y Vite.

**Acceso:**
- App completa (nginx): http://localhost
- Backend API: http://localhost/api
- API Docs: http://localhost/docs
- pgAdmin (opcional): http://localhost:5050

Si solo necesitas reiniciar sin reconstruir (porque ya tienes las imágenes):

```bash
make up
```

---

### Modo B: Testing / Demo (producción simulada)

**Para testing, demos a clientes, o cuando no necesitas hot-reload. Sin montajes de código fuente, usando imágenes de producción con gunicorn + uvicorn workers.**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

O reconstruyendo las imágenes de producción:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

**Acceso:**
- App completa: http://localhost
- Backend API: http://localhost/api
- API Docs: http://localhost/docs

---

## Primeros Pasos

### 1. Requisitos Previos

| Software | Versión | Notas |
|----------|---------|-------|
| Docker | 24.0+ | Con Docker Compose V2 |
| Git | Any | Para clonar |

### 2. Instalación (Nuevos miembros del equipo)

```bash
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
docker compose up -d --build --wait
make seed
```

El sistema estará disponible en:

- App: http://localhost
- Backend: http://localhost/api
- API Docs: http://localhost/docs

### 3. Iniciar Desarrollo

```bash
make up-build
```

Los logs de todos los servicios se pueden seguir con:

```bash
make logs
```

---

## Comandos Makefile

El proyecto incluye un Makefile en la raíz con los comandos esenciales. Ejecutar `make help` para ver la lista completa.

### Gestión de servicios

| Comando | Descripción |
|---------|-------------|
| `make up` | Levanta los 4 servicios (db, backend, frontend, nginx) en modo desarrollo |
| `make up-build` | Reconstruye imágenes y levanta servicios |
| `make down` | Detiene y elimina contenedores |
| `make clean` | Elimina contenedores, volúmenes e imágenes huérfanas |

### Logs

| Comando | Descripción |
|---------|-------------|
| `make logs` | Muestra logs de todos los servicios |
| `make logs-backend` | Logs del backend (FastAPI) |
| `make logs-db` | Logs de PostgreSQL |
| `make logs-frontend` | Logs del frontend (Vite dev server) |
| `make logs-nginx` | Logs de nginx |

### Shell en contenedores

| Comando | Descripción |
|---------|-------------|
| `make shell-backend` | Abre shell interactiva en el contenedor backend |
| `make shell-db` | Abre psql en el contenedor de base de datos |

### Migraciones y datos

| Comando | Descripción |
|---------|-------------|
| `make migrate` | Corre alembic upgrade head |
| `make migrate-status` | Muestra el estado actual de las migraciones |
| `make migrate-history` | Muestra el historial completo de migraciones |
| `make migrate-down` | Revierte la última migración (-1) |
| `make seed` | Carga datos iniciales de prueba en la base de datos |

### Tests

| Comando | Descripción |
|---------|-------------|
| `make test-backend` | Corre pytest en el backend; requiere una BD de pruebas separada |
| `make test-frontend` | Corre los tests del frontend |

---

## Comandos Rápidos

### Base de datos (Docker)

```bash
docker compose ps db
docker compose logs db
docker compose restart db

make shell-db
```

Para reset completo de la base de datos:

```bash
make clean
make up-build
```

### Backend (Docker)

```bash
docker compose logs backend
docker compose restart backend
make shell-backend
```

Las pruebas backend requieren una base aislada que el Compose de demo no proporciona. Consulta [testing/TESTING_GUIDE.md](testing/TESTING_GUIDE.md).

### Frontend (Docker)

```bash
docker compose logs frontend
docker compose restart frontend
docker compose exec frontend npm run lint
docker compose exec frontend npm run test:run
```

### Todos los servicios

```bash
make up
make down
make logs
make clean
```

---

## Migraciones con Alembic

Las migraciones se ejecutan automáticamente al iniciar el backend (tanto en `make up` como en `make up-build`). Para operaciones manuales:

### Comandos rápidos vía Makefile

```bash
make migrate
make migrate-status
make migrate-history
make migrate-down
```

### Workflow manual con shell

Para crear nuevas migraciones o ejecutar comandos avanzados:

```bash
make shell-backend
```

Dentro del contenedor:

```bash
cd /app/backend

alembic current
alembic history
alembic upgrade head
alembic downgrade -1

alembic revision --autogenerate -m "descripcion_del_cambio"
```

---

## Variables de Entorno

El archivo `.env` en la raíz del proyecto configura todo el sistema. Se copia desde `.env.example`:

```bash
cp .env.example .env
```

**Variables principales:**

```env
POSTGRES_DB=fashionvision_ai
POSTGRES_USER=fashionvision_ai_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

FRONTEND_HOST_PORT=80

SECRET_KEY=generate_with_openssl_rand_base64_32
ENVIRONMENT=development
```

---

## Solución de Problemas

### Error: `no existe el rol «fashionvision_ai_user»`

**Causa:** La base de datos no está corriendo o no se creó correctamente.

**Solución:**

```bash
docker compose ps db
docker compose logs db

make clean
make up-build

docker compose ps db
```

### Error: `connection refused` en PostgreSQL

**Causa:** PostgreSQL no está escuchando en el puerto esperado o el puerto no está publicado para el host.

**Solución:**

```bash
docker compose ps db
docker compose logs db
docker compose config
```

### Error: puerto en uso

**Causa:** Otro proceso está usando el puerto.

**Solución:**

```bash
lsof -i :80
kill -9 <PID>
```

### Verificar que todo funciona

```bash
docker compose ps
curl http://localhost/health
curl http://localhost | head -20
```

---

## Tips para el Equipo

1. **Siempre usa `make` para operaciones comunes**: `make up`, `make logs`, `make migrate`, etc.
2. **Si algo falla**: verifica `docker compose ps` y `make logs` para diagnosticar.
3. **Para reset completo**: `make clean && make up-build`.
4. **Para testing/demo sin hot reload**: usa `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.
5. **Nunca commitees el archivo `.env`** al repositorio.
6. **Los modelos de PyTorch (YOLO, CLIP)** se cachean en el volumen `torch_cache` para no descargarlos en cada reinicio.

---
