from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from app.database import get_session
from . import service
from .schemas import Capture, CaptureUpdate, JobRead, JobSummary, SnapshotRead, SnapshotSummary

router = APIRouter(prefix="/career/owners/{owner_id}/jobs", tags=["Local job captures (no authentication)"])

@router.post("", response_model=JobRead, status_code=201)
def create_job(owner_id: UUID, data: Capture, session: Session = Depends(get_session)):
    return service.create(session, owner_id, data)

@router.get("", response_model=list[JobSummary])
def list_jobs(owner_id: UUID, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
    return service.list_sources(session, owner_id, limit, offset)

@router.get("/{source_id}", response_model=JobRead)
def read_job(owner_id: UUID, source_id: UUID, session: Session = Depends(get_session)):
    return service.response(session, service.require_source(session, owner_id, source_id))

@router.post("/{source_id}/snapshots", response_model=JobRead, status_code=201)
def capture_job(owner_id: UUID, source_id: UUID, data: CaptureUpdate, session: Session = Depends(get_session)):
    return service.update(session, owner_id, source_id, data)

@router.get("/{source_id}/snapshots", response_model=list[SnapshotSummary])
def list_captures(owner_id: UUID, source_id: UUID, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
    return service.list_snapshots(session, owner_id, source_id, limit, offset)

@router.get("/{source_id}/snapshots/{version}", response_model=SnapshotRead)
def read_capture(owner_id: UUID, source_id: UUID, version: int = Path(ge=1), session: Session = Depends(get_session)):
    return service.read_snapshot(session, owner_id, source_id, version)
