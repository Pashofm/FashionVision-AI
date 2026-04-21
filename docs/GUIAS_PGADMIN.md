# Guía Completa de pgAdmin para FashionVision-AI

Cómo configurar y usar pgAdmin para administrar la base de datos PostgreSQL del proyecto.

---

## Tabla de Contenidos

1. [¿Qué es pgAdmin?](#1-qué-es-pgadmin)
2. [Opción A: pgAdmin con Docker](#2-opción-a-pgadmin-con-docker-recomendado)
3. [Opción B: pgAdmin Local](#3-opción-b-pgadmin-local-sin-docker)
4. [Agregar Servidor en pgAdmin](#4-agregar-servidor-en-pgadmin)
5. [Navegación Básica de pgAdmin](#5-navegación-básica-de-pgadmin)
6. [Operaciones Comunes con Datos](#6-operaciones-comunes-con-datos)
7. [Consultas SQL en pgAdmin](#7-consultas-sql-en-pgadmin)
8. [Exportar e Importar Datos](#8-exportar-e-importar-datos)
9. [Solución de Problemas](#9-solución-de-problemas)

---

## 1. ¿Qué es pgAdmin?

pgAdmin es una herramienta gráfica gratuita para administrar bases de datos PostgreSQL. Permite:
- Ver tablas y estructura visualmente
- Ejecutar consultas SQL
- Hacer backup y restore de datos
- Gestionar usuarios y permisos
- Visualizar y editar datos en tablas

---

## 2. Opción A: pgAdmin con Docker (Recomendado)

### Linux

```bash
# Crear red para conectar pgAdmin con PostgreSQL
docker network create fva_network

# Verificar que PostgreSQL está en la red
docker network inspect fva_network

# Si PostgreSQL no está en la red, reconectar
docker network connect fva_network fashionvision_db

# Ejecutar pgAdmin
docker run -d \
  --name pgadmin \
  --network fva_network \
  -e PGADMIN_DEFAULT_EMAIL=admin@fashionvision.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin123 \
  -e PGADMIN_CONFIG_SERVER_MODE=False \
  -p 5050:80 \
  --restart unless-stopped \
  dpage/pgadmin4
```

### Windows

Abrir PowerShell o CMD (NO Git Bash):

```powershell
# Crear red
docker network create fva_network

# Conectar PostgreSQL a la red
docker network connect fva_network fashionvision_db

# Ejecutar pgAdmin
docker run -d ^
  --name pgadmin ^
  --network fva_network ^
  -e PGADMIN_DEFAULT_EMAIL=admin@fashionvision.com ^
  -e PGADMIN_DEFAULT_PASSWORD=admin123 ^
  -e PGADMIN_CONFIG_SERVER_MODE=False ^
  -p 5050:80 ^
  --restart unless-stopped ^
  dpage/pgadmin4
```

### Verificar que pgAdmin Está Corriendo

```bash
docker ps
```

Deberías ver:
```
CONTAINER ID   IMAGE          STATUS         PORTS
xxxxx          dpage/pgadmin4   Up 2 minutes   0.0.0.0:5050->80/tcp
xxxxx          postgres:16      Up 5 hours      0.0.0.0:5433->5432/tcp
```

---

## 3. Opción B: pgAdmin Local (sin Docker)

### Paso 3.1: Descargar pgAdmin

1. Ir a https://www.pgadmin.org/download/
2. Elegir versión según tu SO:
   - **Windows**: pgAdmin 4 (Latest)
   - **Linux**: Ver instrucciones según distribución abajo

### Instalación en Windows

1. Descargar archivo `.exe` o `.msi`
2. Ejecutar instalador
3. Seguir wizard de instalación
4. Al finalizar, abrir pgAdmin desde el menú inicio

### Instalación en Linux (Ubuntu/Debian)

```bash
# Instalar dependencias
sudo apt update
sudo apt install -y libpq5 pgadmin4 pgadmin4-apache2

# Configurar (seguir wizard interactivo)
sudo dpkg-reconfigure pgadmin4
```

### Instalación en Linux (Fedora)

```bash
sudo dnf install -y pgadmin4
```

### Instalación en Linux (Arch)

```bash
sudo pacman -S pgadmin4
```

---

## 4. Agregar Servidor en pgAdmin

### Paso 4.1: Acceder a pgAdmin

1. Abrir navegador
2. Ir a: http://localhost:5050
3. Login con:
   - **Email**: `admin@fashionvision.com`
   - **Contraseña**: `admin123`

### Paso 4.2: Agregar Nuevo Servidor

1. Click derecho en **"Servers"** (panel izquierdo)
2. Seleccionar **"Create"** → **"Server..."**

### Paso 4.3: Configurar Pestaña "General"

```
Name: FashionVision DB (o el nombre que prefieras)
Server group: Server Group 1 (dejar por defecto)
```

### Paso 4.4: Configurar Pestaña "Connection"

```
Host name/address: host.docker.internal
Port: 5433
Maintenance database: fashionvision_ai
Username: fashionvision_ai_user
Password: fashionvision_ai_pass
Save password: ✓ (marcar checkbox)
```

**Explicación de campos:**
- **host.docker.internal**: Permite a Docker acceder al host desde el contenedor
- **5433**: Puerto expuesto en Docker (no el interno 5432)
- **Maintenance database**: Base de datos principal

### Paso 4.5: Configurar Avanzado (si es necesario)

Si el paso 4.4 no conecta, probar en pestaña "Advanced":

```
Host address: 172.17.0.1
```

Para encontrar la IP correcta:
```bash
# Linux
docker network inspect bridge | grep Gateway

# Windows
docker network inspect bridge
```

### Paso 4.6: Guardar

1. Click en **"Save"**
2. El servidor debería aparecer en el panel izquierdo
3. Click en el servidor para expandir y ver bases de datos

---

## 5. Navegación Básica de pgAdmin

### Panel Izquierdo (Explorador)

```
├── Servers
│   └── FashionVision DB
│       ├── Databases
│       │   └── fashionvision_ai
│       │       ├── Schemas
│       │       │   └── public
│       │       │       └── Tables
│       │       │           ├── users
│       │       │           ├── categories
│       │       │           ├── products
│       │       │           └── ... (más tablas)
│       │       └── Views
│       └── Login/Group Roles
```

### Ver Estructura de una Tabla

1. Expandir **Tables** → Click en tabla (ej: `users`)
2. Seleccionar pestaña **"Columns"** para ver columnas
3. Seleccionar pestaña **"Constraints"** para ver claves foráneas
4. Seleccionar pestaña **"Indexes"** para ver índices

### Ver Datos de una Tabla

1. Click derecho en tabla → **"View/Edit Data"** → **"All Rows"**
2. O usar herramienta de consulta (Explicado abajo)

---

## 6. Operaciones Comunes con Datos

### Insertar Datos (Nuevo Usuario)

1. Click derecho en tabla `users` → **"Import/Export"** 
2. O besser: Usar Query Tool

### Editar Datos Existentes

1. Click derecho en tabla → **"View/Edit Data"** → **"All Rows"**
2. Doble click en celda para editar
3. Click en **"Save"** para guardar cambios

### Eliminar Datos

1. View/Edit Data → All Rows
2. Seleccionar fila
3. Click en icono **"Delete"** (papelera rojo)
4. Guardar cambios

### Insertar Nueva Fila

1. View/Edit Data → All Rows
2. Click en icono **"Insert Row"** (+)
3. Llenar datos
4. Guardar cambios

---

## 7. Consultas SQL en pgAdmin

### Abrir Query Tool

1. Click derecho en base de datos `fashionvision_ai`
2. Seleccionar **"Query Tool"**

### Consultas Básicas

```sql
-- Ver todos los usuarios
SELECT * FROM users;

-- Ver todas las categorías
SELECT * FROM categories;

-- Ver productos con sus categorías (JOIN)
SELECT 
    p.name AS product_name,
    p.sku,
    p.base_price,
    c.name AS category_name
FROM products p
JOIN categories c ON p.category_id = c.id;

-- Ver productos con bajo stock
SELECT 
    pv.sku_variant,
    p.name AS product,
    i.quantity_available,
    i.low_stock_threshold
FROM inventory i
JOIN product_variants pv ON i.product_variant_id = pv.id
JOIN products p ON pv.product_id = p.id
WHERE i.quantity_available < i.low_stock_threshold;

-- Contar productos por categoría
SELECT 
    c.name AS category,
    COUNT(p.id) AS product_count
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
GROUP BY c.name
ORDER BY product_count DESC;
```

### Insertar Datos

```sql
-- Insertar nuevo usuario
INSERT INTO users (name, email, password_hash, role)
VALUES (
    'Juan Pérez',
    'juan@tienda.com',
    '$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'client'
);

-- Insertar nuevo producto
INSERT INTO products (category_id, name, sku, base_price, yolo_class_name)
VALUES (
    'c0000001-0000-0000-0000-000000000001',
    'Camisa Verde Casual',
    'CAM-VER-001',
    380.00,
    'camisa_verde_casual'
);
```

### Actualizar Datos

```sql
-- Actualizar precio de producto
UPDATE products 
SET base_price = 399.00 
WHERE sku = 'CAM-OXF-001';

-- Activar usuario
UPDATE users 
SET is_active = true 
WHERE email = 'usuario@email.com';
```

### Eliminar Datos

```sql
-- Eliminar producto por SKU
DELETE FROM products 
WHERE sku = 'CAM-VER-001';

-- Eliminar usuario (primero eliminar sus carritos)
DELETE FROM carts 
WHERE session_id IN (SELECT id FROM sessions WHERE client_user_id = 'uuid-del-usuario');
DELETE FROM users 
WHERE email = 'usuario@email.com';
```

---

## 8. Exportar e Importar Datos

### Exportar Tabla a CSV

1. Click derecho en tabla → **"Import/Export"**
2. En "File Name" escribir: `/tmp/users_export.csv`
3. Marcar "Export"
4. Click en "OK"

### Importar Datos desde CSV

1. Click derecho en tabla → **"Import/Export"**
2. En "File Name" seleccionar archivo CSV
3. Marcar "Import"
4. Configurar formato (Header: Yes, Delimiter: comma)
5. Click en "OK"

### Backup Completo de Base de Datos

```bash
# Linux/Mac (terminal)
docker exec fashionvision_db pg_dump -U fashionvision_ai_user fashionvision_ai > backup_$(date +%Y%m%d).sql

# Windows (PowerShell)
docker exec fashionvision_db pg_dump -U fashionvision_ai_user fashionvision_ai > backup_$((Get-Date).ToString('yyyyMMdd')).sql
```

### Restore desde Backup

```bash
# Linux/Mac
cat backup_20260421.sql | docker exec -i fashionvision_db psql -U fashionvision_ai_user fashionvision_ai

# Windows
Get-Content backup_20260421.sql | docker exec -i fashionvision_db psql -U fashionvision_ai_user fashionvision_ai
```

---

## 9. Solución de Problemas

### No puedo conectar al servidor

**Síntoma**: Error "Connection refused" o "could not connect"

**Solución**:
1. Verificar que PostgreSQL está corriendo:
```bash
docker ps
```

2. Verificar que el puerto es correcto (5433, no 5432)

3. Verificar firewall:
```bash
# Linux
sudo ufw allow 5433/tcp

# Windows
# Abrir PowerShell como Admin
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=tcp localport=5433
```

### pgAdmin no carga en el navegador

**Solución**:
1. Verificar que el contenedor está corriendo:
```bash
docker ps | grep pgadmin
```

2. Esperar 1-2 minutos (pgAdmin tarda en iniciar la primera vez)

3. Limpiar cache del navegador y probar http://localhost:5050

### Contraseña olvidada de pgAdmin

**Solución**: Recrear el contenedor:
```bash
docker stop pgadmin
docker rm pgadmin
# Volver a ejecutar comando de creación (sección 2)
```

### "host.docker.internal" no funciona en Windows

**Solución alternativa**:

1. Encontrar IP del contenedor PostgreSQL:
```powershell
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' fashionvision_db
```

2. Usar esa IP en lugar de `host.docker.internal`

O usar la IP del gateway de Docker:
```powershell
docker network inspect bridge | findstr Gateway
```

---

## Comandos Rápidos de Referencia

| Acción | Comando Docker |
|--------|---------------|
| Iniciar pgAdmin | `docker start pgadmin` |
| Detener pgAdmin | `docker stop pgadmin` |
| Ver logs | `docker logs pgadmin` |
| Reiniciar pgAdmin | `docker restart pgadmin` |

| Acción | URL |
|--------|-----|
| pgAdmin en navegador | http://localhost:5050 |
| Health check API | http://localhost:8000/health |
| Swagger docs | http://localhost:8000/docs |

---

## Credenciales

| Servicio | Usuario | Contraseña |
|----------|---------|------------|
| pgAdmin | admin@fashionvision.com | admin123 |
| PostgreSQL | fashionvision_ai_user | fashionvision_ai_pass |

---

## Próximos Pasos

- [Guía de Instalación](./GUIA_INSTALACION.md) - Si aún no has configurado el entorno
- [Comandos Importantes](./COMANDOS.md) - Referencia rápida del proyecto
