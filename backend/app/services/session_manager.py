from datetime import datetime, timedelta
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.models import Session, SessionStatus


class SessionManager:
    SESSION_TIMEOUT_MINUTES: int = 30

    @classmethod
    def set_timeout_minutes(cls, minutes: int):
        cls.SESSION_TIMEOUT_MINUTES = minutes

    @classmethod
    def get_timeout_minutes(cls) -> int:
        return cls.SESSION_TIMEOUT_MINUTES

    @staticmethod
    async def update_activity(db: AsyncSession, session_id: uuid.UUID) -> bool:
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.ended_at = None
                await db.flush()
                return True
            return False
        except Exception:
            return False

    @staticmethod
    async def is_session_active(db: AsyncSession, session_id: uuid.UUID) -> bool:
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if not session:
                return False
            if session.status != SessionStatus.active:
                return False
            timeout = SessionManager.SESSION_TIMEOUT_MINUTES
            if session.ended_at:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    async def expire_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = SessionStatus.abandoned
                session.ended_at = datetime.utcnow()
                await db.flush()
                return True
            return False
        except Exception:
            return False

    @staticmethod
    async def expire_inactive_sessions(db: AsyncSession) -> int:
        try:
            timeout = SessionManager.SESSION_TIMEOUT_MINUTES
            cutoff = datetime.utcnow() - timedelta(minutes=timeout)
            result = await db.execute(
                select(Session).where(
                    Session.status == SessionStatus.active,
                    Session.ended_at == None
                )
            )
            sessions = result.scalars().all()
            expired_count = 0
            for session in sessions:
                if session.started_at and session.started_at < cutoff:
                    session.status = SessionStatus.abandoned
                    session.ended_at = datetime.utcnow()
                    expired_count += 1
            await db.flush()
            return expired_count
        except Exception:
            return 0

    @staticmethod
    async def extend_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session and session.status == SessionStatus.active:
                session.started_at = datetime.utcnow()
                session.ended_at = None
                await db.flush()
                return True
            return False
        except Exception:
            return False