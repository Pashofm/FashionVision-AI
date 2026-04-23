import pytest
import os
import sys
from unittest.mock import AsyncMock
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_DB_TESTS", "false").lower() == "true",
    reason="Database tests skipped (set SKIP_DB_TESTS=false to run)"
)


@pytest.fixture
def mock_db_session():
    return AsyncMock()


class TestSessionManager:
    def test_set_timeout_minutes(self):
        from backend.app.services.session_manager import SessionManager
        SessionManager.set_timeout_minutes(60)
        assert SessionManager.get_timeout_minutes() == 60
        SessionManager.set_timeout_minutes(30)

    def test_get_timeout_minutes_default(self):
        from backend.app.services.session_manager import SessionManager
        SessionManager.set_timeout_minutes(30)
        assert SessionManager.get_timeout_minutes() == 30

    @pytest.mark.asyncio
    async def test_update_activity_no_session(self, mock_db_session):
        from backend.app.services.session_manager import SessionManager
        fake_session_id = uuid.uuid4()

        result = await SessionManager.update_activity(mock_db_session, fake_session_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_session_active_no_session(self, mock_db_session):
        from backend.app.services.session_manager import SessionManager
        fake_session_id = uuid.uuid4()

        result = await SessionManager.is_session_active(mock_db_session, fake_session_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_expire_session_no_session(self, mock_db_session):
        from backend.app.services.session_manager import SessionManager
        fake_session_id = uuid.uuid4()

        result = await SessionManager.expire_session(mock_db_session, fake_session_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_extend_session_no_session(self, mock_db_session):
        from backend.app.services.session_manager import SessionManager
        fake_session_id = uuid.uuid4()

        result = await SessionManager.extend_session(mock_db_session, fake_session_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_expire_inactive_sessions_no_sessions(self, mock_db_session):
        from backend.app.services.session_manager import SessionManager
        result = await SessionManager.expire_inactive_sessions(mock_db_session)
        assert result == 0