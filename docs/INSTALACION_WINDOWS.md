# Guía de Instalación - Windows

Sistema completo para levantar y ejecutar FashionVision-AI en entorno Windows nativo (PowerShell/CMD).

**Para mejor compatibilidad, se recomienda usar WSL2. Ver [WINDOWS_WSL2.md](./WINDOWS_WSL2.md)**

---

## Tabla de Contenidos

1. [Requisitos Previos](#1-requisitos-previos)
2. [Instalación](#2-instalación)
3. [Configuración del Entorno](#3-configuración-del-entorno)
4. [Levantar Base de Datos](#4-levantar-base-de-datos)
5. [Configurar pgAdmin](#5-configurar-pgadmin)
6. [Levantar el Backend](#6-levantar-el-backend)
7. [Levantar el Frontend](#7-levantar-el-frontend)
8. [Verificar que Todo Funciona](#8-verificar-que-todo-funciona)
9. [Solución de Problemas](#9-solución-de-problemas)

---

## 1. Requisitos Previos

### Software Necesario

| Software | Versión Mínima | Descargar |
|----------|----------------|----------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop/ |
| Git | 2.30+ | https://git-scm.com/download |
| Node.js | 20+ | https://nodejs.org/ |

### Verificar Instalaciones (PowerShell)

```powershell
python --version
pip --version
docker --version
docker-compose --version
git --version
node --version
npm --version
```

---

## 2. Instalación

### Paso 2.1: Clonar el Repositorio

Usar PowerShell, CMD o Git Bash:

```powershell
cd C:\Proyectos
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI
```

### Paso 2.2: Instalar Python

1. Descargar Python desde https://www.python.org/downloads/
2. **IMPORTANTE**: Marcar checkbox "Add Python to PATH"
3. Click en "Install Now"
4. Verificar instalación:
```powershell
python --version
pip --version
```

### Paso 2.3: Instalar Docker Desktop

1. Descargar desde https://www.docker.com/products/docker-desktop/
2. Instalar siguiendo el wizard
3. Reiniciar computadora
4. Verificar:
```powershell
docker --version
docker-compose --version
```

### Paso 2.4: Habilitar Hyper-V (Necesario para Docker)

```powershell
# Abrir PowerShell como Administrador
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All
```

### Paso 2.5: Crear Entorno Virtual y Backend

```powershell
cd FashionVision-AI

# Crear entorno virtual
cd backend
python -m venv venv

# Activar entorno (CMD o PowerShell)
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2.6: Instalar Frontend

```powershell
cd ..\frontend
npm install
```

---

## 3. Configuración del Entorno

### Paso 3.1: Variables de Entorno

```powershell
# Desde la raíz del proyecto
copy .env.template .env
```

### Paso 3.2: Configurar .env

Editar el archivo `.env` en la raíz del proyecto:

```env
# Database
DATABASE_URL=postgresql+asyncpg://fashionvision_ai_user:tu_password@localhost:5432/fashionvision_ai
DATABASE_URL_SYNC=postgresql://fashionvision_ai_user:tu_password@localhost:5432/fashionvision_ai
POSTGRES_DB=fashionvision_ai
POSTGRES_USER=fashionvision_ai_user
POSTGRES_PASSWORD=tu_password

# Security
SECRET_KEY=generate_with_openssl_rand_base64_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
BACKEND_PORT=8000

# Files
MEDIA_DIR=backend/media
MAX_IMAGE_SIZE_MB=5
```

---

## 4. Levantar Base de Datos

### Iniciar PostgreSQL con Docker

```powershell
cd C:\ruta\al\proyecto\FashionVision-AI
docker compose up -d db
```

**Nota**: Ejecutar en CMD o PowerShell, NO en Git Bash.

### Verificar que PostgreSQL Está Corriendo

```powershell
docker ps
```

Deberías ver algo como:
```
CONTAINER ID   IMAGE           STATUS         PORTS
xxxxx         postgres:16     Up 5 hours     0.0.0.0:5432->5432/tcp
```

### Verificar Conexión a PostgreSQL

```powershell
docker exec -it fashionvision_db psql -U fashionvision_ai_user -d fashionvision_ai
```

Comandos útiles en psql:
- `\dt` - Ver todas las tablas
- `\d nombre_tabla` - Ver estructura de tabla
- `SELECT * FROM users;` - Ver datos de tabla
- `\q` - Salir

---

## 5. Configurar pgAdmin (Opcional)

pgAdmin es una interfaz gráfica para administrar la base de datos.

### Iniciar pgAdmin

```powershell
docker compose up -d pgadmin
```

### Acceder a pgAdmin

1. Abrir navegador en: http://localhost:5050
2. Login con credenciales del .env

### Conectar a la Base de Datos

1. Click derecho en "Servers" → "Create" → "Server..."
2. En pestaña "General":
   - Name: `FashionVision DB`
3. En pestaña "Connection":
   - Host name/address: `localhost`
   - Port: `5432`
   - Maintenance database: `fashionvision_ai`
   - Username: `fashionvision_ai_user`
   - Password: (la configurada en .env)

---

## 6. Levantar el Backend

### En PowerShell:

```powershell
# Activar entorno virtual
cd C:\ruta\al\proyecto\FashionVision-AI\backend
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar PYTHONPATH
$env:PYTHONPATH = "C:\ruta\al\proyecto\FashionVision-AI"

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### En Git Bash:

```bash
# Activar entorno virtual
cd /c/ruta/al/proyecto/FashionVision-AI
source backend/venv/Scripts/activate

# Configurar PYTHONPATH
export PYTHONPATH=$PWD

# Iniciar servidor
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verificar Backend

Abrir en navegador:
- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 7. Levantar el Frontend

### En otra terminal:

```powershell
cd C:\ruta\al\proyecto\FashionVision-AI\frontend
npm install
npm run dev
```

### Verificar Frontend

Abrir en navegador: http://localhost:5173

---

## 8. Verificar que Todo Funciona

### Test desde Terminal

```powershell
# Health check
curl http://localhost:8000/health

# Login (usuario de prueba)
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"admin@tienda.com\",\"password\":\"admin123\"}"

# Ver categorías
curl http://localhost:8000/api/categories

# Ver productos
curl http://localhost:8000/api/products
```

**Respuestas esperadas:**
- Health: `{"status":"healthy","database":"connected"}`
- Login: Debe devolver token y datos del usuario

---

## 9. Solución de Problemas

### Error: "Port already in use"

```powershell
# Encontrar y matar proceso en puerto 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# O usar un puerto diferente
uvicorn backend.app.main:app --port 8001
```

### Error: Docker no inicia (Hyper-V)

```powershell
# Verificar que Hyper-V está habilitado
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All

# Habilitar Hyper-V si no lo está
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All
```

### Error: PostgreSQL connection refused

```powershell
# Verificar que Docker está corriendo
docker compose ps

# Reiniciar contenedor
docker compose restart db

# Ver logs
docker compose logs db
```

### Error: Module not found (Python)

```powershell
# Asegurarse que PYTHONPATH está configurado
$env:PYTHONPATH = "C:\ruta\al\proyecto\FashionVision-AI"

# Verificar que entorno virtual está activo
# Debe aparecer (venv) antes del prompt
```

### Error: "virtual environment not found"

```powershell
# Crear entorno virtual nuevamente
cd C:\ruta\al\proyecto\FashionVision-AI\backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Error: Migraciones de Alembic fallan

```powershell
# Ver estado de migraciones
.\venv\Scripts\activate
$env:PYTHONPATH = $PWD
cd C:\ruta\al\proyecto\FashionVision-AI\backend
alembic current
alembic history

# Forzar upgrade
alembic upgrade head
```

---

## Credenciales del Sistema

| Servicio | Usuario | Contraseña | Puerto |
|----------|---------|------------|--------|
| PostgreSQL | fashionvision_ai_user | (del .env) | 5432 |
| pgAdmin | (del .env) | (del .env) | 5050 |
| Backend API | - | - | 8000 |
| Frontend (dev) | - | - | 5173 |
| Login por defecto | admin@tienda.com | admin123 | - |

---

## Próximos Pasos

Una vez configurado el entorno, ver:
- [Guía de pgAdmin](./GUIAS_PGADMIN.md) - Para administrar la base de datos visualmente
- [Comandos Importantes](./COMANDOS.md) - Referencia rápida de comandos del proyecto
- [Entorno Docker](./DOCKER_ENVIRONMENT.md) - Migraciones y gestión de contenedores
- [Guía WSL2](./WINDOWS_WSL2.md) - Recomendado para Windows