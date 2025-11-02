"""Analysis processor that integrates OpenRouter with graceful fallbacks."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence  # type: ignore[TCH003]
from decimal import Decimal
from time import perf_counter
from typing import TYPE_CHECKING, Any
from uuid import UUID  # type: ignore[TCH003]

from app.schemas.openrouter import ChatRole, OpenRouterChatMessage
from app.services.openrouter_service import (
    AnalysisItem,
    IngredientVerificationResult,
    MacroProfile,
    OpenRouterService,
    OpenRouterServiceError,
    ServiceDataError,
)

if TYPE_CHECKING:
    from app.db.repositories.analysis_run_items_repository import (
        AnalysisRunItemsRepository,
    )
    from app.db.repositories.analysis_runs_repository import AnalysisRunsRepository
    from app.db.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Jesteś dietetycznym asystentem YetAnotherHealthyApp. "
    "Analizujesz posiłki użytkowników, zwracasz listę składników z gramaturą "
    "oraz zawartością kalorii, białka, tłuszczu i węglowodanów. "
    "WAŻNE: Nazwy składników (ingredient_name) ZAWSZE podawaj w języku angielskim. "
    "Bądź BARDZO SZCZEGÓŁOWY w opisach składników - uwzględniaj metodę "
    "przygotowania i stan (np. 'egg, fried', 'chicken breast, raw', "
    "'rice, cooked', 'milk, whole'). "
    "NIE zwracaj product_id - będzie on wyszukany automatycznie w bazie danych."
)

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "meal_analysis_payload",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "ingredient_name": {"type": "string", "minLength": 2},
                            "amount_grams": {
                                "type": "number",
                                "exclusiveMinimum": 0,
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "macros": {
                                "type": "object",
                                "properties": {
                                    "calories": {"type": "number", "minimum": 0},
                                    "protein": {"type": "number", "minimum": 0},
                                    "fat": {"type": "number", "minimum": 0},
                                    "carbs": {"type": "number", "minimum": 0},
                                },
                                "required": ["calories", "protein", "fat", "carbs"],
                                "additionalProperties": False,
                            },
                        },
                        "required": ["ingredient_name", "amount_grams", "macros"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["items"],
            "additionalProperties": False,
        },
    },
}


class AnalysisRunProcessor:
    """Processes analysis runs using OpenRouter with a deterministic fallback."""

    def __init__(
        self,
        repository: AnalysisRunsRepository,
        items_repository: AnalysisRunItemsRepository,
        product_repository: ProductRepository,
        *,
        openrouter_service: OpenRouterService | None = None,
    ) -> None:
        self._repository = repository
        self._items_repository = items_repository
        self._product_repository = product_repository
        self._openrouter_service = openrouter_service

    async def process(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        meal_id: UUID | None,
        raw_input: dict[str, Any],
        threshold: Decimal,
    ) -> dict[str, Any]:
        start_time = perf_counter()
        await self._repository.update_status(
            run_id=run_id,
            user_id=user_id,
            status="running",
        )

        logger.info(
            "analysis_run.processing",
            extra={
                "run_id": str(run_id),
                "user_id": str(user_id),
                "meal_id": str(meal_id) if meal_id else None,
            },
        )

        try:
            if self._openrouter_service and raw_input.get("text"):
                response = await self._run_openrouter_analysis(
                    run_id=run_id,
                    user_id=user_id,
                    raw_input=raw_input,
                    threshold=threshold,
                )
                analysis_items = response["items"]
                verification = response["verification"]
                usage = response["usage"]
                model_payload = response["model_payload"]
                model_name = response["model_name"]
            else:
                raise ServiceDataError("Text input required for analysis")

            await self._create_items(
                run_id=run_id,
                user_id=user_id,
                ingredients=analysis_items,
            )

            latency_ms = int((perf_counter() - start_time) * 1000)
            tokens_used = usage.get("total_tokens", 0) if usage else 0

            raw_output = {
                "model": model_name,
                "usage": usage,
                "items": [self._serialize_analysis_item(item) for item in analysis_items],
                "verification": [self._serialize_verification(result) for result in verification],
                "raw_model_payload": model_payload,
            }

            final_run = await self._repository.complete_run(
                run_id=run_id,
                user_id=user_id,
                status="succeeded",
                latency_ms=latency_ms,
                tokens=tokens_used,
                cost_minor_units=0,
                cost_currency="USD",
                raw_output=raw_output,
            )

            logger.info(
                "analysis_run.completed",
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                    "items": len(analysis_items),
                    "latency_ms": latency_ms,
                    "model": model_name,
                },
            )

            return final_run

        except (OpenRouterServiceError, ServiceDataError) as exc:
            logger.warning(
                "analysis_run.failed_openrouter",
                exc_info=True,
                extra={"run_id": str(run_id), "user_id": str(user_id)},
            )
            return await self._fail_run(
                run_id=run_id,
                user_id=user_id,
                start_time=start_time,
                error_code=exc.error_code
                if isinstance(exc, OpenRouterServiceError)
                else "external_data_error",
                error_message=str(exc),
            )
        except Exception as exc:  # pragma: no cover - unexpected failure path
            logger.exception(
                "analysis_run.failed_unexpected",
                extra={"run_id": str(run_id), "user_id": str(user_id)},
            )
            return await self._fail_run(
                run_id=run_id,
                user_id=user_id,
                start_time=start_time,
                error_code="PROCESSING_ERROR",
                error_message=str(exc),
            )

    async def _run_openrouter_analysis(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        raw_input: dict[str, Any],
        threshold: Decimal,
    ) -> dict[str, Any]:
        messages = self._build_messages(raw_input)
        metadata = {"run_id": str(run_id)}

        response = await self._openrouter_service.generate_chat_completion(
            messages=messages,
            user_id=user_id,
            response_format=RESPONSE_FORMAT,
            metadata=metadata,
        )

        if not response.choices:
            raise ServiceDataError("OpenRouter returned no choices")

        content = response.choices[0].message.content

        # Log the raw model response for debugging (even if empty)
        logger.info(
            "analysis_run.model_response",
            extra={
                "run_id": str(run_id),
                "content": content,
                "content_type": type(content).__name__,
                "content_length": len(content) if content else 0,
            },
        )

        if not content:
            raise ServiceDataError("OpenRouter returned empty content")

        logger.info("Model content: %s", content)
        parsed_items, payload = self._parse_model_content(content, threshold)
        verification = await self._openrouter_service.verify_ingredients_calories(parsed_items)

        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        }

        return {
            "items": parsed_items,
            "verification": verification,
            "usage": usage,
            "model_payload": payload,
            "model_name": response.model,
        }

    def _build_messages(self, raw_input: dict[str, Any]) -> Sequence[OpenRouterChatMessage]:
        prompt_parts = ["Opis posiłku:"]
        if text := raw_input.get("text"):
            prompt_parts.append(text.strip())
        else:
            prompt_parts.append(
                "Brak opisu tekstowego. Użyj najlepszej heurystyki na "
                "podstawie historii użytkownika."
            )

        prompt_parts.append(
            "Zwróć pola: ingredient_name, amount_grams, confidence (0-1), "
            "product_id (jeśli znasz UUID produktu), oraz makra (calories, "
            "protein, fat, carbs). Wszystkie wartości liczbowo w jednostkach "
            "metrycznych."
        )

        return [
            OpenRouterChatMessage(role=ChatRole.SYSTEM, content=SYSTEM_PROMPT),
            OpenRouterChatMessage(role=ChatRole.USER, content="\n".join(prompt_parts)),
        ]

    def _parse_model_content(
        self,
        content: str,
        threshold: Decimal,
    ) -> tuple[list[AnalysisItem], dict[str, Any]]:
        # Log the raw content
        print("=== MODEL RESPONSE START ===")
        print(content)
        print("=== MODEL RESPONSE END ===")
        logger.info("Parsing model response of length: %d", len(content))

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON. Content: %s", content[:500])
            raise ServiceDataError("Model response is not valid JSON") from exc

        # Handle both formats: direct list or object with "items" key
        if isinstance(payload, list):
            logger.info("Model returned direct list format")
            items_data = payload
            # Wrap in dict for consistency
            payload = {"items": items_data}
        elif isinstance(payload, dict):
            items_data = payload.get("items")
            if not isinstance(items_data, list):
                logger.error("Model response payload: %s", payload)
                raise ServiceDataError("Model response missing 'items' list")
        else:
            logger.error("Model response is neither list nor dict: %s", type(payload))
            raise ServiceDataError("Model response has unexpected format")

        if not items_data:
            raise ServiceDataError("Model response has empty items list")

        results: list[AnalysisItem] = []
        for entry in items_data:
            try:
                ingredient_name = str(entry["ingredient_name"]).strip()
                amount = self._to_decimal(entry["amount_grams"])
                confidence_value = entry.get("confidence")
                confidence = (
                    self._to_decimal(confidence_value)
                    if confidence_value is not None
                    else threshold
                )

                # Handle both formats: nested macros object or flat structure
                if "macros" in entry:
                    # Nested format: {"macros": {"calories": ..., "protein": ...}}
                    macros_data = entry["macros"]
                    macros = MacroProfile(
                        calories=self._to_decimal(macros_data["calories"]),
                        protein=self._to_decimal(macros_data["protein"]),
                        carbs=self._to_decimal(macros_data["carbs"]),
                        fat=self._to_decimal(macros_data["fat"]),
                    )
                else:
                    # Flat format: {"calories": ..., "protein": ...}
                    macros = MacroProfile(
                        calories=self._to_decimal(entry["calories"]),
                        protein=self._to_decimal(entry["protein"]),
                        carbs=self._to_decimal(entry["carbs"]),
                        fat=self._to_decimal(entry["fat"]),
                    )

                # Ignore product_id from model - we'll look it up in the database
                product_uuid = None

            except (KeyError, TypeError, ValueError) as exc:
                logger.error("Failed to parse item: %s. Error: %s", entry, exc)
                raise ServiceDataError("Model response contains invalid item") from exc

            results.append(
                AnalysisItem(
                    ingredient_name=ingredient_name,
                    amount_grams=amount,
                    macros=macros,
                    product_id=product_uuid,
                    confidence=confidence,
                )
            )

        return results, payload

    async def _create_items(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        ingredients: Sequence[AnalysisItem],
    ) -> None:
        for idx, ingredient in enumerate(ingredients, start=1):
            confidence = ingredient.confidence or Decimal("0")

            # Look up product in database by ingredient name
            product_data = await self._lookup_product_by_name(ingredient.ingredient_name)

            if product_data:
                # Use database macros when product is matched
                product_id = product_data["id"]
                macros = product_data["macros"]

                # Scale macros from 100g to actual amount
                scale_factor = ingredient.amount_grams / Decimal("100")
                protein_g = macros["protein"] * scale_factor
                carbs_g = macros["carbs"] * scale_factor
                fat_g = macros["fat"] * scale_factor
                calories_kcal = macros["calories"] * scale_factor

                print(
                    f"Using database macros for '{ingredient.ingredient_name}' "
                    f"({ingredient.amount_grams}g):"
                )
                print(f"  Calories: {calories_kcal} (DB: {macros['calories']}/100g)")
                print(f"  Protein: {protein_g}g (DB: {macros['protein']}/100g)")
                print(f"  Carbs: {carbs_g}g (DB: {macros['carbs']}/100g)")
                print(f"  Fat: {fat_g}g (DB: {macros['fat']}/100g)")
            else:
                # No product match - use model's macros
                product_id = None
                protein_g = ingredient.macros.protein
                carbs_g = ingredient.macros.carbs
                fat_g = ingredient.macros.fat
                calories_kcal = ingredient.macros.calories
                print(f"Using model macros for '{ingredient.ingredient_name}' (no DB match)")

            await self._items_repository.insert_item(
                run_id=run_id,
                user_id=user_id,
                ordinal=idx,
                ingredient_name=ingredient.ingredient_name,
                amount=ingredient.amount_grams,
                unit="g",
                confidence_score=confidence,
                matched_product_id=product_id,
                protein_g=protein_g,
                carbs_g=carbs_g,
                fat_g=fat_g,
                calories_kcal=calories_kcal,
            )

        logger.info(
            "analysis_run.items_created",
            extra={
                "run_id": str(run_id),
                "user_id": str(user_id),
                "items": len(ingredients),
            },
        )

    async def _fail_run(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        start_time: float,
        error_code: str,
        error_message: str,
    ) -> dict[str, Any]:
        latency_ms = int((perf_counter() - start_time) * 1000)
        return await self._repository.complete_run(
            run_id=run_id,
            user_id=user_id,
            status="failed",
            latency_ms=latency_ms,
            tokens=0,
            cost_minor_units=0,
            cost_currency="USD",
            raw_output={
                "error": error_message,
                "error_code": error_code,
            },
            error_code=error_code,
            error_message=error_message,
        )

    async def _lookup_product_by_name(self, ingredient_name: str) -> dict[str, Any] | None:
        """Look up product in database by ingredient name (English).

        Returns dict with product_id and macros if found, None otherwise.
        Format: {"id": "uuid", "macros": {"calories": X, "protein": Y, "carbs": Z, "fat": W}}
        All macros are per 100g.
        """
        try:
            from app.db.repositories.product_repository import SearchMode

            print("=== PRODUCT LOOKUP START ===")
            print(f"Original ingredient: '{ingredient_name}'")

            # Transform search query: replace ", " with "*" for better matching
            # e.g., "egg, fried" becomes "egg*fried"
            search_query = ingredient_name.replace(", ", "*").replace(" ", "*")

            print(f"Search query: '{search_query}'")

            logger.info(
                "Looking up product for ingredient: '%s' (query: '%s')",
                ingredient_name,
                search_query,
            )

            # Search for products matching the ingredient name with macros included
            # Use FULLTEXT mode which supports wildcards and flexible matching
            results = self._product_repository.list_products(
                search=search_query,
                search_mode=SearchMode.FULLTEXT,  # Use fulltext search for better matching
                page_size=1,  # Get only the best match
                include_macros=True,  # Include macronutrient data
            )

            print(f"Search results: {len(results) if results else 0} matches found")

            logger.info(
                "Product search results for '%s': %d matches found",
                ingredient_name,
                len(results) if results else 0,
            )

            if results and len(results) > 0:
                product = results[0]
                product_id = product.id
                product_name = product.name

                macros_dto = product.macros_per_100g
                if macros_dto is None:
                    logger.warning(
                        "Product matched for ingredient '%s' but macros_per_100g is missing",
                        ingredient_name,
                    )
                    print(
                        f"Match found for '{ingredient_name}' (id={product_id}) but "
                        "macros_per_100g is missing"
                    )
                    print("=== PRODUCT LOOKUP END ===")
                    return None

                # Extract macros (per 100g)
                macros = {
                    "calories": Decimal(str(macros_dto.calories)),
                    "protein": Decimal(str(macros_dto.protein)),
                    "carbs": Decimal(str(macros_dto.carbs)),
                    "fat": Decimal(str(macros_dto.fat)),
                }

                print(f"Match found: id={product_id}, name='{product_name}'")
                print(
                    f"  Macros per 100g: Cal={macros['calories']}, "
                    f"P={macros['protein']}g, C={macros['carbs']}g, F={macros['fat']}g"
                )

                logger.info(
                    "Product matched for ingredient '%s': id=%s, name='%s'",
                    ingredient_name,
                    product_id,
                    product_name,
                )
                print("=== PRODUCT LOOKUP END ===")

                return {
                    "id": str(product_id),
                    "macros": macros,
                }
            else:
                print(f"No match found for '{ingredient_name}'")
                logger.warning(
                    "No product match found for ingredient: '%s'",
                    ingredient_name,
                )
                print("=== PRODUCT LOOKUP END ===")
                return None

        except Exception as exc:
            print(f"ERROR during product lookup: {exc}")
            logger.error(
                "Failed to lookup product for ingredient '%s': %s",
                ingredient_name,
                exc,
                exc_info=True,
            )
            print("=== PRODUCT LOOKUP END ===")
            return None

    def _serialize_analysis_item(self, item: AnalysisItem) -> dict[str, Any]:
        return {
            "ingredient_name": item.ingredient_name,
            "amount_grams": float(item.amount_grams),
            "confidence": float(item.confidence) if item.confidence is not None else None,
            "product_id": str(item.product_id) if item.product_id else None,
            "macros": {
                "calories": float(item.macros.calories),
                "protein": float(item.macros.protein),
                "fat": float(item.macros.fat),
                "carbs": float(item.macros.carbs),
            },
        }

    def _serialize_verification(
        self,
        result: IngredientVerificationResult,
    ) -> dict[str, Any]:
        macro_delta = (
            {
                "calories_diff": float(result.macro_delta.calories_diff),
                "protein_diff": float(result.macro_delta.protein_diff),
                "carbs_diff": float(result.macro_delta.carbs_diff),
                "fat_diff": float(result.macro_delta.fat_diff),
                "calories_pct": float(result.macro_delta.calories_pct)
                if result.macro_delta.calories_pct is not None
                else None,
                "protein_pct": float(result.macro_delta.protein_pct)
                if result.macro_delta.protein_pct is not None
                else None,
                "carbs_pct": float(result.macro_delta.carbs_pct)
                if result.macro_delta.carbs_pct is not None
                else None,
                "fat_pct": float(result.macro_delta.fat_pct)
                if result.macro_delta.fat_pct is not None
                else None,
            }
            if result.macro_delta
            else None
        )

        return {
            "ingredient_name": result.ingredient_name,
            "product_id": str(result.product_id) if result.product_id else None,
            "requires_manual_review": result.requires_manual_review,
            "issues": result.issues,
            "macro_delta": macro_delta,
        }

    def _to_decimal(self, value: Any) -> Decimal:
        return Decimal(str(value))
