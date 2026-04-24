from datetime import datetime, timedelta

from app.services.cache_service import is_cache_valid


def test_cache_is_valid_before_expiry():
    now = datetime.utcnow()
    assert is_cache_valid(now + timedelta(seconds=30), now) is True


def test_cache_is_invalid_after_expiry():
    now = datetime.utcnow()
    assert is_cache_valid(now - timedelta(seconds=1), now) is False
