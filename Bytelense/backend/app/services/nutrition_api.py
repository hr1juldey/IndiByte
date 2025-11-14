"""Nutrition data retrieval from OpenFoodFacts and SearXNG."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx

from app.models.schemas import NutritionData
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenFoodFactsClient:
    """Client for OpenFoodFacts API."""

    def __init__(self):
        """Initialize OpenFoodFacts client."""
        self.base_url = settings.openfoodfacts_api_base
        self.timeout = settings.openfoodfacts_timeout
        logger.info("OpenFoodFacts client initialized")

    async def get_by_barcode(self, barcode: str) -> Optional[NutritionData]:
        """
        Get product by barcode.

        Args:
            barcode: Product barcode

        Returns:
            NutritionData if found, None otherwise
        """
        url = f"{self.base_url}/api/v2/product/{barcode}.json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == 1 and "product" in data:
                        return self._parse_product(data["product"], barcode)

                logger.debug(f"Product not found by barcode: {barcode}")
                return None

        except Exception as e:
            logger.error(f"OpenFoodFacts API error (barcode): {e}")
            return None

    async def search_by_text(self, query: str) -> Optional[NutritionData]:
        """
        Search products by text query.

        Args:
            query: Product name or description

        Returns:
            NutritionData for first result, None if no results
        """
        url = f"{self.base_url}/cgi/search.pl"
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    if data.get("products"):
                        # Return first result
                        product = data["products"][0]
                        return self._parse_product(
                            product,
                            product.get("code")
                        )

                logger.debug(f"No products found for query: {query}")
                return None

        except Exception as e:
            logger.error(f"OpenFoodFacts API error (search): {e}")
            return None

    def _parse_product(self, product: Dict[str, Any], barcode: Optional[str]) -> NutritionData:
        """
        Parse OpenFoodFacts product data into NutritionData.

        Args:
            product: Raw product data from API
            barcode: Product barcode

        Returns:
            Parsed NutritionData
        """
        # Extract nutriments
        nutriments = product.get("nutriments", {})

        # Helper to get nutrient value with fallback
        def get_nutrient(key: str, default: float = 0.0) -> float:
            value = nutriments.get(f"{key}_100g", nutriments.get(key, default))
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        return NutritionData(
            product_name=product.get("product_name", product.get("product_name_en", "Unknown")),
            brand=product.get("brands", "Unknown"),
            barcode=barcode,
            serving_size=product.get("serving_size", "100g"),
            calories=get_nutrient("energy-kcal"),
            protein_g=get_nutrient("proteins"),
            carbs_g=get_nutrient("carbohydrates"),
            fat_g=get_nutrient("fat"),
            saturated_fat_g=get_nutrient("saturated-fat"),
            sugar_g=get_nutrient("sugars"),
            sodium_mg=get_nutrient("sodium") * 1000,  # Convert g to mg
            fiber_g=get_nutrient("fiber"),
            ingredients=self._parse_ingredients(product.get("ingredients_text", "")),
            allergens=self._parse_allergens(product.get("allergens_tags", [])),
            additives=product.get("additives_tags", []),
            data_source="openfoodfacts",
            confidence=0.9,  # High confidence for OpenFoodFacts data
            retrieved_at=datetime.now()
        )

    def _parse_ingredients(self, ingredients_text: str) -> List[str]:
        """Parse ingredients from text."""
        if not ingredients_text:
            return []
        # Split by comma and clean up
        ingredients = [ing.strip() for ing in ingredients_text.split(",")]
        return [ing for ing in ingredients if ing][:20]  # Limit to 20

    def _parse_allergens(self, allergen_tags: List[str]) -> List[str]:
        """Parse allergen tags."""
        # Tags are like "en:milk", "en:eggs"
        allergens = []
        for tag in allergen_tags:
            if ":" in tag:
                allergen = tag.split(":")[1].replace("-", " ").title()
                allergens.append(allergen)
        return allergens


class NutritionDataAggregator:
    """Aggregates nutrition data from multiple sources."""

    def __init__(self):
        """Initialize aggregator."""
        self.openfoodfacts = OpenFoodFactsClient()
        logger.info("Nutrition data aggregator initialized")

    async def get_nutrition_data(
        self,
        barcode: Optional[str] = None,
        product_name: Optional[str] = None
    ) -> Optional[NutritionData]:
        """
        Get nutrition data with fallback chain.

        Fallback order:
        1. OpenFoodFacts barcode lookup
        2. OpenFoodFacts text search
        3. SearXNG web search (via DSPy tool)

        Args:
            barcode: Product barcode if available
            product_name: Product name from OCR if barcode failed

        Returns:
            NutritionData if found, None otherwise
        """
        # Try barcode first
        if barcode:
            logger.info(f"Trying OpenFoodFacts barcode: {barcode}")
            data = await self.openfoodfacts.get_by_barcode(barcode)
            if data:
                return data

        # Try text search
        if product_name:
            logger.info(f"Trying OpenFoodFacts search: {product_name}")
            data = await self.openfoodfacts.search_by_text(product_name)
            if data:
                return data

        # SearXNG fallback will be handled by DSPy ReAct agent tools
        logger.warning("No nutrition data found from primary sources")
        return None


# Global aggregator instance
nutrition_aggregator = NutritionDataAggregator()
