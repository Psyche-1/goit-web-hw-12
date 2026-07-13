from datetime import date

import pytest
from pydantic import ValidationError

from src.schemas import (
    ContactCreate,
    ContactResponse,
    Token,
    UserCreate,
    UserResponse,
)


class TestUserSchemas:
    def test_valid_user_create(self):
        user = UserCreate(email="user@example.com", password="secret1")
        assert user.email == "user@example.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="secret1")

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", password="123")

    def test_user_response_from_attributes(self):
        class Obj:
            id = 5
            email = "u@example.com"

        resp = UserResponse.model_validate(Obj())
        assert resp.id == 5
        assert resp.email == "u@example.com"


class TestTokenSchema:
    def test_default_token_type(self):
        token = Token(access_token="a", refresh_token="b")
        assert token.token_type == "bearer"


class TestContactSchemas:
    def test_valid_contact_create(self):
        contact = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="+123456789",
            birthday=date(1990, 1, 1),
        )
        assert contact.additional_data is None

    def test_invalid_contact_email(self):
        with pytest.raises(ValidationError):
            ContactCreate(
                first_name="John",
                last_name="Doe",
                email="bad",
                phone_number="+123",
                birthday=date(1990, 1, 1),
            )

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            ContactCreate(
                first_name="John",
                email="john@example.com",
                phone_number="+123",
                birthday=date(1990, 1, 1),
            )

    def test_contact_response_from_attributes(self):
        class Obj:
            id = 1
            user_id = 2
            first_name = "John"
            last_name = "Doe"
            email = "john@example.com"
            phone_number = "+123"
            birthday = date(1990, 1, 1)
            additional_data = None

        resp = ContactResponse.model_validate(Obj())
        assert resp.id == 1
        assert resp.user_id == 2
