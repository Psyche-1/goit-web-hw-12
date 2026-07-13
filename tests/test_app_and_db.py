from src.conf.config import settings
from src.database.db import get_db


class TestRoot:
    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "message" in resp.json()


class TestSettings:
    def test_settings_loaded(self):
        assert settings.algorithm == "HS256"
        assert settings.database_url
        assert settings.secret_key


class TestGetDb:
    def test_get_db_yields_and_closes(self):
        gen = get_db()
        session = next(gen)
        assert session is not None
        gen.close()
