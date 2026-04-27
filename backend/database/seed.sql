-- ═══════════════════════════════════════════════════════════════════════════
--  AUTOCOBRO — Datos de prueba para desarrollo
--  Este archivo se ejecuta automáticamente después de schema.sql en Docker
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Usuarios de prueba ──────────────────────────────────────────────────────
-- Contraseña de todos: "admin123" (hash bcrypt)
INSERT INTO users (id, name, email, password_hash, role) VALUES
    ('a0000001-0000-0000-0000-000000000001', 'Admin Principal',   'admin@tienda.com',   '$2b$12$jlMVt1QLHuZWsGK0u2fVTuBcKaf2WpZYpeL/kHLSULQ0VPMLJigfu', 'admin'),
    ('a0000001-0000-0000-0000-000000000002', 'Cajero Uno',        'cajero@tienda.com',  '$2b$12$jlMVt1QLHuZWsGK0u2fVTuBcKaf2WpZYpeL/kHLSULQ0VPMLJigfu', 'cashier'),
    ('a0000001-0000-0000-0000-000000000003', 'Cliente Demo',      'cliente@demo.com',   '$2b$12$jlMVt1QLHuZWsGK0u2fVTuBcKaf2WpZYpeL/kHLSULQ0VPMLJigfu', 'client')
ON CONFLICT DO NOTHING;

-- ─── Categorías ──────────────────────────────────────────────────────────────
INSERT INTO categories (id, name, description, icon) VALUES
    ('c0000001-0000-0000-0000-000000000001', 'Camisas',    'Camisas y blusas para dama y caballero',    'shirt'),
    ('c0000001-0000-0000-0000-000000000002', 'Pantalones', 'Pantalones de vestir, jeans y casuales',    'layers'),
    ('c0000001-0000-0000-0000-000000000003', 'Vestidos',   'Vestidos casuales y de ocasión especial',   'sparkles'),
    ('c0000001-0000-0000-0000-000000000004', 'Playeras',   'Playeras, camisetas y tops',                'tag'),
    ('c0000001-0000-0000-0000-000000000005', 'Accesorios', 'Cinturones, gorras, bufandas y más',        'gem')
ON CONFLICT DO NOTHING;

-- ─── Productos ───────────────────────────────────────────────────────────────
-- NOTE: Only products with yolo_class_name matching the trained model are included
-- Current model (best.pt) detects only: gorra-roja-lacoste
INSERT INTO products (id, category_id, name, sku, base_price, yolo_class_id, yolo_class_name, images) VALUES
    ('b0000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000005',
     'Gorra Roja Lacoste', 'GOR-RED-001', 999.99,
     0, 'gorra-roja-lacoste',
     '["gorra_roja_lacoste.jpg"]')
ON CONFLICT DO NOTHING;

-- ─── Variantes de productos ───────────────────────────────────────────────────
INSERT INTO product_variants (id, product_id, size, color, color_hex, sku_variant, price_modifier) VALUES
    -- Gorra Roja Lacoste - Only One Size
    ('f0000001-0000-0000-0000-000000000001', 'b0000001-0000-0000-0000-000000000001', 'One Size', 'Rojo', '#DC2626', 'GOR-RED-001-OS-ROJ', 0)
ON CONFLICT DO NOTHING;

-- ─── Inventario inicial ───────────────────────────────────────────────────────
INSERT INTO inventory (product_variant_id, quantity_available, low_stock_threshold, updated_by)
SELECT
    pv.id,
    10 AS quantity_available,
    5 AS low_stock_threshold,
    'a0000001-0000-0000-0000-000000000001'::UUID
FROM product_variants pv
ON CONFLICT DO NOTHING;

-- ─── Resumen diario de ejemplo (últimos 7 días) ───────────────────────────────
INSERT INTO daily_sales_summary (summary_date, total_orders, total_revenue, total_items_sold, payment_method_breakdown, top_products)
SELECT
    (NOW() - (n || ' days')::INTERVAL)::DATE AS summary_date,
    (5 + FLOOR(RANDOM() * 20))::INTEGER       AS total_orders,
    (2000 + FLOOR(RANDOM() * 8000))::NUMERIC  AS total_revenue,
    (10 + FLOOR(RANDOM() * 50))::INTEGER      AS total_items_sold,
    '{"cash": 3000, "card": 5000}'::JSONB     AS payment_method_breakdown,
    '[{"product_id": "b0000001-0000-0000-0000-000000000001", "name": "Camisa Oxford Azul", "quantity": 5, "revenue": 2250}]'::JSONB AS top_products
FROM generate_series(0, 6) AS n
ON CONFLICT DO NOTHING;

-- ─── Proveedores ──────────────────────────────────────────────────────────────
INSERT INTO suppliers (id, name, contact_name, email, phone, address, is_active) VALUES
    ('d0000001-0000-0000-0000-000000000001', 'Textiles del Norte', 'Carlos Mendoza', 'carlos@textilesnorte.com', '+52 81 1234 5678', 'Av. Industrial 1500, Monterrey, NL', TRUE),
    ('d0000001-0000-0000-0000-000000000002', 'Moda Casual SA', 'Laura García', 'laura@modacual.com', '+52 33 9876 5432', 'Calle Reforma 500, Guadalajara, Jal', TRUE),
    ('d0000001-0000-0000-0000-000000000003', 'Accesorios Premium', 'Roberto Sánchez', 'roberto@accesoriospremium.com', '+52 55 5555 5555', 'Av. Insurgentes 2000, CDMX', TRUE)
ON CONFLICT DO NOTHING;

-- ─── Opciones de atributos (tallas y colores) ─────────────────────────────────
INSERT INTO attribute_options (id, type, value, hex_code, sort_order, is_active) VALUES
    -- Tallas
    ('e0000001-0000-0000-0000-000000000001', 'size', 'XS', NULL, 1, TRUE),
    ('e0000001-0000-0000-0000-000000000002', 'size', 'S',  NULL, 2, TRUE),
    ('e0000001-0000-0000-0000-000000000003', 'size', 'M',  NULL, 3, TRUE),
    ('e0000001-0000-0000-0000-000000000004', 'size', 'L',  NULL, 4, TRUE),
    ('e0000001-0000-0000-0000-000000000005', 'size', 'XL', NULL, 5, TRUE),
    ('e0000001-0000-0000-0000-000000000006', 'size', 'XXL',NULL, 6, TRUE),
    ('e0000001-0000-0000-0000-000000000007', 'size', '28', NULL, 7, TRUE),
    ('e0000001-0000-0000-0000-000000000008', 'size', '30', NULL, 8, TRUE),
    ('e0000001-0000-0000-0000-000000000009', 'size', '32', NULL, 9, TRUE),
    ('e0000001-0000-0000-0000-000000000010', 'size', '34', NULL, 10, TRUE),
    ('e0000001-0000-0000-0000-000000000011', 'size', '36', NULL, 11, TRUE),
    ('e0000001-0000-0000-0000-000000000020', 'size', 'One Size', NULL, 12, TRUE),
    -- Colores
    ('e0000001-0000-0000-0000-000000000012', 'color', 'Azul Marino', '#1B2A4A', 1, TRUE),
    ('e0000001-0000-0000-0000-000000000013', 'color', 'Negro', '#1C1C1C', 2, TRUE),
    ('e0000001-0000-0000-0000-000000000014', 'color', 'Blanco', '#FFFFFF', 3, TRUE),
    ('e0000001-0000-0000-0000-000000000015', 'color', 'Gris', '#6B7280', 4, TRUE),
    ('e0000001-0000-0000-0000-000000000016', 'color', 'Rojo', '#DC2626', 5, TRUE),
    ('e0000001-0000-0000-0000-000000000017', 'color', 'Azul', '#3B82F6', 6, TRUE),
    ('e0000001-0000-0000-0000-000000000018', 'color', 'Verde', '#22C55E', 7, TRUE),
    ('e0000001-0000-0000-0000-000000000019', 'color', 'Multicolor', '#FF6B9D', 8, TRUE)
ON CONFLICT DO NOTHING;

-- ─── Atributos por producto ────────────────────────────────────────────────────
-- Gorra product attributes
INSERT INTO product_attributes (product_id, attribute_option_id)
SELECT 'b0000001-0000-0000-0000-000000000001', id FROM attribute_options WHERE value = 'One Size' AND type = 'size'
ON CONFLICT DO NOTHING;

INSERT INTO product_attributes (product_id, attribute_option_id)
SELECT 'b0000001-0000-0000-0000-000000000001', id FROM attribute_options WHERE value = 'Rojo' AND type = 'color'
ON CONFLICT DO NOTHING;

-- ─── Configuración de tienda (para receipts e invoices) ─────────────────────
INSERT INTO store_config (id, store_name, legal_name, address, phone, email, tax_id, receipt_footer, default_payment_method) VALUES
    ('a0000001-0000-0000-0000-000000000010',
     'FashionVision AI',
     'FashionVision AI S.A. de C.V.',
     'Av. Industrial 1500, Col. Centro, Monterrey, NL, CP 64000',
     '+52 81 1234 5678',
     'contacto@fashionvision.ai',
     'FVA-123456789',
     '¡Gracias por su compra! Vuelva pronto.',
     'cash')
ON CONFLICT DO NOTHING;

-- ─── Movimientos iniciales de inventario (explicar origen del stock) ─────────
INSERT INTO inventory_movements (product_variant_id, movement_type, quantity_change, quantity_before, quantity_after, notes, created_by)
SELECT
    pv.id,
    'restock'::movement_type,
    i.quantity_available,
    0,
    i.quantity_available,
    'Stock inicial cargado desde seed',
    'a0000001-0000-0000-0000-000000000001'::UUID
FROM product_variants pv
JOIN inventory i ON i.product_variant_id = pv.id
ON CONFLICT DO NOTHING;