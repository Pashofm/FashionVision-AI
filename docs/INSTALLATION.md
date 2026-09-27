# Guia de Instalacion - FashionVision-AI

Sistema completo para levantar y ejecutar FashionVision-AI usando Docker.

---

## Requisitos Previos (todos los SO)

| Software | Version | Instalacion |
|----------|---------|-------------|
| Docker | Latest | `curl -fsSL https://get.docker.com | sh` |
| Git | 2.30+ | [git-scm.com](https://git-scm.com) |

## Flujo Principal (todos los SO)

Una vez instalado Docker y Git, el flujo es identico para Linux, macOS, Windows WSL2 y Windows Nativo:

```bash
# 1. Clonar repositorio
git clone git@github.com:Pashofm/FashionVision-AI.git
cd FashionVision-AI

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales (nano .env / notepad .env)

# 3. Construir y levantar todos los servicios
make up-build

# 4. Ejecutar migraciones
make migrate

# 5. Cargar datos de prueba
make seed
```

Servicios disponibles:

| Servicio | URL |
|----------|-----|
| App (Frontend) | http://localhost |
| Backend API | http://localhost/api |
| API Docs (Swagger) | http://localhost/docs |
| pgAdmin | http://localhost:5050 |

---

## Linux

### 1. Instalar Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Cerrar sesion y volver a entrar para que el grupo tenga efecto
```

### 2. Instalar Git

```bash
sudo apt install git -y   # Debian/Ubuntu
sudo dnf install git -y   # Fedora
sudo pacman -S git        # Arch
```

### 3. Seguir el Flujo Principal

Ejecutar los comandos de la seccion [Flujo Principal](#flujo-principal-todos-los-so).

### Solucion de Problemas

```bash
# Error: permission denied con Docker
sudo docker compose up -d

# Error: PostgreSQL connection refused
make logs-db
docker compose restart db

# Verificar servicios
docker ps
```

---

## Windows WSL2 (Recomendado)

### Arquitectura

```
Windows Host
├── WSL2 (Ubuntu)
│   └── Codigo fuente
└── Docker Desktop
    ├── Frontend (:80)
    ├── Backend (:8000)
    ├── DB (:5432)
    ├── pgAdmin (:5050)
    └── nginx
```

### 1. Habilitar WSL2 (PowerShell como Administrador)

```powershell
wsl --install
```

Reiniciar el equipo.

### 2. Instalar Ubuntu desde Microsoft Store

Buscar "Ubuntu 22.04 LTS" o superior e instalar.

### 3. Instalar Docker Desktop

1. Descargar de https://www.docker.com/products/docker-desktop/
2. Marcar "Use WSL 2 instead of Hyper-V"
3. Reiniciar

### 4. Configurar Docker en WSL2

En la terminal de Ubuntu:

```bash
sudo usermod -aG docker $USER
# Cerrar sesion y volver a entrar
docker ps
```

### 5. Seguir el Flujo Principal

Ejecutar los comandos de la seccion [Flujo Principal](#flujo-principal-todos-los-so) desde la terminal de Ubuntu.

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

### 1. Instalar Docker Desktop

1. Descargar de https://www.docker.com/products/docker-desktop/
2. Instalar y reiniciar

### 2. Instalar Git

Descargar de https://git-scm.com e instalar (incluir Git Bash).

### 3. Seguir el Flujo Principal

Ejecutar los comandos de la seccion [Flujo Principal](#flujo-principal-todos-los-so) desde PowerShell o Git Bash.

### Solucion de Problemas

```powershell
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
└── Docker
    ├── Frontend (:80)
    ├── Backend (:8000)
    ├── DB (:5432)
    ├── pgAdmin (:5050)
    └── nginx
```

### 1. Instalar Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Instalar Docker y Git

```bash
brew install --cask docker git
```

Abrir Docker Desktop desde Applications.

### 3. Seguir el Flujo Principal

Ejecutar los comandos de la seccion [Flujo Principal](#flujo-principal-todos-los-so).

### Verificacion

```bash
curl http://localhost/health
curl http://localhost
```

### Apple Silicon (M1/M2/M3/M4)

```bash
uname -m  # debe mostrar arm64
```

---

## Credenciales del Sistema

| Servicio | Usuario | Contrasena | Puerto |
|----------|---------|------------|--------|
| PostgreSQL | fashionvision_ai_user | (del .env) | 5432 |
| pgAdmin | admin@fashionvision.com | admin123 | 5050 |
| Login por defecto | admin@tienda.com | admin123 | - |

---

## Desarrollo sin Docker (avanzado)

Si prefieres ejecutar los servicios de forma nativa sin contenedores, sigue estos pasos.

### Requisitos Previos

| Software | Version | Comando |
|----------|---------|---------|
| Python | 3.12+ | Ver [python.org](https://python.org) |
| Node.js | 20+ | Ver [nodejs.org](https://nodejs.org) |
| PostgreSQL | 16+ | Instalacion nativa o vía Docker |

### Instalacion

```bash
# 1. Clonar repositorio
git clone git@github.com:Pashofm/FashionVision-AI.git
cd FashionVision-AI

# 2. Copiar variables de entorno
cp .env.example .env
# Editar .env con credenciales de PostgreSQL local

# 3. Levantar solo la base de datos con Docker (opcional si no tienes PostgreSQL nativo)
docker compose up -d db

# 4. Backend
cd backend
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# .\venv\Scripts\activate     # Windows PowerShell
pip install -r requirements.txt
cd ..
export PYTHONPATH=$PWD        # Linux/macOS
# $env:PYTHONPATH = $PWD      # Windows PowerShell
alembic upgrade head
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

### URLs (desarrollo local)

| Servicio | URL |
|----------|-----|
| Frontend (dev) | http://localhost:5173 |
| Backend API | http://localhost/api |
| API Docs | http://localhost/docs |
| pgAdmin (si se usa Docker) | http://localhost:5050 |

---

## Proximos Pasos

- [DEVELOPMENT.md](./DEVELOPMENT.md) - Flujo de trabajo en equipo
- [scripts/README.md](../scripts/README.md) - Scripts de automatizacion
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Despliegue a produccion
