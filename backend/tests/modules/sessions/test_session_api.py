"""
Session API Tests

Tests for session-related API endpoints:
- POST /api/sessions - Create session
- GET /api/sessions - List sessions
"""
import pytest
import uuid

from backend.app.models.models import Session, SessionStatus
from backend.app.services.session_manager import SessionManager
from tests.factories import SessionFactory, UserFactory


pytestmark = pytest.mark.asyncio


class TestSessionAPI:
    """Tests for session API endpoints."""

    async def test_create_session(self, client, client_user):
        """Test creating session via API."""
        response = await client.post("/api/sessions", json={
            "client_user_id": str(client_user.id),
            "station_id": "Kiosk-01"
        })

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["station_id"] == "Kiosk-01"

    async def test_create_session_without_user(self, client):
        """Test creating anonymous session."""
        response = await client.post("/api/sessions", json={
            "station_id": "Kiosk-02"
        })

        assert response.status_code == 201

    async def test_get_sessions(self, client):
        """Test listing sessions."""
        response = await client.get("/api/sessions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_sessions_empty(self, client):
        """Test listing sessions when empty."""
        response = await client.get("/api/sessions")

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSessionAuthAPI:
    """Tests for authenticated session endpoints."""

    async def test_session_extend_authenticated(self, authenticated_client, test_session):
        """Test extending session when authenticated."""
        response = await authenticated_client.get("/api/auth/session/extend")

        assert response.status_code == 200

    async def test_session_status_authenticated(self, authenticated_client):
        """Test getting session status when authenticated."""
        response = await authenticated_client.get("/api/auth/session/status")

        assert response.status_code == 200

    async def test_session_status_unauthenticated(self, client):
        """Test getting session status without auth."""
        response = await client.get("/api/auth/session/status")

        assert response.status_code == 403
