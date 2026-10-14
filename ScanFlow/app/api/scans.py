from io import BytesIO
from uuid import UUID, uuid4
from datetime import datetime, timezone
import hashlib
import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.services.storage import delete_file, upload_file
from app.api.rate_limit import enforce_user_rate_limit
from app.api.dependencies import pagination_params, require_role
from app.db.audit import write_audit_log
from app.db.dependencies import get_db
from app.models.models import (
    Report,
    Scan,
    IdempotencyRecord,
)
from app.schemas.scan import ScanResponse


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


@router.post(
    "/",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_scan(
    patient_id: UUID = Form(...),
    modality: str = Form(...),
    body_part: str = Form(...),
    acquired_at: datetime = Form(...),
    file: UploadFile = File(...),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("clinician")),
) -> ScanResponse:
    idempotency_key = idempotency_key.strip()

    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must not be empty",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, and PNG files are allowed",
        )

    file_content = file.file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must be 20 MB or less",
        )

    fingerprint = {
        "patient_id": str(patient_id),
        "modality": modality,
        "body_part": body_part,
        "acquired_at": acquired_at.isoformat(),
        "content_type": file.content_type,
        "file_sha256": hashlib.sha256(file_content).hexdigest(),
    }

    request_hash = hashlib.sha256(
        json.dumps(
            fingerprint,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    user_id = str(current_user["user_id"])

    existing = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.key == idempotency_key,
        )
        .first()
    )

    if existing:
        if existing.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="This Idempotency-Key was already used with a different request",
            )

        if existing.response_body and existing.response_status:
            return ScanResponse.model_validate_json(
                existing.response_body
            )

        raise HTTPException(
            status_code=409,
            detail="A request with this Idempotency-Key is still being processed",
        )

    record = IdempotencyRecord(
        id=str(uuid4()),
        user_id=user_id,
        key=idempotency_key,
        request_hash=request_hash,
        response_body=None,
        response_status=None,
    )

    db.add(record)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        existing = (
            db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.key == idempotency_key,
            )
            .first()
        )

        if existing is None:
            raise HTTPException(
                status_code=409,
                detail="Unable to reserve this Idempotency-Key; retry the request",
            )

        if existing.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="This Idempotency-Key was already used with a different request",
            )

        if existing.response_body and existing.response_status:
            return ScanResponse.model_validate_json(
                existing.response_body
            )

        raise HTTPException(
            status_code=409,
            detail="A request with this Idempotency-Key is still being processed",
        )

    scan_id = uuid4()
    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    file_key = f"scans/{scan_id}{extension}"
    storage_uploaded = False

    try:
        # S3 upload through app/services/storage.py (boto3/Moto endpoint).
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

        db.add(db_scan)

        write_audit_log(
            db=db,
            action="CREATE",
            entity="scan",
            entity_id=str(scan_id),
            actor_id=user_id,
        )

        record.response_body = response.model_dump_json()
        record.response_status = status.HTTP_201_CREATED

        db.commit()
        return response

    except Exception:
        db.rollback()

        if storage_uploaded:
            try:
                delete_file(file_key)
            except Exception:
                pass

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


'''@router.get(
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
    query = db.query(Scan)

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

    scans = (
        query
        .offset(pagination["offset"])
        .limit(pagination["limit"])
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
'''

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
    limit: int = 10,
    cursor: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician", "radiologist")
    ),
) -> list[ScanResponse]:
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 100",
        )

    query = db.query(Scan)

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

    if cursor is not None:
        query = query.filter(Scan.id > str(cursor))

    scans = (
        query
        .order_by(Scan.id.asc())
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
    current_user: dict = Depends(require_role("clinician")),
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

    old_file_key = db_scan.file_key
    new_file_key = old_file_key
    uploaded_new_file = False

    try:
        if file is not None:
            if file.content_type not in ALLOWED_CONTENT_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF, JPG, and PNG files are allowed",
                )

            file_content = file.file.read()

            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="File size must be 20 MB or less",
                )

            extension = ALLOWED_CONTENT_TYPES[file.content_type]
            new_file_key = f"scans/{scan_id}{extension}"

            upload_file(
                file_object=BytesIO(file_content),
                file_key=new_file_key,
                content_type=file.content_type,
            )
            uploaded_new_file = True

        db_scan.patient_id = str(patient_id)
        db_scan.modality = modality
        db_scan.body_part = body_part
        db_scan.acquired_at = acquired_at
        db_scan.status = status_value
        db_scan.file_key = new_file_key

        write_audit_log(
            db=db,
            action="UPDATE",
            entity="scan",
            entity_id=str(scan_id),
            actor_id=current_user["user_id"],
        )

        db.commit()
        db.refresh(db_scan)

    except Exception:
        db.rollback()

        if uploaded_new_file and new_file_key != old_file_key:
            try:
                delete_file(new_file_key)
            except Exception:
                pass

        raise

    # Delete the old object only after the database update succeeds.
    if old_file_key and old_file_key != new_file_key:
        try:
            delete_file(old_file_key)
        except Exception:
            # The database update succeeded; old-object cleanup can be retried.
            pass

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
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
) -> None:
    db_scan = db.get(Scan, str(scan_id))

    if db_scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    # Remove the object before deleting its database reference.
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
