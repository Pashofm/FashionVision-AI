"""
Cart Factory - Creates Cart, CartItem, and Session model instances.
"""
import uuid
from typing import Optional, List
from decimal import Decimal

from backend.app.models.models import (
    Cart, CartItem, Session, CartStatus, SessionStatus, PaymentMethod
)
from .base import BaseFactory
from .user_factory import UserFactory
from .product_factory import ProductFactory, ProductVariantFactory


class SessionFactory(BaseFactory):
    """Factory for creating Session model instances."""

    @classmethod
    def build(cls, **kwargs) -> dict:
        """Build session attributes dictionary."""
        unique_suffix = cls.generate_unique_suffix()

        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "session_token": kwargs.get("session_token", uuid.uuid4()),
            "client_user_id": kwargs.get("client_user_id", None),
            "station_id": kwargs.get("station_id", f"Kiosk-{unique_suffix[:8]}"),
            "status": kwargs.get("status", SessionStatus.active),
        }

    @classmethod
    async def create(cls, db_session, client_user=None, **kwargs) -> Session:
        """Create and save Session to database."""
        if client_user is not None:
            kwargs["client_user_id"] = client_user.id

        data = cls.build(**kwargs)
        session = Session(**data)
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        return session

    @classmethod
    async def create_with_user(cls, db_session, **kwargs) -> tuple:
        """Create session with a client user."""
        user = await UserFactory.create_client(db_session)
        session = await cls.create(db_session, client_user=user, **kwargs)
        return session, user

    @classmethod
    async def create_abandoned(cls, db_session, **kwargs) -> Session:
        """Create an abandoned session."""
        return await cls.create(db_session, status=SessionStatus.abandoned, **kwargs)


class CartFactory(BaseFactory):
    """Factory for creating Cart model instances."""

    @classmethod
    def build(cls, session_id=None, **kwargs) -> dict:
        """Build cart attributes dictionary."""
        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "session_id": session_id or kwargs.get("session_id"),
            "status": kwargs.get("status", CartStatus.building),
            "payment_method": kwargs.get("payment_method", None),
            "submitted_at": kwargs.get("submitted_at", None),
            "notes": kwargs.get("notes", None),
        }

    @classmethod
    async def create(cls, db_session, session=None, **kwargs) -> Cart:
        """Create and save Cart to database."""
        if session is not None:
            kwargs["session_id"] = session.id
        elif "session_id" not in kwargs:
            sess = await SessionFactory.create(db_session)
            kwargs["session_id"] = sess.id

        data = cls.build(**kwargs)
        cart = Cart(**data)
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)
        return cart

    @classmethod
    async def create_with_session(cls, db_session, **kwargs) -> tuple:
        """Create cart with its session."""
        session = await SessionFactory.create(db_session)
        cart = await cls.create(db_session, session=session, **kwargs)
        return cart, session

    @classmethod
    async def create_submitted(cls, db_session, **kwargs) -> Cart:
        """Create a submitted cart."""
        from datetime import datetime
        return await cls.create(
            db_session,
            status=CartStatus.submitted,
            submitted_at=datetime.utcnow(),
            **kwargs
        )

    @classmethod
    async def create_with_items(cls, db_session, item_count=3, **kwargs) -> tuple:
        """Create cart with multiple items."""
        cart = await cls.create(db_session, **kwargs)
        items = []

        for i in range(item_count):
            variant = await ProductVariantFactory.create(db_session)
            item = await CartItemFactory.create(
                db_session,
                cart=cart,
                variant=variant,
                quantity=i + 1
            )
            items.append(item)

        await db_session.refresh(cart)
        return cart, items


class CartItemFactory(BaseFactory):
    """Factory for creating CartItem model instances."""

    @classmethod
    def build(cls, cart_id=None, product_id=None, variant_id=None, **kwargs) -> dict:
        """Build cart item attributes dictionary."""
        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "cart_id": cart_id or kwargs.get("cart_id"),
            "product_id": product_id or kwargs.get("product_id"),
            "product_variant_id": variant_id or kwargs.get("product_variant_id"),
            "quantity": kwargs.get("quantity", 1),
            "unit_price": kwargs.get("unit_price", Decimal("99.99")),
            "detection_confidence": kwargs.get("detection_confidence", None),
            "detection_image_path": kwargs.get("detection_image_path", None),
            "detection_bbox": kwargs.get("detection_bbox", None),
            "confirmed": kwargs.get("confirmed", False),
        }

    @classmethod
    async def create(cls, db_session, cart=None, product=None, variant=None, **kwargs) -> CartItem:
        """Create and save CartItem to database."""
        if cart is not None:
            kwargs["cart_id"] = cart.id
        elif "cart_id" not in kwargs:
            c = await CartFactory.create(db_session)
            kwargs["cart_id"] = c.id

        if product is not None:
            kwargs["product_id"] = product.id
        elif "product_id" not in kwargs:
            p = await ProductFactory.create(db_session)
            kwargs["product_id"] = p.id

        if variant is not None:
            kwargs["product_variant_id"] = variant.id
        elif "product_variant_id" not in kwargs:
            v = await ProductVariantFactory.create(db_session, product_id=kwargs["product_id"])
            kwargs["product_variant_id"] = v.id

        data = cls.build(**kwargs)
        item = CartItem(**data)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        return item

    @classmethod
    async def create_with_detection(
        cls, db_session, confidence=0.95, bbox={"x1": 100, "y1": 100, "x2": 200, "y2": 200}, **kwargs
    ) -> CartItem:
        """Create cart item with YOLO detection data."""
        return await cls.create(
            db_session,
            detection_confidence=confidence,
            detection_bbox=bbox,
            detection_image_path="/tmp/detection.jpg",
            **kwargs
        )
