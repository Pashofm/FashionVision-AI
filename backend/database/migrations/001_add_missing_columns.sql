-- Migration Script: Add missing columns to existing database
-- Run this script against your PostgreSQL database to apply schema changes
-- This script is idempotent - safe to run multiple times

BEGIN;

-- ============================================
-- Add missing columns to users table
-- ============================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_logout_at TIMESTAMPTZ;

-- ============================================
-- Add missing columns to products table
-- ============================================
ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price NUMERIC(10,2) NOT NULL DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS tax_rate NUMERIC(5,4) NOT NULL DEFAULT 0.16;
ALTER TABLE products ADD COLUMN IF NOT EXISTS profit_margin NUMERIC(5,4) NOT NULL DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS supplier VARCHAR(150);
ALTER TABLE products ADD COLUMN IF NOT EXISTS barcode VARCHAR(50) UNIQUE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS weight NUMERIC(8,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS width NUMERIC(8,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS height NUMERIC(8,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS depth NUMERIC(8,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS min_stock_level INTEGER NOT NULL DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS max_stock_level INTEGER;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]';

-- ============================================
-- Add missing columns to carts table
-- ============================================
ALTER TABLE carts ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) NOT NULL DEFAULT 'cash';
ALTER TABLE carts ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ;

-- ============================================
-- Add missing columns to sessions table
-- ============================================
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS session_token UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS client_user_id UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ;

-- Rename existing columns in sessions to match model (only if they exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sessions' AND column_name = 'last_activity') THEN
        ALTER TABLE sessions RENAME COLUMN last_activity TO last_activity_at;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sessions' AND column_name = 'user_id') THEN
        ALTER TABLE sessions RENAME COLUMN user_id TO client_user_id;
    END IF;
    ALTER TABLE sessions DROP COLUMN IF EXISTS expires_at;
END $$;

-- ============================================
-- Create suppliers table
-- ============================================
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- Create attribute_options table
-- ============================================
CREATE TABLE IF NOT EXISTS attribute_options (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(20) NOT NULL CHECK (type IN ('size', 'color')),
    value VARCHAR(50) NOT NULL,
    hex_code VARCHAR(7),
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- Create product_attributes table
-- ============================================
CREATE TABLE IF NOT EXISTS product_attributes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    attribute_option_id UUID NOT NULL REFERENCES attribute_options(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- Create price_history table
-- ============================================
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price_type VARCHAR(20) NOT NULL,
    old_price NUMERIC(10,2),
    new_price NUMERIC(10,2) NOT NULL,
    changed_by UUID REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- Add missing columns to order_items table
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'order_items' AND column_name = 'product_id') THEN
        ALTER TABLE order_items ADD COLUMN product_id UUID DEFAULT '00000000-0000-0000-0000-000000000000';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'order_items' AND column_name = 'product_name') THEN
        ALTER TABLE order_items ADD COLUMN product_name VARCHAR(200);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'order_items' AND column_name = 'variant_description') THEN
        ALTER TABLE order_items ADD COLUMN variant_description VARCHAR(100);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'order_items' AND column_name = 'discount_applied') THEN
        ALTER TABLE order_items ADD COLUMN discount_applied NUMERIC(10,2) NOT NULL DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'order_items' AND column_name = 'subtotal') THEN
        ALTER TABLE order_items ADD COLUMN subtotal NUMERIC(10,2) NOT NULL DEFAULT 0;
    END IF;
END $$;

-- Backfill product_id from product_variants product_id (only if product_id is nullable)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'order_items' AND column_name = 'product_id' AND is_nullable = 'YES') THEN
        UPDATE order_items SET product_id = sub.product_id 
        FROM (SELECT pv.id as variant_id, pv.product_id FROM product_variants pv) AS sub 
        WHERE order_items.product_variant_id = sub.variant_id AND order_items.product_id IS NULL;
        
        ALTER TABLE order_items ALTER COLUMN product_id SET NOT NULL;
    END IF;
END $$;

-- ============================================
-- Create indexes for better performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_products_yolo_class_name ON products(yolo_class_name);
CREATE INDEX IF NOT EXISTS idx_products_cost_price ON products(cost_price);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_inventory_stock_status ON inventory(stock_status);
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse_location ON inventory(warehouse_location);
CREATE INDEX IF NOT EXISTS idx_attribute_options_type ON attribute_options(type);
CREATE INDEX IF NOT EXISTS idx_product_attributes_product_id ON product_attributes(product_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_product_id ON cart_items(product_id);

-- ============================================
-- Add missing columns to cart_items table
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cart_items' AND column_name = 'product_id') THEN
        ALTER TABLE cart_items ADD COLUMN product_id UUID NOT NULL REFERENCES products(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cart_items' AND column_name = 'detection_confidence') THEN
        ALTER TABLE cart_items ADD COLUMN detection_confidence FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cart_items' AND column_name = 'detection_image_path') THEN
        ALTER TABLE cart_items ADD COLUMN detection_image_path TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cart_items' AND column_name = 'detection_bbox') THEN
        ALTER TABLE cart_items ADD COLUMN detection_bbox JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cart_items' AND column_name = 'added_at') THEN
        ALTER TABLE cart_items ADD COLUMN added_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    END IF;
END $$;

-- ============================================
-- Add missing columns to orders table
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'cart_id') THEN
        ALTER TABLE orders ADD COLUMN cart_id UUID NOT NULL REFERENCES carts(id) UNIQUE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'payment_method') THEN
        ALTER TABLE orders ADD COLUMN payment_method VARCHAR(20) NOT NULL DEFAULT 'cash';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'cash_received') THEN
        ALTER TABLE orders ADD COLUMN cash_received NUMERIC(10,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'change_given') THEN
        ALTER TABLE orders ADD COLUMN change_given NUMERIC(10,2);
    END IF;
END $$;

-- ============================================
-- Add missing columns to receipts table
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'receipts' AND column_name = 'receipt_data') THEN
        ALTER TABLE receipts ADD COLUMN receipt_data JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'receipts' AND column_name = 'pdf_path') THEN
        ALTER TABLE receipts ADD COLUMN pdf_path VARCHAR(255);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'receipts' AND column_name = 'emailed_to') THEN
        ALTER TABLE receipts ADD COLUMN emailed_to VARCHAR(255);
    END IF;
END $$;

-- ============================================
-- Add unique constraints (if not already existing)
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_attribute_type_value'
    ) THEN
        ALTER TABLE attribute_options ADD CONSTRAINT uq_attribute_type_value UNIQUE (type, value);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_product_attribute'
    ) THEN
        ALTER TABLE product_attributes ADD CONSTRAINT uq_product_attribute UNIQUE (product_id, attribute_option_id);
    END IF;
END $$;

COMMIT;

-- Verify the migration
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
END $$;
