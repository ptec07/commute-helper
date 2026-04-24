from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop

PROFILES: dict[str, CommuteProfile] = {}


def create_profile(profile: CommuteProfile) -> CommuteProfile:
    if not profile.id:
        profile.id = str(uuid4())
    now = datetime.utcnow()
    if getattr(profile, 'created_at', None) is None:
        profile.created_at = now
    profile.updated_at = now
    PROFILES[profile.id] = profile
    return profile


def list_profiles() -> list[CommuteProfile]:
    return list(PROFILES.values())


def get_profile(profile_id: str) -> CommuteProfile | None:
    return PROFILES.get(profile_id)


def add_stop(profile_id: str, stop: CommuteStop) -> CommuteStop:
    profile = PROFILES[profile_id]
    stop.id = stop.id or str(uuid4())
    stop.commute_profile = profile
    profile.updated_at = datetime.utcnow()
    return stop
