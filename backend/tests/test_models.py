import pytest
import uuid
from decimal import Decimal


class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        from backend.app.models.models import User, UserRole
        from backend.app.services.auth import hash_password

        user = User(
            id=uuid.uuid4(),
            name="Test User",
            email="unique_test@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.admin,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "unique_test@example.com"
        assert user.role == UserRole.admin
        assert user.is_active is True
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_user_unique_email(self, db_session):
        from backend.app.models.models import User, UserRole
        from backend.app.services.auth import hash_password

        user1 = User(
            id=uuid.uuid4(),
            name="User 1",
            email="duplicate@example.com",
            password_hash=hash_password("pass1"),
            role=UserRole.client
        )
        db_session.add(user1)
        await db_session.commit()

        user2 = User(
            id=uuid.uuid4(),
            name="User 2",
            email="duplicate@example.com",
            password_hash=hash_password("pass2"),
            role=UserRole.client
        )
        db_session.add(user2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_roles(self, db_session):
        from backend.app.models.models import User, UserRole

        roles = [UserRole.admin, UserRole.cashier, UserRole.client]
        for i, role in enumerate(roles):
            user = User(
                id=uuid.uuid4(),
                name=f"User {role.value}",
                email=f"user_{i}@{role.value}.com",
                password_hash="hash",
                role=role
            )
            db_session.add(user)
        await db_session.commit()

        for role in roles:
            result = await db_session.query(User).filter_by(role=role).first()
            assert result is not None

    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session):
        from backend.app.models.models import User

        user = User(
            id=uuid.uuid4(),
            name="Default User",
            email="default@test.com",
            password_hash="hash"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.role == UserRole.client
        assert user.is_active is True


class TestCategoryModel:
    @pytest.mark.asyncio
    async def test_create_category(self, db_session):
        from backend.app.models.models import Category

        category = Category(
            id=uuid.uuid4(),
            name="Electronics",
            description="Electronic devices",
            icon="electronic-icon",
            is_active=True
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        assert category.id is not None
        assert category.name == "Electronics"
        assert category.is_active is True

    @pytest.mark.asyncio
    async def test_category_unique_name(self, db_session):
        from backend.app.models.models import Category

        cat1 = Category(id=uuid.uuid4(), name="Unique Category")
        db_session.add(cat1)
        await db_session.commit()

        cat2 = Category(id=uuid.uuid4(), name="Unique Category")
        db_session.add(cat2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_category_products_relationship(self, db_session, test_category, test_product):
        await db_session.refresh(test_category)

        assert len(test_category.products) >= 1
        assert any(p.id == test_product.id for p in test_category.products)


class TestProductModel:
    @pytest.mark.asyncio
    async def test_create_product(self, db_session, test_category):
        from backend.app.models.models import Product

        product = Product(
            id=uuid.uuid4(),
            category_id=test_category.id,
            name="New Product",
            description="Product description",
            sku="NEW-001",
            base_price=Decimal("49.99"),
            is_active=True
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        assert product.id is not None
        assert product.name == "New Product"
        assert float(product.base_price) == 49.99

    @pytest.mark.asyncio
    async def test_product_unique_sku(self, db_session, test_category, test_product):
        from backend.app.models.models import Product

        product2 = Product(
            id=uuid.uuid4(),
            category_id=test_category.id,
            name="Another Product",
            sku=test_product.sku,
            base_price=Decimal("99.99")
        )
        db_session.add(product2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_product_with_yolo_class(self, db_session, test_category):
        from backend.app.models.models import Product

        product = Product(
            id=uuid.uuid4(),
            category_id=test_category.id,
            name="Detectable Product",
            sku="DETECT-001",
            base_price=Decimal("79.99"),
            yolo_class_id=1,
            yolo_class_name="gorra-roja-lacoste"
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        assert product.yolo_class_name == "gorra-roja-lacoste"

    @pytest.mark.asyncio
    async def test_product_images_jsonb(self, db_session, test_category):
        from backend.app.models.models import Product

        product = Product(
            id=uuid.uuid4(),
            category_id=test_category.id,
            name="Product with Images",
            sku="IMG-001",
            base_price=Decimal("99.99"),
            images=[
                {"url": "https://example.com/img1.jpg", "public_id": "abc123"},
                {"url": "https://example.com/img2.jpg", "public_id": "def456"}
            ]
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        assert len(product.images) == 2
        assert product.images[0]["url"] == "https://example.com/img1.jpg"

    @pytest.mark.asyncio
    async def test_product_variants_relationship(self, db_session, test_product, test_variant):
        await db_session.refresh(test_product)

        assert len(test_product.variants) >= 1
        assert any(v.id == test_variant.id for v in test_product.variants)


class TestProductVariantModel:
    @pytest.mark.asyncio
    async def test_create_variant(self, db_session, test_product):
        from backend.app.models.models import ProductVariant

        variant = ProductVariant(
            id=uuid.uuid4(),
            product_id=test_product.id,
            size="XL",
            color="Green",
            color_hex="#00FF00",
            sku_variant="TEST-001-XL-GREEN",
            price_modifier=Decimal("15.00")
        )
        db_session.add(variant)
        await db_session.commit()
        await db_session.refresh(variant)

        assert variant.id is not None
        assert variant.size == "XL"
        assert float(variant.price_modifier) == 15.00

    @pytest.mark.asyncio
    async def test_variant_unique_constraint(self, db_session, test_product, test_variant):
        from backend.app.models.models import ProductVariant

        variant2 = ProductVariant(
            id=uuid.uuid4(),
            product_id=test_product.id,
            size=test_variant.size,
            color=test_variant.color,
            sku_variant="UNIQUE-SKU"
        )
        db_session.add(variant2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_variant_inventory_relationship(self, db_session, test_variant, test_inventory):
        await db_session.refresh(test_variant)

        assert test_variant.inventory is not None
        assert test_variant.inventory.quantity_available == 100


class TestInventoryModel:
    @pytest.mark.asyncio
    async def test_create_inventory(self, db_session, test_variant, admin_user):
        from backend.app.models.models import Inventory

        inventory = Inventory(
            id=uuid.uuid4(),
            product_variant_id=test_variant.id,
            quantity_available=50,
            quantity_reserved=5,
            low_stock_threshold=10,
            updated_by=admin_user.id
        )
        db_session.add(inventory)
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_available == 50
        assert inventory.quantity_reserved == 5
        assert inventory.low_stock_threshold == 10

    @pytest.mark.asyncio
    async def test_inventory_unique_variant(self, db_session, test_inventory):
        from backend.app.models.models import Inventory

        inventory2 = Inventory(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            quantity_available=100
        )
        db_session.add(inventory2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_inventory_variant_relationship(self, db_session, test_inventory, test_variant):
        await db_session.refresh(test_inventory)

        assert test_inventory.variant is not None
        assert test_inventory.variant.sku_variant == test_variant.sku_variant


class TestInventoryMovementModel:
    @pytest.mark.asyncio
    async def test_create_inventory_movement(self, db_session, test_variant, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_variant.id,
            movement_type=MovementType.sale,
            quantity_change=-1,
            quantity_before=100,
            quantity_after=99,
            notes="Sale made",
            created_by=admin_user.id
        )
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(movement)

        assert movement.movement_type == MovementType.sale
        assert movement.quantity_change == -1

    @pytest.mark.asyncio
    async def test_inventory_movement_types(self, db_session, test_variant, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        movement_types = [
            MovementType.sale,
            MovementType.restock,
            MovementType.adjustment,
            MovementType.return_item
        ]

        for i, mov_type in enumerate(movement_types):
            movement = InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=test_variant.id,
                movement_type=mov_type,
                quantity_change=10 if mov_type == MovementType.restock else -5,
                quantity_before=100,
                quantity_after=105 if mov_type == MovementType.restock else 95,
                created_by=admin_user.id
            )
            db_session.add(movement)
        await db_session.commit()

        count = await db_session.query(InventoryMovement).filter_by(product_variant_id=test_variant.id).count()
        assert count >= len(movement_types)


class TestOrderModel:
    @pytest.mark.asyncio
    async def test_create_order(self, db_session, test_cart, cashier_user):
        from backend.app.models.models import Order, OrderStatus, PaymentMethod

        order = Order(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            order_number="ORD-20240115-001",
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

        assert order.order_number == "ORD-20240115-001"
        assert float(order.total_amount) == 255.18

    @pytest.mark.asyncio
    async def test_order_unique_cart(self, db_session, test_cart, cashier_user):
        from backend.app.models.models import Order

        order1 = Order(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            order_number="ORD-001",
            cashier_id=cashier_user.id,
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            payment_method=PaymentMethod.cash
        )
        db_session.add(order1)
        await db_session.commit()

        order2 = Order(
            id=uuid.uuid4(),
            cart_id=test_cart.id,
            order_number="ORD-002",
            cashier_id=cashier_user.id,
            subtotal=Decimal("200.00"),
            total_amount=Decimal("200.00"),
            payment_method=PaymentMethod.card
        )
        db_session.add(order2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_order_items_relationship(self, db_session, test_order, test_product, test_variant):
        from backend.app.models.models import OrderItem

        item = OrderItem(
            id=uuid.uuid4(),
            order_id=test_order.id,
            product_id=test_product.id,
            product_variant_id=test_variant.id,
            product_name=test_product.name,
            variant_description=f"{test_variant.size} / {test_variant.color}",
            quantity=2,
            unit_price=Decimal("109.99"),
            discount_applied=Decimal("0.00"),
            subtotal=Decimal("219.98")
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(test_order)

        assert len(test_order.items) >= 1


class TestReceiptModel:
    @pytest.mark.asyncio
    async def test_create_receipt(self, db_session, test_order):
        from backend.app.models.models import Receipt

        receipt = Receipt(
            id=uuid.uuid4(),
            order_id=test_order.id,
            receipt_number="RCP-20240115-001",
            receipt_data={
                "order_number": test_order.order_number,
                "total": float(test_order.total_amount),
                "items": []
            }
        )
        db_session.add(receipt)
        await db_session.commit()
        await db_session.refresh(receipt)

        assert receipt.receipt_number == "RCP-20240115-001"
        assert receipt.order_id == test_order.id

    @pytest.mark.asyncio
    async def test_receipt_unique_order(self, db_session, test_order):
        from backend.app.models.models import Receipt

        receipt1 = Receipt(
            id=uuid.uuid4(),
            order_id=test_order.id,
            receipt_number="RCP-001",
            receipt_data={}
        )
        db_session.add(receipt1)
        await db_session.commit()

        receipt2 = Receipt(
            id=uuid.uuid4(),
            order_id=test_order.id,
            receipt_number="RCP-002",
            receipt_data={}
        )
        db_session.add(receipt2)

        with pytest.raises(Exception):
            await db_session.commit()


class TestDailySalesSummaryModel:
    @pytest.mark.asyncio
    async def test_create_daily_summary(self, db_session):
        from backend.app.models.models import DailySalesSummary
        from datetime import date

        summary = DailySalesSummary(
            id=uuid.uuid4(),
            summary_date=date.today(),
            total_orders=50,
            total_revenue=Decimal("5000.00"),
            total_items_sold=120,
            payment_method_breakdown={"card": 3000.00, "cash": 2000.00},
            top_products=[
                {"product_id": "uuid1", "name": "Product A", "quantity": 30}
            ]
        )
        db_session.add(summary)
        await db_session.commit()
        await db_session.refresh(summary)

        assert summary.total_orders == 50
        assert summary.payment_method_breakdown["card"] == 3000.00

    @pytest.mark.asyncio
    async def test_daily_summary_unique_date(self, db_session):
        from backend.app.models.models import DailySalesSummary
        from datetime import date

        today = date.today()
        summary1 = DailySalesSummary(
            id=uuid.uuid4(),
            summary_date=today,
            total_orders=10
        )
        db_session.add(summary1)
        await db_session.commit()

        summary2 = DailySalesSummary(
            id=uuid.uuid4(),
            summary_date=today,
            total_orders=20
        )
        db_session.add(summary2)

        with pytest.raises(Exception):
            await db_session.commit()
