from datetime import datetime, timedelta
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.models import Session, SessionStatus


class SessionManager:
    """
    Service class for managing session lifecycle.

    Handles:
    - Session creation and tracking
    - Activity updates (heartbeat)
    - Session expiration (manual and automatic)
    - Timeout configuration

    Attributes:
        SESSION_TIMEOUT_MINUTES: Default timeout in minutes (default: 30)
    """

    SESSION_TIMEOUT_MINUTES: int = 30

    @classmethod
    def set_timeout_minutes(cls, minutes: int):
        """Set the session timeout in minutes."""
        cls.SESSION_TIMEOUT_MINUTES = minutes

    @classmethod
    def get_timeout_minutes(cls) -> int:
        """Get the current session timeout in minutes."""
        return cls.SESSION_TIMEOUT_MINUTES

    @staticmethod
    async def update_activity(db: AsyncSession, session_id: uuid.UUID) -> bool:
        """
        Update session's last activity timestamp.

        This should be called on each user interaction to keep the session alive.

        Args:
            db: Database session
            session_id: UUID of the session to update

        Returns:
            True if update was successful, False otherwise
        """
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session and session.status == SessionStatus.active:
                session.last_activity_at = datetime.utcnow()
                session.ended_at = None
                await db.flush()
                return True
            return False
        except Exception:
            return False

    @staticmethod
    async def is_session_active(db: AsyncSession, session_id: uuid.UUID) -> bool:
        """
        Check if a session is currently active and not expired.

        A session is considered active if:
        - It exists
        - Status is 'active'
        - ended_at is None
        - last_activity_at is within the timeout window

        Args:
            db: Database session
            session_id: UUID of the session to check

        Returns:
            True if session is active, False otherwise
        """
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if not session:
                return False
            if session.status != SessionStatus.active:
                return False
            if session.ended_at:
                return False
            timeout = SessionManager.SESSION_TIMEOUT_MINUTES
            cutoff = datetime.utcnow() - timedelta(minutes=timeout)
            if session.last_activity_at and session.last_activity_at < cutoff:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    async def expire_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
        """
        Manually expire a specific session.

        Args:
            db: Database session
            session_id: UUID of the session to expire

        Returns:
            True if session was expired, False if session not found
        """
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
        """
        Expire all sessions that have exceeded the inactivity timeout.

        Uses last_activity_at to determine if a session should be expired,
        not started_at. This allows sessions to be extended indefinitely
        as long as they remain active.

        Args:
            db: Database session

        Returns:
            Number of sessions that were expired
        """
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
                if session.last_activity_at and session.last_activity_at < cutoff:
                    session.status = SessionStatus.abandoned
                    session.ended_at = datetime.utcnow()
                    expired_count += 1
            if expired_count > 0:
                await db.flush()
            return expired_count
        except Exception:
            return 0

    @staticmethod
    async def extend_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
        """
        Extend an active session's timeout by resetting ended_at.

        This is used for "keep me logged in" functionality.
        Note: last_activity_at is NOT updated here - use update_activity()
        for that purpose.

        Args:
            db: Database session
            session_id: UUID of the session to extend

        Returns:
            True if extension was successful, False if session not found or inactive
        """
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session and session.status == SessionStatus.active:
                session.ended_at = None
                await db.flush()
                return True
            return False
        except Exception:
            return False

    @staticmethod
    async def get_session_info(db: AsyncSession, session_id: uuid.UUID) -> Optional[dict]:
        """
        Get detailed information about a session.

        Args:
            db: Database session
            session_id: UUID of the session

        Returns:
            Dict with session info or None if not found
        """
        try:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if not session:
                return None
            return {
                "id": session.id,
                "status": session.status,
                "started_at": session.started_at,
                "last_activity_at": session.last_activity_at,
                "ended_at": session.ended_at,
                "is_active": await SessionManager.is_session_active(db, session_id)
            }
        except Exception:
            return None
