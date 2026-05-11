# Guía de Instalación - Linux

Sistema completo para levantar y ejecutar FashionVision-AI en entorno Linux.

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

| Software | Versión Mínima | Comando de Instalación |
|----------|----------------|------------------------|
| Python | 3.12+ | `sudo apt install python3 python3-pip` |
| Docker | Latest | `sudo apt install docker.io docker-compose` |
| Git | 2.30+ | `sudo apt install git` |
| Node.js | 20+ | https://nodejs.org/ |

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
cp .env.template .env
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

```bash
cd ~/FashionVision-AI
docker compose up -d db
```

### Verificar que PostgreSQL Está Corriendo

```bash
docker ps
```

Deberías ver algo como:
```
CONTAINER ID   IMAGE           STATUS         PORTS
xxxxx         postgres:16     Up 5 hours     0.0.0.0:5432->5432/tcp
```

### Verificar Conexión a PostgreSQL

```bash
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

```bash
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

### En una terminal:

```bash
# Activar entorno virtual
cd ~/FashionVision-AI/backend
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias (incluye Alembic para migraciones)
pip install -r requirements.txt

# Configurar PYTHONPATH
export PYTHONPATH=~/FashionVision-AI

# Ejecutar migraciones
alembic upgrade head

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

```bash
cd ~/FashionVision-AI/frontend
npm install
npm run dev
```

### Verificar Frontend

Abrir en navegador: http://localhost:5173

---

## 8. Verificar que Todo Funciona

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

## 9. Solución de Problemas

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
sudo docker compose up -d
sudo usermod -aG docker $USER
```

### Error: PostgreSQL connection refused

```bash
# Verificar que Docker está corriendo
docker compose ps

# Reiniciar contenedor
docker compose restart db

# Ver logs
docker compose logs db
```

### Error: Module not found (Python)

```bash
# Asegurarse que PYTHONPATH está configurado
export PYTHONPATH=~/FashionVision-AI

# Verificar que entorno virtual está activo
# Debe aparecer (venv) antes del prompt
```

### Error: "virtual environment not found"

```bash
# Crear entorno virtual nuevamente
cd ~/FashionVision-AI/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Error: Migraciones de Alembic fallan

```bash
# Ver estado de migraciones
source venv/bin/activate
export PYTHONPATH=~/FashionVision-AI
cd ~/FashionVision-AI/backend
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
- [Guía de Despliegue](./DEPLOYMENT.md) - Para producción