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
import asyncio

from app.api.dependencies import pagination_params, require_role
from app.db.audit import write_audit_log
from app.db.dependencies import get_async_db, get_db
from app.models.models import AnalysisJob, Scan
from app.schemas.analysis import AnalysisJobResponse, AnalysisStatusResponse
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

    file_path = UPLOAD_DIR / f"{scan_id}{extension}"

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_size = 0

    try:
        with file_path.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File size must be 20 MB or less",
                    )

                output.write(chunk)

    except Exception:
        if file_path.exists():
            file_path.unlink()

        raise

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

        extension = ALLOWED_CONTENT_TYPES[file.content_type]

        new_file_key = f"scans/{scan_id}{extension}"
        new_file_path = UPLOAD_DIR / f"{scan_id}{extension}"

        old_file_path = None

        if db_scan.file_key:
            old_file_path = (
                UPLOAD_DIR
                / Path(db_scan.file_key).name
            )

        total_size = 0

        try:
            with new_file_path.open("wb") as output:
                while chunk := file.file.read(1024 * 1024):
                    total_size += len(chunk)

                    if total_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="File size must be 20 MB or less",
                        )

                    output.write(chunk)

        except Exception:
            if new_file_path.exists():
                new_file_path.unlink()
            raise

        if (
            old_file_path
            and old_file_path.exists()
            and old_file_path != new_file_path
        ):
            old_file_path.unlink()

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

    write_audit_log(
        db=db,
        action="DELETE",
        entity="scan",
        entity_id=str(scan_id),
        actor_id=current_user["user_id"],
    )

    db.delete(db_scan)
    db.commit()
@router.post(
    "/{scan_id}/analyze",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_scan(
    scan_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> AnalysisJobResponse:
    scan = await db.get(
        Scan,
        str(scan_id),
    )

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    job = AnalysisJob(
        id=str(uuid4()),
        scan_id=str(scan_id),
        status="uploaded",
        request_id=request.headers.get("X-Request-ID"),
    )

    db.add(job)

    await db.commit()
    await db.refresh(job)

    return AnalysisJobResponse(
        job_id=job.id,
        scan_id=job.scan_id,
        status=job.status,
    )


@router.get(
    "/{scan_id}/analysis",
    response_model=AnalysisStatusResponse,
)
async def get_analysis_status(
    scan_id: UUID,
    db: AsyncSession = Depends(get_async_db),
) -> AnalysisStatusResponse:
    result = await db.execute(
        select(AnalysisJob)
        .where(AnalysisJob.scan_id == str(scan_id))
        .order_by(AnalysisJob.created_at.desc())
        .limit(1)
    )

    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis job not found",
        )

    return AnalysisStatusResponse(
        job_id=job.id,
        scan_id=job.scan_id,
        status=job.status,
        retry_count=job.retry_count,
        error=job.error,
        confidence=job.confidence,
        findings=job.findings,
    )


async def analysis_worker(session_factory=AsyncSessionLocal) -> None:
    while True:
        async with session_factory() as db:
            result = await db.execute(
                select(AnalysisJob)
                .where(
                    AnalysisJob.status == "running",
                    AnalysisJob.created_at < text(
                        "now() - interval '60 seconds'"
                    ),
                )
            )

            stale_jobs = result.scalars().all()

            for stale_job in stale_jobs:
                stale_job.status = "uploaded"
                stale_job.error = "Previous worker stopped during processing"

                print(
                    f"Recovered stale analysis job: "
                    f"{stale_job.id}"
                )

            if stale_jobs:
                await db.commit()

            result = await db.execute(
                select(AnalysisJob)
                .where(AnalysisJob.status == "uploaded")
                .with_for_update(skip_locked=True)
                .limit(1)
            )

            job = result.scalar_one_or_none()

            if job is not None:
                job.status = "running"
                await db.commit()

                print(
                    f"Processing analysis job: {job.id} "
                    f"request_id={job.request_id}"
                )

                try:
                    await asyncio.sleep(3)

                    job.confidence = 0.94
                    job.findings = "No acute abnormality detected"
                    job.status = "done"
                    job.error = None

                    await db.commit()

                    print(
                        f"Completed analysis job: {job.id} "
                        f"request_id={job.request_id}"
                    )

                except Exception as exc:
                    job.retry_count += 1
                    job.error = str(exc)

                    if job.retry_count >= 3:
                        job.status = "failed"
                        await db.commit()

                        print(
                            f"Analysis job failed permanently: "
                            f"{job.id} request_id={job.request_id}"
                        )

                    else:
                        job.status = "uploaded"
                        await db.commit()

                        print(
                            f"Analysis job failed, retrying: "
                            f"{job.id} request_id={job.request_id} "
                            f"(attempt {job.retry_count})"
                        )

        await asyncio.sleep(5)