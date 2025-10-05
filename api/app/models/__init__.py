"""Pydantic v2 request/response models for the API."""

from app.models.foods import FoodItem, FoodSearchResponse
from app.models.log import LogItemInput, LogItemOutput, LogRequest, LogResponse
from app.models.match import MatchItemInput, MatchItemOutput, MatchRequest, MatchResponse
from app.models.parse import ParsedItem, ParseRequest, ParseResponse
from app.models.summary import DayTotals, MealSummary, SummaryResponse

__all__ = [
    # Parse
    "ParseRequest",
    "ParseResponse",
    "ParsedItem",
    # Match
    "MatchRequest",
    "MatchResponse",
    "MatchItemInput",
    "MatchItemOutput",
    # Log
    "LogRequest",
    "LogResponse",
    "LogItemInput",
    "LogItemOutput",
    # Summary
    "SummaryResponse",
    "MealSummary",
    "DayTotals",
    # Foods
    "FoodSearchResponse",
    "FoodItem",
]
