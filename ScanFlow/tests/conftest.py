import psycopg
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import (DB_PASSWORD,DB_USER,TEST_DB_NAME,)

from app.models.models import Base
import psycopg
import pytest

@pytest.fixture(scope="session")
def test_database():
    with psycopg.connect(
        host="localhost",
        port=5432,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname="postgres",
        autocommit=True,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
            cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")

    test_engine = create_engine(
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@localhost:5432/{TEST_DB_NAME}"
    )
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()

    with psycopg.connect(
        host="localhost",
        port=5432,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname="postgres",
        autocommit=True,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")

@pytest.fixture
def db_session(test_database):
    SessionLocalTest = sessionmaker(
        bind=test_database,
        expire_on_commit=False,
    )
    db = SessionLocalTest()
    connection = test_database.connect()
    transaction = connection.begin()
    db.bind = connection
    db.join_transaction_mode = "create_savepoint"
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()

from fastapi.testclient import TestClient
from app.main import app
from app.db.dependencies import get_db

@pytest.fixture
def db_override(db_session):
    app.dependency_overrides[get_db] = lambda: db_session

    yield

    app.dependency_overrides.clear()

from app.schemas.auth import RegisterRequest, TokenRequest

@pytest.fixture
def create_user(db_override):
    with TestClient(app) as client:

        def _create_user(email: str, password: str, role: str):
            client.post(
                "/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "role": role,
                },
            )

            response = client.post(
                "/v1/auth/token",
                json={
                    "email": email,
                    "password": password,
                },
            )

            return response.json()["access_token"]

        yield _create_user

@pytest.fixture
def clinician_client(db_override, create_user):
    token = create_user(
        email="clinician@test.com",
        password="testpassword123",
        role="clinician",
    )

    client = TestClient(app)

    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    yield client

    client.close()

@pytest.fixture
def radiologist_client(db_override, create_user):
    token = create_user(
        email="radiologist@test.com",
        password="testpassword123",
        role="radiologist",
    )

    client = TestClient(app)

    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    yield client

    client.close()

@pytest.fixture
def admin_client(db_override, create_user):
    token = create_user(
        email="admin@test.com",
        password="testpassword123",
        role="admin",
    )

    client = TestClient(app)

    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    yield client

    client.close()

