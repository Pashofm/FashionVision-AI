"""Factories for product size and color attributes."""

import uuid

from sqlalchemy import select

from backend.app.models.models import AttributeOption
from .base import BaseFactory


class AttributeOptionFactory(BaseFactory):
    """Create unique attribute options used by product variants."""

    @classmethod
    async def create(cls, db_session, attribute_type, value=None, **kwargs) -> AttributeOption:
        unique_suffix = cls.generate_unique_suffix()
        value = value or f"{attribute_type}-{unique_suffix}"
        existing = await db_session.execute(
            select(AttributeOption).where(
                AttributeOption.type == attribute_type,
                AttributeOption.value == value,
            )
        )
        option = existing.scalar_one_or_none()
        if option:
            return option

        option = AttributeOption(
            id=kwargs.get("id", uuid.uuid4()),
            type=attribute_type,
            value=value,
            hex_code=kwargs.get("hex_code"),
            sort_order=kwargs.get("sort_order", 0),
            is_active=kwargs.get("is_active", True),
        )
        db_session.add(option)
        await db_session.commit()
        await db_session.refresh(option)
        return option
