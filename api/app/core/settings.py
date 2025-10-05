"""Application settings using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    env: str = "dev"
    port: int = 8000

    # API
    api_v1_prefix: str = "/api/v1"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # OpenSearch (retrieval)
    opensearch_host: str = "localhost:9200"
    opensearch_user: str = "admin"
    opensearch_password: str = "admin"
    foods_index: str = "foods"

    # Supabase (persistence)
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""

    # Cache
    cache_ttl_seconds: int = 3600


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
