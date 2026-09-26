# Windows con WSL2

Windows puede ejecutar FashionVision AI mediante Docker Desktop y WSL2. Para la demo no necesitas instalar Python, Node.js ni PostgreSQL dentro de WSL.

## Requisitos

- Windows 10/11 con WSL2 habilitado.
- Ubuntu en WSL2.
- Docker Desktop con integración WSL2 activa.
- Git instalado en WSL2 o en Windows.
- 10 GB libres y 8 GB de RAM recomendados.

Verifica desde WSL:

```bash
wsl --status
docker --version
docker compose version
git --version
```

## Instalación

```bash
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
docker compose up -d --build --wait
```

Si ejecutas los comandos desde PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up -d --build --wait
```

Carga los datos demo con `make seed` desde WSL o ejecuta el comando equivalente descrito en [COMANDOS.md](COMANDOS.md).

## Acceso

| Recurso | URL |
|---|---|
| Aplicación | `http://localhost` |
| Health | `http://localhost/health` |
| Swagger | `http://localhost/docs` |
| pgAdmin opcional | `http://localhost:5050` |

Los puertos de backend y PostgreSQL son internos de Docker. No intentes conectarte desde Windows a `localhost:8000` o `localhost:5432` salvo que hayas creado un override propio que los publique.

## Problemas comunes

### Docker no responde

Abre Docker Desktop y confirma que la integración con Ubuntu está activa en **Settings > Resources > WSL Integration**.

### El puerto 80 está ocupado

Define otro puerto público en `.env`:

```text
FRONTEND_HOST_PORT=8080
```

Después abre `http://localhost:8080`.

### Cambios no se reflejan

En desarrollo, reconstruye las imágenes si cambias dependencias o configuración:

```bash
docker compose up -d --build --wait
```

### Logs

```bash
docker compose ps
docker compose logs -f backend
```
