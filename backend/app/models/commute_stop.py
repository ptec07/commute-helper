from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

SUPPORTED_STOP_TYPES = {'bus_stop', 'subway_station'}


class CommuteStop(Base):
    __tablename__ = 'commute_stops'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    commute_profile_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey('commute_profiles.id'), nullable=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    line_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=datetime.utcnow)

    commute_profile: Mapped['CommuteProfile | None'] = relationship(back_populates='stops')

    @validates('type')
    def validate_type(self, _: str, value: str) -> str:
        if value not in SUPPORTED_STOP_TYPES:
            raise ValueError(f'Unsupported commute stop type: {value}')
        return value
