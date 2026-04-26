-- ═══════════════════════════════════════════════════════════════════════════
--  FashionVision-AI — Esquema completo de base de datos
--  Sistema de FashionVision AI con IA para tiendas pequeñas y medianas
--  PostgreSQL 16+
-- ═══════════════════════════════════════════════════════════════════════════

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- búsqueda por similitud de texto

-- ─────────────────────────────────────────────────────────────────────────────
--  ENUMS — Tipos enumerados reutilizables
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('admin', 'cashier', 'client');

CREATE TYPE cart_status AS ENUM (
    'building',     -- el cliente está agregando prendas
    'submitted',    -- el cliente mandó el carrito al admin
    'processing',   -- el admin lo está procesando en caja
    'paid',         -- pago completado
    'cancelled'     -- cancelado
);

CREATE TYPE order_status AS ENUM (
    'pending',
    'completed',
    'refunded',
    'partially_refunded'
);

CREATE TYPE payment_method AS ENUM ('cash', 'card', 'mixed');

CREATE TYPE queue_status AS ENUM (
    'waiting',      -- en espera en la cola del admin
    'in_progress',  -- el cajero lo está atendiendo
    'completed',    -- pago realizado
    'skipped'       -- saltado (se puede retomar)
);

CREATE TYPE queue_priority AS ENUM ('normal', 'urgent');

CREATE TYPE movement_type AS ENUM (
    'sale',         -- salida por venta
    'restock',      -- entrada por reabastecimiento
    'adjustment',   -- ajuste manual de inventario
    'return',       -- devolución de producto
    'reserved',     -- reserva por carrito activo
    'released'      -- liberación de reserva (carrito cancelado)
);

CREATE TYPE session_status AS ENUM ('active', 'completed', 'abandoned');

CREATE TYPE stock_status AS ENUM ('available', 'reserved', 'damaged', 'in_transit', 'returned');


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: users — Usuarios del sistema
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(150)    NOT NULL,
    email           VARCHAR(255)    UNIQUE NOT NULL,
    password_hash   TEXT            NOT NULL,
    role            user_role       NOT NULL DEFAULT 'client',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    avatar_path     TEXT,
    last_logout_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  users            IS 'Usuarios del sistema: administradores, cajeros y clientes registrados';
COMMENT ON COLUMN users.role       IS 'admin=acceso total, cashier=solo caja, client=solo kiosko';
COMMENT ON COLUMN users.avatar_path IS 'Ruta relativa a /media/avatars/';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: categories — Categorías de prendas
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100)    NOT NULL UNIQUE,
    description TEXT,
    icon        VARCHAR(50),            -- nombre de ícono para la UI
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE categories IS 'Categorías de ropa: Camisas, Pantalones, Vestidos, etc.';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: store_config — Configuración de la tienda (para receipts, invoices)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE store_config (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_name             VARCHAR(200)     NOT NULL DEFAULT 'FashionVision AI',
    legal_name              VARCHAR(255),
    address                 TEXT,
    phone                   VARCHAR(20),
    email                   VARCHAR(255),
    tax_id                  VARCHAR(50),              -- RFC en México
    website                 VARCHAR(255),
    default_currency        VARCHAR(3)       NOT NULL DEFAULT 'MXN',
    default_payment_method  payment_method  NOT NULL DEFAULT 'cash',
    receipt_footer          TEXT,
    is_active               BOOLEAN         NOT NULL DEFAULT TRUE,
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE store_config IS 'Configuración general de la tienda para receipts e invoices';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: suppliers — Proveedores de mercancía
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE suppliers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(150)    NOT NULL,
    contact_name    VARCHAR(100),
    email           VARCHAR(255),
    phone           VARCHAR(20),
    address         TEXT,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE suppliers IS 'Catálogo de proveedores de mercancía';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: attribute_options — Catálogo global de atributos (tallas y colores)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE attribute_options (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type        VARCHAR(20)     NOT NULL CHECK (type IN ('size', 'color')),
    value       VARCHAR(50)     NOT NULL,
    hex_code    CHAR(7),                    -- Solo para colores: '#FF5733'
    sort_order  INTEGER         NOT NULL DEFAULT 0,
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_attribute_type_value UNIQUE (type, value)
);

COMMENT ON TABLE attribute_options IS 'Catálogo de tallas y colores predefinidos disponibles globalmente';
COMMENT ON COLUMN attribute_options.type IS 'Tipo de atributo: size o color';
COMMENT ON COLUMN attribute_options.value IS 'Valor del atributo: "S", "M", "L", "Rojo", "Azul"';
COMMENT ON COLUMN attribute_options.hex_code IS 'Código hexadecimal para colores en la UI';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: product_attributes — Relación productos ↔ atributos disponibles
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE product_attributes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id          UUID            NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    attribute_option_id UUID            NOT NULL REFERENCES attribute_options(id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_product_attribute UNIQUE (product_id, attribute_option_id)
);

COMMENT ON TABLE product_attributes IS 'Define qué tallas/colores están disponibles para cada producto';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: price_history — Historial de cambios de precio
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE price_history (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id    UUID            NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price_type    VARCHAR(20)     NOT NULL CHECK (price_type IN ('cost', 'base', 'special')),
    old_price     NUMERIC(10,2),
    new_price     NUMERIC(10,2)   NOT NULL,
    changed_by    UUID            REFERENCES users(id) ON DELETE SET NULL,
    reason        TEXT,
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE price_history IS 'Registro de todos los cambios de precio realizados en productos';
COMMENT ON COLUMN price_history.price_type IS 'Tipo de precio modificado: cost=costo, base=venta, special=oferta';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: products — Catálogo de prendas
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id     UUID            NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name            VARCHAR(200)    NOT NULL,
    description     TEXT,
    sku             VARCHAR(100)    NOT NULL UNIQUE,

    -- Precio base (las variantes pueden ajustarlo)
    base_price      NUMERIC(10,2)   NOT NULL CHECK (base_price >= 0),

    -- ─── Campos de precio profesional ─────────────────────────────────
    cost_price      NUMERIC(10,2)   NOT NULL DEFAULT 0 CHECK (cost_price >= 0),
    tax_rate        NUMERIC(5,4)    NOT NULL DEFAULT 0.16 CHECK (tax_rate >= 0 AND tax_rate <= 1),
    profit_margin   NUMERIC(5,4)    NOT NULL DEFAULT 0 CHECK (profit_margin >= 0 AND profit_margin <= 1),

    -- ─── Información adicional del producto ───────────────────────────
    brand           VARCHAR(100),
    supplier        VARCHAR(150),
    barcode         VARCHAR(50)    UNIQUE,
    weight          NUMERIC(8,2),
    width           NUMERIC(8,2),
    height          NUMERIC(8,2),
    depth           NUMERIC(8,2),
    min_stock_level INTEGER        NOT NULL DEFAULT 0,
    max_stock_level INTEGER,
    is_featured     BOOLEAN        NOT NULL DEFAULT FALSE,
    tags            JSONB          NOT NULL DEFAULT '[]',

    -- ─── Integración con YOLO ─────────────────────────────────────
    -- Estos campos conectan el modelo de IA con los productos reales.
    -- Cuando YOLO detecta una prenda, busca en esta tabla por yolo_class_name.
    yolo_class_id   INTEGER         UNIQUE,  -- ID numérico de clase en el modelo
    yolo_class_name VARCHAR(100)    UNIQUE,  -- nombre de clase (ej: "camisa_azul_rayada")

    -- Imágenes (array de rutas relativas a /media/products/)
    -- Se almacenan como JSONB: ["img1.jpg", "img2.jpg"]
    images          JSONB           NOT NULL DEFAULT '[]',

    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  products               IS 'Catálogo maestro de prendas';
COMMENT ON COLUMN products.sku           IS 'Stock Keeping Unit — código único interno de la tienda';
COMMENT ON COLUMN products.yolo_class_id IS 'ID numérico de clase en el modelo YOLO entrenado';
COMMENT ON COLUMN products.yolo_class_name IS 'Nombre de clase YOLO. Cuando la IA detecta una prenda, busca aquí';
COMMENT ON COLUMN products.images        IS 'Array JSON con rutas a imágenes: ["foto1.jpg", "foto2.jpg"]';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: product_variants — Tallas y colores por producto
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE product_variants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id      UUID            NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    size            VARCHAR(20),            -- "S", "M", "L", "XL", "28", "30", etc.
    color           VARCHAR(80),
    color_hex       CHAR(7),                -- "#FF5733" para mostrar en UI
    sku_variant     VARCHAR(120)    NOT NULL UNIQUE,
    price_modifier  NUMERIC(10,2)   NOT NULL DEFAULT 0,  -- ajuste sobre base_price
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Una talla+color no puede repetirse en el mismo producto
    CONSTRAINT uq_product_size_color UNIQUE (product_id, size, color)
);

COMMENT ON TABLE  product_variants              IS 'Variantes de producto: combinaciones de talla y color';
COMMENT ON COLUMN product_variants.price_modifier IS 'Se suma al base_price del producto. Puede ser negativo';
COMMENT ON COLUMN product_variants.sku_variant  IS 'SKU único para esta variante específica';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: inventory — Stock actual por variante
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE inventory (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_variant_id      UUID            NOT NULL UNIQUE REFERENCES product_variants(id) ON DELETE CASCADE,
    quantity_available      INTEGER         NOT NULL DEFAULT 0 CHECK (quantity_available >= 0),
    quantity_reserved       INTEGER         NOT NULL DEFAULT 0 CHECK (quantity_reserved >= 0),
    low_stock_threshold     INTEGER         NOT NULL DEFAULT 5,
    stock_status            stock_status    NOT NULL DEFAULT 'available',
    warehouse_location      VARCHAR(50),
    last_updated            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_by              UUID            REFERENCES users(id) ON DELETE SET NULL
);

COMMENT ON TABLE  inventory                    IS 'Stock en tiempo real por variante de producto';
COMMENT ON COLUMN inventory.quantity_available IS 'Unidades físicamente disponibles para venta';
COMMENT ON COLUMN inventory.quantity_reserved  IS 'Unidades en carritos activos (aún no vendidas)';
COMMENT ON COLUMN inventory.low_stock_threshold IS 'Alerta de bajo stock cuando quantity_available cae por debajo de este valor';

-- Vista calculada de stock real (disponible - reservado)
CREATE VIEW inventory_net AS
    SELECT
        i.id,
        i.product_variant_id,
        pv.product_id,
        pv.size,
        pv.color,
        p.name                                      AS product_name,
        p.sku                                       AS product_sku,
        i.quantity_available,
        i.quantity_reserved,
        (i.quantity_available - i.quantity_reserved) AS quantity_net,
        i.low_stock_threshold,
        i.stock_status,
        i.warehouse_location,
        CASE
            WHEN (i.quantity_available - i.quantity_reserved) <= 0             THEN 'out_of_stock'
            WHEN (i.quantity_available - i.quantity_reserved) <= i.low_stock_threshold THEN 'low_stock'
            ELSE 'in_stock'
        END                                         AS availability_status,
        i.last_updated
    FROM inventory i
    JOIN product_variants pv ON pv.id = i.product_variant_id
    JOIN products p          ON p.id  = pv.product_id;

COMMENT ON VIEW inventory_net IS 'Vista de stock real = disponible - reservado, con estado de stock';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: inventory_movements — Historial de movimientos de stock
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE inventory_movements (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_variant_id  UUID            NOT NULL REFERENCES product_variants(id) ON DELETE RESTRICT,
    movement_type       movement_type   NOT NULL,
    quantity_change     INTEGER         NOT NULL,   -- positivo=entrada, negativo=salida
    quantity_before     INTEGER         NOT NULL,
    quantity_after      INTEGER         NOT NULL,
    reference_id        UUID,                       -- ID de orden o carrito relacionado
    notes               TEXT,
    created_by          UUID            REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  inventory_movements              IS 'Registro inmutable de todos los cambios de inventario';
COMMENT ON COLUMN inventory_movements.quantity_change IS 'Positivo=entrada al stock, Negativo=salida del stock';
COMMENT ON COLUMN inventory_movements.reference_id    IS 'UUID de la orden o carrito que originó el movimiento';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: sessions — Sesiones de kiosko del cliente
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token   UUID            NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    client_user_id  UUID            REFERENCES users(id) ON DELETE SET NULL,
    station_id      VARCHAR(50),    -- identificador del kiosko físico: "KIOSKO-01"
    status          session_status  NOT NULL DEFAULT 'active',
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

COMMENT ON TABLE  sessions            IS 'Sesiones de uso del kiosko. Un cliente anónimo igual crea sesión';
COMMENT ON COLUMN sessions.station_id IS 'Identificador del kiosko físico donde se inició la sesión';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: carts — Carritos de compra
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE carts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID            NOT NULL REFERENCES sessions(id) ON DELETE RESTRICT,
    status          cart_status     NOT NULL DEFAULT 'building',
    payment_method  payment_method,
    submitted_at    TIMESTAMPTZ,    -- cuando el cliente apretó "enviar a caja"
    notes           TEXT,           -- comentarios opcionales del cliente
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  carts              IS 'Carrito de compra del cliente. Ciclo: building → submitted → processing → paid';
COMMENT ON COLUMN carts.submitted_at IS 'Se llena al pasar de building a submitted';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: cart_items — Ítems detectados en el carrito
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE cart_items (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id                 UUID            NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_id              UUID            NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_variant_id      UUID            REFERENCES product_variants(id) ON DELETE RESTRICT,
    quantity                INTEGER         NOT NULL DEFAULT 1 CHECK (quantity > 0),

    -- Precio snapshot: guardamos el precio al momento de agregar.
    -- Si el producto cambia de precio después, este ítem NO cambia.
    unit_price              NUMERIC(10,2)   NOT NULL,

    -- ─── Datos de la detección IA ─────────────────────────────────
    detection_confidence    NUMERIC(5,4)    CHECK (detection_confidence BETWEEN 0 AND 1),
    detection_image_path    TEXT,           -- ruta a la foto tomada por el cliente
    detection_bbox          JSONB,          -- bounding box: {"x":0.1,"y":0.2,"w":0.3,"h":0.4}

    -- El cliente puede confirmar o rechazar lo que detectó la IA
    confirmed               BOOLEAN         NOT NULL DEFAULT FALSE,
    added_at                TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  cart_items                     IS 'Prendas detectadas y agregadas al carrito por el cliente';
COMMENT ON COLUMN cart_items.unit_price          IS 'Snapshot del precio al momento de agregar. Inmutable después';
COMMENT ON COLUMN cart_items.detection_confidence IS 'Confianza del modelo YOLO: 0.0 (nada seguro) a 1.0 (100% seguro)';
COMMENT ON COLUMN cart_items.detection_image_path IS 'Foto tomada por el cliente para detectar la prenda';
COMMENT ON COLUMN cart_items.detection_bbox      IS 'Bounding box de la detección: {x, y, width, height} normalizados';
COMMENT ON COLUMN cart_items.confirmed           IS 'El cliente confirmó que la detección es correcta';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: payment_queue — Cola de pagos del administrador/cajero
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE payment_queue (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id         UUID            NOT NULL UNIQUE REFERENCES carts(id) ON DELETE CASCADE,
    queue_position  INTEGER         NOT NULL,       -- número en la cola (1, 2, 3...)
    priority        queue_priority  NOT NULL DEFAULT 'normal',
    status          queue_status    NOT NULL DEFAULT 'waiting',
    assigned_to     UUID            REFERENCES users(id) ON DELETE SET NULL,
    called_at       TIMESTAMPTZ,    -- cuando el cajero abrió este pedido
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  payment_queue              IS 'Cola de tarjetitas del cajero. Se puebla cuando el cliente envía el carrito';
COMMENT ON COLUMN payment_queue.queue_position IS 'Posición en la cola. Se recalcula automáticamente al insertar';
COMMENT ON COLUMN payment_queue.assigned_to  IS 'Cajero que está atendiendo este pedido';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: orders — Órdenes de venta (registro oficial post-pago)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE orders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id             UUID            NOT NULL UNIQUE REFERENCES carts(id) ON DELETE RESTRICT,
    order_number        VARCHAR(30)     NOT NULL UNIQUE, -- "ORD-20240115-00001"
    cashier_id          UUID            NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    -- Montos (todos en la moneda local)
    subtotal            NUMERIC(10,2)   NOT NULL,
    discount_amount     NUMERIC(10,2)   NOT NULL DEFAULT 0,
    tax_amount          NUMERIC(10,2)   NOT NULL DEFAULT 0,
    total_amount        NUMERIC(10,2)   NOT NULL,

    -- Detalles de pago
    payment_method      payment_method  NOT NULL,
    cash_received       NUMERIC(10,2),  -- si pagó en efectivo
    change_given        NUMERIC(10,2),  -- cambio entregado

    status              order_status    NOT NULL DEFAULT 'pending',
    notes               TEXT,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  orders              IS 'Registro oficial e inmutable de cada venta completada';
COMMENT ON COLUMN orders.order_number IS 'Número legible para el recibo: ORD-YYYYMMDD-#####';
COMMENT ON COLUMN orders.subtotal     IS 'Suma de unit_price * quantity de todos los order_items';
COMMENT ON COLUMN orders.total_amount IS 'subtotal - discount_amount + tax_amount';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: order_items — Snapshot de lo que se vendió en cada orden
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE order_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id            UUID            NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id          UUID            NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_variant_id  UUID            REFERENCES product_variants(id) ON DELETE RESTRICT,

    -- Snapshot completo al momento de la venta
    product_name        VARCHAR(200)    NOT NULL,   -- snapshot del nombre
    variant_description VARCHAR(100),               -- snapshot "Talla M - Azul"
    quantity            INTEGER         NOT NULL CHECK (quantity > 0),
    unit_price          NUMERIC(10,2)   NOT NULL,
    discount_applied    NUMERIC(10,2)   NOT NULL DEFAULT 0,
    subtotal            NUMERIC(10,2)   NOT NULL    -- (unit_price - discount) * quantity
);

COMMENT ON TABLE  order_items                 IS 'Snapshot inmutable de cada ítem vendido. No cambia aunque el producto se modifique';
COMMENT ON COLUMN order_items.product_name    IS 'Nombre del producto al momento de la venta (snapshot)';
COMMENT ON COLUMN order_items.variant_description IS 'Descripción de la variante al momento de la venta (snapshot)';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: receipts — Recibos generados
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE receipts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id        UUID            NOT NULL UNIQUE REFERENCES orders(id) ON DELETE RESTRICT,
    receipt_number  VARCHAR(30)     NOT NULL UNIQUE, -- "REC-20240115-00001"
    receipt_data    JSONB           NOT NULL,         -- snapshot completo del recibo en JSON
    pdf_path        TEXT,                            -- ruta al PDF si se imprimió
    printed_at      TIMESTAMPTZ,
    emailed_to      VARCHAR(255),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  receipts              IS 'Recibos generados por cada venta. receipt_data preserva el recibo completo en JSON';
COMMENT ON COLUMN receipts.receipt_data IS 'JSON con todos los datos del recibo: tienda, productos, montos, cajero, fecha';
COMMENT ON COLUMN receipts.pdf_path     IS 'Ruta relativa a /media/receipts/ del PDF generado';


-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: daily_sales_summary — Resúmenes diarios precalculados para dashboard
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE daily_sales_summary (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    summary_date                DATE            NOT NULL UNIQUE,
    total_orders                INTEGER         NOT NULL DEFAULT 0,
    total_revenue               NUMERIC(12,2)   NOT NULL DEFAULT 0,
    total_items_sold            INTEGER         NOT NULL DEFAULT 0,
    average_order_value         NUMERIC(10,2)   GENERATED ALWAYS AS (
                                    CASE WHEN total_orders > 0
                                         THEN total_revenue / total_orders
                                         ELSE 0 END
                                ) STORED,
    payment_method_breakdown    JSONB           NOT NULL DEFAULT '{}',  -- {"cash": 5000, "card": 8000}
    top_products                JSONB           NOT NULL DEFAULT '[]',  -- [{product_id, name, qty, revenue}]
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE daily_sales_summary IS 'Resúmenes diarios precalculados. El dashboard los lee en vez de hacer queries pesadas';
COMMENT ON COLUMN daily_sales_summary.top_products IS 'Array JSON: [{product_id, name, quantity_sold, revenue}]';


-- ═══════════════════════════════════════════════════════════════════════════
--  ÍNDICES — Para acelerar las consultas más frecuentes
-- ═══════════════════════════════════════════════════════════════════════════

-- Búsqueda de productos por nombre (búsqueda de texto)
CREATE INDEX idx_products_name_trgm ON products USING GIN (name gin_trgm_ops);
CREATE INDEX idx_products_category  ON products (category_id);
CREATE INDEX idx_products_yolo      ON products (yolo_class_name) WHERE yolo_class_name IS NOT NULL;
CREATE INDEX idx_products_active    ON products (is_active) WHERE is_active = TRUE;

-- Variantes
CREATE INDEX idx_variants_product ON product_variants (product_id);

-- Inventario
CREATE INDEX idx_inventory_variant ON inventory (product_variant_id);

-- Movimientos de inventario
CREATE INDEX idx_movements_variant    ON inventory_movements (product_variant_id);
CREATE INDEX idx_movements_created_at ON inventory_movements (created_at DESC);
CREATE INDEX idx_movements_type       ON inventory_movements (movement_type);

-- Sesiones
CREATE INDEX idx_sessions_token  ON sessions (session_token);
CREATE INDEX idx_sessions_status ON sessions (status) WHERE status = 'active';

-- Carritos
CREATE INDEX idx_carts_session ON carts (session_id);
CREATE INDEX idx_carts_status  ON carts (status);

-- Cart items
CREATE INDEX idx_cart_items_cart    ON cart_items (cart_id);
CREATE INDEX idx_cart_items_product ON cart_items (product_id);

-- Cola de pagos — el cajero necesita ver los waiting ordenados
CREATE INDEX idx_queue_status_position ON payment_queue (status, queue_position)
    WHERE status = 'waiting';

-- Órdenes
CREATE INDEX idx_orders_cashier    ON orders (cashier_id);
CREATE INDEX idx_orders_created_at ON orders (created_at DESC);
CREATE INDEX idx_orders_status     ON orders (status);
CREATE INDEX idx_orders_number     ON orders (order_number);

-- Order items — para los reportes de productos más vendidos
CREATE INDEX idx_order_items_order   ON order_items (order_id);
CREATE INDEX idx_order_items_product ON order_items (product_id);

-- Resumen diario
CREATE INDEX idx_daily_summary_date ON daily_sales_summary (summary_date DESC);

-- Usuarios
CREATE INDEX idx_users_email  ON users (email);
CREATE INDEX idx_users_role   ON users (role);

-- Suppliers
CREATE INDEX idx_suppliers_active ON suppliers (is_active) WHERE is_active = TRUE;

-- Attribute options
CREATE INDEX idx_attribute_options_type ON attribute_options (type);
CREATE INDEX idx_attribute_options_active ON attribute_options (is_active) WHERE is_active = TRUE;

-- Product attributes
CREATE INDEX idx_product_attributes_product ON product_attributes (product_id);
CREATE INDEX idx_product_attributes_option ON product_attributes (attribute_option_id);

-- Price history
CREATE INDEX idx_price_history_product ON price_history (product_id);
CREATE INDEX idx_price_history_created_at ON price_history (created_at DESC);

-- Inventory - nuevos índices para campos nuevos
CREATE INDEX idx_inventory_status ON inventory (stock_status);
CREATE INDEX idx_inventory_location ON inventory (warehouse_location) WHERE warehouse_location IS NOT NULL;


-- ═══════════════════════════════════════════════════════════════════════════
--  TRIGGERS — Automatizaciones
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Función genérica para actualizar updated_at ─────────────────────────────
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar a todas las tablas con updated_at
CREATE TRIGGER set_updated_at_users
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_products
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_carts
    BEFORE UPDATE ON carts
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_payment_queue
    BEFORE UPDATE ON payment_queue
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_daily_summary
    BEFORE UPDATE ON daily_sales_summary
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- ─── Trigger: auto-generar queue_position al insertar en cola ────────────────
CREATE OR REPLACE FUNCTION trigger_set_queue_position()
RETURNS TRIGGER AS $$
BEGIN
    -- Asigna el siguiente número en la cola solo para carritos 'waiting'
    SELECT COALESCE(MAX(queue_position), 0) + 1
    INTO NEW.queue_position
    FROM payment_queue
    WHERE status = 'waiting';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_queue_position
    BEFORE INSERT ON payment_queue
    FOR EACH ROW EXECUTE FUNCTION trigger_set_queue_position();


-- ─── Trigger: marcar submitted_at cuando el carrito pasa a 'submitted' ────────
CREATE OR REPLACE FUNCTION trigger_cart_submitted_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'submitted' AND OLD.status = 'building' THEN
        NEW.submitted_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER cart_submitted_at
    BEFORE UPDATE ON carts
    FOR EACH ROW EXECUTE FUNCTION trigger_cart_submitted_at();


-- ─── Trigger: marcar completed_at en la orden cuando se completa ─────────────
CREATE OR REPLACE FUNCTION trigger_order_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        NEW.completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_completed_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION trigger_order_completed_at();


-- ─── Función: generar número de orden legible ─────────────────────────────────
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TEXT AS $$
DECLARE
    today_str   TEXT;
    count_today INTEGER;
BEGIN
    today_str   := TO_CHAR(NOW(), 'YYYYMMDD');
    SELECT COUNT(*) + 1 INTO count_today
    FROM orders
    WHERE created_at::DATE = NOW()::DATE;

    RETURN 'ORD-' || today_str || '-' || LPAD(count_today::TEXT, 5, '0');
END;
$$ LANGUAGE plpgsql;

-- ─── Función: generar número de recibo ────────────────────────────────────────
CREATE OR REPLACE FUNCTION generate_receipt_number()
RETURNS TEXT AS $$
DECLARE
    today_str    TEXT;
    count_today  INTEGER;
BEGIN
    today_str   := TO_CHAR(NOW(), 'YYYYMMDD');
    SELECT COUNT(*) + 1 INTO count_today
    FROM receipts
    WHERE created_at::DATE = NOW()::DATE;

    RETURN 'REC-' || today_str || '-' || LPAD(count_today::TEXT, 5, '0');
END;
$$ LANGUAGE plpgsql;


-- ═══════════════════════════════════════════════════════════════════════════
--  VISTAS PARA EL DASHBOARD
-- ═══════════════════════════════════════════════════════════════════════════

-- Vista: ventas de hoy
CREATE VIEW dashboard_today AS
    SELECT
        COUNT(o.id)                         AS total_orders,
        COALESCE(SUM(o.total_amount), 0)    AS total_revenue,
        COALESCE(SUM(oi.total_items), 0)    AS total_items_sold
    FROM orders o
    LEFT JOIN (
        SELECT order_id, SUM(quantity) AS total_items
        FROM order_items
        GROUP BY order_id
    ) oi ON oi.order_id = o.id
    WHERE o.status = 'completed'
      AND o.completed_at::DATE = NOW()::DATE;

-- Vista: productos más vendidos (últimos 30 días)
CREATE VIEW dashboard_top_products AS
    SELECT
        p.id                                AS product_id,
        p.name                              AS product_name,
        c.name                              AS category_name,
        SUM(oi.quantity)                    AS total_quantity_sold,
        SUM(oi.subtotal)                    AS total_revenue,
        COUNT(DISTINCT o.id)                AS order_count
    FROM order_items oi
    JOIN orders o   ON o.id  = oi.order_id
    JOIN products p ON p.id  = oi.product_id
    JOIN categories c ON c.id = p.category_id
    WHERE o.status = 'completed'
      AND o.completed_at >= NOW() - INTERVAL '30 days'
    GROUP BY p.id, p.name, c.name
    ORDER BY total_quantity_sold DESC;

-- Vista: cola de pagos activa (lo que el cajero ve)
CREATE VIEW active_payment_queue AS
    SELECT
        pq.id               AS queue_id,
        pq.queue_position,
        pq.priority,
        pq.status,
        pq.created_at       AS submitted_at,
        c.id                AS cart_id,
        c.notes             AS cart_notes,
        s.station_id,
        COUNT(ci.id)        AS item_count,
        SUM(ci.unit_price * ci.quantity) AS estimated_total
    FROM payment_queue pq
    JOIN carts c        ON c.id  = pq.cart_id
    JOIN sessions s     ON s.id  = c.session_id
    LEFT JOIN cart_items ci ON ci.cart_id = c.id AND ci.confirmed = TRUE
    WHERE pq.status IN ('waiting', 'in_progress')
    GROUP BY pq.id, pq.queue_position, pq.priority, pq.status,
             pq.created_at, c.id, c.notes, s.station_id
    ORDER BY pq.priority DESC, pq.queue_position ASC;

COMMENT ON VIEW active_payment_queue IS 'Cola de pagos activa que ve el cajero en tiempo real';


-- ═══════════════════════════════════════════════════════════════════════════
--  PERMISOS — Usuario de la aplicación (solo lo necesario)
-- ═══════════════════════════════════════════════════════════════════════════

-- El usuario de la app NO es superusuario, solo tiene lo que necesita
GRANT USAGE ON SCHEMA public TO fashionvision_ai_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fashionvision_ai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fashionvision_ai_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fashionvision_ai_user;
