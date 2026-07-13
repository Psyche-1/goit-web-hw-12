from datetime import date, datetime, timedelta

from src.database.models import Contact, User


def make_payload(**overrides):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone_number": "+123456789",
        "birthday": "1990-01-01",
        "additional_data": None,
    }
    payload.update(overrides)
    return payload


class TestCreateContact:
    def test_create_contact(self, auth_client, test_user):
        resp = auth_client.post("/api/contacts/", json=make_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["first_name"] == "John"
        assert data["user_id"] == test_user.id

    def test_create_requires_auth(self, client):
        resp = client.post("/api/contacts/", json=make_payload())
        assert resp.status_code == 401


class TestReadContacts:
    def test_list_empty(self, auth_client):
        resp = auth_client.get("/api/contacts/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_only_own_contacts(self, auth_client, db_session, test_user):
        other = User(email="other@example.com", password="x")
        db_session.add(other)
        db_session.commit()
        db_session.add(
            Contact(
                first_name="Mine",
                last_name="A",
                email="mine@example.com",
                phone_number="1",
                birthday=date(1990, 1, 1),
                user_id=test_user.id,
            )
        )
        db_session.add(
            Contact(
                first_name="Theirs",
                last_name="B",
                email="theirs@example.com",
                phone_number="2",
                birthday=date(1990, 1, 1),
                user_id=other.id,
            )
        )
        db_session.commit()

        resp = auth_client.get("/api/contacts/")
        names = [c["first_name"] for c in resp.json()]
        assert names == ["Mine"]

    def test_search_filters(self, auth_client, db_session, test_user):
        for fn, ln, em in [
            ("Alice", "Smith", "alice@example.com"),
            ("Bob", "Jones", "bob@example.com"),
        ]:
            db_session.add(
                Contact(
                    first_name=fn,
                    last_name=ln,
                    email=em,
                    phone_number="1",
                    birthday=date(1990, 1, 1),
                    user_id=test_user.id,
                )
            )
        db_session.commit()

        resp = auth_client.get("/api/contacts/", params={"search": "alice"})
        results = resp.json()
        assert len(results) == 1
        assert results[0]["first_name"] == "Alice"


class TestReadSingleContact:
    def test_get_existing(self, auth_client, db_session, test_user):
        contact = Contact(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="1",
            birthday=date(1990, 1, 1),
            user_id=test_user.id,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        resp = auth_client.get(f"/api/contacts/{contact.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == contact.id

    def test_get_missing_returns_404(self, auth_client):
        resp = auth_client.get("/api/contacts/9999")
        assert resp.status_code == 404

    def test_cannot_read_others_contact(self, auth_client, db_session):
        other = User(email="other@example.com", password="x")
        db_session.add(other)
        db_session.commit()
        contact = Contact(
            first_name="Secret",
            last_name="X",
            email="secret@example.com",
            phone_number="1",
            birthday=date(1990, 1, 1),
            user_id=other.id,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        resp = auth_client.get(f"/api/contacts/{contact.id}")
        assert resp.status_code == 404


class TestUpdateContact:
    def test_update_existing(self, auth_client, db_session, test_user):
        contact = Contact(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="1",
            birthday=date(1990, 1, 1),
            user_id=test_user.id,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        resp = auth_client.put(
            f"/api/contacts/{contact.id}",
            json=make_payload(first_name="Johnny"),
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Johnny"

    def test_update_missing_404(self, auth_client):
        resp = auth_client.put("/api/contacts/9999", json=make_payload())
        assert resp.status_code == 404


class TestDeleteContact:
    def test_delete_existing(self, auth_client, db_session, test_user):
        contact = Contact(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="1",
            birthday=date(1990, 1, 1),
            user_id=test_user.id,
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        resp = auth_client.delete(f"/api/contacts/{contact.id}")
        assert resp.status_code == 204
        assert db_session.query(Contact).filter(Contact.id == contact.id).first() is None

    def test_delete_missing_404(self, auth_client):
        resp = auth_client.delete("/api/contacts/9999")
        assert resp.status_code == 404


class TestUpcomingBirthdays:
    def test_returns_contacts_within_7_days(self, auth_client, db_session, test_user):
        soon = datetime.now().date() + timedelta(days=3)
        far = datetime.now().date() + timedelta(days=200)
        db_session.add(
            Contact(
                first_name="Soon",
                last_name="A",
                email="soon@example.com",
                phone_number="1",
                birthday=date(1990, soon.month, soon.day),
                user_id=test_user.id,
            )
        )
        db_session.add(
            Contact(
                first_name="Far",
                last_name="B",
                email="far@example.com",
                phone_number="2",
                birthday=date(1990, far.month, far.day),
                user_id=test_user.id,
            )
        )
        db_session.commit()

        resp = auth_client.get("/api/contacts/birthdays")
        assert resp.status_code == 200
        names = [c["first_name"] for c in resp.json()]
        assert "Soon" in names
        assert "Far" not in names
