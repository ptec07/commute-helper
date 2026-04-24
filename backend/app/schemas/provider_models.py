from pydantic import BaseModel, computed_field


class BusArrival(BaseModel):
    route_id: str
    route_name: str
    stop_id: str
    stop_name: str
    arrival_in_sec: int
    arrival_message: str
    is_last_bus: bool

    @computed_field  # type: ignore[misc]
    @property
    def arrival_in_min(self) -> int:
        return max(0, self.arrival_in_sec // 60)


class BusPosition(BaseModel):
    route_id: str
    vehicle_id: str
    station_count_from_target: int
    congestion_level: str | None = None


class SubwayArrival(BaseModel):
    station_id: str
    station_name: str
    line_name: str
    direction: str
    arrival_in_sec: int
    train_type: str

    @computed_field  # type: ignore[misc]
    @property
    def arrival_in_min(self) -> int:
        return max(0, self.arrival_in_sec // 60)


class RecommendationResult(BaseModel):
    mode: str
    message: str
    reason: str
    leave_by: str | None = None
