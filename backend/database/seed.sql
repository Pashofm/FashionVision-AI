-- ═══════════════════════════════════════════════════════════════════════════
--  FashionVision-AI — Datos de prueba para desarrollo
--  Mantener en sincronía con alembic/versions/002_seed_data.py
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
INSERT INTO products (id, category_id, name, description, sku, base_price, cost_price, tax_rate, profit_margin, brand, supplier, barcode, weight, width, height, depth, is_featured, tags, images, is_active) VALUES
    ('b0000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000005',
     'Gorra Lacoste',
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
     FALSE,
     '["gorra", "lacoste", "rojo", "accesorios"]',
     '["https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271604/fashionvision/products/hjy41jxdxigidpzwl5pe.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271605/fashionvision/products/rum8xmdjalwxctt8mwoi.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271606/fashionvision/products/mwor7iy2wtnnjzqkgkuc.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271607/fashionvision/products/tmo35r3hlz13xibagjer.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271610/fashionvision/products/egdajidh8xgdo4cehpri.jpg"]',
     TRUE),
    ('41ce8430-152b-49b4-a08b-2da0db2df072',
     'c0000001-0000-0000-0000-000000000005',
     'Gorra Venados',
     'Gorra de los venados',
     'GOR-VEN-01',
     1000.00,
     700.00,
     0.16,
     0.30,
     'Venados',
     NULL,
     NULL,
     NULL,
     NULL,
     NULL,
     NULL,
     FALSE,
     '[]',
     '["https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271634/fashionvision/products/cfif7xv6zebvsrfisqoj.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271635/fashionvision/products/qwy6p64gshxmk2qkr0ne.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271636/fashionvision/products/m6lwjn5xkrolxebn86bj.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271636/fashionvision/products/cxjjrih7f45zta2joy56.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271637/fashionvision/products/eyamhez90mqqqrvo8l9b.jpg"]',
     TRUE),
    ('6f718ca2-d7e5-4a88-95f6-cdc173a0bbac',
     'c0000001-0000-0000-0000-000000000002',
     'Pantalon Mezclilla Cargo',
     'Pantalon Mezclilla cargo',
     'PAN-MEZ-CAR-01',
     500.00,
     200.00,
     0.16,
     0.40,
     'Cuidado con el perro',
     NULL,
     NULL,
     NULL,
     NULL,
     NULL,
     NULL,
     FALSE,
     '[]',
     '["https://res.cloudinary.com/dyuuzbvz3/image/upload/v1779759456/fashionvision/products/pvfaavabvrwajdhridqe.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1779759456/fashionvision/products/teac8oveqsi6tj7veksh.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1779759457/fashionvision/products/taymqkinrmcax8stfffo.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1779759457/fashionvision/products/bdryyw93bwy00um8rmpb.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1779759458/fashionvision/products/wq4s0wkbjh338gn9fzwn.jpg"]',
     TRUE),
    ('dcf76b48-4b03-456a-87ed-373d3a4d2189',
     'c0000001-0000-0000-0000-000000000002',
     'Pantalon Mezclilla Oversize',
     'Pantalon Mezclilla Oversize',
     'PAN-MEZ-OVE-01',
     300.00,
     170.00,
     0.16,
     0.00,
     'Levis',
     NULL,
     NULL,
     NULL,
     NULL,
     NULL,
     NULL,
     FALSE,
     '[]',
     '["https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271241/fashionvision/products/uczgs341e6ylnidrznrl.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271242/fashionvision/products/sastcj4vy83oim3ko4kw.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271243/fashionvision/products/ntnori8auyllpkqno9zh.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271243/fashionvision/products/ji72srcmvw8l6p0nhjev.jpg", "https://res.cloudinary.com/dyuuzbvz3/image/upload/v1780271244/fashionvision/products/sn7gjoesfivsgxvtqbi3.jpg"]',
     TRUE)
ON CONFLICT DO NOTHING;

-- ─── Variantes de productos ───────────────────────────────────────────────────
INSERT INTO product_variants (id, product_id, size_attribute_id, color_attribute_id, color_hex, sku_variant, price_modifier, is_active) VALUES
    ('f0000001-0000-0000-0000-000000000001', 'b0000001-0000-0000-0000-000000000001',
     'e0000001-0000-0000-0000-000000000020', 'e0000001-0000-0000-0000-000000000016',
     '#DC2626', 'GOR-RED-001-OS-ROJ', 0, TRUE),
    ('d317341d-b306-46ca-b18a-1e56a6eb252c', 'b0000001-0000-0000-0000-000000000001',
     'e0000001-0000-0000-0000-000000000020', 'e0000001-0000-0000-0000-000000000015',
     '#9a9996', 'GOR-RED-001-OS-NEG', 0, TRUE),
    ('a3d7f491-82a8-4db6-a4c0-5396e5cbd0ba', '41ce8430-152b-49b4-a08b-2da0db2df072',
     'e0000001-0000-0000-0000-000000000020', 'e0000001-0000-0000-0000-000000000016',
     '#ff0000', 'GOR-VEN-001-OS-ROJ', 0, TRUE),
    ('74be3456-50c2-41be-b8ae-307c579b7648', '41ce8430-152b-49b4-a08b-2da0db2df072',
     'e0000001-0000-0000-0000-000000000020', 'e0000001-0000-0000-0000-000000000013',
     '#000000', 'GOR-VEN-001-OS-NEG', 0, TRUE),
    ('7aef4af3-5903-4185-8e54-8ec397f98fdc', '41ce8430-152b-49b4-a08b-2da0db2df072',
     'e0000001-0000-0000-0000-000000000020', 'e0000001-0000-0000-0000-000000000014',
     '#ffffff', 'GOR-VEN-001-OS-BLA', 0, TRUE),
    ('2b6f88c4-2bac-4505-bb29-d15799c8b654', '6f718ca2-d7e5-4a88-95f6-cdc173a0bbac',
     'e0000001-0000-0000-0000-000000000001', 'e0000001-0000-0000-0000-000000000012',
     '#1f4bff', 'PAN-MEZ-CAR-001-CHI-AZM', 0, TRUE),
    ('60bf83c8-1a7c-4a2c-9d0e-1e9b103e3e5d', 'dcf76b48-4b03-456a-87ed-373d3a4d2189',
     'e0000001-0000-0000-0000-000000000002', 'e0000001-0000-0000-0000-000000000017',
     '#05acff', 'PAN-MEZ-OVE-01-CHI-AZU', 0, TRUE)
ON CONFLICT DO NOTHING;

-- ─── Inventario inicial ───────────────────────────────────────────────────────
INSERT INTO inventory (id, product_variant_id, quantity_available, quantity_reserved, low_stock_threshold, stock_status, warehouse_location, updated_by) VALUES
    ('a0000001-0000-0000-0000-000000000020', 'f0000001-0000-0000-0000-000000000001', 5, 0, 5, 'available', 'A-01-03', 'a0000001-0000-0000-0000-000000000001'),
    ('adb90ee5-2cfb-4008-8740-665b1c3df5bc', 'd317341d-b306-46ca-b18a-1e56a6eb252c', 13, 0, 5, 'available', NULL, 'a0000001-0000-0000-0000-000000000001'),
    ('a3a60e75-ac3b-4e83-8aca-3bbac211d1cb', 'a3d7f491-82a8-4db6-a4c0-5396e5cbd0ba', 10, 0, 5, 'available', NULL, 'a0000001-0000-0000-0000-000000000001'),
    ('2c57a0a1-4a3a-4512-9feb-ea5ae5f7eefb', '74be3456-50c2-41be-b8ae-307c579b7648', 10, 0, 5, 'available', NULL, 'a0000001-0000-0000-0000-000000000001'),
    ('a421ab48-2e53-4ad2-8127-5ab61e42641f', '7aef4af3-5903-4185-8e54-8ec397f98fdc', 10, 0, 5, 'available', NULL, 'a0000001-0000-0000-0000-000000000001'),
    ('ad9d90e0-9e8f-4558-877e-6e0a7e93f2e6', '2b6f88c4-2bac-4505-bb29-d15799c8b654', 10, 0, 5, 'available', NULL, 'a0000001-0000-0000-0000-000000000001'),
    ('f456d2d5-6e85-4e68-b0db-76f51c9e4274', '60bf83c8-1a7c-4a2c-9d0e-1e9b103e3e5d', 10, 0, 5, 'available', NULL, 'a0000001-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

-- ─── Movimientos de inventario ───────────────────────────────────────────────
INSERT INTO inventory_movements (id, product_variant_id, movement_type, quantity_change, quantity_before, quantity_after, notes, created_by) VALUES
    ('a0000001-0000-0000-0000-000000000021', 'f0000001-0000-0000-0000-000000000001', 'restock', 5, 0, 5, 'Stock inicial cargado desde seed', 'a0000001-0000-0000-0000-000000000001'),
    ('7d43f0e7-3dec-4ae2-8e7e-b96af857fca8', 'd317341d-b306-46ca-b18a-1e56a6eb252c', 'restock', 13, 0, 13, 'Stock inicial', 'a0000001-0000-0000-0000-000000000001'),
    ('f25f8e0b-14b6-4c2a-9af7-9cce13440eeb', 'a3d7f491-82a8-4db6-a4c0-5396e5cbd0ba', 'restock', 10, 0, 10, 'Stock inicial', 'a0000001-0000-0000-0000-000000000001'),
    ('15aff7e7-3d5d-4d1b-8fee-5b7a9e5f45b3', '74be3456-50c2-41be-b8ae-307c579b7648', 'restock', 10, 0, 10, 'Stock inicial', 'a0000001-0000-0000-0000-000000000001'),
    ('a67a2f40-5e78-4d00-a4b6-c5fcd1b45006', '7aef4af3-5903-4185-8e54-8ec397f98fdc', 'restock', 10, 0, 10, 'Stock inicial', 'a0000001-0000-0000-0000-000000000001'),
    ('4d5fe43f-4011-460a-9669-7974df3f94ed', '2b6f88c4-2bac-4505-bb29-d15799c8b654', 'restock', 10, 0, 10, 'Stock inicial', 'a0000001-0000-0000-0000-000000000001'),
    ('811ad231-ded4-4eeb-8864-6206f9f1c196', '60bf83c8-1a7c-4a2c-9d0e-1e9b103e3e5d', 'restock', 10, 0, 10, 'Stock inicial', 'a0000001-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

-- ─── Proveedores ──────────────────────────────────────────────────────────────
INSERT INTO suppliers (id, name, contact_name, email, phone, address, is_active) VALUES
    ('d0000001-0000-0000-0000-000000000001', 'Textiles del Norte', 'Carlos Mendoza', 'carlos@textilesnorte.com', '+52 81 1234 5678', 'Av. Industrial 1500, Monterrey, NL', TRUE),
    ('d0000001-0000-0000-0000-000000000002', 'Moda Casual SA', 'Laura García', 'laura@modacual.com', '+52 33 9876 5432', 'Calle Reforma 500, Guadalajara, Jal', TRUE),
    ('d0000001-0000-0000-0000-000000000003', 'Accesorios Premium', 'Roberto Sánchez', 'roberto@accesoriospremium.com', '+52 55 5555 5555', 'Av. Insurgentes 2000, CDMX', TRUE)
ON CONFLICT DO NOTHING;
