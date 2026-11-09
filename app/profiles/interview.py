from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, StringConstraints, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_session
from .models import CareerInterview
from .schemas import Schema
from .service import require_owner

Topic = Literal["experience", "projects", "skills", "results"]
Answer = Annotated[str, StringConstraints(min_length=1, max_length=3000)]
Fact = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]

router = APIRouter(prefix="/career/owners/{owner_id}/interviews", tags=["Career interviews"])


class InterviewContent(Schema):
    answers: dict[Topic, Answer] = Field(min_length=1)
    facts: dict[Topic, Fact] = Field(min_length=1)

    @model_validator(mode="after")
    def check_sources(self):
        if any(not answer.strip() for answer in self.answers.values()):
            raise ValueError("Answers must contain text")
        if not self.facts.keys() <= self.answers.keys():
            raise ValueError("Every confirmed fact needs an interview answer")
        return self


class InterviewSummary(Schema):
    id: UUID
    created_at: datetime


class InterviewRead(InterviewSummary, InterviewContent):
    pass


@router.put("/{interview_id}", response_model=InterviewRead, status_code=201)
def save_interview(owner_id: UUID, interview_id: UUID, data: InterviewContent,
                   session: Session = Depends(get_session)):
    require_owner(session, owner_id)
    interview = CareerInterview(id=interview_id, owner_id=owner_id, answers=data.answers, facts=data.facts)
    session.add(interview)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.get(CareerInterview, interview_id)
        if existing is None:
            raise
        if existing.owner_id != owner_id or existing.answers != data.answers or existing.facts != data.facts:
            raise HTTPException(409, "Interview identifier already in use")
        return existing
    return interview


@router.get("", response_model=list[InterviewSummary])
def list_interviews(owner_id: UUID, limit: int = Query(50, ge=1, le=100),
                    offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
    require_owner(session, owner_id)
    return session.scalars(
        select(CareerInterview)
        .where(CareerInterview.owner_id == owner_id)
        .order_by(CareerInterview.created_at.desc(), CareerInterview.id)
        .limit(limit)
        .offset(offset)
    ).all()


@router.get("/{interview_id}", response_model=InterviewRead)
def read_interview(owner_id: UUID, interview_id: UUID, session: Session = Depends(get_session)):
    interview = session.scalar(select(CareerInterview).where(
        CareerInterview.owner_id == owner_id, CareerInterview.id == interview_id,
    ))
    if interview is None:
        raise HTTPException(404, "Interview not found for this owner")
    return interview
