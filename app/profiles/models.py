from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, String, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Owner(Base):
    __tablename__ = "owners"
    __table_args__ = {"schema": "career"}
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    label: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id"], ["career.owners.id"], ondelete="CASCADE"),
        UniqueConstraint("owner_id", "id", name="uq_profiles_owner_id"),
        {"schema": "career"},
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    label: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProfileVersion(Base):
    __tablename__ = "profile_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "profile_id"], ["career.profiles.owner_id", "career.profiles.id"],
            ondelete="CASCADE", name="fk_versions_owned_profile",
        ),
        UniqueConstraint("owner_id", "profile_id", "version", name="uq_versions_profile_number"),
        CheckConstraint("version > 0", name="ck_versions_positive"),
        CheckConstraint("schema_version = 1", name="ck_versions_schema"),
        {"schema": "career"},
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    profile_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version: Mapped[int]
    schema_version: Mapped[int] = mapped_column(default=1)
    preferences_json: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
