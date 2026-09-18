from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from db.dependencies import get_db
from models.models import Patient
from schemas.patient import PatientCreate, PatientResponse
from .dependencies import pagination_params

router = APIRouter(prefix="/v1/patients", tags=["patients"])

@router.post("", response_model=PatientResponse, status_code=201)
def create_patient(patient: PatientCreate,db: Session=Depends(get_db)) -> PatientResponse:
    exists=db.get(Patient,str(patient.synthetic_study_id))
    if exists is not None:
        raise HTTPException(status_code=409,detail="Patient already exists",)
    db_patient = Patient(
        synthetic_study_id=str(patient.synthetic_study_id),
        dob=patient.dob,
        sex=patient.sex,
    )

    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    return PatientResponse(
        synthetic_study_id=db_patient.synthetic_study_id,
        dob=db_patient.dob,
        sex=db_patient.sex,
    )

@router.get("/{synthetic_study_id}", response_model=PatientResponse)
def get_patient(synthetic_study_id: UUID,db: Session = Depends(get_db)) -> PatientResponse:
    patient = db.get(Patient,str(synthetic_study_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return PatientResponse(
        synthetic_study_id=patient.synthetic_study_id,
        dob=patient.dob,
        sex=patient.sex,
    )

@router.get("", response_model=list[PatientResponse])
def list_patients(
    pagination: dict[str, int] = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[PatientResponse]:
    limit = pagination["limit"]
    offset = pagination["offset"]

    patients = (
        db.query(Patient)
        .offset(offset)
        .limit(limit)
        .all()
    )

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

    db.delete(db_patient)
    db.commit()