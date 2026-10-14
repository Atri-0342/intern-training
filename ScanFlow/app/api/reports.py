from io import BytesIO
from typing import Annotated
from uuid import uuid4, UUID
import hashlib
import json

from app.models.models import IdempotencyRecord, Report
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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import pagination_params, require_role
from app.api.rate_limit import enforce_user_rate_limit
from app.db.audit import write_audit_log
from app.db.dependencies import get_db
from app.models.models import Report
from app.schemas.report import ReportCreate, ReportResponse
from app.services.storage import upload_file, delete_file

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

router = APIRouter(
    prefix="/v1/reports",
    tags=["reports"],
    dependencies=[Depends(enforce_user_rate_limit)]
)

@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    report: Annotated[ReportCreate, Form()],
    file: UploadFile = File(...),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("radiologist")),
) -> ReportResponse:
    idempotency_key = idempotency_key.strip()

    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must not be empty",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed",
        )

    file_content = file.file.read(MAX_FILE_SIZE + 1)

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must be 20 MB or less",
        )

    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    fingerprint = {
        "report_id": str(report.id),
        "scan_id": str(report.scan_id),
        "findings": report.findings,
        "radiologist_id": str(report.radiologist_id),
        "finalized_at": (
            report.finalized_at.isoformat()
            if report.finalized_at
            else None
        ),
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
                detail=(
                    "This Idempotency-Key was already used "
                    "with a different request"
                ),
            )

        if existing.response_body and existing.response_status:
            return ReportResponse.model_validate_json(
                existing.response_body
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "A request with this Idempotency-Key "
                "is still being processed"
            ),
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
                detail=(
                    "Unable to reserve this Idempotency-Key; "
                    "retry the request"
                ),
            )

        if existing.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This Idempotency-Key was already used "
                    "with a different request"
                ),
            )

        if existing.response_body and existing.response_status:
            return ReportResponse.model_validate_json(
                existing.response_body
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "A request with this Idempotency-Key "
                "is still being processed"
            ),
        )

    storage_uploaded = False
    pdf_key = f"reports/{report.id}.pdf"

    try:
        # Prevent creating a report whose ID already exists.
        if db.get(Report, str(report.id)) is not None:
            raise HTTPException(
                status_code=409,
                detail="Report already exists",
            )

        # Upload the PDF to S3.
        upload_file(
            file_object=BytesIO(file_content),
            file_key=pdf_key,
            content_type="application/pdf",
        )
        storage_uploaded = True

        db_report = Report(
            id=str(report.id),
            scan_id=str(report.scan_id),
            findings=report.findings,
            radiologist_id=str(report.radiologist_id),
            finalized_at=report.finalized_at,
            pdf_key=pdf_key,
        )

        response = ReportResponse(
            id=db_report.id,
            scan_id=db_report.scan_id,
            findings=db_report.findings,
            radiologist_id=db_report.radiologist_id,
            finalized_at=db_report.finalized_at,
            pdf_key=db_report.pdf_key,
        )

        db.add(db_report)

        write_audit_log(
            db=db,
            action="CREATE",
            entity="report",
            entity_id=str(report.id),
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
                delete_file(file_key=pdf_key)
            except Exception:
                pass

        raise

@router.get(
    "/{report_id}",
    response_model=ReportResponse,
)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician", "radiologist")
    ),
) -> ReportResponse:

    report = db.get(
        Report,
        str(report_id),
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return ReportResponse(
        id=report.id,
        scan_id=report.scan_id,
        findings=report.findings,
        radiologist_id=report.radiologist_id,
        finalized_at=report.finalized_at,
        pdf_key=report.pdf_key,
    )

@router.get(
    "",
    response_model=list[ReportResponse],
)
def list_reports(
    pagination: dict[str, int] = Depends(pagination_params),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician", "radiologist")
    ),
) -> list[ReportResponse]:

    limit = pagination["limit"]
    offset = pagination["offset"]

    reports = (
        db.query(Report)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        ReportResponse(
            id=report.id,
            scan_id=report.scan_id,
            findings=report.findings,
            radiologist_id=report.radiologist_id,
            finalized_at=report.finalized_at,
            pdf_key=report.pdf_key,
        )
        for report in reports
    ]


@router.patch(
    "/{report_id}",
    response_model=ReportResponse,
)
def update_report(
    report_id: UUID,
    report: Annotated[ReportCreate, Form()],
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("radiologist")
    ),
) -> ReportResponse:

    db_report = db.get(
        Report,
        str(report_id),
    )

    if db_report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed",
        )

    file_content = file.file.read(MAX_FILE_SIZE + 1)

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must be 20 MB or less",
        )

    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    old_pdf_key = db_report.pdf_key
    new_pdf_key = f"reports/{report_id}-{uuid4()}.pdf"
    storage_uploaded = False

    try:
        upload_file(
            file_object=BytesIO(file_content),
            file_key=new_pdf_key,
            content_type="application/pdf",
        )
        storage_uploaded = True

        db_report.scan_id = str(report.scan_id)
        db_report.findings = report.findings
        db_report.radiologist_id = str(report.radiologist_id)
        db_report.finalized_at = report.finalized_at
        db_report.pdf_key = new_pdf_key

        write_audit_log(
            db=db,
            action="UPDATE",
            entity="report",
            entity_id=str(report_id),
            actor_id=current_user["user_id"],
        )

        db.commit()
        db.refresh(db_report)

    except Exception:
        db.rollback()

        if storage_uploaded:
            try:
                delete_file(file_key=new_pdf_key)
            except Exception:
                pass

        raise

    if old_pdf_key and old_pdf_key != new_pdf_key:
        try:
            delete_file(file_key=old_pdf_key)
        except Exception:
            pass

    return ReportResponse(
        id=db_report.id,
        scan_id=db_report.scan_id,
        findings=db_report.findings,
        radiologist_id=db_report.radiologist_id,
        finalized_at=db_report.finalized_at,
        pdf_key=db_report.pdf_key,
    )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("admin")
    ),
) -> None:
    db_report = db.get(
        Report,
        str(report_id),
    )

    if db_report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    pdf_key = db_report.pdf_key

    write_audit_log(
        db=db,
        action="DELETE",
        entity="report",
        entity_id=str(report_id),
        actor_id=current_user["user_id"],
    )

    db.delete(db_report)
    db.commit()

    if pdf_key:
        try:
            delete_file(file_key=pdf_key)
        except Exception:
            pass