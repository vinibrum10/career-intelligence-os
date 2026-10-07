from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Owner, Profile, ProfileVersion
from .schemas import OwnerCreate, OwnerRead, ProfileCreate, ProfileRead, ProfileUpdate, VersionRead


def create_owner(session: Session, data: OwnerCreate) -> OwnerRead:
    owner = Owner(label=data.label)
    session.add(owner)
    session.commit()
    return OwnerRead(id=owner.id, label=owner.label, created_at=owner.created_at)


def require_owner(session: Session, owner_id: UUID):
    if session.get(Owner, owner_id) is None:
        raise HTTPException(404, "Owner not found")


def require_profile(session: Session, owner_id: UUID, profile_id: UUID, *, lock=False):
    query = select(Profile).where(Profile.owner_id == owner_id, Profile.id == profile_id)
    if lock:
        query = query.with_for_update()
    profile = session.scalar(query)
    if profile is None:
        raise HTTPException(404, "Profile not found for this owner")
    return profile


def version_response(row: ProfileVersion) -> VersionRead:
    return VersionRead(
        id=row.id, version=row.version, schema_version=row.schema_version,
        preferences=row.preferences_json, created_at=row.created_at,
    )


def latest_version(session: Session, profile: Profile):
    return session.scalar(select(ProfileVersion).where(
        ProfileVersion.owner_id == profile.owner_id, ProfileVersion.profile_id == profile.id,
    ).order_by(ProfileVersion.version.desc()).limit(1))


def profile_response(session: Session, profile: Profile) -> ProfileRead:
    return ProfileRead(
        id=profile.id, owner_id=profile.owner_id, label=profile.label,
        created_at=profile.created_at, latest=version_response(latest_version(session, profile)),
    )


def create_profile(session: Session, owner_id: UUID, data: ProfileCreate):
    require_owner(session, owner_id)
    profile = Profile(owner_id=owner_id, label=data.label)
    session.add(profile)
    session.flush()
    session.add(ProfileVersion(
        owner_id=owner_id, profile_id=profile.id, version=1,
        preferences_json=data.preferences.model_dump(mode="json"),
    ))
    session.commit()
    return profile_response(session, profile)


def update_profile(session: Session, owner_id: UUID, profile_id: UUID, data: ProfileUpdate):
    # Short row lock serializes version allocation; stale client edits get HTTP 409.
    profile = require_profile(session, owner_id, profile_id, lock=True)
    current = latest_version(session, profile)
    if data.expected_version != current.version:
        session.rollback()
        raise HTTPException(409, "Profile changed; read the latest version before updating")
    profile.label = data.label
    session.add(ProfileVersion(
        owner_id=owner_id, profile_id=profile_id, version=current.version + 1,
        preferences_json=data.preferences.model_dump(mode="json"),
    ))
    session.commit()
    return profile_response(session, profile)


def list_profiles(session: Session, owner_id: UUID, limit: int, offset: int):
    require_owner(session, owner_id)
    profiles = session.scalars(select(Profile).where(Profile.owner_id == owner_id).order_by(
        Profile.created_at, Profile.id,
    ).limit(limit).offset(offset)).all()
    return [profile_response(session, profile) for profile in profiles]


def list_versions(session: Session, owner_id: UUID, profile_id: UUID, limit: int, offset: int):
    require_profile(session, owner_id, profile_id)
    rows = session.scalars(select(ProfileVersion).where(
        ProfileVersion.owner_id == owner_id, ProfileVersion.profile_id == profile_id,
    ).order_by(ProfileVersion.version.desc()).limit(limit).offset(offset)).all()
    return [version_response(row) for row in rows]
