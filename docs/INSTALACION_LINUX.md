# Guía de Instalación - Linux

Sistema completo para levantar y ejecutar FashionVision-AI en entorno Linux.

---

## Tabla de Contenidos

1. [Requisitos Previos](#1-requisitos-previos)
2. [Instalación](#2-instalación)
3. [Configuración del Entorno](#3-configuración-del-entorno)
4. [Levantar Base de Datos](#4-levantar-base-de-datos)
5. [Levantar el Backend](#5-levantar-el-backend)
6. [Levantar el Frontend](#6-levantar-el-frontend)
7. [Verificar que Todo Funciona](#7-verificar-que-todo-funciona)
8. [Solución de Problemas](#8-solución-de-problemas)

---

## 1. Requisitos Previos

### Software Necesario

| Software | Versión Mínima | Comando de Instalación |
|----------|----------------|------------------------|
| Python | 3.10+ (3.12 recomendado) | `sudo apt install python3 python3-pip` |
| Docker | Latest | `sudo apt install docker.io docker-compose` |
| Git | 2.30+ | `sudo apt install git` |
| Node.js | 18+ | https://nodejs.org/ |

### Verificar Instalaciones

```bash
python3 --version
docker --version
git --version
node --version
npm --version
```

---

## 2. Instalación

### Paso 2.1: Clonar el Repositorio

```bash
cd ~/Proyectos
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI
```

### Paso 2.2: Instalar Dependencias del Sistema

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-venv python3-pip docker.io docker-compose

# Fedora
sudo dnf install -y python3 python3-pip docker docker-compose

# Arch Linux
sudo pacman -S python python-pip docker docker-compose
```

### Paso 2.3: Crear Entorno Virtual y Backend

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

### Paso 2.5: Instalar Frontend

```bash
cd ../frontend
npm install
```

---

## 3. Configuración del Entorno

### Paso 3.1: Variables de Entorno

```bash
# Desde la raíz del proyecto
cp backend/.env.example backend/.env

# Crear symlink
ln -s backend/.env .env
```

### Paso 3.2: Configurar .env

El archivo `backend/.env` debe contener:

```env
# Database
DATABASE_URL=postgresql+asyncpg://fashionvision_ai_user:fashionvision_ai_pass@localhost:5432/fashionvision_ai
DATABASE_URL_SYNC=postgresql://fashionvision_ai_user:fashionvision_ai_pass@localhost:5432/fashionvision_ai
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

---

## 4. Levantar Base de Datos

### Iniciar PostgreSQL con Docker

```bash
cd backend
sudo docker-compose up -d
```

### Verificar que PostgreSQL Está Corriendo

```bash
sudo docker ps
```

Deberías ver algo como:
```
CONTAINER ID   IMAGE           STATUS         PORTS
xxxxx         postgres:16     Up 5 hours     0.0.0.0:5432->5432/tcp
```

### Verificar Conexión a PostgreSQL

```bash
PGPASSWORD=fashionvision_ai_pass psql -h localhost -p 5432 -U fashionvision_ai_user -d fashionvision_ai
```

Comandos útiles en psql:
- `\dt` - Ver todas las tablas
- `\d nombre_tabla` - Ver estructura de tabla
- `SELECT * FROM users;` - Ver datos de tabla
- `\q` - Salir

---

## 5. Levantar el Backend

### En una terminal:

```bash
# Activar entorno virtual
cd /ruta/al/proyecto/FashionVision-AI
source backend/venv/bin/activate

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

## 6. Levantar el Frontend

### En otra terminal:

```bash
cd /ruta/al/proyecto/FashionVision-AI/frontend
npm run dev
```

### Verificar Frontend

Abrir en navegador: http://localhost:5173

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
# Matar proceso en puerto 8000
lsof -i :8000
kill -9 <PID>

# O usar un puerto diferente
uvicorn backend.app.main:app --port 8001
```

### Error: "permission denied" con Docker

```bash
# Usar sudo o agregar usuario al grupo docker
sudo docker-compose up -d
sudo usermod -aG docker $USER
```

### Error: PostgreSQL connection refused

```bash
# Verificar que Docker está corriendo
sudo docker ps

# Reiniciar contenedor
cd backend
sudo docker-compose restart

# Ver logs
sudo docker-compose logs db
```

### Error: Module not found (Python)

```bash
# Asegurarse que PYTHONPATH está configurado
export PYTHONPATH=/ruta/al/proyecto

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
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Credenciales del Sistema

| Servicio | Usuario | Contraseña | Puerto |
|----------|---------|------------|--------|
| PostgreSQL | fashionvision_ai_user | fashionvision_ai_pass | 5432 |
| Backend API | - | - | 8000 |
| Frontend | - | - | 5173 |
| Login por defecto | admin@tienda.com | admin123 | - |

---

## Próximos Pasos

Una vez configurado el entorno, ver:
- [Guía de pgAdmin](./GUIAS_PGADMIN.md) - Para administrar la base de datos visualmente
- [Comandos Importantes](./COMANDOS.md) - Referencia rápida de comandos del proyecto
