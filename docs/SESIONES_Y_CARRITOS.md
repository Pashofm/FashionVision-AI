# Sistema de Sesiones y Carritos

## Índice

1. [Arquitectura General](#arquitectura-general)
2. [Flujo de Sesiones](#flujo-de-sesiones)
3. [Flujo de Carritos](#flujo-de-carritos)
4. [Endpoints de API](#endpoints-de-api)
5. [Gestión de Tiempo y Timezones](#gestión-de-tiempo-y-timezones)
6. [Expiración Automática](#expiración-automática)
7. [Diagrama de Estados](#diagrama-de-estados)
8. [Recuperación ante Recargas](#recuperación-ante-recargas)

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                              │
│  ClientDetection.jsx                                                     │
│  - Crea sesión/cart al iniciar                                          │
│  - Persiste sessionId/cartId en localStorage                            │
│  - Al recargar, recupera sesión existente                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ POST /api/sessions
                                 │ POST /api/carts/by-session/{session_id}
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                             │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   Sessions   │    │    Carts     │    │  CartItems   │             │
│  │   Service    │    │   Service    │    │   Service    │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         │                   │                   │                      │
│         ▼                   ▼                   ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                   SessionManager                             │       │
│  │  - create_session()      - expire_inactive_sessions()        │       │
│  │  - update_activity()    - is_session_active()                │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                 │                                       │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                                  │  │
│  │  sessions ──► carts ──► cart_items                              │  │
│  │  (timeout 30min)   (building/submitted/processing/paid)         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Background Task: cleanup cada 5 minutos                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Flujo de Sesiones

### Inicio de Sesión del Cliente

```
1. Cliente accede a /cliente
   └─► ClientDetection.jsx useEffect llama initSession()

2. initSession() verifica localStorage
   ├─► Si existe sessionId/cartId:
   │   └─► GET /api/carts/{cartId} → recupera carrito existente
   │       └─► Si existe y está "building" → carga items al estado React
   │
   └─► Si NO existe o falló:
       └─► POST /api/sessions → crea nueva sesión
           └─► GET /api/carts/by-session/{sessionId} → crea carrito "building"
               └─► Guarda sessionId/cartId en localStorage
```

### Archivos Relacionados

- **Frontend**: `frontend/src/pages/ClientDetection.jsx` (líneas 58-105)
- **Backend**: `backend/app/main.py` - endpoint `POST /api/sessions`
- **Modelo**: `backend/app/models/models.py` - clase `DbSession`

### Persistencia en localStorage

```javascript
const STORAGE_KEY_SESSION = 'client_session_id';
const STORAGE_KEY_CART = 'client_cart_id';

// Al guardar
localStorage.setItem(STORAGE_KEY_SESSION, session.id);
localStorage.setItem(STORAGE_KEY_CART, cart.id);

// Al recuperar
const sessionId = localStorage.getItem(STORAGE_KEY_SESSION);
const cartId = localStorage.getItem(STORAGE_KEY_CART);
```

---

## Flujo de Carritos

### Estados del Carrito

| Estado | Descripción | Transiciones Permitidas |
|--------|-------------|------------------------|
| `building` | Cliente agregando items | `submitted`, `cancelled` |
| `submitted` | Enviado, esperando admin | `processing`, `cancelled` |
| `processing` | Admin procesando | `paid`, `cancelled` |
| `paid` | Completado | (ninguna) |
| `cancelled` | Cancelado | (ninguna) |

### Agregar Producto

```
1. Cliente detecta prenda → YOLO
2. Cliente selecciona producto
3. Click "Agregar al Carrito"
   └─► POST /api/carts/{cartId}/items
       {
         product_id: "uuid",
         quantity: 1,
         unit_price: 299.99,
         detection_confidence: 0.85
       }

4. Backend:
   ├─► Valida que el carrito existe
   ├─► Crea CartItem con ID único (UUID)
   ├─► Retorna CartItemResponse con el ID real

5. Frontend recibe newItem.id y actualiza estado:
   └─► setCarrito(prev => [...prev, { ...producto, cartItemId: newItem.id }])
```

**Importante**: El `cartItemId` usado es el UUID real del backend, no `Date.now()`.

### Eliminar Producto

```
1. Cliente click en eliminar (🗑️)
   └─► DELETE /api/carts/{cartId}/items/{cartItemId}

2. Backend:
   ├─► Valida que item existe y pertenece al carrito
   ├─► DELETE FROM cart_items WHERE id = cartItemId
   └─► Retorna {"message": "Item removed"}

3. Frontend:
   ├─► Si exitoso → setCarrito(prev => prev.filter(...))
   └─► Si falla → muestra error
```

### Enviar Carrito a Caja (Submit)

```
1. Cliente click "Enviar a Caja"
   └─► PUT /api/carts/{cartId}
       { status: "submitted" }

2. Backend valida transición:
   ├─► building → submitted ✓ (válida)
   ├─► Actualiza status del carrito
   └─► Trigger en BD actualiza submitted_at

3. Frontend:
   ├─► setCarrito([])
   ├─► clearSession() → limpia localStorage
   ├─► Crea nuevo session + cart
   └─► Alert "Pedido enviado a caja"
```

---

## Endpoints de API

### Sesiones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/sessions` | Crear nueva sesión |
| GET | `/api/sessions` | Listar todas las sesiones |
| GET | `/api/sessions/{id}` | Obtener sesión por ID |
| POST | `/api/sessions/cleanup` | Limpiar sesiones expiradas |

### Carritos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/carts` | Crear carrito |
| GET | `/api/carts` | Listar carritos (filtro por session_id, status) |
| GET | `/api/carts/{id}` | Obtener carrito con items |
| GET | `/api/carts/by-session/{session_id}` | Obtener o crear carrito para sesión |
| PUT | `/api/carts/{id}` | Actualizar carrito (status, notes, payment_method) |
| DELETE | `/api/carts/{id}` | Eliminar carrito |

### Items del Carrito

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/carts/{cart_id}/items` | Agregar item al carrito |
| GET | `/api/carts/{cart_id}/items` | Listar items del carrito |
| DELETE | `/api/carts/{cart_id}/items/{item_id}` | Eliminar item |

---

## Gestión de Tiempo y Timezones

### Arquitectura de Timezone

El sistema maneja tres zonas horarias:

1. **UTC**: Almacenamiento interno en PostgreSQL
2. **Servidor**: `America/Mazatlan` (MST) por defecto
3. **Cliente**: Detectada automáticamente o por header `X-Timezone`

### Servicio de Timezone

Ubicación: `backend/app/services/timezone_service.py`

```python
from backend.app.services.timezone_service import (
    get_current_utc_time,    # datetime.now(timezone.utc)
    get_server_time,          # datetime.now(America/Mazatlan)
    utc_to_local,             # Convierte UTC a timezone del cliente
    local_to_utc,             # Convierte hora local a UTC
    get_timezone_from_request # Detecta timezone del request
)
```

### Headers de Cliente

```javascript
// Para especificar timezone manualmente
headers: { 'X-Timezone': 'America/Mexico_City' }

// O automáticamente por Accept-Language
headers: { 'Accept-Language': 'es-MX' }
```

### Detección Automática

```python
# Se detecta en orden:
# 1. Header X-Timezone (explícito)
# 2. Accept-Language (país)
# 3. DEFAULT_TIMEZONE del config (America/Mazatlan)
```

---

## Expiración Automática

### Configuración

```python
# backend/app/config.py
SESSION_TIMEOUT_MINUTES: int = 30  # 30 minutos de inactividad
```

### Background Task

El cleanup se ejecuta automáticamente cada **5 minutos** via `periodic_session_cleanup()` en el lifespan de FastAPI:

```python
async def periodic_session_cleanup(app: FastAPI):
    while True:
        await asyncio.sleep(300)  # 5 minutos
        async with _cleanup_lock:  # Previene ejecuciones concurrentes
            async with AsyncSessionLocal() as db:
                expired_count = await SessionManager.expire_inactive_sessions(db)
```

### Proceso de Cleanup

```
1. Buscar sesiones activas con last_activity_at < NOW() - 30 minutos

2. Marcar como abandonadas:
   UPDATE sessions
   SET status = 'abandoned', ended_at = NOW()
   WHERE status = 'active' AND last_activity_at < cutoff

3. Cancelar carritos huérfanos:
   UPDATE carts
   SET status = 'cancelled'
   WHERE status = 'building'
   AND session_id IN (SELECT id FROM sessions WHERE status != 'active')
```

### Cleanup Manual

```bash
curl -X POST http://localhost:8000/api/sessions/cleanup
```

Respuesta:
```json
{
  "success": true,
  "expired_sessions": 5,
  "cancelled_carts": 3
}
```

---

## Diagrama de Estados

```
┌────────────────────────────────────────────────────────────────────────┐
│                         CICLO DE VIDA DEL CARRITO                      │
└────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │              │
                    │   building   │ ◄── Cliente agrega items
                    │              │     POST /api/carts/{id}/items
                    └──────┬───────┘
                           │
                           │ PUT /api/carts/{id} { status: "submitted" }
                           │
                           ▼
                    ┌──────────────┐       ┌──────────────┐
        ┌───────────│              │       │              │
        │           │  submitted   │──────►│  cancelled   │
        │           │              │  PUT   │              │
        │           └──────┬───────┘  {     └──────────────┘
        │                  │       status:  │      ▲
        │                  │     "cancelled"│      │
        │                  │                 │      │
        │                  │ PUT { status:   │      │
        │                  │   "processing"} │      │
        │                  │                 │      │
        │                  ▼                 │      │
        │           ┌──────────────┐         │      │
        │           │              │         │      │
        │           │  processing  │─────────┘      │
        │           │              │ PUT { status:    │
        │           └──────┬───────┘   "cancelled"   │
        │                  │                         │
        │                  │ PUT { status: "paid" }  │
        │                  │    + payment_method     │
        │                  ▼                         │
        │           ┌──────────────┐                │
        │           │              │                │
        └──────────►│     paid     │                │
                    │              │                │
                    └──────────────┘                │
                              (completado)          │
                                                  │
                    Cualquier estado puede ser ────┘
                    cancelado por timeout automático
```

### Validación de Transiciones

```python
VALID_TRANSITIONS = {
    'building':   ['submitted', 'cancelled'],
    'submitted':  ['processing', 'cancelled'],
    'processing': ['paid', 'cancelled'],
    'paid':       [],
    'cancelled':  []
}
```

**Ejemplo de error:**
```bash
PUT /api/carts/{id} { "status": "submitted" }
# Si el carrito ya está "submitted" → 400 Bad Request

{
  "detail": "Invalid status transition from 'submitted' to 'submitted'. 
             Allowed transitions: ['processing', 'cancelled']"
}
```

---

## Recuperación ante Recargas

### Problema Original

Cuando un cliente recarga la página, se perdían los productos agregados al carrito porque:
1. Se creaba una nueva sesión
2. Se creaba un nuevo carrito
3. El carrito anterior quedaba huérfano

### Solución Implementada

```javascript
// initSession() en ClientDetection.jsx

1. Lee sessionId/cartId de localStorage

2. Intenta recuperar carrito existente:
   GET /api/carts/{cartId}
   
3. Si existe y está "building":
   - Carga items al estado React
   - Continua con la sesión

4. Si falla (no existe o está en otro estado):
   - Crea nueva sesión
   - Crea nuevo carrito
```

### Flujo Completo de Recuperación

```
1. Page reload → useEffect ejecuta initSession()

2. Lee localStorage:
   ├─► sessionId = "16e40a9d-65f4-47d2-9182-c0c3073b4a4c"
   └─► cartId = "2973782b-a401-4f16-bc51-7f3408dc91bc"

3. GET /api/carts/2973782b...
   └─► Backend retorna carrito + items (con relaciones cargadas via selectinload)

4. Frontend sincroniza estado:
   └─► setCarrito(items.map(item => ({
         name: item.product.name,
         price: item.unit_price,
         cartItemId: item.id  ← UUID real del backend
       })))
```

### Beneficios

- ✅ Productos persisten al recargar
- ✅ Sesión se mantiene si el carrito existe
- ✅ No se crean carritos duplicados
- ✅ Limpieza automática de sesiones abandonadas

---

## Estructura de Archivos

| Archivo | Descripción |
|---------|-------------|
| `backend/app/main.py` | Endpoints de API, lifespan, periodic cleanup |
| `backend/app/services/session_manager.py` | Lógica de sesiones, expiración |
| `backend/app/services/timezone_service.py` | Conversión de timezones |
| `backend/app/models/models.py` | Modelos SQLAlchemy (DbSession, Cart, CartItem) |
| `backend/app/schemas/schemas.py` | Schemas Pydantic para validación |
| `frontend/src/pages/ClientDetection.jsx` | UI del cliente, gestión de carrito |
| `frontend/src/services/api.js` | Funciones de API para frontend |

---

## Comandos Útiles

### Ver sesiones activas
```sql
SELECT id, station_id, status, last_activity_at,
       (NOW() - last_activity_at) as idle
FROM sessions
WHERE status = 'active'
ORDER BY last_activity_at;
```

### Ver carritos por estado
```sql
SELECT status, COUNT(*) as total
FROM carts
GROUP BY status;
```

### Forzar cleanup manual
```bash
curl -X POST http://localhost:8000/api/sessions/cleanup
```

### Ver carritos huérfanos (sin items y building)
```sql
SELECT c.id, c.created_at
FROM carts c
LEFT JOIN cart_items ci ON ci.cart_id = c.id
WHERE c.status = 'building'
GROUP BY c.id, c.created_at
HAVING COUNT(ci.id) = 0;
```