"""
Base Factory - Abstract factory class for all model factories.
Provides common functionality for creating test data with unique identifiers.
"""
import uuid
from typing import Any, Dict, Optional
from datetime import datetime


class BaseFactory:
    """Abstract base class for all factories."""

    _counter = 0

    @classmethod
    def generate_id(cls) -> uuid.UUID:
        """Generate a unique UUID."""
        return uuid.uuid4()

    @classmethod
    def generate_unique_suffix(cls) -> str:
        """Generate a unique suffix for names to avoid conflicts."""
        cls._counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{timestamp}_{cls._counter}_{uuid.uuid4().hex[:6]}"

    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build a dictionary of model attributes (not saved to DB)."""
        raise NotImplementedError("Subclasses must implement build()")

    @classmethod
    async def create(cls, db_session, **kwargs):
        """Create and save model instance to database."""
        raise NotImplementedError("Subclasses must implement create()")

    @classmethod
    async def create_batch(cls, db_session, count: int, **kwargs):
        """Create multiple instances."""
        instances = []
        for _ in range(count):
            instance = await cls.create(db_session, **kwargs)
            instances.append(instance)
        return instances
