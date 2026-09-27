# Scripts - FashionVision-AI

Documentación de todos los scripts de automatización disponibles y del Makefile principal.

## Makefile (Herramienta Principal)

El `Makefile` en la raíz del proyecto reemplaza la mayoría de los scripts anteriores. Todos los comandos se ejecutan desde la raíz del proyecto con `make <target>`.

| Comando `make` | Descripción | Reemplaza a |
|---|---|---|
| `make up` | Levanta los 4 servicios en modo desarrollo | `dev-start.sh` + `docker-start.sh` |
| `make up-build` | Reconstruye imágenes y levanta servicios | `dev-start.sh` + `docker-start.sh` |
| `make down` | Detiene y elimina contenedores | `dev-stop.sh` |
| `make logs` | Muestra logs de todos los servicios | — |
| `make logs-backend` | Logs del backend (FastAPI) | — |
| `make logs-db` | Logs de PostgreSQL | — |
| `make logs-frontend` | Logs del frontend (Vite dev server) | — |
| `make logs-nginx` | Logs de nginx | — |
| `make shell-backend` | Abre shell interactiva en el contenedor backend | — |
| `make shell-db` | Abre psql en el contenedor de base de datos | — |
| `make migrate` | Corre `alembic upgrade head` | `migrate.sh` |
| `make migrate-status` | Muestra el estado actual de las migraciones | `migrate.sh status` |
| `make migrate-history` | Muestra el historial completo de migraciones | `migrate.sh` |
| `make migrate-down` | Revierte la última migración (-1) | `migrate.sh down` |
| `make seed` | Carga datos iniciales de prueba | Seed de `setup.sh` |
| `make test-backend` | Corre los tests del backend | Tests de `deploy-local.sh` |
| `make test-frontend` | Corre los tests del frontend | Tests de `deploy-local.sh` |
| `make clean` | Elimina contenedores, volúmenes e imágenes huérfanas | `db-reset.sh` |
| `make help` | Muestra todos los comandos disponibles | — |

---

## Tabla de Contenidos

1. [Makefile (Herramienta Principal)](#makefile-herramienta-principal)
2. [Scripts Disponibles](#scripts-disponibles)
3. [Uso Rápido](#uso-rápido)
4. [Descripción Detallada](#descripción-detallada)
5. [Flujo de Trabajo](#flujo-de-trabajo)

---

## Scripts Disponibles

| Script | Uso | Descripción |
|--------|-----|-------------|
| `check-env.sh` | `./scripts/check-env.sh` | Verificación de seguridad |
| `common_versions.sh` | `source scripts/common_versions.sh` | Librería de funciones para gestión de versiones Python/Node |
| `export-openapi.py` | `python scripts/export-openapi.py` | Exporta especificación OpenAPI a JSON estático |
| `update.sh` | `./scripts/update.sh [action]` | Actualizar servicios sin rebuild |

---

## Uso Rápido

### Nuevo Desarrollador (clonación fresca)

```bash
# 1. Clonar repositorio
git clone git@github.com:Pashofm/FashionVision-AI.git
cd FashionVision-AI

# 2. Copiar y editar .env
cp .env.template .env
nano .env

# 3. Levantar todos los servicios
make up-build

# 4. Ejecutar migraciones y seed
make migrate
make seed
```

### Desarrollo Diario

```bash
# Iniciar servicios
make up

# Detener
make down
```

### Testing/Demo (Docker completo)

```bash
# Iniciar todo en Docker
make up-build

# Detener
make down
```

---

## Descripción Detallada

### check-env.sh

Verificación de seguridad.

```bash
./scripts/check-env.sh
```

**Qué verifica:**
- Que `.env` no esté tracked en git
- Que `backend/.env` no esté tracked
- Que `.gitignore` tenga las reglas correctas
- Que `.env.template` exista con placeholders

**Útil para:** Detectar problemas de seguridad antes de commit.

---

### common_versions.sh

Librería de funciones compartidas para gestión de versiones de Python y Node.js. No se ejecuta directamente, se importa con `source` desde otros scripts.

```bash
source scripts/common_versions.sh
```

**Funciones principales:**

| Función | Descripción |
|---------|-------------|
| `check_python_version` | Verifica que haya Python 3.10–3.12 disponible |
| `check_node_version` | Verifica que haya Node.js 18+ disponible |
| `setup_python_environment` | Instala Python vía pyenv si no hay versión compatible |
| `setup_node_environment` | Instala Node.js vía nvm si no hay versión compatible |
| `ensure_python_venv` | Crea/recrea el virtualenv de Python en `backend/venv` |
| `ensure_node_deps` | Instala dependencias de frontend (`npm install`) |
| `check_python_ctypes` | Verifica que el módulo `_ctypes` esté disponible |
| `get_python_binary` | Devuelve la ruta al binario de Python adecuado |
| `install_pyenv` | Instala pyenv si no está presente |
| `install_nvm` | Instala nvm si no está presente |

**Versiones requeridas:**
- Python: 3.10, 3.11 o 3.12 (máximo)
- Node.js: 18+

---

### export-openapi.py

Exporta la especificación OpenAPI de FashionVision AI a un archivo JSON estático.

```bash
python scripts/export-openapi.py
```

**Output:** `docs/api/openapi.json` — Especificación completa de la API en formato OpenAPI 3.1.

**Requisitos:** Dependencias del backend instaladas (`pip install -r backend/requirements.txt`).

---

### update.sh

Actualiza servicios sin rebuild completo.

```bash
./scripts/update.sh [action]
```

**Acciones disponibles:**

| Acción | Descripción |
|--------|-------------|
| `backend` | Reinicia backend Docker |
| `frontend` | Reinicia frontend Docker |
| `db` | Reinicia base de datos |
| `backend-full` | Rebuild + reinicia backend |
| `frontend-full` | Rebuild + reinicia frontend |
| `all` | Reinicia todos los servicios |
| `logs` | Muestra logs de todos los servicios |
| `status` | Muestra estado de servicios |
| `help` | Muestra ayuda |

**Ejemplos:**
```bash
./scripts/update.sh backend        # Solo reiniciar backend
./scripts/update.sh frontend-full  # Rebuild + reiniciar frontend
./scripts/update.sh logs           # Ver todos los logs
```

> **Nota:** `update.sh` asume que los servicios se levantaron con `make up` o `make up-build`. Para un rebuild completo desde cero, usar `make up-build`.

---

## Flujo de Trabajo

### Flujo: Nuevo Desarrollador

```
1. git clone git@github.com:Pashofm/FashionVision-AI.git
2. cp .env.template .env
3. nano .env
4. make up-build
5. make migrate
6. make seed
7. Abrir http://localhost
```

### Flujo: Desarrollo Diario

```
1. make up                    # Iniciar servicios
2. coding...
3. make logs-backend          # Ver logs si es necesario
4. make down                  # Al terminar
```

### Flujo: Testing/Demo

```
1. make up-build
2. Abrir http://localhost
3. Testing...
4. make down                  # Al terminar
```

### Flujo: Update Servicios

```
1. git pull
2. make up-build              # Rebuild completo
# O para cambios puntuales:
3. ./scripts/update.sh backend-full   # Si hay cambios en backend
4. ./scripts/update.sh frontend-full  # Si hay cambios en frontend
```

### Flujo: Migraciones

```
1. make migrate               # Aplicar migraciones pendientes
2. make migrate-status        # Ver estado actual
3. make migrate-history       # Ver historial
4. make migrate-down          # Rollback de última migración
```

---

## Notas Importantes

- El **Makefile** es la herramienta principal. Usar `make help` para ver todos los comandos.
- Todos los comandos `make` y scripts asumen que se ejecutan desde la raíz del proyecto.
- Los comandos Docker requieren que `.env` exista (copiado de `.env.template`).
- `update.sh` requiere que los servicios estén corriendo en Docker (levantados con `make up`).
- `export-openapi.py` requiere las dependencias de backend instaladas localmente.
- Para limpiar todo y empezar de cero: `make clean && make up-build`.
