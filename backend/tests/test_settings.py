from app.core.settings import get_settings


def test_default_settings_use_sqlite_for_dev():
    settings = get_settings()
    assert settings.app_name == '출근도우미'
    assert settings.database_url.startswith('sqlite')


def test_test_suite_defaults_to_fixture_mode_even_if_local_env_enables_live_data():
    settings = get_settings()
    assert settings.use_live_public_data is False
    assert settings.allow_insecure_seoul_transit_http is False
