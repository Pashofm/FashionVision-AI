# Quickstart - FashionVision-AI

Guía rápida para poner en marcha el proyecto. Todo corre en Docker — no necesitas instalar Python ni Node.js en tu máquina.

---

## 4 Comandos para Empezar

```bash
# 1. Clonar el repositorio
git clone https://github.com/Pashofm/FashionVision-AI.git
cd FashionVision-AI

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Construir y esperar los 4 servicios (DB + Backend + Frontend + Nginx)
docker compose up -d --build --wait

# 4. Cargar datos iniciales de prueba
make seed
```

En Windows puedes ejecutar estos comandos desde WSL2 o Git Bash con `make` instalado. Si no tienes `make`, usa los comandos equivalentes de [docs/COMANDOS.md](./docs/COMANDOS.md).

Las migraciones se aplican automáticamente durante el arranque del backend. El sistema ya está corriendo cuando los servicios estén saludables. Abre http://localhost en tu navegador.

---

## Requisitos

| Software | Versión | Verificar |
|----------|---------|-----------|
| Docker | 24.0+ | `docker --version` |
| Docker Compose | v2 (plugin) | `docker compose version` |
| Git | 2.40+ | `git --version` |
| Espacio en disco | 10 GB libres | Dependencias e imágenes Docker |

---

## URLs de Acceso

| Servicio | URL | Notas |
|----------|-----|-------|
| App | http://localhost | Vía nginx (puerto 80) |
| Backend API | http://localhost/api | FastAPI vía nginx |
| API Docs | http://localhost/docs | Swagger UI vía nginx |
| pgAdmin | http://localhost:5050 | Requiere `docker compose --profile tools up -d pgadmin` |

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
make help            # Ver todos los comandos disponibles
make logs            # Ver logs de todos los servicios
make logs-backend    # Solo logs del backend
make down            # Detener todos los servicios
make clean           # Eliminar contenedores y volúmenes
make shell-backend   # Abrir shell en el contenedor backend
make shell-db        # Abrir psql en la base de datos
make test-backend    # Requiere una BD de pruebas separada; ver testing/TESTING_GUIDE.md
make test-frontend   # Correr tests del frontend
```

---

## Solución de Problemas Comunes

### "Port already in use"

```bash
# Linux/Mac
lsof -i :80
kill -9 <PID>

# Windows
netstat -ano | findstr :80
taskkill /PID <PID> /F
```

### "Database connection refused"

```bash
docker compose ps db               # Verificar que db está corriendo
make logs-db                       # Ver logs de PostgreSQL
docker compose restart db          # Reiniciar
```

### "Cannot connect to the Docker daemon"

```bash
sudo systemctl start docker        # Linux
# Windows/Mac: abrir Docker Desktop
```

### La detección descarga dependencias en el primer uso

La primera detección puede tardar mientras PyTorch prepara su caché. Espera a que finalice y revisa `make logs-backend` si el proceso no concluye.

---

## Próximos Pasos

1. Revisar [README.md](./README.md) para la arquitectura completa
2. Revisar [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) para flujo de trabajo
3. Revisar [docs/DOCKER_ENVIRONMENT.md](./docs/DOCKER_ENVIRONMENT.md) para migraciones
4. Explorar la API en http://localhost/docs

Para aprender a operar el sistema por rol, consulta [docs/USER_GUIDE.md](./docs/USER_GUIDE.md).
