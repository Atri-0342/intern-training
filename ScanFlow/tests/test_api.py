import asyncio
from uuid import uuid4
from datetime import date, datetime
from xmlrpc import client
from xmlrpc import client

from sqlalchemy import select
from app.schemas import auth
from app.api import auth
from app.models.models import AnalysisJob, User, Patient, Scan
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.scans import analysis_worker

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

def test_create_patient(clinician_client):
    response = clinician_client.post(
        "/v1/patients",
        json={
            "synthetic_study_id": "11111111-1111-1111-1111-111111111111",
            "dob": "1990-05-15",
            "sex": "male",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["synthetic_study_id"] == "11111111-1111-1111-1111-111111111111"
    assert data["dob"] == "1990-05-15"
    assert data["sex"] == "male"

def test_get_patient(clinician_client, test_database):
    patient_id = "22222222-2222-2222-2222-222222222222"

    with test_database.begin() as connection:
        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_id,
                dob=date(1990, 5, 15),
                sex="male",
            )
        )

    response = clinician_client.get(
        f"/v1/patients/{patient_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["synthetic_study_id"] == patient_id
    assert data["dob"] == "1990-05-15"
    assert data["sex"] == "male"

def test_get_patient_not_found(clinician_client):
    patient_id = "33333333-3333-3333-3333-333333333333"

    response = clinician_client.get(
        f"/v1/patients/{patient_id}"
    )

    assert response.status_code == 404

import pytest


@pytest.mark.parametrize(
    "payload",
    [
        {
            "synthetic_study_id": "not-a-uuid",
            "dob": "1990-05-15",
            "sex": "male",
        },
        {
            "synthetic_study_id": "44444444-4444-4444-4444-444444444444",
            "dob": "not-a-date",
            "sex": "male",
        },
        {
            "synthetic_study_id": "55555555-5555-5555-5555-555555555555",
            "dob": "1990-05-15",
            "sex": "invalid",
        },
    ],
)
def test_create_patient_validation_error(clinician_client, payload):
    response = clinician_client.post(
        "/v1/patients",
        json=payload,
    )

    assert response.status_code == 422


def test_get_patient_without_token():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        response = client.get(
            "/v1/patients/33333333-3333-3333-3333-333333333333"
        )

    assert response.status_code == 401

def test_create_patient_wrong_role(radiologist_client):
    response = radiologist_client.post(
        "/v1/patients",
        json={
            "synthetic_study_id": "66666666-6666-6666-6666-666666666666",
            "dob": "1990-05-15",
            "sex": "male",
        },
    )

    assert response.status_code == 403

def test_update_patient(clinician_client, test_database):
    patient_id = "77777777-7777-7777-7777-777777777777"

    with test_database.begin() as connection:
        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_id,
                dob=date(1990, 5, 15),
                sex="male",
            )
        )

    response = clinician_client.patch(
        f"/v1/patients/{patient_id}",
        json={
            "synthetic_study_id": patient_id,
            "dob": "1995-10-20",
            "sex": "female",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["synthetic_study_id"] == patient_id
    assert data["dob"] == "1995-10-20"
    assert data["sex"] == "female"


def test_list_patients(clinician_client, test_database):
    patient_one = "88888888-8888-8888-8888-888888888888"
    patient_two = "99999999-9999-9999-9999-999999999999"

    with test_database.begin() as connection:
        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_one,
                dob=date(1990, 5, 15),
                sex="male",
            )
        )

        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_two,
                dob=date(1995, 10, 20),
                sex="female",
            )
        )

    response = clinician_client.get("/v1/patients")

    assert response.status_code == 200

    data = response.json()

    patient_ids = {
        patient["synthetic_study_id"]
        for patient in data
    }

    assert patient_one in patient_ids
    assert patient_two in patient_ids

def test_delete_patient(admin_client, test_database):
    patient_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    with test_database.begin() as connection:
        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_id,
                dob=date(1990, 5, 15),
                sex="male",
            )
        )

    response = admin_client.delete(
        f"/v1/patients/{patient_id}"
    )

    assert response.status_code == 204

    response = admin_client.delete(
        f"/v1/patients/{patient_id}"
    )

    assert response.status_code == 404

def test_pagination_limit_enforced(clinician_client):
    response = clinician_client.get(
        "/v1/patients?limit=101"
    )

    assert response.status_code == 422

def test_analysis_job_created(clinician_client, test_database):
    patient_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    scan_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    with test_database.begin() as connection:
        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_id,
                dob=date(1990, 5, 15),
                sex="male",
            )
        )

        connection.execute(
            Scan.__table__.insert().values(
                id=scan_id,
                patient_id=patient_id,
                modality="CT",
                body_part="chest",
                acquired_at=datetime(
                    2026, 1, 1, 10, 0, 0
                ),
                uploaded_at=datetime(
                    2026, 1, 1, 10, 5, 0
                ),
                status="uploaded",
            )
        )

    response = clinician_client.post(
        f"/v1/scans/{scan_id}/analyze"
    )

    assert response.status_code == 202

    data = response.json()

    assert data["job_id"] is not None
    assert data["scan_id"] == scan_id
    assert data["status"] == "uploaded"

def test_patient_create_rolls_back_when_audit_fails(
    create_user,
    db_session,
    db_override,
    monkeypatch,
):
    from fastapi.testclient import TestClient
    from app.main import app

    patient_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"

    token = create_user(
        "audit-failure@test.com",
        "testpassword123",
        "clinician",
    )

    def failing_audit_log(*args, **kwargs):
        raise RuntimeError("TEST: force audit failure")

    monkeypatch.setattr(
        "app.api.patients.write_audit_log",
        failing_audit_log,
    )
    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        client.headers.update(
            {"Authorization": f"Bearer {token}"}
        )

        response = client.post(
            "/v1/patients",
            json={
                "synthetic_study_id": patient_id,
                "dob": "1990-05-15",
                "sex": "male",
            },
        )

    assert response.status_code == 500

    db_session.rollback()

    patient = db_session.get(Patient, patient_id)

    assert patient is None

def patient_payload():
    return {
        "synthetic_study_id": str(uuid4()),
        "dob": "1980-01-01",
        "sex": "female",
    }
from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.models import AnalysisJob, Patient, Scan

def test_analysis_job_happy_path(clinician_client, test_database):
    patient_id = str(uuid4())
    scan_id = str(uuid4())

    with test_database.begin() as connection:
        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_id,
                dob=date(1980, 1, 1),
                sex="female",
            )
        )
        connection.execute(
            Scan.__table__.insert().values(
                id=scan_id,
                patient_id=patient_id,
                modality="CT",
                body_part="chest",
                acquired_at=datetime.now(timezone.utc),
                status="completed",
            )
        )

    response = clinician_client.post(
        f"/v1/scans/{scan_id}/analyze"
    )

    assert response.status_code == 202
    assert response.json()["status"] == "uploaded"

    response = clinician_client.get(
        f"/v1/scans/{scan_id}/analysis"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "uploaded"


def test_analysis_job_failure_status(
    clinician_client,
    test_database,
):
    patient_id = str(uuid4())
    scan_id = str(uuid4())

    with test_database.begin() as connection:
        connection.execute(
            Patient.__table__.insert().values(
                synthetic_study_id=patient_id,
                dob=date(1980, 1, 1),
                sex="female",
            )
        )
        connection.execute(
            Scan.__table__.insert().values(
                id=scan_id,
                patient_id=patient_id,
                modality="MRI",
                body_part="head",
                acquired_at=datetime.now(timezone.utc),
                status="failed",
            )
        )
        connection.execute(
            AnalysisJob.__table__.insert().values(
                id=str(uuid4()),
                scan_id=scan_id,
                status="failed",
                retry_count=3,
                error="inference failed",
            )
        )

    response = clinician_client.get(
        f"/v1/scans/{scan_id}/analysis"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error"] == "inference failed"
    assert response.json()["retry_count"] == 3