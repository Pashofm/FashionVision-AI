# Glosario de Términos

Definiciones de términos técnicos y de dominio utilizados en FashionVision AI.

---

## Visión por Computadora

### YOLO (You Only Look Once)
Modelo de detección de objetos en tiempo real. En FashionVision AI se usa para detectar prendas de vestir en imágenes capturadas por la cámara del kiosko. El modelo pre-entrenado (`best.pt`) identifica clases como `clothing`, `shoes`, `bags`, `accessories` y devuelve bounding boxes con nivel de confianza.

### CLIP (Contrastive Language-Image Pre-training)
Modelo de OpenAI que genera embeddings (vectores numéricos de 512 dimensiones) a partir de imágenes. Se usa para comparar visualmente una prenda detectada con las imágenes del catálogo y encontrar el producto más similar.

### Embedding
Vector numérico que representa una imagen en un espacio de alta dimensionalidad. Dos imágenes visualmente similares producen embeddings cercanos (alta similitud coseno). Se almacenan en PostgreSQL usando la extensión pgvector.

### Bounding Box (bbox)
Rectángulo que delimita la ubicación de un objeto detectado en una imagen. Formato: `[x1, y1, x2, y2]` donde (x1,y1) es la esquina superior izquierda y (x2,y2) la inferior derecha.

### Confianza (Confidence)
Valor entre 0 y 1 que indica qué tan seguro está el modelo de que la detección es correcta. El umbral mínimo configurado es 0.30 (30%).

### Similitud Coseno (Cosine Similarity)
Medida de similitud entre dos vectores. Va de -1 a 1, donde 1 significa vectores idénticos. Se usa para comparar el embedding de una prenda detectada con los embeddings de productos en catálogo.

---

## Base de Datos

### pgvector
Extensión de PostgreSQL que agrega soporte para vectores y operaciones de similitud. Permite almacenar los embeddings de CLIP y buscar productos por similitud visual directamente en la base de datos.

### pg_trgm
Extensión de PostgreSQL para búsqueda por similitud de texto usando trigramas. Mejora las búsquedas de productos por nombre o SKU cuando hay errores tipográficos.

### Alembic
Herramienta de migraciones para SQLAlchemy. Permite versionar los cambios en el esquema de la base de datos y aplicarlos de forma controlada.

### Migración
Archivo que describe un cambio en el esquema de la base de datos (crear/alterar tablas, columnas, índices). Se aplican secuencialmente con Alembic.

---

## Dominio del Negocio

### Variante (ProductVariant)
Combinación específica de un producto: talla + color. Por ejemplo, "Camiseta básica — Talla M, Color Negro" es una variante. Cada variante tiene su propio SKU, precio y stock.

### SKU (Stock Keeping Unit)
Código único que identifica una variante de producto en el inventario. Se usa para tracking de stock y referencias en ventas.

### Umbral de Stock Bajo (Low Stock Threshold)
Cantidad mínima de unidades antes de que el sistema active una alerta de stock bajo. Se configura por variante (default: 5 unidades).

### Carrito (Cart)
Contenedor temporal de productos que un cliente está considerando comprar. Tiene un ciclo de vida: `building → submitted → processing → paid / cancelled`.

### Sesión (Session)
Representa una instancia de uso del sistema. Puede ser de tipo auth (admin/cajero) o kiosk (cliente en tienda). Las sesiones de kiosko expiran tras 2 minutos de inactividad.

### Kiosko
Estación física en la tienda donde el cliente puede escanear prendas usando la cámara. Es el punto de entrada del módulo de detección automática.

### Cajero (Cashier)
Rol de usuario que procesa los pagos y gestiona los carritos enviados por los clientes desde el kiosko.

### Orden (Order)
Registro de una venta completada. Se crea cuando un carrito pasa a estado `paid`.

### Recibo (Receipt)
Comprobante de venta generado tras completar un pago. Puede imprimirse en formato físico (térmica ESCPOS) o digital (HTML).

### Movimiento de Inventario (InventoryMovement)
Registro histórico de cada cambio en el stock: ventas, reabastecimientos, ajustes, devoluciones, reservas. Permite auditoría completa del inventario.

---

## Infraestructura

### Modo A — Hot-Reload (Desarrollo)
Backend y frontend se ejecutan localmente con recarga automática al detectar cambios en el código. Solo la base de datos corre en Docker.

### Modo B — Docker Full (Producción/Testing)
Todos los servicios (BD, backend, frontend, pgAdmin) se ejecutan en contenedores Docker orquestados con Docker Compose.

### Proxy Reverso
El frontend (Nginx) recibe todas las peticiones HTTP y redirige las que empiezan con `/api/` al backend. Esto evita problemas de CORS y permite servir todo desde un mismo dominio.

### JWT (JSON Web Token)
Token de autenticación sin estado. Contiene información del usuario firmada digitalmente. El access token expira en 30 minutos; el refresh token en 7 días.

---

## Tipos de Datos y Enums

### UserRole
- `admin` — Acceso total al sistema
- `cashier` — Gestiona caja y procesa pagos
- `client` — Usuario del kiosko (detección de prendas)

### CartStatus
- `building` — El cliente está agregando productos
- `submitted` — Enviado al cajero para procesar
- `processing` — El cajero está procesando el pago
- `paid` — Pago completado
- `cancelled` — Cancelado (por cliente o cajero)

### OrderStatus
- `pending` — Orden creada, esperando procesamiento
- `completed` — Orden finalizada exitosamente
- `refunded` — Reembolso total
- `partially_refunded` — Reembolso parcial

### MovementType (Inventario)
- `sale` — Venta (reduce stock)
- `restock` — Reabastecimiento (aumenta stock)
- `adjustment` — Ajuste manual
- `return` — Devolución
- `reserved` — Reservado para un carrito
- `released` — Reserva liberada

### StockStatus
- `available` — Disponible para venta
- `reserved` — Reservado en un carrito activo
- `damaged` — Dañado, no disponible
- `in_transit` — En tránsito (recibido pero no verificado)
- `returned` — Devuelto por cliente

### PaymentMethod
- `cash` — Efectivo
- `card` — Tarjeta (crédito/débito)
- `mixed` — Pago combinado (efectivo + tarjeta)

### SessionStatus
- `active` — Sesión en uso
- `completed` — Sesión finalizada normalmente
- `abandoned` — Sesión expirada por inactividad

### QueueStatus (POS)
- `waiting` — Esperando turno
- `in_progress` — Siendo procesado
- `completed` — Finalizado
- `skipped` — Saltado
