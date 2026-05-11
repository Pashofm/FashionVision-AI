# Scripts - FashionVision-AI

Documentación de todos los scripts de automatización disponibles.

## Tabla de Contenidos

1. [Scripts Disponibles](#scripts-disponibles)
2. [Uso Rápido](#uso-rápido)
3. [Descripción Detallada](#descripción-detallada)
4. [Flujo de Trabajo](#flujo-de-trabajo)

---

## Scripts Disponibles

| Script | Uso | Descripción |
|--------|-----|-------------|
| `setup.sh` | `./scripts/setup.sh` | Setup inicial para clonación fresca |
| `dev-start.sh` | `./scripts/dev-start.sh` | Inicia modo desarrollo (DB + dependencias) |
| `dev-stop.sh` | `./scripts/dev-stop.sh` | Detiene servicios Docker |
| `deploy-local.sh` | `./scripts/deploy-local.sh` | Inicia backend + frontend con 1 comando |
| `docker-start.sh` | `./scripts/docker-start.sh` | Todo en Docker (testing/demo) |
| `update.sh` | `./scripts/update.sh [action]` | Actualizar servicios sin rebuild |
| `migrate.sh` | `./scripts/migrate.sh [action]` | Control de migraciones |
| `db-reset.sh` | `./scripts/db-reset.sh` | Reset de base de datos |
| `check-env.sh` | `./scripts/check-env.sh` | Verificación de seguridad |

---

## Uso Rápido

### Nuevo Desarrollador (clonación fresca)

```bash
# 1. Clonar repositorio
git clone <repo-url> FashionVision-AI
cd FashionVision-AI

# 2. Setup inicial (instala todo)
./scripts/setup.sh

# 3. Editar .env con credenciales
nano .env

# 4. Volver a ejecutar setup si es necesario
./scripts/setup.sh
```

### Desarrollo Diario

```bash
# Iniciar servicios (2 terminales)
./scripts/deploy-local.sh  # Terminal 1: todo en background

# O manualmente:
./scripts/dev-start.sh      # Terminal 1: prepara DB + dependencias
# Terminal 2: cd backend && source venv/bin/activate && export PYTHONPATH=$PWD && uvicorn ...
# Terminal 3: cd frontend && npm run dev

# Detener
./scripts/dev-stop.sh
```

### Testing/Demo (Docker completo)

```bash
# Iniciar todo en Docker
./scripts/docker-start.sh

# Detener
docker compose down
```

---

## Descripción Detallada

### setup.sh

Setup inicial para máquina nueva o clonación fresca.

```bash
./scripts/setup.sh
```

**Qué hace:**
1. Verifica prerrequisitos (docker, python, node)
2. Crea `.env` desde `.env.template` si no existe
3. Inicia base de datos en Docker
4. Instala dependencias Python (venv + requirements)
5. Instala dependencias frontend (npm)
6. Ejecuta migraciones de Alembic

**Primera vez:** Ejecutar, editar `.env`, ejecutar de nuevo.

---

### dev-start.sh

Prepara el entorno de desarrollo (no inicia los servers).

```bash
./scripts/dev-start.sh
```

**Qué hace:**
1. Verifica/crea `.env`
2. Inicia DB y pgAdmin en Docker
3. Crea venv de Python si no existe
4. Instala dependencias Python
5. Ejecuta migraciones Alembic
6. Instala dependencias frontend si no existen

**No inicia:** Backend ni Frontend (manual o con deploy-local.sh).

---

### dev-stop.sh

Detiene servicios Docker del entorno de desarrollo.

```bash
./scripts/dev-stop.sh
```

**Qué hace:**
- `docker compose stop db pgadmin`
- Preserva datos en volúmenes

---

### deploy-local.sh

Inicia backend y frontend con un solo comando.

```bash
./scripts/deploy-local.sh
```

**Qué hace:**
1. Verifica que DB esté corriendo
2. Limpia puertos 8000 y 5173 si hay procesos
3. Inicia backend en background (puerto 8000)
4. Inicia frontend en background (puerto 5173)
5. Muestra logs en `/tmp/fashionvision-*.log`

**Precaución:** Mata procesos existentes en esos puertos.

---

### docker-start.sh

Inicia todo en contenedores Docker (modo testing/demo/producción).

```bash
./scripts/docker-start.sh
```

**Qué hace:**
1. Verifica `.env`
2. `docker compose up -d --build`
3. Espera a que servicios estén ready
4. Muestra estado de servicios

**Uso:** Para testing, demos, o despliegue producción.

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

---

### migrate.sh

Control de migraciones de Alembic.

```bash
./scripts/migrate.sh [action]
```

**Acciones disponibles:**

| Acción | Descripción |
|--------|-------------|
| (ninguna) | Ejecuta `alembic upgrade head` |
| `status` | Muestra estado actual e historial |
| `down` | Hace rollback de una migración |
| `reset` | Reset completo (requiere confirmación) |

**Ejemplos:**
```bash
./scripts/migrate.sh        # Aplicar migraciones pendientes
./scripts/migrate.sh status  # Ver estado
./scripts/migrate.sh down    # Rollback una migración
./scripts/migrate.sh reset   # Reset completo
```

---

### db-reset.sh

Reset de base de datos (¡CUIDADO! Elimina datos).

```bash
./scripts/db-reset.sh
```

**Qué hace:**
1. Pide confirmación
2. `docker compose down`
3. Elimina volumen de datos
4. Inicia DB nuevamente
5. Espera a que esté ready

**Útil para:** Reset de desarrollo limpio.

---

### check-env.sh

Verificación de seguridad.

```bash
./scripts/check-env.sh
```

**Qué verifica:**
- Que `.env` no esté tracked en git
- Que `backend/.env` no esté tracked
- Que `.gitignore` tenga las reglas correctas
- Que `.env.template` exista

**Útil para:** Detectar problemas de seguridad antes de commit.

---

## Flujo de Trabajo

### Flujo: Nuevo Desarrollador

```
1. git clone <repo>
2. ./scripts/setup.sh
3. Editar .env
4. ./scripts/setup.sh (otra vez)
5. ./scripts/deploy-local.sh
6. Abrir http://localhost:5173
```

### Flujo: Desarrollo Diario

```
1. ./scripts/dev-start.sh      # Preparar entorno
2. Terminal 1: backend manually  # o ./scripts/deploy-local.sh
3. Terminal 2: frontend
4. coding...
5. ./scripts/dev-stop.sh       # Al terminar
```

### Flujo: Testing/Demo

```
1. ./scripts/docker-start.sh
2. Abrir http://localhost
3. Testing...
4. docker compose down          # Al terminar
```

### Flujo: Update Servicios

```
1. git pull
2. ./scripts/update.sh backend-full   # Si hay cambios en backend
3. ./scripts/update.sh frontend-full  # Si hay cambios en frontend
# O simplemente:
4. ./scripts/docker-start.sh          # Rebuild completo
```

---

## Notas Importantes

- Todos los scripts asumen que se ejecutan desde la raíz del proyecto
- Los scripts Docker requieren que `.env` exista (copiado de `.env.template`)
- `deploy-local.sh` requiere que `backend/venv` esté creado
- Para producción, usar `./scripts/docker-start.sh` o la guía en `docs/DEPLOYMENT.md`