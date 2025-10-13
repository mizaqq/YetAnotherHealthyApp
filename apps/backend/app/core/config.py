from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    app_name: str = "YetAnotherHealthyApp"
    app_version: str = "0.1.0"

    class Config:
        env_file = ".env"


settings = Settings()
