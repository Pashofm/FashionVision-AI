"""
Test Configuration and Fixtures

This module provides:
- Database session fixtures with automatic rollback
- HTTP client fixtures for API testing
- Authentication fixtures
- Import of factory classes

All tests use PostgreSQL with automatic cleanup after each test.
"""
import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("SKIP_DB_TESTS", "false")

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://fashionvision_ai_user:fashionvision_ai_pass@localhost:5433/fashionvision_ai_test"
)

SKIP_DB_TESTS = os.environ.get("SKIP_DB_TESTS", "false").lower() == "true"

pytestmark = pytest.mark.skipif(
    SKIP_DB_TESTS,
    reason="Database tests skipped (set SKIP_DB_TESTS=false to run with PostgreSQL)"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    """Setup database schema before tests and cleanup after."""
    from backend.app.database import Base
    from backend.app.models.models import (
        User, UserRole, Category, Product, ProductVariant,
        Inventory, InventoryMovement, MovementType, Session, SessionStatus,
        Cart, CartItem, CartStatus, Order, OrderItem, OrderStatus,
        PaymentMethod, Receipt, PaymentQueue, QueueStatus, QueuePriority,
        DailySalesSummary
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database, test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for each test with automatic rollback.

    Each test gets a fresh session. After the test completes (pass or fail),
    all changes are rolled back automatically. This ensures test isolation
    without needing to manually clean up data.
    """
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    await session.close()


@pytest.fixture
async def client(db_session) -> AsyncGenerator:
    """Provide HTTP client for API testing."""
    from backend.app.main import app
    from backend.app.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session) -> "User":
    """Create an admin user for testing."""
    from backend.app.models.models import User, UserRole
    from backend.app.services.auth import hash_password
    import uuid

    user = User(
        id=uuid.uuid4(),
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password("admin123"),
        role=UserRole.admin,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def cashier_user(db_session) -> "User":
    """Create a cashier user for testing."""
    from backend.app.models.models import User, UserRole
    from backend.app.services.auth import hash_password
    import uuid

    user = User(
        id=uuid.uuid4(),
        name="Cashier User",
        email=f"cashier_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password("cashier123"),
        role=UserRole.cashier,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client_user(db_session) -> "User":
    """Create a client user for testing."""
    from backend.app.models.models import User, UserRole
    from backend.app.services.auth import hash_password
    import uuid

    user = User(
        id=uuid.uuid4(),
        name="Client User",
        email=f"client_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password("client123"),
        role=UserRole.client,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def authenticated_admin_client(client, admin_user) -> AsyncClient:
    """HTTP client with admin authentication."""
    from backend.app.services.auth import create_access_token

    token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest.fixture
async def authenticated_cashier_client(client, cashier_user) -> AsyncClient:
    """HTTP client with cashier authentication."""
    from backend.app.services.auth import create_access_token

    token = create_access_token({"sub": str(cashier_user.id), "role": cashier_user.role.value})
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest.fixture
async def authenticated_client(client, admin_user) -> AsyncClient:
    """HTTP client with admin authentication (alias for authenticated_admin_client)."""
    from backend.app.services.auth import create_access_token

    token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest.fixture
async def test_category(db_session) -> "Category":
    """Create a test category."""
    from backend.app.models.models import Category
    import uuid

    category = Category(
        id=uuid.uuid4(),
        name=f"Test Category {uuid.uuid4().hex[:8]}",
        description="Test category description",
        icon="test-icon",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
async def test_product(db_session, test_category) -> "Product":
    """Create a test product."""
    from backend.app.models.models import Product
    import uuid
    from decimal import Decimal

    product = Product(
        id=uuid.uuid4(),
        category_id=test_category.id,
        name=f"Test Product {uuid.uuid4().hex[:8]}",
        description="Test product description",
        sku=f"SKU-{uuid.uuid4().hex[:8]}",
        base_price=Decimal("99.99"),
        yolo_class_name=f"test_class_{uuid.uuid4().hex[:6]}",
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def test_variant(db_session, test_product) -> "ProductVariant":
    """Create a test product variant."""
    from backend.app.models.models import ProductVariant
    import uuid
    from decimal import Decimal

    variant = ProductVariant(
        id=uuid.uuid4(),
        product_id=test_product.id,
        size="M",
        color="Red",
        color_hex="#FF0000",
        sku_variant=f"VAR-{uuid.uuid4().hex[:8]}",
        price_modifier=Decimal("10.00"),
        is_active=True
    )
    db_session.add(variant)
    await db_session.commit()
    await db_session.refresh(variant)
    return variant


@pytest.fixture
async def test_inventory(db_session, test_variant, admin_user) -> "Inventory":
    """Create test inventory."""
    from backend.app.models.models import Inventory
    import uuid

    inventory = Inventory(
        id=uuid.uuid4(),
        product_variant_id=test_variant.id,
        quantity_available=100,
        quantity_reserved=0,
        low_stock_threshold=10,
        updated_by=admin_user.id
    )
    db_session.add(inventory)
    await db_session.commit()
    await db_session.refresh(inventory)
    return inventory


@pytest.fixture
async def test_session(db_session, client_user) -> "Session":
    """Create a test session."""
    from backend.app.models.models import Session, SessionStatus
    import uuid

    session = Session(
        id=uuid.uuid4(),
        session_token=uuid.uuid4(),
        client_user_id=client_user.id,
        station_id="Kiosk-01",
        status=SessionStatus.active
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def test_cart(db_session, test_session) -> "Cart":
    """Create a test cart."""
    from backend.app.models.models import Cart, CartStatus
    import uuid

    cart = Cart(
        id=uuid.uuid4(),
        session_id=test_session.id,
        status=CartStatus.building
    )
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)
    return cart


@pytest.fixture
async def test_cart_item(db_session, test_cart, test_product, test_variant) -> "CartItem":
    """Create a test cart item."""
    from backend.app.models.models import CartItem
    import uuid
    from decimal import Decimal

    cart_item = CartItem(
        id=uuid.uuid4(),
        cart_id=test_cart.id,
        product_id=test_product.id,
        product_variant_id=test_variant.id,
        quantity=2,
        unit_price=Decimal("109.99"),
        detection_confidence=0.95,
        confirmed=True
    )
    db_session.add(cart_item)
    await db_session.commit()
    await db_session.refresh(cart_item)
    return cart_item


@pytest.fixture
async def test_order(db_session, test_cart, cashier_user) -> "Order":
    """Create a test order."""
    from backend.app.models.models import Order, OrderStatus, PaymentMethod
    import uuid
    from decimal import Decimal

    order = Order(
        id=uuid.uuid4(),
        cart_id=test_cart.id,
        order_number=f"ORD-{uuid.uuid4().hex[:8]}",
        cashier_id=cashier_user.id,
        subtotal=Decimal("219.98"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("35.20"),
        total_amount=Decimal("255.18"),
        payment_method=PaymentMethod.card,
        status=OrderStatus.pending
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


class BaseTest:
    """
    Base test class providing common test functionality.

    Subclasses can use:
    - self.db_session: Database session with auto-rollback
    - self.client: HTTP client for API testing
    - Factories imported from tests.factories

    Example:
        class TestMyFeature(BaseTest):
            async def test_something(self, admin_user):
                user = await UserFactory.create(self.db_session)
                ...
    """

    @pytest.fixture(autouse=True)
    async def setup_test(self, db_session):
        """Setup each test with database session."""
        self.db_session = db_session
        yield
        await db_session.rollback()
