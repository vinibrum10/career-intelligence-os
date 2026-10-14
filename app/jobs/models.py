from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, String, Text, UniqueConstraint, Uuid, func
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
