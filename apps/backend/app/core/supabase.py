from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


@lru_cache
def get_supabase_client() -> Client:
    """Return a singleton Supabase client configured for the API service."""

    return create_client(
        str(settings.supabase_url),
        settings.supabase_service_role_key.get_secret_value(),
    )
