from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import pagination_params, require_role
from app.db.audit import write_audit_log
from app.db.dependencies import get_db
from app.models.models import Report
from app.schemas.report import ReportCreate, ReportResponse


router = APIRouter(
    prefix="/v1/reports",
    tags=["reports"],
)


@router.post(
    "",
    response_model=ReportResponse,
    status_code=201,
)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("clinician")),
) -> ReportResponse:

    exists = db.get(
        Report,
        str(report.id),
    )

    if exists is not None:
        raise HTTPException(
            status_code=409,
            detail="Report already exists",
        )

    db_report = Report(
        id=str(report.id),
        scan_id=str(report.scan_id),
        findings=report.findings,
        radiologist_id=str(report.radiologist_id),
        finalized_at=report.finalized_at,
    )

    db.add(db_report)

    write_audit_log(
        db=db,
        action="CREATE",
        entity="report",
        entity_id=str(report.id),
        actor_id=current_user["user_id"],
    )

    db.commit()
    db.refresh(db_report)

    return ReportResponse(
        id=db_report.id,
        scan_id=db_report.scan_id,
        findings=db_report.findings,
        radiologist_id=db_report.radiologist_id,
        finalized_at=db_report.finalized_at,
    )


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
        )
        for report in reports
    ]


@router.patch(
    "/{report_id}",
    response_model=ReportResponse,
)
def update_report(
    report_id: UUID,
    report: ReportCreate,
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

    db_report.scan_id = str(report.scan_id)
    db_report.findings = report.findings
    db_report.radiologist_id = str(report.radiologist_id)
    db_report.finalized_at = report.finalized_at

    write_audit_log(
        db=db,
        action="UPDATE",
        entity="report",
        entity_id=str(report_id),
        actor_id=current_user["user_id"],
    )

    db.commit()
    db.refresh(db_report)

    return ReportResponse(
        id=db_report.id,
        scan_id=db_report.scan_id,
        findings=db_report.findings,
        radiologist_id=db_report.radiologist_id,
        finalized_at=db_report.finalized_at,
    )


@router.delete(
    "/{report_id}",
    status_code=204,
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

    write_audit_log(
        db=db,
        action="DELETE",
        entity="report",
        entity_id=str(report_id),
        actor_id=current_user["user_id"],
    )

    db.delete(db_report)
    db.commit()