#!/usr/bin/env python3
"""
Extract product names, calories, and macros from USDA FoodData Central JSON.

This script processes the Foundation Foods JSON file and extracts only:
- Product name (description)
- Calories (Energy in kcal)
- Protein (g per 100g)
- Fat (g per 100g)
- Carbohydrates (g per 100g)

Output: CSV file with simplified nutritional data
"""

import json
import csv
import sys
from pathlib import Path
from typing import Optional

# USDA nutrient IDs for macros (these are standard across FoodData Central)
NUTRIENT_IDS = {
    "energy_kcal": 1008,      # Energy (kcal)
    "protein": 1003,          # Protein
    "fat": 1004,              # Total lipid (fat)
    "carbs": 1005,            # Carbohydrate, by difference
}


def extract_nutrient(food_nutrients: list, nutrient_id: int) -> Optional[float]:
    """Extract a specific nutrient value from the food nutrients list.
    
    Args:
        food_nutrients: List of nutrient objects from USDA data
        nutrient_id: USDA nutrient ID to search for
        
    Returns:
        Nutrient amount or None if not found
    """
    for nutrient in food_nutrients:
        if nutrient.get("nutrient", {}).get("id") == nutrient_id:
            return nutrient.get("amount")
    return None


def process_usda_json(input_path: Path, output_path: Path) -> None:
    """Process USDA JSON and extract macros to CSV.
    
    Args:
        input_path: Path to USDA FoodData Central JSON file
        output_path: Path to output CSV file
    """
    print(f"Reading USDA data from: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    foundation_foods = data.get("FoundationFoods", [])
    print(f"Found {len(foundation_foods)} foods in database")
    
    # Extract macros from each food
    extracted_foods = []
    foods_with_complete_data = 0
    
    for food in foundation_foods:
        description = food.get("description", "")
        fdc_id = food.get("fdcId", "")
        food_nutrients = food.get("foodNutrients", [])
        
        # Extract each macro
        calories = extract_nutrient(food_nutrients, NUTRIENT_IDS["energy_kcal"])
        protein = extract_nutrient(food_nutrients, NUTRIENT_IDS["protein"])
        fat = extract_nutrient(food_nutrients, NUTRIENT_IDS["fat"])
        carbs = extract_nutrient(food_nutrients, NUTRIENT_IDS["carbs"])
        
        # Only include foods with complete macro data
        if all(v is not None for v in [calories, protein, fat, carbs]):
            extracted_foods.append({
                "fdc_id": fdc_id,
                "name": description,
                "calories_kcal_per_100g": round(calories, 2),
                "protein_g_per_100g": round(protein, 2),
                "fat_g_per_100g": round(fat, 2),
                "carbs_g_per_100g": round(carbs, 2),
            })
            foods_with_complete_data += 1
    
    print(f"Foods with complete macro data: {foods_with_complete_data}")
    
    # Write to CSV
    if extracted_foods:
        fieldnames = [
            "fdc_id",
            "name",
            "calories_kcal_per_100g",
            "protein_g_per_100g",
            "fat_g_per_100g",
            "carbs_g_per_100g",
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(extracted_foods)
        
        print(f"\n✓ Successfully extracted {len(extracted_foods)} foods to: {output_path}")
        print(f"\nSample entries:")
        for food in extracted_foods[:5]:
            print(f"  - {food['name']}: {food['calories_kcal_per_100g']} kcal, "
                  f"P:{food['protein_g_per_100g']}g F:{food['fat_g_per_100g']}g "
                  f"C:{food['carbs_g_per_100g']}g")
    else:
        print("No foods with complete macro data found!")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python extract_usda_macros.py <input_json_path> [output_csv_path]")
        print("\nExample:")
        print("  python extract_usda_macros.py ~/Downloads/FoodData_Central_foundation_food_json_2025-04-24.json")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Default output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = Path("usda_foods_macros.csv")
    
    try:
        process_usda_json(input_path, output_path)
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

