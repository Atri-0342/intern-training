from io import BytesIO
from uuid import UUID, uuid4
from pathlib import Path
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.db.session import AsyncSessionLocal
from app.services.storage import delete_file, upload_file

import asyncio

from app.api.dependencies import pagination_params, require_role
from app.db.audit import write_audit_log
from app.db.dependencies import get_async_db, get_db
from app.models.models import AnalysisJob, Scan
from app.schemas.scan import ScanCreate, ScanResponse


UPLOAD_DIR = Path("/code/uploads/scans")
MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}


router = APIRouter(
    prefix="/v1/scans",
    tags=["scans"],
)


@router.post(
    "/upload",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_scan(
    patient_id: UUID = Form(...),
    modality: str = Form(...),
    body_part: str = Form(...),
    acquired_at: datetime = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician")
    ),
) -> ScanResponse:

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, and PNG files are allowed",
        )

    scan_id = uuid4()

    extension = ALLOWED_CONTENT_TYPES[file.content_type]

    file_key = f"scans/{scan_id}{extension}"

    file_content = file.file.read()

    total_size = len(file_content)

    if total_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must be 20 MB or less",
        )

    upload_file(
        file_object=BytesIO(file_content),
        file_key=file_key,
        content_type=file.content_type,
    )

    uploaded_at = datetime.now(timezone.utc)

    db_scan = Scan(
        id=str(scan_id),
        patient_id=str(patient_id),
        modality=modality,
        body_part=body_part,
        file_key=file_key,
        acquired_at=acquired_at,
        uploaded_at=uploaded_at,
        status="uploaded",
    )

    db.add(db_scan)

    write_audit_log(
        db=db,
        action="CREATE",
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
        file_key=db_scan.file_key,
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
        file_key=scan.file_key,
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
            file_key=scan.file_key,
        )
        for scan in scans
    ]


@router.patch(
    "/{scan_id}",
    response_model=ScanResponse,
)
def update_scan(
    scan_id: UUID,
    patient_id: UUID = Form(...),
    modality: str = Form(...),
    body_part: str = Form(...),
    acquired_at: datetime = Form(...),
    status_value: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician")
    ),
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

    if modality not in {
        "CT",
        "MRI",
        "X-ray",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid modality",
        )

    if status_value not in {
        "uploaded",
        "processing",
        "completed",
        "failed",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid scan status",
        )

    db_scan.patient_id = str(patient_id)
    db_scan.modality = modality
    db_scan.body_part = body_part
    db_scan.acquired_at = acquired_at
    db_scan.status = status_value

    if file is not None:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, JPG, and PNG files are allowed",
            )

        extension = ALLOWED_CONTENT_TYPES[
            file.content_type
        ]

        new_file_key = (
            f"scans/{scan_id}{extension}"
        )

        file_content = file.file.read()

        total_size = len(file_content)

        if total_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size must be 20 MB or less",
            )

        old_file_key = db_scan.file_key

        upload_file(
            file_object=BytesIO(file_content),
            file_key=new_file_key,
            content_type=file.content_type,
        )

        db_scan.file_key = new_file_key

        if (
            old_file_key
            and old_file_key != new_file_key
        ):
            delete_file(old_file_key)

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
        file_key=db_scan.file_key,
    )

@router.delete(
    "/{scan_id}",
    status_code=204,
)
def delete_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("admin")
    ),
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

    if db_scan.file_key:
        delete_file(db_scan.file_key)

    write_audit_log(
        db=db,
        action="DELETE",
        entity="scan",
        entity_id=str(scan_id),
        actor_id=current_user["user_id"],
    )

    db.delete(db_scan)
    db.commit()