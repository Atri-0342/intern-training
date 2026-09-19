from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import pagination_params, require_role
from app.db.audit import write_audit_log
from app.db.dependencies import get_db
from app.models.models import Scan
from app.schemas.scan import ScanCreate, ScanResponse


router = APIRouter(
    prefix="/v1/scans",
    tags=["scans"],
)


@router.post(
    "",
    response_model=ScanResponse,
    status_code=201,
)
def create_scan(
    scan: ScanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("clinician")),
) -> ScanResponse:
    exists = db.get(
        Scan,
        str(scan.id),
    )

    if exists is not None:
        raise HTTPException(
            status_code=409,
            detail="Scan already exists",
        )

    db_scan = Scan(
        id=str(scan.id),
        patient_id=str(scan.patient_id),
        modality=scan.modality,
        body_part=scan.body_part,
        acquired_at=scan.acquired_at,
        uploaded_at=scan.uploaded_at,
        status=scan.status,
    )

    db.add(db_scan)

    write_audit_log(
        db=db,
        action="CREATE",
        entity="scan",
        entity_id=str(scan.id),
        actor_id=current_user["user_id"],
    )

    db.commit()
    db.refresh(db_scan)

    return ScanResponse(
        id=db_scan.id,
        patient_id=db_scan.patient_id,
        modality=db_scan.modality,
        body_part=db_scan.body_part,
        acquired_at=db_scan.acquired_at,
        uploaded_at=db_scan.uploaded_at,
        status=db_scan.status,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
)
def get_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician", "radiologist")
    ),
) -> ScanResponse:
    scan = db.get(
        Scan,
        str(scan_id),
    )

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    return ScanResponse(
        id=scan.id,
        patient_id=scan.patient_id,
        modality=scan.modality,
        body_part=scan.body_part,
        acquired_at=scan.acquired_at,
        uploaded_at=scan.uploaded_at,
        status=scan.status,
    )


@router.get(
    "",
    response_model=list[ScanResponse],
)
def list_scans(
    modality: str | None = None,
    status: str | None = None,
    acquired_at_from: datetime | None = None,
    acquired_at_to: datetime | None = None,
    pagination: dict[str, int] = Depends(pagination_params),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician", "radiologist")
    ),
) -> list[ScanResponse]:

    limit = pagination["limit"]
    offset = pagination["offset"]

    query = db.query(Scan)

    if modality is not None:
        query = query.filter(
            Scan.modality == modality
        )

    if status is not None:
        query = query.filter(
            Scan.status == status
        )

    if acquired_at_from is not None:
        query = query.filter(
            Scan.acquired_at >= acquired_at_from
        )

    if acquired_at_to is not None:
        query = query.filter(
            Scan.acquired_at <= acquired_at_to
        )

    scans = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        ScanResponse(
            id=scan.id,
            patient_id=scan.patient_id,
            modality=scan.modality,
            body_part=scan.body_part,
            acquired_at=scan.acquired_at,
            uploaded_at=scan.uploaded_at,
            status=scan.status,
        )
        for scan in scans
    ]


@router.patch(
    "/{scan_id}",
    response_model=ScanResponse,
)
def update_scan(
    scan_id: UUID,
    scan: ScanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("clinician")),
) -> ScanResponse:

    db_scan = db.get(
        Scan,
        str(scan_id),
    )

    if db_scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    db_scan.patient_id = str(scan.patient_id)
    db_scan.modality = scan.modality
    db_scan.body_part = scan.body_part
    db_scan.acquired_at = scan.acquired_at
    db_scan.uploaded_at = scan.uploaded_at
    db_scan.status = scan.status

    write_audit_log(
        db=db,
        action="UPDATE",
        entity="scan",
        entity_id=str(scan_id),
        actor_id=current_user["user_id"],
    )

    db.commit()
    db.refresh(db_scan)

    return ScanResponse(
        id=db_scan.id,
        patient_id=db_scan.patient_id,
        modality=db_scan.modality,
        body_part=db_scan.body_part,
        acquired_at=db_scan.acquired_at,
        uploaded_at=db_scan.uploaded_at,
        status=db_scan.status,
    )


@router.delete(
    "/{scan_id}",
    status_code=204,
)
def delete_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
) -> None:

    db_scan = db.get(
        Scan,
        str(scan_id),
    )

    if db_scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    write_audit_log(
        db=db,
        action="DELETE",
        entity="scan",
        entity_id=str(scan_id),
        actor_id=current_user["user_id"],
    )

    db.delete(db_scan)
    db.commit()