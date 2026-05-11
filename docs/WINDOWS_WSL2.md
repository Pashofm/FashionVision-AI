# Guía de Instalación - Windows con WSL2

Sistema completo para levantar FashionVision-AI en Windows usando WSL2 (Ubuntu) + Docker Desktop.

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
│                    Windows Host                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              WSL2 (Ubuntu)                           │   │
│  │  ┌──────────────┐   ┌──────────────┐                 │   │
│  │  │   Backend    │   │   Frontend   │  (Hot Reload)  │   │
│  │  │   :8000      │   │   :5173      │                 │   │
│  │  └──────────────┘   └──────────────┘                 │   │
│  │         │                  │                          │   │
│  │         └──────────────────┴──────────────────┐     │   │
│  └────────────────────────────────────────────────│─────┘   │
│                                                     │       │
│  ┌─────────────────────────────────────────────────▼─────┐ │
│  │              Docker Desktop (Windows)                 │ │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────┐ │ │
│  │  │     DB       │   │   pgAdmin    │   │ Backend  │ │ │
│  │  │   :5432      │   │   :5050      │   │  Docker  │ │ │
│  │  └──────────────┘   └──────────────┘   └──────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Requisitos Previos

### Software Necesario

| Software | Versión | Notes |
|----------|---------|-------|
| Windows 10/11 | 22H2+ | Con soporte para WSL2 |
| WSL2 | Latest | Incluido en Windows |
| Ubuntu (WSL) | 22.04 LTS | Desde Microsoft Store |
| Docker Desktop | 4.0+ | Con integración WSL2 |
| Git | 2.30+ | En WSL2 |

### Verificar Instalación (en WSL2 terminal)

```bash
# Verificar WSL2
wsl --status

# Verificar Ubuntu
wsl -l -v

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

### Paso 1: Habilitar WSL2

Ejecutar en **PowerShell como Administrador**:

```powershell
wsl --install
```

Reiniciar el computador después de la instalación.

### Paso 2: Instalar Ubuntu desde Microsoft Store

1. Abrir Microsoft Store
2. Buscar "Ubuntu 22.04 LTS"
3. Click en "Instalar"
4. Crear usuario y contraseña cuando termine

### Paso 3: Instalar Docker Desktop

1. Descargar desde https://www.docker.com/products/docker-desktop/
2. Ejecutar el instalador
3. **Importante**: Marcar "Use WSL 2 instead of Hyper-V"
4. Esperar a que termine y reiniciar

### Paso 4: Configurar Docker en WSL2

En la terminal de Ubuntu (WSL2):

```bash
# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Verificar que Docker funciona
docker ps

# Si hay error de permisos, reiniciar WSL
wsl --shutdown
# Luego abrir Ubuntu de nuevo
```

### Paso 5: Clonar el Repositorio

En la terminal de Ubuntu:

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

### Paso 3: Configurar puertos en Windows Firewall (opcional)

Si tienes problemas de conexión, verificar que los puertos no estén bloqueados.

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

Esto iniciara backend y frontend en segundo plano.

---

## Verificar el Sistema

### Verificar servicios

```bash
# En otra terminal de WSL2
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

### Error: WSL2 no está instalado

```powershell
# En PowerShell Admin
wsl --install
```

### Error: Docker no inicia en WSL2

```bash
# En WSL2 terminal
export DOCKER_HOST=wsl://localhost
docker ps
```

### Error: Puerto en uso

```bash
# Encontrar proceso
lsof -i :8000

# Matar proceso
kill -9 <PID>
```

### Error: Permiso denegado en Docker

```bash
# Reiniciar WSL
wsl --shutdown

# O agregar usuario al grupo
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

### Error: ModuleNotFoundError

```bash
# Asegurar que PYTHONPATH está configurado
export PYTHONPATH=~/Projects/FashionVision-AI
```

### Problemas de encoding con npm en WSL2

```bash
# Si hay errores con caracteres especiales
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
npm install
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

# Reiniciar WSL2
wsl --shutdown
```

---

## Próximos Pasos

- Revisar [docs/DEVELOPMENT.md](./DEVELOPMENT.md) para flujo de trabajo
- Revisar [scripts/README.md](./scripts/README.md) para scripts disponibles
- Configurar IDE en WSL2 (VS Code con Remote WSL)