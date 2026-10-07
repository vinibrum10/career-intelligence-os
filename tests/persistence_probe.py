"""Synthetic restart probe. Runs only inside career_profile_test_* databases."""
import os
import sys
from sqlalchemy.engine import make_url

url = make_url(os.environ["DATABASE_URL"])
if url.get_backend_name() != "postgresql" or not (url.database or "").startswith("career_profile_test_"):
    raise RuntimeError("Probe requires a dedicated profile test database")

from app.database import SessionFactory
from app.profiles.models import Owner, Profile
from app.profiles.schemas import ProfileCreate, ProfileUpdate
from app.profiles.service import create_profile, profile_response, update_profile, list_versions
from sqlalchemy import select

LABEL = "Synthetic restart probe"
with SessionFactory() as session:
    if sys.argv[1] == "seed":
        owner = Owner(label=LABEL)
        session.add(owner)
        session.commit()
        profile = create_profile(session, owner.id, ProfileCreate(label=LABEL, preferences={
            "current_location": {"country": "NZ", "city": "Wellington"},
            "pathways": [{"id": "local", "label": "Local synthetic pathway",
                "contracts": {"mode": "required", "values": ["employee"]}}],
        }))
        preferences = profile.latest.preferences.model_dump(mode="json")
        preferences["current_location"]["city"] = "Christchurch"
        update_profile(session, owner.id, profile.id, ProfileUpdate(
            label=LABEL, preferences=preferences, expected_version=1,
        ))
        print("Synthetic profile saved before restart")
    elif sys.argv[1] == "check":
        owner = session.scalar(select(Owner).where(Owner.label == LABEL))
        if owner is None:
            raise RuntimeError("Owner missing after restart")
        profile = session.scalar(select(Profile).where(Profile.owner_id == owner.id, Profile.label == LABEL))
        if profile is None:
            raise RuntimeError("Profile missing after restart")
        response = profile_response(session, profile)
        versions = list_versions(session, owner.id, profile.id, 100, 0)
        if (response.latest.version != 2
            or response.latest.preferences.current_location.country != "NZ"
            or response.latest.preferences.current_location.city != "Christchurch"
            or response.latest.preferences.pathways[0].contracts.values != ["employee"]
            or [entry.version for entry in versions] != [2, 1]
            or versions[1].preferences.current_location.city != "Wellington"):
            raise RuntimeError("Profile preferences or history changed after restart")
        print("PASS: profile preferences survived container restart")
    else:
        raise ValueError("Expected seed or check")
