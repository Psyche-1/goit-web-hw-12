from src.database.models import User
from src.services.auth import HashService


class TestSignup:
    def test_signup_creates_user(self, client, db_session):
        resp = client.post(
            "/api/auth/signup",
            json={"email": "new@example.com", "password": "secret123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "password" not in data

        user = db_session.query(User).filter(User.email == "new@example.com").first()
        assert user is not None
        assert user.password != "secret123"

    def test_signup_duplicate_email_conflict(self, client, test_user):
        resp = client.post(
            "/api/auth/signup",
            json={"email": test_user.email, "password": "secret123"},
        )
        assert resp.status_code == 409

    def test_signup_invalid_email(self, client):
        resp = client.post(
            "/api/auth/signup",
            json={"email": "bad", "password": "secret123"},
        )
        assert resp.status_code == 422


class TestLogin:
    def test_login_success_returns_tokens(self, client, db_session, test_user):
        resp = client.post(
            "/api/auth/login",
            data={"username": test_user.email, "password": "secret123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert data["access_token"]
        assert data["refresh_token"]

        db_session.refresh(test_user)
        assert test_user.refresh_token == data["refresh_token"]

    def test_login_wrong_password(self, client, test_user):
        resp = client.post(
            "/api/auth/login",
            data={"username": test_user.email, "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post(
            "/api/auth/login",
            data={"username": "ghost@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401

    def test_login_then_access_protected_route(self, client, test_user):
        login = client.post(
            "/api/auth/login",
            data={"username": test_user.email, "password": "secret123"},
        )
        token = login.json()["access_token"]
        resp = client.get(
            "/api/contacts/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []
