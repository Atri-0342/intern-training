import asyncio
import psycopg
import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import (
    DB_PASSWORD,
    DB_USER,
    TEST_DB_NAME,
)

from app.models.models import Base
from app.main import app
from app.db.dependencies import get_db, get_async_db


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
        f"postgresql+psycopg://"
        f"{DB_USER}:{DB_PASSWORD}"
        f"@localhost:5432/{TEST_DB_NAME}"
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


@pytest.fixture(scope="session")
def async_test_engine(test_database):
    engine = create_async_engine(
        f"postgresql+asyncpg://"
        f"{DB_USER}:{DB_PASSWORD}"
        f"@localhost:5432/{TEST_DB_NAME}",
        poolclass=NullPool,
    )

    yield engine

    asyncio.run(engine.dispose())


@pytest.fixture
def db_session(test_database):
    SessionLocalTest = sessionmaker(
        bind=test_database,
        expire_on_commit=False,
    )

    connection = test_database.connect()
    transaction = connection.begin()

    db = SessionLocalTest(
        bind=connection,
    )

    db.join_transaction_mode = "create_savepoint"

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_override(
    db_session,
    async_test_engine,
):
    app.dependency_overrides[get_db] = lambda: db_session

    async_session_factory = async_sessionmaker(
        bind=async_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_async_db():
        async with async_session_factory() as db:
            yield db

    app.dependency_overrides[get_async_db] = override_async_db

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def create_user(db_override):
    with TestClient(app) as client:

        def _create_user(
            email: str,
            password: str,
            role: str,
        ):
            register_response = client.post(
                "/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "role": role,
                },
            )

            assert register_response.status_code == 201

            token_response = client.post(
                "/v1/auth/token",
                json={
                    "email": email,
                    "password": password,
                },
            )

            assert token_response.status_code == 200

            return token_response.json()["access_token"]

        yield _create_user


@pytest.fixture
def clinician_client(
    db_override,
    create_user,
):
    token = create_user(
        email="clinician@test.com",
        password="testpassword123",
        role="clinician",
    )

    client = TestClient(app)

    client.headers.update(
        {
            "Authorization": f"Bearer {token}"
        }
    )

    yield client

    client.close()


@pytest.fixture
def radiologist_client(
    db_override,
    create_user,
):
    token = create_user(
        email="radiologist@test.com",
        password="testpassword123",
        role="radiologist",
    )

    client = TestClient(app)

    client.headers.update(
        {
            "Authorization": f"Bearer {token}"
        }
    )

    yield client

    client.close()


@pytest.fixture
def admin_client(
    db_override,
    create_user,
):
    token = create_user(
        email="admin@test.com",
        password="testpassword123",
        role="admin",
    )

    client = TestClient(app)

    client.headers.update(
        {
            "Authorization": f"Bearer {token}"
        }
    )

    yield client

    client.close()

