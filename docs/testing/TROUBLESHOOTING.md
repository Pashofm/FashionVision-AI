# Problemas de pruebas

## No se puede conectar a PostgreSQL

Comprueba que la base aislada de pruebas está ejecutándose y que `TEST_DATABASE_URL` usa el host y puerto correctos:

```bash
echo "$TEST_DATABASE_URL"
pg_isready -h localhost -p 5433
```

La base demo de Compose usa el servicio interno `db:5432` y no debe utilizarse para pruebas destructivas.

## No existe la base de pruebas

El script heredado puede crearla si tienes una PostgreSQL de pruebas accesible:

```bash
cd backend
./scripts/setup_test_db.sh
```

Puedes cambiar host y puerto antes de ejecutarlo:

```bash
DB_HOST=localhost DB_PORT=5433 ./scripts/setup_test_db.sh
```

## `No module named backend`

Ejecuta pytest desde la raíz con el path correcto o desde `backend/`:

```bash
export PYTHONPATH="$PWD/backend"
cd backend
pytest tests/ -v
```

## Fallos de imports en `tests.factories`

Comprueba que `backend/tests/__init__.py` existe y ejecuta pytest desde el directorio `backend`.

## Datos contaminados entre pruebas

Usa una base exclusiva para tests y las fixtures de `tests/conftest.py`. No ejecutes la suite contra la base demo.

## Pruebas frontend fallan al resolver componentes

Comprueba que las pruebas apuntan a componentes existentes y que las dependencias están instaladas:

```bash
cd frontend
npm ci
npm run test:run
```

Si el componente o contrato cambió, actualiza la prueba en el mismo Pull Request que introdujo el cambio.
