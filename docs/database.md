# FashionVision AI - Database Documentation

## Overview

This document describes the PostgreSQL database implementation for the FashionVision AI system, which includes three main components:
1. Inventory Management System
2. Sales Analytics Dashboard
3. Payment System

---

## Architecture

```
FastAPI (Backend)
    ├── database/
    │   ├── connection.py    # SQLAlchemy setup
    │   └── models.py       # ORM models
    ├── schemas/
    │   └── schemas.py     # Pydantic schemas
    └── main.py          # API endpoints
```

---

## Database Schema

### 1. Users Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL | Username |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password |
| `role` | ENUM | DEFAULT 'customer' | 'customer' or 'admin' |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Registration date |

**Roles:**
- `customer` - Regular user who can create carts and add items
- `admin` - Administrator with full access to system

---

### 2. Categories Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `nombre` | VARCHAR(100) | NOT NULL | Category name |
| `descripcion` | TEXT | NULLABLE | Category description |

---

### 3. Products Table (Inventory)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `nombre` | VARCHAR(255) | NOT NULL | Product name |
| `cantidad` | INTEGER | DEFAULT 0 | Stock quantity |
| `precio` | DECIMAL(10,2) | NOT NULL | Price |
| `color` | VARCHAR(50) | NULLABLE | Product color |
| `tipo_prenda` | VARCHAR(100) | NULLABLE | Clothing type |
| `imagen_url` | TEXT | NULLABLE | Image URL |
| `category_id` | INTEGER | FK → categories.id | Category reference |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation date |
| `updated_at` | TIMESTAMP | AUTO UPDATE | Last update |

---

### 4. Inventory Movements Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `product_id` | INTEGER | FK → products.id | Product reference |
| `movement_type` | ENUM | NOT NULL | 'entrada', 'salida', 'ajuste' |
| `cantidad` | INTEGER | NOT NULL | Quantity changed |
| `nota` | TEXT | NULLABLE | Note/description |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Movement date |

**Movement Types:**
- `entrada` - Stock entry (add inventory)
- `salida` - Stock removal (subtract inventory)
- `ajuste` - Manual adjustment (set exact quantity)

---

### 5. Sales Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `total` | DECIMAL(10,2) | NOT NULL | Sale total amount |
| `metodo_pago` | VARCHAR(50) | NULLABLE | Payment method |
| `estado` | ENUM | DEFAULT 'completado' | 'completado' or 'cancelado' |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Sale date |

---

### 6. Sale Items Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `sale_id` | INTEGER | FK → sales.id | Sale reference |
| `product_id` | INTEGER | FK → products.id | Product reference |
| `cantidad` | INTEGER | NOT NULL | Quantity sold |
| `precio_unitario` | DECIMAL(10,2) | NOT NULL | Unit price at sale |

---

### 7. Carts Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `user_id` | INTEGER | FK → users.id | Customer reference |
| `status` | ENUM | DEFAULT 'pending' | 'pending' or 'processed' |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Cart creation date |

**Cart Status:**
- `pending` - Awaiting processing
- `processed` - Payment completed

---

### 8. Cart Items Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `cart_id` | INTEGER | FK → carts.id | Cart reference |
| `product_id` | INTEGER | FK → products.id | Product reference |
| `cantidad` | INTEGER | DEFAULT 1 | Quantity |

---

### 9. Payments Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `cart_id` | INTEGER | FK → carts.id | Cart reference |
| `metodo_pago` | VARCHAR(50) | NOT NULL | 'cash' or 'card' |
| `monto` | DECIMAL(10,2) | NOT NULL | Total paid |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Payment date |

---

### 10. Receipts Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Unique identifier |
| `payment_id` | INTEGER | FK → payments.id | Payment reference |
| `cart_id` | INTEGER | FK → carts.id | Cart reference |
| `numero_recibo` | VARCHAR(20) | UNIQUE | Receipt number (e.g., REC-000001) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Generation date |

---

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐
│    users    │       │  categories │
└──────────────┘       └──────────────┘
       │                       │
       │ 1:N                   │ 1:N
       ▼                       ▼
┌──────────────┐       ┌──────────────┐
│    carts    │       │   products   │
└──────────────┘       └──────────────┘
      │                       │
      │ 1:N                  │ 1:N
      ▼                      ▼
┌──────────────┐       ┌─────────────────┐
│  cart_items  │       │inventory_movements│
└──────────────┘       └─────────────────┘
      │
      │ 1:1
      ▼
┌──────────────┐       ┌──────────────┐
│   payments   │       │ sale_items   │
└──────────────┘       └──────────────┘
      │
      │ 1:1
      ▼
┌──────────────┐       ┌──────────────┐
│   receipts  │       │    sales    │
└──────────────┘       └──────────────┘
```

---

## API Endpoints

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users` | Create user |
| GET | `/api/users` | List all users |
| GET | `/api/users/{id}` | Get user by ID |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/categories` | Create category |
| GET | `/api/categories` | List categories |

### Products (Inventory)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/products` | Create product |
| GET | `/api/products` | List products |
| GET | `/api/products/{id}` | Get product |
| PUT | `/api/products/{id}` | Update product |
| DELETE | `/api/products/{id}` | Delete product |

### Inventory Movements
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/inventory-movements` | Register movement |
| GET | `/api/inventory-movements` | List movements |

### Sales
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sales` | Create sale |
| GET | `/api/sales` | List sales |

### Carts
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/carts` | Create cart |
| GET | `/api/carts` | List user's carts |
| GET | `/api/carts/admin` | List pending carts (admin) |
| POST | `/api/carts/{id}/items` | Add item to cart |
| DELETE | `/api/carts/{id}/items/{id}` | Remove item from cart |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments` | Create payment |
| POST | `/api/payments/{cart_id}/process` | Process payment & generate receipt |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/sales` | Sales summary (daily/weekly/monthly) |
| GET | `/api/analytics/products/most-sold` | Top 10 selling products |
| GET | `/api/analytics/products/least-sold` | Bottom 10 selling products |
| GET | `/api/analytics/inventory` | Inventory status (excess/low/out) |

---

## Usage

### 1. Setup Database

```bash
# Create PostgreSQL database
createdb fashionvision

# Install dependencies
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL

# Run server
uvicorn main:app --reload --port 8000
```

### 2. Workflow Example

#### Customer Flow
```bash
# 1. Create customer account
POST /api/users
{"username": "john", "password": "secret", "role": "customer"}

# 2. Create cart
POST /api/carts
{"user_id": 1}

# 3. Add items to cart
POST /api/carts/1/items
{"product_id": 1, "cantidad": 2}
```

#### Admin Flow
```bash
# 1. View pending carts
GET /api/carts/admin

# 2. Process payment
POST /api/payments/1/process?metodo_pago=cash

# 3. View analytics
GET /api/analytics/sales
GET /api/analytics/inventory
```

---

## Security Notes

- Passwords are hashed using bcrypt
- In production, change `DATABASE_URL` credentials
- Restrict CORS `allow_origins` in production
- Use environment variables for sensitive data

---

## Future Enhancements

- User authentication (JWT tokens)
- Product images storage (S3/local)
- Receipt PDF generation
- Email notifications
- Multi-admin support
- Audit logging