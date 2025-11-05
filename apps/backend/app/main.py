import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.supabase import get_supabase_client


def create_application() -> FastAPI:
    # Configure logging level based on settings
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    application = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        debug=settings.debug,
    )

    # Configure CORS with environment-specific origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.state.supabase = get_supabase_client()
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    print(f"Settings: {settings}")
    print(f"CORS origins: {settings.cors_origins}")
    print(f"API v1 prefix: {settings.api_v1_prefix}")
    print(f"App name: {settings.app_name}")
    print(f"App version: {settings.app_version}")
    print(f"Debug: {settings.debug}")
    print(f"Log level: {settings.log_level}")
    print(f"Supabase URL: {settings.supabase_url}")
    print(f"Supabase service role key: {settings.supabase_service_role_key}")
    print(f"OpenRouter API key: {settings.openrouter_api_key}")
    print(f"Environment: {settings.app_env}")
    return application


app = create_application()
