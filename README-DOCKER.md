# FashionVision-AI - Deployment con Docker

Documentación completa para desplegar FashionVision-AI usando Docker en WSL2 con Docker Desktop.

## Índice

- [Requisitos](#requisitos)
- [Arquitectura](#arquitectura)
- [Configuración Inicial](#configuración-inicial)
- [Ejecución](#ejecución)
- [Verificación](#verificación)
- [Comandos Útiles](#comandos-útiles)
- [Solución de Problemas](#solución-de-problemas)
- [Desarrollo vs Producción](#desarrollo-vs-producción)

---

## Requisitos

### Sistema Operativo

- **Windows 10/11** con WSL2 habilitado
- **WSL2** (Windows Subsystem for Linux 2)
- **Ubuntu 24.04 LTS** (distribución Linux para WSL2)

### Software

| Software | Versión Mínima | Descarga |
|----------|---------------|----------|
| Docker Desktop | 4.0+ | [docker.com](https://docs.docker.com/desktop/install/windows-install/) |
| WSL2 | Latest | Incluido en Windows 10/11 |
| Ubuntu | 24.04 | Microsoft Store |

### Recursos Recomendados

| Recurso | Mínimo | Recomendado |
|--------|--------|-------------|
| RAM | 4 GB | 8 GB |
| CPU | 2 cores | 4 cores |
| Disco | 20 GB | 50 GB |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network (fashionnet)               │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   nginx     │  │   backend   │  │       db            │  │
│  │   :80       │  │   :8000     │  │     :5432           │  │
│  │  (frontend) │  │  (FastAPI)  │  │   (PostgreSQL)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                   │              │
│         └────────────────┴───────────────────┘              │
│                                                             │
│  Volúmenes:                                                  │
│  - postgres_data (datos persistentes)                       │
│  - media_files (archivos subidos)                           │
│  - model_files (modelo YOLO)                                │
└─────────────────────────────────────────────────────────────┘
```

### Servicios

| Servicio | Imagen | Puerto | Descripción |
|----------|--------|--------|-------------|
| frontend | Custom (nginx:alpine) | 80 | Aplicación web (React build) |
| backend | Custom (python:3.12-slim) | 8000 | API REST + YOLO |
| db | postgres:16-alpine | 5432 | Base de datos PostgreSQL |

---

## Configuración Inicial

### 1. Instalar WSL2

Abrir **PowerShell como Administrador** y ejecutar:

```powershell
wsl --install -d Ubuntu-24.04
```

Reiniciar el equipo cuando termine.

### 2. Configurar Ubuntu

Al abrir Ubuntu por primera vez, crear usuario y contraseña:

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar git (si no está)
sudo apt install -y git
```

### 3. Instalar Docker Desktop

1. Descargar Docker Desktop de https://docs.docker.com/desktop/install/windows-install/
2. Ejecutar el instalador
3. Durante la instalación, marcar **"Install required dependencies for WSL 2"**
4. Finalizar y reiniciar si es necesario

### 4. Habilitar WSL Integration

1. Abrir Docker Desktop
2. Ir a **Settings** → **Resources** → **WSL Integration**
3. Habilitar **Ubuntu-24.04**
4. Click **Apply & Restart**

### 5. Configurar Git (opcional)

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

### 6. Clonar el Repositorio

```bash
cd /mnt/d/Proyectos/Desarrollo_de_Software  # O la ruta donde tengas el proyecto
git clone <repo-url> FashionVision-AI
cd FashionVision-AI
```

> **Nota:** Si trabajas desde Windows, tus proyectos probablemente están en `/mnt/c/Users/...` o `/mnt/d/...`

---

## Ejecución

### 1. Configurar Variables de Entorno

```bash
# Copiar plantilla
cp .env.template .env

# Editar con tu editor preferido
nano .env
# o
code .env
```

**Variables obligatorias en `.env`:**

```env
# Database
POSTGRES_DB=fashionvision_ai
POSTGRES_USER=fashionvision_user
POSTGRES_PASSWORD=una_password_segura_aqui
POSTGRES_HOST_PORT=5432

# Security
SECRET_KEY=$(openssl rand -base64 32)  # Generar en Linux/Mac
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_TIMEOUT_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost

# Puertos
BACKEND_HOST_PORT=8000
FRONTEND_HOST_PORT=80
```

### 2. Generar SECRET_KEY

```bash
# En Linux/WSL
openssl rand -base64 32

# Copiar el resultado y pegarlo en .env como SECRET_KEY=...
```

### 3. Construir e Iniciar Contenedores

```bash
# Construir imágenes
docker compose build

# Iniciar todos los servicios
docker compose up -d

# Ver logs en tiempo real (opcional)
docker compose logs -f
```

### 4. Primera Ejecución (Base de Datos)

La primera vez que se ejecuta, PostgreSQL:
1. Crea automáticamente la base de datos
2. Ejecuta `schema.sql` para crear las tablas
3. Ejecuta `seed.sql` para datos iniciales

Esto puede tomar 30-60 segundos.

---

## Verificación

### Ver Estado de Servicios

```bash
docker compose ps
```

**Salida esperada:**
```
NAME                STATUS          PORTS
fashionvision_db    running ( healthy )   0.0.0.0:5432->5432/tcp
fashionvision_backend   running ( healthy )   0.0.0.0:8000->8000/tcp
fashionvision_frontend  running            0.0.0.0:80->80/tcp
```

### Verificar Backend

```bash
curl http://localhost:8000/health
```

**Respuesta esperada:**
```json
{"status":"healthy","model_loaded":true}
```

### Verificar Frontend

Abrir en navegador:
```
http://localhost
```

### Ver Logs

```bash
# Todos los servicios
docker compose logs

# Servicio específico
docker compose logs backend
docker compose logs frontend
docker compose logs db

# Con seguimiento en tiempo real
docker compose logs -f backend
```

---

## Comandos Útiles

### Iniciar/Detener

```bash
# Iniciar todos los servicios
docker compose up -d

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (¡CUIDADO! Elimina datos)
docker compose down -v

# Reiniciar un servicio específico
docker compose restart backend
```

### Rebuild

```bash
# Rebuild completo
docker compose build --no-cache
docker compose up -d

# Rebuild solo un servicio
docker compose build backend
docker compose up -d backend
```

### Base de Datos

```bash
# Conectar a PostgreSQL
docker exec -it fashionvision_db psql -U fashionvision_user -d fashionvision_ai

# Ver tablas
\dt

# Ver datos de una tabla
SELECT * FROM users LIMIT 5;

# Salir
\q
```

### Limpiar Recursos

```bash
# Eliminar imágenes no usadas
docker image prune -f

# Eliminar contenedores parados
docker container prune -f

# Rebuild completo limpio
docker compose down --rmi local
docker compose build --no-cache
docker compose up -d
```

### Ver Uso de Recursos

```bash
docker stats
```

---

## Solución de Problemas

### Problema: `docker: command not found`

**Causa:** Docker no está instalado o no está en el PATH.

**Solución:**
1. Verificar que Docker Desktop esté corriendo (icono en la bandeja)
2. Reiniciar Docker Desktop
3. En WSL, verificar: `which docker`

### Problema: `Cannot connect to the Docker daemon`

**Causa:** Docker daemon no está corriendo o WSL no tiene acceso.

**Solución:**
1. Abrir Docker Desktop
2. Ir a Settings > General > Mark "Expose daemon on tcp://..."
3. En WSL: `export DOCKER_HOST=tcp://localhost:2375`

### Problema: PostgreSQL no inicia

**Causa:** Puerto 5432 ocupado o volumen corrupto.

**Solución:**
```bash
# Ver logs
docker compose logs db

# Limpiar volumen si es primera vez corrupto
docker compose down -v
docker compose up -d
```

### Problema: Backend no conecta a DB

**Causa:** El backend intenta conectarse antes de que DB esté listo.

**Solución:**
- El `docker-compose.yml` ya tiene `depends_on` con `condition: service_healthy`
- Esperar a que DB esté healthy: `docker compose ps db`

### Problema: YOLO model not found

**Causa:** El modelo no se copió correctamente.

**Solución:**
```bash
# Verificar que el volumen tiene el modelo
docker exec fashionvision_backend ls -la /app/models/

# Si está vacío, copiar manualmente
docker cp backend/models/best.pt fashionvision_backend:/app/models/
```

### Problema: CORS errors en el navegador

**Causa:** `ALLOWED_ORIGINS` no incluye la URL correcta.

**Solución:**
En `.env`:
```env
ALLOWED_ORIGINS=http://localhost,http://localhost:80
```

Luego:
```bash
docker compose up -d backend
```

### Problema: Puerto ya en uso

**Causa:** Otro servicio está usando el mismo puerto.

**Solución:**
Cambiar puerto en `.env`:
```env
BACKEND_HOST_PORT=8001
FRONTEND_HOST_PORT=8080
```

---

## Desarrollo vs Producción

### Desarrollo

```bash
# Usar configuración de desarrollo
export ENVIRONMENT=development

# Backend con hot-reload
docker compose exec backend uvicorn backend.app.main:app --reload
```

### Producción

1. **Generar secretos seguros:**
```bash
# SECRET_KEY
openssl rand -base64 32

# POSTGRES_PASSWORD
openssl rand -base64 24
```

2. **Configurar `.env` con valores seguros**

3. **Usar valores de producción:**
```env
ENVIRONMENT=production
ALLOWED_ORIGINS=https://tudominio.com
```

4. **Habilitar HTTPS** (requiere configuración adicional con Caddy/Traefik)

---

## Estructura de Archivos

```
FashionVision-AI/
├── docker-compose.yml        # Orquestación de servicios
├── Dockerfile.backend        # Imagen del backend
├── Dockerfile.frontend       # Imagen del frontend (multi-stage)
├── nginx.conf                # Configuración de Nginx
├── .env.template             # Plantilla de variables
├── .env                      # Variables reales (no commitear)
├── backend/
│   ├── app/
│   │   ├── main.py          # API FastAPI
│   │   ├── services/
│   │   │   └── detection.py # Servicio YOLO
│   │   └── ...
│   ├── models/
│   │   └── best.pt          # Modelo YOLO
│   └── database/
│       ├── schema.sql        # Esquema DB
│       └── seed.sql         # Datos iniciales
└── frontend/
    ├── src/                  # Código React
    └── ...
```

---

## Volúmenes

| Volumen | Host Path | Contenedor | Propósito |
|---------|-----------|------------|-----------|
| postgres_data | Docker managed | /var/lib/postgresql/data | Datos PostgreSQL |
| media_files | Docker managed | /app/media | Archivos subidos |
| model_files | Docker managed | /app/models:ro | Modelo YOLO (solo lectura) |

---

## Créditos

Proyecto FashionVision-AI - YOLO-based clothes detection system.
