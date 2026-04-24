# Comandos Importantes - FashionVision-AI

Referencia rápida de comandos para desarrollar, ejecutar y mantener el proyecto.

---

## Tabla de Contenidos

1. [Docker - Base de Datos](#1-docker---base-de-datos)
2. [Backend - Python/FastAPI](#2-backend---pythonfastapi)
3. [Frontend - React/Vite](#3-frontend---reactvite)
4. [PostgreSQL - Terminal](#4-postgresql---terminal)
5. [Git - Control de Versiones](#5-git---control-de-versiones)
6. [Logs y Debugging](#6-logs-y-debugging)
7. [Base de Datos - Backup y Restore](#7-base-de-datos---backup-y-restore)
8. [Limpieza y Mantenimiento](#8-limpieza-y-mantenimiento)

---

## 1. Docker - Base de Datos

### Iniciar/Detener Servicios

```bash
# ============================================
# LEVANTAR BASE DE DATOS
# ============================================

# Linux y Windows (PowerShell/CMD)
cd backend
docker-compose up -d

# Ver que está corriendo
docker ps
```

```powershell
# ============================================
# EN WINDOWS (Git Bash)
# ============================================
# Usar PowerShell o CMD, NO Git Bash para docker-compose
```

```bash
# ============================================
# DETENER BASE DE DATOS
# ============================================

# Detener contenedor
docker-compose down

# Detener y eliminar datos (¡CUIDADO! Elimina todo)
docker-compose down -v
```

### Reiniciar Base de Datos

```bash
# Reiniciar contenedor
docker-compose restart

# Forzar reinicio
docker-compose stop
docker-compose start

# Ver estado
docker-compose ps
```

### Ver Logs de PostgreSQL

```bash
# Ver logs en tiempo real
docker-compose logs -f db

# Ver últimas 50 líneas
docker-compose logs --tail 50 db

# Ver logs de contenedor específico
docker logs fashionvision_db
```

### Eliminar y Recrear Contenedor

```bash
# Detener y eliminar
docker-compose down

# Eliminar volumen de datos (¡PÉRDIDA DE DATOS!)
docker volume rm backend_postgres_data

# Recrear desde cero
docker-compose up -d
```

---

## 2. Backend - Python/FastAPI

### Activar Entorno Virtual

```bash
# ============================================
# LINUX / MAC
# ============================================
cd backend
source venv/bin/activate

# Verificar (debe mostrar venv entre paréntesis)
which python
python --version
```

```powershell
# ============================================
# WINDOWS POWERSHELL
# ============================================
cd backend
.\venv\Scripts\activate

# Verificar
where python
python --version
```

```bash
# ============================================
# WINDOWS GIT BASH
# ============================================
cd backend
source venv/Scripts/activate

# Verificar
which python
python --version
```

### Iniciar Servidor Backend

```bash
# ============================================
# COMANDO COMPLETO
# ============================================

# Linux
cd /ruta/al/proyecto/FashionVision-AI
source backend/venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Windows PowerShell
cd C:\ruta\al\proyecto\FashionVision-AI
.\backend\venv\Scripts\activate
$env:PYTHONPATH = $PWD
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# ============================================
# COMANDO ABREVIADO (después de configurar)
# ============================================
cd backend
source venv/bin/activate
uvicorn app.main:app --reload  # Si PYTHONPATH está configurado
```

### Verificar que Backend Funciona

```bash
# Health check
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"healthy","database":"connected"}
```

### Detener Servidor Backend

```bash
# Opción 1: Ctrl+C en la terminal donde está corriendo

# Opción 2: Matar proceso
pkill -f uvicorn

# Opción 3: Matar por puerto
lsof -i :8000  # Linux
kill -9 <PID>
```

### Reinstall Dependencies

```bash
# Salir del venv
deactivate

# Eliminar venv
rm -rf backend/venv

# Recrear
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install 'bcrypt<5.0.0'  # Si hay problemas con bcrypt
```

---

## 3. Frontend - React/Vite

### Instalar Dependencias

```bash
cd frontend
npm install
```

### Iniciar Servidor de Desarrollo

```bash
# Linux y Windows
cd frontend
npm run dev
```

### Build para Producción

```bash
cd frontend
npm run build
```

### Ver Archivos Build

```bash
# El build se guarda en frontend/dist/
cd frontend/dist
ls -la
```

### Linting

```bash
# Verificar código
npm run lint

# Corregir errores automáticamente
npm run lint -- --fix
```

### Preview Producción

```bash
npm run preview
```

---

## 4. PostgreSQL - Terminal

### Conectar a Base de Datos

```bash
# ============================================
# DESDE DOCKER (cualquier SO)
# ============================================
docker exec -it fashionvision_db psql -U fashionvision_ai_user -d fashionvision_ai
```

```bash
# ============================================
# DESDE TERMINAL DIRECTA (Linux)
# ============================================
PGPASSWORD=fashionvision_ai_pass psql -h localhost -p 5433 -U fashionvision_ai_user -d fashionvision_ai
```

```powershell
# ============================================
# DESDE TERMINAL DIRECTA (Windows)
# ============================================
# Primero instalar psql o usar Git Bash
set PGPASSWORD=fashionvision_ai_pass
psql -h localhost -p 5433 -U fashionvision_ai_user -d fashionvision_ai
```

### Comandos dentro de psql

```sql
-- Ver todas las tablas
\dt

-- Ver estructura de una tabla
\d users
\d products

-- Ver todas las bases de datos
\l

-- Ver todas las secuencias
\ds

-- Ver todos los índices
\di

-- Ver funciones
\df

-- Ver vistas
\dv

-- Listar usuarios/roles
\du
\dg

-- Ejecutar archivo SQL
\i archivo.sql

-- Salir
\q

-- Help
\h
\?
```

### Consultas SQL Comunes

```sql
-- Ver todos los usuarios
SELECT * FROM users;

-- Ver categorías
SELECT * FROM categories;

-- Ver productos
SELECT * FROM products;

-- Ver usuarios activos
SELECT name, email, role FROM users WHERE is_active = true;

-- Contar registros
SELECT COUNT(*) FROM products;

-- Ver productos con categoría
SELECT p.name, p.sku, p.base_price, c.name as category
FROM products p
JOIN categories c ON p.category_id = c.id;

-- Ver inventario bajo
SELECT pv.sku_variant, p.name, i.quantity_available
FROM inventory i
JOIN product_variants pv ON i.product_variant_id = pv.id
JOIN products p ON pv.product_id = p.id
WHERE i.quantity_available < 5;
```

### CRUD Básico en SQL

```sql
-- INSERTAR
INSERT INTO categories (name, description, icon)
VALUES ('Gorras', 'Gorras y sombreros', 'cap');

-- ACTUALIZAR
UPDATE products SET base_price = 299.99 WHERE sku = 'PLAY-BAS-001';

-- ELIMINAR
DELETE FROM products WHERE sku = 'CAM-VER-001';

-- INSERTAR múltiples
INSERT INTO products (category_id, name, sku, base_price) VALUES
('id-categoria', 'Producto 1', 'SKU-001', 100.00),
('id-categoria', 'Producto 2', 'SKU-002', 200.00);
```

---

## 5. Git - Control de Versiones

### Configuración Inicial

```bash
# Configurar nombre y email
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# Configurar editor
git config --global core.editor nano

# Ver configuración
git config --list
```

### Operaciones Básicas

```bash
# ============================================
# CLONAR REPOSITORIO
# ============================================
git clone https://github.com/tu-usuario/FashionVision-AI.git
cd FashionVision-AI
```

```bash
# ============================================
# ESTADO DEL REPOSITORIO
# ============================================

# Ver estado de archivos
git status

# Ver diferencias (cambios no rastreados)
git diff

# Ver diferencias en archivos específicos
git diff archivo.js
```

```bash
# ============================================
# STAGING Y COMMIT
# ============================================

# Agregar archivos modificados al staging
git add .

# Agregar archivo específico
git add archivo.js

# Crear commit
git commit -m "Descripción del cambio"

# Commit rápido (agrega todo y hace commit)
git commit -am "Descripción del cambio"
```

```bash
# ============================================
# RAMAS (BRANCHES)
# ============================================

# Ver ramas
git branch

# Crear nueva rama
git branch nueva-funcionalidad

# Cambiar a otra rama
git checkout nueva-funcionalidad

# Crear y cambiar en un paso
git checkout -b nueva-funcionalidad

# Eliminar rama (primero salir de ella)
git branch -d nombre-rama

# Ver ramas remotas
git branch -r
```

```bash
# ============================================
# SINCRONIZAR CON REMOTO
# ============================================

# Traer cambios del remoto
git pull origin main

# Subir cambios al remoto
git push origin nombre-rama

# Ver remotos configurados
git remote -v
```

---

## 6. Logs y Debugging

### Ver Logs del Backend

```bash
# Si está corriendo con uvicorn, ver en terminal directamente

# Si está corriendo en background
journalctl -u uvicorn  # Linux (si es servicio)
tail -f /tmp/server.log  # Si guardamos logs ahí
```

### Ver Logs de Docker

```bash
# Todos los contenedores
docker-compose logs

# Contenedor específico
docker-compose logs db
docker-compose logs -f app

# Últimas 100 líneas
docker-compose logs --tail 100
```

### Reconstruir Contenedor Backend (si hay cambios)

```bash
cd backend
docker-compose build --no-cache
docker-compose up -d
```

### Debug Python

```bash
# Activar modo debug
export DEBUG=1

# Ver variables de entorno
printenv | grep -i python

# Probar imports
python -c "from backend.app.main import app; print('OK')"
```

---

## 7. Base de Datos - Backup y Restore

### Backup Completo

```bash
# ============================================
# LINUX / MAC
# ============================================
docker exec fashionvision_db pg_dump -U fashionvision_ai_user fashionvision_ai > backup_$(date +%Y%m%d_%H%M%S).sql

# Con compresión
docker exec fashionvision_db pg_dump -U fashionvision_ai_user fashionvision_ai | gzip > backup_$(date +%Y%m%d).sql.gz
```

```powershell
# ============================================
# WINDOWS POWERSHELL
# ============================================
$fecha = Get-Date -Format "yyyyMMdd_HHmmss"
docker exec fashionvision_db pg_dump -U fashionvision_ai_user fashionvision_ai > backup_$fecha.sql
```

### Backup de Tabla Específica

```bash
docker exec fashionvision_db pg_dump -U fashionvision_ai_user -t products fashionvision_ai > products_backup.sql
```

### Restore desde Backup

```bash
# Linux/Mac
cat backup_archivo.sql | docker exec -i fashionvision_db psql -U fashionvision_ai_user fashionvision_ai

# Windows PowerShell
Get-Content backup_archivo.sql | docker exec -i fashionvision_db psql -U fashionvision_ai_user fashionvision_ai
```

### Restore en pgAdmin

1. Click derecho en base de datos → **"Restore..."**
2. Seleccionar archivo `.sql`
3. Click en **"Restore"**

---

## 8. Limpieza y Mantenimiento

### Limpiar Docker

```bash
# Detener y eliminar contenedores
docker-compose down

# Eliminar volúmenes (¡PÉRDIDA DE DATOS!)
docker-compose down -v

# Eliminar imágenes no usadas
docker image prune -a

# Limpiar todo el sistema Docker
docker system prune -a --volumes
```

### Reconstruir Todo desde Cero

```bash
# 1. Eliminar todo
docker-compose down -v
rm -rf backend/venv
rm -f .env

# 2. Recrear entorno
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Copiar configuración
cp .env.example .env
ln -s backend/.env .env  # Linux

# 4. Levantar base de datos
docker-compose up -d

# 5. Iniciar backend
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --reload
```

### Verificar Espacio en Disco

```bash
# Docker
docker system df

# Linux general
df -h
du -sh backend/*
```

### Matar Procesos por Puerto

```bash
# Linux
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Resumen Visual de Comandos

### Levantar Proyecto Completo

```bash
# Terminal 1: Base de datos
cd backend
docker-compose up -d

# Terminal 2: Backend
source backend/venv/bin/activate
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --port 8000 --reload

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Verificaciones Rápidas

```bash
# ¿Docker corriendo?
docker ps

# ¿Backend funcionando?
curl http://localhost:8000/health

# ¿pgAdmin funcionando?
curl http://localhost:5050

# ¿Frontend funcionando?
curl http://localhost:5173
```

---

## Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Puerto en uso | `lsof -i :8000` → `kill -9 <PID>` |
| Docker no responde | `sudo systemctl restart docker` |
| Backend no conecta DB | Verificar `.env` y `PYTHONPATH=$PWD` |
| Dependencies rotos | Recrear venv: `rm -rf venv && python -m venv venv` |
| Permiso denegado (Docker) | Usar `sudo` o agregar usuario a grupo docker |
| pgAdmin no carga | Esperar 1-2 min, limpiar cache navegador |

---

## Documentación Relacionada

- [Guía de Instalación](./GUIA_INSTALACION.md)
- [Guía de pgAdmin](./GUIAS_PGADMIN.md)
- [Sistema de Sesiones y Carritos](./SESIONES_Y_CARRITOS.md)
