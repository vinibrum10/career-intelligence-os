from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator, model_validator

class Capture(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=200)
    original_text: str = Field(min_length=1, max_length=100000)
    source_url: str | None = Field(default=None, max_length=2048)
    association_confirmed: bool = False
    captured_at: datetime | None = None

    @field_validator("label")
    @classmethod
    def label_valid(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("Provide a non-empty label without NUL characters")
        return value.strip()

    @field_validator("original_text")
    @classmethod
    def text_valid(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("Provide non-empty text without NUL characters")
        return value  # Preserve whitespace, accents and line endings exactly.

    @field_validator("source_url")
    @classmethod
    def url_valid(cls, value):
        if value is None:
            return value
        if any(ord(c) < 32 for c in value):
            raise ValueError("URL must not contain control characters")
        value = value.strip()
        url = TypeAdapter(HttpUrl).validate_python(value)
        if url.username or url.password:
            raise ValueError("URL must not contain credentials")
        return value

    @field_validator("captured_at")
    @classmethod
    def time_valid(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Capture time requires a timezone")
        return value

    @model_validator(mode="after")
    def association_valid(self):
        if self.association_confirmed and self.source_url is None:
            raise ValueError("Confirming association requires a source URL")
        return self

class CaptureUpdate(Capture):
    expected_version: int = Field(ge=1)

class SnapshotSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    source_id: UUID
    version: int
    label: str
    source_url: str | None
    association_confirmed: bool
    captured_at: datetime | None
    imported_at: datetime

class SnapshotRead(SnapshotSummary):
    original_text: str
    content_sha256: str

class JobSummary(BaseModel):
    id: UUID
    owner_id: UUID
    created_at: datetime
    latest: SnapshotSummary

class JobRead(JobSummary):
    latest: SnapshotRead
