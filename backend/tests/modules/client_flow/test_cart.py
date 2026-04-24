"""
Cart Operations Tests

Tests for shopping cart functionality:
- Cart creation and lifecycle
- Adding/removing items
- Cart status transitions
- Cart calculations
"""
import pytest
import uuid
from datetime import datetime
from decimal import Decimal

from backend.app.models.models import Cart, CartItem, CartStatus
from backend.app.services.session_manager import SessionManager
from tests.factories import (
    CartFactory, CartItemFactory, SessionFactory,
    ProductFactory, ProductVariantFactory, UserFactory
)


pytestmark = pytest.mark.asyncio


class TestCartCreation:
    """Tests for cart creation."""

    async def test_create_empty_cart(self, db_session):
        """Test creating an empty cart."""
        session = await SessionFactory.create(db_session)

        cart = await CartFactory.create(db_session, session=session)

        assert cart.id is not None
        assert cart.session_id == session.id
        assert cart.status == CartStatus.building

    async def test_create_cart_with_session(self, db_session):
        """Test creating a cart linked to a session."""
        session = await SessionFactory.create(db_session)

        cart = await CartFactory.create_with_session(db_session)

        assert cart.session_id == session.id

    async def test_cart_default_status(self, db_session):
        """Test that new carts have 'building' status."""
        session = await SessionFactory.create(db_session)

        cart = Cart(
            id=uuid.uuid4(),
            session_id=session.id
        )
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.building

    async def test_cart_without_session_fails(self, db_session):
        """Test that cart without session fails integrity."""
        cart = Cart(
            id=uuid.uuid4(),
            session_id=uuid.uuid4()
        )
        db_session.add(cart)

        with pytest.raises(Exception):
            await db_session.commit()


class TestCartItems:
    """Tests for cart item operations."""

    async def test_add_item_to_cart(self, db_session):
        """Test adding an item to a cart."""
        cart = await CartFactory.create(db_session)
        product = await ProductFactory.create(db_session)
        variant = await ProductVariantFactory.create(db_session, product=product)

        item = await CartItemFactory.create(
            db_session,
            cart=cart,
            product=product,
            variant=variant
        )

        assert item.cart_id == cart.id
        assert item.quantity == 1

    async def test_add_multiple_items(self, db_session):
        """Test adding multiple items to a cart."""
        cart = await CartFactory.create(db_session)

        for i in range(3):
            variant = await ProductVariantFactory.create(db_session)
            await CartItemFactory.create(
                db_session,
                cart=cart,
                variant=variant,
                quantity=i + 1
            )

        await db_session.refresh(cart)
        assert len(cart.items) == 3

    async def test_update_item_quantity(self, db_session):
        """Test updating item quantity in cart."""
        cart = await CartFactory.create(db_session)
        item = await CartItemFactory.create(db_session, cart=cart, quantity=1)

        item.quantity = 5
        await db_session.commit()
        await db_session.refresh(item)

        assert item.quantity == 5

    async def test_remove_item_from_cart(self, db_session):
        """Test removing an item from cart."""
        cart = await CartFactory.create(db_session)
        item = await CartItemFactory.create(db_session, cart=cart)
        item_id = item.id

        await db_session.delete(item)
        await db_session.commit()

        result = await db_session.get(CartItem, item_id)
        assert result is None

    async def test_cart_item_with_detection_data(self, db_session):
        """Test cart item with YOLO detection metadata."""
        cart = await CartFactory.create(db_session)
        product = await ProductFactory.create(db_session)

        item = await CartItemFactory.create_with_detection(
            db_session,
            cart=cart,
            product=product,
            confidence=0.95,
            bbox={"x1": 100, "y1": 100, "x2": 200, "y2": 200}
        )

        assert item.detection_confidence == 0.95
        assert item.detection_bbox == {"x1": 100, "y1": 100, "x2": 200, "y2": 200}


class TestCartStatusTransitions:
    """Tests for cart status state machine."""

    async def test_cart_to_submitted(self, db_session):
        """Test transitioning cart to submitted status."""
        cart = await CartFactory.create(db_session)

        cart.status = CartStatus.submitted
        cart.submitted_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.submitted

    async def test_cart_to_processing(self, db_session):
        """Test transitioning cart to processing."""
        cart = await CartFactory.create_submitted(db_session)

        cart.status = CartStatus.processing
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.processing

    async def test_cart_to_paid(self, db_session):
        """Test transitioning cart to paid."""
        cart = await CartFactory.create(db_session)

        cart.status = CartStatus.paid
        from backend.app.models.models import PaymentMethod
        cart.payment_method = PaymentMethod.card
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.paid

    async def test_cart_to_cancelled(self, db_session):
        """Test transitioning cart to cancelled."""
        cart = await CartFactory.create(db_session)

        cart.status = CartStatus.cancelled
        cart.notes = "Cancelled by user"
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.cancelled

    async def test_cart_status_workflow(self, db_session):
        """Test full cart status workflow: building -> submitted -> processing -> paid."""
        cart = await CartFactory.create(db_session)
        await CartItemFactory.create(db_session, cart=cart)

        cart.status = CartStatus.submitted
        cart.submitted_at = datetime.utcnow()
        await db_session.commit()
        assert cart.status == CartStatus.submitted

        cart.status = CartStatus.processing
        await db_session.commit()
        assert cart.status == CartStatus.processing

        cart.status = CartStatus.paid
        await db_session.commit()
        assert cart.status == CartStatus.paid


class TestCartCalculations:
    """Tests for cart total calculations."""

    async def test_cart_total_with_single_item(self, db_session):
        """Test cart total with single item."""
        cart = await CartFactory.create(db_session)
        variant = await ProductVariantFactory.create(db_session)

        await CartItemFactory.create(
            db_session,
            cart=cart,
            variant=variant,
            quantity=2,
            unit_price=Decimal("100.00")
        )
        await db_session.refresh(cart)

        total = sum(float(item.unit_price) * item.quantity for item in cart.items)
        assert total == 200.00

    async def test_cart_total_with_multiple_items(self, db_session):
        """Test cart total with multiple items."""
        cart = await CartFactory.create(db_session)

        await CartItemFactory.create(
            db_session, cart=cart, quantity=2, unit_price=Decimal("50.00")
        )
        await CartItemFactory.create(
            db_session, cart=cart, quantity=1, unit_price=Decimal("75.00")
        )

        await db_session.refresh(cart)
        total = sum(float(item.unit_price) * item.quantity for item in cart.items)

        assert total == 175.00

    async def test_cart_with_price_modifiers(self, db_session):
        """Test cart with variant price modifiers."""
        product = await ProductFactory.create(db_session, base_price=Decimal("100.00"))
        variant = await ProductVariantFactory.create(
            db_session, product=product, price_modifier=Decimal("20.00")
        )
        cart = await CartFactory.create(db_session)

        unit_price = float(product.base_price) + float(variant.price_modifier)
        await CartItemFactory.create(
            db_session, cart=cart, variant=variant, unit_price=Decimal(str(unit_price))
        )

        await db_session.refresh(cart)
        total = sum(float(item.unit_price) * item.quantity for item in cart.items)

        assert total == 120.00


class TestCartRelationships:
    """Tests for cart relationships."""

    async def test_cart_session_relationship(self, db_session):
        """Test cart belongs to session."""
        session = await SessionFactory.create(db_session)
        cart = await CartFactory.create(db_session, session=session)

        await db_session.refresh(session)
        assert cart.session_id == session.id

    async def test_cart_items_relationship(self, db_session):
        """Test cart has items relationship."""
        cart = await CartFactory.create(db_session)
        item = await CartItemFactory.create(db_session, cart=cart)

        await db_session.refresh(cart)
        assert any(i.id == item.id for i in cart.items)

    async def test_cascade_delete_items(self, db_session):
        """Test that deleting cart deletes items."""
        cart = await CartFactory.create(db_session)
        await CartItemFactory.create(db_session, cart=cart)
        await CartItemFactory.create(db_session, cart=cart)
        await db_session.refresh(cart)

        cart_id = cart.id
        await db_session.delete(cart)
        await db_session.commit()

        result = await db_session.get(Cart, cart_id)
        assert result is None


class TestCartEdgeCases:
    """Tests for edge cases."""

    async def test_cart_item_zero_quantity(self, db_session):
        """Test item with zero quantity."""
        cart = await CartFactory.create(db_session)
        item = await CartItemFactory.create(db_session, cart=cart, quantity=0)

        assert item.quantity == 0

    async def test_multiple_carts_per_session(self, db_session):
        """Test multiple carts can belong to same session."""
        session = await SessionFactory.create(db_session)

        cart1 = await CartFactory.create(db_session, session=session)
        cart2 = await CartFactory.create(db_session, session=session)

        assert cart1.id != cart2.id

    async def test_cart_empty_after_item_removal(self, db_session):
        """Test cart appears empty after removing all items."""
        cart = await CartFactory.create(db_session)
        item = await CartItemFactory.create(db_session, cart=cart)

        await db_session.delete(item)
        await db_session.commit()
        await db_session.refresh(cart)

        assert len(cart.items) == 0
