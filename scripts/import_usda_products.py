#!/usr/bin/env python3
"""
Import USDA SR Legacy products into the database.

This script reads the usda_sr_legacy_macros.csv file and inserts products
into the public.products table via Supabase.
"""

import csv
import os
import sys
from decimal import Decimal
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed.")
    print("Install it with: pip install supabase")
    sys.exit(1)


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
    key = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
    )
    return create_client(url, key)


def import_products(csv_path: str, batch_size: int = 100) -> None:
    """Import products from CSV into database.

    Args:
        csv_path: Path to the CSV file
        batch_size: Number of products to insert per batch
    """
    client = get_supabase_client()

    products = []
    total_processed = 0
    total_inserted = 0
    total_errors = 0

    print(f"Reading products from {csv_path}...")

    with open(csv_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            total_processed += 1

            try:
                # Parse macronutrients
                calories = Decimal(row["calories_kcal_per_100g"])
                protein = Decimal(row["protein_g_per_100g"])
                fat = Decimal(row["fat_g_per_100g"])
                carbs = Decimal(row["carbs_g_per_100g"])

                # Create product record
                product = {
                    "name": row["name"].strip(),
                    "off_id": None,  # USDA products don't have OFF IDs
                    "macros_per_100g": {
                        "calories": float(calories),
                        "protein": float(protein),
                        "fat": float(fat),
                        "carbs": float(carbs),
                    },
                    "source": "usda_sr_legacy",
                }

                products.append(product)

                # Insert batch when batch_size is reached
                if len(products) >= batch_size:
                    try:
                        result = client.table("products").insert(products).execute()
                        total_inserted += len(products)
                        print(
                            f"✓ Inserted batch of {len(products)} products (total: {total_inserted})"
                        )
                        products = []
                    except Exception as e:
                        print(f"✗ Error inserting batch: {e}")
                        total_errors += len(products)
                        products = []

            except Exception as e:
                print(f"✗ Error processing row {total_processed}: {e}")
                print(f"   Row data: {row}")
                total_errors += 1
                continue

            # Progress indicator
            if total_processed % 1000 == 0:
                print(f"Processed {total_processed} rows...")

    # Insert remaining products
    if products:
        try:
            result = client.table("products").insert(products).execute()
            total_inserted += len(products)
            print(f"✓ Inserted final batch of {len(products)} products")
        except Exception as e:
            print(f"✗ Error inserting final batch: {e}")
            total_errors += len(products)

    print("\n" + "=" * 60)
    print(f"Import complete!")
    print(f"Total rows processed: {total_processed}")
    print(f"Total products inserted: {total_inserted}")
    print(f"Total errors: {total_errors}")
    print("=" * 60)


def main():
    """Main entry point."""
    # Get CSV path
    csv_path = Path(__file__).parent.parent / "data" / "usda_sr_legacy_macros.csv"

    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)

    print("USDA SR Legacy Products Importer")
    print("=" * 60)
    print(f"CSV file: {csv_path}")
    print(f"File size: {csv_path.stat().st_size / 1024:.2f} KB")
    print("=" * 60)

    # Count rows
    with open(csv_path, "r", encoding="utf-8") as f:
        row_count = sum(1 for _ in f) - 1  # Exclude header

    print(f"Found {row_count} products to import")

    # Confirm
    response = input("\nProceed with import? (y/n): ")
    if response.lower() != "y":
        print("Import cancelled.")
        sys.exit(0)

    # Import
    import_products(str(csv_path), batch_size=100)


if __name__ == "__main__":
    main()
