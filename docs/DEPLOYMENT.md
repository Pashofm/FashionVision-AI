# Guía de Despliegue - FashionVision-AI

Documentación para desplegar FashionVision-AI en entornos de producción.

## Tabla de Contenidos

1. [Arquitectura de Producción](#arquitectura-de-producción)
2. [Requisitos del Servidor](#requisitos-del-servidor)
3. [Configuración de Seguridad](#configuración-de-seguridad)
4. [Despliegue con Docker](#despliegue-con-docker)
5. [docker-compose.prod.yml — Override de Producción](#docker-composeprodyml--override-de-producción)
6. [Configuración de Nginx](#configuración-de-nginx)
7. [Variables de Entorno](#variables-de-entorno)
8. [Mantenimiento](#mantenimiento)
9. [Solución de Problemas](#solución-de-problemas)

---

## Arquitectura de Producción

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCCIÓN                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                Nginx (Puerto 80/443)                     │  │
│   │              SSL Termination + Proxy                      │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│              ┌───────────────┼───────────────┐                 │
│              │               │               │                 │
│              ▼               ▼               ▼                 │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│   │   Frontend   │   │   Backend    │   │     DB       │       │
│   │   Docker     │   │   Docker     │   │   Docker     │       │
│   │   (build     │   │   :8000      │   │   :5432      │       │
│   │   estático)  │   │   (Gunicorn) │   │              │       │
│   └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

Cuatro servicios Docker orquestados: Nginx expone los puertos 80/443 y actúa como proxy reverso hacia el frontend (contenido estático) y el backend (Gunicorn en :8000), mientras PostgreSQL corre en :5432 sin exponerse al exterior.

---

## Requisitos del Servidor

### Hardware Mínimo

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Almacenamiento | 20 GB | 50+ GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### Software

| Software | Versión |
|----------|---------|
| Docker | 24.0+ |
| Docker Compose (plugin) | 2.20+ |
| Nginx | 1.18+ |

### Consideraciones de YOLO

El modelo YOLO requiere recursos adicionales:

| Recurso | Requerimiento |
|---------|---------------|
| RAM adicional | +2 GB para inferencia |
| GPU (opcional) | NVIDIA GPU con CUDA para mejor rendimiento |

---

## Configuración de Seguridad

### 1. Variables de Entorno Críticas

**NUNCA** commitear archivos `.env` con credenciales reales.

Crear `.env` en el servidor con:

```env
# PRODUCCIÓN - SOLO USAR EN SERVIDOR
POSTGRES_DB=fashionvision_ai
POSTGRES_USER=fashionvision_ai_user
POSTGRES_PASSWORD=<GENERAR_PASSWORD_FUERTE>
POSTGRES_HOST_PORT=5432

SECRET_KEY=<GENERAR_CON_OPENSSL>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

ENVIRONMENT=production
ALLOWED_ORIGINS=https://{{TU_DOMINIO}},https://www.{{TU_DOMINIO}}

PGADMIN_EMAIL=admin@{{TU_DOMINIO}}
PGADMIN_PASSWORD=<GENERAR_PASSWORD_FUERTE>
```

### 2. Generar Secretos Seguros

```bash
# Generar SECRET_KEY
openssl rand -base64 32

# Generar passwords
openssl rand -base64 24
```

### 3. Permisos de Archivos

```bash
# En el servidor
chmod 600 .env
chmod 600 docker-compose.yml
chmod 600 docker-compose.prod.yml
```

### 4. Firewall

```bash
# Solo permitir puertos necesarios
sudo ufw allow 22    # SSH
sudo ufw allow 80     # HTTP
sudo ufw allow 443    # HTTPS

# Si necesitas pgAdmin temporalmente:
sudo ufw allow 5050   # Solo IPterna
```

---

## Despliegue con Docker

### Paso 1: Preparar el Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Instalar el plugin oficial de Docker Compose (NO docker-compose v1)
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Verificar instalación
docker compose version
```

**Nota:** el plugin oficial de Docker Compose se invoca con `docker compose` (con espacio, no con guion). El paquete legacy `docker-compose` (v1, Python) está deprecado y **no debe usarse**. En Ubuntu 22.04+, el plugin `docker-compose-plugin` se instala directamente desde los repositorios oficiales.

### Paso 2: Transferir Archivos

```bash
# Desde tu máquina local
rsync -avz --exclude='.git' --exclude='venv' --exclude='node_modules' \
    --exclude='.env' FashionVision-AI/ user@{{TU_SERVIDOR}}:{{RUTA_PROYECTO}}
```

### Paso 3: Configurar en el Servidor

```bash
cd {{RUTA_PROYECTO}}

# Crear archivo .env de producción
nano .env

# Hacer scripts ejecutables
chmod +x scripts/*.sh

# Verificar security check
./scripts/check-env.sh
```

### Paso 4: Iniciar Servicios

```bash
# Usar ambos archivos de configuración: base + override de producción
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Importante:** siempre se deben especificar ambos archivos (`docker-compose.yml` como base y `docker-compose.prod.yml` como override de producción). Si se ejecuta `docker compose up -d` sin el archivo de producción, los servicios se iniciarán con la configuración de desarrollo (hot reload, volúmenes de código, sin política de reinicio, etc.).

### Paso 5: Configurar SSL (Let's Encrypt)

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Generar certificado
sudo certbot --nginx -d {{TU_DOMINIO}} -d www.{{TU_DOMINIO}}

# Verificar renovación automática
sudo certbot renew --dry-run
```

---

## docker-compose.prod.yml — Override de Producción

El archivo `docker-compose.prod.yml` es un **archivo de override** que se combina con el `docker-compose.yml` base para aplicar configuraciones exclusivas de producción. Docker Compose hace merge de ambos archivos automáticamente cuando se especifican con la flag `-f`.

### Qué sobreescribe docker-compose.prod.yml

| Aspecto | Desarrollo (base) | Producción (override) |
|---------|-------------------|----------------------|
| **Política de reinicio** | No configurado | `restart: always` en todos los servicios |
| **Backend WSGI** | Uvicorn con `--reload` | Gunicorn + Uvicorn workers (sin hot reload) |
| **Volúmenes de código** | `.:/app` montado para live reload | Sin montaje de código (usa la imagen construida) |
| **Debug** | `ENVIRONMENT=development` | `ENVIRONMENT=production` (desactiva debuggers) |
| **Frontend** | Vite dev server con HMR | Build estático servido por Nginx |
| **Exposición de puertos** | Frontend :5173, Backend :8000 | Solo Nginx expone :80 y :443 |
| **Logging** | stdout/stderr por defecto | Configurado para rotación y persistencia |

### Ejemplo de docker-compose.prod.yml

```yaml
version: "3.8"

services:
  backend:
    restart: always
    environment:
      - ENVIRONMENT=production
    command: >
      gunicorn app.main:app
      --workers 4
      --worker-class uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8000
      --access-logfile -
      --error-logfile -

  frontend:
    restart: always

  nginx:
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro

  db:
    restart: always
```

### Cómo usar el override

```bash
# Iniciar producción (SIEMPRE con ambos archivos)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Detener producción
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Ver estado
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Reconstruir y desplegar
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Configuración de Nginx

**Nota importante:** este documento describe la configuración de Nginx tanto para un Nginx instalado a nivel de host (vía `apt`) como para el servicio Nginx dentro de Docker. Ambos enfoques funcionan en producción; la diferencia principal es que con el Nginx de Docker, la configuración se monta como volumen dentro del contenedor, mientras que con el Nginx del host se gestiona vía `systemctl` y `sites-available/sites-enabled`. El contenido de la configuración del server block es el mismo en ambos casos.

### Configuración Base (server block)

```nginx
server {
    listen 80;
    server_name {{TU_DOMINIO}} www.{{TU_DOMINIO}};

    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name {{TU_DOMINIO}} www.{{TU_DOMINIO}};

    ssl_certificate /etc/letsencrypt/live/{{TU_DOMINIO}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{TU_DOMINIO}}/privkey.pem;

    root /var/www/html;
    index index.html;

    # Frontend
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support (si se usa)
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Logs
    access_log /var/log/nginx/fashionvision_access.log;
    error_log /var/log/nginx/fashionvision_error.log;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
```

### Enfoque A: Nginx del Host (vía systemd)

```bash
# Guardar la configuración
sudo cp nginx.conf /etc/nginx/sites-available/fashionvision

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/fashionvision /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Enfoque B: Nginx dentro de Docker (recomendado para despliegues simples)

El servicio Nginx se define en `docker-compose.yml` y se configura vía `docker-compose.prod.yml`. La configuración se monta como volumen:

```yaml
# En docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend
    restart: always
```

**Nota sobre el proxy_pass:** cuando Nginx corre dentro de Docker y los servicios están en la misma red interna de Docker, `proxy_pass http://backend:8000;` es correcto porque Docker resuelve los nombres de servicio internamente. Si se usa Nginx a nivel de host, cambiar a `proxy_pass http://localhost:8000;`.

---

## Variables de Entorno

### Para Producción, configurar:

| Variable | Valor Recomendado | Notas |
|----------|------------------|-------|
| `ENVIRONMENT` | `production` | Desactiva debug |
| `SECRET_KEY` | 64 chars aleatorios | Crítico para seguridad |
| `POSTGRES_PASSWORD` | 24+ chars | Generado con openssl |
| `PGADMIN_PASSWORD` | 24+ chars | Solo para admins |
| `ALLOWED_ORIGINS` | Solo tu dominio | No localhost |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15-30 | Seguridad JWT |

### Configuración Docker

Para producción, usar Docker secrets o un sistema de gestión de secretos.

---

## Mantenimiento

### Actualizaciones

```bash
# Verificar estado de servicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Actualizar solo Backend (sin reconstruir, sin dependencias)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend

# Actualizar solo Frontend (sin reconstruir, sin dependencias)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps frontend

# Actualización completa con rebuild
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Backups

```bash
# Backup de base de datos (formato SQL)
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    exec db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    > backup_$(date +%Y%m%d).sql

# Backup de volumen (formato comprimido)
docker run --rm \
    -v fashionvision-ai_postgres_data:/data \
    alpine tar czf - -C /data . \
    > backup_db_$(date +%Y%m%d).tar.gz
```

### Monitoreo

```bash
# Ver uso de recursos
docker stats

# Ver logs de todos los servicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Ver salud de servicios
curl http://localhost:8000/health
```

---

## Solución de Problemas

### Contenedor no inicia

```bash
# Ver logs de un servicio específico
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs <service>

# Reiniciar
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart <service>

# Rebuild si es necesario
docker compose -f docker-compose.yml -f docker-compose.prod.yml build <service>
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d <service>
```

### Base de datos no conecta

```bash
# Verificar que DB está corriendo
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps db

# Ver logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs db

# Verificar desde dentro del contenedor
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    exec db psql -U fashionvision_ai_user -d fashionvision_ai
```

### Error 502 Bad Gateway

```bash
# Verificar que backend está corriendo
curl http://localhost:8000/health

# Ver logs de nginx (Docker)
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx

# Si usas nginx del host
tail -f /var/log/nginx/fashionvision_error.log
sudo systemctl reload nginx
```

### SSL certificate issues

```bash
# Verificar certbot
sudo certbot certificates

# Renovar manualmente
sudo certbot renew

# Verificar configuración
sudo nginx -t
```

---

## Checklist de Producción

- [ ] Servidor con Ubuntu 22.04 LTS
- [ ] Docker y Docker Compose plugin instalados
- [ ] Archivos .env configurados con passwords seguros
- [ ] Secrets generados con openssl
- [ ] docker-compose.prod.yml configurado con overrides correctos
- [ ] Firewall configurado (solo 22, 80, 443)
- [ ] SSL con Let's Encrypt configurado
- [ ] Nginx configurado con proxy al backend
- [ ] Backup automático configurado
- [ ] Logs rotados (logrotate)
- [ ] Monitoreo básico (docker stats, health checks)
- [ ] Dominio apuntando correctamente (A record)

---

## Comandos de Emergencia

```bash
# Parar todo
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Parar y eliminar volúmenes (¡CUIDADO! Elimina la base de datos)
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v

# Reiniciar todos los servicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Ver logs de todos los servicios (últimas 100 líneas)
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=100

# Verificar estado del backend desde dentro del contenedor
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    exec backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```
