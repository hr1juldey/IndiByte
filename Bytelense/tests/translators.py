import json
import re
from typing import Dict, Any, List

class OpenFoodFactsRequestTranslator:
    """Convert user input to OpenFoodFacts API call"""

    def translate(self, food_name: str, portion: str) -> Dict:
        """
        Input: "pav bhaji", "1 plate"
        Output: API call parameters
        """
        return {
            "method": "text_search",
            "query": food_name,
            "fields": [
                "product_name",
                "energy_kcal_100g",
                "carbohydrates_100g",
                "proteins_100g",
                "fat_100g",
                "fiber_100g",
                "sodium_100g",
                "sugars_100g",
                "nutrition_grades"
            ],
            "context": {
                "portion_size": portion,
                "estimated_grams": self._estimate_grams(portion)
            }
        }

    def _estimate_grams(self, portion: str) -> int:
        """Convert portion description to grams"""
        estimates = {
            "plate": 300,
            "cup": 240,
            "bowl": 200,
            "packet": 35,
            "slice": 50
        }
        for key, grams in estimates.items():
            if key in portion.lower():
                return grams
        return 100  # default


class OpenFoodFactsResponseTranslator:
    """Convert raw API response to standardized format"""

    # Realistic bounds for nutrition per 100g (Fix #2: Data Validation)
    REALISTIC_BOUNDS = {
        "calories": (0, 900),        # kcal per 100g
        "carbs_g": (0, 100),         # g per 100g
        "protein_g": (0, 80),        # g per 100g
        "fat_g": (0, 100),           # g per 100g
        "fiber_g": (0, 30),          # g per 100g
        "sodium_mg": (0, 2500),      # mg per 100g (hard cap)
        "sugars_g": (0, 100),        # g per 100g
    }

    # Category-specific bounds to detect wrong product types
    CATEGORY_BOUNDS = {
        "vegetable": {"sodium_mg": (0, 100)},      # Fresh vegetables < 100mg
        "fruit": {"sodium_mg": (0, 50)},           # Fresh fruits < 50mg
        "grain": {"sodium_mg": (0, 500)},          # Grains can be higher
        "egg": {"sodium_mg": (0, 300)},            # Eggs typically ~120mg
        "fish": {"sodium_mg": (0, 300)},           # Fish typically ~50-100mg
    }

    def _detect_food_category(self, product_name: str) -> str:
        """Detect food category from product name"""
        name_lower = product_name.lower() if product_name else ""

        if any(w in name_lower for w in ["cucumber", "tomato", "carrot", "spinach", "broccoli", "lettuce", "potato"]):
            return "vegetable"
        elif any(w in name_lower for w in ["apple", "banana", "orange", "grape", "watermelon", "fruit"]):
            return "fruit"
        elif any(w in name_lower for w in ["rice", "bread", "wheat", "grain", "oat"]):
            return "grain"
        elif any(w in name_lower for w in ["egg"]):
            return "egg"
        elif any(w in name_lower for w in ["fish", "salmon", "tuna", "rohu", "katla"]):
            return "fish"
        return ""

    def _is_value_realistic(self, nutrient: str, value: float, product_name: str = "") -> bool:
        """Check if nutrient value is realistic (Fix #2)"""
        if value is None or value < 0:
            return True  # None or negative = missing data

        # Check global bounds
        if nutrient in self.REALISTIC_BOUNDS:
            min_val, max_val = self.REALISTIC_BOUNDS[nutrient]
            if not (min_val <= value <= max_val):
                print(f"      ⚠️  VALIDATION: {nutrient}={value} exceeds global bound ({min_val}-{max_val})")
                return False

        # Check category-specific bounds
        category = self._detect_food_category(product_name)
        if category and nutrient in self.CATEGORY_BOUNDS.get(category, {}):
            min_val, max_val = self.CATEGORY_BOUNDS[category][nutrient]
            if not (min_val <= value <= max_val):
                print(f"      ⚠️  VALIDATION: {product_name} ({category}) {nutrient}={value} exceeds category bound ({min_val}-{max_val})")
                return False

        return True

    def translate(self, api_response: Dict) -> Dict:
        """
        Input: Raw OFF API response
        Output: Standardized nutrition schema with validation (Fix #2)
        """
        product_name = api_response.get("product_name", "")

        energy_kcal = api_response.get("energy_kcal_100g")
        if energy_kcal is None:
            # Handle case where energy is in kJ, so we need to convert to kcal
            energy_kj = api_response.get("energy_100g")
            if energy_kj:
                energy_kcal = energy_kj / 4.184  # Convert kJ to kcal

        sodium_mg = api_response.get("sodium_100g")
        if sodium_mg is not None:
            # If sodium is provided as a ratio (e.g., 0.01), convert to mg
            sodium_mg = sodium_mg * 1000

        # Validate all values (Fix #2: Data Validation)
        nutrition_data = {
            "calories": energy_kcal,
            "carbs_g": api_response.get("carbohydrates_100g"),
            "protein_g": api_response.get("proteins_100g"),
            "fat_g": api_response.get("fat_100g"),
            "fiber_g": api_response.get("fiber_100g"),
            "sodium_mg": sodium_mg,
            "sugars_g": api_response.get("sugars_100g")
        }

        # Check each nutrient for realism
        validation_failed = False
        for nutrient, value in nutrition_data.items():
            if not self._is_value_realistic(nutrient, value, product_name):
                validation_failed = True
                # Mark unrealistic values as None so they'll be inferred/replaced
                nutrition_data[nutrient] = None

        if validation_failed:
            print(f"      ℹ️  Marked unrealistic values as None for KB fallback")

        return {
            "source": "OpenFoodFacts",
            "product_name": product_name,
            "nutrition_per_100g": nutrition_data,
            "metadata": {
                "completeness": self._calc_completeness(api_response),
                "missing_fields": self._get_missing(api_response),
                "reliability": 0.85 if not validation_failed else 0.5,  # Lower reliability if validation failed
                "validation_passed": not validation_failed
            }
        }

    def _calc_completeness(self, data: Dict) -> float:
        """% of expected fields present"""
        required = ["energy_kcal_100g", "carbohydrates_100g",
                    "proteins_100g", "fat_100g"]
        found = sum(1 for f in required if data.get(f) is not None)
        return (found / len(required)) * 100

    def _get_missing(self, data: Dict) -> List[str]:
        """List fields not in response"""
        required = ["sodium_100g", "sugars_100g", "fiber_100g"]
        return [f for f in required if data.get(f) is None]


class SearXNGResponseTranslator:
    """Convert SearXNG search results to standardized format"""

    def translate(self, search_results: List[Dict]) -> Dict:
        """
        Input: SearXNG search results
        Output: Standardized nutrition schema
        """
        # Try to extract nutritional data from search results
        nutrition_data = {
            "source": "SearXNG",
            "product_name": "",
            "nutrition_per_100g": {
                "calories": None,
                "carbs_g": None,
                "protein_g": None,
                "fat_g": None,
                "fiber_g": None,
                "sodium_mg": None,
                "sugars_g": None
            },
            "metadata": {
                "completeness": 0,
                "missing_fields": [],
                "reliability": 0.6  # Web source reliability
            }
        }

        # Extract data from search results
        for result in search_results:
            content = result.get("content", "")
            title = result.get("title", "")
            
            # Look for nutritional values in content
            if not nutrition_data["product_name"]:
                nutrition_data["product_name"] = title

            # Extract calories
            cal_match = re.search(r'(\d+)\s*calories?|calories?\s*(\d+)', content, re.IGNORECASE)
            if cal_match:
                nutrition_data["nutrition_per_100g"]["calories"] = int(cal_match.group(1) or cal_match.group(2))

            # Extract carbs
            carb_match = re.search(r'carbohydrates?\s*[:=]?\s*(\d+\.?\d*)\s*g', content, re.IGNORECASE)
            if carb_match:
                nutrition_data["nutrition_per_100g"]["carbs_g"] = float(carb_match.group(1))

            # Extract protein
            protein_match = re.search(r'protein\s*[:=]?\s*(\d+\.?\d*)\s*g', content, re.IGNORECASE)
            if protein_match:
                nutrition_data["nutrition_per_100g"]["protein_g"] = float(protein_match.group(1))

            # Extract fat
            fat_match = re.search(r'fat\s*[:=]?\s*(\d+\.?\d*)\s*g', content, re.IGNORECASE)
            if fat_match:
                nutrition_data["nutrition_per_100g"]["fat_g"] = float(fat_match.group(1))

            # Extract fiber
            fiber_match = re.search(r'fiber\s*[:=]?\s*(\d+\.?\d*)\s*g', content, re.IGNORECASE)
            if fiber_match:
                nutrition_data["nutrition_per_100g"]["fiber_g"] = float(fiber_match.group(1))

            # Extract sodium
            sodium_match = re.search(r'sodium\s*[:=]?\s*(\d+\.?\d*)\s*mg', content, re.IGNORECASE)
            if sodium_match:
                nutrition_data["nutrition_per_100g"]["sodium_mg"] = float(sodium_match.group(1))

            # Extract sugars
            sugars_match = re.search(r'sugars?\s*[:=]?\s*(\d+\.?\d*)\s*g', content, re.IGNORECASE)
            if sugars_match:
                nutrition_data["nutrition_per_100g"]["sugars_g"] = float(sugars_match.group(1))

        # Calculate completeness
        nutrition_100g = nutrition_data["nutrition_per_100g"]
        required_fields = ["calories", "carbs_g", "protein_g", "fat_g"]
        found_count = sum(1 for field in required_fields if nutrition_100g.get(field) is not None)
        nutrition_data["metadata"]["completeness"] = (found_count / len(required_fields)) * 100

        missing_fields = [field for field, value in nutrition_100g.items() if value is None]
        nutrition_data["metadata"]["missing_fields"] = missing_fields

        return nutrition_data


class DomainKnowledgeBaseTranslator:
    """Convert food name to standardized format using domain knowledge"""

    def __init__(self):
        # CONSOLIDATED KB (Fix #3): Top 20 most common Indian foods
        # Reduced from 58 foods / 108 lines to 20 foods / ~40 lines
        # Regional aliases handled separately below
        self.food_knowledge_base = {
            # === TOP 10 DAILY STAPLES (Tier 1 - Essential) ===
            "rice": {"calories": 130, "carbs_g": 28, "protein_g": 2.7, "fat_g": 0.3, "fiber_g": 0.4, "sodium_mg": 1, "sugars_g": 0.1},
            "roti": {"calories": 71, "carbs_g": 15, "protein_g": 3, "fat_g": 0.4, "fiber_g": 2.7, "sodium_mg": 119, "sugars_g": 0.4},
            "egg": {"calories": 155, "carbs_g": 1.1, "protein_g": 13, "fat_g": 11, "fiber_g": 0, "sodium_mg": 124, "sugars_g": 1.1},
            "banana": {"calories": 89, "carbs_g": 23, "protein_g": 1.1, "fat_g": 0.3, "fiber_g": 2.6, "sodium_mg": 1, "sugars_g": 12},
            "apple": {"calories": 52, "carbs_g": 14, "protein_g": 0.3, "fat_g": 0.2, "fiber_g": 2.4, "sodium_mg": 1, "sugars_g": 10},
            "cucumber": {"calories": 16, "carbs_g": 3.6, "protein_g": 0.7, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 1.7},
            "potato": {"calories": 77, "carbs_g": 17, "protein_g": 2, "fat_g": 0.1, "fiber_g": 2.2, "sodium_mg": 6, "sugars_g": 0.8},
            "dal": {"calories": 116, "carbs_g": 20, "protein_g": 9, "fat_g": 0.4, "fiber_g": 8, "sodium_mg": 238, "sugars_g": 2},
            "tea": {"calories": 1, "carbs_g": 0.3, "protein_g": 0, "fat_g": 0, "fiber_g": 0, "sodium_mg": 2, "sugars_g": 0.3},
            "paneer": {"calories": 291, "carbs_g": 3.6, "protein_g": 21.4, "fat_g": 22.2, "fiber_g": 0, "sodium_mg": 22, "sugars_g": 1.6},

            # === TOP 10 COMMON INDIAN DISHES (Tier 2) ===
            "dosa": {"calories": 133, "carbs_g": 23.8, "protein_g": 5, "fat_g": 2.5, "fiber_g": 2.7, "sodium_mg": 8, "sugars_g": 0.8},
            "idli": {"calories": 39, "carbs_g": 8.1, "protein_g": 1.7, "fat_g": 0.2, "fiber_g": 1.2, "sodium_mg": 2, "sugars_g": 0.6},
            "pav bhaji": {"calories": 200, "carbs_g": 25, "protein_g": 4, "fat_g": 8, "fiber_g": 2, "sodium_mg": 400, "sugars_g": 3},
            "samosa": {"calories": 262, "carbs_g": 24, "protein_g": 4, "fat_g": 17, "fiber_g": 2, "sodium_mg": 430, "sugars_g": 2},
            "curd": {"calories": 59, "carbs_g": 3.6, "protein_g": 3.8, "fat_g": 3.3, "fiber_g": 0, "sodium_mg": 36, "sugars_g": 3.6},
            "lassi": {"calories": 105, "carbs_g": 16.4, "protein_g": 3.8, "fat_g": 2.7, "fiber_g": 0, "sodium_mg": 46, "sugars_g": 15.8},
            "naan": {"calories": 262, "carbs_g": 45, "protein_g": 9, "fat_g": 5, "fiber_g": 2, "sodium_mg": 419, "sugars_g": 3.5},
            "vegetable soup": {"calories": 67, "carbs_g": 12, "protein_g": 3.4, "fat_g": 0.7, "fiber_g": 3, "sodium_mg": 450, "sugars_g": 5},
            "rohu": {"calories": 97, "carbs_g": 0, "protein_g": 19, "fat_g": 2, "fiber_g": 0, "sodium_mg": 55, "sugars_g": 0},
            "buttermilk": {"calories": 48, "carbs_g": 5.2, "protein_g": 3.4, "fat_g": 1.9, "fiber_g": 0, "sodium_mg": 30, "sugars_g": 5.2},
        }

        # === REGIONAL ALIASES (Fix #3: Reduce KB, handle variations) ===
        # These common variations map to the primary food in KB
        self.aliases = {
            # Staple variations
            "white rice": "rice",
            "brown rice": "rice",
            "wheat": "roti",
            "chapati": "roti",
            "boiled egg": "egg",
            "chicken eggs": "egg",
            "fried egg": "egg",
            "bananas": "banana",
            "cucumbers": "cucumber",
            "fish": "rohu",
            "rohu fish": "rohu",
            "katla": "rohu",
            "mosambi": "apple",  # Similar citrus
            "mousumbi": "apple",
            "coffee": "tea",  # Similar hot beverage
            "black tea": "tea",
            "green tea": "tea",
        }

    def translate(self, food_name: str) -> Dict:
        """
        Input: Food name
        Output: Standardized nutrition schema based on domain knowledge (with alias resolution - Fix #3)
        """
        food_lower = food_name.lower()
        nutrition = None

        # Step 1: Check if food is in aliases (Fix #3: Regional name handling)
        if food_lower in self.aliases:
            canonical_name = self.aliases[food_lower]
            nutrition = self.food_knowledge_base.get(canonical_name)
            if nutrition:
                print(f"      ℹ️  KB Alias resolution: '{food_lower}' → '{canonical_name}'")

        # Step 2: Look for exact match in KB
        if nutrition is None:
            nutrition = self.food_knowledge_base.get(food_lower)
            if nutrition:
                print(f"      ℹ️  KB Direct match found for '{food_lower}'")

        # Step 3: Look for partial matches
        if nutrition is None:
            for key, value in self.food_knowledge_base.items():
                if key in food_lower or food_lower in key:
                    nutrition = value
                    print(f"      ℹ️  KB Partial match: '{food_lower}' matched with '{key}'")
                    break

        if nutrition is None:
            # If no match found, return empty nutrition with low reliability
            return {
                "source": "DomainKnowledge",
                "product_name": food_name,
                "nutrition_per_100g": {
                    "calories": None,
                    "carbs_g": None,
                    "protein_g": None,
                    "fat_g": None,
                    "fiber_g": None,
                    "sodium_mg": None,
                    "sugars_g": None
                },
                "metadata": {
                    "completeness": 0,
                    "missing_fields": ["calories", "carbs_g", "protein_g", "fat_g"],
                    "reliability": 0.3  # Low reliability when no match
                }
            }

        # Return standardized format
        return {
            "source": "DomainKnowledge",
            "product_name": food_name,
            "nutrition_per_100g": nutrition,
            "metadata": {
                "completeness": 100,
                "missing_fields": [],
                "reliability": 0.7  # Medium reliability for domain knowledge
            }
        }