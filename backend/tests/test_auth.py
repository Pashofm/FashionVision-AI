import pytest
from backend.app.services.auth import (
    verify_password, hash_password, create_access_token,
    decode_access_token, create_refresh_token, decode_refresh_token
)


class TestPasswordHashing:
    def test_hash_password_creates_hash(self):
        password = "testpassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_invalid_hash(self):
        assert verify_password("password", "invalid_hash") is False


class TestJWTTokens:
    def test_create_access_token(self):
        data = {"sub": "user-123", "role": "admin"}
        token = create_access_token(data)
        assert token is not None
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        data = {"sub": "user-123", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["role"] == "admin"

    def test_decode_access_token_invalid(self):
        decoded = decode_access_token("invalid_token")
        assert decoded is None

    def test_access_token_expiration(self):
        from datetime import timedelta
        data = {"sub": "user-123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        decoded = decode_access_token(token)
        assert decoded is None

    def test_create_refresh_token(self):
        user_id = "user-123"
        token = create_refresh_token(user_id)
        assert token is not None

    def test_decode_refresh_token_valid(self):
        user_id = "user-123"
        token = create_refresh_token(user_id)
        decoded = decode_refresh_token(token)
        assert decoded is not None
        assert decoded["sub"] == user_id
        assert decoded["type"] == "refresh"

    def test_decode_refresh_token_wrong_type(self):
        access_token = create_access_token({"sub": "user-123"})
        decoded = decode_refresh_token(access_token)
        assert decoded is None