# Guía de Despliegue - FashionVision-AI

Documentación para desplegar FashionVision-AI en entornos de producción.

## Tabla de Contenidos

1. [Arquitectura de Producción](#arquitectura-de-producción)
2. [Requisitos del Servidor](#requisitos-del-servidor)
3. [Configuración de Seguridad](#configuración-de-seguridad)
4. [Despliegue con Docker](#despliegue-con-docker)
5. [Configuración de Nginx](#configuración-de-nginx)
6. [Variables de Entorno](#variables-de-entorno)
7. [Mantenimiento](#mantenimiento)
8. [Solución de Problemas](#solución-de-problemas)

---

## Arquitectura de Producción

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCCIÓN                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                    Nginx (Puerto 80/443)                 │  │
│   │                  SSL Termination + Proxy                  │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│              ┌───────────────┼───────────────┐                 │
│              │               │               │                 │
│              ▼               ▼               ▼                 │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│   │   Frontend   │   │   Backend    │   │     DB       │       │
│   │   Docker     │   │   Docker     │   │   Docker     │       │
│   │   :80        │   │   :8000      │   │   :5432      │       │
│   └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                  │              │
│                                                  ▼              │
│                                          ┌──────────────┐       │
│                                          │   pgAdmin    │       │
│                                          │   :5050      │       │
│                                          └──────────────┘       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

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
| Docker Compose | 2.20+ |
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

**NUNCA**commitear archivos `.env` con credenciales reales.

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
ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com

PGADMIN_EMAIL=admin@tudominio.com
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

# Instalar Docker Compose
sudo apt install docker-compose
```

### Paso 2: Transferir Archivos

```bash
# Desde tu máquina local
rsync -avz --exclude='.git' --exclude='venv' --exclude='node_modules' \
    --exclude='.env' FashionVision-AI/ user@server:/path/to/FashionVision-AI/
```

### Paso 3: Configurar en el Servidor

```bash
cd /path/to/FashionVision-AI

# Crear archivo .env de producción
nano .env

# Hacer scripts ejecutables
chmod +x scripts/*.sh

# Verificar security check
./scripts/check-env.sh
```

### Paso 4: Iniciar Servicios

```bash
# Opción A: Usar script de Docker (recomendado)
./scripts/docker-start.sh

# Opción B: Docker compose directo
docker compose up -d
```

### Paso 5: Configurar SSL (Let's Encrypt)

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Generar certificado
sudo certbot --nginx -d tudominio.com -d www.tudominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

---

## Configuración de Nginx

### Configuración Básica (`/etc/nginx/sites-available/fashionvision`)

```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tudominio.com www.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tudominio.com/privkey.pem;

    root /var/www/html;
    index index.html;

    # Frontend
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
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
        proxy_pass http://localhost:8000;
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

### Habilitar Sitio

```bash
sudo ln -s /etc/nginx/sites-available/fashionvision /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

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
# Verificar actualización de servicios
./scripts/update.sh status

# Actualizar Backend (sin rebuild)
./scripts/update.sh backend

# Actualizar Frontend (sin rebuild)
./scripts/update.sh frontend

# Actualización completa con rebuild
docker compose build
docker compose up -d
```

### Backups

```bash
# Backup de base de datos
docker compose exec db pg_dump -U fashionvision_ai_user fashionvision_ai > backup_$(date +%Y%m%d).sql

# Backup de volumen
docker run --rm -v fashionvision-ai_postgres_data:/data alpine tar czf - -C /data . > backup_db_$(date +%Y%m%d).tar.gz
```

### Monitoreo

```bash
# Ver uso de recursos
docker stats

# Ver logs
docker compose logs -f

# Ver salud de servicios
curl http://localhost:8000/health
```

---

## Solución de Problemas

### Contenedor no inicia

```bash
# Ver logs
docker compose logs <service>

# Reiniciar
docker compose restart <service>

# Rebuild si es necesario
docker compose build <service>
docker compose up -d <service>
```

### Base de datos no conecta

```bash
# Verificar que DB está corriendo
docker compose ps db

# Ver logs
docker compose logs db

# Verificar desde dentro del contenedor
docker compose exec db psql -U fashionvision_ai_user -d fashionvision_ai
```

### Error 502 Bad Gateway

```bash
# Verificar que backend está corriendo
curl http://localhost:8000/health

# Ver logs de nginx
tail -f /var/log/nginx/fashionvision_error.log

# Reiniciar nginx
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
- [ ] Docker y Docker Compose instalados
- [ ] Archivos .env configurados con passwords seguros
- [ ] Secrets generados con openssl
- [ ] Firewall configurado (solo 22, 80, 443)
- [ ] SSL con Let's Encrypt configurado
- [ ] Nginx configurado con proxy a backend
- [ ] Backup automático configurado
- [ ] Logs rotados (logrotate)
- [ ] Monitoreo básico (docker stats, health checks)
- [ ] Dominio apuntando correctamente (A record)

---

## Comandos de Emergencia

```bash
# Parar todo
docker compose down

# Parar y eliminar volúmenes (¡CUIDADO!)
docker compose down -v

# Reiniciar servidor completo
docker compose restart

# Ver logs de todos los servicios
docker compose logs -f --tail=100

# Ejecutar comandos de mantenimiento
docker compose exec backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```