# FashionVision-AI - Entorno Docker

Guia completa para configurar y usar los entornos de desarrollo y produccion con Docker.

## Tabla de Contenidos

1. [Arquitectura](#arquitectura)
2. [Modos de Uso](#modos-de-uso)
3. [Makefile](#makefile)
4. [Primeros Pasos](#primeros-pasos)
5. [Migraciones de Base de Datos (Alembic)](#migraciones-de-base-de-datos-alembic)
6. [Configuracion de pgAdmin](#configuracion-de-pgadmin)
7. [Variables de Entorno](#variables-de-entorno)
8. [Solucion de Problemas](#solucion-de-problemas)
9. [Comandos Rapidos de Referencia](#comandos-rapidos-de-referencia)
10. [Acceso Rapido](#acceso-rapido)
11. [Documentacion Relacionada](#documentacion-relacionada)

---

## Arquitectura

### Modo Desarrollo (4 servicios en Docker con hot reload)

```
+--------------------------------------------------------------+
|                    Docker (Desarrollo)                        |
|                                                              |
|   +-----------+     +-------------+     +-------------+      |
|   |   Nginx   |     |  Frontend   |     |   Backend   |      |
|   |   :80    <-------  Vite :5173 |     |  uvicorn    |      |
|   |           |     | (hot reload) |     |  :8000      |      |
|   +-----+-----+     +-------------+     +------+------+      |
|         |                                      |              |
|         |    /api/*  --> backend:8000          |              |
|         |    /*      --> frontend:5173         |              |
|         |                                      |              |
|         |                             +--------+------+      |
|         |                             |      DB       |      |
|         |                             |  PostgreSQL   |      |
|         |                             |    :5432      |      |
|         |                             +---------------+      |
|         |                                    |               |
|         |                                    v               |
|         |                             +---------------+      |
|         +---------------------------->+   pgAdmin     |      |
|                                       |   :5050       |      |
|                                       |  (opcional)   |      |
|                                       +---------------+      |
+--------------------------------------------------------------+
```

| Servicio | Puerto interno | Descripcion |
|----------|---------------|-------------|
| nginx | 80 (host) | Reverse proxy unificado |
| frontend | 5173 | Vite dev server, hot reload activo |
| backend | 8000 | FastAPI + YOLO + CLIP, hot reload con --reload |
| db | 5432 | PostgreSQL 16 + pgvector |
| pgadmin | 5050 (opcional) | Administracion web de BD (perfil `tools`) |

### Modo Produccion (Docker completo sin hot reload)

```
+--------------------------------------------------------------+
|                    Docker (Produccion)                        |
|                                                              |
|   +-----------+     +-------------+     +-------------+      |
|   |   Nginx   |     |  Frontend   |     |   Backend   |      |
|   |   :80    <-------  build :80  |     |  gunicorn   |      |
|   |           |     | (estaticos) |     |  :8000      |      |
|   +-----+-----+     +-------------+     +------+------+      |
|         |                                      |              |
|         |    /api/*  --> backend:8000          |              |
|         |    /*      --> frontend:80           |              |
|         |                                      |              |
|         |                             +--------+------+      |
|         |                             |      DB       |      |
|         |                             |  PostgreSQL   |      |
|         |                             |    :5432      |      |
|         |                             +---------------+      |
|                                                              |
+--------------------------------------------------------------+
```

| Servicio | Puerto interno | Descripcion |
|----------|---------------|-------------|
| nginx | 80 (host) | Reverse proxy unificado |
| frontend | 80 | Build estatico de Vite servido por nginx |
| backend | 8000 | FastAPI + YOLO + CLIP con gunicorn (4 workers) |
| db | 5432 | PostgreSQL 16 + pgvector |

---

## Modos de Uso

### Modo A: Desarrollo (hot reload en Docker)

Para desarrollo activo con todos los servicios en Docker y hot reload habilitado.

```bash
make up-build
make migrate
```

El comando `make up-build` reconstruye las imagenes y levanta los 4 servicios (db, backend, frontend, nginx). Las migraciones de base de datos se ejecutan automaticamente al iniciar el backend. `make migrate` es un paso adicional por seguridad para verificar que las migraciones esten al dia.

Para incluir pgAdmin (opcional):

```bash
docker compose --profile tools up -d pgadmin
```

**Acceso:**

| Servicio | URL |
|----------|-----|
| App | http://localhost |
| Backend API | http://localhost/api |
| API Docs | http://localhost/docs |
| pgAdmin | http://localhost:5050 |

**Credenciales pgAdmin:**
- Email: `admin@fashionvision.com` (o el configurado en .env)
- Password: `admin123` (o el configurado en .env)

---

### Modo B: Produccion

Para despliegue en produccion sin hot reload, imagenes optimizadas y gunicorn.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Esto levanta los 4 servicios usando las imagenes de produccion: backend con gunicorn + 4 workers uvicorn, frontend con build estatico, sin montajes de codigo fuente, y con `restart: always`.

```bash
# Ver servicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Detener
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

**Acceso:**

| Servicio | URL |
|----------|-----|
| App | http://localhost |
| Backend API | http://localhost/api |
| API Docs | http://localhost/docs |

---

## Makefile

El proyecto incluye un `Makefile` en la raiz con los siguientes targets:

| Target | Comando | Descripcion |
|--------|---------|-------------|
| `make up` | `docker compose up -d` | Levanta los 4 servicios (db, backend, frontend, nginx) en modo desarrollo |
| `make up-build` | `docker compose up -d --build` | Reconstruye imagenes y levanta los 4 servicios |
| `make down` | `docker compose down` | Detiene y elimina todos los contenedores |
| `make logs` | `docker compose logs -f` | Muestra logs de todos los servicios en tiempo real |
| `make logs-backend` | `docker compose logs -f backend` | Logs del backend (FastAPI) |
| `make logs-db` | `docker compose logs -f db` | Logs de PostgreSQL |
| `make logs-frontend` | `docker compose logs -f frontend` | Logs del frontend (Vite dev server) |
| `make logs-nginx` | `docker compose logs -f nginx` | Logs de nginx |
| `make shell-backend` | `docker compose exec backend bash` | Abre shell interactiva en el contenedor backend |
| `make shell-db` | `docker compose exec db psql -U ...` | Abre psql en el contenedor de base de datos |
| `make migrate` | `alembic upgrade head` en contenedor | Aplica todas las migraciones pendientes |
| `make migrate-status` | `alembic current` en contenedor | Muestra la revision actual de la BD |
| `make migrate-history` | `alembic history` en contenedor | Muestra el historial completo de migraciones |
| `make migrate-down` | `alembic downgrade -1` en contenedor | Revierte la ultima migracion aplicada |
| `make seed` | carga seed.sql en BD | Carga datos iniciales de prueba en la base de datos |
| `make test-backend` | `pytest` en contenedor | Corre los tests del backend con cobertura |
| `make test-frontend` | `npm run test:run` en contenedor | Corre los tests del frontend |
| `make clean` | `docker compose down -v --remove-orphans` | Elimina contenedores, volumenes e imagenes huerfanas |

**Uso tipico:**

```bash
# Iniciar desarrollo
make up-build
make migrate

# Ver logs de un servicio
make logs-backend

# Entrar al contenedor del backend
make shell-backend

# Correr tests
make test-backend
make test-frontend

# Detener todo
make down

# Limpiar completamente (incluye datos de BD)
make clean
```

---

## Primeros Pasos

### Requisitos Previos

| Software | Version | Notas |
|----------|---------|-------|
| Docker | 24.0+ | Con Docker Compose V2 integrado |
| Git | Any | Para clonar el repositorio |

### Instalacion (Nuevos miembros del equipo)

```bash
# 1. Clonar repositorio
git clone git@github.com:Pashofm/FashionVision-AI.git
cd FashionVision-AI

# 2. Copiar archivo de variables de entorno
cp .env.example .env

# 3. (Opcional) Editar .env con valores personalizados
# vi .env

# 4. Construir e iniciar todos los servicios
make up-build

# 5. Verificar que las migraciones esten aplicadas
make migrate
```

**Verificar que todo funciona:**

```bash
# Ver estado de los servicios
docker compose ps

# Ver logs en tiempo real
make logs

# Acceder a la aplicacion
# Abrir http://localhost en el navegador
```

---

## Migraciones de Base de Datos (Alembic)

El sistema usa **Alembic** para gestionar cambios en el schema de la base de datos de forma versionada.

### Como funciona?

1. Los cambios de DB se crean como **migraciones** en `backend/alembic/versions/`
2. El backend ejecuta automaticamente `alembic upgrade head` al iniciar
3. Cuando otro desarrollador hace `git pull` y ejecuta `make up-build`, las migraciones se aplican automaticamente
4. Los datos existentes se preservan (Alembic solo modifica el schema, no los datos)

### Flujo de Trabajo

```bash
# DESARROLLADOR A: Crear un cambio en la DB

# 1. Entrar al contenedor del backend
make shell-backend

# 2. Dentro del contenedor, ir al directorio de backend
cd /app/backend

# 3. Crear migracion automaticamente desde cambios en modelos
alembic revision --autogenerate -m "descripcion_del_cambio"

# 4. Salir del contenedor
exit

# 5. Revisar la migracion creada en backend/alembic/versions/
# 6. Commit y push
git add backend/alembic/versions/
git commit -m "migration: descripcion_del_cambio"
git push

# DESARROLLADOR B: Recibir cambios

# 1. Pull
git pull

# 2. Reconstruir (las migraciones se aplican automaticamente)
make up-build
```

### Comandos de Migracion via Makefile

```bash
# Ver estado actual de migraciones
make migrate-status

# Ver historial de migraciones
make migrate-history

# Aplicar migraciones pendientes
make migrate

# Revertir la ultima migracion
make migrate-down

# Para revertir multiples migraciones, repetir make migrate-down
# O entrar al contenedor y ejecutar directamente:
#   make shell-backend
#   cd /app/backend
#   alembic downgrade -2    (revierte 2 migraciones)
#   alembic downgrade base   (revierte todas)

# Para un reset completo de BD (pierde todos los datos):
make clean && make up-build
```

### Crear una Nueva Migracion

```bash
# Entrar al contenedor del backend
make shell-backend

# Dentro del contenedor:
cd /app/backend

# Crear migracion automaticamente desde cambios en modelos
alembic revision --autogenerate -m "agregar campo telefono a users"

# O crear migracion vacia para cambios manuales
alembic revision -m "crear tabla nuevo_modulo"

# Salir del contenedor
exit
```

### Archivos de Migracion

Las migraciones se guardan en:

```
backend/alembic/versions/
+-- 001_initial.py      # Schema inicial
+-- 002_xxx.py          # Siguientes migraciones
+-- ...
```

**Importante:** No editar migraciones ya aplicadas. Crear una nueva migracion para cada cambio.

---

## Configuracion de pgAdmin

pgAdmin es un servicio opcional que se levanta con el perfil `tools`. Para iniciarlo:

```bash
docker compose --profile tools up -d pgadmin
```

### Conectar a la Base de Datos

1. Abrir http://localhost:5050
2. Login con credenciales de `.env`
3. Click derecho en "Servers" > "Create" > "Server..."

**Configuracion de conexion:**

| Campo | Valor |
|-------|-------|
| Host name/address | `db` |
| Port | `5432` |
| Maintenance database | `fashionvision_ai` |
| Username | `fashionvision_ai_user` |
| Password | (de .env) |

> **Nota:** El hostname es `db` (nombre del servicio en Docker Compose). La red interna `pos-network` permite que los contenedores se comuniquen usando el nombre del servicio como hostname.

### Cambio de Contrasena pgAdmin

Editar `.env`:

```env
PGADMIN_EMAIL=tu@email.com
PGADMIN_PASSWORD=tu_nueva_password
```

Reiniciar contenedor:

```bash
docker compose --profile tools restart pgadmin
```

---

## Variables de Entorno

### Archivo `.env`

Copiar desde el template:

```bash
cp .env.example .env
```

Editar `.env` con valores reales antes de levantar el sistema. Nunca commitear `.env` al repositorio.

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

| Servicio | Puerto | Descripcion |
|----------|--------|-------------|
| Frontend (via nginx) | 80 | Acceso unificado a la app |
| Backend | 8000 | FastAPI (via nginx o directo) |
| PostgreSQL | 5432 | Base de datos |
| pgAdmin | 5050 | Administracion DB (perfil tools) |

---

## Solucion de Problemas

### pgAdmin no conecta a la base de datos

**Sintoma:** Error "could not connect"

**Solucion:**

```bash
# Verificar que la DB esta corriendo
docker compose ps db

# Ver logs de la base de datos
make logs-db

# Ver logs de pgAdmin
docker compose logs pgadmin

# Reiniciar pgAdmin
docker compose --profile tools restart pgadmin
```

### El contenedor de pgAdmin no inicia

**Sintoma:** Contenedor en estado "Restarting"

**Solucion:**

```bash
# Ver logs de errores
docker compose logs pgadmin

# Eliminar y recrear
docker compose --profile tools down pgadmin
docker compose --profile tools up -d pgadmin
```

### Cambie credenciales de pgAdmin y no puedo entrar

**Solucion:**

```bash
# Eliminar volumen de pgAdmin (pierde configuracion)
docker compose --profile tools down -v pgadmin
docker compose --profile tools up -d pgadmin

# O editar .env y reiniciar
docker compose --profile tools restart pgadmin
```

### La base de datos no esta healthy

**Sintoma:** `condition: service_healthy` failed

**Solucion:**

```bash
# Ver logs de PostgreSQL
make logs-db

# Reiniciar base de datos
docker compose restart db

# Si persiste, resetear completamente
make clean && make up-build
```

### Error en migraciones Alembic

**Sintoma:** Error "Can't locate revision" o similares

**Solucion:**

```bash
# Ver estado actual
make migrate-status

# Ver historial de migraciones
make migrate-history

# Si hay conflicto, resetear migraciones (pierde datos)
make clean && make up-build

# O revertir una a una
make migrate-down
```

### Migraciones no se ejecutan

**Sintoma:** La DB no tiene los cambios esperados

**Solucion:**

```bash
# Forzar ejecucion de migraciones
make migrate

# Verificar estado
make migrate-status

# Si el problema persiste, entrar al contenedor y verificar
make shell-backend
cd /app/backend
alembic current
alembic heads
```

### Puertos en conflicto

**Sintoma:** Error "port is already allocated"

**Solucion:**

```bash
# Ver que proceso esta usando el puerto
sudo lsof -i :80
sudo lsof -i :8000
sudo lsof -i :5432

# Detener el proceso o cambiar los puertos en .env
# Luego reiniciar
make down && make up
```

---

## Comandos Rapidos de Referencia

### Ver servicios activos

```bash
docker compose ps
```

### Logs

```bash
make logs                # Todos los servicios
make logs-backend        # Solo backend
make logs-db             # Solo base de datos
make logs-frontend       # Solo frontend
make logs-nginx          # Solo nginx
```

### Reiniciar un servicio

```bash
docker compose restart backend
docker compose restart db
docker compose restart frontend
docker compose restart nginx
```

### Detener servicios

```bash
make down                # Detiene y elimina contenedores
```

### Rebuild completo

```bash
make clean               # Elimina contenedores y volumenes
make up-build            # Reconstruye y levanta
```

### Shell en contenedores

```bash
make shell-backend       # Shell bash en backend
make shell-db            # psql en base de datos
```

### Migraciones

```bash
make migrate             # Aplicar migraciones
make migrate-status      # Ver estado
make migrate-history     # Ver historial
make migrate-down        # Revertir ultima
```

### Tests

```bash
make test-backend        # Tests del backend
make test-frontend       # Tests del frontend
```

---

## Acceso Rapido

| Recurso | URL |
|---------|-----|
| App (produccion y desarrollo) | http://localhost |
| Backend API | http://localhost/api |
| API Docs | http://localhost/docs |
| pgAdmin | http://localhost:5050 |

### Credenciales por Defecto

| Servicio | Usuario | Contrasena |
|----------|---------|------------|
| pgAdmin | `admin@fashionvision.com` | `admin123` |
| PostgreSQL | `fashionvision_ai_user` | `fashionvision_ai_pass` |

---

## Documentacion Relacionada

- [Guia de Desarrollo](./DEVELOPMENT.md)
- [Comandos Importantes](./COMANDOS.md)
- [Guia de pgAdmin](./GUIAS_PGADMIN.md)
- [Sistema de Sesiones y Carritos](./SESIONES_Y_CARRITOS.md)
