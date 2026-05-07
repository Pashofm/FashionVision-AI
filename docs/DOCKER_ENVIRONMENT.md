# FashionVision-AI - Entorno Docker

Guía completa para configurar y usar los entornos de desarrollo y producción con Docker.

## Tabla de Contenidos

1. [Arquitectura](#arquitectura)
2. [Modos de Uso](#modos-de-uso)
3. [Primeros Pasos](#primeros-pasos)
4. [Scripts de Ayuda](#scripts-de-ayuda)
5. [Configuración de pgAdmin](#configuración-de-pgadmin)
6. [Solución de Problemas](#solución-de-problemas)

---

## Arquitectura

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

```
┌─────────────────────────────────────────────────────────────┐
│                        Producción                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│   │   Frontend   │   │   Backend    │   │     DB       │   │
│   │   Docker     │   │   Docker     │   │   Docker     │   │
│   │   :80        │   │   :8000      │   │   :5432      │   │
│   └──────────────┘   └──────────────┘   └──────────────┘   │
│         │                  │                    │          │
│         └──────────────────┴────────────────────┘          │
│                              │                              │
│                              ▼                              │
│                       ┌──────────────┐                     │
│                       │   pgAdmin    │                     │
│                       │   Docker     │                     │
│                       │   :5050      │                     │
│                       └──────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Modos de Uso

### Modo A: Desarrollo (Hot-Reload Activo)

Para desarrollo activo cuando necesitas iterar rápido.

```bash
# 1. Iniciar base de datos + pgAdmin en Docker
docker compose up -d db pgadmin

# 2. Terminal Backend (hot-reload)
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# 3. Terminal Frontend (hot-reload)
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

**Credenciales pgAdmin:**
- Email: `admin@fashionvision.com` (o el configurado en .env)
- Password: `admin123` (o el configurado en .env)

---

### Modo B: Testing / Demo (Docker Completo)

Para testing, demos a clientes, o cuando no necesitas hot-reload.

```bash
# Todo en Docker (comando único)
docker compose up -d

# Ver servicios
docker compose ps

# Ver logs
docker compose logs -f
```

**Acceso:**
| Servicio | URL |
|----------|-----|
| App | http://localhost |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

---

## Primeros Pasos

### Requisitos Previos

| Software | Versión | Notas |
|----------|---------|-------|
| Docker Desktop | 4.0+ | Para Windows/WSL |
| Git | Any | Para clonar |
| Python | 3.12+ | Para venv local |
| Node.js | 20+ | Para frontend local |

### Instalación (Nuevos miembros del equipo)

```bash
# 1. Clonar repositorio
git clone <repo-url> FashionVision-AI
cd FashionVision-AI

# 2. Copiar archivo de variables
cp .env.template .env

# 3. Crear entorno virtual de Python
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 4. Crear entorno de frontend
cd ../frontend
npm install

# 5. Iniciar entorno de desarrollo
cd ..
./scripts/dev-start.sh
```

---

## Scripts de Ayuda

### Scripts Disponibles

| Script | Uso | Descripción |
|--------|-----|-------------|
| `dev-start.sh` | `./scripts/dev-start.sh` | Inicia modo desarrollo (DB + pgAdmin + migraciones) |
| `dev-stop.sh` | `./scripts/dev-stop.sh` | Detiene servicios Docker |
| `docker-start.sh` | `./scripts/docker-start.sh` | Inicia todo en Docker (modo producción/testing) |
| `db-reset.sh` | `./scripts/db-reset.sh` | Reinicia la base de datos (¡cuidado!) |
| `pgadmin-start.sh` | `./scripts/pgadmin-start.sh` | Inicia solo pgAdmin |
| `pgadmin-stop.sh` | `./scripts/pgadmin-stop.sh` | Detiene pgAdmin |
| `migrate.sh` | `./scripts/migrate.sh` | Control manual de migraciones Alembic |

### Uso Típico

```bash
# --- DESARROLLO ---
# Iniciar entorno desarrollo (incluye migraciones automáticas)
./scripts/dev-start.sh

# Backend: cd backend && source venv/bin/activate && export PYTHONPATH=$PWD && uvicorn backend.app.main:app --reload
# Frontend: cd frontend && npm run dev

# Ver estado de migraciones
./scripts/migrate.sh status

# Detener servicios
./scripts/dev-stop.sh

# --- PRODUCCIÓN/TESTING ---
# Iniciar todo en Docker
./scripts/docker-start.sh

# Detener todo
docker compose down

# --- SOLO PGADMIN ---
./scripts/pgadmin-start.sh
./scripts/pgadmin-stop.sh

# --- MIGRACIONES ---
./scripts/migrate.sh status   # Ver estado
./scripts/migrate.sh down     # Rollback
./scripts/migrate.sh reset    # Reset completo
```

---

## Migraciones de Base de Datos (Alembic)

El sistema usa **Alembic** para gestionar cambios en el schema de la base de datos de forma versionada.

### ¿Cómo funciona?

1. Los cambios de DB se crean como **migraciones** en `backend/alembic/versions/`
2. Cuando otro desarrollador hace `git pull` y ejecuta `dev-start.sh`, las migraciones se aplican automáticamente
3. Los datos existentes se preservan (Alembic solo modifica el schema, no los datos)

### Flujo de Trabajo

```bash
# DESARROLLADOR A: Crear un cambio en la DB

# 1. Hacer cambios en los modelos Python (backend/app/models/)
# 2. Crear migración automáticamente
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
alembic revision --autogenerate -m "descripcion_del_cambio"

# 3. Revisar la migración creada en backend/alembic/versions/
# 4. Commit y push
git add backend/alembic/versions/
git commit -m "migration: descripcion_del_cambio"
git push

# DESARROLLADOR B: Recibir cambios

# 1. Pull
git pull

# 2. Ejecutar dev-start.sh (las migraciones se aplican automáticamente)
./scripts/dev-start.sh
```

### Scripts de Migración

| Script | Uso | Descripción |
|--------|-----|-------------|
| `dev-start.sh` | `./scripts/dev-start.sh` | Ejecuta `alembic upgrade head` automáticamente |
| `migrate.sh` | `./scripts/migrate.sh` | Control manual de migraciones |

### Comandos de Migración

```bash
# Ver estado actual de migraciones
./scripts/migrate.sh status

# Ver historial de migraciones
source backend/venv/bin/activate
export PYTHONPATH=$PWD
alembic history

# Hacer rollback de una migración
./scripts/migrate.sh down

# Resetear migraciones (¡cuidado!)
./scripts/migrate.sh reset
```

### Crear una Nueva Migración

```bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD

# Crear migración automáticamente desde cambios en modelos
alembic revision --autogenerate -m "agregar campo telefono a users"

# O crear migración vacía para hacer cambios manuales
alembic revision -m "crear tabla nuevo_modulo"
```

### Archivos de Migración

Las migraciones se guardan en:
```
backend/alembic/versions/
├── 001_initial.py      # Schema inicial
├── 002_xxx.py          # Siguientes migraciones
└── ...
```

**Importante:** No editar migraciones ya aplicadas. Crear una nueva migración para cada cambio.

---

## Configuración de pgAdmin

### Conectar a la Base de Datos

1. Abrir http://localhost:5050
2. Login con credenciales de `.env`
3. Click derecho en "Servers" → "Create" → "Server..."

**Configuración de conexión:**

| Campo | Valor |
|-------|-------|
| Host name/address | `fashionvision_db` |
| Port | `5432` |
| Maintenance database | `fashionvision_ai` |
| Username | `fashionvision_ai_user` |
| Password | (de .env) |

### Cambio de Contraseña pgAdmin

Editar `.env`:

```env
PGADMIN_EMAIL=tu@email.com
PGADMIN_PASSWORD=tu_nueva_password
```

Reiniciar contenedor:
```bash
docker compose restart pgadmin
```

---

## Variables de Entorno

### Archivo `.env`

```env
# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
POSTGRES_DB=fashionvision_ai
POSTGRES_USER=fashionvision_ai_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST_PORT=5432

# =============================================================================
# PORTS
# =============================================================================
BACKEND_HOST_PORT=8000
FRONTEND_HOST_PORT=80
PGADMIN_HOST_PORT=5050

# =============================================================================
# PGADMIN
# =============================================================================
PGADMIN_EMAIL=admin@fashionvision.com
PGADMIN_PASSWORD=your_password

# =============================================================================
# SECURITY
# =============================================================================
SECRET_KEY=generate_with_openssl_rand_base64_32
```

### Puertos por Defecto

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Frontend (dev) | 5173 | Vite dev server |
| Frontend (prod) | 80 | Nginx Docker |
| Backend | 8000 | FastAPI |
| PostgreSQL | 5432 | Base de datos |
| pgAdmin | 5050 | Administración DB |

---

## Solución de Problemas

### pgAdmin no conecta a la base de datos

**Síntoma**: Error "could not connect"

**Solución**:
```bash
# Verificar que la DB está corriendo
docker compose ps db

# Ver logs de pgAdmin
docker compose logs pgadmin

# Reiniciar pgAdmin
docker compose restart pgadmin
```

### El contenedor de pgAdmin no inicia

**Síntoma**: Contenedor en estado "Restarting"

**Solución**:
```bash
# Ver logs de errores
docker logs fashionvision_pgadmin

# Eliminar y recrear
docker compose down pgadmin
docker compose up -d pgadmin
```

### Cambié credenciales de pgAdmin y no puedo entrar

**Solución**:
```bash
# Eliminar volumen de pgAdmin (pierde configuración)
docker compose down -v pgadmin
docker compose up -d pgadmin

# O editar .env y reiniciar
docker compose restart pgadmin
```

### La base de datos no está healthy

**Síntoma**: `condition: service_healthy` failed

**Solución**:
```bash
# Ver logs de PostgreSQL
docker compose logs db

# Reiniciar database
docker compose restart db

# Si persiste, resetear
./scripts/db-reset.sh
```

### Error en migraciones Alembic

**Síntoma**: Error "Can't locate revision" o similares

**Solución**:
```bash
# Ver estado actual
./scripts/migrate.sh status

# Ver historial de migraciones
source backend/venv/bin/activate
export PYTHONPATH=$PWD
alembic history

# Si hay conflicto, resetear migraciones
./scripts/migrate.sh reset
```

### Migraciones no se ejecutan

**Síntoma**: La DB no tiene los cambios esperados

**Solución**:
```bash
# Forzar ejecución de migraciones
source backend/venv/bin/activate
export PYTHONPATH=$PWD
alembic upgrade head

# Verificar estado
alembic current
```

---

## Comandos Rápidos de Referencia

### Ver servicios activos
```bash
docker compose ps
```

### Ver todos los logs
```bash
docker compose logs -f
```

### Ver logs de un servicio específico
```bash
docker compose logs -f pgadmin
docker compose logs -f db
docker compose logs -f backend
```

### Reiniciar un servicio
```bash
docker compose restart pgadmin
docker compose restart db
```

### Detener todos los servicios
```bash
docker compose stop
```

### Eliminar todos los contenedores
```bash
docker compose down
```

### Rebuild completo
```bash
docker compose build --no-cache
docker compose up -d
```

---

## Acceso Rápido

| Recurso | URL |
|---------|-----|
| App (producción) | http://localhost |
| Frontend (dev) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

### Credenciales por Defecto

| Servicio | Usuario | Contraseña |
|----------|---------|------------|
| pgAdmin | `admin@fashionvision.com` | `admin123` |
| PostgreSQL | `fashionvision_ai_user` | `fashionvision_ai_pass` |

---

## Documentación Relacionada

- [Guía de Desarrollo](./DEVELOPMENT.md)
- [Comandos Importantes](./COMANDOS.md)
- [Guía de pgAdmin](./GUIAS_PGADMIN.md)
- [Sistema de Sesiones y Carritos](./SESIONES_Y_CARRITOS.md)