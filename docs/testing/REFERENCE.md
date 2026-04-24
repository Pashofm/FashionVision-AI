# Testing Reference

Quick reference for testing FashionVision-AI.

## Common Patterns

### Testing Database Operations

```python
async def test_example(self, db_session):
    # Create using factory
    user = await UserFactory.create(db_session)

    # Query
    result = await db_session.get(User, user.id)

    # Assert
    assert result.id == user.id
```

### Testing API Endpoints

```python
async def test_api_endpoint(self, authenticated_client):
    response = await authenticated_client.get("/api/endpoint")

    assert response.status_code == 200
    assert "data" in response.json()
```

### Testing Session Management

```python
async def test_session(self, db_session):
    from backend.app.services.session_manager import SessionManager

    # Create session
    session = await SessionFactory.create(db_session)

    # Test activity update
    result = await SessionManager.update_activity(db_session, session.id)
    assert result is True

    # Test is active
    is_active = await SessionManager.is_session_active(db_session, session.id)
    assert is_active is True
```

### Testing Inventory Operations

```python
async def test_inventory_adjustment(self, db_session):
    inventory = await InventoryFactory.create(db_session, quantity_available=100)

    # Create movement
    movement = InventoryMovement(
        id=uuid.uuid4(),
        product_variant_id=inventory.product_variant_id,
        movement_type=MovementType.adjustment,
        quantity_change=-5,
        quantity_before=100,
        quantity_after=95
    )
    db_session.add(movement)

    # Update inventory
    inventory.quantity_available = 95
    await db_session.commit()
    await db_session.refresh(inventory)

    assert inventory.quantity_available == 95
```

### Testing Cart Workflow

```python
async def test_cart_workflow(self, db_session):
    # Create session and cart
    cart = await CartFactory.create_with_items(db_session, item_count=3)

    # Submit
    cart.status = CartStatus.submitted
    cart.submitted_at = datetime.utcnow()
    await db_session.commit()

    # Verify
    assert cart.status == CartStatus.submitted
```

## Session Status Enum

```python
from backend.app.models.models import SessionStatus

SessionStatus.active      # Session is active
SessionStatus.completed   # Session completed normally
SessionStatus.abandoned   # Session was abandoned/expired
```

## Cart Status Enum

```python
from backend.app.models.models import CartStatus

CartStatus.building      # Cart being built
CartStatus.submitted      # Submitted to cashier
CartStatus.processing     # Being processed by cashier
CartStatus.paid           # Payment completed
CartStatus.cancelled      # Order cancelled
```

## Movement Types

```python
from backend.app.models.models import MovementType

MovementType.sale         # Sale transaction (decreases inventory)
MovementType.restock      # Restock (increases inventory)
MovementType.adjustment    # Manual adjustment
MovementType.return_item   # Item returned
MovementType.reserved      # Reserved for order
MovementType.released      # Released from reservation
```

## User Roles

```python
from backend.app.models.models import UserRole

UserRole.admin     # Administrator
UserRole.cashier   # Cashier
UserRole.client    # Client (kiosk user)
```

## Payment Methods

```python
from backend.app.models.models import PaymentMethod

PaymentMethod.cash    # Cash payment
PaymentMethod.card     # Card payment
PaymentMethod.mixed    # Mixed payment
```

## Order Status

```python
from backend.app.models.models import OrderStatus

OrderStatus.pending           # Order created, awaiting completion
OrderStatus.completed         # Order completed
OrderStatus.refunded          # Order refunded
OrderStatus.partially_refunded # Partially refunded
```

## Key Imports

```python
# Models
from backend.app.models.models import (
    User, Category, Product, ProductVariant,
    Inventory, InventoryMovement,
    Session, Cart, CartItem,
    Order, OrderItem, Receipt
)

# Enums
from backend.app.models.models import (
    UserRole, SessionStatus, CartStatus,
    MovementType, PaymentMethod, OrderStatus
)

# Services
from backend.app.services.session_manager import SessionManager
from backend.app.services.detection import detect_in_image, get_model_classes

# Factories
from tests.factories import (
    UserFactory, CategoryFactory,
    ProductFactory, ProductVariantFactory,
    InventoryFactory, InventoryMovementFactory,
    CartFactory, CartItemFactory, SessionFactory
)
```

## Environment Setup

```bash
# Required environment variables
export SKIP_DB_TESTS=false
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5433/fashionvision_ai_test"
export PYTHONPATH=/path/to/project
```

## Running Specific Tests

```bash
# Single test file
pytest tests/modules/sessions/test_session_unit.py -v

# Single test class
pytest tests/modules/sessions/test_session_unit.py::TestSessionCreation -v

# Single test
pytest tests/modules/sessions/test_session_unit.py::TestSessionCreation::test_create_session -v

# Using keyword filter
pytest -k "session" -v

# Using marker
pytest -m asyncio -v
```
