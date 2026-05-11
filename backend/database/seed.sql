-- ═══════════════════════════════════════════════════════════════════════════
--  AUTOCOBRO — Datos de prueba para desarrollo
--  Script corregido para coincidir con el esquema actual de la BD
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Usuarios de prueba ──────────────────────────────────────────────────────
-- Contraseña de todos: "admin123" (hash bcrypt)
INSERT INTO users (id, name, email, password_hash, role, is_active) VALUES
    ('a0000001-0000-0000-0000-000000000001', 'Admin Principal', 'admin@tienda.com', '$2b$12$jlMVt1QLHuZWsGK0u2fVTuBcKaf2WpZYpeL/kHLSULQ0VPMLJigfu', 'admin', TRUE),
    ('a0000001-0000-0000-0000-000000000002', 'Cajero Uno', 'cajero@tienda.com', '$2b$12$jlMVt1QLHuZWsGK0u2fVTuBcKaf2WpZYpeL/kHLSULQ0VPMLJigfu', 'cashier', TRUE),
    ('a0000001-0000-0000-0000-000000000003', 'Cliente Demo', 'cliente@demo.com', '$2b$12$jlMVt1QLHuZWsGK0u2fVTuBcKaf2WpZYpeL/kHLSULQ0VPMLJigfu', 'client', TRUE)
ON CONFLICT DO NOTHING;

-- ─── Categorías ──────────────────────────────────────────────────────────────
INSERT INTO categories (id, name, description, icon, is_active) VALUES
    ('c0000001-0000-0000-0000-000000000001', 'Camisas', 'Camisas y blusas para dama y caballero', 'shirt', TRUE),
    ('c0000001-0000-0000-0000-000000000002', 'Pantalones', 'Pantalones de vestir, jeans y casuales', 'layers', TRUE),
    ('c0000001-0000-0000-0000-000000000003', 'Vestidos', 'Vestidos casuales y de ocasión especial', 'sparkles', TRUE),
    ('c0000001-0000-0000-0000-000000000004', 'Playeras', 'Playeras, camisetas y tops', 'tag', TRUE),
    ('c0000001-0000-0000-0000-000000000005', 'Accesorios', 'Cinturones, gorras, bufandas y más', 'gem', TRUE)
ON CONFLICT DO NOTHING;

-- ─── Atributos (tallas y colores) ───────────────────────────────────────────
INSERT INTO attribute_options (id, type, value, hex_code, sort_order, is_active) VALUES
    -- Tallas
    ('e0000001-0000-0000-0000-000000000001', 'size', 'XS', NULL, 1, TRUE),
    ('e0000001-0000-0000-0000-000000000002', 'size', 'S', NULL, 2, TRUE),
    ('e0000001-0000-0000-0000-000000000003', 'size', 'M', NULL, 3, TRUE),
    ('e0000001-0000-0000-0000-000000000004', 'size', 'L', NULL, 4, TRUE),
    ('e0000001-0000-0000-0000-000000000005', 'size', 'XL', NULL, 5, TRUE),
    ('e0000001-0000-0000-0000-000000000006', 'size', 'XXL', NULL, 6, TRUE),
    ('e0000001-0000-0000-0000-000000000020', 'size', 'One Size', NULL, 12, TRUE),
    -- Colores
    ('e0000001-0000-0000-0000-000000000012', 'color', 'Azul Marino', '#1B2A4A', 1, TRUE),
    ('e0000001-0000-0000-0000-000000000013', 'color', 'Negro', '#1C1C1C', 2, TRUE),
    ('e0000001-0000-0000-0000-000000000014', 'color', 'Blanco', '#FFFFFF', 3, TRUE),
    ('e0000001-0000-0000-0000-000000000015', 'color', 'Gris', '#6B7280', 4, TRUE),
    ('e0000001-0000-0000-0000-000000000016', 'color', 'Rojo', '#DC2626', 5, TRUE),
    ('e0000001-0000-0000-0000-000000000017', 'color', 'Azul', '#3B82F6', 6, TRUE),
    ('e0000001-0000-0000-0000-000000000018', 'color', 'Verde', '#22C55E', 7, TRUE)
ON CONFLICT DO NOTHING;

-- ─── Productos ───────────────────────────────────────────────────────────────
INSERT INTO products (id, category_id, name, description, sku, base_price, cost_price, tax_rate, profit_margin, brand, supplier, barcode, weight, width, height, depth, min_stock_level, max_stock_level, is_featured, tags, yolo_class_id, yolo_class_name, images, is_active) VALUES
    ('b0000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000005',
     'Gorra Roja Lacoste',
     'Gorra marca Lacoste color rojo, estilo clásico',
     'GOR-RED-001',
     999.99,
     450.00,
     0.16,
     0.55,
     'Lacoste',
     'Textiles del Norte',
     '1234567890123',
     0.3,
     28,
     12,
     28,
     5,
     50,
     FALSE,
     '["gorra", "lacoste", "rojo", "accesorios"]',
     0,
     'gorra-roja-lacoste',
     '["gorra_roja_lacoste.jpg"]',
     TRUE)
ON CONFLICT DO NOTHING;

-- ─── Variantes de productos ───────────────────────────────────────────────────
-- Schema usa size_attribute_id y color_attribute_id (UUIDS referencing attribute_options)
INSERT INTO product_variants (id, product_id, size_attribute_id, color_attribute_id, color_hex, sku_variant, price_modifier, is_active) VALUES
    ('f0000001-0000-0000-0000-000000000001',
     'b0000001-0000-0000-0000-000000000001',
     'e0000001-0000-0000-0000-000000000020',  -- One Size
     'e0000001-0000-0000-0000-000000000016',  -- Rojo
     '#DC2626',
     'GOR-RED-001-OS-ROJ',
     0,
     TRUE)
ON CONFLICT DO NOTHING;

-- ─── Inventario inicial ───────────────────────────────────────────────────────
INSERT INTO inventory (id, product_variant_id, quantity_available, quantity_reserved, low_stock_threshold, stock_status, warehouse_location, updated_by) VALUES
    ('a0000001-0000-0000-0000-000000000020',
     'f0000001-0000-0000-0000-000000000001',
     10,
     0,
     5,
     'available',
     'A-01-03',
     'a0000001-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

-- ─── Movimientos de inventario ───────────────────────────────────────────────
INSERT INTO inventory_movements (id, product_variant_id, movement_type, quantity_change, quantity_before, quantity_after, notes, created_by) VALUES
    ('a0000001-0000-0000-0000-000000000021',
     'f0000001-0000-0000-0000-000000000001',
     'restock',
     10,
     0,
     10,
     'Stock inicial cargado desde seed',
     'a0000001-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

-- ─── Proveedores ──────────────────────────────────────────────────────────────
INSERT INTO suppliers (id, name, contact_name, email, phone, address, is_active) VALUES
    ('d0000001-0000-0000-0000-000000000001', 'Textiles del Norte', 'Carlos Mendoza', 'carlos@textilesnorte.com', '+52 81 1234 5678', 'Av. Industrial 1500, Monterrey, NL', TRUE),
    ('d0000001-0000-0000-0000-000000000002', 'Moda Casual SA', 'Laura García', 'laura@modacual.com', '+52 33 9876 5432', 'Calle Reforma 500, Guadalajara, Jal', TRUE),
    ('d0000001-0000-0000-0000-000000000003', 'Accesorios Premium', 'Roberto Sánchez', 'roberto@accesoriospremium.com', '+52 55 5555 5555', 'Av. Insurgentes 2000, CDMX', TRUE)
ON CONFLICT DO NOTHING;

-- ─── Resumen diario de ejemplo (últimos 7 días) ───────────────────────────────
INSERT INTO daily_sales_summary (id, summary_date, total_orders, total_revenue, total_items_sold, payment_method_breakdown, top_products) VALUES
    ('a0000001-0000-0000-0000-000000000030', CURRENT_DATE - INTERVAL '7 days', 5, 2500.00, 10, '{"cash": 1000, "card": 1500}'::JSONB, '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Gorra Roja Lacoste", "quantity": 2, "revenue": 2000}]'::JSONB),
    ('a0000001-0000-0000-0000-000000000031', CURRENT_DATE - INTERVAL '6 days', 8, 4200.00, 16, '{"cash": 2000, "card": 2200}'::JSONB, '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Gorra Roja Lacoste", "quantity": 4, "revenue": 4000}]'::JSONB),
    ('a0000001-0000-0000-0000-000000000032', CURRENT_DATE - INTERVAL '5 days', 6, 3100.00, 12, '{"cash": 1500, "card": 1600}'::JSONB, '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Gorra Roja Lacoste", "quantity": 3, "revenue": 3000}]'::JSONB),
    ('a0000001-0000-0000-0000-000000000033', CURRENT_DATE - INTERVAL '4 days', 10, 5500.00, 22, '{"cash": 2500, "card": 3000}'::JSONB, '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Gorra Roja Lacoste", "quantity": 5, "revenue": 5000}]'::JSONB),
    ('a0000001-0000-0000-0000-000000000034', CURRENT_DATE - INTERVAL '3 days', 4, 1800.00, 8, '{"cash": 800, "card": 1000}'::JSONB, '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Gorra Roja Lacoste", "quantity": 2, "revenue": 2000}]'::JSONB),
    ('a0000001-0000-0000-0000-000000000035', CURRENT_DATE - INTERVAL '2 days', 7, 3800.00, 14, '{"cash": 1800, "card": 2000}'::JSONB, '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Gorra Roja Lacoste", "quantity": 4, "revenue": 4000}]'::JSONB),
    ('a0000001-0000-0000-0000-000000000036', CURRENT_DATE - INTERVAL '1 day', 9, 4800.00, 18, '{"cash": 2200, "card": 2600}'::JSONB, '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Gorra Roja Lacoste", "quantity": 5, "revenue": 5000}]'::JSONB)
ON CONFLICT DO NOTHING;