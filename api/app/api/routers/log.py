"""Log endpoint: POST /api/v1/log."""

from fastapi import APIRouter, status

from app.models.log import (
    LogItemOutput,
    LogRequest,
    LogResponse,
    MealTotals,
)

router = APIRouter(prefix="/log", tags=["log"])


@router.post(
    "",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a meal",
    description="""
    Log a consumed meal with food items and quantities.
    
    Requires authentication. Computes and returns total macros for the meal.
    """,
)
async def log_meal(request: LogRequest) -> LogResponse:
    """Log a meal to the database.

    Args:
        request: Log request with meal details and items

    Returns:
        Logged meal with computed totals
    """
    # Return example response for now (Step 2 - minimal implementation)
    return LogResponse(
        meal_id="meal_abc123",
        totals=MealTotals(
            kcal=247.5,
            protein_g=46.5,
            fat_g=5.4,
            carbs_g=0.0,
        ),
        items=[
            LogItemOutput(
                food_id="food_12345",
                label="kurczak pierś",
                grams=150.0,
                macros=MealTotals(
                    kcal=247.5,
                    protein_g=46.5,
                    fat_g=5.4,
                    carbs_g=0.0,
                ),
            ),
        ],
    )
