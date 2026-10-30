from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.profiles.models import Base

class JobSource(Base):
    __tablename__ = "job_sources"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id"], ["career.owners.id"], ondelete="CASCADE"),
        UniqueConstraint("owner_id", "id", name="uq_jobs_owned_source"),
        {"schema": "career"},
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class JobSnapshot(Base):
    __tablename__ = "job_snapshots"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id", "source_id"], ["career.job_sources.owner_id", "career.job_sources.id"],
                             ondelete="CASCADE", name="fk_snapshots_owned_source"),
        UniqueConstraint("owner_id", "source_id", "version", name="uq_snapshots_source_version"),
        UniqueConstraint("owner_id", "id", name="uq_snapshots_owned"),
        CheckConstraint("version > 0", name="ck_snapshots_positive"),
        {"schema": "career"},
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version: Mapped[int]
    label: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    association_confirmed: Mapped[bool] = mapped_column(default=False)
    original_text: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ExtractionRun(Base):
    __tablename__ = "extraction_runs"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id", "snapshot_id"], ["career.job_snapshots.owner_id", "career.job_snapshots.id"],
                             ondelete="CASCADE", name="fk_runs_owned_snapshot"),
        UniqueConstraint("owner_id", "id", name="uq_runs_owned"),
        {"schema": "career"},
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    snapshot_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    extractor: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class JobClaim(Base):
    __tablename__ = "job_claims"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id", "run_id"], ["career.extraction_runs.owner_id", "career.extraction_runs.id"],
                             ondelete="CASCADE", name="fk_claims_owned_run"),
        UniqueConstraint("owner_id", "id", name="uq_claims_owned"),
        CheckConstraint("knowledge IN ('explicit', 'inferred', 'not_provided')", name="ck_claims_knowledge"),
        CheckConstraint("requirement IS NULL OR requirement IN ('required', 'preferred', 'informational')", name="ck_claims_requirement"),
        CheckConstraint("(knowledge = 'not_provided') = (value IS NULL)", name="ck_claims_value_matches_knowledge"),
        CheckConstraint("knowledge <> 'inferred' OR basis IS NOT NULL", name="ck_claims_inference_basis"),
        {"schema": "career"},
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    run_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    position: Mapped[int] = mapped_column(Integer)
    field_key: Mapped[str] = mapped_column(String(40))
    knowledge: Mapped[str] = mapped_column(String(12))
    requirement: Mapped[str | None] = mapped_column(String(13))
    value: Mapped[object | None] = mapped_column(JSONB(none_as_null=True))
    basis: Mapped[str | None] = mapped_column(Text)

class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id", "claim_id"], ["career.job_claims.owner_id", "career.job_claims.id"],
                             ondelete="CASCADE", name="fk_evidence_owned_claim"),
        CheckConstraint("start_char >= 0 AND end_char > start_char", name="ck_evidence_range"),
        {"schema": "career"},
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    claim_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    start_char: Mapped[int] = mapped_column(Integer)
    end_char: Mapped[int] = mapped_column(Integer)
    excerpt: Mapped[str] = mapped_column(Text)

