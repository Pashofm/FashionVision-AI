# Pruebas

Esta guía describe cómo ejecutar las pruebas existentes y cómo interpretar sus resultados. No confundas la base de datos de demo con una base de datos de pruebas.

## Pruebas disponibles

- Backend: pytest, pruebas unitarias, API y flujos de cliente/cajero.
- Frontend: Vitest y Testing Library.
- Build frontend: compilación Vite para comprobar que la SPA se genera correctamente.
- Smoke test Docker: health, Swagger, login y seed.

## Validación rápida de la demo

```bash
docker compose ps
curl http://localhost/health
curl --fail http://localhost/docs
make seed
```

La validación manual confirma que el entorno funciona, pero no sustituye las pruebas automatizadas.

## Ejecutar pruebas

```bash
make test-frontend
```

`make test-backend` ejecuta pytest dentro del contenedor, pero el Compose de demo no crea ni publica la base de datos aislada que necesitan las pruebas backend. No lo ejecutes contra la base de datos demo.

Con Python, las dependencias del backend y una PostgreSQL de pruebas accesible desde el host:

```bash
cd backend
./scripts/setup_test_db.sh
./scripts/run_tests.sh --coverage
```

El script usa por defecto `localhost:5433`. Si la base de pruebas usa otro host o puerto, define `DB_HOST` y `DB_PORT` antes de ejecutar ambos scripts.

Para compilar el frontend:

```bash
docker compose exec frontend npm run build
```

También puedes ejecutar frontend fuera de Docker si ya instalaste sus dependencias:

```bash
cd frontend
npm run lint
npm run test:run
npm run build
```

## Base de datos de pruebas

Los scripts de `backend/scripts/` esperan una PostgreSQL de pruebas en `localhost:5433` por defecto. El Compose principal no publica ese puerto, por lo que esos scripts no funcionan automáticamente después de `make up-build`.

Antes de ejecutar la suite backend completa, prepara una base aislada y define:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://usuario:password@localhost:5433/fashionvision_ai_test"
export SKIP_DB_TESTS=false
export PYTHONPATH="$PWD/backend"
```

No apuntes `TEST_DATABASE_URL` a la base de datos demo.

## Ejecutar una prueba concreta

Desde `backend/`:

```bash
pytest tests/modules/sessions/test_session_unit.py -v
pytest -k "session" -v
```

## Estado conocido

La suite no debe considerarse completamente verde sin una base de datos de pruebas configurada. Además, algunas pruebas frontend pueden requerir actualización cuando cambian componentes o contratos de servicios. Reporta los fallos reproducibles con el sistema operativo, comando y salida relevante.
