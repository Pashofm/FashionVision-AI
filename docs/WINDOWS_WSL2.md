# Windows con WSL2

Esta guía instala FashionVision AI desde Ubuntu en WSL2 usando Docker Desktop. Es el método recomendado para desarrollar en Windows porque los volúmenes de Docker y el hot reload funcionan mejor dentro del filesystem Linux.

## Requisitos

- Windows 10 versión 2004 o posterior, o Windows 11.
- Virtualización habilitada en BIOS/UEFI.
- 8 GB de RAM y 20 GB libres recomendados.
- Permisos de administrador para instalar WSL2 y Docker Desktop.

## 1. Instalar WSL2 y Ubuntu

Abre PowerShell como administrador y ejecuta:

```powershell
wsl --install
```

Reinicia Windows cuando se solicite. Después abre Ubuntu desde el menú Inicio, crea el usuario Linux y verifica desde PowerShell:

```powershell
wsl --status
wsl -l -v
```

La distribución Ubuntu debe mostrar versión `2`. Si ya tenías WSL1, ejecuta `wsl --set-version Ubuntu 2` desde PowerShell como administrador.

## 2. Instalar Docker Desktop

1. Instala [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Durante la instalación, selecciona el backend WSL2 si se ofrece la opción.
3. Abre Docker Desktop y espera a que el motor quede iniciado.
4. En **Settings > Resources > WSL Integration**, activa la integración para Ubuntu.

Desde la terminal Ubuntu verifica que Docker está disponible sin `sudo`:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

Si Docker no responde, cierra Docker Desktop, ejecuta `wsl --shutdown` desde PowerShell y vuelve a iniciar Docker Desktop.

## 3. Instalar Git y clonar el proyecto

En Ubuntu:

```bash
sudo apt update
sudo apt install -y git make
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
```

No clones el proyecto en `/mnt/c` ni `C:\`. Los montajes desde el disco Windows reducen el rendimiento y pueden afectar el hot reload.

## 4. Configurar y ejecutar la demo

```bash
cp .env.example .env
docker compose up -d --build --wait
make seed
docker compose ps
```

Si no instalaste `make`, usa el seed sin Make de [COMANDOS.md](COMANDOS.md#datos-iniciales-y-migraciones).

Abre desde Windows o Ubuntu:

| Recurso | URL |
|---|---|
| Aplicación | `http://localhost` |
| Health | `http://localhost/health` |
| Swagger | `http://localhost/docs` |
| pgAdmin opcional | `http://localhost:5050` |

## PowerShell frente a WSL

Ejecuta los comandos Docker del proyecto desde Ubuntu. Si necesitas usar PowerShell, abre el repositorio mediante `wsl` o sigue la sección [Windows nativo](INSTALLATION.md#windows-nativo). No alternes ambos directorios para el mismo checkout.

## Problemas comunes

### Docker no responde en Ubuntu

1. Confirma que Docker Desktop está iniciado.
2. Confirma que la integración WSL está habilitada para Ubuntu.
3. Reinicia WSL y Docker Desktop:

```powershell
wsl --shutdown
```

### El puerto 80 está ocupado

Edita `.env`:

```text
FRONTEND_HOST_PORT=8080
```

Recrea los servicios y abre `http://localhost:8080`:

```bash
docker compose up -d --force-recreate nginx
```

### Los cambios no se reflejan

Confirma que el repositorio está bajo `~/Projects` y no bajo `/mnt/c`. Si cambias dependencias o configuración, reconstruye:

```bash
docker compose up -d --build --wait
```

### Ver logs

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```
