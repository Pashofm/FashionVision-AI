# Entorno Docker

Esta página resume la topología Docker del proyecto. Para instalar la demo consulta [INSTALLATION.md](INSTALLATION.md); para comandos consulta [COMANDOS.md](COMANDOS.md).

## Servicios

| Servicio | Función | Acceso desde el host |
|---|---|---|
| `db` | PostgreSQL 16 + pgvector | Interno, `db:5432` |
| `backend` | FastAPI + YOLO + CLIP | Interno, `backend:8000` |
| `frontend` | Vite en desarrollo o SPA en producción | Interno |
| `nginx` | Punto de entrada y proxy | `http://localhost` |
| `pgadmin` | Administración opcional de BD | `http://localhost:5050` |

El servicio `pgadmin` pertenece al perfil `tools`. PostgreSQL y backend no publican sus puertos en el host por defecto.

## Desarrollo

```bash
cp .env.example .env
docker compose up -d --build --wait
make seed
```

El Compose de desarrollo monta el código fuente y activa hot reload en backend y frontend. Las migraciones se ejecutan automáticamente en el arranque del backend.

URLs:

- Aplicación: `http://localhost`.
- API: `http://localhost/api`.
- Health: `http://localhost/health`.
- Swagger: `http://localhost/docs`.

## Producción simulada

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

El override usa imágenes de producción, Gunicorn, frontend compilado y `restart: always`. Sigue siendo responsabilidad del operador añadir TLS, dominio, secretos y backups antes de exponerlo públicamente. Consulta [DEPLOYMENT.md](DEPLOYMENT.md).

## Volúmenes

| Volumen | Contenido |
|---|---|
| `postgres_data` | Datos de PostgreSQL |
| `torch_cache` | Modelos descargados y caché PyTorch |
| `media_files` | Archivos subidos |
| `pgadmin_data` | Configuración de pgAdmin |

`docker compose down` conserva los volúmenes. `make clean` los elimina.

## Migraciones

El backend ejecuta `alembic upgrade head` al iniciar. Para operar manualmente:

```bash
make migrate
make migrate-status
make migrate-history
make migrate-down
```

Genera nuevas migraciones desde el contenedor:

```bash
make shell-backend
cd /app/backend
alembic revision --autogenerate -m "descripcion_del_cambio"
```

Revisa siempre la migración generada antes de hacer commit.

## pgAdmin

```bash
docker compose --profile tools up -d pgadmin
```

Registra PostgreSQL con host `db`, puerto `5432`, y las credenciales de `.env`. No uses `localhost` como host dentro de pgAdmin. Consulta [GUIAS_PGADMIN.md](GUIAS_PGADMIN.md).

## Diagnóstico

```bash
curl http://localhost/health
```

Si el puerto 80 está ocupado, define `FRONTEND_HOST_PORT` en `.env` y usa ese puerto para acceder a la aplicación.
