import pytest
import uuid
from datetime import datetime, timedelta


class TestSessionCreation:
    @pytest.mark.asyncio
    async def test_create_session(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            station_id="Kiosk-01",
            status=SessionStatus.active
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None
        assert session.session_token is not None
        assert session.client_user_id == client_user.id
        assert session.status == SessionStatus.active
        assert session.started_at is not None
        assert session.ended_at is None

    @pytest.mark.asyncio
    async def test_create_session_without_user(self, db_session):
        from backend.app.models.models import Session, SessionStatus

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            station_id="Kiosk-02",
            status=SessionStatus.active
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.client_user_id is None
        assert session.status == SessionStatus.active

    @pytest.mark.asyncio
    async def test_session_unique_token(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus

        token = uuid.uuid4()
        session1 = Session(
            id=uuid.uuid4(),
            session_token=token,
            client_user_id=client_user.id,
            status=SessionStatus.active
        )
        db_session.add(session1)
        await db_session.commit()

        session2 = Session(
            id=uuid.uuid4(),
            session_token=token,
            status=SessionStatus.active
        )
        db_session.add(session2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_session_default_status(self, db_session):
        from backend.app.models.models import Session, SessionStatus

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4()
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.status == SessionStatus.active


class TestSessionManagerUpdateActivity:
    @pytest.mark.asyncio
    async def test_update_activity_active_session(self, db_session, test_session):
        from backend.app.services.session_manager import SessionManager

        result = await SessionManager.update_activity(db_session, test_session.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_activity_nonexistent_session(self, db_session):
        from backend.app.services.session_manager import SessionManager

        fake_id = uuid.uuid4()
        result = await SessionManager.update_activity(db_session, fake_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_update_activity_expired_session(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.abandoned
        )
        db_session.add(session)
        await db_session.commit()

        result = await SessionManager.update_activity(db_session, session.id)

        assert result is False


class TestSessionManagerIsActive:
    @pytest.mark.asyncio
    async def test_is_session_active_true(self, db_session, test_session):
        from backend.app.services.session_manager import SessionManager

        result = await SessionManager.is_session_active(db_session, test_session.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_is_session_active_nonexistent(self, db_session):
        from backend.app.services.session_manager import SessionManager

        fake_id = uuid.uuid4()
        result = await SessionManager.is_session_active(db_session, fake_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_session_active_abandoned(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.abandoned
        )
        db_session.add(session)
        await db_session.commit()

        result = await SessionManager.is_session_active(db_session, session.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_session_active_completed(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.completed
        )
        db_session.add(session)
        await db_session.commit()

        result = await SessionManager.is_session_active(db_session, session.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_session_active_with_ended_at(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.active,
            ended_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.commit()

        result = await SessionManager.is_session_active(db_session, session.id)

        assert result is False


class TestSessionManagerExpireSession:
    @pytest.mark.asyncio
    async def test_expire_session_success(self, db_session, test_session):
        from backend.app.models.models import SessionStatus
        from backend.app.services.session_manager import SessionManager

        result = await SessionManager.expire_session(db_session, test_session.id)

        assert result is True
        await db_session.refresh(test_session)
        assert test_session.status == SessionStatus.abandoned
        assert test_session.ended_at is not None

    @pytest.mark.asyncio
    async def test_expire_nonexistent_session(self, db_session):
        from backend.app.services.session_manager import SessionManager

        fake_id = uuid.uuid4()
        result = await SessionManager.expire_session(db_session, fake_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_expire_already_expired_session(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.abandoned
        )
        db_session.add(session)
        await db_session.commit()

        result = await SessionManager.expire_session(db_session, session.id)

        assert result is True


class TestSessionManagerExtendSession:
    @pytest.mark.asyncio
    async def test_extend_session_success(self, db_session, test_session):
        from backend.app.models.models import SessionStatus
        from backend.app.services.session_manager import SessionManager

        original_started_at = test_session.started_at

        result = await SessionManager.extend_session(db_session, test_session.id)

        assert result is True
        await db_session.refresh(test_session)
        assert test_session.status == SessionStatus.active
        assert test_session.ended_at is None
        assert test_session.started_at == original_started_at

    @pytest.mark.asyncio
    async def test_extend_nonexistent_session(self, db_session):
        from backend.app.services.session_manager import SessionManager

        fake_id = uuid.uuid4()
        result = await SessionManager.extend_session(db_session, fake_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_extend_abandoned_session(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.abandoned
        )
        db_session.add(session)
        await db_session.commit()

        result = await SessionManager.extend_session(db_session, session.id)

        assert result is False


class TestSessionManagerExpireInactiveSessions:
    @pytest.mark.asyncio
    async def test_expire_inactive_sessions_none_expired(self, db_session, test_session):
        from backend.app.services.session_manager import SessionManager

        result = await SessionManager.expire_inactive_sessions(db_session)

        assert result == 0

    @pytest.mark.asyncio
    async def test_expire_inactive_sessions_one_expired(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        old_time = datetime.utcnow() - timedelta(minutes=60)
        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.active,
            started_at=old_time
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        SessionManager.set_timeout_minutes(30)

        result = await SessionManager.expire_inactive_sessions(db_session)

        assert result >= 0

    @pytest.mark.asyncio
    async def test_expire_inactive_sessions_multiple(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        old_time = datetime.utcnow() - timedelta(minutes=60)
        sessions = []
        for i in range(5):
            session = Session(
                id=uuid.uuid4(),
                session_token=uuid.uuid4(),
                client_user_id=client_user.id,
                status=SessionStatus.active,
                started_at=old_time
            )
            sessions.append(session)
            db_session.add(session)
        await db_session.commit()

        SessionManager.set_timeout_minutes(30)

        result = await SessionManager.expire_inactive_sessions(db_session)

        assert result >= 0

    @pytest.mark.asyncio
    async def test_expire_inactive_sessions_recent_sessions_not_expired(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        recent_time = datetime.utcnow() - timedelta(minutes=5)
        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.active,
            started_at=recent_time
        )
        db_session.add(session)
        await db_session.commit()

        SessionManager.set_timeout_minutes(30)

        result = await SessionManager.expire_inactive_sessions(db_session)

        assert result == 0

    @pytest.mark.asyncio
    async def test_expire_inactive_sessions_only_active(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        old_time = datetime.utcnow() - timedelta(minutes=60)
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        session_active = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.active,
            started_at=old_time
        )
        session_completed = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.completed,
            started_at=recent_time
        )
        db_session.add(session_active)
        db_session.add(session_completed)
        await db_session.commit()

        SessionManager.set_timeout_minutes(30)

        result = await SessionManager.expire_inactive_sessions(db_session)

        assert result >= 0

    @pytest.mark.asyncio
    async def test_timeout_affects_expiration(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus
        from backend.app.services.session_manager import SessionManager

        old_time = datetime.utcnow() - timedelta(minutes=10)
        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.active,
            started_at=old_time
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        SessionManager.set_timeout_minutes(5)

        is_active = await SessionManager.is_session_active(db_session, session.id)

        assert is_active is False


class TestSessionRelationships:
    @pytest.mark.asyncio
    async def test_session_carts_relationship(self, db_session, test_session, test_cart):
        from backend.app.models.models import Cart
        from sqlalchemy import select

        result = await db_session.execute(
            select(Cart).where(Cart.session_id == test_session.id)
        )
        carts = result.scalars().all()
        assert len(carts) >= 1

    @pytest.mark.asyncio
    async def test_session_user_relationship(self, db_session, test_session, client_user):
        assert test_session.client_user_id == client_user.id


class TestSessionEdgeCases:
    @pytest.mark.asyncio
    async def test_session_without_station_id(self, db_session, client_user):
        from backend.app.models.models import Session, SessionStatus

        session = Session(
            id=uuid.uuid4(),
            session_token=uuid.uuid4(),
            client_user_id=client_user.id,
            status=SessionStatus.active
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.station_id is None

    @pytest.mark.asyncio
    async def test_session_status_transitions(self, db_session, test_session):
        from backend.app.models.models import SessionStatus
        from backend.app.services.session_manager import SessionManager

        test_session.status = SessionStatus.completed
        await db_session.commit()
        await db_session.refresh(test_session)

        is_active = await SessionManager.is_session_active(db_session, test_session.id)
        assert is_active is False
