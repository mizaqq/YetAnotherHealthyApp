#!/usr/bin/env python3
"""
Extract product names, calories, and macros from USDA FoodData Central CSV files.

This script processes the full USDA CSV dataset and extracts only:
- Product name (description)
- FDC ID (USDA identifier)
- Data type (SR Legacy, Foundation, Branded, etc.)
- Calories (Energy in kcal per 100g)
- Protein (g per 100g)
- Fat (g per 100g)
- Carbohydrates (g per 100g)

Input: Directory containing USDA CSV files (food.csv, food_nutrient.csv, nutrient.csv)
Output: CSV file with simplified nutritional data
"""

import csv
import sys
from pathlib import Path
from typing import Dict, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# USDA nutrient IDs for macros
NUTRIENT_IDS = {
    "energy": 1008,  # Energy (kcal) - nutrient_nbr: 208
    "protein": 1003,  # Protein - nutrient_nbr: 203
    "fat": 1004,  # Total lipid (fat) - nutrient_nbr: 204
    "carbs": 1005,  # Carbohydrate, by difference - nutrient_nbr: 205
}


def load_foods_metadata(csv_dir: Path) -> Dict[str, Dict]:
    """Load food metadata (names, types) from food.csv.

    Uses head command to get first rows for sampling structure.

    Args:
        csv_dir: Directory containing USDA CSV files

    Returns:
        Dictionary mapping fdc_id to {name, data_type}
    """
    logger.info("Loading food metadata from food.csv...")

    food_file = csv_dir / "food.csv"
    if not food_file.exists():
        raise FileNotFoundError(f"food.csv not found in {csv_dir}")

    foods = {}

    # Read the CSV in chunks to handle large file
    chunk_size = 100000
    total_foods = 0

    with open(food_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Expected columns: fdc_id, data_type, description, food_category_id, publication_date
        for row in reader:
            fdc_id = row.get("fdc_id", "").strip()
            description = row.get("description", "").strip()
            data_type = row.get("data_type", "").strip()

            if fdc_id and description:
                foods[fdc_id] = {
                    "name": description,
                    "data_type": data_type,
                }
                total_foods += 1

                if total_foods % chunk_size == 0:
                    logger.info(f"  Loaded {total_foods:,} foods...")

    logger.info(f"✓ Loaded {len(foods):,} foods")
    return foods


def extract_macros_from_nutrients(csv_dir: Path, food_ids: Set[str]) -> Dict[str, Dict]:
    """Extract macro nutrients from food_nutrient.csv.

    Args:
        csv_dir: Directory containing USDA CSV files
        food_ids: Set of food IDs to process

    Returns:
        Dictionary mapping fdc_id to {calories, protein, fat, carbs}
    """
    logger.info("Extracting macros from food_nutrient.csv...")

    nutrient_file = csv_dir / "food_nutrient.csv"
    if not nutrient_file.exists():
        raise FileNotFoundError(f"food_nutrient.csv not found in {csv_dir}")

    # Store nutrients for each food
    food_nutrients = {}

    chunk_size = 500000
    total_nutrients = 0
    relevant_nutrients = 0

    with open(nutrient_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Expected columns: id, fdc_id, nutrient_id, amount, data_points, derivation_id, ...
        for row in reader:
            total_nutrients += 1

            fdc_id = row.get("fdc_id", "").strip()
            nutrient_id_str = row.get("nutrient_id", "").strip()
            amount_str = row.get("amount", "").strip()

            # Skip if food not in our list
            if fdc_id not in food_ids:
                continue

            # Skip if nutrient is not one of our macros
            try:
                nutrient_id = int(nutrient_id_str)
            except (ValueError, TypeError):
                continue

            if nutrient_id not in NUTRIENT_IDS.values():
                continue

            # Parse amount
            try:
                amount = float(amount_str)
            except (ValueError, TypeError):
                continue

            # Initialize food entry if needed
            if fdc_id not in food_nutrients:
                food_nutrients[fdc_id] = {}

            # Store the nutrient
            nutrient_name = [k for k, v in NUTRIENT_IDS.items() if v == nutrient_id][0]
            food_nutrients[fdc_id][nutrient_name] = amount
            relevant_nutrients += 1

            if total_nutrients % chunk_size == 0:
                logger.info(
                    f"  Processed {total_nutrients:,} nutrient records... "
                    f"({relevant_nutrients:,} relevant)"
                )

    logger.info(f"✓ Processed {total_nutrients:,} nutrient records")
    logger.info(f"✓ Found macros for {len(food_nutrients):,} foods")

    return food_nutrients


def filter_complete_foods(foods: Dict, nutrients: Dict) -> list:
    """Filter foods that have complete macro data.

    Args:
        foods: Dictionary of food metadata
        nutrients: Dictionary of nutrient data

    Returns:
        List of foods with complete macro data
    """
    logger.info("Filtering foods with complete macro data...")

    complete_foods = []

    for fdc_id, food_data in foods.items():
        if fdc_id not in nutrients:
            continue

        macros = nutrients[fdc_id]

        # Check if all macros are present
        if all(k in macros for k in ["energy", "protein", "fat", "carbs"]):
            complete_foods.append(
                {
                    "fdc_id": fdc_id,
                    "name": food_data["name"],
                    "data_type": food_data["data_type"],
                    "calories_kcal_per_100g": round(macros["energy"], 2),
                    "protein_g_per_100g": round(macros["protein"], 2),
                    "fat_g_per_100g": round(macros["fat"], 2),
                    "carbs_g_per_100g": round(macros["carbs"], 2),
                }
            )

    logger.info(f"✓ Found {len(complete_foods):,} foods with complete macros")

    # Show breakdown by data type
    type_counts = {}
    for food in complete_foods:
        dt = food["data_type"]
        type_counts[dt] = type_counts.get(dt, 0) + 1

    logger.info(f"  Breakdown by data type:")
    for data_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    - {data_type}: {count:,} foods")

    return complete_foods


def write_output_csv(foods: list, output_path: Path, data_types: list = None) -> None:
    """Write foods to CSV file.

    Args:
        foods: List of food dictionaries
        output_path: Path to output CSV file
        data_types: Optional list of data types to include (e.g., ['SR Legacy', 'Foundation'])
    """
    # Filter by data type if specified
    if data_types:
        foods = [f for f in foods if f["data_type"] in data_types]
        logger.info(
            f"Filtered to {len(foods):,} foods of types: {', '.join(data_types)}"
        )

    if not foods:
        logger.warning("No foods to write!")
        return

    fieldnames = [
        "fdc_id",
        "name",
        "data_type",
        "calories_kcal_per_100g",
        "protein_g_per_100g",
        "fat_g_per_100g",
        "carbs_g_per_100g",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(foods)

    logger.info(f"\n✓ Successfully wrote {len(foods):,} foods to: {output_path}")

    # Show sample entries
    logger.info(f"\nSample entries:")
    for food in foods[:10]:
        logger.info(
            f"  - {food['name']} ({food['data_type']}): "
            f"{food['calories_kcal_per_100g']} kcal, "
            f"P:{food['protein_g_per_100g']}g "
            f"F:{food['fat_g_per_100g']}g "
            f"C:{food['carbs_g_per_100g']}g"
        )


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(
            "Usage: python extract_usda_csv_macros.py <csv_directory> [output_csv_path] [--type TYPE1,TYPE2,...]"
        )
        print("\nArguments:")
        print("  csv_directory     : Directory containing USDA CSV files")
        print(
            "  output_csv_path   : Optional output CSV path (default: data/usda_all_macros.csv)"
        )
        print(
            "  --type            : Optional comma-separated list of data types to include"
        )
        print("\nData types:")
        print(
            "  - 'SR Legacy'     : Standard Reference (legacy) - best for basic ingredients (~7,000 foods)"
        )
        print(
            "  - 'Foundation'    : Foundation Foods - detailed nutrient data (~400 foods)"
        )
        print("  - 'branded_food'  : Branded commercial products (~300,000 foods)")
        print("  - 'survey_fndds_food' : Survey foods")
        print("\nExamples:")
        print("  # Extract all foods")
        print("  python extract_usda_csv_macros.py FoodData_Central_csv_2025-04-24/")
        print("\n  # Extract only SR Legacy and Foundation foods")
        print("  python extract_usda_csv_macros.py FoodData_Central_csv_2025-04-24/ \\")
        print("    data/usda_legacy_macros.csv --type 'SR Legacy,Foundation'")
        sys.exit(1)

    csv_dir = Path(sys.argv[1])

    if not csv_dir.exists():
        logger.error(f"Directory not found: {csv_dir}")
        sys.exit(1)

    # Parse output path
    if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
        output_path = Path(sys.argv[2])
    else:
        output_path = Path("data/usda_all_macros.csv")

    # Parse data type filter
    data_types = None
    for i, arg in enumerate(sys.argv):
        if arg == "--type" and i + 1 < len(sys.argv):
            data_types = [t.strip() for t in sys.argv[i + 1].split(",")]
            logger.info(f"Filtering to data types: {data_types}")
            break

    try:
        # Step 1: Load food metadata
        foods = load_foods_metadata(csv_dir)

        # Step 2: Extract macros from nutrients
        food_ids = set(foods.keys())
        nutrients = extract_macros_from_nutrients(csv_dir, food_ids)

        # Step 3: Filter to complete foods
        complete_foods = filter_complete_foods(foods, nutrients)

        # Step 4: Write output
        write_output_csv(complete_foods, output_path, data_types)

        logger.info("\n✅ Extraction complete!")

    except Exception as e:
        logger.error(f"Error processing files: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
