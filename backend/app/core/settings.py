from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = '출근도우미'
    database_url: str = 'sqlite:///./commute_helper.db'
    odsay_api_key: str = ''
    public_data_service_key: str = ''
    seoul_open_api_key: str = ''
    use_live_public_data: bool = False
    allow_insecure_seoul_transit_http: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
