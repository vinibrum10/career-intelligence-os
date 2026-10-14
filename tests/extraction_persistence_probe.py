import os, sys
from sqlalchemy import select
from sqlalchemy.engine import make_url
url=make_url(os.environ["DATABASE_URL"])
if url.get_backend_name()!="postgresql" or not (url.database or "").startswith("career_profile_test_"):
    raise RuntimeError("Probe requires a dedicated test database")
from app.database import SessionFactory
from app.profiles.models import Owner
from app.jobs.models import JobSource
from app.jobs.schemas import Capture
from app.jobs import service, extractions
LABEL="Synthetic extraction restart probe"
RAW="Remoto\r\nSalário: R$ 8.000\nContrato CLT ⚡\n"
def piece(text):
    start=RAW.index(text); return {"start_char":start,"end_char":start+len(text),"excerpt":text}
with SessionFactory() as s:
    if sys.argv[1]=="seed":
        owner=Owner(label=LABEL); s.add(owner); s.commit()
        job=service.create(s,owner.id,Capture(label=LABEL,original_text=RAW))
        extractions.create(s,owner.id,job.id,1,extractions.ExtractionIn(extractor="manual-v1",claims=[
            {"field_key":"work_arrangement","knowledge":"explicit","requirement":"required","value":"remote","evidence":[piece("Remoto")]},
            {"field_key":"compensation","knowledge":"explicit","value":{"minimum":"8000","currency":"BRL","currency_basis":"advertised","period":"month","amount_basis":"unknown"},"evidence":[piece("R$ 8.000")]},
            {"field_key":"contract","knowledge":"explicit","value":"employee","evidence":[piece("CLT ⚡")]},
            {"field_key":"sponsorship","knowledge":"not_provided"}]))
        print("Synthetic extraction saved before restart")
    elif sys.argv[1]=="check":
        owner=s.scalar(select(Owner).where(Owner.label==LABEL))
        if owner is None: raise RuntimeError("Owner missing after restart")
        source=s.scalar(select(JobSource).where(JobSource.owner_id==owner.id))
        snapshot=service.read_snapshot(s,owner.id,source.id,1)
        runs=s.scalars(select(extractions.ExtractionRun).where(extractions.ExtractionRun.owner_id==owner.id)).all()
        if len(runs)!=1: raise RuntimeError("Extraction run missing after restart")
        data=extractions.read(s,runs[0])
        keys=[c.field_key for c in data.claims]
        if keys!=["work_arrangement","compensation","contract","sponsorship"]: raise RuntimeError("Claims changed after restart")
        if data.claims[1].value["minimum"]!="8000" or data.claims[3].value is not None: raise RuntimeError("Claim values changed after restart")
        for claim in data.claims:
            for e in claim.evidence:
                if snapshot.original_text[e.start_char:e.end_char]!=e.excerpt: raise RuntimeError("Evidence no longer matches the saved text")
        if sum(len(c.evidence) for c in data.claims)!=3: raise RuntimeError("Evidence missing after restart")
        print("PASS: extraction claims and exact evidence survived container restart")
    else: raise ValueError("Expected seed or check")
