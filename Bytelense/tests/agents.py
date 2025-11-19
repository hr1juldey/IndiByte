import dspy
import json
import requests
import time
import random
from typing import Dict, Any, List, Optional
from translators import OpenFoodFactsRequestTranslator, OpenFoodFactsResponseTranslator, SearXNGResponseTranslator, DomainKnowledgeBaseTranslator

# Define signatures for different aspects of the task
class DataQualityAssessment(dspy.Signature):
    """Assess quality of raw nutritional data from all sources"""
    raw_sources = dspy.InputField(
        desc="Raw data from OpenFoodFacts, SearXNG, DomainKB"
    )
    food_name = dspy.InputField(desc="Food item (e.g., 'pav bhaji')")

    completeness_score = dspy.OutputField(
        desc="0-100: % of required fields present"
    )
    conflict_severity = dspy.OutputField(
        desc="0-100: How severe are data conflicts? "
             "100=major (406 vs 490), 0=none"
    )
    missing_fields = dspy.OutputField(
        desc="List of critical missing fields"
    )
    conflicts_found = dspy.OutputField(
        desc="List of conflicting values and sources"
    )
    recommended_path = dspy.OutputField(
        desc="'simple_cot' | 'hybrid' | 'deep_reasoning'"
    )


class DataInferenceAndReconciliation(dspy.Signature):
    """Infer missing values and reconcile conflicts"""
    available_data = dspy.InputField(desc="What we have")
    missing_nutrients = dspy.InputField(desc="What's missing")
    food_name = dspy.InputField(desc="Food item")
    conflicting_values = dspy.InputField(desc="If conflicts exist")

    inferred_nutrition = dspy.OutputField(
        desc="Complete nutrition with inferred values marked"
    )
    inference_reasoning = dspy.OutputField(
        desc="Explain how missing values were estimated"
    )
    conflict_resolution = dspy.OutputField(
        desc="Which value chosen and why"
    )
    uncertainty = dspy.OutputField(
        desc="What remains uncertain?"
    )
    confidence = dspy.OutputField(desc="0-100 confidence")


class PortionScaling(dspy.Signature):
    """Scale 100g data to user portion"""
    nutrition_per_100g = dspy.InputField(desc="Per 100g values")
    user_portion = dspy.InputField(desc="'1 plate', '1 cup', etc")
    food_name = dspy.InputField(desc="Food for density estimate")

    estimated_grams = dspy.OutputField(desc="How many grams in portion")
    scaled_nutrition = dspy.OutputField(desc="Nutrition in user portion")
    confidence = dspy.OutputField(desc="0-100 confidence in estimate")


class MedicalContextAdapter(dspy.Signature):
    """Adapt nutritional information for medical conditions"""
    nutrition_data = dspy.InputField(desc="Raw nutritional data")
    medical_condition = dspy.InputField(desc="User's medical condition (diabetes, hypertension, etc)")
    food_name = dspy.InputField(desc="Food item")

    personalized_nutrition = dspy.OutputField(
        desc="Nutrition data with medical context considerations"
    )
    medical_warnings = dspy.OutputField(
        desc="Health warnings based on condition"
    )
    recommendations = dspy.OutputField(
        desc="Medical recommendations for consumption"
    )
    confidence = dspy.OutputField(desc="0-100 confidence")


class ThinOrchestrationAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.assessor = dspy.Predict(DataQualityAssessment)

    def forward(self, raw_sources: list, food_name: str):
        """Decide routing based on data quality"""
        assessment = self.assessor(
            raw_sources=json.dumps(raw_sources),
            food_name=food_name
        )

        # Route decision
        if assessment.conflict_severity and float(assessment.conflict_severity) > 70:
            return {"path": "deep_reasoning", "reason": "High conflicts"}
        elif assessment.completeness_score and float(assessment.completeness_score) > 80:
            return {"path": "simple_cot", "reason": "Complete data"}
        else:
            return {"path": "hybrid", "reason": "Partial data"}


class DeepInferenceAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.reasoner = dspy.ChainOfThought(
            DataInferenceAndReconciliation
        )

    def forward(self, available: dict, missing: list,
                food_name: str, conflicts: list):
        """Reason through missing data and conflicts"""
        return self.reasoner(
            available_data=json.dumps(available),
            missing_nutrients=json.dumps(missing),
            food_name=food_name,
            conflicting_values=json.dumps(conflicts)
        )


class PortionScalingAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.scaler = dspy.Predict(PortionScaling)

    def forward(self, nutrition_100g: dict, portion: str, food: str):
        """Scale nutrition to user portion"""
        result = self.scaler(
            nutrition_per_100g=json.dumps(nutrition_100g),
            user_portion=portion,
            food_name=food
        )

        # Calculate scaled values
        try:
            scale_factor = float(result.estimated_grams) / 100.0
            scaled = {}
            for k, v in nutrition_100g.items():
                if isinstance(v, (int, float)):
                    scaled[k] = v * scale_factor
                else:
                    scaled[k] = v
            return {
                "scaled_nutrition": scaled,
                "estimated_grams": float(result.estimated_grams),
                "confidence": float(result.confidence) if result.confidence else 70
            }
        except:
            # Fallback if scaling calculation fails
            return {
                "scaled_nutrition": nutrition_100g,
                "estimated_grams": 100,
                "confidence": 50
            }


class MedicalAdapterAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.adapter = dspy.Predict(MedicalContextAdapter)

    def forward(self, nutrition_data: dict, medical_condition: str, food_name: str):
        """Adapt nutrition data for medical conditions"""
        return self.adapter(
            nutrition_data=json.dumps(nutrition_data),
            medical_condition=medical_condition,
            food_name=food_name
        )


class MedicalNutritionAgent(dspy.Module):
    def __init__(self):
        super().__init__()

        # Initialize all agents
        self.thin_orchestration_agent = ThinOrchestrationAgent()
        self.inference_agent = DeepInferenceAgent()
        self.scaling_agent = PortionScalingAgent()
        self.medical_adapter = MedicalAdapterAgent()

        # Initialize translators
        self.off_request_translator = OpenFoodFactsRequestTranslator()
        self.off_response_translator = OpenFoodFactsResponseTranslator()
        self.searxng_translator = SearXNGResponseTranslator()
        self.domain_translator = DomainKnowledgeBaseTranslator()

    def _query_openfoodfacts(self, food_name: str, portion: str):
        """
        Query OpenFoodFacts API for nutritional data.
        API Docs: https://world.openfoodfacts.org/data
        """
        try:
            # Search endpoint
            search_url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                "search_terms": food_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("products"):
                return {}

            # Get first product
            product = data["products"][0]

            # Return in expected format
            return {
                "product_name": product.get("product_name", ""),
                "energy_kcal_100g": product.get("nutriments", {}).get("energy-kcal_100g"),
                "carbohydrates_100g": product.get("nutriments", {}).get("carbohydrates_100g"),
                "proteins_100g": product.get("nutriments", {}).get("proteins_100g"),
                "fat_100g": product.get("nutriments", {}).get("fat_100g"),
                "fiber_100g": product.get("nutriments", {}).get("fiber_100g"),
                "sodium_100g": product.get("nutriments", {}).get("sodium_100g"),
                "sugars_100g": product.get("nutriments", {}).get("sugars_100g")
            }

        except requests.Timeout:
            print(f"  WARNING: OpenFoodFacts timeout for '{food_name}'")
            return {}
        except Exception as e:
            print(f"  WARNING: OpenFoodFacts error: {str(e)}")
            return {}

    def _query_searxng(self, food_name: str, num_results: int = 3):
        """Query SearXNG for nutritional information from web."""
        try:
            from test_pot import searxng_search_func  # Import inside the function to avoid circular import

            # Construct nutrition-focused query
            query = f"{food_name} nutrition facts calories protein carbs"

            # Get results using the existing search function
            results_json = searxng_search_func(query, num_results)
            results = json.loads(results_json)

            return results

        except ImportError:
            print(f"  WARNING: Could not import searxng_search_func, skipping SearXNG query")
            return []
        except Exception as e:
            print(f"  WARNING: SearXNG error: {str(e)}")
            return []

    def _query_domain_kb(self, food_name: str):
        """Query domain knowledge base"""
        return self.domain_translator.translate(food_name)
    
    def _simple_path(self, translated_sources: List[Dict], food_name: str, portion: str):
        """Handle simple path with complete data"""
        # Use the most reliable source
        best_source = max(translated_sources, key=lambda x: x.get("metadata", {}).get("reliability", 0))
        
        # Scale to portion
        scaled = self.scaling_agent(
            nutrition_100g=best_source["nutrition_per_100g"],
            portion=portion,
            food=food_name
        )
        
        return {
            "food": food_name,
            "portion": portion,
            "nutrition": scaled["scaled_nutrition"],
            "confidence": scaled["confidence"],
            "reasoning": f"Used most reliable source: {best_source.get('source', 'unknown')}"
        }
    
    def _hybrid_path(self, translated_sources: List[Dict], food_name: str, portion: str):
        """Handle hybrid path with partial data"""
        # Merge data from multiple sources
        merged_nutrition = {}
        for source in translated_sources:
            for key, value in source.get("nutrition_per_100g", {}).items():
                if value is not None and merged_nutrition.get(key) is None:
                    merged_nutrition[key] = value
        
        # Infer missing values
        available = merged_nutrition
        missing = [k for k, v in merged_nutrition.items() if v is None]
        
        # Use domain knowledge to infer missing values
        domain_data = self._query_domain_kb(food_name)
        for key, value in domain_data.get("nutrition_per_100g", {}).items():
            if key not in merged_nutrition or merged_nutrition[key] is None:
                merged_nutrition[key] = value
        
        # Scale to portion
        scaled = self.scaling_agent(
            nutrition_100g=merged_nutrition,
            portion=portion,
            food=food_name
        )
        
        return {
            "food": food_name,
            "portion": portion,
            "nutrition": scaled["scaled_nutrition"],
            "confidence": scaled["confidence"],
            "reasoning": "Hybrid path: Merged data from multiple sources and inferred missing values"
        }
    
    def _deep_path(self, translated_sources: List[Dict], food_name: str, portion: str):
        """Handle deep reasoning path with conflicts"""
        # Collect available data and identify conflicts
        all_data = []
        for source in translated_sources:
            all_data.append(source.get("nutrition_per_100g", {}))
        
        # Find conflicts by comparing calorie values from different sources
        calories = []
        for data in all_data:
            if data.get("calories") is not None:
                calories.append(data["calories"])
        
        conflicts = []
        if len(calories) > 1:
            # Calculate differences
            for i in range(len(calories)):
                for j in range(i+1, len(calories)):
                    if abs(calories[i] - calories[j]) > 50:  # Significant difference threshold
                        conflicts.append(f"Source {i}: {calories[i]} vs Source {j}: {calories[j]}")
        
        # Use inference agent to reconcile conflicts
        available = all_data[0] if all_data else {}
        missing = [k for k, v in available.items() if v is None]
        
        inference_result = self.inference_agent(
            available=available,
            missing=missing,
            food_name=food_name,
            conflicts=conflicts
        )
        
        # Use inferred nutrition data
        inferred_nutrition = available  # fallback
        try:
            inferred_nutrition = json.loads(inference_result.inferred_nutrition)
        except:
            pass  # Use fallback if parsing fails
        
        # Scale to portion
        scaled = self.scaling_agent(
            nutrition_100g=inferred_nutrition,
            portion=portion,
            food=food_name
        )
        
        return {
            "food": food_name,
            "portion": portion,
            "nutrition": scaled["scaled_nutrition"],
            "confidence": scaled["confidence"],
            "reasoning": inference_result.inference_reasoning,
            "conflicts_resolved": inference_result.conflict_resolution
        }
    
    def forward(self, food_name: str, portion: str, medical_condition: str = "none"):
        """Main forward method that orchestrates everything"""
        # Fetch from all sources with INVERTED lookup order
        # KB-first architecture: Domain KB (accurate for common foods) → API sources (for unknowns) → Validate
        raw_sources = []

        # Try Domain KB FIRST (more accurate for common foods, prevents wrong product selection)
        print(f"  Querying Domain KB for: {food_name}")
        domain_data = self._query_domain_kb(food_name)
        if domain_data and any(v is not None for v in domain_data.values()):
            raw_sources.append(("DomainKB", domain_data))
            print(f"    Domain KB: Found data (using KB-first architecture)")
        else:
            print(f"    Domain KB: No data found, will try API sources")

        # Try OpenFoodFacts (secondary source - for rare foods not in KB)
        print(f"  Querying OpenFoodFacts for: {food_name}")
        off_data = self._query_openfoodfacts(food_name, portion)
        if off_data and any(v is not None for v in off_data.values()):  # Check for actual data
            raw_sources.append(("OpenFoodFacts", off_data))
            print(f"    OpenFoodFacts: Found data")
        else:
            print(f"    OpenFoodFacts: No data found")

        # Try SearXNG (tertiary source - last resort for web search)
        print(f"  Querying SearXNG for: {food_name}")
        searxng_data = self._query_searxng(food_name)
        if searxng_data:
            raw_sources.append(("SearXNG", searxng_data))
            print(f"    SearXNG: Found data")
        else:
            print(f"    SearXNG: No data found")

        # Translate responses to standard format
        translated_sources = []
        for source_name, raw_data in raw_sources:
            if source_name == "OpenFoodFacts":
                translated = self.off_response_translator.translate(raw_data)
            elif source_name == "SearXNG":
                translated = self.searxng_translator.translate(raw_data)
            elif source_name == "DomainKB":
                translated = raw_data  # Already in standard format
            else:
                translated = raw_data  # Use raw as fallback

            # Ensure translated data is valid
            if translated:
                translated_sources.append(translated)

        # Assess data quality using the agent
        print(f"  Assessing data quality for: {food_name}")
        quality_assessment = self.thin_orchestration_agent(
            raw_sources=translated_sources,
            food_name=food_name
        )

        # Route to appropriate path based on quality
        path = quality_assessment.get("path", "hybrid")  # Default to hybrid
        print(f"  Routing to: {path} path")

        if path == "simple_cot":
            result = self._simple_path(translated_sources, food_name, portion)
        elif path == "deep_reasoning":
            result = self._deep_path(translated_sources, food_name, portion)
        else:  # hybrid path
            result = self._hybrid_path(translated_sources, food_name, portion)

        # Apply medical context if needed
        if medical_condition and medical_condition.lower() != "none":
            print(f"  Applying medical context for: {medical_condition}")
            medical_result = self.medical_adapter(
                nutrition_data=result.get("nutrition", {}),
                medical_condition=medical_condition,
                food_name=food_name
            )
            if hasattr(medical_result, 'medical_warnings'):
                result["medical_advice"] = {
                    "warnings": medical_result.medical_warnings,
                    "recommendations": medical_result.recommendations,
                    "confidence": medical_result.confidence
                }

        # Add overall confidence
        result["overall_confidence"] = result.get("confidence", 70)
        result["food"] = food_name
        result["portion"] = portion

        return result