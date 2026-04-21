# Guía de Instalación y Configuración del Proyecto

Sistema completo para levantar y ejecutar FashionVision-AI en cualquier entorno de desarrollo.

---

## Tabla de Contenidos

1. [Requisitos Previos](#1-requisitos-previos)
2. [Instalación en Linux](#2-instalación-en-linux)
3. [Instalación en Windows](#3-instalación-en-windows)
4. [Configuración del Entorno](#4-configuración-del-entorno)
5. [Levantar Base de Datos](#5-levantar-base-de-datos)
6. [Levantar el Backend](#6-levantar-el-backend)
7. [Verificar que Todo Funciona](#7-verificar-que-todo-funciona)
8. [Solución de Problemas](#8-solución-de-problemas)

---

## 1. Requisitos Previos

### Software Necesario

| Software | Versión Mínima | Descargar |
|----------|----------------|----------|
| Python | 3.10+ (3.12 recomendado) | https://www.python.org/downloads/ |
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop/ |
| Git | 2.30+ | https://git-scm.com/download |
| Node.js | 18+ | https://nodejs.org/ (para frontend) |

### Verificar Instalaciones

**Linux (terminal):**
```bash
python3 --version
docker --version
git --version
```

**Windows (PowerShell o CMD):**
```powershell
python --version
docker --version
git --version
```

---

## 2. Instalación en Linux

### Paso 2.1: Clonar el Repositorio

```bash
cd ~/Proyectos
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI
```

### Paso 2.2: Instalar Python y Dependencias del Sistema

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-venv python3-pip docker.io docker-compose

# Fedora
sudo dnf install -y python3 python3-pip docker docker-compose

# Arch Linux
sudo pacman -S python python-pip docker docker-compose
```

### Paso 2.3: Crear Entorno Virtual

```bash
cd backend

# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Si hay errores con bcrypt, instalar versión compatible:
pip install 'bcrypt<5.0.0'
```

### Paso 2.4: Configurar Docker

```bash
# Agregar usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# Cerrar sesión y volver a entrar para que tome efecto
# O ejecutar:
newgrp docker

# Habilitar y iniciar Docker
sudo systemctl enable docker
sudo systemctl start docker
```

---

## 3. Instalación en Windows

### Paso 3.1: Clonar el Repositorio

Usar Git Bash, PowerShell o CMD:
```powershell
cd C:\Proyectos
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI
```

### Paso 3.2: Instalar Python

1. Descargar Python desde https://www.python.org/downloads/
2. **IMPORTANTE**: Marcar checkbox "Add Python to PATH"
3. Click en "Install Now"
4. Verificar instalación:
```powershell
python --version
pip --version
```

### Paso 3.3: Instalar Docker Desktop

1. Descargar desde https://www.docker.com/products/docker-desktop/
2. Instalar siguiendo el wizard
3. Reiniciar computadora
4. Verificar:
```powershell
docker --version
docker-compose --version
```

### Paso 3.4: Crear Entorno Virtual

```powershell
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno (CMD o PowerShell)
venv\Scripts\activate

# Activar entorno (Git Bash)
source venv/Scripts/activate

# Instalar dependencias
pip install -r requirements.txt

# Si hay errores con bcrypt, instalar versión compatible:
pip install 'bcrypt<5.0.0'
```

### Paso 3.5: Habilitar Hyper-V (Necesario para Docker)

```powershell
# Abrir PowerShell como Administrador
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All
```

---

## 4. Configuración del Entorno

### Paso 4.1: Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp backend/.env.example backend/.env
```

### Paso 4.2: Crear Symlink (SOLO Linux/macOS)

```bash
# Desde la raíz del proyecto
ln -s backend/.env .env
```

### Paso 4.3: Configurar .env

El archivo `.env` debe contener:

```env
# Database
DATABASE_URL=postgresql+asyncpg://fashionvision_ai_user:fashionvision_ai_pass@localhost:5433/fashionvision_ai
DATABASE_URL_SYNC=postgresql://fashionvision_ai_user:fashionvision_ai_pass@localhost:5433/fashionvision_ai
POSTGRES_DB=fashionvision_ai
POSTGRES_USER=fashionvision_ai_user
POSTGRES_PASSWORD=fashionvision_ai_pass
POSTGRES_PORT=5432

# Security
SECRET_KEY=dev_secret_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# App
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
BACKEND_PORT=8000

# Files
MEDIA_DIR=/app/media
MAX_IMAGE_SIZE_MB=5
```

**Nota para Windows**: Si tienes problemas con el symlink, puedes copiar el archivo:
```powershell
copy backend\.env.example backend\.env
```

---

## 5. Levantar Base de Datos

### Usando Docker Compose (Ambos SO)

```bash
cd backend

# Linux
sudo docker-compose up -d

# Windows (en CMD o PowerShell, NO Git Bash)
docker-compose up -d
```

### Verificar que PostgreSQL Está Corriendo

```bash
# Linux y Windows
docker ps
```

Deberías ver algo como:
```
CONTAINER ID   IMAGE           STATUS         PORTS
xxxxx         postgres:16     Up 5 hours     0.0.0.0:5433->5432/tcp
```

### Verificar Conexión a PostgreSQL

```bash
# Linux
PGPASSWORD=fashionvision_ai_pass psql -h localhost -p 5433 -U fashionvision_ai_user -d fashionvision_ai

# Windows (usar Git Bash o PowerShell)
docker exec -it fashionvision_db psql -U fashionvision_ai_user -d fashionvision_ai
```

Comandos útiles en psql:
- `\dt` - Ver todas las tablas
- `\d nombre_tabla` - Ver estructura de tabla
- `SELECT * FROM users;` - Ver datos de tabla
- `\q` - Salir

---

## 6. Levantar el Backend

### En Linux

```bash
# Activar entorno virtual
cd /ruta/al/proyecto/FashionVision-AI
source backend/venv/bin/activate

# Configurar PYTHONPATH
export PYTHONPATH=$PWD

# Iniciar servidor
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### En Windows

```powershell
# Activar entorno virtual
cd C:\ruta\al\proyecto\FashionVision-AI\backend
.\venv\Scripts\activate

# Configurar PYTHONPATH (PowerShell)
$env:PYTHONPATH = $PWD

# Iniciar servidor
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### En Windows (Git Bash)

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

## 7. Verificar que Todo Funciona

### Test desde Terminal

```bash
# Health check
curl http://localhost:8000/health

# Login (usuario de prueba)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tienda.com","password":"admin123"}'

# Ver categorías
curl http://localhost:8000/api/categories

# Ver productos
curl http://localhost:8000/api/products
```

**Respuestas esperadas:**
- Health: `{"status":"healthy","database":"connected"}`
- Login: Debe devolver token y datos del usuario

---

## 8. Solución de Problemas

### Error: "Port already in use" (Errno 98)

```bash
# Linux: Matar proceso en puerto 8000
lsof -i :8000
kill -9 <PID>

# Windows: Encontrar y matar proceso
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# O usar un puerto diferente
uvicorn backend.app.main:app --port 8001
```

### Error: "permission denied" con Docker

```bash
# Linux: Usar sudo o agregar usuario al grupo docker
sudo docker-compose up -d
sudo usermod -aG docker $USER
```

### Error: PostgreSQL connection refused

```bash
# Verificar que Docker está corriendo
docker ps

# Reiniciar contenedor
docker-compose restart

# Ver logs
docker-compose logs db
```

### Error: Module not found (Python)

```bash
# Asegurarse que PYTHONPATH está configurado
# Linux
export PYTHONPATH=/ruta/al/proyecto

# Windows PowerShell
$env:PYTHONPATH = "C:\ruta\al\proyecto"

# Verificar que entorno virtual está activo
# Debe aparecer (venv) antes del prompt
```

### Error: bcrypt installation failed

```bash
# Instalar versión compatible
pip install 'bcrypt<5.0.0'
```

### Error: "virtual environment not found"

```bash
# Crear entorno virtual nuevamente
cd backend
python -m venv venv
source venv/bin/activate  # Linux
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## Credenciales del Sistema

| Servicio | Usuario | Contraseña | Puerto |
|----------|---------|------------|--------|
| PostgreSQL | fashionvision_ai_user | fashionvision_ai_pass | 5433 |
| Backend API | - | - | 8000 |
| Login por defecto | admin@tienda.com | admin123 | - |

---

## Próximos Pasos

Una vez configurado el entorno, ver:
- [Guía de pgAdmin](./GUIAS_PGADMIN.md) - Para administrar la base de datos visualmente
- [Comandos Importantes](./COMANDOS.md) - Referencia rápida de comandos del proyecto
