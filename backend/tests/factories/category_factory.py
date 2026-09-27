"""
Category Factory - Creates Category model instances with unique data.
"""
import uuid
from .base import BaseFactory
from backend.app.models.models import Category


class CategoryFactory(BaseFactory):
    """Factory for creating Category model instances."""

    @classmethod
    def build(cls, **kwargs) -> dict:
        """Build category attributes dictionary."""
        unique_suffix = cls.generate_unique_suffix()

        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "name": kwargs.get("name", f"Category {unique_suffix}"),
            "description": kwargs.get("description", f"Description for category {unique_suffix}"),
            "icon": kwargs.get("icon", "category-icon"),
            "is_active": kwargs.get("is_active", True),
        }

    @classmethod
    async def create(cls, db_session, **kwargs) -> Category:
        """Create and save Category to database."""
        data = cls.build(**kwargs)
        category = Category(**data)
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        return category

    @classmethod
    async def create_batch(cls, db_session, count: int, **kwargs) -> list:
        """Create multiple categories."""
        categories = []
        for i in range(count):
            category = await cls.create(db_session, **kwargs)
            categories.append(category)
        return categories
