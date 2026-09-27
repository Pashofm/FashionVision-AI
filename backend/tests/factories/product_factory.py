"""
Product Factory - Creates Product and ProductVariant model instances with unique data.
"""
import uuid
from typing import Optional, List
from decimal import Decimal

from backend.app.models.models import Product, ProductVariant
from .base import BaseFactory
from .category_factory import CategoryFactory


class ProductFactory(BaseFactory):
    """Factory for creating Product model instances."""

    @classmethod
    def build(cls, category_id=None, **kwargs) -> dict:
        """Build product attributes dictionary."""
        unique_suffix = cls.generate_unique_suffix()

        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "category_id": category_id or kwargs.get("category_id"),
            "name": kwargs.get("name", f"Product {unique_suffix}"),
            "description": kwargs.get("description", f"Description for product {unique_suffix}"),
            "sku": kwargs.get("sku", f"SKU-{unique_suffix}"),
            "base_price": kwargs.get("base_price", Decimal("99.99")),
            "images": kwargs.get("images", []),
            "is_active": kwargs.get("is_active", True),
        }

    @classmethod
    async def create(cls, db_session, category=None, **kwargs) -> Product:
        """Create and save Product to database."""
        if category is not None:
            kwargs["category_id"] = category.id
        elif "category_id" not in kwargs:
            cat = await CategoryFactory.create(db_session)
            kwargs["category_id"] = cat.id

        data = cls.build(**kwargs)
        product = Product(**data)
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        return product

    @classmethod
    async def create_with_category(cls, db_session, **kwargs) -> tuple:
        """Create product with its category."""
        category = await CategoryFactory.create(db_session)
        product = await cls.create(db_session, category=category, **kwargs)
        return product, category


class ProductVariantFactory(BaseFactory):
    """Factory for creating ProductVariant model instances."""

    @classmethod
    def build(cls, product_id=None, **kwargs) -> dict:
        """Build variant attributes dictionary."""
        unique_suffix = cls.generate_unique_suffix()

        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "product_id": product_id or kwargs.get("product_id"),
            "size": kwargs.get("size", "M"),
            "color": kwargs.get("color", f"Color {unique_suffix}"),
            "color_hex": kwargs.get("color_hex", "#FF0000"),
            "sku_variant": kwargs.get("sku_variant", f"VAR-{unique_suffix}"),
            "price_modifier": kwargs.get("price_modifier", Decimal("0.00")),
            "is_active": kwargs.get("is_active", True),
        }

    @classmethod
    async def create(cls, db_session, product=None, **kwargs) -> ProductVariant:
        """Create and save ProductVariant to database."""
        if product is not None:
            kwargs["product_id"] = product.id
        elif "product_id" not in kwargs:
            prod = await ProductFactory.create(db_session)
            kwargs["product_id"] = prod.id

        data = cls.build(**kwargs)
        variant = ProductVariant(**data)
        db_session.add(variant)
        await db_session.commit()
        await db_session.refresh(variant)
        return variant

    @classmethod
    async def create_with_product(cls, db_session, **kwargs) -> tuple:
        """Create variant with its product."""
        product = await ProductFactory.create(db_session)
        variant = await cls.create(db_session, product=product, **kwargs)
        return variant, product

    @classmethod
    async def create_batch_sizes(cls, db_session, product, sizes: List[str], **kwargs) -> List[ProductVariant]:
        """Create multiple variants for same product with different sizes."""
        variants = []
        for size in sizes:
            variant = await cls.create(db_session, product=product, size=size, **kwargs)
            variants.append(variant)
        return variants
