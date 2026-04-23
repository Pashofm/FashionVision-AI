import pytest
import asyncio
import sys
import os
from typing import AsyncGenerator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_DB_TESTS", "true").lower() == "true",
    reason="Database tests skipped by default (set SKIP_DB_TESTS=false to run)"
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    from unittest.mock import AsyncMock
    return AsyncMock()


@pytest.fixture
async def db_session() -> AsyncGenerator:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool

    try:
        import aiosqlite
    except ImportError:
        pytest.skip("aiosqlite not installed")

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from backend.app.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
async def client(db_session) -> AsyncGenerator:
    from httpx import AsyncClient, ASGITransport
    from backend.app.main import app
    from backend.app.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client, db_session) -> AsyncGenerator:
    import uuid
    from backend.app.models.models import User, UserRole
    from backend.app.services.auth import hash_password, create_access_token

    user = User(
        id=uuid.uuid4(),
        name="Test Admin",
        email="admin@test.com",
        password_hash=hash_password("testpassword123"),
        role=UserRole.admin,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    client.headers["Authorization"] = f"Bearer {token}"

    yield client

    client.headers.pop("Authorization", None)