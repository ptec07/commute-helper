from fastapi import APIRouter, HTTPException, Query

from app.services.search_service import search_stops

router = APIRouter(prefix='/api/search', tags=['search'])


@router.get('/stops')
def search_stop_catalog(q: str = Query(..., min_length=1)):
    try:
        return search_stops(q)
    except OSError as exc:
        raise HTTPException(status_code=503, detail='Search index unavailable') from exc
