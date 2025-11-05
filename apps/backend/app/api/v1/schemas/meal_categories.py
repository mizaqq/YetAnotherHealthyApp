"""Pydantic models for meal categories endpoint."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class MealCategoriesQueryParams(BaseModel):
    """Query parameters accepted by the meal categories endpoint."""

    locale: Annotated[
        str,
        Field(
            default="pl-PL",
            max_length=5,
            pattern=r"^[a-z]{2}-[A-Z]{2}$",
            description="BCP 47 locale code (e.g. pl-PL)",
        ),
    ]

    model_config = ConfigDict(extra="forbid")


class MealCategoryResponseItem(BaseModel):
    """Single meal category returned by the API."""

    code: str
    label: str
    sort_order: int

    model_config = ConfigDict(extra="forbid")


class MealCategoriesResponse(BaseModel):
    """Envelope for the meal categories list response."""

    data: list[MealCategoryResponseItem]

    model_config = ConfigDict(extra="forbid")
