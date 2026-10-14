"""Manual, evidence-linked facts (claims) about a saved job capture. Append-only: corrections create a new run."""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, get_args
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter, ValidationError, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_session
from app.profiles.schemas import Contract, Country, Currency, WorkArrangement
from .models import ClaimEvidence, ExtractionRun, JobClaim
from .service import read_snapshot

Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class WorkCountries(Strict):
    countries: list[Country] = Field(min_length=1, max_length=100)
    @model_validator(mode="after")
    def unique(self):
        if len(set(self.countries)) != len(self.countries):
            raise ValueError("Duplicate countries")
        return self

class SkillGroup(Strict):
    """Alternatives inside one group (e.g. 'A, B or similar') stay one requirement, not several."""
    alternatives: list[Short] = Field(min_length=1, max_length=20)
    @model_validator(mode="after")
    def unique(self):
        if len(set(self.alternatives)) != len(self.alternatives):
            raise ValueError("Duplicate alternatives")
        return self

class Compensation(Strict):
    minimum: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    maximum: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    currency: Currency
    currency_basis: Literal["advertised", "actual_payment"]
    period: Literal["hour", "month", "year"]
    amount_basis: Literal["gross", "net", "unknown"]
    @model_validator(mode="after")
    def amounts(self):
        if self.minimum is None and self.maximum is None:
            raise ValueError("Provide a minimum or a maximum")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("Minimum is greater than maximum")
        return self

VALUE_TYPES = {
    "work_arrangement": TypeAdapter(WorkArrangement),
    "work_countries": TypeAdapter(WorkCountries),
    "sponsorship": TypeAdapter(Literal["offered", "not_offered"]),
    "authorization_restriction": TypeAdapter(Short),
    "contract": TypeAdapter(Contract),
    "working_time": TypeAdapter(Literal["full_time", "part_time", "other"]),
    "compensation": TypeAdapter(Compensation),
    "skill_group": TypeAdapter(SkillGroup),
}
FieldKey = Literal["work_arrangement", "work_countries", "sponsorship", "authorization_restriction",
                   "contract", "working_time", "compensation", "skill_group"]
assert set(get_args(FieldKey)) == set(VALUE_TYPES)

class EvidenceIn(Strict):
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=1)
    excerpt: str = Field(min_length=1, max_length=5000)
    @model_validator(mode="after")
    def order(self):
        if self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        return self

class ClaimIn(Strict):
    field_key: FieldKey
    knowledge: Literal["explicit", "inferred", "not_provided"]
    requirement: Literal["required", "preferred", "informational"] | None = None
    value: Any = None
    basis: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)] | None = None
    evidence: list[EvidenceIn] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def rules(self):
        if self.knowledge == "not_provided":
            if self.value is not None or self.evidence or self.requirement or self.basis:
                raise ValueError("A not_provided claim records only that the field was inspected")
            return self
        if self.value is None:
            raise ValueError("Provide a value, or use knowledge=not_provided")
        try:
            adapter = VALUE_TYPES[self.field_key]
            self.value = adapter.dump_python(adapter.validate_python(self.value), mode="json")
        except ValidationError as error:
            raise ValueError(f"Invalid value for {self.field_key}: {error.errors()[0]['msg']}") from None
        if self.knowledge == "explicit" and not self.evidence:
            raise ValueError("An explicit claim needs at least one evidence excerpt")
        if self.knowledge == "inferred" and not self.basis:
            raise ValueError("An inferred claim needs its basis")
        return self

class ExtractionIn(Strict):
    extractor: Short = Field(max_length=60)
    claims: list[ClaimIn] = Field(min_length=1, max_length=200)

class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    start_char: int
    end_char: int
    excerpt: str

class ClaimRead(BaseModel):
    id: UUID
    field_key: str
    knowledge: str
    requirement: str | None
    value: Any
    basis: str | None
    evidence: list[EvidenceRead]

class ExtractionRead(BaseModel):
    id: UUID
    snapshot_id: UUID
    extractor: str
    created_at: datetime
    claims: list[ClaimRead]

def read(session, run):
    claims = session.scalars(select(JobClaim).where(JobClaim.owner_id == run.owner_id, JobClaim.run_id == run.id)
                             .order_by(JobClaim.position)).all()
    by_claim = {claim.id: [] for claim in claims}
    for item in session.scalars(select(ClaimEvidence).where(ClaimEvidence.owner_id == run.owner_id,
            ClaimEvidence.claim_id.in_(by_claim)).order_by(ClaimEvidence.start_char, ClaimEvidence.end_char)):
        by_claim[item.claim_id].append(EvidenceRead.model_validate(item))
    return ExtractionRead(id=run.id, snapshot_id=run.snapshot_id, extractor=run.extractor, created_at=run.created_at,
        claims=[ClaimRead(id=c.id, field_key=c.field_key, knowledge=c.knowledge, requirement=c.requirement,
                          value=c.value, basis=c.basis, evidence=by_claim[c.id]) for c in claims])

def create(session, owner_id, source_id, version, data):
    snapshot = read_snapshot(session, owner_id, source_id, version)
    text = snapshot.original_text
    errors = [f"claims[{i}].evidence[{j}]: excerpt does not match the saved text at {e.start_char}:{e.end_char}"
              for i, claim in enumerate(data.claims) for j, e in enumerate(claim.evidence)
              if e.end_char > len(text) or text[e.start_char:e.end_char] != e.excerpt]
    if errors:
        raise HTTPException(422, errors)
    run = ExtractionRun(owner_id=owner_id, snapshot_id=snapshot.id, extractor=data.extractor)
    session.add(run)
    session.flush()
    for position, claim in enumerate(data.claims):
        row = JobClaim(owner_id=owner_id, run_id=run.id, position=position, field_key=claim.field_key,
                       knowledge=claim.knowledge, requirement=claim.requirement, value=claim.value, basis=claim.basis)
        session.add(row)
        session.flush()
        session.add_all(ClaimEvidence(owner_id=owner_id, claim_id=row.id, start_char=e.start_char,
                                      end_char=e.end_char, excerpt=e.excerpt) for e in claim.evidence)
    session.commit()
    return read(session, run)

def find(session, owner_id, source_id, version, extraction_id):
    snapshot = read_snapshot(session, owner_id, source_id, version)
    run = session.scalar(select(ExtractionRun).where(ExtractionRun.owner_id == owner_id,
        ExtractionRun.snapshot_id == snapshot.id, ExtractionRun.id == extraction_id))
    if run is None:
        raise HTTPException(404, "Extraction not found")
    return run

router = APIRouter(prefix="/career/owners/{owner_id}/jobs/{source_id}/snapshots/{version}/extractions",
                   tags=["Local job captures (no authentication)"])

@router.post("", response_model=ExtractionRead, status_code=201)
def create_extraction(owner_id: UUID, source_id: UUID, data: ExtractionIn, version: int = Path(ge=1), session: Session = Depends(get_session)):
    return create(session, owner_id, source_id, version, data)

@router.get("", response_model=list[ExtractionRead])
def list_extractions(owner_id: UUID, source_id: UUID, version: int = Path(ge=1), limit: int = Query(20, ge=1, le=100),
                     offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
    snapshot = read_snapshot(session, owner_id, source_id, version)
    runs = session.scalars(select(ExtractionRun).where(ExtractionRun.owner_id == owner_id, ExtractionRun.snapshot_id == snapshot.id)
        .order_by(ExtractionRun.created_at.desc(), ExtractionRun.id).limit(limit).offset(offset)).all()
    return [read(session, run) for run in runs]

@router.get("/{extraction_id}", response_model=ExtractionRead)
def read_extraction(owner_id: UUID, source_id: UUID, extraction_id: UUID, version: int = Path(ge=1), session: Session = Depends(get_session)):
    return read(session, find(session, owner_id, source_id, version, extraction_id))
