from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import TEXT, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Float

class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("sex IN ('male', 'female', 'other')", name="patients_sex_check"),
    )

    synthetic_study_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('clinician', 'radiologist', 'admin')", name="users_role_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    email: Mapped[str] = mapped_column(TEXT, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(TEXT, nullable=False)
    role: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = (
        CheckConstraint("modality IN ('CT', 'MRI', 'X-ray')", name="scans_modality_check"),
        CheckConstraint("status IN ('uploaded', 'processing', 'completed', 'failed')", name="scans_status_check"),
        Index("idx_scans_acquired_at", "acquired_at"),
        Index("idx_scans_modality_acquired_at", "modality", "acquired_at"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    patient_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("patients.synthetic_study_id", ondelete="RESTRICT"), nullable=False)
    modality: Mapped[str] = mapped_column(TEXT, nullable=False)
    body_part: Mapped[str] = mapped_column(TEXT, nullable=False)
    # priority: Mapped[str] = mapped_column(TEXT, nullable=False, server_default=text("'normal'"))
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(TEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    __table_args__ = (
        CheckConstraint(
            "status IN ('uploaded', 'pending', 'running', 'done', 'failed')",
            name="analysis_jobs_status_check",
        ),
        Index(
            "idx_analysis_jobs_status_created_at",
            "status",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )

    scan_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        TEXT,
        nullable=False,
        server_default=text("'pending'"),
    )

    retry_count: Mapped[int] = mapped_column(
        nullable=False,
        server_default=text("0"),
    )

    error: Mapped[str | None] = mapped_column(
        TEXT,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
    )

    findings: Mapped[str | None] = mapped_column(
        TEXT,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    scan_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    findings: Mapped[str] = mapped_column(TEXT, nullable=False)
    radiologist_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(TEXT, nullable=False)
    entity: Mapped[str] = mapped_column(TEXT, nullable=False)
    entity_id: Mapped[str] = mapped_column(TEXT, nullable=False)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))