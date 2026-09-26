import pytest
import uuid
from decimal import Decimal


class TestCartCreation:
    @pytest.mark.asyncio
    async def test_create_cart(self, db_session, test_session):
        from backend.app.models.models import Cart, CartStatus

        cart = Cart(
            id=uuid.uuid4(),
            session_id=test_session.id,
            status=CartStatus.building
        )
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.id is not None
        assert cart.session_id == test_session.id
        assert cart.status == CartStatus.building
        assert cart.created_at is not None

    @pytest.mark.asyncio
    async def test_create_cart_without_session_fails(self, db_session):
        from backend.app.models.models import Cart, CartStatus
        from sqlalchemy import exc

        cart = Cart(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            status=CartStatus.building
        )
        db_session.add(cart)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_cart_default_values(self, db_session, test_session):
        from backend.app.models.models import Cart, CartStatus

        cart = Cart(
            id=uuid.uuid4(),
            session_id=test_session.id
        )
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        assert cart.status == CartStatus.building
        assert cart.payment_method is None
        assert cart.submitted_at is None
        assert cart.notes is None


class TestCartItems:
    @pytest.mark.asyncio
    async def test_add_item_to_cart(self, db_session, test_cart, test_product, test_variant):
        from backend.app.models.models import CartItem

        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=1,
            unit_price=Decimal("109.99")
        )
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)

        assert cart_item.id is not None
        assert cart_item.cart_id == test_cart.id
        assert cart_item.product_id == test_product.id
        assert cart_item.quantity == 1
        assert float(cart_item.unit_price) == 109.99

    @pytest.mark.asyncio
    async def test_add_multiple_items_to_cart(self, db_session, test_cart, test_product, test_variant):
        from backend.app.models.models import CartItem, ProductVariant

        variant2 = ProductVariant(
            id=uuid.uuid4(),
            product_id=test_product.id,
            size="L",
            color="Blue",
            sku_variant="TEST-001-L-BLUE"
        )
        db_session.add(variant2)
        await db_session.commit()

        item1 = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=2,
            unit_price=Decimal("109.99")
        )
        item2 = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=variant2.id,
            quantity=1,
            unit_price=Decimal("114.99")
        )
        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        from backend.app.models.models import Cart
        await db_session.refresh(test_cart)
        items = test_cart.items

        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_cart_item_with_detection_data(self, db_session, test_cart, test_product):
        from backend.app.models.models import CartItem

        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            quantity=1,
            unit_price=Decimal("99.99"),
            detection_confidence=0.95,
            detection_image_path="/tmp/detection.jpg",
            detection_bbox={"x1": 100, "y1": 100, "x2": 200, "y2": 200},
            confirmed=False
        )
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)

        assert cart_item.detection_confidence == 0.95
        assert cart_item.detection_bbox == {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
        assert cart_item.confirmed is False

    @pytest.mark.asyncio
    async def test_update_cart_item_quantity(self, db_session, test_cart_item):
        test_cart_item.quantity = 5
        await db_session.commit()
        await db_session.refresh(test_cart_item)

        assert test_cart_item.quantity == 5

    @pytest.mark.asyncio
    async def test_remove_cart_item(self, db_session, test_cart_item):
        item_id = test_cart_item.id
        await db_session.delete(test_cart_item)
        await db_session.commit()

        from backend.app.models.models import CartItem
        result = await db_session.get(CartItem, item_id)
        assert result is None


class TestCartStatusTransitions:
    @pytest.mark.asyncio
    async def test_cart_to_submitted(self, db_session, test_cart):
        from datetime import datetime
        from backend.app.models.models import CartStatus

        test_cart.status = CartStatus.submitted
        test_cart.submitted_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(test_cart)

        assert test_cart.status == CartStatus.submitted
        assert test_cart.submitted_at is not None

    @pytest.mark.asyncio
    async def test_cart_to_processing(self, db_session, test_cart):
        from backend.app.models.models import CartStatus

        test_cart.status = CartStatus.processing
        await db_session.commit()
        await db_session.refresh(test_cart)

        assert test_cart.status == CartStatus.processing

    @pytest.mark.asyncio
    async def test_cart_to_paid(self, db_session, test_cart):
        from backend.app.models.models import CartStatus, PaymentMethod

        test_cart.status = CartStatus.paid
        test_cart.payment_method = PaymentMethod.card
        await db_session.commit()
        await db_session.refresh(test_cart)

        assert test_cart.status == CartStatus.paid
        assert test_cart.payment_method == PaymentMethod.card

    @pytest.mark.asyncio
    async def test_cart_to_cancelled(self, db_session, test_cart):
        from backend.app.models.models import CartStatus

        test_cart.status = CartStatus.cancelled
        test_cart.notes = "Cancelled by user"
        await db_session.commit()
        await db_session.refresh(test_cart)

        assert test_cart.status == CartStatus.cancelled
        assert test_cart.notes == "Cancelled by user"

    @pytest.mark.asyncio
    async def test_cart_status_workflow_building_to_paid(self, db_session, test_cart, test_cart_item):
        from backend.app.models.models import CartStatus, PaymentMethod

        test_cart.status = CartStatus.submitted
        await db_session.commit()
        await db_session.refresh(test_cart)
        assert test_cart.status == CartStatus.submitted

        test_cart.status = CartStatus.processing
        await db_session.commit()
        await db_session.refresh(test_cart)
        assert test_cart.status == CartStatus.processing

        test_cart.status = CartStatus.paid
        test_cart.payment_method = PaymentMethod.cash
        await db_session.commit()
        await db_session.refresh(test_cart)
        assert test_cart.status == CartStatus.paid
        assert test_cart.payment_method == PaymentMethod.cash


class TestCartCalculations:
    @pytest.mark.asyncio
    async def test_cart_total_calculation(self, db_session, test_cart, test_product, test_variant):
        from backend.app.models.models import CartItem

        item1 = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=2,
            unit_price=Decimal("100.00")
        )
        db_session.add(item1)

        variant2 = ProductVariant(
            id=uuid.uuid4(),
            product_id=test_product.id,
            size="S",
            color="Black",
            sku_variant="TEST-001-S-BLACK"
        )
        db_session.add(variant2)
        await db_session.flush()

        item2 = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=variant2.id,
            quantity=1,
            unit_price=Decimal("150.00")
        )
        db_session.add(item2)
        await db_session.commit()

        total = sum(float(item.unit_price) * item.quantity for item in test_cart.items)
        assert total == 350.00

    @pytest.mark.asyncio
    async def test_cart_with_price_modifiers(self, db_session, test_cart, test_product, test_variant):
        from backend.app.models.models import CartItem

        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=1,
            unit_price=Decimal("109.99")
        )
        db_session.add(cart_item)
        await db_session.commit()

        expected_price = float(test_product.base_price) + float(test_variant.price_modifier)
        assert float(cart_item.unit_price) == expected_price


class TestCartRelationships:
    @pytest.mark.asyncio
    async def test_cart_session_relationship(self, db_session, test_cart, test_session):
        await db_session.refresh(test_cart)

        assert test_cart.session is not None
        assert test_cart.session.id == test_session.id
        assert test_cart.session.client_user_id == test_session.client_user_id

    @pytest.mark.asyncio
    async def test_cart_items_relationship(self, db_session, test_cart, test_cart_item):
        await db_session.refresh(test_cart)

        assert len(test_cart.items) >= 1
        assert any(item.id == test_cart_item.id for item in test_cart.items)

    @pytest.mark.asyncio
    async def test_cart_cascade_delete_items(self, db_session, test_cart, test_product, test_variant):
        from backend.app.models.models import CartItem

        item1 = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=1,
            unit_price=Decimal("99.99")
        )
        item2 = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=1,
            unit_price=Decimal("99.99")
        )
        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        items_count = len(test_cart.items)

        await db_session.delete(test_cart)
        await db_session.commit()

        from backend.app.models.models import Cart
        cart_exists = await db_session.get(Cart, test_cart.id)
        assert cart_exists is None


class TestCartEdgeCases:
    @pytest.mark.asyncio
    async def test_cart_item_zero_quantity(self, db_session, test_cart, test_product, test_variant):
        from backend.app.models.models import CartItem

        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=0,
            unit_price=Decimal("99.99")
        )
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)

        assert cart_item.quantity == 0

    @pytest.mark.asyncio
    async def test_cart_item_negative_quantity_rejected(self, db_session, test_cart, test_product, test_variant):
        from backend.app.models.models import CartItem

        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            quantity=-1,
            unit_price=Decimal("99.99")
        )
        db_session.add(cart_item)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_multiple_carts_per_session(self, db_session, test_session):
        from backend.app.models.models import Cart, CartStatus

        cart1 = Cart(id=uuid.uuid4(), session_id=test_session.id, status=CartStatus.building)
        cart2 = Cart(id=uuid.uuid4(), session_id=test_session.id, status=CartStatus.building)
        db_session.add(cart1)
        db_session.add(cart2)
        await db_session.commit()

        assert cart1.id != cart2.id
