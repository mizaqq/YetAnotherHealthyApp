"""Offline evaluation harness for the OpenRouter analysis pipeline.

This script reads a CSV file with reference meals (name, ingredients, macros)
and benchmarks the YetAnotherHealthyApp analysis pipeline powered by
`AnalysisRunProcessor`/`OpenRouterService`. For each meal, it:

1. Builds the same chat prompt used in production (`AnalysisRunProcessor`).
2. Calls OpenRouter to analyse the meal description.
3. Parses the structured JSON response into `AnalysisItem` instances.
4. Aggregates predicted macros and compares them with the reference values.
5. Reports per-meal deltas alongside aggregate error metrics (MAE / MAPE).

Requirements:
- OPENROUTER_API_KEY must be set in the environment.
- Optional overrides via CLI flags (model, temperature, etc.).

Usage::

    poetry run python -m apps.backend.scripts.evaluate_analysis_model \
        --csv /path/to/dania_20_z_makro_mikro.csv

The script executes requests sequentially (20 meals) to avoid exhausting
rate limits; expect a few minutes to complete depending on model latency.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import dataclasses
import logging
import math
import os
from decimal import Decimal
from pathlib import Path
from statistics import mean
from typing import Any
from uuid import uuid4

from pydantic import SecretStr

from app.core.config import OpenRouterConfig
from app.services.analysis_processor import AnalysisRunProcessor
from app.services.openrouter_client import OpenRouterClient
from app.services.openrouter_service import OpenRouterService, ServiceDataError

logger = logging.getLogger("evaluate_model")


# ---------------------------------------------------------------------------
# Support data structures


@dataclasses.dataclass(slots=True)
class MacroTotals:
    calories: Decimal
    protein: Decimal
    fat: Decimal
    carbs: Decimal

    @classmethod
    def zero(cls) -> MacroTotals:
        zero = Decimal("0")
        return cls(zero, zero, zero, zero)


@dataclasses.dataclass(slots=True)
class MealExample:
    name: str
    ingredients: str
    reference_macros: MacroTotals


@dataclasses.dataclass(slots=True)
class MealEvaluation:
    meal: MealExample
    predicted_macros: MacroTotals | None
    absolute_error: MacroTotals | None
    percentage_error: MacroTotals | None
    raw_items: list[dict[str, Any]] | None
    error: str | None = None


# ---------------------------------------------------------------------------
# Minimal stubs to satisfy AnalysisRunProcessor dependencies


class _NoopAnalysisRepository:
    async def update_status(self, **_: Any) -> None:  # pragma: no cover - no-op
        return None

    async def complete_run(self, **kwargs: Any) -> dict[str, Any]:  # pragma: no cover
        return kwargs


class _NoopItemsRepository:
    async def insert_item(self, **_: Any) -> None:  # pragma: no cover - no-op
        return None

    async def list_items(self, **_: Any) -> list[dict[str, Any]]:  # pragma: no cover
        return []


class _StubProductRepository:
    """Stub repository that avoids database lookups during evaluation."""

    def list_products(self, **_: Any) -> list[Any]:  # pragma: no cover - no DB
        # Return empty list so product lookup always fails gracefully
        return []

    def get_product_by_id(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        return None


@dataclasses.dataclass(slots=True)
class _InlineSettings:
    openrouter: OpenRouterConfig


# ---------------------------------------------------------------------------
# CSV ingestion helpers


def _decimal_from_csv(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except Exception as exc:  # pragma: no cover - defensive parsing
        raise ValueError(f"Invalid decimal value '{value}'") from exc


def load_meal_dataset(csv_path: Path) -> list[MealExample]:
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_columns = {
            "Nazwa",
            "Składniki (g)",
            "Kcal",
            "Białko (g)",
            "Tłuszcz (g)",
            "Węglowodany (g)",
        }
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")

        meals: list[MealExample] = []
        for row in reader:
            if not row.get("Nazwa"):
                continue
            macros = MacroTotals(
                calories=_decimal_from_csv(row["Kcal"]),
                protein=_decimal_from_csv(row["Białko (g)"]),
                fat=_decimal_from_csv(row["Tłuszcz (g)"]),
                carbs=_decimal_from_csv(row["Węglowodany (g)"]),
            )
            meals.append(
                MealExample(
                    name=row["Nazwa"].strip(),
                    ingredients=row["Składniki (g)"].strip(),
                    reference_macros=macros,
                )
            )

    if not meals:
        raise ValueError("Dataset is empty")

    return meals


# ---------------------------------------------------------------------------
# Evaluation core


def aggregate_macros(items: list[Any]) -> MacroTotals:
    total = MacroTotals.zero()
    for item in items:
        macros = item.macros
        total = MacroTotals(
            calories=total.calories + macros.calories,
            protein=total.protein + macros.protein,
            fat=total.fat + macros.fat,
            carbs=total.carbs + macros.carbs,
        )
    return total


def compute_absolute_error(actual: MacroTotals, predicted: MacroTotals) -> MacroTotals:
    return MacroTotals(
        calories=(predicted.calories - actual.calories).copy_abs(),
        protein=(predicted.protein - actual.protein).copy_abs(),
        fat=(predicted.fat - actual.fat).copy_abs(),
        carbs=(predicted.carbs - actual.carbs).copy_abs(),
    )


def compute_percentage_error(actual: MacroTotals, predicted: MacroTotals) -> MacroTotals:
    def pct(a: Decimal, p: Decimal) -> Decimal:
        if a == 0:
            return Decimal("0") if p == 0 else Decimal("NaN")
        return ((p - a) / a * Decimal("100")).quantize(Decimal("0.01"))

    return MacroTotals(
        calories=pct(actual.calories, predicted.calories),
        protein=pct(actual.protein, predicted.protein),
        fat=pct(actual.fat, predicted.fat),
        carbs=pct(actual.carbs, predicted.carbs),
    )


async def evaluate_meal(
    processor: AnalysisRunProcessor,
    meal: MealExample,
    *,
    threshold: Decimal,
    model_metadata: dict[str, Any],
) -> MealEvaluation:
    raw_input = {
        "text": (
            f"Meal: {meal.name}.\n"
            f"Ingredients (with gram weights): {meal.ingredients}.\n"
            "Return detailed ingredient breakdown with macros for the entire meal."
        )
    }

    try:
        response = await processor._run_openrouter_analysis(  # pylint: disable=protected-access
            run_id=uuid4(),
            user_id=uuid4(),
            raw_input=raw_input,
            threshold=threshold,
        )
    except ServiceDataError as exc:
        return MealEvaluation(
            meal=meal,
            predicted_macros=None,
            absolute_error=None,
            percentage_error=None,
            raw_items=None,
            error=f"Model response error: {exc}",
        )
    except Exception as exc:  # pragma: no cover - network fail
        return MealEvaluation(
            meal=meal,
            predicted_macros=None,
            absolute_error=None,
            percentage_error=None,
            raw_items=None,
            error=f"Unexpected failure: {exc}",
        )

    items = response["items"]
    totals = aggregate_macros(items)
    absolute_error = compute_absolute_error(meal.reference_macros, totals)
    percentage_error = compute_percentage_error(meal.reference_macros, totals)

    # Serialize analysis items for debugging / reporting
    raw_items = [
        {
            "ingredient": item.ingredient_name,
            "grams": float(item.amount_grams),
            "calories": float(item.macros.calories),
            "protein": float(item.macros.protein),
            "fat": float(item.macros.fat),
            "carbs": float(item.macros.carbs),
        }
        for item in items
    ]

    result = MealEvaluation(
        meal=meal,
        predicted_macros=totals,
        absolute_error=absolute_error,
        percentage_error=percentage_error,
        raw_items=raw_items,
        error=None,
    )

    logger.debug(
        "meal_evaluated",
        extra={
            "meal": meal.name,
            "model": model_metadata,
            "calories_diff": float(absolute_error.calories),
        },
    )

    return result


def summarize(results: list[MealEvaluation]) -> dict[str, Any]:
    successful = [r for r in results if r.error is None]
    if not successful:
        return {"success_count": 0, "errors": [r.error for r in results if r.error]}

    def _macro_series(selector: str) -> list[Decimal]:
        return [getattr(result.absolute_error, selector) for result in successful]

    def _mape(selector: str) -> list[Decimal]:
        values: list[Decimal] = []
        for result in successful:
            pct = getattr(result.percentage_error, selector)
            if math.isnan(float(pct)):
                continue
            values.append(pct.copy_abs())
        return values

    return {
        "success_count": len(successful),
        "failure_count": len(results) - len(successful),
        "mae": {
            key: float(mean(_macro_series(key))) for key in ("calories", "protein", "fat", "carbs")
        },
        "mape": {
            key: float(mean(_mape(key))) if _mape(key) else None
            for key in ("calories", "protein", "fat", "carbs")
        },
        "errors": [r.error for r in results if r.error],
    }


# ---------------------------------------------------------------------------
# CLI / entrypoint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate OpenRouter meal analysis accuracy")
    parser.add_argument("--csv", type=Path, required=True, help="Path to reference dataset CSV")
    parser.add_argument(
        "--threshold", type=float, default=0.8, help="Confidence fallback for missing scores"
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Override OpenRouter model identifier"
    )
    parser.add_argument("--max", type=int, default=None, help="Limit number of meals evaluated")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level (INFO/DEBUG)")
    return parser


def load_openrouter_config(args: argparse.Namespace) -> OpenRouterConfig:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY environment variable is required")

    base_kwargs: dict[str, Any] = {}
    if args.model:
        base_kwargs["default_model"] = args.model

    optional_env = {
        "base_url": os.environ.get("OPENROUTER_BASE_URL"),
        "default_temperature": os.environ.get("OPENROUTER_TEMPERATURE"),
        "default_top_p": os.environ.get("OPENROUTER_TOP_P"),
        "max_output_tokens": os.environ.get("OPENROUTER_MAX_OUTPUT_TOKENS"),
        "max_input_tokens": os.environ.get("OPENROUTER_MAX_INPUT_TOKENS"),
        "request_timeout_seconds": os.environ.get("OPENROUTER_TIMEOUT"),
    }

    for key, value in optional_env.items():
        if value is None:
            continue
        if key.endswith("tokens") or key == "max_input_tokens":
            base_kwargs[key] = int(value)
        elif key in {"default_temperature", "default_top_p", "request_timeout_seconds"}:
            base_kwargs[key] = float(value)
        else:
            base_kwargs[key] = value

    return OpenRouterConfig(api_key=SecretStr(api_key), **base_kwargs)


async def run(args: argparse.Namespace) -> int:
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    meals = load_meal_dataset(args.csv.resolve())
    if args.max:
        meals = meals[: args.max]

    config = load_openrouter_config(args)
    settings = _InlineSettings(openrouter=config)

    client = OpenRouterClient(config)
    product_repo = _StubProductRepository()
    processor = AnalysisRunProcessor(
        repository=_NoopAnalysisRepository(),
        items_repository=_NoopItemsRepository(),
        product_repository=product_repo,
        openrouter_service=OpenRouterService(settings, client, product_repo),
    )

    threshold = Decimal(str(args.threshold))
    logger.info("Evaluating %s meals using model %s", len(meals), config.default_model)

    results: list[MealEvaluation] = []
    for idx, meal in enumerate(meals, start=1):
        logger.info("[%02d/%02d] Evaluating '%s'", idx, len(meals), meal.name)
        evaluation = await evaluate_meal(
            processor,
            meal,
            threshold=threshold,
            model_metadata={"model": config.default_model},
        )
        results.append(evaluation)

    summary = summarize(results)

    print("\n=== Evaluation Summary ===")
    print(f"Successful evaluations: {summary['success_count']}")
    print(f"Failed evaluations    : {summary['failure_count']}")
    if summary.get("mae"):
        print("\nMean Absolute Error (macros):")
        for macro, value in summary["mae"].items():
            print(f"  {macro:<9}: {value:.2f}")
    if summary.get("mape"):
        print("\nMean Absolute Percentage Error (macros):")
        for macro, value in summary["mape"].items():
            if value is None:
                print(f"  {macro:<9}: n/a")
            else:
                print(f"  {macro:<9}: {value:.2f}%")

    if summary.get("errors"):
        print("\nErrors encountered:")
        for err in summary["errors"]:
            print(f"  - {err}")

    await client.aclose()
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        exit_code = asyncio.run(run(args))
    except KeyboardInterrupt:  # pragma: no cover - CLI behaviour
        exit_code = 130
    raise SystemExit(exit_code)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
