"""Mock analysis processor for MVP.

This module provides a synchronous mock implementation of the analysis processor
that simulates AI-based ingredient extraction and nutrition analysis.
In production, this would integrate with an actual AI service (OpenRouter, etc.).
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class AnalysisRunProcessor:
    """Processes analysis runs synchronously with mock AI inference (MVP)."""

    # Mock product database for ingredient matching
    # Using real product UUIDs from the database
    MOCK_PRODUCTS = [
        {
            "id": "379a524e-4b28-4288-bd10-5495fbed68d7",  # QUAKER Instant Oatmeal
            "name": "Oatmeal",
            "protein_g": Decimal("13.15"),
            "carbs_g": Decimal("66.27"),
            "fat_g": Decimal("6.90"),
            "calories_kcal": Decimal("389.0"),
        },
        {
            "id": "803038ec-b35a-426e-a2fd-4fcf82029777",  # Bananas, raw
            "name": "Banana",
            "protein_g": Decimal("1.09"),
            "carbs_g": Decimal("22.84"),
            "fat_g": Decimal("0.33"),
            "calories_kcal": Decimal("89.0"),
        },
        {
            "id": "3548c925-bd9e-40a9-b40a-155dfb0b6ab6",  # Yogurt, fruit variety, nonfat
            "name": "Yogurt",
            "protein_g": Decimal("3.47"),
            "carbs_g": Decimal("4.66"),
            "fat_g": Decimal("3.25"),
            "calories_kcal": Decimal("61.0"),
        },
        {
            "id": "125d9727-490a-473b-8bc7-c8492a075379",  # Chicken, grilled breast
            "name": "Chicken breast",
            "protein_g": Decimal("31.00"),
            "carbs_g": Decimal("0.0"),
            "fat_g": Decimal("3.60"),
            "calories_kcal": Decimal("165.0"),
        },
        {
            "id": "b30de2fe-764a-4f8f-bf2f-31047d817206",  # CREAM OF RICE, dry
            "name": "Rice",
            "protein_g": Decimal("2.69"),
            "carbs_g": Decimal("28.17"),
            "fat_g": Decimal("0.28"),
            "calories_kcal": Decimal("130.0"),
        },
        {
            "id": "1a2bbfd0-10bb-4a12-a83c-a91c76fee707",  # Egg, whole, cooked, hard-boiled
            "name": "Egg",
            "protein_g": Decimal("12.56"),
            "carbs_g": Decimal("1.12"),
            "fat_g": Decimal("9.51"),
            "calories_kcal": Decimal("143.0"),
        },
        {
            "id": "7d168c2e-6e6a-4f4b-a33d-b68ade1b6072",  # Fish, salmon, Atlantic, farmed, raw
            "name": "Salmon",
            "protein_g": Decimal("20.42"),
            "carbs_g": Decimal("0.0"),
            "fat_g": Decimal("13.42"),
            "calories_kcal": Decimal("206.0"),
        },
    ]

    def __init__(self, repository, items_repository):
        """Initialize processor with repository dependencies.

        Args:
            repository: AnalysisRunsRepository for updating run status
            items_repository: AnalysisRunItemsRepository for creating items
        """
        self._repository = repository
        self._items_repository = items_repository

    async def process(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        meal_id: UUID,
        raw_input: dict[str, Any],
        threshold: Decimal,
    ) -> dict[str, Any]:
        """Process an analysis run synchronously (MVP mock).

        Updates run status to 'running', simulates AI inference,
        creates analysis_run_items, and updates final status to 'succeeded' or 'failed'.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier
            meal_id: Meal identifier
            raw_input: Raw input dict (meal description, etc.)
            threshold: Confidence threshold for matching

        Returns:
            Dict with final run state after processing

        Raises:
            Exception: If processing fails (will be caught by service layer)
        """
        start_time = datetime.utcnow()

        try:
            # Step 1: Update status to 'running'
            await self._repository.update_status(
                run_id=run_id,
                user_id=user_id,
                status="running",
            )

            logger.info(
                "Started processing analysis run (mock)",
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                    "meal_id": str(meal_id),
                },
            )

            # Step 2: Simulate AI inference (mock)
            # In production: call OpenRouter API with raw_input
            mock_ingredients = self._mock_extract_ingredients(raw_input, threshold)

            # Step 3: Create analysis_run_items
            await self._create_items(
                run_id=run_id,
                user_id=user_id,
                ingredients=mock_ingredients,
            )

            # Step 4: Calculate metrics (mock)
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            tokens_used = random.randint(1500, 3000)  # Mock token count
            cost_minor_units = int(tokens_used * 0.015)  # Mock cost calculation

            # Step 5: Store raw_output (mock)
            raw_output = {
                "model_response": {
                    "ingredients": [
                        {
                            "name": item["ingredient_name"],
                            "amount": float(item["amount"]),
                            "unit": item["unit"],
                            "confidence": float(item["confidence_score"]),
                        }
                        for item in mock_ingredients
                    ],
                },
                "tokens": tokens_used,
                "latency_ms": latency_ms,
            }

            # Step 6: Update run to 'succeeded' with metrics
            final_run = await self._repository.complete_run(
                run_id=run_id,
                user_id=user_id,
                status="succeeded",
                latency_ms=latency_ms,
                tokens=tokens_used,
                cost_minor_units=cost_minor_units,
                cost_currency="USD",
                raw_output=raw_output,
            )

            logger.info(
                "Completed processing analysis run (mock)",
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                    "status": "succeeded",
                    "items_count": len(mock_ingredients),
                    "latency_ms": latency_ms,
                },
            )

            return final_run

        except Exception as exc:
            # Step 7: Handle failures - update run to 'failed'
            logger.error(
                "Failed to process analysis run (mock)",
                exc_info=True,
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                },
            )

            try:
                end_time = datetime.utcnow()
                latency_ms = int((end_time - start_time).total_seconds() * 1000)

                failed_run = await self._repository.complete_run(
                    run_id=run_id,
                    user_id=user_id,
                    status="failed",
                    latency_ms=latency_ms,
                    tokens=0,
                    cost_minor_units=0,
                    cost_currency="USD",
                    raw_output={"error": str(exc)},
                    error_code="PROCESSING_ERROR",
                    error_message=f"Mock processing failed: {exc}",
                )

                return failed_run
            except Exception as update_exc:
                logger.exception(
                    "Failed to update run status after processing error",
                    exc_info=True,
                    extra={"run_id": str(run_id)},
                )
                # Re-raise original exception
                raise exc from update_exc

    def _mock_extract_ingredients(
        self,
        raw_input: dict[str, Any],
        threshold: Decimal,
    ) -> list[dict[str, Any]]:
        """Mock AI extraction of ingredients from input.

        Simulates parsing meal description and matching to products.

        Args:
            raw_input: Raw input dict with meal info
            threshold: Confidence threshold (affects which items are included)

        Returns:
            List of ingredient dicts with amounts, units, and confidence scores
        """
        # Extract description from raw_input
        description = raw_input.get("text", "").lower()

        # Simple keyword matching to mock products
        detected_ingredients = []
        ordinal = 1

        for product in self.MOCK_PRODUCTS:
            if product["name"].lower() in description:
                # Generate mock confidence score above threshold
                confidence = float(threshold) + random.uniform(0.05, 0.20)
                confidence = min(confidence, 0.99)  # Cap at 0.99

                # Generate realistic amount based on product type
                amount = self._generate_realistic_amount(product["name"])

                detected_ingredients.append(
                    {
                        "ordinal": ordinal,
                        "ingredient_name": product["name"],
                        "amount": Decimal(str(amount)),
                        "unit": "g",
                        "confidence_score": Decimal(str(round(confidence, 2))),
                        "matched_product_id": product["id"],
                        "protein_g": product["protein_g"],
                        "carbs_g": product["carbs_g"],
                        "fat_g": product["fat_g"],
                        "calories_kcal": product["calories_kcal"],
                    }
                )
                ordinal += 1

        # If no ingredients detected, add a random one for demo
        if not detected_ingredients:
            product = random.choice(self.MOCK_PRODUCTS)
            amount = self._generate_realistic_amount(product["name"])
            confidence = float(threshold) + 0.10

            detected_ingredients.append(
                {
                    "ordinal": 1,
                    "ingredient_name": product["name"],
                    "amount": Decimal(str(amount)),
                    "unit": "g",
                    "confidence_score": Decimal(str(round(confidence, 2))),
                    "matched_product_id": product["id"],
                    "protein_g": product["protein_g"],
                    "carbs_g": product["carbs_g"],
                    "fat_g": product["fat_g"],
                    "calories_kcal": product["calories_kcal"],
                }
            )

        return detected_ingredients

    def _generate_realistic_amount(self, product_name: str) -> float:
        """Generate realistic amounts for different food types."""
        # Different food types have different typical serving sizes
        if product_name.lower() in ("chicken breast", "salmon"):
            return round(random.uniform(100, 200), 1)  # Meat: 100-200g
        elif product_name.lower() in ("rice", "oatmeal"):
            return round(random.uniform(50, 150), 1)  # Grains: 50-150g
        elif product_name.lower() in ("apple", "banana"):
            return round(random.uniform(120, 180), 1)  # Fruit: 120-180g
        elif product_name.lower() in ("milk", "yogurt"):
            return round(random.uniform(150, 300), 1)  # Liquids: 150-300ml
        elif product_name.lower() == "egg":
            return round(random.uniform(50, 70), 1)  # Egg: 50-70g
        elif product_name.lower() == "bread":
            return round(random.uniform(30, 60), 1)  # Bread slice: 30-60g
        else:
            return round(random.uniform(50, 150), 1)  # Default: 50-150g

    async def _create_items(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        ingredients: list[dict[str, Any]],
    ) -> None:
        """Create analysis_run_items records for detected ingredients.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier
            ingredients: List of ingredient dicts with amounts and nutrition
        """
        for ingredient in ingredients:
            # Calculate nutrition based on amount (per 100g values)
            amount = ingredient["amount"]
            factor = amount / 100

            await self._items_repository.insert_item(
                run_id=run_id,
                user_id=user_id,
                ordinal=ingredient["ordinal"],
                ingredient_name=ingredient["ingredient_name"],
                amount=ingredient["amount"],
                unit=ingredient["unit"],
                confidence_score=ingredient["confidence_score"],
                matched_product_id=ingredient.get("matched_product_id"),
                protein_g=ingredient["protein_g"] * Decimal(str(factor)),
                carbs_g=ingredient["carbs_g"] * Decimal(str(factor)),
                fat_g=ingredient["fat_g"] * Decimal(str(factor)),
                calories_kcal=ingredient["calories_kcal"] * Decimal(str(factor)),
            )

        logger.info(
            "Created analysis run items",
            extra={
                "run_id": str(run_id),
                "user_id": str(user_id),
                "items_count": len(ingredients),
            },
        )
