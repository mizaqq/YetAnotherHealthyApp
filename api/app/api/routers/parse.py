"""Parse endpoint: POST /api/v1/parse."""

from fastapi import APIRouter, status

from app.models.parse import ParsedItem, ParseRequest, ParseResponse

router = APIRouter(prefix="/parse", tags=["parse"])


@router.post(
    "",
    response_model=ParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse natural language food description",
    description="""
    Parse a natural language description of consumed foods (in Polish) into structured items.
    
    This endpoint extracts food items and normalizes quantities to grams/ml.
    Returns a clarification flag if the input is ambiguous.
    """,
)
async def parse_food_description(request: ParseRequest) -> ParseResponse:
    """Parse food description into structured items.

    Args:
        request: Parse request with text input

    Returns:
        Parsed items with normalized quantities
    """
    # Return example response for now (Step 2 - minimal implementation)
    return ParseResponse(
        items=[
            ParsedItem(
                label="jajko",
                quantity_expr="2 sztuki",
                grams=100.0,
                confidence=0.95,
            ),
            ParsedItem(
                label="kurczak",
                quantity_expr="100g",
                grams=100.0,
                confidence=1.0,
            ),
        ],
        needs_clarification=False,
    )
