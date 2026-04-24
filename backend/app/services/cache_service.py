from __future__ import annotations

from datetime import datetime


def is_cache_valid(expires_at: datetime, now: datetime | None = None) -> bool:
    reference = now or datetime.utcnow()
    return expires_at > reference
