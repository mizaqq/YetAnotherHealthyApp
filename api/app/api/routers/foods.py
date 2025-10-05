"""Foods endpoint: GET /api/v1/foods/search."""

from fastapi import APIRouter, Query, status

from app.models.foods import FoodItem, FoodSearchResponse
from app.models.match import MacrosPer100g

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get(
    "/search",
    response_model=FoodSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search foods",
    description="""
    Search for foods in the database by name.
    
    Useful for autocomplete and manual food selection.
    Authentication is optional.
    """,
)
async def search_foods(
    q: str = Query(
        ...,
        description="Search query for food name",
        min_length=1,
        max_length=100,
        examples=["kurczak"],
    ),
    limit: int = Query(
        10,
        description="Maximum number of results to return",
        ge=1,
        le=50,
    ),
) -> FoodSearchResponse:
    """Search for foods in the database.

    Args:
        q: Search query string
        limit: Maximum number of results

    Returns:
        List of matching foods with macros
    """
    # Return example response for now (Step 2 - minimal implementation)
    return FoodSearchResponse(
        results=[
            FoodItem(
                id="food_12345",
                name="Kurczak pierś bez skóry",
                brand=None,
                source="usda",
                macros_per_100g=MacrosPer100g(
                    kcal=165.0,
                    protein_g=31.0,
                    fat_g=3.6,
                    carbs_g=0.0,
                ),
            ),
        ],
        total=1,
    )
