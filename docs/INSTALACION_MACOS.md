# Guía de Instalación - macOS

Sistema completo para levantar FashionVision-AI en macOS usando Homebrew + Docker Desktop.

## Tabla de Contenidos

1. [Arquitectura](#arquitectura)
2. [Requisitos Previos](#requisitos-previos)
3. [Instalación Paso a Paso](#instalación-paso-a-paso)
4. [Configuración del Entorno](#configuración-del-entorno)
5. [Iniciar los Servicios](#iniciar-los-servicios)
6. [Verificar el Sistema](#verificar-el-sistema)
7. [Solución de Problemas](#solución-de-problemas)

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    macOS Host                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│   │   Frontend    │   │   Backend    │   │     DB       │ │
│   │    Local      │   │    Local     │   │   Docker     │ │
│   │   :5173       │   │   :8000      │   │   :5432      │ │
│   │  (Vite)       │   │  (HotReload) │   │              │ │
│   └──────────────┘   └──────────────┘   └──────────────┘ │
│         ↑                  ↑                   ↑           │
│         │                  │                   │           │
│         └──────────────────┴───────────────────┘           │
│                              ↓                              │
│                       ┌──────────────┐                    │
│                       │   pgAdmin    │                    │
│                       │   Docker     │                    │
│                       │   :5050      │                    │
│                       └──────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Requisitos Previos

### Software Necesario

| Software | Versión | Comando de Instalación |
|----------|---------|------------------------|
| macOS | Monterey+ | - |
| Homebrew | Latest | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Docker Desktop | 4.0+ | `brew install --cask docker` |
| Git | Any | `brew install git` |
| Python | 3.12+ | `brew install python@3.12` |
| Node.js | 20+ | `brew install node` |

### Verificar Instalaciones

```bash
# Verificar Homebrew
brew --version

# Verificar Docker
docker --version
docker compose version

# Verificar Git
git --version

# Verificar Python
python3 --version

# Verificar Node.js
node --version
npm --version
```

---

## Instalación Paso a Paso

### Paso 1: Instalar Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Seguir las instrucciones del installer.

### Paso 2: Instalar Docker Desktop

```bash
brew install --cask docker
```

O descargar desde https://www.docker.com/products/docker-desktop/

**Importante**: Después de instalar, abrir Docker Desktop desde Applications y esperar a que inicialice.

### Paso 3: Instalar Python y Node.js

```bash
brew install python@3.12 node
```

### Paso 4: Clonar el Repositorio

```bash
# Ir al directorio home
cd ~

# Crear directorio de proyectos
mkdir -p Projects && cd Projects

# Clonar repositorio
git clone <repo-url> FashionVision-AI
cd FashionVision-AI
```

---

## Configuración del Entorno

### Paso 1: Copiar archivo de variables

```bash
cd ~/Projects/FashionVision-AI
cp .env.template .env
```

### Paso 2: Editar .env

```bash
nano .env
```

Configurar las siguientes variables:

```env
# DATABASE
POSTGRES_PASSWORD=your_strong_password_here

# SECURITY
SECRET_KEY=generate_with_openssl_rand_base64_32

# PGADMIN
PGADMIN_PASSWORD=your_pgadmin_password_here
```

### Paso 3: Configurar PATH

Agregar al `~/.zshrc` o `~/.bash_profile`:

```bash
echo 'export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## Iniciar los Servicios

### Opción A: Script automático (recomendado para nuevo setup)

```bash
cd ~/Projects/FashionVision-AI

# Primera vez: instalar todo
./scripts/setup.sh

# Iniciar servicios manualmente:
# Terminal 1:
cd backend && source venv/bin/activate && export PYTHONPATH=$PWD && uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Terminal 2:
cd frontend && npm run dev
```

### Opción B: Script deploy-local (un solo comando)

```bash
cd ~/Projects/FashionVision-AI
./scripts/deploy-local.sh
```

Esto iniciará backend y frontend en segundo plano.

---

## Verificar el Sistema

### Verificar servicios

```bash
# En otra terminal
curl http://localhost:8000/health
curl http://localhost:5173
```

### Verificar Docker

```bash
docker compose ps
```

### Accesos

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Frontend (dev) | http://localhost:5173 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| pgAdmin | http://localhost:5050 | ver .env |
| PostgreSQL | localhost:5432 | ver .env |

---

## Solución de Problemas

### Error: Docker Desktop no inicia

```bash
# Verificar que Docker Desktop está abierto
open -a Docker

# Ver estado
docker info
```

### Error: Puerto en uso

```bash
# Encontrar proceso
lsof -i :8000

# Matar proceso
kill -9 <PID>
```

### Error: Permiso denegado

```bash
# Verificar que usuario está en docker group
groups

# Si no está, agregar
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

### Error: ModuleNotFoundError

```bash
# Asegurar que PYTHONPATH está configurado
export PYTHONPATH=~/Projects/FashionVision-AI
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

### Python en Apple Silicon

Si tienes Mac con chip M1/M2/M3:

```bash
# Verificar arquitectura
uname -m  # debe mostrar arm64

# Asegurar que usas python3 correcto
which python3
/opt/homebrew/bin/python3 --version
```

---

## Comandos Rápidos

```bash
# Iniciar base de datos
docker compose up -d db

# Ver logs
docker compose logs -f

# Detener servicios
docker compose stop

# Ver contenedores activos
docker ps
```

---

## Homebrew - Comandos Útiles

```bash
# Actualizar Homebrew
brew update

# Ver packages instalados
brew list

# Ver servicios de Homebrew
brew services list

# Limpiar caché
brew cleanup
```

---

## Próximos Pasos

- Revisar [docs/DEVELOPMENT.md](./DEVELOPMENT.md) para flujo de trabajo
- Revisar [scripts/README.md](./scripts/README.md) para scripts disponibles
- Configurar IDE (VS Code o PyCharm)