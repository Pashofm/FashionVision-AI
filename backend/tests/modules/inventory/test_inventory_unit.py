"""
Inventory Unit Tests

Tests for inventory management logic including:
- Inventory creation and queries
- Stock adjustments (positive/negative)
- Restock operations
- Sale operations
- Low stock threshold detection
"""
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from backend.app.models.models import (
    Inventory, InventoryMovement, MovementType, Product, ProductVariant
)
from backend.app.services.session_manager import SessionManager
from tests.factories import (
    InventoryFactory, InventoryMovementFactory,
    ProductFactory, ProductVariantFactory, UserFactory
)


pytestmark = pytest.mark.asyncio


class TestInventoryCreation:
    """Tests for inventory record creation."""

    async def test_create_inventory(self, db_session):
        """Test creating inventory with default values."""
        inventory = await InventoryFactory.create(db_session)

        assert inventory.id is not None
        assert inventory.quantity_available == 100
        assert inventory.quantity_reserved == 0
        assert inventory.low_stock_threshold == 10

    async def test_create_inventory_custom_values(self, db_session):
        """Test creating inventory with custom values."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=50,
            quantity_reserved=5,
            low_stock_threshold=15
        )

        assert inventory.quantity_available == 50
        assert inventory.quantity_reserved == 5
        assert inventory.low_stock_threshold == 15

    async def test_create_inventory_with_variant(self, db_session):
        """Test creating inventory linked to a variant."""
        variant, product = await ProductVariantFactory.create_with_product(db_session)
        inventory = await InventoryFactory.create(db_session, variant=variant)

        assert inventory.product_variant_id == variant.id

    async def test_inventory_unique_per_variant(self, db_session):
        """Test that each variant can only have one inventory record."""
        variant = await ProductVariantFactory.create(db_session)

        inv1 = await InventoryFactory.create(db_session, variant=variant)

        with pytest.raises(Exception):
            await InventoryFactory.create(db_session, variant=variant)


class TestInventoryQueries:
    """Tests for inventory querying."""

    async def test_get_inventory_by_variant_id(self, db_session):
        """Test querying inventory by variant ID."""
        variant = await ProductVariantFactory.create(db_session)
        inventory = await InventoryFactory.create(db_session, variant=variant)

        result = await db_session.get(Inventory, inventory.id)

        assert result is not None
        assert result.product_variant_id == variant.id

    async def test_get_low_stock_inventory(self, db_session):
        """Test querying products with low stock."""
        await InventoryFactory.create(db_session, quantity_available=5, low_stock_threshold=10)
        await InventoryFactory.create(db_session, quantity_available=20, low_stock_threshold=10)
        await InventoryFactory.create(db_session, quantity_available=3, low_stock_threshold=5)

        from sqlalchemy import select, and_

        result = await db_session.execute(
            select(Inventory).where(
                and_(
                    Inventory.quantity_available <= Inventory.low_stock_threshold,
                    Inventory.quantity_available > 0
                )
            )
        )
        low_stock = result.scalars().all()

        assert len(low_stock) == 2

    async def test_get_out_of_stock_inventory(self, db_session):
        """Test querying out of stock inventory."""
        await InventoryFactory.create(db_session, quantity_available=0, low_stock_threshold=10)
        await InventoryFactory.create(db_session, quantity_available=50, low_stock_threshold=10)

        from sqlalchemy import select

        result = await db_session.execute(
            select(Inventory).where(Inventory.quantity_available == 0)
        )
        out_of_stock = result.scalars().all()

        assert len(out_of_stock) == 1


class TestInventoryAdjustments:
    """Tests for inventory adjustments."""

    async def test_adjust_inventory_positive(self, db_session):
        """Test positive inventory adjustment increases quantity."""
        admin = await UserFactory.create_admin(db_session)
        inventory = await InventoryFactory.create(db_session, quantity_available=100)

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=inventory.product_variant_id,
            movement_type=MovementType.adjustment,
            quantity_change=50,
            quantity_before=100,
            quantity_after=150,
            notes="Correction: Found extra stock",
            created_by=admin.id
        )
        inventory.quantity_available = 150
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_available == 150

    async def test_adjust_inventory_negative(self, db_session):
        """Test negative inventory adjustment decreases quantity."""
        admin = await UserFactory.create_admin(db_session)
        inventory = await InventoryFactory.create(db_session, quantity_available=100)

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=inventory.product_variant_id,
            movement_type=MovementType.adjustment,
            quantity_change=-30,
            quantity_before=100,
            quantity_after=70,
            notes="Damaged goods",
            created_by=admin.id
        )
        inventory.quantity_available = 70
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_available == 70

    async def test_adjust_inventory_records_movement(self, db_session):
        """Test that inventory adjustment creates a movement record."""
        admin = await UserFactory.create_admin(db_session)
        inventory = await InventoryFactory.create(db_session)

        movement = await InventoryMovementFactory.create(
            db_session,
            variant_id=inventory.product_variant_id,
            movement_type=MovementType.adjustment,
            quantity_change=10,
            quantity_before=100,
            quantity_after=110,
            created_by=admin.id
        )

        from sqlalchemy import select

        result = await db_session.execute(
            select(InventoryMovement).where(
                InventoryMovement.product_variant_id == inventory.product_variant_id,
                InventoryMovement.movement_type == MovementType.adjustment
            )
        )
        movements = result.scalars().all()

        assert len(movements) >= 1
        assert movements[-1].quantity_change == 10


class TestRestockOperations:
    """Tests for restock operations."""

    async def test_restock_increases_quantity(self, db_session):
        """Test that restocking increases inventory quantity."""
        admin = await UserFactory.create_admin(db_session)
        inventory = await InventoryFactory.create(db_session, quantity_available=100)

        restock_qty = 50
        new_qty = 100 + restock_qty

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=inventory.product_variant_id,
            movement_type=MovementType.restock,
            quantity_change=restock_qty,
            quantity_before=100,
            quantity_after=new_qty,
            notes="Supplier delivery",
            created_by=admin.id
        )
        inventory.quantity_available = new_qty
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_available == 150

    async def test_restock_creates_movement_record(self, db_session):
        """Test that restocking creates a movement record with type 'restock'."""
        admin = await UserFactory.create_admin(db_session)
        variant = await ProductVariantFactory.create(db_session)

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=variant.id,
            movement_type=MovementType.restock,
            quantity_change=100,
            quantity_before=0,
            quantity_after=100,
            notes="Initial stock",
            created_by=admin.id
        )
        db_session.add(movement)
        await db_session.commit()

        from sqlalchemy import select

        result = await db_session.execute(
            select(InventoryMovement).where(
                InventoryMovement.product_variant_id == variant.id,
                InventoryMovement.movement_type == MovementType.restock
            )
        )
        restock_movements = result.scalars().all()

        assert len(restock_movements) >= 1
        assert restock_movements[0].notes == "Initial stock"

    async def test_multiple_restock_operations(self, db_session):
        """Test multiple restock operations accumulate correctly."""
        variant = await ProductVariantFactory.create(db_session)

        for i in range(3):
            movement = InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=variant.id,
                movement_type=MovementType.restock,
                quantity_change=10,
                quantity_before=i * 10,
                quantity_after=(i + 1) * 10,
            )
            db_session.add(movement)

        await db_session.commit()

        from sqlalchemy import select, func

        result = await db_session.execute(
            select(func.sum(InventoryMovement.quantity_change)).where(
                InventoryMovement.product_variant_id == variant.id,
                InventoryMovement.movement_type == MovementType.restock
            )
        )
        total_restock = result.scalar()

        assert total_restock == 30


class TestSaleOperations:
    """Tests for sale (decrement) operations."""

    async def test_sale_decreases_inventory(self, db_session):
        """Test that a sale decreases inventory quantity."""
        inventory = await InventoryFactory.create(db_session, quantity_available=100)

        sale_qty = 3
        new_qty = 100 - sale_qty

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=inventory.product_variant_id,
            movement_type=MovementType.sale,
            quantity_change=-sale_qty,
            quantity_before=100,
            quantity_after=new_qty,
        )
        inventory.quantity_available = new_qty
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_available == 97

    async def test_sale_records_movement(self, db_session):
        """Test that a sale creates a movement record."""
        variant = await ProductVariantFactory.create(db_session)

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=variant.id,
            movement_type=MovementType.sale,
            quantity_change=-2,
            quantity_before=100,
            quantity_after=98,
        )
        db_session.add(movement)
        await db_session.commit()

        from sqlalchemy import select

        result = await db_session.execute(
            select(InventoryMovement).where(
                InventoryMovement.product_variant_id == variant.id,
                InventoryMovement.movement_type == MovementType.sale
            )
        )
        sales = result.scalars().all()

        assert len(sales) >= 1
        assert sales[-1].quantity_change == -2

    async def test_multiple_sales_calculation(self, db_session):
        """Test that multiple sales are tracked correctly."""
        variant = await ProductVariantFactory.create(db_session)
        initial_qty = 100

        for i in range(5):
            movement = InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=variant.id,
                movement_type=MovementType.sale,
                quantity_change=-2,
                quantity_before=initial_qty - (i * 2),
                quantity_after=initial_qty - ((i + 1) * 2),
            )
            db_session.add(movement)

        await db_session.commit()

        from sqlalchemy import select, func

        result = await db_session.execute(
            select(func.sum(InventoryMovement.quantity_change)).where(
                InventoryMovement.product_variant_id == variant.id,
                InventoryMovement.movement_type == MovementType.sale
            )
        )
        total_sold = result.scalar()

        assert total_sold == -10


class TestReservedInventory:
    """Tests for reserved inventory functionality."""

    async def test_reserve_inventory(self, db_session):
        """Test reserving inventory for an order."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=100,
            quantity_reserved=0
        )

        inventory.quantity_reserved = 10
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_reserved == 10

    async def test_available_after_reservation(self, db_session):
        """Test that available quantity excludes reserved."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=100,
            quantity_reserved=10
        )

        actual_available = inventory.quantity_available - inventory.quantity_reserved

        assert actual_available == 90

    async def test_release_reservation(self, db_session):
        """Test releasing reserved inventory."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=100,
            quantity_reserved=10
        )

        inventory.quantity_reserved = 5
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.quantity_reserved == 5


class TestLowStockThreshold:
    """Tests for low stock threshold functionality."""

    async def test_low_stock_threshold_detection(self, db_session):
        """Test that threshold is correctly stored."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=5,
            low_stock_threshold=10
        )

        assert inventory.low_stock_threshold == 10
        assert inventory.quantity_available <= inventory.low_stock_threshold

    async def test_multiple_inventory_threshold_levels(self, db_session):
        """Test different threshold levels."""
        thresholds = [5, 10, 20, 50]

        for threshold in thresholds:
            await InventoryFactory.create(
                db_session,
                quantity_available=threshold - 1,
                low_stock_threshold=threshold
            )

        from sqlalchemy import select

        result = await db_session.execute(
            select(Inventory).where(
                Inventory.quantity_available <= Inventory.low_stock_threshold
            )
        )
        low_stock = result.scalars().all()

        assert len(low_stock) == 4

    async def test_threshold_update(self, db_session):
        """Test updating low stock threshold."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=15,
            low_stock_threshold=10
        )

        inventory.low_stock_threshold = 20
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.low_stock_threshold == 20
        assert inventory.quantity_available <= inventory.low_stock_threshold


class TestInventoryMovementHistory:
    """Tests for inventory movement history tracking."""

    async def test_get_movements_by_variant(self, db_session):
        """Test retrieving all movements for a variant."""
        variant = await ProductVariantFactory.create(db_session)

        movements = [
            InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=variant.id,
                movement_type=MovementType.restock,
                quantity_change=100,
                quantity_before=0,
                quantity_after=100,
            ),
            InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=variant.id,
                movement_type=MovementType.sale,
                quantity_change=-5,
                quantity_before=100,
                quantity_after=95,
            ),
            InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=variant.id,
                movement_type=MovementType.adjustment,
                quantity_change=10,
                quantity_before=95,
                quantity_after=105,
            ),
        ]

        for m in movements:
            db_session.add(m)
        await db_session.commit()

        from sqlalchemy import select

        result = await db_session.execute(
            select(InventoryMovement).where(
                InventoryMovement.product_variant_id == variant.id
            ).order_by(InventoryMovement.created_at)
        )
        all_movements = result.scalars().all()

        assert len(all_movements) == 3

    async def test_movement_timestamps(self, db_session):
        """Test that movements have timestamps."""
        variant = await ProductVariantFactory.create(db_session)

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=variant.id,
            movement_type=MovementType.restock,
            quantity_change=50,
            quantity_before=0,
            quantity_after=50,
        )
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(movement)

        assert movement.created_at is not None

    async def test_movement_notes(self, db_session):
        """Test that movements can store notes."""
        movement = await InventoryMovementFactory.create(
            db_session,
            notes="Test movement note"
        )

        assert movement.notes == "Test movement note"


class TestInventoryEdgeCases:
    """Tests for edge cases in inventory management."""

    async def test_zero_inventory_allowed(self, db_session):
        """Test that zero inventory is allowed."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=0,
            low_stock_threshold=10
        )

        assert inventory.quantity_available == 0

    async def test_large_inventory_values(self, db_session):
        """Test handling large inventory values."""
        inventory = await InventoryFactory.create(
            db_session,
            quantity_available=1000000
        )

        assert inventory.quantity_available == 1000000

    async def test_inventory_variant_not_found(self, db_session):
        """Test querying non-existent inventory."""
        from sqlalchemy import select

        result = await db_session.execute(
            select(Inventory).where(
                Inventory.product_variant_id == uuid.uuid4()
            )
        )
        inventory = result.scalar_one_or_none()

        assert inventory is None

    async def test_movement_for_nonexistent_variant(self, db_session):
        """Test creating movement for non-existent variant."""
        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=uuid.uuid4(),
            movement_type=MovementType.restock,
            quantity_change=10,
            quantity_before=0,
            quantity_after=10,
        )
        db_session.add(movement)

        with pytest.raises(Exception):
            await db_session.commit()
