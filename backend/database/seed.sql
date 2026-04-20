-- ═══════════════════════════════════════════════════════════════════════════
--  AUTOCOBRO — Datos de prueba para desarrollo
--  Este archivo se ejecuta automáticamente después de init.sql en Docker
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Usuarios de prueba ──────────────────────────────────────────────────────
-- Contraseña de todos: "admin123" (hash bcrypt)
INSERT INTO users (id, name, email, password_hash, role) VALUES
    ('a0000001-0000-0000-0000-000000000001', 'Admin Principal',   'admin@tienda.com',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGf.fHb6rCeZuM5.oPdm5y2g5jK', 'admin'),
    ('a0000001-0000-0000-0000-000000000002', 'Cajero Uno',        'cajero@tienda.com',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGf.fHb6rCeZuM5.oPdm5y2g5jK', 'cashier'),
    ('a0000001-0000-0000-0000-000000000003', 'Cliente Demo',      'cliente@demo.com',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGf.fHb6rCeZuM5.oPdm5y2g5jK', 'client')
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
INSERT INTO products (id, category_id, name, sku, base_price, yolo_class_id, yolo_class_name, images) VALUES
    ('p0000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000001',
     'Camisa Oxford Azul Marino', 'CAM-OXF-001', 450.00,
     0, 'camisa_oxford_azul',
     '["camisa_oxford_azul_frente.jpg", "camisa_oxford_azul_espalda.jpg"]'),

    ('p0000001-0000-0000-0000-000000000002',
     'c0000001-0000-0000-0000-000000000002',
     'Jeans Slim Fit Negro', 'JEAN-SLM-001', 680.00,
     1, 'jeans_slim_negro',
     '["jeans_slim_negro.jpg"]'),

    ('p0000001-0000-0000-0000-000000000003',
     'c0000001-0000-0000-0000-000000000003',
     'Vestido Floral Verano', 'VES-FLO-001', 890.00,
     2, 'vestido_floral_verano',
     '["vestido_floral_verano.jpg"]'),

    ('p0000001-0000-0000-0000-000000000004',
     'c0000001-0000-0000-0000-000000000004',
     'Playera Básica Blanca', 'PLAY-BAS-001', 180.00,
     3, 'playera_basica_blanca',
     '["playera_blanca_frente.jpg"]'),

    ('p0000001-0000-0000-0000-000000000005',
     'c0000001-0000-0000-0000-000000000004',
     'Playera Gráfica Urbana', 'PLAY-GRF-001', 250.00,
     4, 'playera_grafica_urbana',
     '["playera_grafica.jpg"]')
ON CONFLICT DO NOTHING;

-- ─── Variantes de productos ───────────────────────────────────────────────────
INSERT INTO product_variants (id, product_id, size, color, color_hex, sku_variant, price_modifier) VALUES
    -- Camisa Oxford Azul
    ('v0000001-0000-0000-0000-000000000001', 'p0000001-0000-0000-0000-000000000001', 'S',  'Azul Marino', '#1B2A4A', 'CAM-OXF-001-S-AZM',  0),
    ('v0000001-0000-0000-0000-000000000002', 'p0000001-0000-0000-0000-000000000001', 'M',  'Azul Marino', '#1B2A4A', 'CAM-OXF-001-M-AZM',  0),
    ('v0000001-0000-0000-0000-000000000003', 'p0000001-0000-0000-0000-000000000001', 'L',  'Azul Marino', '#1B2A4A', 'CAM-OXF-001-L-AZM',  0),
    ('v0000001-0000-0000-0000-000000000004', 'p0000001-0000-0000-0000-000000000001', 'XL', 'Azul Marino', '#1B2A4A', 'CAM-OXF-001-XL-AZM', 20),

    -- Jeans Slim Fit Negro
    ('v0000001-0000-0000-0000-000000000005', 'p0000001-0000-0000-0000-000000000002', '28', 'Negro', '#1C1C1C', 'JEAN-SLM-001-28-NEG', 0),
    ('v0000001-0000-0000-0000-000000000006', 'p0000001-0000-0000-0000-000000000002', '30', 'Negro', '#1C1C1C', 'JEAN-SLM-001-30-NEG', 0),
    ('v0000001-0000-0000-0000-000000000007', 'p0000001-0000-0000-0000-000000000002', '32', 'Negro', '#1C1C1C', 'JEAN-SLM-001-32-NEG', 0),

    -- Vestido Floral
    ('v0000001-0000-0000-0000-000000000008', 'p0000001-0000-0000-0000-000000000003', 'S',  'Multicolor', '#FF6B9D', 'VES-FLO-001-S-MUL', 0),
    ('v0000001-0000-0000-0000-000000000009', 'p0000001-0000-0000-0000-000000000003', 'M',  'Multicolor', '#FF6B9D', 'VES-FLO-001-M-MUL', 0),

    -- Playera Blanca
    ('v0000001-0000-0000-0000-000000000010', 'p0000001-0000-0000-0000-000000000004', 'S',  'Blanco', '#FFFFFF', 'PLAY-BAS-001-S-BLA',  0),
    ('v0000001-0000-0000-0000-000000000011', 'p0000001-0000-0000-0000-000000000004', 'M',  'Blanco', '#FFFFFF', 'PLAY-BAS-001-M-BLA',  0),
    ('v0000001-0000-0000-0000-000000000012', 'p0000001-0000-0000-0000-000000000004', 'L',  'Blanco', '#FFFFFF', 'PLAY-BAS-001-L-BLA',  0),

    -- Playera Gráfica
    ('v0000001-0000-0000-0000-000000000013', 'p0000001-0000-0000-0000-000000000005', 'M',  'Negro', '#1C1C1C', 'PLAY-GRF-001-M-NEG', 0),
    ('v0000001-0000-0000-0000-000000000014', 'p0000001-0000-0000-0000-000000000005', 'L',  'Negro', '#1C1C1C', 'PLAY-GRF-001-L-NEG', 0)
ON CONFLICT DO NOTHING;

-- ─── Inventario inicial ───────────────────────────────────────────────────────
INSERT INTO inventory (product_variant_id, quantity_available, low_stock_threshold, updated_by)
SELECT
    pv.id,
    CASE
        WHEN pv.sku_variant LIKE '%XL%' THEN 8
        WHEN pv.sku_variant LIKE '%S-%' THEN 15
        ELSE 20
    END AS quantity_available,
    5 AS low_stock_threshold,
    'a0000001-0000-0000-0000-000000000001' AS updated_by
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
    '[{"product_id": "p0000001-0000-0000-0000-000000000001", "name": "Camisa Oxford Azul", "quantity": 5, "revenue": 2250}]'::JSONB AS top_products
FROM generate_series(0, 6) AS n
ON CONFLICT DO NOTHING;
