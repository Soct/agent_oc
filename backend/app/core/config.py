from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration injectée par variables d'environnement."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FFE Opening Coach"
    app_env: str = "development"
    cors_origins: str = "http://localhost:4200,http://localhost"
    lichess_base_url: str = "https://explorer.lichess.org"
    lichess_api_token: str = ""
    external_api_timeout_seconds: float = 8.0
    stockfish_path: str = "/usr/games/stockfish"
    stockfish_depth: int = 12
    youtube_api_key: str = ""
    youtube_max_results: int = 4
    mongodb_url: str = "mongodb://mongodb:27017"
    mongodb_database: str = "ffe_opening_coach"
    milvus_uri: str = "http://milvus:19530"
    milvus_collection: str = "opening_chunks"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = Field(default=384, ge=8)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
