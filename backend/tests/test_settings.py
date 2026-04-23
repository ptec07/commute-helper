from app.core.settings import get_settings


def test_default_settings_use_sqlite_for_dev():
    settings = get_settings()
    assert settings.app_name == '출근도우미'
    assert settings.database_url.startswith('sqlite')
