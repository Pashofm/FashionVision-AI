"""
Inventory Factory - Creates Inventory and InventoryMovement model instances.
"""
import uuid
from typing import Optional
from decimal import Decimal

from backend.app.models.models import Inventory, InventoryMovement, MovementType
from .base import BaseFactory
from .product_factory import ProductVariantFactory, ProductFactory


class InventoryFactory(BaseFactory):
    """Factory for creating Inventory model instances."""

    @classmethod
    def build(cls, variant_id=None, **kwargs) -> dict:
        """Build inventory attributes dictionary."""
        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "product_variant_id": variant_id or kwargs.get("product_variant_id"),
            "quantity_available": kwargs.get("quantity_available", 100),
            "quantity_reserved": kwargs.get("quantity_reserved", 0),
            "low_stock_threshold": kwargs.get("low_stock_threshold", 10),
            "updated_by": kwargs.get("updated_by", None),
        }

    @classmethod
    async def create(cls, db_session, variant=None, **kwargs) -> Inventory:
        """Create and save Inventory to database."""
        if variant is not None:
            kwargs["product_variant_id"] = variant.id
        elif "product_variant_id" not in kwargs:
            var = await ProductVariantFactory.create(db_session)
            kwargs["product_variant_id"] = var.id

        data = cls.build(**kwargs)
        inventory = Inventory(**data)
        db_session.add(inventory)
        await db_session.commit()
        await db_session.refresh(inventory)
        return inventory

    @classmethod
    async def create_with_variant(cls, db_session, **kwargs) -> tuple:
        """Create inventory with its variant."""
        variant = await ProductVariantFactory.create(db_session)
        inventory = await cls.create(db_session, variant=variant, **kwargs)
        return inventory, variant

    @classmethod
    async def create_low_stock(cls, db_session, threshold=10, **kwargs) -> Inventory:
        """Create inventory with low stock."""
        return await cls.create(
            db_session,
            quantity_available=5,
            low_stock_threshold=threshold,
            **kwargs
        )


class InventoryMovementFactory(BaseFactory):
    """Factory for creating InventoryMovement model instances."""

    @classmethod
    def build(cls, variant_id=None, **kwargs) -> dict:
        """Build movement attributes dictionary."""
        quantity_change = kwargs.get("quantity_change", 10)
        quantity_before = kwargs.get("quantity_before", 100)
        quantity_after = kwargs.get("quantity_after", quantity_before + quantity_change)

        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "product_variant_id": variant_id or kwargs.get("product_variant_id"),
            "movement_type": kwargs.get("movement_type", MovementType.restock),
            "quantity_change": quantity_change,
            "quantity_before": quantity_before,
            "quantity_after": quantity_after,
            "reference_id": kwargs.get("reference_id", None),
            "notes": kwargs.get("notes", f"Movement note"),
            "created_by": kwargs.get("created_by", None),
        }

    @classmethod
    async def create(cls, db_session, variant=None, **kwargs) -> InventoryMovement:
        """Create and save InventoryMovement to database."""
        if variant is not None:
            kwargs["product_variant_id"] = variant.id
        elif "product_variant_id" not in kwargs:
            var = await ProductVariantFactory.create(db_session)
            kwargs["product_variant_id"] = var.id

        data = cls.build(**kwargs)
        movement = InventoryMovement(**data)
        db_session.add(movement)
        await db_session.commit()
        await db_session.refresh(movement)
        return movement

    @classmethod
    def build_sale(cls, quantity=1, **kwargs) -> dict:
        """Build sale movement."""
        return cls.build(
            movement_type=MovementType.sale,
            quantity_change=-abs(quantity),
            **kwargs
        )

    @classmethod
    def build_restock(cls, quantity=10, **kwargs) -> dict:
        """Build restock movement."""
        return cls.build(
            movement_type=MovementType.restock,
            quantity_change=abs(quantity),
            **kwargs
        )

    @classmethod
    def build_adjustment(cls, quantity=5, **kwargs) -> dict:
        """Build adjustment movement."""
        return cls.build(
            movement_type=MovementType.adjustment,
            quantity_change=quantity,
            **kwargs
        )
