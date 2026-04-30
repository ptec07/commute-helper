import pytest

import app.models  # noqa: F401
from app.core.settings import get_settings
from app.db.base import Base
from app.db.session import engine


@pytest.fixture(autouse=True)
def isolate_test_settings(monkeypatch):
    monkeypatch.setenv('PUBLIC_DATA_SERVICE_KEY', '')
    monkeypatch.setenv('SEOUL_OPEN_API_KEY', '')
    monkeypatch.setenv('USE_LIVE_PUBLIC_DATA', 'false')
    monkeypatch.setenv('ALLOW_INSECURE_SEOUL_TRANSIT_HTTP', 'false')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        from app.services.dashboard_service import clear_live_arrival_cache

        clear_live_arrival_cache()
    except Exception:
        pass
    yield
