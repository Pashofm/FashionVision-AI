# Política de Seguridad

## Reporte de Vulnerabilidades

Si descubres una vulnerabilidad de seguridad en FashionVision AI, por favor **no la reportes públicamente** en issues de GitHub. En su lugar, sigue estos pasos:

1. Envía un correo a los mantenedores del proyecto con los detalles
2. Incluye una descripción clara del problema, pasos para reproducirlo y el impacto potencial
3. Permite hasta 90 días para la resolución antes de divulgar públicamente

Agradecemos la divulgación responsable y reconocemos a quienes reporten vulnerabilidades.

---

## Versiones Soportadas

| Versión | Soportada |
|---------|-----------|
| 0.1.x   | ✅ Sí |

---

## Modelo de Seguridad

### Autenticación

- **JWT (JSON Web Tokens)** con algoritmo **HS256**
- Access token expira en **30 minutos** (configurable)
- Refresh token expira en **7 días** (configurable)
- Contraseñas hasheadas con **bcrypt**
- Invalidación de sesiones vía `last_logout_at`

### Roles y Permisos

| Rol | Dashboard | Inventario | Catálogo | Clientes | Caja |
|-----|-----------|------------|----------|----------|------|
| `admin` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `cashier` | ✅ | ❌ | ❌ | ❌ | ✅ |
| `client` | ❌ | ❌ | ❌ | ✅ (kiosko) | ❌ |

### Protección de Datos

- **Variables de entorno**: Configuración sensible (DB, JWT secret, API keys) se maneja vía `.env` (excluido de git)
- **CORS**: Orígenes permitidos configurables vía `ALLOWED_ORIGINS`
- **Validación de entrada**: FastAPI + Pydantic validan y sanitizan automáticamente los datos de entrada
- **SQL Injection**: Prevención mediante SQLAlchemy ORM con consultas parametrizadas

---

## Mejores Prácticas en Desarrollo

### Entorno Local

- Nunca commitees el archivo `.env` al repositorio
- Usa `SECRET_KEY` único por entorno (no el valor por defecto en producción)
- Rota las credenciales de Cloudinary regularmente

### Producción

- Cambia `SECRET_KEY` por un valor generado aleatoriamente (ej: `openssl rand -hex 32`)
- Cambia las contraseñas por defecto de PostgreSQL y pgAdmin
- Configura HTTPS (ver [Guía de Deploy](DEPLOYMENT.md))
- Habilita firewalls para limitar acceso a los puertos de BD y pgAdmin
- Ejecuta backups regulares de la base de datos
- Mantén las dependencias actualizadas (`pip list --outdated`, `npm outdated`)

### Dependencias

Para verificar vulnerabilidades conocidas en dependencias:

```bash
# Backend (Python)
pip install safety
safety check -r backend/requirements.txt

# Frontend (Node.js)
cd frontend
npm audit
```

---

## Consideraciones de Seguridad por Módulo

### Módulo de Visión (YOLO + CLIP)

- Las imágenes de clientes se procesan en memoria y no se almacenan permanentemente
- Los modelos se cargan al iniciar el servidor y no aceptan entradas arbitrarias del usuario
- Límite de tamaño de imagen: 5 MB por defecto (configurable vía `MAX_IMAGE_SIZE_MB`)

### Módulo de Pagos (POS)

- El driver mock para desarrollo no procesa pagos reales
- Para producción, migrar a un proveedor certificado PCI-DSS (Stripe Terminal, Square)
- Nunca almacenar datos de tarjetas de crédito en la base de datos

### Módulo de Sesiones

- Las sesiones de kiosko expiran automáticamente tras 2 minutos de inactividad
- Al hacer logout, se registra `last_logout_at` para invalidar tokens emitidos anteriormente
- La cuenta regresiva de 10 segundos permite al cliente cancelar el cierre de sesión

### Subida de Imágenes

- Las imágenes de productos se almacenan en Cloudinary (servicio externo)
- Cloudinary proporciona URLs firmadas y transformaciones seguras
- No se almacenan archivos subidos por usuarios directamente en el servidor
