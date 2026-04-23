from datetime import datetime, time

from pydantic import BaseModel, ConfigDict


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
