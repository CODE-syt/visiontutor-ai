"""
Centralized application configuration.

All environment-driven settings live here so the rest of the codebase
never reads os.environ directly. This keeps provider swaps, RAG toggles,
and security limits in one auditable place.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # AI provider
    ai_provider: str = "openai"          # openai | gemini | qwen | llava
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_base_url: str = ""
    ai_timeout: int = 60

    # RAG
    enable_rag: bool = True
    knowledge_base_dir: str = "../knowledge_base"
    vector_index_path: str = "./app/rag/index.faiss"
    embedding_model: str = "text-embedding-3-small"

    # History / DB
    enable_history: bool = False
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "visiontutor"

    # App / security
    max_upload_mb: int = 8
    allowed_origins: str = "http://localhost:5173"
    rate_limit_per_minute: int = 20

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
