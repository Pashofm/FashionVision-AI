# Comandos

Ejecuta los comandos desde la raíz del repositorio. El `Makefile` raíz es la interfaz recomendada para el desarrollo local.

## Inicio y parada

```bash
make up-build  # Construir imágenes y levantar la demo
make up        # Levantar imágenes existentes
make down      # Detener contenedores sin borrar volúmenes
make clean     # Detener y borrar contenedores, volúmenes huérfanos
```

Sin `make`, usa los equivalentes:

```bash
docker compose up -d --build --wait  # Construir y esperar la demo
docker compose up -d          # Levantar imágenes existentes
docker compose down           # Detener contenedores sin borrar volúmenes
docker compose down -v --remove-orphans  # Borrar contenedores y volúmenes
```

## Datos iniciales y migraciones

El backend ejecuta `alembic upgrade head` durante su arranque. Estos comandos sirven para operar manualmente:

```bash
make migrate         # Aplicar migraciones pendientes
make migrate-status  # Ver la revisión actual
make migrate-history # Ver el historial
make migrate-down    # Revertir la última revisión
make seed            # Insertar productos y usuarios demo
```

`make seed` es idempotente y debe ejecutarse después de que el backend y PostgreSQL estén saludables.

Sin `make`, usa este equivalente compatible con Bash y PowerShell:

```bash
docker compose cp backend/database/seed.sql db:/tmp/seed.sql
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/seed.sql'
```

## Estado, logs y shells

```bash
make logs
make logs-backend
make logs-db
make logs-frontend
make logs-nginx
make shell-backend
make shell-db
```

Accesos públicos:

| Recurso | URL |
|---|---|
| Aplicación | `http://localhost` |
| Health | `http://localhost/health` |
| Swagger | `http://localhost/docs` |
| API | `http://localhost/api` |
| pgAdmin opcional | `http://localhost:5050` |

El backend y PostgreSQL no se publican directamente en el host. Usa Nginx para la API, `make shell-db` o pgAdmin para la base de datos.

## pgAdmin

```bash
docker compose --profile tools up -d pgadmin
```

Dentro de pgAdmin usa `db:5432` como servidor. Consulta [GUIAS_PGADMIN.md](GUIAS_PGADMIN.md).

## Pruebas

```bash
make test-backend
make test-frontend
```

`make test-backend` requiere una base de datos de pruebas separada. Consulta [testing/TESTING_GUIDE.md](testing/TESTING_GUIDE.md) antes de ejecutarlo; `make test-frontend` no requiere PostgreSQL.

La guía de pruebas explica requisitos y limitaciones actuales: [testing/TESTING_GUIDE.md](testing/TESTING_GUIDE.md).

## Producción

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Configura `ENVIRONMENT=production` y secretos reales en `.env` antes de ejecutar este comando.
Consulta [DEPLOYMENT.md](DEPLOYMENT.md) antes de exponer el sistema fuera de la máquina local.

## Diagnóstico rápido

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 db
curl http://localhost/health
```

Si el puerto 80 está ocupado, configura `FRONTEND_HOST_PORT` en `.env`. La base de datos no publica `5432` por defecto y no debería entrar en conflicto con una instalación local de PostgreSQL.
