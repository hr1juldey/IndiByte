#!/usr/bin/env python3
"""
Integration validation script for Bytelense backend.

Tests:
1. SearXNG connection and JSON format
2. OpenFoodFacts API
3. Ollama availability (optional)
4. Profile storage
"""

import asyncio
import httpx
import json
from pathlib import Path


async def test_searxng():
    """Test SearXNG connection."""
    print("\n🔍 Testing SearXNG...")

    url = "http://192.168.1.4/search"
    params = {
        "q": "coca cola nutrition facts",
        "format": "json"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"  ✅ SearXNG is accessible")
                print(f"  ✅ JSON format is enabled")
                print(f"  ✅ Query returned {len(results)} results")

                if results:
                    print(f"  ✅ First result: {results[0]['title'][:60]}...")
                return True
            else:
                print(f"  ❌ SearXNG returned status {response.status_code}")
                return False

    except Exception as e:
        print(f"  ❌ SearXNG connection failed: {e}")
        return False


async def test_openfoodfacts():
    """Test OpenFoodFacts API."""
    print("\n🍔 Testing OpenFoodFacts API...")

    # Test with Coca-Cola barcode
    barcode = "5449000000996"  # Coca-Cola
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()

                if data.get("status") == 1:
                    product = data["product"]
                    name = product.get("product_name", "Unknown")
                    print(f"  ✅ OpenFoodFacts API is accessible")
                    print(f"  ✅ Product found: {name}")

                    nutriments = product.get("nutriments", {})
                    if nutriments:
                        print(f"  ✅ Nutrition data available")
                        print(f"     - Energy: {nutriments.get('energy-kcal_100g', 'N/A')} kcal/100g")
                        print(f"     - Sugar: {nutriments.get('sugars_100g', 'N/A')} g/100g")
                    return True
                else:
                    print(f"  ⚠️  Product not found")
                    return False
            else:
                print(f"  ❌ API returned status {response.status_code}")
                return False

    except Exception as e:
        print(f"  ❌ OpenFoodFacts API failed: {e}")
        return False


async def test_ollama():
    """Test Ollama availability (optional)."""
    print("\n🤖 Testing Ollama...")

    url = "http://localhost:11434/api/tags"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                print(f"  ✅ Ollama is running")
                print(f"  ✅ Available models: {len(models)}")

                for model in models:
                    name = model.get("name", "unknown")
                    size = model.get("size", 0) / (1024**3)  # Convert to GB
                    print(f"     - {name} ({size:.1f} GB)")

                # Check for recommended models
                model_names = [m.get("name", "") for m in models]
                if any("qwen" in m or "deepseek" in m for m in model_names):
                    print(f"  ✅ Recommended model found")
                else:
                    print(f"  ⚠️  No qwen or deepseek model found")
                    print(f"     Run: ollama pull qwen3:8b")

                return True
            else:
                print(f"  ❌ Ollama returned status {response.status_code}")
                return False

    except Exception as e:
        print(f"  ⚠️  Ollama not accessible: {e}")
        print(f"     This is optional for testing, but required for AI scoring")
        return False


def test_profile_storage():
    """Test profile storage directory."""
    print("\n📁 Testing Profile Storage...")

    profiles_dir = Path("./data/profiles")

    try:
        profiles_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Profiles directory exists: {profiles_dir}")

        # Test write permission
        test_file = profiles_dir / ".test"
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✅ Write permissions OK")

        return True

    except Exception as e:
        print(f"  ❌ Profile storage error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Bytelense Backend - Integration Validation")
    print("=" * 60)

    results = {}

    # Run tests
    results["searxng"] = await test_searxng()
    results["openfoodfacts"] = await test_openfoodfacts()
    results["ollama"] = await test_ollama()
    results["storage"] = test_profile_storage()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name.upper():<20} {status}")

    required_tests = ["searxng", "openfoodfacts", "storage"]
    required_passed = all(results[t] for t in required_tests)

    print("\n" + "=" * 60)
    if required_passed:
        print("✅ All required integrations are working!")
        print("\nYou can now start the backend server:")
        print("  python -m app.main")
    else:
        print("❌ Some required integrations failed")
        print("\nPlease fix the issues above before starting the server")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
