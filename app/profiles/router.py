from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_session
from . import service
from .schemas import OwnerCreate, OwnerRead, ProfileCreate, ProfileRead, ProfileUpdate, VersionRead

router = APIRouter(prefix="/career", tags=["Local profiles (no authentication)"])


@router.post("/owners", response_model=OwnerRead, status_code=201)
def create_owner(data: OwnerCreate, session: Session = Depends(get_session)):
    return service.create_owner(session, data)


@router.post("/owners/{owner_id}/profiles", response_model=ProfileRead, status_code=201)
def create_profile(owner_id: UUID, data: ProfileCreate, session: Session = Depends(get_session)):
    return service.create_profile(session, owner_id, data)


@router.get("/owners/{owner_id}/profiles", response_model=list[ProfileRead])
def list_profiles(owner_id: UUID, limit: int = Query(50, ge=1, le=100),
                  offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
    return service.list_profiles(session, owner_id, limit, offset)


@router.get("/owners/{owner_id}/profiles/{profile_id}", response_model=ProfileRead)
def read_profile(owner_id: UUID, profile_id: UUID, session: Session = Depends(get_session)):
    return service.profile_response(session, service.require_profile(session, owner_id, profile_id))


@router.put("/owners/{owner_id}/profiles/{profile_id}", response_model=ProfileRead)
def update_profile(owner_id: UUID, profile_id: UUID, data: ProfileUpdate,
                   session: Session = Depends(get_session)):
    return service.update_profile(session, owner_id, profile_id, data)


@router.get("/owners/{owner_id}/profiles/{profile_id}/versions", response_model=list[VersionRead])
def list_versions(owner_id: UUID, profile_id: UUID, limit: int = Query(50, ge=1, le=100),
                  offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
    return service.list_versions(session, owner_id, profile_id, limit, offset)
