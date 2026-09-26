# Configuración

La configuración de la demo se realiza mediante `.env`. Nunca commitees ese archivo. Usa `.env.example` como plantilla:

```bash
cp .env.example .env
```

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Variables principales

| Variable | Uso | Valor de demo |
|---|---|---|
| `POSTGRES_DB` | Nombre de la base de datos | `fashionvision_ai` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `fashionvision_ai_user` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | Cambiar fuera de demo |
| `SECRET_KEY` | Firma de tokens JWT | Cambiar fuera de demo |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | URLs locales |
| `ENVIRONMENT` | Entorno de ejecución | `development` |
| `MODEL_PATH` | Ruta del modelo YOLO dentro del contenedor | `/app/backend/models/best.pt` |
| `MEDIA_DIR` | Directorio de imágenes persistentes | `/app/media` |
| `MAX_IMAGE_SIZE_MB` | Tamaño máximo de imagen | `5` |
| `FRONTEND_HOST_PORT` | Puerto público de la aplicación | `80` |
| `PGADMIN_HOST_PORT` | Puerto público de pgAdmin | `5050` |
| `PGADMIN_EMAIL` | Usuario de pgAdmin | `admin@fashionvision.com` |
| `PGADMIN_PASSWORD` | Contraseña de pgAdmin | Cambiar fuera de demo |

## Detección YOLO y matching CLIP

Las variables `YOLO_*`, `CLIP_*`, `BBOX_*` y `REQUIRE_CATALOG_MATCH` ajustan la precisión y el comportamiento de la detección. Para empezar, conserva los valores del ejemplo.

- `YOLO_MIN_CONFIDENCE`: confianza mínima de detección.
- `YOLO_TTA_ENABLED`: activa aumento de imagen durante inferencia.
- `CLIP_MATCH_THRESHOLD`: similitud necesaria para aceptar un producto.
- `CLIP_WEAK_MATCH_THRESHOLD`: umbral para coincidencias débiles.
- `REQUIRE_CATALOG_MATCH`: oculta detecciones que no coinciden con el catálogo cuando vale `true`.

Los valores JSON deben permanecer en una sola línea dentro de `.env`.

## Cloudinary

Cloudinary es opcional. Configura `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` y `CLOUDINARY_API_SECRET` para almacenar imágenes de productos remotamente. Si se dejan vacías, la aplicación puede funcionar con las capacidades que no requieren almacenamiento remoto.

## Configuración de producción

Antes de usar el override de producción:

1. Genera una clave: `openssl rand -base64 32`.
2. Define contraseñas únicas para PostgreSQL y pgAdmin.
3. Revisa `ALLOWED_ORIGINS`.
4. No uses las cuentas demo en un entorno real.
5. Configura TLS y un dominio en la infraestructura que se coloque delante de Nginx.

Consulta [DEPLOYMENT.md](DEPLOYMENT.md) para conocer el alcance actual del despliegue de producción.
