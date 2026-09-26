# Scripts y automatización

El flujo principal se ejecuta desde la raíz con el `Makefile`. Los scripts restantes son utilidades específicas y no sustituyen la guía de instalación.

## Makefile

```bash
make help
```

Targets principales:

| Comando | Uso |
|---|---|
| `make up-build` | Construir imágenes y arrancar servicios |
| `make up` | Arrancar servicios existentes |
| `make down` | Detener servicios |
| `make seed` | Cargar datos demo |
| `make migrate` | Aplicar migraciones manualmente |
| `make logs` | Ver logs |
| `make test-backend` | Ejecutar pruebas backend con una BD de pruebas separada |
| `make test-frontend` | Ejecutar pruebas frontend |
| `make clean` | Eliminar servicios y volúmenes |

## Scripts disponibles

| Archivo | Uso |
|---|---|
| `scripts/check-env.sh` | Revisar variables sensibles antes de operar |
| `scripts/export-openapi.py` | Exportar el esquema OpenAPI |
| `scripts/update.sh` | Actualizar o reconstruir servicios Docker |
| `scripts/common_versions.sh` | Funciones auxiliares heredadas para versiones locales |

Los scripts se ejecutan desde la raíz. Revisa el archivo antes de usarlo y no ejecutes `make clean` si necesitas conservar la base de datos.

## Flujo de un desarrollador

```bash
cp .env.example .env
docker compose up -d --build --wait
make seed
make logs-backend
make down
```

Para cambios de esquema, modifica los modelos, genera una migración desde el contenedor backend y revisa el archivo resultante antes de hacer commit:

```bash
make shell-backend
cd /app/backend
alembic revision --autogenerate -m "descripcion_del_cambio"
```
