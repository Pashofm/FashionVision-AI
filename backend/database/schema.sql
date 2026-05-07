-- ═══════════════════════════════════════════════════════════════════════════
--  FashionVision-AI — Esquema completo de base de datos
--  Sistema POS con detección YOLO para tiendas de ropa
--  PostgreSQL 16+
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
--  EXTENSIONES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ─────────────────────────────────────────────────────────────────────────────
--  ENUMS — Tipos enumerados
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('admin', 'cashier', 'client');

CREATE TYPE cart_status AS ENUM (
    'building',     -- el cliente está agregando prendas
    'submitted',     -- el cliente mandó el carrito al admin
    'processing',    -- el admin lo está procesando en caja
    'paid',          -- pago completado
    'cancelled'      -- cancelado
);

CREATE TYPE order_status AS ENUM (
    'pending',
    'completed',
    'refunded',
    'partially_refunded'
);

CREATE TYPE payment_method AS ENUM ('cash', 'card', 'mixed');

CREATE TYPE queue_status AS ENUM (
    'waiting',
    'in_progress',
    'completed',
    'skipped'
);

CREATE TYPE queue_priority AS ENUM ('normal', 'urgent');

CREATE TYPE movement_type AS ENUM (
    'sale',
    'restock',
    'adjustment',
    'return',
    'reserved',
    'released'
);

CREATE TYPE session_status AS ENUM ('active', 'completed', 'abandoned');

CREATE TYPE stock_status AS ENUM ('available', 'reserved', 'damaged', 'in_transit', 'returned');

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: users — Usuarios del sistema
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(150)    NOT NULL,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    role            user_role      NOT NULL DEFAULT 'cashier',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    avatar_path     TEXT,
    last_logout_at  TIMESTAMPTZ,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE users IS 'Usuarios del sistema: admins, cashiers, clients';
COMMENT ON COLUMN users.role IS 'admin=tiene acceso total, cashier=opera POS, client=usa kiosco';

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: categories — Categorías de ropa
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100)    NOT NULL UNIQUE,
    description TEXT,
    icon        VARCHAR(50),
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE categories IS 'Categorías de ropa: Camisas, Pantalones, Vestidos, etc.';

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: store_config — Configuración de la tienda
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE store_config (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_name             VARCHAR(200)     NOT NULL DEFAULT 'FashionVision AI',
    legal_name              VARCHAR(255),
    address                 TEXT,
    phone                   VARCHAR(20),
    email                   VARCHAR(255),
    tax_id                  VARCHAR(50),
    website                 VARCHAR(255),
    default_currency        VARCHAR(3)       NOT NULL DEFAULT 'MXN',
    default_payment_method  payment_method    NOT NULL DEFAULT 'cash',
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
--  TABLA: attribute_options — Catálogo de tallas y colores
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE attribute_options (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type        VARCHAR(20)     NOT NULL CHECK (type IN ('size', 'color')),
    value       VARCHAR(50)     NOT NULL,
    hex_code    CHAR(7),
    sort_order  INTEGER         NOT NULL DEFAULT 0,
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_attribute_type_value UNIQUE (type, value)
);

COMMENT ON TABLE attribute_options IS 'Catálogo de tallas y colores predefinidos';
COMMENT ON COLUMN attribute_options.type IS 'Tipo de atributo: size o color';
COMMENT ON COLUMN attribute_options.value IS 'Valor: "S", "M", "L", "Rojo", "Azul"';
COMMENT ON COLUMN attribute_options.hex_code IS 'Código hex para colores: "#FF5733"';

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: products — Catálogo de prendas
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id     UUID            NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name            VARCHAR(200)    NOT NULL,
    description     TEXT,
    sku             VARCHAR(100)    NOT NULL UNIQUE,
    base_price      NUMERIC(10,2)   NOT NULL CHECK (base_price >= 0),
    cost_price      NUMERIC(10,2)   NOT NULL DEFAULT 0 CHECK (cost_price >= 0),
    tax_rate        NUMERIC(5,4)    NOT NULL DEFAULT 0.16 CHECK (tax_rate >= 0 AND tax_rate <= 1),
    profit_margin   NUMERIC(5,4)    NOT NULL DEFAULT 0 CHECK (profit_margin >= 0 AND profit_margin <= 1),
    brand           VARCHAR(100),
    supplier        VARCHAR(150),
    barcode         VARCHAR(50)    UNIQUE,
    weight          NUMERIC(8,2),
    width           NUMERIC(8,2),
    height          NUMERIC(8,2),
    depth           NUMERIC(8,2),
    min_stock_level INTEGER         NOT NULL DEFAULT 0,
    max_stock_level INTEGER,
    is_featured     BOOLEAN         NOT NULL DEFAULT FALSE,
    tags            JSONB           NOT NULL DEFAULT '[]',
    yolo_class_id   INTEGER         UNIQUE,
    yolo_class_name VARCHAR(100)    UNIQUE,
    images          JSONB           NOT NULL DEFAULT '[]',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE products IS 'Catálogo maestro de prendas';
COMMENT ON COLUMN products.sku IS 'Stock Keeping Unit - código único interno';
COMMENT ON COLUMN products.yolo_class_name IS 'Nombre de clase YOLO para detección automática';

CREATE INDEX idx_products_name_trgm ON products USING GIN (name gin_trgm_ops);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_yolo ON products(yolo_class_name) WHERE yolo_class_name IS NOT NULL;
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE;

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: product_variants — Variantes (talla + color)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE product_variants (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id          UUID            NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    size_attribute_id  UUID            REFERENCES attribute_options(id) ON DELETE SET NULL,
    color_attribute_id UUID            REFERENCES attribute_options(id) ON DELETE SET NULL,
    color_hex           CHAR(7),
    sku_variant         VARCHAR(150)    NOT NULL UNIQUE,
    price_modifier      NUMERIC(10,2)   NOT NULL DEFAULT 0,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_product_size_color UNIQUE (product_id, size_attribute_id, color_attribute_id)
);

COMMENT ON TABLE product_variants IS 'Variantes: combina talla + color por producto';

CREATE INDEX idx_variants_product ON product_variants(product_id);
CREATE INDEX idx_variants_sku ON product_variants(sku_variant);
CREATE INDEX idx_variants_size ON product_variants(size_attribute_id);
CREATE INDEX idx_variants_color ON product_variants(color_attribute_id);

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

COMMENT ON TABLE price_history IS 'Registro de todos los cambios de precio';
COMMENT ON COLUMN price_history.price_type IS 'cost=costo, base=venta, special=oferta';

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: inventory — Stock por variante
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE inventory (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_variant_id  UUID            NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    quantity_available  INTEGER         NOT NULL DEFAULT 0 CHECK (quantity_available >= 0),
    quantity_reserved   INTEGER         NOT NULL DEFAULT 0 CHECK (quantity_reserved >= 0),
    low_stock_threshold INTEGER         NOT NULL DEFAULT 5,
    stock_status        stock_status    NOT NULL DEFAULT 'available',
    warehouse_location  VARCHAR(100),
    last_updated        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_by          UUID            REFERENCES users(id) ON DELETE SET NULL
);

COMMENT ON TABLE inventory IS 'Stock disponible y reservado por variante';
COMMENT ON COLUMN inventory.stock_status IS 'available, reserved, damaged, in_transit, returned';

CREATE INDEX idx_inventory_variant ON inventory(product_variant_id);
CREATE INDEX idx_inventory_status ON inventory(stock_status);
CREATE INDEX idx_inventory_low_stock ON inventory(low_stock_threshold) WHERE quantity_available <= low_stock_threshold;

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: inventory_movements — Bitácora de movimientos
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE inventory_movements (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_variant_id  UUID            NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    movement_type       movement_type   NOT NULL,
    quantity_change     INTEGER         NOT NULL,
    quantity_before     INTEGER         NOT NULL,
    quantity_after      INTEGER         NOT NULL,
    reference_id        UUID,
    notes               TEXT,
    created_by          UUID            REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE inventory_movements IS 'Bitácora: sales, restocks, returns, adjustments';
COMMENT ON COLUMN inventory_movements.movement_type IS 'sale, restock, adjustment, return, reserved, released';

CREATE INDEX idx_movements_variant ON inventory_movements(product_variant_id);
CREATE INDEX idx_movements_type ON inventory_movements(movement_type);
CREATE INDEX idx_movements_created_at ON inventory_movements(created_at DESC);
CREATE INDEX idx_movements_reference ON inventory_movements(reference_id) WHERE reference_id IS NOT NULL;

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: sessions — Sesiones de kiosco/cliente
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token   UUID            NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    client_user_id   UUID            REFERENCES users(id) ON DELETE SET NULL,
    station_id      VARCHAR(50),
    status          session_status  NOT NULL DEFAULT 'active',
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    ip_address      VARCHAR(45),
    user_agent      TEXT
);

COMMENT ON TABLE sessions IS 'Sesiones activas de usuarios en kioscos/POS';

CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_client_user ON sessions(client_user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: carts — Carritos de compra activos
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE carts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID            NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    status          cart_status     NOT NULL DEFAULT 'building',
    payment_method   payment_method  NOT NULL DEFAULT 'cash',
    submitted_at    TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE carts IS 'Carritos activos por sesión';

CREATE INDEX idx_carts_session ON carts(session_id);
CREATE INDEX idx_carts_status ON carts(status);

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: cart_items — Items en carrito
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE cart_items (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id               UUID            NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_id            UUID            NOT NULL REFERENCES products(id),
    product_variant_id    UUID            NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    quantity              INTEGER         NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price            NUMERIC(10,2)   NOT NULL,
    confirmed             BOOLEAN         NOT NULL DEFAULT FALSE,
    detected_class        VARCHAR(100),
    detection_confidence  FLOAT,
    detection_image_path  TEXT,
    detection_bbox        JSONB,
    added_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE cart_items IS 'Items dentro de un carrito';
COMMENT ON COLUMN cart_items.detected_class IS 'Clase YOLO que detectó esta prenda';
COMMENT ON COLUMN cart_items.detection_confidence IS 'Confianza de la detección YOLO';
COMMENT ON COLUMN cart_items.detection_image_path IS 'Ruta a la imagen de la detección';
COMMENT ON COLUMN cart_items.detection_bbox IS 'Bounding box de la detección YOLO';

CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);
CREATE INDEX idx_cart_items_variant ON cart_items(product_variant_id);
CREATE INDEX idx_cart_items_product ON cart_items(product_id);

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: orders — Órdenes completadas
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE orders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id             UUID            NOT NULL REFERENCES carts(id) UNIQUE,
    order_number        VARCHAR(50)    NOT NULL UNIQUE,
    session_id          UUID,
    cashier_id          UUID            REFERENCES users(id) ON DELETE SET NULL,
    subtotal           NUMERIC(10,2)   NOT NULL,
    tax_amount          NUMERIC(10,2)   NOT NULL DEFAULT 0,
    discount_amount     NUMERIC(10,2)   NOT NULL DEFAULT 0,
    total_amount        NUMERIC(10,2)   NOT NULL,
    payment_method      VARCHAR(20)     NOT NULL DEFAULT 'cash',
    cash_received       NUMERIC(10,2),
    change_given        NUMERIC(10,2),
    status              order_status    NOT NULL DEFAULT 'pending',
    notes               TEXT,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE orders IS 'Órdenes/compras completadas';

CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_cashier ON orders(cashier_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: order_items — Items de orden (snapshot)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE order_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id            UUID            NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id          UUID            NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_variant_id  UUID            NOT NULL REFERENCES product_variants(id) ON DELETE RESTRICT,
    quantity            INTEGER         NOT NULL CHECK (quantity > 0),
    unit_price          NUMERIC(10,2)   NOT NULL,
    cost_price          NUMERIC(10,2)   NOT NULL DEFAULT 0,
    discount            NUMERIC(10,2)   NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE order_items IS 'Snapshot de items vendidos';

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_variant ON order_items(product_variant_id);

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: receipts — Recibos generados
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE receipts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_number  VARCHAR(50)     NOT NULL UNIQUE,
    order_id        UUID            NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    receipt_data    JSONB,
    pdf_path        VARCHAR(255),
    printed_at      TIMESTAMPTZ,
    printer_name    VARCHAR(100),
    emailed_to      VARCHAR(255),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE receipts IS 'Registro de recibos impresos';

CREATE INDEX idx_receipts_order ON receipts(order_id);

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: payment_queue — Cola de pagos (POS)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE payment_queue (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id         UUID            NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    priority        queue_priority  NOT NULL DEFAULT 'normal',
    queue_position  INTEGER         NOT NULL DEFAULT 0,
    status          queue_status    NOT NULL DEFAULT 'waiting',
    station_id      VARCHAR(50),
    notes           TEXT,
    assigned_to     UUID            REFERENCES users(id),
    called_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE payment_queue IS 'Cola de pagos pendientes en el POS';

CREATE INDEX idx_payment_queue_status ON payment_queue(status);
CREATE INDEX idx_payment_queue_priority ON payment_queue(priority);
CREATE INDEX idx_payment_queue_status_position ON payment_queue(status, queue_position) WHERE status = 'waiting';

-- ─────────────────────────────────────────────────────────────────────────────
--  TABLA: daily_sales_summary — Resumen diario para dashboard
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE daily_sales_summary (
    id                        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    summary_date              DATE            NOT NULL UNIQUE,
    total_orders              INTEGER         NOT NULL DEFAULT 0,
    total_revenue             NUMERIC(12,2)   NOT NULL DEFAULT 0,
    total_items_sold          INTEGER         NOT NULL DEFAULT 0,
    payment_method_breakdown  JSONB           NOT NULL DEFAULT '{}',
    top_products              JSONB           NOT NULL DEFAULT '[]',
    created_at                TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE daily_sales_summary IS 'Resúmenes diarios precalculados para dashboards';

CREATE INDEX idx_daily_summary_date ON daily_sales_summary(summary_date DESC);

-- ═══════════════════════════════════════════════════════════════════════════
--  PERMISOS — Usuario de la aplicación
-- ═══════════════════════════════════════════════════════════════════════════
GRANT USAGE ON SCHEMA public TO fashionvision_ai_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fashionvision_ai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fashionvision_ai_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fashionvision_ai_user;