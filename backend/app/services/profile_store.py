from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop


def create_profile(session: Session, profile: CommuteProfile) -> CommuteProfile:
    if not profile.id:
        profile.id = str(uuid4())
    now = datetime.utcnow()
    if getattr(profile, 'created_at', None) is None:
        profile.created_at = now
    profile.updated_at = now
    session.add(profile)
    session.commit()
    return get_profile(session, profile.id) or profile


def list_profiles(session: Session) -> list[CommuteProfile]:
    statement = select(CommuteProfile).options(selectinload(CommuteProfile.stops)).order_by(CommuteProfile.created_at)
    return list(session.scalars(statement).all())


def get_profile(session: Session, profile_id: str) -> CommuteProfile | None:
    statement = (
        select(CommuteProfile)
        .options(selectinload(CommuteProfile.stops))
        .where(CommuteProfile.id == profile_id)
        .execution_options(populate_existing=True)
    )
    return session.scalars(statement).first()


def add_stop(session: Session, profile_id: str, stop: CommuteStop) -> CommuteStop:
    profile = get_profile(session, profile_id)
    if profile is None:
        raise KeyError(profile_id)
    stop.id = stop.id or str(uuid4())
    stop.commute_profile_id = profile.id
    session.add(stop)
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(stop)
    return stop
