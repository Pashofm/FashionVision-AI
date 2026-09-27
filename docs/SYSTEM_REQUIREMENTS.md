# Requisitos del Sistema

FashionVision AI se ejecuta completamente con Docker. No necesitas instalar Python, Node.js, PostgreSQL ni herramientas de compilacion en el host.

## Requisitos

| Componente | Requisito |
|---|---|
| Docker Engine o Docker Desktop | 24.0 o superior |
| Docker Compose | Plugin v2 (`docker compose`) |
| Git | 2.40 o superior |
| Memoria | 8 GB recomendados |
| Espacio libre | 10 GB recomendados |

Para Windows se recomienda Docker Desktop con WSL2. Consulta [WINDOWS_WSL2.md](./WINDOWS_WSL2.md) si necesitas configurarlo.

## Verificacion

```bash
docker --version
docker compose version
git --version
```

## Primer arranque

```bash
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
docker compose up -d --build --wait
make seed
```

El backend aplica las migraciones automaticamente durante su arranque. Abre `http://localhost` cuando los servicios esten saludables.

## Solucion de problemas

### Docker no responde

Inicia Docker Desktop en macOS o Windows. En Linux, comprueba el servicio:

```bash
sudo systemctl start docker
docker compose ps
```

### El puerto 80 esta ocupado

Edita `FRONTEND_HOST_PORT` en `.env` y vuelve a ejecutar `make up`.

### El inicio tarda varios minutos

La imagen del backend instala PyTorch y librerias de vision; la primera construccion puede tardar. Revisa el progreso con:

```bash
make logs-backend
```

### Reiniciar los datos demo

```bash
make clean
docker compose up -d --build --wait
make seed
```
