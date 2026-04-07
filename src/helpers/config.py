from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    
    FILL_MAX_SIZE: int
    FILE_ALLOWED_TYPES: list
    FILE_DEFAULT_CHUNK_SIZE:int


    model_config = SettingsConfigDict(env_file=".env")


def get_settings():
    return Settings()
