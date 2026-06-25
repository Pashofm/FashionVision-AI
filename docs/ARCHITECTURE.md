# Arquitectura del Sistema

Documento de arquitectura de referencia para FashionVision AI. Describe los componentes principales, el modelo de datos, los flujos de información y las decisiones técnicas clave.

---

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENTE (Navegador)                         │
│                                                                      │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │   Kiosko (Cliente)   │  │   Dashboard      │  │   Inventario  │  │
│  │   React + Cámara     │  │   Admin/Cajero   │  │   Admin       │  │
│  │   Detección YOLO     │  │   Reportes/PDF   │  │   Catálogo    │  │
│  └─────────┬────────────┘  └────────┬─────────┘  └───────┬───────┘  │
│            │                        │                     │          │
└────────────┼────────────────────────┼─────────────────────┼──────────┘
             │                        │                     │
        HTTP/REST                HTTP/REST             HTTP/REST
             │                  (JWT Auth)                  │
             ▼                        ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        NGINX (Frontend Container)                    │
│  • Sirve SPA (React build)                                          │
│  • Proxy /api/* → backend:8000                                      │
│  • Compresión gzip                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    proxy_pass /api/*
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   BACKEND — FastAPI (Python 3.12)                    │
│                                                                      │
│  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────────┐ │
│  │   Auth    │ │  Products│ │ Inventory │ │   Analytics          │ │
│  │  JWT      │ │  CRUD    │ │  Stock    │ │   Dashboard/Reportes │ │
│  │  Sessions │ │  Variants│ │  Movements│ │   Top Products       │ │
│  └───────────┘ └──────────┘ └───────────┘ └──────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Servicios de Visión por Computadora                          │   │
│  │  ┌─────────────────┐  ┌──────────────────────────────────┐   │   │
│  │  │  YOLO Detection │  │  CLIP Matcher                    │   │   │
│  │  │  • Detecta      │  │  • Embeddings de productos       │   │   │
│  │  │    prendas      │  │  • Match por similitud coseno    │   │   │
│  │  │  • Bounding box │  │  • Búsqueda en catálogo          │   │   │
│  │  └─────────────────┘  └──────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Servicios de Negocio                                        │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │   │
│  │  │  Cart/Orders │ │  Receipts    │ │  POS Terminal        │ │   │
│  │  │  Flujo de    │ │  Impresión   │ │  Pagos (Mock/Stripe) │ │   │
│  │  │  compra      │ │  Recibos     │ │  Init→Process→Done   │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Infraestructura                                              │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │   │
│  │  │  SQLAlchemy  │ │  Alembic     │ │  Cloudinary          │ │   │
│  │  │  ORM Async   │ │  Migrations  │ │  Almacenamiento      │ │   │
│  │  │  PostgreSQL  │ │  Versionado  │ │  de imágenes         │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    SQLAlchemy Async
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                PostgreSQL 16 + pgvector + pg_trgm                    │
│                                                                      │
│  • Datos transaccionales (usuarios, productos, ventas, inventario)  │
│  • Embeddings vectoriales (CLIP) para matching visual               │
│  • Búsqueda por similitud de texto (pg_trgm)                        │
│  • Migraciones versionadas con Alembic                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Diagrama Entidad-Relación (ERD)

```
┌──────────┐       ┌──────────┐       ┌──────────────┐
│  users   │       │ sessions │       │    carts      │
├──────────┤       ├──────────┤       ├───────────────┤
│ id (PK)  │──┐    │ id (PK)  │──┐    │ id (PK)       │
│ email    │  │    │ station  │  │    │ session_id FK │──┐
│ password │  │    │ status   │  │    │ status        │  │
│ role     │  │    │ expires  │  │    │ notes         │  │
│ name     │  │    │ user_id──┼──┘    │ total_amount  │  │
└──────────┘  │    └──────────┘       └───────┬───────┘  │
              │                               │           │
              │    ┌──────────────┐    ┌──────┴──────┐    │
              └───►│  inventory   │    │ cart_items  │◄───┘
                   ├──────────────┤    ├─────────────┤
    ┌──────────┐   │ id (PK)      │    │ id (PK)     │
    │ suppliers│   │ variant_id───┼──┐ │ cart_id FK  │
    ├──────────┤   │ qty_available│  │ │ variant_id──┼──┐
    │ id (PK)  │   │ qty_reserved │  │ │ quantity    │  │
    │ name     │   │ threshold    │  │ │ unit_price  │  │
    │ contact  │   │ status       │  │ └─────────────┘  │
    └──────────┘   │ supplier_id──┼──┘                  │
                   └──────┬───────┘                      │
                          │                              │
                   ┌──────┴──────────┐                   │
                   │ product_variants│◄──────────────────┘
                   ├─────────────────┤
    ┌──────────┐   │ id (PK)         │       ┌──────────────┐
    │ products │   │ product_id FK ──┼──┐    │   orders     │
    ├──────────┤   │ size_attr_id    │  │    ├──────────────┤
    │ id (PK)──┼───┤ color_attr_id   │  │    │ id (PK)     │
    │ name     │   │ sku             │  │    │ cart_id FK   │──┐
    │ category─┼─┐ │ price           │  │    │ status       │  │
    │ brand    │ │ │ cost            │  │    │ total_amount │  │
    │ featured │ │ └─────────────────┘  │    │ payment_meth │  │
    └────┬─────┘ │                      │    └──────┬───────┘  │
         │       │   ┌──────────────┐   │           │          │
         │       │   │  attributes  │   │    ┌──────┴──────┐   │
         │       │   ├──────────────┤   │    │ order_items │   │
         │       │   │ id (PK)      │   │    ├─────────────┤   │
         │       │   │ name         │   │    │ id (PK)     │   │
         │       │   │ type         │   │    │ order_id FK │◄──┘
         │       │   │ value        │   │    │ variant_id──┼───┘
         │       │   └──────┬───────┘   │    │ quantity    │
         │       │          │           │    │ unit_price  │
         │       │   ┌──────┴────────┐  │    └─────────────┘
         │       │   │product_attrs  │  │
         │       │   │ (junction)    │  │    ┌────────────────┐
         │       │   │ product_id FK─┼──┘    │inventory_mvmts │
         │       │   │ attribute_id──┼──────┤ (historial)    │
         │       │   └───────────────┘      │ variant_id FK──┼──┐
         │       │                          │ type           │  │
    ┌────┴───┐   │   ┌───────────────┐      │ quantity_change│  │
    │categories│  │   │product_images │      │ reason         │  │
    ├─────────┤  │   ├───────────────┤      └────────────────┘  │
    │ id (PK)─┼──┘   │ product_id FK─┼──┐                       │
    │ name    │      │ url           │  │    ┌───────────────┐  │
    │ active  │      │ public_id     │  │    │   receipts    │  │
    └─────────┘      │ is_primary    │  │    ├───────────────┤  │
                     └───────────────┘  │    │ id (PK)       │  │
                                        │    │ order_id FK───┼──┘
    ┌───────────────────┐               │    │ cart_id FK────┼──┘
    │ product_embeddings│               │    │ type          │
    ├───────────────────┤               │    │ content       │
    │ id (PK)           │               │    └───────────────┘
    │ product_id FK ────┼───────────────┘
    │ embedding (vector)│
    │ model_version     │
    │ generated_at      │
    └───────────────────┘
```

### Relaciones principales

| Entidad A | Entidad B | Tipo | Descripción |
|-----------|-----------|------|-------------|
| users | sessions | 1:N | Un usuario puede tener múltiples sesiones |
| sessions | carts | 1:1 | Una sesión tiene un carrito activo |
| carts | cart_items | 1:N | Un carrito contiene múltiples ítems |
| cart_items | product_variants | N:1 | Cada ítem referencia una variante |
| products | product_variants | 1:N | Un producto tiene variantes (talla+color) |
| products | categories | N:1 | Un producto pertenece a una categoría |
| products | product_embeddings | 1:1 | Un producto tiene un embedding CLIP |
| products | product_attributes | M:N | Producto ↔ Atributos (talla, color) vía tabla junction |
| products | product_images | 1:N | Múltiples imágenes por producto |
| carts | orders | 1:1 | Un carrito pagado genera una orden |
| orders | order_items | 1:N | Una orden contiene ítems |
| orders | receipts | 1:1 | Una orden tiene un recibo |
| product_variants | inventory | 1:1 | Cada variante tiene un registro de inventario |
| product_variants | inventory_movements | 1:N | Historial de movimientos por variante |
| inventory | suppliers | N:1 | Registro de inventario vinculado a proveedor |

---

## Flujo de Datos

### Flujo Principal: Detección → Catálogo → Compra

```
1. CLIENTE KIOSKO
   ┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────────┐
   │ Cámara  │────►│ Captura  │────►│ POST /detect │────►│ YOLO Model   │
   │ (env)   │     │ Frame    │     │ (image/jpeg) │     │ (best.pt)    │
   └─────────┘     └──────────┘     └──────┬───────┘     └──────┬───────┘
                                           │                     │
                                           │  Detecciones         │
                                           │  (clase, bbox,       │
                                           │   confianza)         │
                                           ▼                     │
                                    ┌──────────────┐             │
                                    │ POST /detect/ │◄────────────┘
                                    │ match-catalog │
                                    │ (imagen+bbox) │
                                    └──────┬───────┘
                                           │
                                           │ CLIP embedding del crop
                                           │ Cosine similarity vs BD
                                           ▼
                                    ┌──────────────┐
                                    │ Resultado:    │
                                    │ product_id,   │
                                    │ similarity,   │
                                    │ precio, stock │
                                    └──────┬───────┘
                                           │
                                           ▼
2. SELECCIÓN DE VARIANTE
   ┌──────────────┐     ┌─────────────────┐
   │ Elegir talla │────►│ GET /variants/  │
   │ y color      │     │ search          │
   └──────────────┘     └────────┬────────┘
                                 │
                                 │ Variante encontrada
                                 │ (sku, stock, precio)
                                 ▼
3. AGREGAR AL CARRITO
   ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
   │ POST /carts/ │────►│ Reserva stock    │────►│ Carrito      │
   │ {id}/items   │     │ (Inventory)      │     │ actualizado  │
   └──────────────┘     └──────────────────┘     └──────────────┘

4. ENVIAR A CAJA
   ┌──────────────┐     ┌──────────────────┐
   │ PUT /carts/  │────►│ Cart status:     │
   │ {id}         │     │ 'submitted'      │
   └──────────────┘     └──────────────────┘
                                 │
                                 ▼
5. CAJERO PROCESA
   ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
   │ PUT /carts/  │────►│ Cart status:     │────►│ POST /orders │
   │ {id}         │     │ 'processing'     │     │ (crear orden)│
   └──────────────┘     └──────────────────┘     └──────┬───────┘
                                                        │
6. PAGO Y CIERRE                                          │
   ┌──────────────┐     ┌──────────────────┐             │
   │ Cart status: │────►│ Reducir stock    │◄────────────┘
   │ 'paid'       │     │ InventoryMovement│
   └──────────────┘     │ type='sale'      │
                        └──────────────────┘
```

### Flujo de Embeddings (CLIP)

```
┌─────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│ Imagen producto │────►│ POST /products/   │────►│ CLIP Model       │
│ (upload)        │     │ {id}/generate-    │     │ (ViT-B/32)       │
│                 │     │ embedding         │     │                  │
└─────────────────┘     └───────────────────┘     └────────┬─────────┘
                                                           │
                                                    Vector 512-dim
                                                           │
                                                           ▼
                                                   ┌───────────────┐
                                                   │ PostgreSQL    │
                                                   │ pgvector      │
                                                   │ cosine <=>    │
                                                   └───────────────┘
```

### Flujo de Autenticación

```
┌──────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────────┐
│ Login    │────►│ POST /auth/   │────►│ Validar       │────►│ Generar      │
│ (email,  │     │ login         │    │ credenciales  │     │ JWT tokens   │
│  pass)   │     │               │     │ (bcrypt)      │     │ access+refr. │
└──────────┘     └───────────────┘     └──────────────┘     └──────┬───────┘
                                                                    │
┌───────────────────────────────────────────────────────────────────┘
│
▼
┌──────────────┐     ┌───────────────┐     ┌────────────────────────┐
│ Petición     │────►│ Middleware    │────►│ Token válido?          │
│ autenticada  │     │ JWT (Bearer)  │     │ ├─ Sí: continuar       │
│              │     │               │     │ └─ No: refresh token   │
└──────────────┘     └───────────────┘     │    o redirigir login   │
                                           └────────────────────────┘
```

---

## Stack Tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| **Frontend** | React 19 + Vite 7 | SPA con hot-reload |
| **Routing** | React Router DOM 7 | Navegación SPA |
| **Charts** | Recharts 3 | Gráficos de dashboard y reportes |
| **Export** | jsPDF + xlsx | PDF y Excel |
| **Backend** | FastAPI 0.115 (Python 3.12) | API REST asíncrona |
| **ORM** | SQLAlchemy 2.0 (async) | Mapeo objeto-relacional |
| **Auth** | JWT (HS256) + bcrypt | Autenticación sin estado |
| **BD** | PostgreSQL 16 | Datos transaccionales |
| **Vectorial** | pgvector | Búsqueda por similitud de embeddings |
| **Texto** | pg_trgm | Búsqueda por similitud de texto |
| **Migraciones** | Alembic 1.18 | Versionado de esquema de BD |
| **Visión** | YOLO (Ultralytics 8) | Detección de prendas |
| **Embeddings** | CLIP (ViT-B/32) | Vectores de imagen para matching |
| **Imágenes** | Cloudinary | Almacenamiento externo de imágenes |
| **Impresión** | ESCPOS / HTML / TextFile | Drivers de recibos |
| **Contenedores** | Docker + Docker Compose | Orquestación de servicios |
| **Proxy** | Nginx (Alpine) | Servidor web + proxy reverso |

---

## Decisiones de Arquitectura

| Decisión | Motivación | Ver ADR |
|----------|-----------|---------|
| PostgreSQL + pgvector | Una sola BD para datos transaccionales y vectoriales, evita sincronización | [ADR-001](adr/001-postgresql-pgvector.md) |
| YOLO + CLIP | YOLO para detección de prendas, CLIP para matching con catálogo | [ADR-002](adr/002-yolo-clip-pipeline.md) |
| Sesión dual (auth + kiosk) | Separar sesiones de admin/cajero de las de cliente kiosko | [ADR-003](adr/003-dual-session-auth.md) |
| FastAPI async | Alto rendimiento para inferencia de modelos y operaciones de BD | — |
| Docker multi-stage | Imágenes optimizadas (separar build de runtime) | — |
| Nginx proxy reverso | Evita CORS en producción, sirve SPA y API desde mismo origen | — |
| JWT sin estado | Escalabilidad horizontal sin almacenamiento de sesión centralizado | — |
