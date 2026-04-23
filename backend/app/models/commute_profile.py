from __future__ import annotations

from datetime import datetime, time
from uuid import uuid4

from sqlalchemy import DateTime, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommuteProfile(Base):
    __tablename__ = 'commute_profiles'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_label: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_label: Mapped[str] = mapped_column(String(100), nullable=False)
    target_arrival_time: Mapped[time] = mapped_column(Time(), nullable=False)
    preferred_mode: Mapped[str] = mapped_column(String(20), nullable=False, default='balanced')
    walking_tolerance_min: Mapped[int] = mapped_column(nullable=False, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.preferred_mode is None:
            self.preferred_mode = 'balanced'
        if self.walking_tolerance_min is None:
            self.walking_tolerance_min = 10
