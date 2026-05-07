# Quickstart - FashionVision-AI

Guía rápida para nuevos desarrolladores que quieren poner en marcha el proyecto.

---

## Resumen: 5 Pasos para Empezar

```bash
# 1. Clonar el repositorio
git clone <repo-url> FashionVision-AI
cd FashionVision-AI

# 2. Configurar variables de entorno
cp .env.template .env

# 3. Iniciar base de datos y pgAdmin
docker compose up -d db pgadmin

# 4. Instalar dependencias
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install

# 5. Iniciar servicios
# Terminal 1: cd backend && source venv/bin/activate && export PYTHONPATH=$PWD && uvicorn backend.app.main:app --reload
# Terminal 2: cd frontend && npm run dev
```

---

## Requisitos

| Software | Versión | Verificar |
|----------|---------|-----------|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| Docker | 4.0+ | `docker --version` |

---

## URLs de Acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Frontend (dev) | http://localhost:5173 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| pgAdmin | http://localhost:5050 | admin@fashionvision.com / admin123 |

---

## Usuarios de Prueba

| Email | Rol | Password |
|-------|-----|----------|
| admin@tienda.com | admin | admin123 |
| cajero@tienda.com | cashier | admin123 |
| cliente@demo.com | client | admin123 |

---

## Comandos Más Comunes

```bash
# Iniciar todo (desarrollo)
./scripts/dev-start.sh

# Ver estado de servicios
docker compose ps

# Ver logs
docker compose logs -f

# Detener servicios
./scripts/dev-stop.sh

# Ver migraciones
source backend/venv/bin/activate
export PYTHONPATH=$PWD
cd backend
alembic current
```

---

## Solución de Problemas Comunes

### "Module not found: backend"

```bash
export PYTHONPATH=$PWD
# Ejecutar desde la raíz del proyecto
```

### "Database connection refused"

```bash
# Verificar que Docker está corriendo
docker compose ps

# Reiniciar base de datos
docker compose restart db
```

### "Port already in use"

```bash
# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Próximos Pasos

1. Revisar [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) para flujo de trabajo
2. Revisar [docs/DOCKER_ENVIRONMENT.md](./docs/DOCKER_ENVIRONMENT.md) para migraciones
3. Explorar la API en http://localhost:8000/docs

---

## Estructura de Archivos

```
FashionVision-AI/
├── backend/           # Python/FastAPI
│   ├── app/          # Código de la aplicación
│   ├── alembic/      # Migraciones de DB
│   └── models/       # Modelo YOLO
├── frontend/          # React/Vite
├── docker/           # Dockerfiles
├── scripts/           # Scripts de automatización
├── docs/             # Documentación
└── docker-compose.yml
```

---

## Help

Si algo no funciona:

1. Revisar esta guía de nuevo
2. Consultar [docs/COMANDOS.md](./docs/COMANDOS.md)
3. Consultar [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)