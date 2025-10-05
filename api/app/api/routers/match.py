"""Match endpoint: POST /api/v1/match."""

from fastapi import APIRouter, status

from app.models.match import (
    MacrosPer100g,
    MatchItemOutput,
    MatchRequest,
    MatchResponse,
)

router = APIRouter(prefix="/match", tags=["match"])


@router.post(
    "",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Match food items to database",
    description="""
    Match parsed food items against the foods database using hybrid search (BM25 + k-NN).
    
    Returns the best matches with macronutrient information and match scores.
    """,
)
async def match_foods(request: MatchRequest) -> MatchResponse:
    """Match food items to database entries.

    Args:
        request: Match request with food labels and quantities

    Returns:
        Matched foods with macros and scores
    """
    # Return example response for now (Step 2 - minimal implementation)
    return MatchResponse(
        matches=[
            MatchItemOutput(
                label="kurczak pierś bez skóry",
                food_id="food_12345",
                source="usda",
                source_ref="05006",
                match_score=0.92,
                macros_per_100g=MacrosPer100g(
                    kcal=165.0,
                    protein_g=31.0,
                    fat_g=3.6,
                    carbs_g=0.0,
                ),
            ),
        ],
    )
