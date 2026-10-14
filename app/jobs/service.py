from hashlib import sha256
from fastapi import HTTPException
from sqlalchemy import select
from app.profiles.service import require_owner
from .models import JobSource, JobSnapshot
from .schemas import JobRead, JobSummary, SnapshotRead, SnapshotSummary

def require_source(session, owner_id, source_id, lock=False):
    query = select(JobSource).where(JobSource.owner_id == owner_id, JobSource.id == source_id)
    if lock:
        query = query.with_for_update()
    source = session.scalar(query)
    if source is None:
        raise HTTPException(404, "Job source not found")
    return source

def latest(session, source):
    return session.scalar(select(JobSnapshot).where(JobSnapshot.owner_id == source.owner_id,
        JobSnapshot.source_id == source.id).order_by(JobSnapshot.version.desc()).limit(1))

def response(session, source, full=True):
    schema = JobRead if full else JobSummary
    snapshot_schema = SnapshotRead if full else SnapshotSummary
    return schema(id=source.id, owner_id=source.owner_id, created_at=source.created_at,
                  latest=snapshot_schema.model_validate(latest(session, source)))

def snapshot(source, data, version):
    values = data.model_dump(exclude={"expected_version"})
    return JobSnapshot(owner_id=source.owner_id, source_id=source.id, version=version,
                       content_sha256=sha256(data.original_text.encode("utf-8")).hexdigest(), **values)

def create(session, owner_id, data):
    require_owner(session, owner_id)
    source = JobSource(owner_id=owner_id)
    session.add(source)
    session.flush()
    session.add(snapshot(source, data, 1))
    session.commit()
    return response(session, source)

def update(session, owner_id, source_id, data):
    source = require_source(session, owner_id, source_id, lock=True)
    current = latest(session, source)
    if current.version != data.expected_version:
        session.rollback()
        raise HTTPException(409, "A newer capture exists. Reload before saving.")
    session.add(snapshot(source, data, current.version + 1))
    session.commit()
    return response(session, source)

def list_sources(session, owner_id, limit, offset):
    require_owner(session, owner_id)
    sources = session.scalars(select(JobSource).where(JobSource.owner_id == owner_id)
        .order_by(JobSource.created_at.desc(), JobSource.id).limit(limit).offset(offset)).all()
    return [response(session, source, full=False) for source in sources]

def list_snapshots(session, owner_id, source_id, limit, offset):
    require_source(session, owner_id, source_id)
    return session.scalars(select(JobSnapshot).where(JobSnapshot.owner_id == owner_id,
        JobSnapshot.source_id == source_id).order_by(JobSnapshot.version.desc()).limit(limit).offset(offset)).all()

def read_snapshot(session, owner_id, source_id, version):
    require_source(session, owner_id, source_id)
    result = session.scalar(select(JobSnapshot).where(JobSnapshot.owner_id == owner_id,
        JobSnapshot.source_id == source_id, JobSnapshot.version == version))
    if result is None:
        raise HTTPException(404, "Capture not found")
    return result
