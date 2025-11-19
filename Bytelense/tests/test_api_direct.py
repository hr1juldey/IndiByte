#!/usr/bin/env python3
"""
Sub-Phase 2.2: Direct API Testing Script
Purpose: Query OpenFoodFacts API directly to understand sodium values
for cucumber and other test foods

This bypasses the system's processing to see raw API responses.
"""

import requests
import json
from typing import Dict, List, Optional

def query_openfoodfacts(food_name: str) -> Dict:
    """
    Query OpenFoodFacts API directly for a food item.

    Args:
        food_name: Name of the food to search for

    Returns:
        Raw API response (unprocessed by our system)
    """
    base_url = "https://world.openfoodfacts.org/cgi/search.pl"

    params = {
        "search_terms": food_name,
        "json": 1,
        "action": "process",
        "page_size": 10
    }

    try:
        print(f"\n{'='*70}")
        print(f"Querying OpenFoodFacts for: {food_name}")
        print(f"{'='*70}")
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"Found {data.get('count', 0)} results")

        if data.get('products'):
            print(f"\nTop result details:")
            top_product = data['products'][0]

            # Extract key fields
            product_name = top_product.get('product_name', 'N/A')
            print(f"  Product Name: {product_name}")

            nutrition = top_product.get('nutriments', {})
            print(f"\n  Nutrition Data (per 100g if available):")
            print(f"    Calories: {nutrition.get('energy-kcal', 'N/A')} kcal")
            print(f"    Carbs: {nutrition.get('carbohydrates', 'N/A')}g")
            print(f"    Protein: {nutrition.get('proteins', 'N/A')}g")
            print(f"    Fat: {nutrition.get('fat', 'N/A')}g")

            # CRITICAL: Check sodium value
            sodium_raw = nutrition.get('sodium', None)
            sodium_unit = nutrition.get('sodium_unit', 'g')
            print(f"    Sodium (RAW): {sodium_raw} {sodium_unit}")

            # Convert to mg if in grams
            if sodium_raw is not None and sodium_unit == 'g':
                sodium_mg = sodium_raw * 1000
                print(f"    Sodium (converted): {sodium_mg} mg")

            # Check if there's a _100g variant
            sodium_100g = nutrition.get('sodium_100g', None)
            print(f"    Sodium_100g: {sodium_100g} (raw unit)")

            print(f"\n  Full nutrition dict keys: {list(nutrition.keys())}")

            # Return full data for inspection
            return {
                "product_name": product_name,
                "nutrition": nutrition,
                "raw_response": top_product
            }
        else:
            print("No products found!")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
        return {}

def compare_foods():
    """
    Test multiple foods to understand sodium values across the dataset.

    Focus on:
    1. Cucumber (the problem case with 1680mg)
    2. Other vegetables
    3. Salted variants
    """

    test_foods = [
        "cucumber",
        "cucumber salted",
        "salt",
        "red salt",
        "vegetable",
        "rice",
        "egg",
        "rohu fish",
        "banana"
    ]

    results = {}

    for food in test_foods:
        result = query_openfoodfacts(food)
        results[food] = result

        # Print summary
        if result:
            nutrition = result.get('nutrition', {})
            sodium = nutrition.get('sodium', None)
            sodium_100g = nutrition.get('sodium_100g', None)
            print(f"\n  ✓ Found: {result.get('product_name')}")
            print(f"    Sodium: {sodium} | Sodium_100g: {sodium_100g}")
        else:
            print(f"\n  ✗ No result for: {food}")

    return results

def analyze_findings(results: Dict):
    """
    Analyze patterns in the sodium data.
    """
    print(f"\n{'='*70}")
    print("SODIUM ANALYSIS FINDINGS")
    print(f"{'='*70}")

    for food, data in results.items():
        if data:
            nutrition = data.get('nutrition', {})
            sodium_100g = nutrition.get('sodium_100g', None)

            if sodium_100g is not None:
                # Check if value is unrealistic
                if sodium_100g > 3000:
                    print(f"\n⚠️  UNREALISTIC: {food}")
                    print(f"    Sodium: {sodium_100g} mg/100g (>3000mg - possible error)")
                elif sodium_100g > 1000:
                    print(f"\n⚠️  HIGH: {food}")
                    print(f"    Sodium: {sodium_100g} mg/100g (high but possible for salted items)")
                else:
                    print(f"\n✓ NORMAL: {food}")
                    print(f"    Sodium: {sodium_100g} mg/100g")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SUB-PHASE 2.2: DIRECT OPENFOODFACTS API TESTING")
    print("="*70)

    # Test specific problem case
    print("\n[STAGE 1] Testing cucumber specifically...")
    cucumber_data = query_openfoodfacts("cucumber")

    # Test other foods
    print("\n[STAGE 2] Testing multiple foods for comparison...")
    results = compare_foods()

    # Analyze patterns
    print("\n[STAGE 3] Analyzing patterns...")
    analyze_findings(results)

    # Save detailed results to JSON for review
    with open("SODIUM_API_RAW_RESPONSES.json", "w") as f:
        # Convert to serializable format
        serializable = {}
        for food, data in results.items():
            if data:
                serializable[food] = {
                    "product_name": data.get('product_name'),
                    "nutrition": data.get('nutrition')
                }
        json.dump(serializable, f, indent=2)

    print(f"\n✓ Raw API responses saved to SODIUM_API_RAW_RESPONSES.json")
