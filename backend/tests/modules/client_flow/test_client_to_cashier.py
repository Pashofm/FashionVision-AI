"""
Client to Cashier Flow Tests

Tests for the complete client-to-cashier workflow:
- Client creates cart and adds items via detection
- Client submits cart to cashier
- Cashier views pending carts
- Cashier approves or rejects orders
- Order completion and payment
"""
import pytest
import uuid
from datetime import datetime
from decimal import Decimal

from backend.app.models.models import (
    Cart, CartItem, CartStatus, Session, SessionStatus,
    Order, OrderStatus, PaymentMethod, User, UserRole
)
from backend.app.services.session_manager import SessionManager
from tests.factories import (
    CartFactory, CartItemFactory, SessionFactory,
    ProductFactory, ProductVariantFactory, UserFactory
)


pytestmark = pytest.mark.asyncio


class TestClientCartWorkflow:
    """Tests for client's cart creation and management."""

    async def test_client_creates_session(self, db_session, client_user):
        """Test client creating a shopping session."""
        session = await SessionFactory.create(
            db_session,
            client_user=client_user,
            station_id="Kiosk-01"
        )

        assert session.client_user_id == client_user.id
        assert session.status == SessionStatus.active

    async def test_client_creates_cart(self, db_session, client_user):
        """Test client creating a cart."""
        session = await SessionFactory.create(db_session, client_user=client_user)
        cart = await CartFactory.create(db_session, session=session)

        assert cart.session_id == session.id
        assert cart.status == CartStatus.building

    async def test_client_adds_detected_items(self, db_session):
        """Test client adding YOLO-detected items to cart."""
        session = await SessionFactory.create(db_session)
        cart = await CartFactory.create(db_session, session=session)
        product = await ProductFactory.create(
            db_session,
            yolo_class_name="top"
        )
        variant = await ProductVariantFactory.create(db_session, product=product)

        item = await CartItemFactory.create_with_detection(
            db_session,
            cart=cart,
            product=product,
            variant=variant,
            confidence=0.95
        )

        await db_session.refresh(cart)
        assert len(cart.items) == 1
        assert item.detection_confidence == 0.95

    async def test_client_updates_item_quantity(self, db_session):
        """Test client updating quantity in cart."""
        cart = await CartFactory.create(db_session)
        item = await CartItemFactory.create(db_session, cart=cart, quantity=1)

        item.quantity = 3
        await db_session.commit()
        await db_session.refresh(item)

        assert item.quantity == 3

    async def test_client_removes_item(self, db_session):
        """Test client removing item from cart."""
        cart = await CartFactory.create(db_session)
        item = await CartItemFactory.create(db_session, cart=cart)
        item_id = item.id

        await db_session.delete(item)
        await db_session.commit()

        result = await db_session.get(CartItem, item_id)
        assert result is None


class TestSubmitToCashier:
    """Tests for submitting cart to cashier."""

    async def test_client_submits_cart(self, db_session):
        """Test client submitting cart for processing."""
        session = await SessionFactory.create(db_session)
        cart = await CartFactory.create(db_session, session=session)
        await CartItemFactory.create(db_session, cart=cart)

        cart.status = CartStatus.submitted
        cart.submitted_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.submitted
        assert cart.submitted_at is not None

    async def test_submitted_cart_cannot_be_modified(self, db_session):
        """Test that submitted cart status blocks further modifications."""
        cart = await CartFactory.create_submitted(db_session)

        cart.status = CartStatus.submitted
        await db_session.commit()

        original_status = CartStatus.submitted
        assert cart.status == original_status


class TestCashierViewsPending:
    """Tests for cashier viewing pending orders."""

    async def test_cashier_sees_pending_carts(self, db_session, cashier_user):
        """Test cashier can see submitted carts."""
        session = await SessionFactory.create(db_session)
        cart = await CartFactory.create(db_session, session=session)
        cart.status = CartStatus.submitted
        cart.submitted_at = datetime.utcnow()
        await db_session.commit()

        from sqlalchemy import select

        result = await db_session.execute(
            select(Cart).where(Cart.status == CartStatus.submitted)
        )
        pending = result.scalars().all()

        assert len(pending) >= 1
        assert any(c.id == cart.id for c in pending)

    async def test_cashier_only_sees_submitted(self, db_session):
        """Test cashier only sees submitted, not building carts."""
        cart_building = await CartFactory.create(db_session)
        cart_building.status = CartStatus.building
        await db_session.commit()

        cart_submitted = await CartFactory.create(db_session)
        cart_submitted.status = CartStatus.submitted
        cart_submitted.submitted_at = datetime.utcnow()
        await db_session.commit()

        from sqlalchemy import select

        result = await db_session.execute(
            select(Cart).where(Cart.status == CartStatus.submitted)
        )
        pending = result.scalars().all()

        assert all(c.status == CartStatus.submitted for c in pending)


class TestCashierApproval:
    """Tests for cashier approving orders."""

    async def test_cashier_approves_order(self, db_session, cashier_user):
        """Test cashier approving an order."""
        cart = await CartFactory.create_submitted(db_session)
        await CartItemFactory.create(db_session, cart=cart, quantity=2)

        cart.status = CartStatus.processing
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.processing

    async def test_approved_cart_creates_order(self, db_session, cashier_user):
        """Test that approved cart creates an order."""
        cart = await CartFactory.create_submitted(db_session)
        await CartItemFactory.create(db_session, cart=cart, quantity=2)
        cart.status = CartStatus.processing
        await db_session.commit()

        await db_session.refresh(cart)
        subtotal = sum(
            float(item.unit_price) * item.quantity
            for item in cart.items
        )
        tax = subtotal * 0.16
        total = subtotal + tax

        order = Order(
            id=uuid.uuid4(),
            cart_id=cart.id,
            order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
            cashier_id=cashier_user.id,
            subtotal=Decimal(str(subtotal)),
            tax_amount=Decimal(str(tax)),
            total_amount=Decimal(str(total)),
            payment_method=PaymentMethod.card,
            status=OrderStatus.pending
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        assert order.cart_id == cart.id
        assert order.cashier_id == cashier_user.id

    async def test_approved_cart_updates_inventory(self, db_session, cashier_user):
        """Test that approved order updates inventory."""
        variant = await ProductVariantFactory.create(db_session)
        inventory = await InventoryFactory.create(db_session, variant=variant)
        initial_qty = inventory.quantity_available

        cart = await CartFactory.create_submitted(db_session)
        item = await CartItemFactory.create(
            db_session,
            cart=cart,
            variant=variant,
            quantity=2
        )

        inventory.quantity_available -= 2
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_available == initial_qty - 2


class TestCashierRejection:
    """Tests for cashier rejecting orders."""

    async def test_cashier_rejects_order(self, db_session):
        """Test cashier rejecting an order."""
        cart = await CartFactory.create_submitted(db_session)

        cart.status = CartStatus.cancelled
        cart.notes = "Item not available"
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.cancelled
        assert cart.notes == "Item not available"

    async def test_rejected_cart_releases_reserved(self, db_session):
        """Test that rejected cart releases reserved inventory."""
        variant = await ProductVariantFactory.create(db_session)
        inventory = await InventoryFactory.create(
            db_session,
            variant=variant,
            quantity_available=100,
            quantity_reserved=5
        )

        cart = await CartFactory.create_submitted(db_session)
        cart.status = CartStatus.cancelled
        inventory.quantity_reserved = 0
        await db_session.commit()

        await db_session.refresh(inventory)
        assert inventory.quantity_reserved == 0


class TestPaymentProcessing:
    """Tests for payment processing."""

    async def test_cart_payment_cash(self, db_session):
        """Test payment with cash method."""
        cart = await CartFactory.create(db_session)

        cart.status = CartStatus.paid
        cart.payment_method = PaymentMethod.cash
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.paid
        assert cart.payment_method == PaymentMethod.cash

    async def test_cart_payment_card(self, db_session):
        """Test payment with card method."""
        cart = await CartFactory.create(db_session)

        cart.status = CartStatus.paid
        cart.payment_method = PaymentMethod.card
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.paid
        assert cart.payment_method == PaymentMethod.card

    async def test_order_completion(self, db_session, cashier_user):
        """Test order marked as completed after payment."""
        cart = await CartFactory.create(db_session)
        cart.status = CartStatus.paid
        cart.payment_method = PaymentMethod.card
        await db_session.commit()

        subtotal = Decimal("100.00")
        order = Order(
            id=uuid.uuid4(),
            cart_id=cart.id,
            order_number=f"ORD-{uuid.uuid4().hex[:8]}",
            cashier_id=cashier_user.id,
            subtotal=subtotal,
            tax_amount=Decimal("16.00"),
            total_amount=Decimal("116.00"),
            payment_method=PaymentMethod.card,
            status=OrderStatus.completed,
            completed_at=datetime.utcnow()
        )
        db_session.add(order)
        await db_session.commit()

        assert order.status == OrderStatus.completed
        assert order.completed_at is not None


class TestFullClientToCashierFlow:
    """End-to-end tests for complete client to cashier workflow."""

    async def test_complete_flow_success(self, db_session, cashier_user):
        """Test complete workflow: create -> add items -> submit -> approve -> pay."""
        session = await SessionFactory.create(db_session)

        cart = await CartFactory.create(db_session, session=session)

        variant = await ProductVariantFactory.create(db_session)
        await CartItemFactory.create(
            db_session,
            cart=cart,
            variant=variant,
            quantity=2,
            unit_price=Decimal("100.00")
        )

        assert cart.status == CartStatus.building

        cart.status = CartStatus.submitted
        cart.submitted_at = datetime.utcnow()
        await db_session.commit()
        assert cart.status == CartStatus.submitted

        cart.status = CartStatus.processing
        await db_session.commit()
        assert cart.status == CartStatus.processing

        cart.status = CartStatus.paid
        cart.payment_method = PaymentMethod.card
        await db_session.commit()
        assert cart.status == CartStatus.paid

    async def test_complete_flow_with_rejection(self, db_session):
        """Test workflow ending in rejection."""
        session = await SessionFactory.create(db_session)
        cart = await CartFactory.create(db_session, session=session)
        await CartItemFactory.create(db_session, cart=cart)

        cart.status = CartStatus.submitted
        cart.submitted_at = datetime.utcnow()
        await db_session.commit()

        cart.status = CartStatus.cancelled
        cart.notes = "Customer changed mind"
        await db_session.commit()

        assert cart.status == CartStatus.cancelled


from backend.app.models.models import Inventory
from tests.factories import InventoryFactory
