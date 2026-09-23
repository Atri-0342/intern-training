from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import pagination_params, require_role
from app.db.audit import write_audit_log
from app.db.dependencies import get_db, get_async_db
from app.models.models import Patient
from app.schemas.patient import PatientCreate, PatientResponse


router = APIRouter(
    prefix="/v1/patients",
    tags=["patients"],
)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=201,
)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("clinician")),
) -> PatientResponse:

    exists = db.get(
        Patient,
        str(patient.synthetic_study_id),
    )

    if exists is not None:
        raise HTTPException(
            status_code=409,
            detail="Patient already exists",
        )

    db_patient = Patient(
        synthetic_study_id=str(patient.synthetic_study_id),
        dob=patient.dob,
        sex=patient.sex,
    )

    db.add(db_patient)

    write_audit_log(
        db=db,
        action="CREATE",
        entity="patient",
        entity_id=str(patient.synthetic_study_id),
        actor_id=current_user["user_id"],
    )

    db.commit()
    db.refresh(db_patient)

    return PatientResponse(
        synthetic_study_id=db_patient.synthetic_study_id,
        dob=db_patient.dob,
        sex=db_patient.sex,
    )


@router.get(
    "/{synthetic_study_id}",
    response_model=PatientResponse,
)
async def get_patient(
    synthetic_study_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    # current_user: dict = Depends(require_role("clinician", "radiologist")),
) -> PatientResponse:

    patient = await db.get(
        Patient,
        str(synthetic_study_id),
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    return PatientResponse(
        synthetic_study_id=patient.synthetic_study_id,
        dob=patient.dob,
        sex=patient.sex,
    )


@router.get(
    "",
    response_model=list[PatientResponse],
)
async def list_patients(
    pagination: dict[str, int] = Depends(pagination_params),
    db: AsyncSession = Depends(get_async_db),
    # current_user: dict = Depends(require_role("clinician", "radiologist")),
) -> list[PatientResponse]:

    limit = pagination["limit"]
    offset = pagination["offset"]

    result = await db.execute(
        select(Patient)
        .offset(offset)
        .limit(limit)
    )

    patients = result.scalars().all()

    return [
        PatientResponse(
            synthetic_study_id=patient.synthetic_study_id,
            dob=patient.dob,
            sex=patient.sex,
        )
        for patient in patients
    ]


@router.patch(
    "/{synthetic_study_id}",
    response_model=PatientResponse,
)
def update_patient(
    synthetic_study_id: UUID,
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("clinician")),
) -> PatientResponse:

    db_patient = db.get(
        Patient,
        str(synthetic_study_id),
    )

    if db_patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    db_patient.dob = patient.dob
    db_patient.sex = patient.sex

    write_audit_log(
        db=db,
        action="UPDATE",
        entity="patient",
        entity_id=str(synthetic_study_id),
        actor_id=current_user["user_id"],
    )

    db.commit()
    db.refresh(db_patient)

    return PatientResponse(
        synthetic_study_id=db_patient.synthetic_study_id,
        dob=db_patient.dob,
        sex=db_patient.sex,
    )


@router.delete(
    "/{synthetic_study_id}",
    status_code=204,
)
def delete_patient(
    synthetic_study_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
) -> None:

    db_patient = db.get(
        Patient,
        str(synthetic_study_id),
    )

    if db_patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    write_audit_log(
        db=db,
        action="DELETE",
        entity="patient",
        entity_id=str(synthetic_study_id),
        actor_id=current_user["user_id"],
    )

    db.delete(db_patient)
    db.commit()