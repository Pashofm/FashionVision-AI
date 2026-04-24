# FashionVision-AI Testing Guide

Comprehensive guide for testing the FashionVision-AI system.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Test Structure](#test-structure)
4. [Running Tests](#running-tests)
5. [Writing Tests](#writing-tests)
6. [Factories](#factories)
7. [Fixtures](#fixtures)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The testing infrastructure provides:

- **PostgreSQL-based testing** with automatic database setup/teardown
- **Factory pattern** for creating test data with unique identifiers
- **Automatic rollback** after each test for isolation
- **Module-based organization** for easy navigation
- **Coverage reporting** capabilities

### Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Unit Tests | `tests/modules/*/test_*_unit.py` | Test individual functions/methods |
| Integration Tests | `tests/modules/*/test_*_api.py` | Test API endpoints |
| E2E Tests | `tests/modules/*/test_client_to_cashier.py` | Test complete workflows |

---

## Quick Start

### 1. Setup Test Database

```bash
cd backend
./scripts/setup_test_db.sh
```

### 2. Run All Tests

```bash
cd backend
./scripts/run_tests.sh
```

### 3. Run with Coverage

```bash
./scripts/run_tests.sh --coverage
```

---

## Test Structure

```
backend/tests/
├── conftest.py                 # Main fixtures and configuration
├── factories/                  # Factory functions for test data
│   ├── __init__.py
│   ├── base.py                # BaseFactory class
│   ├── user_factory.py        # User creation
│   ├── category_factory.py    # Category creation
│   ├── product_factory.py     # Product & Variant creation
│   ├── inventory_factory.py   # Inventory & Movement creation
│   └── cart_factory.py        # Cart, CartItem, Session creation
├── modules/                   # Tests organized by domain
│   ├── inventory/
│   │   ├── test_inventory_unit.py
│   │   └── test_inventory_api.py
│   ├── client_flow/
│   │   ├── test_detection.py
│   │   ├── test_cart.py
│   │   └── test_client_to_cashier.py
│   └── sessions/
│       ├── test_session_unit.py
│       └── test_session_api.py
├── test_auth.py              # Auth service tests
├── test_pos_terminal.py      # POS terminal tests
└── scripts/
    ├── setup_test_db.sh
    ├── run_tests.sh
    └── teardown_test_db.sh
```

---

## Running Tests

### Using Scripts (Recommended)

```bash
# Setup database
./scripts/setup_test_db.sh

# Run all tests
./scripts/run_tests.sh

# Run with coverage
./scripts/run_tests.sh --coverage

# Run specific module
./scripts/run_tests.sh --module sessions

# Run with verbose output
./scripts/run_tests.sh --verbose
```

### Using pytest Directly

```bash
# Set environment
export SKIP_DB_TESTS=false
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5433/fashionvision_ai_test"
export PYTHONPATH=/path/to/project

# Run all tests
python -m pytest tests/ -v

# Run specific file
python -m pytest tests/modules/sessions/test_session_unit.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SKIP_DB_TESTS` | `false` | Skip database tests |
| `TEST_DATABASE_URL` | (see conftest.py) | PostgreSQL connection string |
| `PYTHONPATH` | project root | Python path for imports |

---

## Writing Tests

### Basic Test Structure

```python
import pytest
from tests.factories import UserFactory, ProductFactory

pytestmark = pytest.mark.asyncio

class TestMyFeature:
    """Tests for my feature."""

    async def test_basic_functionality(self, db_session):
        """Test basic functionality."""
        # Use db_session for database operations
        user = await UserFactory.create(db_session)
        assert user.id is not None

    async def test_with_fixture(self, admin_user):
        """Test using pre-defined fixtures."""
        assert admin_user.role == UserRole.admin
```

### Using Factories

```python
# Create a user
user = await UserFactory.create(db_session)

# Create with custom values
product = await ProductFactory.create(
    db_session,
    name="Custom Product",
    base_price=Decimal("49.99")
)

# Create with relationships
variant, product = await ProductVariantFactory.create_with_product(db_session)
```

### API Testing

```python
async def test_create_product(self, authenticated_client, test_category):
    """Test creating a product via API."""
    response = await authenticated_client.post("/api/products", json={
        "name": "New Product",
        "category_id": str(test_category.id),
        "sku": "NEW-001",
        "base_price": 99.99
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Product"
```

---

## Factories

Factories provide a convenient way to create test data with automatic unique identifiers.

### Available Factories

| Factory | Creates | Key Methods |
|---------|---------|-------------|
| `UserFactory` | User | `create_admin()`, `create_cashier()`, `create_client()` |
| `CategoryFactory` | Category | `create()` |
| `ProductFactory` | Product | `create()`, `create_with_category()` |
| `ProductVariantFactory` | ProductVariant | `create()`, `create_with_product()`, `create_batch_sizes()` |
| `InventoryFactory` | Inventory | `create()`, `create_with_variant()`, `create_low_stock()` |
| `InventoryMovementFactory` | InventoryMovement | `create()`, `build_sale()`, `build_restock()` |
| `CartFactory` | Cart | `create()`, `create_with_session()`, `create_with_items()` |
| `CartItemFactory` | CartItem | `create()`, `create_with_detection()` |
| `SessionFactory` | Session | `create()`, `create_with_user()`, `create_abandoned()` |

### Factory Methods

```python
# Build (don't save)
data = UserFactory.build(name="Test")

# Create (save to DB)
user = await UserFactory.create(db_session)

# Create with specific values
admin = await UserFactory.create(db_session, role=UserRole.admin)

# Create batch
users = await UserFactory.create_batch(db_session, count=5)
```

---

## Fixtures

Fixtures are provided by `conftest.py` and available in all tests.

### Database Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `db_session` | AsyncSession | Database session with auto-rollback |
| `test_engine` | Engine | SQLAlchemy engine |
| `setup_database` | Session scope | Creates/drops schema |

### Auth Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `admin_user` | User | Admin user |
| `cashier_user` | User | Cashier user |
| `client_user` | User | Client user |
| `authenticated_client` | AsyncClient | HTTP client with admin auth |
| `authenticated_admin_client` | AsyncClient | HTTP client with admin auth |
| `authenticated_cashier_client` | AsyncClient | HTTP client with cashier auth |

### Model Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `test_category` | Category | Test category |
| `test_product` | Product | Test product |
| `test_variant` | ProductVariant | Test variant |
| `test_inventory` | Inventory | Test inventory |
| `test_session` | Session | Test session |
| `test_cart` | Cart | Test cart |
| `test_cart_item` | CartItem | Test cart item |
| `test_order` | Order | Test order |

### HTTP Client Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `client` | AsyncClient | Unauthenticated HTTP client |
| `authenticated_client` | AsyncClient | Authenticated HTTP client |

---

## Troubleshooting

### Database Connection Issues

```
Error: could not connect to server
```

**Solution:** Ensure PostgreSQL is running and the test database exists:

```bash
./scripts/setup_test_db.sh
```

### Import Errors

```
ModuleNotFoundError: No module named 'backend'
```

**Solution:** Set PYTHONPATH:

```bash
export PYTHONPATH=/path/to/project
```

### Unique Constraint Violations

```
IntegrityError: duplicate key value violates unique constraint
```

**Solution:** This shouldn't happen with factories (they generate unique names). If it occurs, check that:
1. You're using the factory's `create()` method, not direct model instantiation
2. The database session is being rolled back properly

### Async Issues

```
RuntimeError: Event loop is closed
```

**Solution:** Ensure you're using `@pytest.mark.asyncio` on async tests.

---

## Best Practices

1. **Use factories** for creating test data - they handle uniqueness automatically
2. **Don't modify shared fixtures** - create new objects instead
3. **One assertion per test** when possible - makes debugging easier
4. **Use descriptive names** - `test_cart_total_with_multiple_items` not `test_cart`
5. **Test edge cases** - empty inputs, boundary values, error conditions
6. **Keep tests independent** - don't rely on execution order
7. **Use rollback** - db_session auto-rollbacks, don't commit manually

---

## Coverage Goals

Target coverage by module:

| Module | Target | Current |
|--------|--------|---------|
| Models | 90% | - |
| Services | 80% | - |
| API Endpoints | 70% | - |
| **Overall** | **80%** | - |

Generate coverage report:

```bash
./scripts/run_tests.sh --coverage
open htmlcov/index.html
```
