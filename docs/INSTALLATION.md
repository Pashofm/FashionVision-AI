# Instalación

FashionVision AI se ejecuta con Docker. No necesitas instalar Python, Node.js ni PostgreSQL para usar la demo.

Elige el método que corresponde a tu equipo:

| Sistema | Guía | Recomendación |
|---|---|---|
| Linux | [Linux](#linux) | Docker Engine nativo |
| Windows 10/11 | [Windows nativo](#windows-nativo) | Docker Desktop y PowerShell |
| Windows 10/11 con Ubuntu | [Windows con WSL2](#windows-con-wsl2) | Recomendado para desarrollo |

## Requisitos comunes

- Git 2.40+.
- Docker Engine 24+ o Docker Desktop 4+.
- Docker Compose v2 (`docker compose`).
- 8 GB de RAM recomendados.
- 20 GB libres recomendados para imágenes, modelos y cachés.

Después de instalar las herramientas, verifica:

```bash
git --version
docker --version
docker compose version
```

## Flujo de la demo

Estos comandos son iguales en Linux y WSL2. En PowerShell usa la variante indicada en la sección de Windows nativo.

```bash
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
docker compose up -d --build --wait
make seed
```

`--wait` espera a que los servicios estén saludables y a que el backend aplique las migraciones. Si no tienes `make`, usa el comando de seed de [COMANDOS.md](COMANDOS.md#datos-iniciales-y-migraciones).

Comprueba el resultado:

```bash
docker compose ps
curl http://localhost/health
```

## Acceso

| Recurso | URL |
|---|---|
| Aplicación | `http://localhost` |
| Health | `http://localhost/health` |
| Swagger | `http://localhost/docs` |
| pgAdmin opcional | `http://localhost:5050` |

Las cuentas de demostración se documentan en [QUICKSTART.md](../QUICKSTART.md#usuarios-de-prueba). Para operar la aplicación consulta [USER_GUIDE.md](USER_GUIDE.md).

## Linux

### 1. Instalar Docker y Git

Instala Docker Engine y el plugin Docker Compose usando la guía oficial para tu distribución:

- Debian/Ubuntu: <https://docs.docker.com/engine/install/debian/> o <https://docs.docker.com/engine/install/ubuntu/>.
- Fedora: <https://docs.docker.com/engine/install/fedora/>.
- Arch Linux: instala los paquetes `docker`, `docker-compose`, `git` y `make` con `pacman`.

Instala Git y Make con el gestor de paquetes de tu distribución:

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install -y git make

# Fedora
sudo dnf install -y git make
```

En Arch Linux:

```bash
sudo pacman -Syu docker docker-compose git make
sudo systemctl enable --now docker
```

Permite usar Docker sin `sudo` y vuelve a iniciar sesión:

```bash
sudo usermod -aG docker "$USER"
```

Comprueba que Docker funciona antes de continuar:

```bash
docker run --rm hello-world
```

### 2. Ejecutar la demo

Sigue el [flujo de la demo](#flujo-de-la-demo). Si el puerto 80 está ocupado, define `FRONTEND_HOST_PORT=8080` en `.env` antes de iniciar los servicios y abre `http://localhost:8080`.

## Windows nativo

Este método ejecuta los comandos desde PowerShell. Docker Desktop puede usar WSL2 internamente, pero no requiere trabajar dentro de una terminal Linux.

### 1. Instalar herramientas

1. Activa la virtualización en BIOS/UEFI si Docker Desktop lo solicita.
2. Instala [Docker Desktop](https://www.docker.com/products/docker-desktop/) y deja el motor iniciado.
3. Instala [Git for Windows](https://git-scm.com/download/win) o ejecuta `winget install Git.Git` desde PowerShell.
4. Reinicia PowerShell y verifica:

```powershell
git --version
docker --version
docker compose version
```

### 2. Ejecutar la demo

```powershell
git clone https://github.com/Pashofm/FashionVision-AI.git
Set-Location FashionVision-AI
Copy-Item .env.example .env
docker compose up -d --build --wait
docker compose cp backend/database/seed.sql db:/tmp/seed.sql
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/seed.sql'
```

Verifica los servicios y abre `http://localhost`:

```powershell
docker compose ps
Invoke-WebRequest http://localhost/health
```

### Problemas frecuentes

- Si Docker no responde, abre Docker Desktop y espera a que indique que el motor está activo.
- Si el puerto 80 está ocupado, cambia `FRONTEND_HOST_PORT=8080` en `.env` y abre `http://localhost:8080`.
- Para identificar un proceso que usa el puerto 80: `netstat -ano | findstr :80` y `taskkill /PID <PID> /F`.

## Windows con WSL2

Este es el método recomendado para desarrollo. Sigue la guía detallada de [WINDOWS_WSL2.md](WINDOWS_WSL2.md), que cubre la instalación de WSL2, Ubuntu, Docker Desktop e integración entre Windows y Linux.

Resumen del flujo una vez configurado WSL2:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
docker compose up -d --build --wait
make seed
```

Guarda el repositorio bajo `~/Projects` u otro directorio Linux, no en `C:\`, para evitar problemas de rendimiento con volúmenes y hot reload.

## macOS

Instala [Docker Desktop](https://www.docker.com/products/docker-desktop/) y Git, y sigue el [flujo de la demo](#flujo-de-la-demo) desde Terminal. Si no tienes `make`, usa el seed sin Make de [COMANDOS.md](COMANDOS.md#datos-iniciales-y-migraciones).

## pgAdmin opcional

Inicia pgAdmin cuando necesites administrar PostgreSQL:

```bash
docker compose --profile tools up -d pgadmin
```

Abre `http://localhost:5050` y registra el servidor con host `db`, puerto `5432` y credenciales de `.env`. Consulta [GUIAS_PGADMIN.md](GUIAS_PGADMIN.md).

## Reiniciar completamente la demo

Este flujo elimina los contenedores y volúmenes, incluidos los datos PostgreSQL y modelos descargados:

```bash
docker compose down -v --remove-orphans
docker compose up -d --build --wait
make seed
```

En Windows nativo, sustituye `make seed` por el comando de [COMANDOS.md](COMANDOS.md#datos-iniciales-y-migraciones).
