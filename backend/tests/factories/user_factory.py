"""
User Factory - Creates User model instances with unique data.
"""
import uuid
from typing import Optional
from decimal import Decimal

from backend.app.models.models import User, UserRole
from backend.app.services.auth import hash_password
from .base import BaseFactory


class UserFactory(BaseFactory):
    """Factory for creating User model instances."""

    @classmethod
    def build(cls, **kwargs) -> dict:
        """Build user attributes dictionary."""
        unique_suffix = cls.generate_unique_suffix()

        return {
            "id": kwargs.get("id", uuid.uuid4()),
            "name": kwargs.get("name", f"Test User {unique_suffix}"),
            "email": kwargs.get("email", f"user_{unique_suffix}@test.com"),
            "password_hash": kwargs.get("password_hash", hash_password("password123")),
            "role": kwargs.get("role", UserRole.client),
            "is_active": kwargs.get("is_active", True),
            "avatar_path": kwargs.get("avatar_path", None),
        }

    @classmethod
    async def create(cls, db_session, **kwargs) -> User:
        """Create and save User to database."""
        data = cls.build(**kwargs)
        user = User(**data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @classmethod
    def build_admin(cls, **kwargs) -> dict:
        """Build admin user attributes."""
        return cls.build(role=UserRole.admin, **kwargs)

    @classmethod
    def build_cashier(cls, **kwargs) -> dict:
        """Build cashier user attributes."""
        return cls.build(role=UserRole.cashier, **kwargs)

    @classmethod
    def build_client(cls, **kwargs) -> dict:
        """Build client user attributes."""
        return cls.build(role=UserRole.client, **kwargs)

    @classmethod
    async def create_admin(cls, db_session, **kwargs) -> User:
        """Create admin user."""
        return await cls.create(db_session, role=UserRole.admin, **kwargs)

    @classmethod
    async def create_cashier(cls, db_session, **kwargs) -> User:
        """Create cashier user."""
        return await cls.create(db_session, role=UserRole.cashier, **kwargs)

    @classmethod
    async def create_client(cls, db_session, **kwargs) -> User:
        """Create client user."""
        return await cls.create(db_session, role=UserRole.client, **kwargs)
