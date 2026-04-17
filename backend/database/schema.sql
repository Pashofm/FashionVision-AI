-- FashionVision AI Database Schema
-- PostgreSQL 12+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE user_role AS ENUM ('customer', 'admin');
CREATE TYPE movement_type AS ENUM ('entrada', 'salida', 'ajuste');
CREATE TYPE cart_status AS ENUM ('pending', 'processed');
CREATE TYPE sale_status AS ENUM ('completado', 'cancelado');

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    cantidad INTEGER DEFAULT 0,
    precio DECIMAL(10, 2) NOT NULL,
    color VARCHAR(50),
    tipo_prenda VARCHAR(100),
    imagen_url TEXT,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Inventory movements table
CREATE TABLE inventory_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    movement_type movement_type NOT NULL,
    cantidad INTEGER NOT NULL,
    nota TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sales table
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    total DECIMAL(10, 2) NOT NULL,
    metodo_pago VARCHAR(50),
    estado sale_status DEFAULT 'completado',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sale items table
CREATE TABLE sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER REFERENCES sales(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    cantidad INTEGER NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL
);

-- Carts table
CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status cart_status DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cart items table
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES carts(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    cantidad INTEGER DEFAULT 1
);

-- Payments table
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES carts(id),
    metodo_pago VARCHAR(50) NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Receipts table
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id),
    cart_id INTEGER NOT NULL REFERENCES carts(id),
    numero_recibo VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_tipo_prenda ON products(tipo_prenda);
CREATE INDEX idx_products_color ON products(color);
CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_sale_items_product ON sale_items(product_id);
CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX idx_carts_user ON carts(user_id);
CREATE INDEX idx_carts_status ON carts(status);
CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);
CREATE INDEX idx_payments_cart ON payments(cart_id);
CREATE INDEX idx_sales_created ON sales(created_at);
CREATE INDEX idx_receipts_numero ON receipts(numero_recibo);

-- Insert sample data
INSERT INTO categories (nombre, descripcion) VALUES 
    ('Camisetas', 'Camisetas de todo tipo'),
    ('Pantalones', 'Pantalones y jeans'),
    ('Gorras', 'Gorras y sombreros'),
    ('Accesorios', 'Accesorios de moda');

INSERT INTO products (nombre, cantidad, precio, color, tipo_prenda, category_id) VALUES 
    ('Camiseta Algodon', 50, 299.99, 'Blanco', 'top', 1),
    ('Jean Slim Fit', 30, 599.99, 'Azul', 'pants', 2),
    ('Gorra Roja Lacoste', 25, 999.99, 'Rojo', 'gorra', 3);

INSERT INTO users (username, password_hash, role) VALUES 
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfQ3Z9rYFy', 'admin'),
    ('customer1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfQ3Z9rYFy', 'customer');