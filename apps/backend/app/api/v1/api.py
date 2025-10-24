from fastapi import APIRouter

from app.api.v1 import endpoints

api_router = APIRouter()
api_router.include_router(
    endpoints.analysis_runs.router,
    prefix="/analysis-runs",
    tags=["analysis-runs"],
)
api_router.include_router(endpoints.auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(endpoints.health.router, prefix="/health", tags=["health"])
api_router.include_router(
    endpoints.meal_categories.router,
    prefix="/meal-categories",
    tags=["meal-categories"],
)
api_router.include_router(endpoints.meals.router, prefix="/meals", tags=["meals"])
api_router.include_router(endpoints.products.router, prefix="/products", tags=["products"])
api_router.include_router(endpoints.profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(endpoints.reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(endpoints.units.router, prefix="/units", tags=["units"])
