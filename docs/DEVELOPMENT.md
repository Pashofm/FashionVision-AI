# FashionVision-AI - Guía de Desarrollo en Equipo

Documentación para configurar el entorno de desarrollo en equipo con Docker + desarrollo local mixto.

## Índice

- [Arquitectura](#arquitectura)
- [Modos de Uso](#modos-de-uso)
- [Primeros Pasos](#primeros-pasos)
- [Comandos Rápidos](#comandos-rápidos)
- [Scripts de Ayuda](#scripts-de-ayuda)
- [Solución de Problemas](#solución-de-problemas)

---

## Arquitectura

### Entorno de Desarrollo Activo

```
┌─────────────────────────────────────────────────────────────┐
│                    Tu Equipo de Desarrollo                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│   │   Frontend   │   │   Backend    │   │     DB      │   │
│   │    Local     │   │    Local     │   │   Docker    │   │
│   │   :5173      │   │   :8000      │   │   :5432     │   │
│   │  (Vite)      │   │  (HotReload) │   │             │   │
│   └──────────────┘   └──────────────┘   └──────────────┘   │
│         ↑                  ↑                   ↑           │
│         │                  │                   │           │
│         └──────────────────┴───────────────────┘           │
│                              ↓                              │
│                    Desarrollo Activo                        │
└─────────────────────────────────────────────────────────────┘
```

### Entorno de Testing/Demo (Docker Completo)

```bash
docker compose up -d   # Todo en contenedores
```

---

## Modos de Uso

### Modo A: Desarrollo (hot-reload activo)

**Para desarrollo activo cuando necesitas iterar rápido.**

```bash
# Terminal 1 - Base de datos (solo una vez al inicio)
docker compose up -d db

# Terminal 2 - Backend con hot-reload
source backend/venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Terminal 3 - Frontend con hot-reload
cd frontend && npm run dev
```

**Acceso:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Modo B: Testing / Demo (Docker completo)

**Para testing, demos a clientes, o cuando no necesitas hot-reload.**

```bash
# Todo en Docker (single command)
docker compose up -d

# Ver servicios
docker compose ps

# Ver logs
docker compose logs -f
```

**Acceso:**
- App completa: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Primeros Pasos

### 1. Requisitos Previos

| Software | Versión | Notas |
|----------|---------|-------|
| Docker Desktop | 4.0+ | Para Windows/WSL |
| WSL2 | Latest | Solo Windows |
| Git | Any | Para clonar |
| Python | 3.12+ | Para venv local |
| Node.js | 20+ | Para frontend local |

### 2. Instalación (Nuevos miembros del equipo)

```bash
# 1. Clonar repositorio
git clone <repo-url> FashionVision-AI
cd FashionVision-AI

# 2. Copiar archivo de variables
cp .env.template .env

# 3. Crear entorno virtual de Python
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 4. Instalar dependencias Python
pip install -r requirements.txt

# 5. Crear venv de frontend
cd ../frontend
npm install

# 6. Levantar base de datos Docker
cd ..
docker compose up -d db

# 7. Verificar que DB está lista
docker compose ps db
# Debería mostrar "healthy"
```

### 3. Iniciar Desarrollo

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Terminal 2 - Frontend (nueva terminal)
cd frontend
npm run dev
```

---

## Comandos Rápidos

### Base de datos (Docker)

```bash
# Iniciar solo DB
docker compose up -d db

# Ver estado
docker compose ps db

# Ver logs
docker compose logs db

# Conectar directamente
docker exec -it fashionvision_db psql -U fashionvision_ai_user -d fashionvision_ai

# Reiniciar DB
docker compose restart db

# Reset completo (¡cuidado! Elimina datos)
docker compose down -v
docker compose up -d db
```

### Backend (local)

```bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PWD

# Iniciar con hot-reload
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

# Solo verificar que funciona
python -c "from backend.app.main import app; print('OK')"
```

### Frontend (local)

```bash
cd frontend

# Iniciar con hot-reload
npm run dev

# Build para producción
npm run build

# Solo lint
npm run lint
```

### Docker completo

```bash
# Iniciar todo
docker compose up -d

# Detener todo
docker compose down

# Rebuild completo
docker compose build --no-cache
docker compose up -d

# Ver servicios activos
docker compose ps

# Ver todos los logs
docker compose logs -f
```

---

## Scripts de Ayuda

### Scripts disponibles en `/scripts/`

| Script | Uso | Descripción |
|--------|-----|-------------|
| `dev-start.sh` | `./scripts/dev-start.sh` | Inicia modo desarrollo (DB + backend + frontend) |
| `dev-stop.sh` | `./scripts/dev-stop.sh` | Detiene todos los servicios |
| `docker-start.sh` | `./scripts/docker-start.sh` | Inicia todo en Docker (modo testing) |
| `db-reset.sh` | `./scripts/db-reset.sh` | Reinicia la base de datos |

### Uso de scripts

```bash
# Modo desarrollo completo
./scripts/dev-start.sh

# Solo Docker (testing)
./scripts/docker-start.sh

# Detener todo
./scripts/dev-stop.sh

# Reset de base de datos
./scripts/db-reset.sh
```

---

## Solución de Problemas

### Error: `no existe el rol «fashionvision_ai_user»`

**Causa:** La base de datos no está corriendo o no se creó correctamente.

**Solución:**
```bash
# Ver estado de la DB
docker compose ps db

# Si no está corriendo
docker compose up -d db

# Ver logs
docker compose logs db

# Si el problema persiste, resetear
docker compose down -v
docker compose up -d db

# Esperar a que esté healthy
docker compose ps db
```

### Error: `connection refused` en PostgreSQL

**Causa:** PostgreSQL no está escuchando en el puerto esperado.

**Solución:**
```bash
# Verificar que postgres está corriendo
docker compose ps db

# Ver logs
docker compose logs db

# Ver puertos en uso
netstat -an | grep 5432  # Linux/Mac
netstat -ano | findstr 5432  # Windows
```

### Error: módulo no encontrado `backend.app`

**Causa:** Falta `PYTHONPATH=$PWD`

**Solución:**
```bash
export PYTHONPATH=$PWD
# Ejecutar desde la raíz del proyecto
```

### Error: puerto en uso

**Causa:** Otro proceso está usando el puerto.

**Solución:**
```bash
# Encontrar proceso en puerto 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr 8000  # Windows

# Matar proceso si es necesario
kill -9 <PID>
```

### Verificar que todo funciona

```bash
# 1. DB
docker compose ps db
docker exec -it fashionvision_db psql -U fashionvision_ai_user -d fashionvision_ai -c "SELECT 1"

# 2. Backend
curl http://localhost:8000/health

# 3. Frontend
curl http://localhost:5173 | head -20
```

---

## Variables de Entorno

El archivo `.env` en la raíz del proyecto configura todo el sistema.

**Variables principales:**

```env
# Database
POSTGRES_DB=fashionvision_ai
POSTGRES_USER=fashionvision_ai_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST_PORT=5432

# Backend
BACKEND_HOST_PORT=8000

# Frontend (para desarrollo local)
FRONTEND_HOST_PORT=5173
```

---

## Tips para el Equipo

1. **Siempre ejecutar desde la raíz del proyecto** al usar `export PYTHONPATH=$PWD`

2. **La DB en Docker debe estar corriendo** antes de iniciar el backend local

3. **Para nuevos miembros**: Seguir sección [Primeros Pasos](#primeros-pasos)

4. **Para testing/demo**: Usar `docker compose up -d` (Modo B)

5. **Si algo falla**:
   - Verificar `docker compose ps` que todos los servicios están corriendo
   - Ver logs con `docker compose logs <service>`
   - Resetear con `docker compose down -v && docker compose up -d`