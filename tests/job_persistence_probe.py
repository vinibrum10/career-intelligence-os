import os, sys
from hashlib import sha256
from sqlalchemy import select
from sqlalchemy.engine import make_url
url=make_url(os.environ["DATABASE_URL"])
if url.get_backend_name()!="postgresql" or not (url.database or "").startswith("career_profile_test_"):
    raise RuntimeError("Probe requires a dedicated test database")
from app.database import SessionFactory
from app.profiles.models import Owner
from app.jobs.models import JobSource
from app.jobs.schemas import Capture,CaptureUpdate
from app.jobs import service
LABEL="Synthetic vacancy restart probe"
RAW="  original\r\nenergia ⚡\n  "
with SessionFactory() as s:
    if sys.argv[1]=="seed":
        owner=Owner(label=LABEL); s.add(owner); s.commit()
        job=service.create(s,owner.id,Capture(label=LABEL,original_text=RAW,source_url="https://example.com/jobs/42",association_confirmed=True))
        service.update(s,owner.id,job.id,CaptureUpdate(label=LABEL,original_text="New evidence",source_url="https://example.com/jobs/43",expected_version=1))
        print("Synthetic job captures saved before restart")
    elif sys.argv[1]=="check":
        owner=s.scalar(select(Owner).where(Owner.label==LABEL))
        if owner is None: raise RuntimeError("Owner missing after restart")
        source=s.scalar(select(JobSource).where(JobSource.owner_id==owner.id))
        if source is None: raise RuntimeError("Source missing after restart")
        current=service.response(s,source).latest
        old=service.read_snapshot(s,owner.id,source.id,1)
        versions=service.list_snapshots(s,owner.id,source.id,20,0)
        if (current.version!=2 or current.original_text!="New evidence" or current.source_url!="https://example.com/jobs/43" or current.association_confirmed
            or old.original_text!=RAW or old.content_sha256!=sha256(RAW.encode("utf-8")).hexdigest()
            or old.source_url!="https://example.com/jobs/42" or not old.association_confirmed or old.captured_at is not None
            or [v.version for v in versions]!=[2,1]): raise RuntimeError("Evidence or history changed after restart")
        print("PASS: job text, provenance and history survived container restart")
    else: raise ValueError("Expected seed or check")
