from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_service import build_dashboard
from app.services.profile_store import get_profile

router = APIRouter(prefix='/api/dashboard', tags=['dashboard'])


@router.get('/{profile_id}')
def get_dashboard(profile_id: str, session: Session = Depends(get_db)):
    profile = get_profile(session, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Profile not found')
    try:
        return build_dashboard(profile)
    except OSError as exc:
        raise HTTPException(status_code=503, detail='Dashboard data unavailable') from exc
