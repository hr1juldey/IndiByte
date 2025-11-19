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

    def translate(self, api_response: Dict) -> Dict:
        """
        Input: Raw OFF API response
        Output: Standardized nutrition schema
        """
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

        return {
            "source": "OpenFoodFacts",
            "product_name": api_response.get("product_name"),
            "nutrition_per_100g": {
                "calories": energy_kcal,
                "carbs_g": api_response.get("carbohydrates_100g"),
                "protein_g": api_response.get("proteins_100g"),
                "fat_g": api_response.get("fat_100g"),
                "fiber_g": api_response.get("fiber_100g"),
                "sodium_mg": sodium_mg,
                "sugars_g": api_response.get("sugars_100g")
            },
            "metadata": {
                "completeness": self._calc_completeness(api_response),
                "missing_fields": self._get_missing(api_response),
                "reliability": 0.85  # Database source
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
        # Define typical nutritional values per 100g for common foods
        # Expanded to include 40+ common Indian foods (V2 fix)
        self.food_knowledge_base = {
            # === BEVERAGES ===
            "tea": {
                "calories": 1,
                "carbs_g": 0.3,
                "protein_g": 0,
                "fat_g": 0,
                "fiber_g": 0,
                "sodium_mg": 2,
                "sugars_g": 0.3
            },
            "black tea": {
                "calories": 1,
                "carbs_g": 0.3,
                "protein_g": 0,
                "fat_g": 0,
                "fiber_g": 0,
                "sodium_mg": 2,
                "sugars_g": 0.3
            },
            "green tea": {
                "calories": 1,
                "carbs_g": 0.3,
                "protein_g": 0,
                "fat_g": 0,
                "fiber_g": 0,
                "sodium_mg": 2,
                "sugars_g": 0.3
            },
            "coffee": {
                "calories": 1,
                "carbs_g": 0,
                "protein_g": 0.1,
                "fat_g": 0,
                "fiber_g": 0,
                "sodium_mg": 5,
                "sugars_g": 0
            },

            # === INDIAN STAPLES ===
            "rice": {"calories": 130, "carbs_g": 28, "protein_g": 2.7, "fat_g": 0.3, "fiber_g": 0.4, "sodium_mg": 1, "sugars_g": 0.1},
            "white rice": {"calories": 130, "carbs_g": 28, "protein_g": 2.7, "fat_g": 0.3, "fiber_g": 0.4, "sodium_mg": 1, "sugars_g": 0.1},
            "brown rice": {"calories": 112, "carbs_g": 24, "protein_g": 2.6, "fat_g": 0.9, "fiber_g": 1.8, "sodium_mg": 5, "sugars_g": 0.4},
            "roti": {"calories": 71, "carbs_g": 15, "protein_g": 3, "fat_g": 0.4, "fiber_g": 2.7, "sodium_mg": 119, "sugars_g": 0.4},
            "chapati": {"calories": 71, "carbs_g": 15, "protein_g": 3, "fat_g": 0.4, "fiber_g": 2.7, "sodium_mg": 119, "sugars_g": 0.4},
            "naan": {"calories": 262, "carbs_g": 45, "protein_g": 9, "fat_g": 5, "fiber_g": 2, "sodium_mg": 419, "sugars_g": 3.5},
            "paratha": {"calories": 290, "carbs_g": 36, "protein_g": 6, "fat_g": 13, "fiber_g": 2, "sodium_mg": 400, "sugars_g": 1.5},

            # === FISH & SEAFOOD ===
            "rohu fish": {"calories": 97, "carbs_g": 0, "protein_g": 19, "fat_g": 2, "fiber_g": 0, "sodium_mg": 55, "sugars_g": 0},
            "rohu": {"calories": 97, "carbs_g": 0, "protein_g": 19, "fat_g": 2, "fiber_g": 0, "sodium_mg": 55, "sugars_g": 0},
            "katla fish": {"calories": 96, "carbs_g": 0, "protein_g": 17.5, "fat_g": 2.7, "fiber_g": 0, "sodium_mg": 59, "sugars_g": 0},
            "hilsa fish": {"calories": 310, "carbs_g": 0, "protein_g": 18, "fat_g": 25, "fiber_g": 0, "sodium_mg": 65, "sugars_g": 0},

            # === EGGS ===
            "egg": {"calories": 155, "carbs_g": 1.1, "protein_g": 13, "fat_g": 11, "fiber_g": 0, "sodium_mg": 124, "sugars_g": 1.1},
            "boiled egg": {"calories": 155, "carbs_g": 1.1, "protein_g": 13, "fat_g": 11, "fiber_g": 0, "sodium_mg": 124, "sugars_g": 1.1},
            "chicken eggs": {"calories": 155, "carbs_g": 1.1, "protein_g": 13, "fat_g": 11, "fiber_g": 0, "sodium_mg": 124, "sugars_g": 1.1},
            "fried egg": {"calories": 196, "carbs_g": 0.8, "protein_g": 13.6, "fat_g": 15, "fiber_g": 0, "sodium_mg": 207, "sugars_g": 0.4},

            # === VEGETABLES ===
            "cucumber": {"calories": 16, "carbs_g": 3.6, "protein_g": 0.7, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 1.7},
            "cucumbers": {"calories": 16, "carbs_g": 3.6, "protein_g": 0.7, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 1.7},
            "potato": {"calories": 77, "carbs_g": 17, "protein_g": 2, "fat_g": 0.1, "fiber_g": 2.2, "sodium_mg": 6, "sugars_g": 0.8},
            "pumpkin": {"calories": 26, "carbs_g": 6.5, "protein_g": 1, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 1, "sugars_g": 2.8},
            "alu posto": {"calories": 180, "carbs_g": 20, "protein_g": 5, "fat_g": 9, "fiber_g": 3, "sodium_mg": 350, "sugars_g": 2},

            # === FRUITS ===
            "banana": {"calories": 89, "carbs_g": 23, "protein_g": 1.1, "fat_g": 0.3, "fiber_g": 2.6, "sodium_mg": 1, "sugars_g": 12},
            "bananas": {"calories": 89, "carbs_g": 23, "protein_g": 1.1, "fat_g": 0.3, "fiber_g": 2.6, "sodium_mg": 1, "sugars_g": 12},
            "apple": {"calories": 52, "carbs_g": 14, "protein_g": 0.3, "fat_g": 0.2, "fiber_g": 2.4, "sodium_mg": 1, "sugars_g": 10},
            "water apple": {"calories": 25, "carbs_g": 6, "protein_g": 0.6, "fat_g": 0.1, "fiber_g": 0.9, "sodium_mg": 7, "sugars_g": 4.5},
            "watermelon": {"calories": 30, "carbs_g": 8, "protein_g": 0.6, "fat_g": 0.2, "fiber_g": 0.4, "sodium_mg": 1, "sugars_g": 6},
            "mosambi": {"calories": 43, "carbs_g": 9, "protein_g": 0.7, "fat_g": 0.2, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 8},
            "mousumbi": {"calories": 43, "carbs_g": 9, "protein_g": 0.7, "fat_g": 0.2, "fiber_g": 0.5, "sodium_mg": 2, "sugars_g": 8},
            "lemon": {"calories": 29, "carbs_g": 9, "protein_g": 1.1, "fat_g": 0.3, "fiber_g": 2.8, "sodium_mg": 2, "sugars_g": 2.5},

            # === SNACKS ===
            "chips": {"calories": 540, "carbs_g": 47, "protein_g": 6, "fat_g": 37, "fiber_g": 4, "sodium_mg": 850, "sugars_g": 0.5},
            "potato chips": {"calories": 540, "carbs_g": 47, "protein_g": 6, "fat_g": 37, "fiber_g": 4, "sodium_mg": 850, "sugars_g": 0.5},

            # === CURRIES ===
            "pav bhaji": {"calories": 200, "carbs_g": 25, "protein_g": 4, "fat_g": 8, "fiber_g": 2, "sodium_mg": 400, "sugars_g": 3},
            "dal": {"calories": 116, "carbs_g": 20, "protein_g": 9, "fat_g": 0.4, "fiber_g": 8, "sodium_mg": 238, "sugars_g": 2},
            "vegetable soup": {"calories": 67, "carbs_g": 12, "protein_g": 3.4, "fat_g": 0.7, "fiber_g": 3, "sodium_mg": 450, "sugars_g": 5},

            # === ADDITIONAL INDIAN FOODS ===
            "paneer": {"calories": 291, "carbs_g": 3.6, "protein_g": 21.4, "fat_g": 22.2, "fiber_g": 0, "sodium_mg": 22, "sugars_g": 1.6},
            "dosa": {"calories": 133, "carbs_g": 23.8, "protein_g": 5, "fat_g": 2.5, "fiber_g": 2.7, "sodium_mg": 8, "sugars_g": 0.8},
            "idli": {"calories": 39, "carbs_g": 8.1, "protein_g": 1.7, "fat_g": 0.2, "fiber_g": 1.2, "sodium_mg": 2, "sugars_g": 0.6},
            "poha": {"calories": 110, "carbs_g": 23, "protein_g": 2.4, "fat_g": 1.5, "fiber_g": 1.3, "sodium_mg": 4, "sugars_g": 0.5},
            "upma": {"calories": 96, "carbs_g": 20, "protein_g": 2.4, "fat_g": 0.7, "fiber_g": 1.3, "sodium_mg": 2, "sugars_g": 0.3},
            "medu vada": {"calories": 152, "carbs_g": 23.6, "protein_g": 7.1, "fat_g": 3.6, "fiber_g": 2.2, "sodium_mg": 8, "sugars_g": 0.6},
            "sambar": {"calories": 49, "carbs_g": 7.7, "protein_g": 2.5, "fat_g": 1.1, "fiber_g": 2.1, "sodium_mg": 653, "sugars_g": 2.1},
            "raita": {"calories": 54, "carbs_g": 3.8, "protein_g": 3.4, "fat_g": 3.1, "fiber_g": 0.4, "sodium_mg": 227, "sugars_g": 3.8},
            "curd": {"calories": 59, "carbs_g": 3.6, "protein_g": 3.8, "fat_g": 3.3, "fiber_g": 0, "sodium_mg": 36, "sugars_g": 3.6},
            "lassi": {"calories": 105, "carbs_g": 16.4, "protein_g": 3.8, "fat_g": 2.7, "fiber_g": 0, "sodium_mg": 46, "sugars_g": 15.8},
            "buttermilk": {"calories": 48, "carbs_g": 5.2, "protein_g": 3.4, "fat_g": 1.9, "fiber_g": 0, "sodium_mg": 30, "sugars_g": 5.2},
            "khichdi": {"calories": 107, "carbs_g": 19.7, "protein_g": 4.4, "fat_g": 1.4, "fiber_g": 2.3, "sodium_mg": 4, "sugars_g": 0.4},
            "misal pav": {"calories": 200, "carbs_g": 25, "protein_g": 8, "fat_g": 6, "fiber_g": 5, "sodium_mg": 600, "sugars_g": 2},
            "vada pav": {"calories": 250, "carbs_g": 35, "protein_g": 6, "fat_g": 9, "fiber_g": 2, "sodium_mg": 600, "sugars_g": 5},
            "bhel puri": {"calories": 135, "carbs_g": 23, "protein_g": 3, "fat_g": 3, "fiber_g": 2, "sodium_mg": 550, "sugars_g": 4},
            "pani puri": {"calories": 150, "carbs_g": 25, "protein_g": 2, "fat_g": 1, "fiber_g": 1, "sodium_mg": 600, "sugars_g": 2},
            "samosa": {"calories": 262, "carbs_g": 24, "protein_g": 4, "fat_g": 17, "fiber_g": 2, "sodium_mg": 430, "sugars_g": 2},
            "kachori": {"calories": 380, "carbs_g": 45, "protein_g": 8, "fat_g": 18, "fiber_g": 3, "sodium_mg": 700, "sugars_g": 3},
            "jalebi": {"calories": 343, "carbs_g": 84.9, "protein_g": 2.7, "fat_g": 0.8, "fiber_g": 0, "sodium_mg": 11, "sugars_g": 67.4},
            "gulab jamun": {"calories": 348, "carbs_g": 62.8, "protein_g": 6.9, "fat_g": 8.7, "fiber_g": 0, "sodium_mg": 94, "sugars_g": 50.6},
            "rasgulla": {"calories": 148, "carbs_g": 32.6, "protein_g": 3.2, "fat_g": 0.6, "fiber_g": 0, "sodium_mg": 75, "sugars_g": 27.6}
        }

    def translate(self, food_name: str) -> Dict:
        """
        Input: Food name
        Output: Standardized nutrition schema based on domain knowledge
        """
        food_lower = food_name.lower()
        nutrition = None

        # Look for exact match first
        nutrition = self.food_knowledge_base.get(food_lower)

        # If no exact match, look for partial matches
        if nutrition is None:
            for key, value in self.food_knowledge_base.items():
                if key in food_lower or food_lower in key:
                    nutrition = value
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