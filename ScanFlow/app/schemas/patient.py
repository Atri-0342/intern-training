from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PatientCreate(BaseModel):
    synthetic_study_id: UUID
    dob: date
    sex: str = Field(pattern="^(male|female|other)$")

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value


class PatientResponse(BaseModel):
    synthetic_study_id: UUID
    dob: date
    sex: str