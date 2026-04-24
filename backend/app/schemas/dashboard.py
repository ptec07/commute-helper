from pydantic import BaseModel

from app.schemas.provider_models import BusArrival, BusPosition, RecommendationResult, SubwayArrival
from app.schemas.profile import CommuteProfileRead


class DashboardResponse(BaseModel):
    profile: CommuteProfileRead
    bus: list[BusArrival]
    bus_positions: list[BusPosition] = []
    subway: list[SubwayArrival]
    recommendation: RecommendationResult
