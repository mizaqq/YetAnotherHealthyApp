#!/usr/bin/env python3
"""
Quick search utility for USDA food data.

Usage:
    python search_usda_foods.py "chicken breast"
    python search_usda_foods.py "egg" --limit 20
    python search_usda_foods.py "rice cooked" --type sr_legacy_food
"""

import csv
import sys
from pathlib import Path
from typing import List, Dict
import argparse


def search_foods(
    csv_path: Path,
    query: str,
    limit: int = 10,
    data_type: str = None,
    case_sensitive: bool = False,
) -> List[Dict]:
    """Search for foods matching query.

    Args:
        csv_path: Path to USDA CSV file
        query: Search term
        limit: Maximum results to return
        data_type: Optional filter by data type
        case_sensitive: Whether search is case sensitive

    Returns:
        List of matching food dictionaries
    """
    results = []
    query_term = query if case_sensitive else query.lower()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row["name"]
            search_name = name if case_sensitive else name.lower()

            # Check if query matches
            if query_term not in search_name:
                continue

            # Filter by data type if specified
            if data_type and row["data_type"] != data_type:
                continue

            results.append(row)

            if len(results) >= limit:
                break

    return results


def format_food(food: Dict, show_type: bool = True) -> str:
    """Format food entry for display.

    Args:
        food: Food dictionary
        show_type: Whether to show data type

    Returns:
        Formatted string
    """
    type_str = f" ({food['data_type']})" if show_type else ""
    return (
        f"[{food['fdc_id']}] {food['name']}{type_str}\n"
        f"  Calories: {food['calories_kcal_per_100g']} kcal | "
        f"Protein: {food['protein_g_per_100g']}g | "
        f"Fat: {food['fat_g_per_100g']}g | "
        f"Carbs: {food['carbs_g_per_100g']}g"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Search USDA food database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search_usda_foods.py "chicken breast"
  python search_usda_foods.py "egg" --limit 20
  python search_usda_foods.py "rice cooked" --type sr_legacy_food
  python search_usda_foods.py "banana" --csv data/usda_all_foods_macros.csv
        """,
    )

    parser.add_argument("query", help="Search term to look for in food names")

    parser.add_argument(
        "--csv",
        default="data/usda_sr_legacy_macros.csv",
        help="Path to USDA CSV file (default: data/usda_sr_legacy_macros.csv)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to show (default: 10)",
    )

    parser.add_argument(
        "--type",
        choices=[
            "sr_legacy_food",
            "foundation_food",
            "branded_food",
            "survey_fndds_food",
        ],
        help="Filter by food data type",
    )

    parser.add_argument(
        "--case-sensitive", action="store_true", help="Make search case sensitive"
    )

    parser.add_argument(
        "--no-type", action="store_true", help="Hide data type in output"
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)

    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        print(f"\nMake sure you've extracted the USDA data first:")
        print(
            f"  python scripts/extract_usda_csv_macros.py FoodData_Central_csv_2025-04-24/"
        )
        sys.exit(1)

    print(f"Searching for: '{args.query}'")
    if args.type:
        print(f"Filter by type: {args.type}")
    print(f"File: {csv_path}")
    print()

    results = search_foods(
        csv_path=csv_path,
        query=args.query,
        limit=args.limit,
        data_type=args.type,
        case_sensitive=args.case_sensitive,
    )

    if not results:
        print("No results found.")
        print("\nTips:")
        print("  - Try a shorter search term")
        print("  - Remove the --type filter")
        print("  - Try searching in usda_all_foods_macros.csv for branded products")
        return

    print(f"Found {len(results)} result(s):\n")

    for i, food in enumerate(results, 1):
        print(f"{i}. {format_food(food, show_type=not args.no_type)}")
        print()

    if len(results) == args.limit:
        print(f"(Showing first {args.limit} results. Use --limit to see more)")


if __name__ == "__main__":
    main()
