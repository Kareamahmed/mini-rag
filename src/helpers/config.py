from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    FILL_MAX_SIZE: int
    FILE_ALLOWED_TYPES: list
    FILE_DEFAULT_CHUNK_SIZE: int

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_MAIN_DATABASE: str

    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    GEMINI_API_KEY: str
    COHERE_API_KEY: str

    GENERATION_MODEL_ID: str
    EMBEDDING_MODEL_ID: str

    MAX_INPUT_TOKENS: int
    MAX_OUTPUT_TOKENS: int
    TEMPERATURE: float
    EMBEDDING_SIZE: int

    ## VectorDB config
    VECTOR_DB_BACKEND_lITERAL: List[str]
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DISTANCE_METRIC: str
    VECTOR_DB_PGVECT_INDEX_THRESHOLD: int

    ## template config
    PRIMARY_LANG: str
    DEFAULT_LANG: str

    model_config = SettingsConfigDict(env_file=".env")


def get_settings():
    return Settings()
