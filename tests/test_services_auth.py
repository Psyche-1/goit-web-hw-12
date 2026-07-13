from datetime import timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from src.conf.config import settings
from src.database.models import User
from src.services.auth import (
    HashService,
    TokenService,
    get_current_user,
)


class TestHashService:
    def test_hash_is_not_plaintext(self):
        hashed = HashService.get_password_hash("my-password")
        assert hashed != "my-password"
        assert isinstance(hashed, str)

    def test_verify_correct_password(self):
        hashed = HashService.get_password_hash("correct horse")
        assert HashService.verify_password("correct horse", hashed) is True

    def test_verify_wrong_password(self):
        hashed = HashService.get_password_hash("correct horse")
        assert HashService.verify_password("battery staple", hashed) is False

    def test_hash_is_salted_unique(self):
        assert HashService.get_password_hash("same") != HashService.get_password_hash(
            "same"
        )


class TestTokenService:
    def test_access_token_payload(self):
        token = TokenService.create_token({"sub": "a@b.com"})
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        assert payload["sub"] == "a@b.com"
        assert payload["scope"] == "access_token"
        assert "exp" in payload

    def test_refresh_token_scope(self):
        token = TokenService.create_token({"sub": "a@b.com"}, is_refresh=True)
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        assert payload["scope"] == "refresh_token"

    def test_custom_expires_delta(self):
        short = TokenService.create_token(
            {"sub": "a@b.com"}, expires_delta=timedelta(minutes=1)
        )
        long = TokenService.create_token(
            {"sub": "a@b.com"}, expires_delta=timedelta(days=30)
        )
        exp_short = jwt.decode(
            short, settings.secret_key, algorithms=[settings.algorithm]
        )["exp"]
        exp_long = jwt.decode(
            long, settings.secret_key, algorithms=[settings.algorithm]
        )["exp"]
        assert exp_long > exp_short

    def test_original_data_not_mutated(self):
        data = {"sub": "a@b.com"}
        TokenService.create_token(data)
        assert data == {"sub": "a@b.com"}


@pytest.mark.asyncio
class TestGetCurrentUser:
    async def test_valid_token_returns_user(self, db_session):
        user = User(email="cur@example.com", password="x")
        db_session.add(user)
        db_session.commit()
        token = TokenService.create_token({"sub": "cur@example.com"})
        result = await get_current_user(token=token, db=db_session)
        assert result.email == "cur@example.com"

    async def test_invalid_token_raises(self, db_session):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token="not-a-jwt", db=db_session)
        assert exc.value.status_code == 401

    async def test_refresh_scope_rejected(self, db_session):
        user = User(email="cur@example.com", password="x")
        db_session.add(user)
        db_session.commit()
        token = TokenService.create_token({"sub": "cur@example.com"}, is_refresh=True)
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token=token, db=db_session)
        assert exc.value.status_code == 401

    async def test_missing_sub_rejected(self, db_session):
        token = TokenService.create_token({"foo": "bar"})
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token=token, db=db_session)
        assert exc.value.status_code == 401

    async def test_unknown_user_rejected(self, db_session):
        token = TokenService.create_token({"sub": "ghost@example.com"})
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token=token, db=db_session)
        assert exc.value.status_code == 401
