from fastapi import APIRouter, HTTPException, status

from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop
from app.schemas.profile import CommuteProfileCreate, CommuteProfileRead, CommuteStopBase, CommuteStopRead
from app.services.profile_store import add_stop, create_profile, get_profile, list_profiles

router = APIRouter(prefix='/api/commute-profiles', tags=['commute-profiles'])


@router.post('', response_model=CommuteProfileRead, status_code=status.HTTP_201_CREATED)
def create_commute_profile(payload: CommuteProfileCreate) -> CommuteProfileRead:
    profile = CommuteProfile(**payload.model_dump())
    stored = create_profile(profile)
    return CommuteProfileRead.model_validate(stored)


@router.get('', response_model=list[CommuteProfileRead])
def list_commute_profiles() -> list[CommuteProfileRead]:
    return [CommuteProfileRead.model_validate(item) for item in list_profiles()]


@router.post('/{profile_id}/stops', response_model=CommuteStopRead, status_code=status.HTTP_201_CREATED)
def create_commute_stop(profile_id: str, payload: CommuteStopBase) -> CommuteStopRead:
    if get_profile(profile_id) is None:
        raise HTTPException(status_code=404, detail='Profile not found')
    stop = CommuteStop(**payload.model_dump())
    stored = add_stop(profile_id, stop)
    return CommuteStopRead.model_validate(stored)
