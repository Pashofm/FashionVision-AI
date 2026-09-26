# Despliegue

Esta guía describe el alcance real del override de producción incluido en el repositorio. No es una guía de hosting público completa: TLS, dominio, firewall, backups externos y observabilidad deben configurarse en la infraestructura donde se ejecute Docker.

## Qué incluye el proyecto

El comando de producción utiliza:

- PostgreSQL 16 con pgvector.
- Backend FastAPI ejecutado con Gunicorn y cuatro workers Uvicorn.
- Frontend compilado como SPA estática.
- Nginx como punto de entrada HTTP.
- Volúmenes persistentes para PostgreSQL, media y caché de modelos.
- Migraciones Alembic automáticas al iniciar el backend.
- pgAdmin desactivado porque el servicio usa el perfil `tools` del Compose de desarrollo.

El Compose actual expone HTTP mediante `FRONTEND_HOST_PORT` y no configura HTTPS ni certificados. No publiques este servicio directamente en Internet sin colocar TLS y controles de acceso delante de Nginx.

## Requisitos

- Docker Engine 24+.
- Docker Compose v2.
- 8 GB de RAM recomendados por PyTorch/YOLO/CLIP.
- 20 GB libres como mínimo para imágenes, dependencias, cachés y datos.
- Dominio y proxy TLS externo si se requiere acceso público.

## Configuración segura

Crea `.env` a partir de `.env.example` y reemplaza como mínimo:

```bash
openssl rand -base64 32
```

Configura el resultado en `SECRET_KEY` y cambia:

- `POSTGRES_PASSWORD`.
- `PGADMIN_PASSWORD` si se usa pgAdmin en desarrollo.
- Contraseñas de las cuentas demo o elimina esas cuentas del seed.
- `ALLOWED_ORIGINS` con los dominios reales.

No guardes `.env` en Git ni muestres sus valores en logs, tickets o capturas.

## Despliegue

```bash
git clone --branch develop https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI
cp .env.example .env
# Editar .env con secretos, dominios reales y ENVIRONMENT=production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Comprueba el estado:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
curl http://localhost/health
```

El seed contiene cuentas y productos de demostración. En producción no ejecutes `make seed` sin revisar primero el contenido de `backend/database/seed.sql`.

## Operación diaria

```bash
# Logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Estado
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Detener sin borrar datos
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Actualizar imágenes después de cambiar el código
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Backups

La base de datos está en el volumen `postgres_data`. Un volumen Docker no sustituye un backup externo. Exporta periódicamente desde un equipo con acceso al contenedor:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```

Para restaurar en una base vacía:

```bash
cat backup.sql | docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Limitaciones conocidas

- Nginx solo está configurado para HTTP en el repositorio.
- El terminal POS es simulado y no procesa pagos reales.
- No se incluye rotación de logs ni monitorización externa.
- No se incluye una política automática de backup.
- La GPU no está configurada en Compose; la inferencia usa los recursos disponibles dentro del contenedor.

Antes de considerar el sistema listo para producción, añade TLS, gestión de secretos, backups probados, monitorización, política de actualización y un proveedor de pagos certificado.
