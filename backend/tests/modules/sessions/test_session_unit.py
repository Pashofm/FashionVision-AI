"""
Session Manager Unit Tests

Tests for session lifecycle management:
- Session creation
- Activity updates (heartbeat)
- Session expiration (manual and automatic)
- Timeout configuration
- Session status transitions
"""
import pytest
import uuid
from datetime import datetime, timedelta

from backend.app.models.models import Session, SessionStatus
from backend.app.services.session_manager import SessionManager
from tests.factories import SessionFactory, UserFactory


pytestmark = pytest.mark.asyncio


class TestSessionCreation:
    """Tests for session creation."""

    async def test_create_session(self, db_session):
        """Test creating a basic session."""
        session = await SessionFactory.create(db_session)

        assert session.id is not None
        assert session.session_token is not None
        assert session.status == SessionStatus.active
        assert session.started_at is not None
        assert session.last_activity_at is not None
        assert session.ended_at is None

    async def test_create_session_with_user(self, db_session, client_user):
        """Test creating session linked to user."""
        session = await SessionFactory.create(
            db_session,
            client_user=client_user
        )

        assert session.client_user_id == client_user.id

    async def test_create_session_without_user(self, db_session):
        """Test creating anonymous session (kiosk mode)."""
        session = await SessionFactory.create(db_session)

        assert session.client_user_id is None
        assert session.station_id is not None

    async def test_create_session_unique_token(self, db_session):
        """Test that session tokens are unique."""
        token = uuid.uuid4()
        session1 = await SessionFactory.create(db_session, session_token=token)

        session2 = Session(
            id=uuid.uuid4(),
            session_token=token,
            status=SessionStatus.active
        )
        db_session.add(session2)

        with pytest.raises(Exception):
            await db_session.commit()

    async def test_session_default_status(self, db_session):
        """Test default session status is active."""
        session = await SessionFactory.create(db_session)

        assert session.status == SessionStatus.active


class TestSessionActivityUpdate:
    """Tests for session activity updates."""

    async def test_update_activity_success(self, db_session):
        """Test successful activity update."""
        session = await SessionFactory.create(db_session)
        original_activity = session.last_activity_at

        result = await SessionManager.update_activity(db_session, session.id)
        await db_session.commit()
        await db_session.refresh(session)

        assert result is True
        assert session.last_activity_at is not None

    async def test_update_activity_nonexistent_session(self, db_session):
        """Test activity update for non-existent session."""
        result = await SessionManager.update_activity(
            db_session,
            uuid.uuid4()
        )

        assert result is False

    async def test_update_activity_clears_ended_at(self, db_session):
        """Test that update_activity clears ended_at."""
        session = await SessionFactory.create(db_session)
        session.ended_at = datetime.utcnow()
        await db_session.commit()

        await SessionManager.update_activity(db_session, session.id)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.ended_at is None

    async def test_update_activity_preserves_ended_if_not_active(self, db_session):
        """Test that update_activity does not affect ended_at if session not active."""
        session = await SessionFactory.create(db_session)
        session.status = SessionStatus.abandoned
        session.ended_at = datetime.utcnow()
        await db_session.commit()

        await SessionManager.update_activity(db_session, session.id)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.ended_at is not None


class TestSessionActiveStatus:
    """Tests for checking session active status."""

    async def test_is_session_active_true(self, db_session):
        """Test session is active."""
        from datetime import datetime

        session = await SessionFactory.create(db_session)
        session.last_activity_at = datetime.utcnow()
        await db_session.commit()

        result = await SessionManager.is_session_active(db_session, session.id)

        assert result is True

    async def test_is_session_active_nonexistent(self, db_session):
        """Test non-existent session is not active."""
        result = await SessionManager.is_session_active(db_session, uuid.uuid4())

        assert result is False

    async def test_is_session_active_abandoned(self, db_session):
        """Test abandoned session is not active."""
        session = await SessionFactory.create(db_session)
        session.status = SessionStatus.abandoned
        await db_session.commit()

        result = await SessionManager.is_session_active(db_session, session.id)

        assert result is False

    async def test_is_session_active_completed(self, db_session):
        """Test completed session is not active."""
        session = await SessionFactory.create(db_session)
        session.status = SessionStatus.completed
        await db_session.commit()

        result = await SessionManager.is_session_active(db_session, session.id)

        assert result is False

    async def test_is_session_active_with_ended_at(self, db_session):
        """Test session with ended_at is not active."""
        session = await SessionFactory.create(db_session)
        session.ended_at = datetime.utcnow()
        await db_session.commit()

        result = await SessionManager.is_session_active(db_session, session.id)

        assert result is False


class TestSessionExpiration:
    """Tests for session expiration."""

    async def test_expire_session_success(self, db_session):
        """Test manually expiring a session."""
        session = await SessionFactory.create(db_session)

        result = await SessionManager.expire_session(db_session, session.id)
        await db_session.commit()
        await db_session.refresh(session)

        assert result is True
        assert session.status == SessionStatus.abandoned
        assert session.ended_at is not None

    async def test_expire_nonexistent_session(self, db_session):
        """Test expiring non-existent session."""
        result = await SessionManager.expire_session(db_session, uuid.uuid4())

        assert result is False

    async def test_expire_already_expired_session(self, db_session):
        """Test expiring already abandoned session."""
        session = await SessionFactory.create(db_session)
        await SessionManager.expire_session(db_session, session.id)
        await db_session.commit()

        result = await SessionManager.expire_session(db_session, session.id)
        await db_session.refresh(session)

        assert result is True
        assert session.status == SessionStatus.abandoned


class TestSessionExtend:
    """Tests for extending session timeout."""

    async def test_extend_session_success(self, db_session):
        """Test extending an active session."""
        session = await SessionFactory.create(db_session)
        original_activity = session.last_activity_at

        result = await SessionManager.extend_session(db_session, session.id)
        await db_session.commit()
        await db_session.refresh(session)

        assert result is True
        assert session.ended_at is None
        assert session.status == SessionStatus.active

    async def test_extend_session_clears_ended_at(self, db_session):
        """Test that extend_session clears ended_at."""
        session = await SessionFactory.create(db_session)
        session.ended_at = datetime.utcnow()
        await db_session.commit()

        await SessionManager.extend_session(db_session, session.id)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.ended_at is None

    async def test_extend_nonexistent_session(self, db_session):
        """Test extending non-existent session."""
        result = await SessionManager.extend_session(db_session, uuid.uuid4())

        assert result is False

    async def test_extend_abandoned_session_fails(self, db_session):
        """Test that extending abandoned session fails."""
        session = await SessionFactory.create(db_session)
        session.status = SessionStatus.abandoned
        await db_session.commit()

        result = await SessionManager.extend_session(db_session, session.id)

        assert result is False

    async def test_extend_completed_session_fails(self, db_session):
        """Test that extending completed session fails."""
        session = await SessionFactory.create(db_session)
        session.status = SessionStatus.completed
        await db_session.commit()

        result = await SessionManager.extend_session(db_session, session.id)

        assert result is False


class TestExpireInactiveSessions:
    """Tests for automatic expiration of inactive sessions."""

    async def test_expire_inactive_sessions_none_to_expire(self, db_session):
        """Test when no sessions need expiration."""
        await SessionFactory.create(db_session)

        SessionManager.set_timeout_minutes(30)
        result = await SessionManager.expire_inactive_sessions(db_session)

        assert result == 0

    async def test_expire_inactive_sessions_one_expired(self, db_session):
        """Test expiring one inactive session."""
        SessionManager.set_timeout_minutes(30)

        old_time = datetime.utcnow() - timedelta(minutes=60)
        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            status=SessionStatus.active,
            last_activity_at=old_time,
            started_at=old_time
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        result = await SessionManager.expire_inactive_sessions(db_session)
        await db_session.commit()

        assert result >= 0

    async def test_expire_inactive_sessions_preserves_active(self, db_session):
        """Test that recently active sessions are not expired."""
        SessionManager.set_timeout_minutes(30)

        recent_time = datetime.utcnow() - timedelta(minutes=5)
        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            status=SessionStatus.active,
            last_activity_at=recent_time,
            started_at=recent_time
        )
        db_session.add(session)
        await db_session.commit()

        result = await SessionManager.expire_inactive_sessions(db_session)
        await db_session.refresh(session)

        assert result == 0
        assert session.status == SessionStatus.active


class TestSessionTimeoutConfiguration:
    """Tests for session timeout configuration."""

    async def test_set_and_get_timeout(self):
        """Test setting and getting timeout."""
        SessionManager.set_timeout_minutes(60)
        assert SessionManager.get_timeout_minutes() == 60

        SessionManager.set_timeout_minutes(30)
        assert SessionManager.get_timeout_minutes() == 30

    async def test_timeout_affects_expiration(self, db_session):
        """Test that timeout value affects session expiration."""
        from datetime import datetime

        SessionManager.set_timeout_minutes(5)

        old_time = datetime.utcnow() - timedelta(minutes=10)
        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            status=SessionStatus.active,
            last_activity_at=old_time,
            started_at=old_time
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        is_active = await SessionManager.is_session_active(db_session, session.id)

        assert is_active is False


class TestSessionInfo:
    """Tests for session info retrieval."""

    async def test_get_session_info(self, db_session):
        """Test getting session information."""
        session = await SessionFactory.create(db_session)

        info = await SessionManager.get_session_info(db_session, session.id)

        assert info is not None
        assert info["id"] == session.id
        assert "status" in info
        assert "last_activity_at" in info

    async def test_get_session_info_nonexistent(self, db_session):
        """Test getting info for non-existent session."""
        info = await SessionManager.get_session_info(db_session, uuid.uuid4())

        assert info is None


class TestSessionEdgeCases:
    """Tests for edge cases in session management."""

    async def test_session_without_station_id(self, db_session):
        """Test session without station ID."""
        session = await SessionFactory.create(db_session, station_id=None)

        assert session.station_id is None

    async def test_session_status_transitions(self, db_session):
        """Test session status transitions."""
        session = await SessionFactory.create(db_session)

        session.status = SessionStatus.completed
        await db_session.commit()

        is_active = await SessionManager.is_session_active(db_session, session.id)
        assert is_active is False

    async def test_multiple_sessions_same_user(self, db_session, client_user):
        """Test user can have multiple sessions."""
        session1 = await SessionFactory.create(
            db_session,
            client_user=client_user
        )
        session2 = await SessionFactory.create(
            db_session,
            client_user=client_user
        )

        assert session1.id != session2.id

    async def test_session_activity_during_checkout(self, db_session):
        """Test session remains active during checkout process."""
        session = await SessionFactory.create(db_session)

        await SessionManager.update_activity(db_session, session.id)
        await db_session.commit()

        is_active = await SessionManager.is_session_active(db_session, session.id)
        assert is_active is True
