from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    FILL_MAX_SIZE: int
    FILE_ALLOWED_TYPES: list
    FILE_DEFAULT_CHUNK_SIZE: int

    MONGO_URL: str
    MONGODB_DATABASE: str

    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    GEMINI_API_KEY: str
    COHERE_API_KEY: str

    GENERATION_MODEL_ID: str
    EMBEDDING_MODEL_ID: str

    model_config = SettingsConfigDict(env_file=".env")


def get_settings():
    return Settings()
