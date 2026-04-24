from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CommuteStopBase(BaseModel):
    type: Literal['bus_stop', 'subway_station']
    external_id: str
    name: str
    line_name: str | None = None
    direction: str | None = None
    sort_order: int


class CommuteStopRead(CommuteStopBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class CommuteProfileCreate(BaseModel):
    name: str
    origin_label: str
    destination_label: str
    target_arrival_time: time
    preferred_mode: str = 'balanced'
    walking_tolerance_min: int = 10


class CommuteProfileRead(CommuteProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    stops: list[CommuteStopRead] = []
