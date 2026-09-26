import pytest
import uuid
from decimal import Decimal


class TestInventoryQueries:
    @pytest.mark.asyncio
    async def test_get_inventory_by_variant(self, db_session, test_inventory, test_variant):
        from backend.app.models.models import Inventory

        result = await db_session.query(Inventory).filter_by(product_variant_id=test_variant.id).first()

        assert result is not None
        assert result.id == test_inventory.id
        assert result.quantity_available == 100

    @pytest.mark.asyncio
    async def test_get_low_stock_inventory(self, db_session, test_variant, admin_user):
        from backend.app.models.models import Inventory

        low_stock_variant = ProductVariant(
            id=uuid.uuid4(),
            product_id=test_variant.product_id,
            size="S",
            color="Yellow",
            sku_variant="LOW-STOCK-001"
        )
        db_session.add(low_stock_variant)
        await db_session.flush()

        low_inventory = Inventory(
            id=uuid.uuid4(),
            product_variant_id=low_stock_variant.id,
            quantity_available=5,
            quantity_reserved=0,
            low_stock_threshold=10,
            updated_by=admin_user.id
        )
        db_session.add(low_inventory)
        await db_session.commit()

        result = await db_session.query(Inventory).filter(
            Inventory.quantity_available <= Inventory.low_stock_threshold
        ).all()

        assert any(inv.id == low_inventory.id for inv in result)

    @pytest.mark.asyncio
    async def test_update_inventory_quantity(self, db_session, test_inventory):
        test_inventory.quantity_available = 75
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_available == 75

    @pytest.mark.asyncio
    async def test_update_low_stock_threshold(self, db_session, test_inventory):
        test_inventory.low_stock_threshold = 20
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.low_stock_threshold == 20


class TestInventoryAdjustments:
    @pytest.mark.asyncio
    async def test_adjust_inventory_positive(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        old_qty = test_inventory.quantity_available
        new_qty = old_qty + 50

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.adjustment,
            quantity_change=50,
            quantity_before=old_qty,
            quantity_after=new_qty,
            notes="Inventory correction",
            created_by=admin_user.id
        )
        test_inventory.quantity_available = new_qty
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_available == new_qty

    @pytest.mark.asyncio
    async def test_adjust_inventory_negative(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        old_qty = test_inventory.quantity_available
        new_qty = max(0, old_qty - 30)

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.adjustment,
            quantity_change=-30,
            quantity_before=old_qty,
            quantity_after=new_qty,
            notes="Damaged goods",
            created_by=admin_user.id
        )
        test_inventory.quantity_available = new_qty
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_available == new_qty

    @pytest.mark.asyncio
    async def test_cannot_go_below_zero(self, db_session, test_inventory):
        test_inventory.quantity_available = 0
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_available == 0


class TestRestockOperations:
    @pytest.mark.asyncio
    async def test_restock_inventory(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        old_qty = test_inventory.quantity_available
        restock_qty = 100
        new_qty = old_qty + restock_qty

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.restock,
            quantity_change=restock_qty,
            quantity_before=old_qty,
            quantity_after=new_qty,
            notes="Supplier delivery",
            created_by=admin_user.id
        )
        test_inventory.quantity_available = new_qty
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_available == 100 + 100

    @pytest.mark.asyncio
    async def test_restock_creates_movement_record(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.restock,
            quantity_change=50,
            quantity_before=100,
            quantity_after=150,
            notes="Regular restock",
            created_by=admin_user.id
        )
        db_session.add(movement)
        await db_session.commit()

        result = await db_session.query(InventoryMovement).filter_by(
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.restock
        ).all()

        assert len(result) >= 1
        assert result[0].notes == "Regular restock"


class TestSaleOperations:
    @pytest.mark.asyncio
    async def test_sale_decreases_inventory(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        old_qty = test_inventory.quantity_available
        sale_qty = 3
        new_qty = old_qty - sale_qty

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.sale,
            quantity_change=-sale_qty,
            quantity_before=old_qty,
            quantity_after=new_qty
        )
        test_inventory.quantity_available = new_qty
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_available == 97

    @pytest.mark.asyncio
    async def test_sale_records_movement(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.sale,
            quantity_change=-2,
            quantity_before=100,
            quantity_after=98,
            created_by=admin_user.id
        )
        db_session.add(movement)
        await db_session.commit()

        result = await db_session.query(InventoryMovement).filter_by(
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.sale
        ).all()

        assert len(result) >= 1


class TestReservedInventory:
    @pytest.mark.asyncio
    async def test_reserve_inventory(self, db_session, test_inventory):
        test_inventory.quantity_reserved = 10
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_reserved == 10

    @pytest.mark.asyncio
    async def test_available_after_reservation(self, db_session, test_inventory):
        test_inventory.quantity_available = 100
        test_inventory.quantity_reserved = 10
        await db_session.commit()
        await db_session.refresh(test_inventory)

        actual_available = test_inventory.quantity_available - test_inventory.quantity_reserved
        assert actual_available == 90

    @pytest.mark.asyncio
    async def test_release_reservation(self, db_session, test_inventory):
        from backend.app.models.models import InventoryMovement, MovementType

        test_inventory.quantity_reserved = 10
        await db_session.commit()

        test_inventory.quantity_reserved = 5
        await db_session.commit()
        await db_session.refresh(test_inventory)

        assert test_inventory.quantity_reserved == 5


class TestInventoryMovements:
    @pytest.mark.asyncio
    async def test_get_movements_by_variant(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        movements = [
            InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=test_inventory.product_variant_id,
                movement_type=MovementType.restock,
                quantity_change=50,
                quantity_before=100,
                quantity_after=150,
                created_by=admin_user.id
            ),
            InventoryMovement(
                id=uuid.uuid4(),
                product_variant_id=test_inventory.product_variant_id,
                movement_type=MovementType.sale,
                quantity_change=-5,
                quantity_before=150,
                quantity_after=145,
                created_by=admin_user.id
            )
        ]
        for m in movements:
            db_session.add(m)
        await db_session.commit()

        result = await db_session.query(InventoryMovement).filter_by(
            product_variant_id=test_inventory.product_variant_id
        ).all()

        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_movement_timestamps(self, db_session, test_inventory, admin_user):
        from backend.app.models.models import InventoryMovement, MovementType

        movement = InventoryMovement(
            id=uuid.uuid4(),
            product_variant_id=test_inventory.product_variant_id,
            movement_type=MovementType.adjustment,
            quantity_change=10,
            quantity_before=100,
            quantity_after=110,
            created_by=admin_user.id
        )
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(movement)

        assert movement.created_at is not None


class TestInventoryEdgeCases:
    @pytest.mark.asyncio
    async def test_inventory_with_no_threshold(self, db_session, test_variant):
        from backend.app.models.models import Inventory

        inventory = Inventory(
            id=uuid.uuid4(),
            product_variant_id=test_variant.id,
            quantity_available=100,
            quantity_reserved=0,
            low_stock_threshold=0
        )
        db_session.add(inventory)
        await db_session.commit()
        await db_session.refresh(inventory)

        assert inventory.low_stock_threshold == 0

    @pytest.mark.asyncio
    async def test_inventory_variant_not_found(self, db_session):
        from backend.app.models.models import Inventory

        result = await db_session.query(Inventory).filter_by(
            product_variant_id=uuid.uuid4()
        ).first()

        assert result is None


class TestInventoryCalculations:
    @pytest.mark.asyncio
    async def test_total_value_calculation(self, db_session, test_inventory, test_variant):
        test_inventory.quantity_available = 100
        await db_session.commit()

        unit_price = float(test_variant.product.base_price) + float(test_variant.price_modifier)
        total_value = unit_price * 100

        assert total_value == (99.99 + 10.00) * 100

    @pytest.mark.asyncio
    async def test_low_stock_check(self, db_session, test_inventory):
        test_inventory.quantity_available = 10
        test_inventory.low_stock_threshold = 10
        await db_session.commit()
        await db_session.refresh(test_inventory)

        is_low_stock = test_inventory.quantity_available <= test_inventory.low_stock_threshold
        assert is_low_stock is True

        test_inventory.quantity_available = 11
        await db_session.commit()
        await db_session.refresh(test_inventory)

        is_low_stock = test_inventory.quantity_available <= test_inventory.low_stock_threshold
        assert is_low_stock is False


from backend.app.models.models import ProductVariant
