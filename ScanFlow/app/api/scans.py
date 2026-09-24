from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
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


router = APIRouter(
    prefix="/v1/scans",
    tags=["scans"],
)


@router.post(
    "/{scan_id}/analyze",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_scan(
    scan_id: UUID,
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

            # Find and claim one uploaded job
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

                print(f"Processing analysis job: {job.id}")

                try:
                    # Simulate inference
                    await asyncio.sleep(3)

                    # Synthetic analysis result
                    job.confidence = 0.94
                    job.findings = "No acute abnormality detected"
                    job.status = "done"
                    job.error = None

                    await db.commit()

                    print(f"Completed analysis job: {job.id}")

                except Exception as exc:
                    job.retry_count += 1
                    job.error = str(exc)

                    if job.retry_count >= 3:
                        job.status = "failed"
                        await db.commit()

                        print(
                            f"Analysis job failed permanently: "
                            f"{job.id}"
                        )

                    else:
                        job.status = "uploaded"
                        await db.commit()

                        print(
                            f"Analysis job failed, retrying: "
                            f"{job.id} "
                            f"(attempt {job.retry_count})"
                        )

        await asyncio.sleep(5)

@router.post(
    "",
    response_model=ScanResponse,
    status_code=201,
)
def create_scan(
    scan: ScanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_role("clinician")
    ),
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
