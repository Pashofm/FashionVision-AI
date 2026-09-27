-- Rollback Script: Remove migration changes
-- WARNING: This will remove data! Use only for development/testing.

BEGIN;

-- Remove new tables
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS product_attributes CASCADE;
DROP TABLE IF EXISTS attribute_options CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;

-- Remove new columns from payment_queue (added to schema.sql)
ALTER TABLE payment_queue DROP COLUMN IF EXISTS assigned_to;
ALTER TABLE payment_queue DROP COLUMN IF EXISTS called_at;

-- Remove new columns from inventory
ALTER TABLE inventory DROP COLUMN IF EXISTS stock_status;
ALTER TABLE inventory DROP COLUMN IF EXISTS warehouse_location;

-- Remove new columns from users
ALTER TABLE users DROP COLUMN IF EXISTS last_logout_at;

-- Remove columns from order_items
ALTER TABLE order_items DROP COLUMN IF EXISTS product_id;
ALTER TABLE order_items DROP COLUMN IF EXISTS product_name;
ALTER TABLE order_items DROP COLUMN IF EXISTS variant_description;
ALTER TABLE order_items DROP COLUMN IF EXISTS discount_applied;
ALTER TABLE order_items DROP COLUMN IF EXISTS subtotal;

-- Remove indexes
DROP INDEX IF EXISTS idx_products_cost_price;
DROP INDEX IF EXISTS idx_products_brand;
DROP INDEX IF EXISTS idx_products_supplier;
DROP INDEX IF EXISTS idx_products_barcode;
DROP INDEX IF EXISTS idx_inventory_stock_status;
DROP INDEX IF EXISTS idx_inventory_warehouse_location;
DROP INDEX IF EXISTS idx_attribute_options_type;
DROP INDEX IF EXISTS idx_product_attributes_product_id;
DROP INDEX IF EXISTS idx_cart_items_product_id;

-- Remove columns from products (WARNING: data loss)
ALTER TABLE products DROP COLUMN IF EXISTS cost_price;
ALTER TABLE products DROP COLUMN IF EXISTS tax_rate;
ALTER TABLE products DROP COLUMN IF EXISTS profit_margin;
ALTER TABLE products DROP COLUMN IF EXISTS brand;
ALTER TABLE products DROP COLUMN IF EXISTS supplier;
ALTER TABLE products DROP COLUMN IF EXISTS barcode;
ALTER TABLE products DROP COLUMN IF EXISTS weight;
ALTER TABLE products DROP COLUMN IF EXISTS width;
ALTER TABLE products DROP COLUMN IF EXISTS height;
ALTER TABLE products DROP COLUMN IF EXISTS depth;
ALTER TABLE products DROP COLUMN IF EXISTS min_stock_level;
ALTER TABLE products DROP COLUMN IF EXISTS max_stock_level;
ALTER TABLE products DROP COLUMN IF EXISTS is_featured;
ALTER TABLE products DROP COLUMN IF EXISTS tags;

COMMIT;

DO $$
BEGIN
    RAISE NOTICE 'Rollback completed!';
END $$;
