from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(clinician|radiologist|admin)$")


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str