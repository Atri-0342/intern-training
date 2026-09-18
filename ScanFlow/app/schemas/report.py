from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportCreate(BaseModel):
    id: UUID
    scan_id: UUID
    findings: str
    radiologist_id: UUID
    finalized_at: datetime | None = None


class ReportResponse(BaseModel):
    id: UUID
    scan_id: UUID
    findings: str
    radiologist_id: UUID
    finalized_at: datetime | None