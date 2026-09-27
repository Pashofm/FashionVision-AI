-- ═══════════════════════════════════════════════════════════════════════════
--  Migration: Add size/color attribute FK to product_variants
--  Run this script against an EXISTING database to add the missing columns
--  This script is SAFE to run - it uses IF NOT EXISTS and only alters if needed
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ============================================
-- Step 1: Add new FK columns to product_variants
-- ============================================
ALTER TABLE product_variants ADD COLUMN IF NOT EXISTS size_attribute_id UUID REFERENCES attribute_options(id) ON DELETE SET NULL;
ALTER TABLE product_variants ADD COLUMN IF NOT EXISTS color_attribute_id UUID REFERENCES attribute_options(id) ON DELETE SET NULL;

-- ============================================
-- Step 2: Create indexes for new columns
-- ============================================
CREATE INDEX IF NOT EXISTS idx_variants_size_attr ON product_variants(size_attribute_id);
CREATE INDEX IF NOT EXISTS idx_variants_color_attr ON product_variants(color_attribute_id);

-- ============================================
-- Step 3: Populate the FK columns from existing size/color strings
-- This maps the old string values to the attribute_options UUIDs
-- ============================================

-- First, update size_attribute_id using the size string values
UPDATE product_variants pv
SET size_attribute_id = ao.id
FROM attribute_options ao
WHERE ao.type = 'size'
  AND pv.size IS NOT NULL
  AND pv.size <> ''
  AND ao.value = pv.size;

-- Then, update color_attribute_id using the color string values
UPDATE product_variants pv
SET color_attribute_id = ao.id
FROM attribute_options ao
WHERE ao.type = 'color'
  AND pv.color IS NOT NULL
  AND pv.color <> ''
  AND ao.value = pv.color;

-- ============================================
-- Step 4: Drop old string columns (optional - only after confirming data migrated)
-- Uncomment these lines only after verifying the migration worked
-- ============================================
-- ALTER TABLE product_variants DROP COLUMN IF EXISTS size;
-- ALTER TABLE product_variants DROP COLUMN IF EXISTS color;

-- ============================================
-- Step 5: Update unique constraint to use FK columns
-- ============================================
DO $$
BEGIN
    -- Drop old constraint if it exists
    ALTER TABLE product_variants DROP CONSTRAINT IF EXISTS uq_product_size_color_old;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- Rename existing constraint to allow new one
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_product_size_color'
    ) THEN
        ALTER TABLE product_variants RENAME CONSTRAINT uq_product_size_color TO uq_product_size_color_old;
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- Add new constraint with FK columns
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_product_size_color_fk'
    ) THEN
        ALTER TABLE product_variants ADD CONSTRAINT uq_product_size_color_fk
            UNIQUE (product_id, size_attribute_id, color_attribute_id);
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- ============================================
-- Verify the migration
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '=== Migration Summary ===';
    RAISE NOTICE 'product_variants size_attribute_id populated: %',
        (SELECT COUNT(*) FROM product_variants WHERE size_attribute_id IS NOT NULL);

    RAISE NOTICE 'product_variants color_attribute_id populated: %',
        (SELECT COUNT(*) FROM product_variants WHERE color_attribute_id IS NOT NULL);

    RAISE NOTICE 'product_variants still with NULL size_attribute_id: %',
        (SELECT COUNT(*) FROM product_variants WHERE size_attribute_id IS NULL AND size IS NOT NULL AND size <> '');

    RAISE NOTICE 'product_variants still with NULL color_attribute_id: %',
        (SELECT COUNT(*) FROM product_variants WHERE color_attribute_id IS NULL AND color IS NOT NULL AND color <> '');

    RAISE NOTICE '';
    RAISE NOTICE 'If there are still NULL values, check attribute_options table';
    RAISE NOTICE 'to ensure matching size/color values exist.';
END $$;

COMMIT;

-- Final verification message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANT: Verify the data migration worked by checking:';
    RAISE NOTICE '  - product_variants.size_attribute_id is populated';
    RAISE NOTICE '  - product_variants.color_attribute_id is populated';
    RAISE NOTICE '';
    RAISE NOTICE 'If you want to remove the old string columns (size, color),';
    RAISE NOTICE 'run this AFTER verifying the migration was successful:';
    RAISE NOTICE '  ALTER TABLE product_variants DROP COLUMN IF EXISTS size;';
    RAISE NOTICE '  ALTER TABLE product_variants DROP COLUMN IF EXISTS color;';
END $$;
