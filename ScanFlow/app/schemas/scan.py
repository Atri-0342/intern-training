from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ScanCreate(BaseModel):
    id: UUID
    patient_id: UUID
    modality: str = Field(pattern="^(CT|MRI|X-ray)$")
    body_part: str
    acquired_at: datetime
    uploaded_at: datetime | None = None
    status: str = Field(pattern="^(uploaded|processing|completed|failed)$")

    @field_validator("uploaded_at")
    @classmethod
    def validate_uploaded_at(
        cls,
        value: datetime | None,
        info,
    ) -> datetime | None:
        if value is not None:
            acquired_at = info.data.get("acquired_at")

            if acquired_at is not None and value < acquired_at:
                raise ValueError(
                    "uploaded_at cannot be earlier than acquired_at"
                )

        return value


class ScanResponse(BaseModel):
    id: UUID
    patient_id: UUID
    modality: str
    body_part: str
    acquired_at: datetime
    uploaded_at: datetime | None
    status: str