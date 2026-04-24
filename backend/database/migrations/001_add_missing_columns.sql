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
-- Add missing columns to inventory table
-- ============================================
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS stock_status VARCHAR(20) NOT NULL DEFAULT 'available';
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS warehouse_location VARCHAR(100);

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
    RAISE NOTICE 'Products table columns:';
    FOR col IN SELECT column_name FROM information_schema.columns WHERE table_name = 'products' ORDER BY ordinal_position LOOP
        RAISE NOTICE '  - %', col;
    END LOOP;
END $$;
