from io import BytesIO
from uuid import UUID, uuid4
from pathlib import Path
from datetime import datetime, timezone

# UPDATED: IDEMPOTENCY — imports for hashing and JSON response replay
import hashlib
import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,  # UPDATED: IDEMPOTENCY
    HTTPException,
    Request,
    UploadFile,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import func, select, text

# UPDATED: IDEMPOTENCY — transaction conflict handling
from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionLocal
from app.services.storage import delete_file, upload_file

import asyncio
from app.api.rate_limit import enforce_user_rate_limit
from app.api.dependencies import pagination_params, require_role
from app.db.audit import write_audit_log
from app.db.dependencies import get_async_db, get_db

# UPDATED: IDEMPOTENCY — import the new model
from app.models.models import (
    AnalysisJob,
    Report,
    Scan,
    IdempotencyRecord,
)
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
    dependencies=[Depends(enforce_user_rate_limit)],
)


# UPDATED: IDEMPOTENCY — endpoint accepts Idempotency-Key.
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

    # UPDATED: IDEMPOTENCY — clients send a unique key for each logical upload.
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),

    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("clinician")),
) -> ScanResponse:

    # UPDATED: IDEMPOTENCY — normalize and validate the key.
    idempotency_key = idempotency_key.strip()
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not be empty",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, JPG, and PNG files are allowed",
        )

    # Read the file once so its bytes can be hashed and uploaded.
    file_content = file.file.read()
    total_size = len(file_content)

    if total_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must be 20 MB or less",
        )

    # UPDATED: IDEMPOTENCY — fingerprint the metadata and file content.
    # Repeating the same key with different content is rejected.
    request_fingerprint = {
        "patient_id": str(patient_id),
        "modality": modality,
        "body_part": body_part,
        "acquired_at": acquired_at.isoformat(),
        "content_type": file.content_type,
        "file_sha256": hashlib.sha256(file_content).hexdigest(),
    }

    request_hash = hashlib.sha256(
        json.dumps(
            request_fingerprint,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    user_id = str(current_user["user_id"])

    # UPDATED: IDEMPOTENCY — scope each key to its authenticated user.
    existing_record = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.key == idempotency_key,
        )
        .first()
    )

    if existing_record is not None:
        # UPDATED: IDEMPOTENCY — the same key cannot represent a new request.
        if existing_record.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This Idempotency-Key was already used "
                    "with a different request"
                ),
            )

        # UPDATED: IDEMPOTENCY — replay the stored successful response.
        if (
            existing_record.response_body is not None
            and existing_record.response_status is not None
        ):
            return ScanResponse.model_validate_json(
                existing_record.response_body
            )

        # A record without a saved response is not replayable.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is still being processed",
        )

    # UPDATED: IDEMPOTENCY — create a record for the new request.
    # The unique constraint on (user_id, key) protects key ownership.
    idempotency_record = IdempotencyRecord(
        id=str(uuid4()),
        user_id=user_id,
        key=idempotency_key,
        request_hash=request_hash,
        response_body=None,
        response_status=None,
    )

    db.add(idempotency_record)

    try:
        # Persist the reservation before uploading the file.
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()

        # UPDATED: IDEMPOTENCY — handle a concurrent request using the same key.
        existing_record = (
            db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.key == idempotency_key,
            )
            .first()
        )

        if existing_record is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to reserve this Idempotency-Key; retry the request",
            )

        if existing_record.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This Idempotency-Key was already used "
                    "with a different request"
                ),
            )

        if (
            existing_record.response_body is not None
            and existing_record.response_status is not None
        ):
            return ScanResponse.model_validate_json(
                existing_record.response_body
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is still being processed",
        )

    scan_id = uuid4()
    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    file_key = f"scans/{scan_id}{extension}"

    # UPDATED: IDEMPOTENCY — track whether external storage succeeded.
    storage_uploaded = False

    try:
        upload_file(
            file_object=BytesIO(file_content),
            file_key=file_key,
            content_type=file.content_type,
        )
        storage_uploaded = True

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
            actor_id=user_id,
        )

        # UPDATED: IDEMPOTENCY — save the scan and replayable response together.
        response = ScanResponse(
            id=str(scan_id),
            patient_id=str(patient_id),
            modality=modality,
            body_part=body_part,
            acquired_at=acquired_at,
            uploaded_at=uploaded_at,
            status="uploaded",
            file_key=file_key,
        )

        idempotency_record.response_body = response.model_dump_json()
        idempotency_record.response_status = status.HTTP_201_CREATED

        db.commit()

        return response

    except Exception:
        # UPDATED: IDEMPOTENCY — roll back database changes on failure.
        db.rollback()

        # Best-effort cleanup if the file was uploaded but DB work failed.
        if storage_uploaded:
            try:
                delete_file(file_key)
            except Exception:
                # Preserve the original exception.
                pass

        # Keep the idempotency record so the same key isn't silently reused
        # for a different request. The client may retry and receive 409 while
        # the incomplete reservation remains.
        raise


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
    scan = db.get(Scan, str(scan_id))

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
    q: str | None = None,
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

    # Existing full-text search — unchanged.
    if q and q.strip():
        search_query = func.plainto_tsquery("english", q.strip())

        matching_scan_ids = (
            db.query(Report.scan_id)
            .filter(
                func.to_tsvector(
                    "english",
                    Report.findings,
                ).op("@@")(search_query)
            )
        )

        query = query.filter(Scan.id.in_(matching_scan_ids))

    if modality is not None:
        query = query.filter(Scan.modality == modality)

    if status is not None:
        query = query.filter(Scan.status == status)

    if acquired_at_from is not None:
        query = query.filter(Scan.acquired_at >= acquired_at_from)

    if acquired_at_to is not None:
        query = query.filter(Scan.acquired_at <= acquired_at_to)

    scans = query.offset(offset).limit(limit).all()

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

    db_scan = db.get(Scan, str(scan_id))

    if db_scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    if modality not in {"CT", "MRI", "X-ray"}:
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

        extension = ALLOWED_CONTENT_TYPES[file.content_type]
        new_file_key = f"scans/{scan_id}{extension}"

        file_content = file.file.read()

        if len(file_content) > MAX_FILE_SIZE:
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

        if old_file_key and old_file_key != new_file_key:
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

    db_scan = db.get(Scan, str(scan_id))

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
