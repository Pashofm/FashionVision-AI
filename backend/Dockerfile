# ============================================================
# FashionVision AI — Dockerfile Backend
# ============================================================
# Multi-stage build para FastAPI + YOLO + CLIP
#
# Stage dev:  Python 3.12-slim, hot reload con uvicorn --reload
# Stage prod: Python 3.12-slim, gunicorn + uvicorn workers,
#             usuario no-root para seguridad
#
# Para usar en desarrollo:
#   docker compose up -d               (usa target: dev por defecto)
# Para usar en producción:
#   docker compose -f docker-compose.yml \
#                   -f docker-compose.prod.yml up -d   (usa target: prod)
# ============================================================

# ---- Stage base: dependencias del sistema y Python comunes ----
FROM python:3.12-slim-bookworm AS base

# Variables de build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema:
# - libpq-dev + gcc: necesarios para psycopg2/asyncpg
# - postgresql-client: aporta pg_isready para esperar la base de datos
# - libgl1 + libglib2.0-0 + libsm6 + libxext6 + libxrender-dev: OpenCV
# - wget: para descargar modelos si es necesario
# - netcat-openbsd: para health checks en scripts de espera
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt — se copia antes del código para
# aprovechar caché de capas de Docker
COPY requirements.txt .

# ---- Stage dev: entorno de desarrollo con hot reload ----
FROM base AS dev

RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios y archivos placeholder para pydantic-settings
RUN mkdir -p /app/media /app/.cache/torch /app/backend/models && \
    touch /app/.env /app/.env.local

# El código fuente se monta como volumen en docker-compose.yml
# por lo que no se copia aquí. Solo establecemos el WORKDIR.
# El directorio /app/backend será el mountpoint del volumen.

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ---- Stage prod: entorno de producción ----
FROM base AS prod

# Instalar solo dependencias (sin --reload ni herramientas dev)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente completo dentro de la imagen
COPY . /app/backend/

# Crear directorios y asignar permisos
RUN mkdir -p /app/media /app/.cache/torch && \
    chown -R nobody:nogroup /app && \
    chmod -R 755 /app

# Crear usuario no-root para ejecutar en producción
USER nobody

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "--bind", "0.0.0.0:8000", "backend.app.main:app"]
