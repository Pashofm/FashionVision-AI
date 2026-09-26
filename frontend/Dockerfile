# ============================================================
# FashionVision AI — Dockerfile Frontend
# ============================================================
# Multi-stage build para React 19 + Vite
#
# Stage dev:  node:20-alpine, Vite dev server con hot reload
#             El código fuente se monta como volumen.
# Stage prod: node:20-alpine builder → build estático →
#             nginx:alpine para servir la SPA compilada
#
# Para usar en desarrollo:
#   docker compose up -d               (usa target: dev)
# Para usar en producción:
#   docker compose -f docker-compose.yml \
#                   -f docker-compose.prod.yml up -d   (usa target: prod)
# ============================================================

# ---- Stage dev: Vite dev server con hot reload ----
FROM node:20-alpine AS dev

WORKDIR /app

# Instalar dependencias (capa cacheada si package*.json no cambia)
COPY package*.json ./
RUN npm ci

# El código fuente se monta como volumen en docker-compose.yml:
#   - ./frontend/src:/app/src:delegated
#   - ./frontend/public:/app/public:delegated
#   - ./frontend/index.html:/app/index.html:delegated
#   - ./frontend/vite.config.js:/app/vite.config.js:delegated
# Solo copiamos node_modules ya instalados; el resto viene del volumen.

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# ---- Stage builder: compilar la SPA con Vite ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

# Variable de build: API se sirve desde /api vía proxy nginx
ENV VITE_API_URL=/api

COPY . .
RUN npm run build


# ---- Stage prod: nginx sirviendo la SPA compilada ----
FROM nginx:1.25-alpine AS prod

# Copiar archivos estáticos compilados
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración de nginx para servir la SPA
# - fallback a index.html para React Router
# - proxy /api/* → backend:8000
# - gzip habilitado
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    client_max_body_size 50M; \
    location /nginx-health { \
        access_log off; \
        return 200 "healthy\n"; \
        add_header Content-Type text/plain; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_cache_bypass $http_upgrade; \
        proxy_read_timeout 120s; \
        proxy_send_timeout 120s; \
    } \
    location /health { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
    } \
    location /docs { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
    } \
    location /openapi.json { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
    } \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    gzip on; \
    gzip_vary on; \
    gzip_min_length 1000; \
    gzip_comp_level 6; \
    gzip_types text/plain text/css text/javascript application/javascript application/json application/xml text/xml image/svg+xml; \
    gzip_proxied any; \
    gzip_disable "msie6"; \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header Referrer-Policy "strict-origin-when-cross-origin" always; \
    error_page 500 502 503 504 /50x.html; \
    location = /50x.html { \
        root /usr/share/nginx/html; \
        internal; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
