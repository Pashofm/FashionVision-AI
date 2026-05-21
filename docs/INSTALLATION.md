# Guia de Instalacion - FashionVision-AI

Sistema completo para levantar y ejecutar FashionVision-AI.

---

## Selecciona tu Sistema Operativo

| Sistema | Seccion |
|---------|---------|
| Linux (Ubuntu, Debian, Fedora, Arch) | [Linux](#linux) |
| Windows + WSL2 (Recomendado) | [WSL2](#windows-wsl2) |
| Windows Nativo (PowerShell) | [Windows](#windows-nativo) |
| macOS | [macOS](#macos) |

---

## Linux

### Requisitos Previos

| Software | Version | Comando de Instalacion |
|----------|---------|------------------------|
| Python | 3.12+ | `sudo apt install python3 python3-pip` |
| Docker | Latest | `sudo apt install docker.io docker-compose` |
| Git | 2.30+ | `sudo apt install git` |
| Node.js | 20+ | https://nodejs.org/ |

### Instalacion

```bash
# 1. Clonar repositorio
cd ~/Proyectos
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI

# 2. Instalar dependencias del sistema
sudo apt update
sudo apt install -y python3-venv python3-pip docker.io docker-compose

# 3. Crear entorno virtual y backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar Docker
sudo usermod -aG docker $USER
# Cerrar sesion y volver a entrar

# 5. Instalar Frontend
cd ../frontend
npm install

# 6. Copiar variables de entorno
cp .env.template .env

# 7. Editar .env
nano .env

# 8. Levantar base de datos
docker compose up -d db

# 9. Verificar que PostgreSQL esta corriendo
docker ps

# 10. Levantar Backend
cd ..
source backend/venv/bin/activate
export PYTHONPATH=$PWD
alembic upgrade head
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 11. Levantar Frontend (en otra terminal)
cd frontend
npm run dev
```

### Verificacion

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tienda.com","password":"admin123"}'
```

### Solucion de Problemas

```bash
# Error: Puerto en uso
lsof -i :8000
kill -9 <PID>

# Error: permission denied con Docker
sudo docker compose up -d

# Error: PostgreSQL connection refused
docker compose restart db
docker compose logs db
```

---

## Windows WSL2 (Recomendado)

### Arquitectura

```
Windows Host
├── WSL2 (Ubuntu)
│   ├── Backend (:8000)
│   └── Frontend (:5173)
└── Docker Desktop
    ├── DB (:5432)
    ├── pgAdmin (:5050)
    └── Backend Docker
```

### Requisitos Previos

| Software | Version | Instalacion |
|----------|---------|-------------|
| Windows 10/11 | 22H2+ | - |
| WSL2 | Latest | `wsl --install` |
| Ubuntu | 22.04 LTS | Microsoft Store |
| Docker Desktop | 4.0+ | docker.com |

### Instalacion Paso a Paso

#### 1. Habilitar WSL2 (PowerShell como Administrador)

```powershell
wsl --install
```

Reiniciar el equipo.

#### 2. Instalar Ubuntu desde Microsoft Store

Buscar "Ubuntu 22.04 LTS" e instalar.

#### 3. Instalar Docker Desktop

1. Descargar de https://www.docker.com/products/docker-desktop/
2. Marcar "Use WSL 2 instead of Hyper-V"
3. Reiniciar

#### 4. Configurar Docker en WSL2

En la terminal de Ubuntu:

```bash
sudo usermod -aG docker $USER
# Cerrar sesion y volver a entrar
docker ps
```

#### 5. Clonar el Repositorio

```bash
mkdir -p ~/Projects && cd ~/Projects
git clone <repo-url> FashionVision-AI
cd FashionVision-AI
```

#### 6. Setup inicial

```bash
./scripts/setup.sh
nano .env  # Editar credenciales
```

#### 7. Iniciar servicios

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && export PYTHONPATH=$PWD && uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Verificacion

```bash
curl http://localhost:8000/health
curl http://localhost:5173
```

### Solucion de Problemas

```bash
# Docker no inicia en WSL2
export DOCKER_HOST=wsl://localhost
docker ps

# Problemas de permisos
wsl --shutdown
# Abrir Ubuntu de nuevo

# Puerto en uso
lsof -i :8000
kill -9 <PID>
```

---

## Windows Nativo

**Nota:** Para mejor compatibilidad, se recomienda usar WSL2. Ver seccion anterior.

### Requisitos Previos

| Software | Version | Descargar |
|----------|---------|----------|
| Python | 3.12+ | python.org/downloads |
| Docker Desktop | Latest | docker.com |
| Git | 2.30+ | git-scm.com |
| Node.js | 20+ | nodejs.org |

### Instalacion

#### 1. Clonar Repositorio (PowerShell)

```powershell
cd C:\Proyectos
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI
```

#### 2. Crear Entorno Virtual y Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Instalar Frontend

```powershell
cd ..\frontend
npm install
```

#### 4. Configurar .env

```powershell
copy .env.template .env
# Editar con credenciales
```

#### 5. Levantar Base de Datos

```powershell
docker compose up -d db
```

#### 6. Levantar Backend

```powershell
cd ..
$env:PYTHONPATH = $PWD
alembic upgrade head
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 7. Levantar Frontend (otra terminal)

```powershell
cd frontend
npm run dev
```

### Solucion de Problemas

```powershell
# Puerto en uso
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Hyper-V no habilitado
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All

# PostgreSQL connection refused
docker compose restart db
```

---

## macOS

### Arquitectura

```
macOS Host
├── Frontend Local (:5173)
├── Backend Local (:8000)
└── Docker
    ├── DB (:5432)
    └── pgAdmin (:5050)
```

### Requisitos Previos

| Software | Version | Comando |
|----------|---------|---------|
| Homebrew | Latest | /bin/bash -c "$(curl -fsSL ...)" |
| Docker Desktop | 4.0+ | brew install --cask docker |
| Git | Any | brew install git |
| Python | 3.12+ | brew install python@3.12 |
| Node.js | 20+ | brew install node |

### Instalacion

#### 1. Instalar Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Instalar Docker y dependencias

```bash
brew install --cask docker python@3.12 node
```

Abrir Docker Desktop desde Applications.

#### 3. Clonar Repositorio

```bash
mkdir -p ~/Projects && cd ~/Projects
git clone <repo-url> FashionVision-AI
cd FashionVision-AI
```

#### 4. Setup inicial

```bash
./scripts/setup.sh
nano .env
```

#### 5. Iniciar servicios

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && export PYTHONPATH=$PWD && uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Verificacion

```bash
curl http://localhost:8000/health
curl http://localhost:5173
```

### Apple Silicon (M1/M2/M3)

```bash
uname -m  # debe mostrar arm64
which python3
```

---

## Credenciales del Sistema

| Servicio | Usuario | Contrasena | Puerto |
|----------|---------|------------|--------|
| PostgreSQL | fashionvision_ai_user | (del .env) | 5432 |
| pgAdmin | admin@fashionvision.com | admin123 | 5050 |
| Login por defecto | admin@tienda.com | admin123 | - |

## URLs de Acceso

| Servicio | URL |
|----------|-----|
| Frontend (dev) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |
| App (Docker) | http://localhost |

## Proximos Pasos

- [DEVELOPMENT.md](./DEVELOPMENT.md) - Flujo de trabajo en equipo
- [scripts/README.md](../scripts/README.md) - Scripts de automatizacion
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Despliegue a produccion