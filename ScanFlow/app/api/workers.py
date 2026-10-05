# app/api/worker.py

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.dependencies import get_async_db
from app.db.session import AsyncSessionLocal
from app.models.models import AnalysisJob
from app.models.models import Scan
from app.schemas.analysis import (
    AnalysisJobResponse,
    AnalysisStatusResponse,
)

router = APIRouter(
    prefix="/v1/scans",
    tags=["analysis"],
)
WS_TICKET_TTL_SECONDS = 30
ws_tickets: dict[str, dict[str, Any]] = {}

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(
        self,
        scan_id: str,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        self.connections[scan_id].add(websocket)

    def disconnect(
        self,
        scan_id: str,
        websocket: WebSocket,
    ) -> None:
        sockets = self.connections.get(scan_id)

        if not sockets:
            return

        sockets.discard(websocket)

        if not sockets:
            self.connections.pop(scan_id, None)

    async def broadcast(
        self,
        scan_id: str,
        message: dict,
    ) -> None:
        sockets = self.connections.get(
            scan_id,
            set(),
        ).copy()

        for websocket in sockets:
            try:
                await websocket.send_json(message)

            except Exception:
                self.disconnect(
                    scan_id,
                    websocket,
                )


manager = ConnectionManager()

ticket_router = APIRouter(
    prefix="/v1/ws",
    tags=["websocket"],
)


@ticket_router.post("/tickets")
async def create_websocket_ticket(
    scan_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict:

    scan = await db.get(
        Scan,
        str(scan_id),
    )

    if scan is None:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    ticket = str(uuid4())

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            seconds=WS_TICKET_TTL_SECONDS
        )
    )

    ws_tickets[ticket] = {
        "user_id": current_user["user_id"],
        "scan_id": str(scan_id),
        "expires_at": expires_at,
    }

    return {
        "ticket": ticket,
        "expires_in": WS_TICKET_TTL_SECONDS,
    }

def consume_websocket_ticket(
    ticket: str,
    scan_id: str,
) -> dict:
    ticket_data = ws_tickets.pop(ticket, None)

    if ticket_data is None:
        raise ValueError(
            "Invalid or already used WebSocket ticket"
        )

    expires_at = ticket_data["expires_at"]

    if datetime.now(timezone.utc) >= expires_at:
        raise ValueError(
            "WebSocket ticket expired"
        )

    if ticket_data["scan_id"] != scan_id:
        raise ValueError(
            "WebSocket ticket does not match scan"
        )

    return ticket_data


ws_router = APIRouter(
    prefix="/v1/ws",
    tags=["websocket"],
)


@ws_router.websocket(
    "/scans/{scan_id}"
)
async def scan_websocket(
    websocket: WebSocket,
    scan_id: UUID,
):
    scan_id_str = str(scan_id)

    ticket = websocket.query_params.get(
        "ticket"
    )

    if not ticket:
        await websocket.close(
            code=1008,
            reason="WebSocket ticket required",
        )
        return

    try:
        ticket_data = consume_websocket_ticket(
            ticket,
            scan_id_str,
        )

    except ValueError as exc:
        await websocket.close(
            code=1008,
            reason=str(exc),
        )
        return

    await manager.connect(
        scan_id_str,
        websocket,
    )

    print(
        "WebSocket connected: "
        f"user_id={ticket_data['user_id']} "
        f"scan_id={scan_id_str}"
    )

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(
            scan_id_str,
            websocket,
        )

    except Exception:
        manager.disconnect(
            scan_id_str,
            websocket,
        )


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
        request_id=request.headers.get(
            "X-Request-ID"
        ),
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
        .where(
            AnalysisJob.scan_id == str(scan_id)
        )
        .order_by(
            AnalysisJob.created_at.desc()
        )
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


# ============================================================
# ANALYSIS WORKER
# ============================================================

async def analysis_worker(
    session_factory=AsyncSessionLocal,
) -> None:

    while True:

        async with session_factory() as db:

            # ------------------------------------------------
            # Recover stale jobs
            # ------------------------------------------------

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

                stale_job.error = (
                    "Previous worker stopped during processing"
                )

                print(
                    f"Recovered stale analysis job: "
                    f"{stale_job.id}"
                )

            if stale_jobs:
                await db.commit()

            # ------------------------------------------------
            # Get next analysis job
            # ------------------------------------------------

            result = await db.execute(
                select(AnalysisJob)
                .where(
                    AnalysisJob.status == "uploaded"
                )
                .with_for_update(
                    skip_locked=True
                )
                .limit(1)
            )

            job = result.scalar_one_or_none()

            if job is not None:

                # ------------------------------------------------
                # RUNNING
                # ------------------------------------------------

                job.status = "running"

                await db.commit()

                print(
                    f"Processing analysis job: "
                    f"{job.id} "
                    f"request_id={job.request_id}"
                )

                await manager.broadcast(
                    str(job.scan_id),
                    {
                        "job_id": job.id,
                        "scan_id": job.scan_id,
                        "status": "running",
                    },
                )

                try:

                    # ------------------------------------------------
                    # Simulated analysis
                    # ------------------------------------------------

                    await asyncio.sleep(3)

                    job.confidence = 0.94

                    job.findings = (
                        "No acute abnormality detected"
                    )

                    job.status = "done"

                    job.error = None

                    await db.commit()

                    print(
                        f"Completed analysis job: "
                        f"{job.id} "
                        f"request_id={job.request_id}"
                    )

                    # ------------------------------------------------
                    # DONE
                    # ------------------------------------------------

                    await manager.broadcast(
                        str(job.scan_id),
                        {
                            "job_id": job.id,
                            "scan_id": job.scan_id,
                            "status": "done",
                            "confidence": job.confidence,
                            "findings": job.findings,
                        },
                    )

                except Exception as exc:

                    job.retry_count += 1

                    job.error = str(exc)


                    if job.retry_count >= 3:

                        job.status = "failed"

                        await db.commit()

                        print(
                            f"Analysis job failed permanently: "
                            f"{job.id} "
                            f"request_id={job.request_id}"
                        )

                        await manager.broadcast(
                            str(job.scan_id),
                            {
                                "job_id": job.id,
                                "scan_id": job.scan_id,
                                "status": "failed",
                                "error": job.error,
                            },
                        )

                    # ------------------------------------------------
                    # RETRY
                    # ------------------------------------------------

                    else:

                        job.status = "uploaded"

                        await db.commit()

                        print(
                            f"Analysis job failed, retrying: "
                            f"{job.id} "
                            f"request_id={job.request_id} "
                            f"(attempt "
                            f"{job.retry_count})"
                        )

                        await manager.broadcast(
                            str(job.scan_id),
                            {
                                "job_id": job.id,
                                "scan_id": job.scan_id,
                                "status": "uploaded",
                                "retry_count": job.retry_count,
                                "error": job.error,
                            },
                        )

        await asyncio.sleep(5)