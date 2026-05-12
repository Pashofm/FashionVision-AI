# Requisitos del Sistema

## Dependencias del Sistema Operativo

Antes de ejecutar el proyecto, necesitas instalar las siguientes dependencias del sistema.

### Ubuntu/Debian

```bash
sudo apt-get update && sudo apt-get install -y \
    build-essential \
    libffi-dev \
    python3-dev \
    libjpeg-dev \
    libpq-dev \
    git \
    curl \
    docker.io \
    docker-compose
```

### Fedora/RHEL

```bash
sudo yum install -y \
    @development-tools \
    libffi-devel \
    python3-devel \
    libjpeg-turbo-devel \
    postgresql-devel \
    git \
    curl \
    docker \
    docker-compose
```

### macOS

```bash
# Usando Homebrew
brew install \
    libffi \
    python@3.12 \
    git \
    curl \
    docker

# Instalar Docker Desktop desde https://docker.com
```

### Windows (WSL2)

Se recomienda usar WSL2 con Ubuntu. Ver [docs/INSTALACION_WINDOWS.md](./INSTALACION_WINDOWS.md) para instrucciones detalladas.

---

## Descripción de Dependencias

| Paquete | Descripción | ¿Por qué es necesario? |
|---------|-------------|------------------------|
| `build-essential` | Compilador GCC y herramientas de build | Compila extensiones C de Python (psycopg2, pillow, etc.) |
| `libffi-dev` | Foreign Function Interface library | Módulo `_ctypes` de Python - requerido por torch, cryptography |
| `python3-dev` | Archivos de desarrollo de Python | Headers para compilar paquetes con extensiones C |
| `libjpeg-dev` | Librerías de desarrollo JPEG | Pillow (procesamiento de imágenes) |
| `libpq-dev` | Librerías de desarrollo PostgreSQL | psycopg2 (conector PostgreSQL) |
| `git` | Sistema de control de versiones | Clonar repositorio + instalar pyenv |
| `curl` | Utilidad HTTP | Descargar pyenv y nvm |
| `docker.io` | Motor de contenedores | PostgreSQL y pgAdmin en desarrollo |

---

## Versiones de Python y Node.js

| Componente | Versión Requerida | Gestión Automática |
|------------|-------------------|-------------------|
| Python | **3.10, 3.11, o 3.12** | Los scripts instalan pyenv y la versión correcta automáticamente |
| Node.js | **18.x LTS o 20.x LTS** | Los scripts instalan nvm y la versión correcta automáticamente |

**Nota:** Python 3.13+ y Node.js 17 o inferior **NO** son compatibles actualmente.

---

## Verificación de Instalación

### Verificar Docker

```bash
docker --version
docker compose version
```

Si Docker no está instalado, visita https://docs.docker.com/get-docker/

### Verificar libffi (crítico para torch)

```bash
python3 -c "import _ctypes" && echo "OK: _ctypes funciona"
```

Si ves un error como `ModuleNotFoundError: No module named '_ctypes'`, significa que Python fue compilado sin `libffi-dev`. Ver la sección de [Solución de Problemas](#solución-de-problemas-comunes).

### Verificar espacio en disco

Se recomienda mínimo **10 GB** de espacio libre para:
- Dependencias Python (especialmente torch ~2GB)
- Docker images (PostgreSQL + pgAdmin ~500MB)
- Node modules (~500MB)

---

## Estructura de Scripts

| Script | Propósito | Cuándo Usar |
|--------|-----------|-------------|
| `./scripts/setup.sh` | Setup completo del entorno | **Primera vez** - después de clonar |
| `./scripts/dev-start.sh` | Iniciar DB + pgAdmin + migraciones | **Sesiones siguientes** |
| `./scripts/dev-stop.sh` | Detener servicios Docker | Cuando termines de desarrollar |

### Flujo de Inicialización

```
┌─────────────────────────────────────────────────────────────┐
│                    CLON NUEVO                                │
├─────────────────────────────────────────────────────────────┤
│  1. Instalar dependencias del SO                           │
│  2. git clone <repo>                                       │
│  3. ./scripts/setup.sh  ← Instala pyenv, Python 3.12,     │
│       nvm, Node 18, crea venv, instala deps, inicia DB    │
│  4. ./scripts/dev-start.sh  ← Levanta DB + pgAdmin         │
│  5. Iniciar backend + frontend manualmente                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    SESIONES SIGUIENTES                     │
├─────────────────────────────────────────────────────────────┤
│  1. ./scripts/dev-start.sh  ← Solo levanta DB + migraciones│
│  2. Iniciar backend + frontend manualmente                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Solución de Problemas Comunes

### Error: `ModuleNotFoundError: No module named '_ctypes'`

**Causa:** Python fue compilado sin `libffi-dev` instalado.

**Solución:**

```bash
# 1. Instalar libffi-dev
sudo apt-get install -y libffi-dev python3-dev

# 2. Reconstruir Python 3.12
rm -rf ~/.pyenv/versions/3.12.0
~/.pyenv/bin/pyenv install 3.12.0

# 3. Recrear venv
rm -rf backend/venv
./scripts/setup.sh
```

### Error: `torch==2.5.1` not found

**Causa:** La versión de torch es incorrecta en requirements.txt o el sistema tiene Python 3.14.

**Solución:**

```bash
# Verificar versión de Python
python3 --version

# Si es 3.14, los scripts deberían auto-instalar 3.12
# Si el problema persiste, verificar requirements.txt
grep torch backend/requirements.txt
```

### Error: `alembic: command not found`

**Causa:** Script intenta usar alembic sin activar el venv o con PATH incorrecto.

**Solución:**

```bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
alembic upgrade head
```

### Error: `No such file or directory: 'requirements.txt'`

**Causa:** El script se ejecuta desde el directorio incorrecto.

**Solución:**

```bash
cd /ruta/al/proyecto
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

### Error: Docker container not starting

**Causa:** Puerto en uso o Docker daemon no está corriendo.

**Solución:**

```bash
# Verificar estado de Docker
sudo systemctl status docker
sudo systemctl start docker

# Verificar puertos en uso
docker compose ps

# Limpiar contenedores
docker compose down
docker compose up -d
```

### Error: `pg_isready` timeout en pgAdmin

**Causa:** La base de datos tarda en iniciar.

**Solución:**

```bash
# Esperar más tiempo
docker compose logs db
docker compose restart db
```

---

## Verificación del Sistema

Después de completar la instalación, verifica que todo funcione:

```bash
# 1. Verificar Python
python3 --version  # Debería ser 3.12 (via pyenv)
source backend/venv/bin/activate
python --version    # Debería ser 3.12

# 2. Verificar _ctypes (crítico)
python -c "import _ctypes; print('OK: _ctypes')"

# 3. Verificar torch
python -c "import torch; print(f'torch: {torch.__version__}')"

# 4. Verificar Docker
docker compose ps

# 5. Verificar pgAdmin
curl http://localhost:5050
```

---

## Credenciales y Puertos

| Servicio | Puerto | Usuario | Contraseña |
|----------|--------|---------|------------|
| Frontend (Vite) | 5173 | - | - |
| Backend (FastAPI) | 8000 | - | - |
| pgAdmin | 5050 | admin@fashionvision.com | admin123 |
| PostgreSQL | 5432 | fashionvision_ai_user | fashionvision_ai_pass |

---

## Recursos Adicionales

- [Guía de Instalación Linux](./INSTALACION_LINUX.md)
- [Guía de Instalación Windows](./INSTALACION_WINDOWS.md)
- [Guía de Docker](./DOCKER_ENVIRONMENT.md)
- [Comandos Importantes](./COMANDOS.md)