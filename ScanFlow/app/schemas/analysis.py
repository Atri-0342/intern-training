from uuid import UUID

from pydantic import BaseModel

class AnalysisJobResponse(BaseModel):
    job_id: UUID
    scan_id: UUID
    status: str


class AnalysisStatusResponse(BaseModel):
    job_id: UUID
    scan_id: UUID
    status: str
    retry_count: int
    error: str | None = None
    confidence: float | None = None
    findings: str | None = None