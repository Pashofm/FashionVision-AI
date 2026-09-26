# Instalación

FashionVision AI se ejecuta con Docker. Python, Node.js y PostgreSQL no son necesarios en el sistema anfitrión para usar la demo.

## Requisitos

- Docker Engine 24+ en Linux, o Docker Desktop 4+ en Windows/macOS.
- Docker Compose v2 (`docker compose`).
- Git 2.40+.
- 8 GB de RAM recomendados.
- 10 GB de espacio libre como mínimo; 20 GB es más cómodo para modelos y cachés.

Verifica la instalación:

```bash
docker --version
```

En Windows se recomienda Docker Desktop con integración WSL2. Consulta [WINDOWS_WSL2.md](WINDOWS_WSL2.md).

## Instalación común

```bash
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
docker compose up -d --build --wait
```

En Windows PowerShell, sustituye la copia del entorno por:

```powershell
Copy-Item .env.example .env
docker compose up -d --build --wait
```

Comprueba que los servicios estén saludables:

```bash
docker compose ps
```

Carga los datos demo con `make seed` o consulta el equivalente en [COMANDOS.md](COMANDOS.md). Las migraciones se ejecutan automáticamente al arrancar el backend.

## Acceso

| Recurso | URL |
|---|---|
| Aplicación | `http://localhost` |
| Health | `http://localhost/health` |
| Swagger | `http://localhost/docs` |
| pgAdmin opcional | `http://localhost:5050` |

Para utilizar la aplicación consulta [USER_GUIDE.md](USER_GUIDE.md).

## Linux

Instala Docker desde el gestor de paquetes de tu distribución o Docker Engine. En Arch Linux, asegúrate de tener el daemon activo:

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Cierra y vuelve a iniciar sesión si agregaste tu usuario al grupo `docker`.

## Windows

Instala Docker Desktop, activa la integración con tu distribución WSL2 y ejecuta los comandos desde WSL o PowerShell. No necesitas instalar Python ni Node.js para la demo.

## macOS

Instala Docker Desktop y ejecuta los mismos comandos de la sección de instalación común desde Terminal.

## Reiniciar completamente la demo

Este flujo borra la base de datos y los volúmenes persistentes:

```bash
docker compose down -v --remove-orphans
docker compose up -d --build --wait
make seed
```
