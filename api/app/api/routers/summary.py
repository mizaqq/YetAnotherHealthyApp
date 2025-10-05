"""Summary endpoint: GET /api/v1/summary."""

from datetime import date as DateType
from datetime import datetime

from fastapi import APIRouter, Query, status

from app.models.log import LogItemOutput, MealTotals
from app.models.summary import (
    DayTotals,
    MealSummary,
    SummaryResponse,
)

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get(
    "",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get daily summary",
    description="""
    Get a summary of all meals and totals for a specific date.
    
    Requires authentication. Returns meals ordered by time with computed totals.
    """,
)
async def get_daily_summary(
    date_param: DateType = Query(
        ...,
        alias="date",
        description="Date for summary in YYYY-MM-DD format",
        examples=["2025-10-05"],
    ),
) -> SummaryResponse:
    """Get daily meal summary.

    Args:
        date_param: Date to retrieve summary for

    Returns:
        Daily summary with meals and totals
    """
    # Return example response for now (Step 2 - minimal implementation)
    return SummaryResponse(
        date=date_param,
        totals=DayTotals(
            kcal=1850.0,
            protein_g=120.0,
            fat_g=65.0,
            carbs_g=180.0,
        ),
        meals=[
            MealSummary(
                id="meal_abc123",
                eaten_at=datetime.fromisoformat("2025-10-05T12:30:00Z"),
                note="Lunch",
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
                totals=MealTotals(
                    kcal=247.5,
                    protein_g=46.5,
                    fat_g=5.4,
                    carbs_g=0.0,
                ),
            ),
        ],
    )
