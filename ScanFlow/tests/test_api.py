from uuid import uuid4

from app.models.models import User


def test_test_database_exists(test_database):
    with test_database.connect() as connection:
        result = connection.exec_driver_sql("SELECT 1")
        assert result.scalar() == 1


def test_transaction_is_rolled_back(db_session):
    user = User(
        id=str(uuid4()),
        email="rollback@test.com",
        hashed_password="test",
        role="clinician",
    )

    db_session.add(user)
    db_session.flush()

    saved_user = (
        db_session.query(User)
        .filter(User.email == "rollback@test.com")
        .first()
    )

    assert saved_user is not None


def test_transaction_starts_clean(db_session):
    user = (
        db_session.query(User)
        .filter(User.email == "rollback@test.com")
        .first()
    )

    assert user is None

def test_clinician_client(clinician_client):
    response = clinician_client.get("/v1/auth/me")

    assert response.status_code == 200

    data = response.json()

    assert data["role"] == "clinician"

def test_radiologist_client(radiologist_client):
    response = radiologist_client.get("/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["role"] == "radiologist"

def test_admin_client(admin_client):
    response = admin_client.get("/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"

