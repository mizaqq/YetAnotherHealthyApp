import os
from functools import cached_property

from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TEST_PLACEHOLDER_SUPABASE_URL = "https://supabase.test.local"
TEST_PLACEHOLDER_SUPABASE_SERVICE_ROLE_KEY = "supabase-service-role-test-key"
TEST_PLACEHOLDER_OPENROUTER_API_KEY = "openrouter-test-api-key"


def get_env_files() -> tuple[str, ...]:
    """Get environment files in priority order based on APP_ENV."""
    env = os.getenv("APP_ENV", "development")

    # Base .env file is always loaded first
    files = [".env"]

    # Environment-specific overrides
    if env == "production":
        files.extend([".env.production", ".env.production.local"])
    elif env == "staging":
        files.extend([".env.staging", ".env.staging.local"])
    elif env == "test":
        files.extend([".env.test", ".env.test.local"])
    else:  # development
        files.extend([".env.development", ".env.development.local"])

    # Local overrides always loaded last
    files.append(".env.local")

    return tuple(files)


class OpenRouterConfig(BaseModel):
    """Runtime configuration for the OpenRouter API integration."""

    base_url: HttpUrl = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for OpenRouter API endpoints",
    )
    api_key: SecretStr = Field(..., description="API key used to authenticate with OpenRouter")
    default_model: str = Field(
        default="google/gemini-2.0-flash-exp:free",
        description="Default model identifier used for chat completions",
        min_length=1,
    )
    default_temperature: float = Field(
        default=0.2,
        ge=0,
        le=2,
        description="Default temperature for model sampling",
    )
    default_top_p: float = Field(
        default=0.95,
        ge=0,
        le=1,
        description="Default nucleus sampling top-p value",
    )
    max_output_tokens: int = Field(
        default=600,
        gt=0,
        description="Upper bound for tokens returned by the model",
    )
    max_input_tokens: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Optional limit enforced on outgoing prompt token budgets before hitting the API"
        ),
    )
    request_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="HTTP client timeout for OpenRouter requests",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of retry attempts for transient errors",
    )
    retry_backoff_initial: float = Field(
        default=0.5,
        gt=0,
        description="Initial delay in seconds used for exponential backoff",
    )
    retry_backoff_max: float = Field(
        default=4.0,
        gt=0,
        description="Maximum delay in seconds for exponential backoff",
    )
    http_referer: HttpUrl | None = Field(
        default=None,
        description="Optional HTTP referer header forwarded to OpenRouter",
    )
    http_title: str | None = Field(
        default=None,
        description="Optional title header forwarded to OpenRouter",
        min_length=1,
    )

    model_config = {"frozen": True}


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    app_name: str = "YetAnotherHealthyApp"
    app_version: str = "0.1.0"
    app_env: str = Field(
        default="development",
        description="Application environment (development, staging, production, test)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode with detailed logging and error pages",
        alias="DEBUG",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        alias="LOG_LEVEL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins for cross-origin requests",
        alias="CORS_ORIGINS",
    )
    supabase_url: HttpUrl = Field(
        default=TEST_PLACEHOLDER_SUPABASE_URL,
        description="Supabase project URL",
        alias="SUPABASE_URL",
    )
    supabase_service_role_key: SecretStr = Field(
        default_factory=lambda: SecretStr(TEST_PLACEHOLDER_SUPABASE_SERVICE_ROLE_KEY),
        description=(
            "Supabase service role key used for server-side operations. Keep this value secret."
        ),
        alias="SUPABASE_SERVICE_ROLE_KEY",
    )
    analysis_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="AI model identifier used for meal analysis",
    )
    openrouter_api_key: SecretStr = Field(
        default_factory=lambda: SecretStr(TEST_PLACEHOLDER_OPENROUTER_API_KEY),
        description="OpenRouter API key used by backend services",
        alias="OPENROUTER_API_KEY",
    )
    openrouter_default_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="Default OpenRouter model when none is specified",
        min_length=1,
        alias="OPENROUTER_DEFAULT_MODEL",
    )
    openrouter_default_temperature: float = Field(
        default=0.2,
        ge=0,
        le=2,
        description="Baseline temperature for OpenRouter requests",
        alias="OPENROUTER_DEFAULT_TEMPERATURE",
    )
    openrouter_default_top_p: float = Field(
        default=0.95,
        ge=0,
        le=1,
        description="Baseline nucleus sampling for OpenRouter requests",
        alias="OPENROUTER_DEFAULT_TOP_P",
    )
    openrouter_max_output_tokens: int = Field(
        default=600,
        gt=0,
        description="Maximum tokens expected in OpenRouter responses",
    )
    openrouter_max_input_tokens: int | None = Field(
        default=None,
        gt=0,
        description="Optional guardrail for request token budget",
    )
    openrouter_request_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="HTTP request timeout when calling OpenRouter",
    )
    openrouter_max_retries: int = Field(
        default=3,
        ge=0,
        description="Number of retries for transient OpenRouter errors",
    )
    openrouter_retry_backoff_initial: float = Field(
        default=2,
        gt=0,
        description="Initial delay used for exponential backoff to OpenRouter",
    )
    openrouter_retry_backoff_max: float = Field(
        default=10.0,
        gt=0,
        description="Maximum delay used for exponential backoff to OpenRouter",
    )
    openrouter_base_url: HttpUrl = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for OpenRouter REST API",
    )
    openrouter_http_referer: HttpUrl | None = Field(
        default=None,
        description="Optional referer header forwarded to OpenRouter",
    )
    openrouter_http_title: str | None = Field(
        default=None,
        description="Optional title header forwarded to OpenRouter",
        min_length=1,
    )

    model_config = SettingsConfigDict(
        env_file=get_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        populate_by_name=True,
    )

    @cached_property
    def openrouter(self) -> OpenRouterConfig:
        """Aggregate OpenRouter configuration into a typed object for consumers."""

        return OpenRouterConfig(
            base_url=self.openrouter_base_url,
            api_key=self.openrouter_api_key,
            default_model=self.openrouter_default_model,
            default_temperature=self.openrouter_default_temperature,
            default_top_p=self.openrouter_default_top_p,
            max_output_tokens=self.openrouter_max_output_tokens,
            max_input_tokens=self.openrouter_max_input_tokens,
            request_timeout_seconds=self.openrouter_request_timeout_seconds,
            max_retries=self.openrouter_max_retries,
            retry_backoff_initial=self.openrouter_retry_backoff_initial,
            retry_backoff_max=self.openrouter_retry_backoff_max,
            http_referer=self.openrouter_http_referer,
            http_title=self.openrouter_http_title,
        )

    @model_validator(mode="after")
    def ensure_runtime_secrets_present(self) -> "Settings":
        """Ensure non-test environments provide real credentials via environment variables."""

        if self.app_env == "test":
            return self

        missing: list[str] = []

        if str(self.supabase_url) == TEST_PLACEHOLDER_SUPABASE_URL:
            missing.append("SUPABASE_URL")

        if (
            self.supabase_service_role_key.get_secret_value()
            == TEST_PLACEHOLDER_SUPABASE_SERVICE_ROLE_KEY
        ):
            missing.append("SUPABASE_SERVICE_ROLE_KEY")

        if self.openrouter_api_key.get_secret_value() == TEST_PLACEHOLDER_OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY")

        if missing:
            missing_vars = ", ".join(missing)
            msg = (
                "Set the following environment variables or provide .env overrides before "
                f"starting the backend: {missing_vars}"
            )
            raise ValueError(msg)

        return self


settings = Settings()
