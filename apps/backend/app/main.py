from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.supabase import get_supabase_client


def create_application() -> FastAPI:
    application = FastAPI(title="YetAnotherHealthyApp API", version="0.1.0")
    # Allow Vite dev server and same-origin during development
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.state.supabase = get_supabase_client()
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_application()
