from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    app_name: str = "YetAnotherHealthyApp"
    app_version: str = "0.1.0"
    supabase_url: HttpUrl = Field(..., description="Supabase project URL")
    supabase_service_role_key: SecretStr = Field(
        ...,
        description=(
            "Supabase service role key used for server-side operations. Keep this value secret."
        ),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
