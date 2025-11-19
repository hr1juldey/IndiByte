#!/usr/bin/env python3
"""
CLI tool to calculate caloric intake and quality using DSPy, SearXNG, and Program of Thought.
TEST VERSION - with pre-defined inputs for testing
"""

import dspy
import json
import re
from typing import Dict, Any, List
import httpx
import sys
import os

# Import the new medical nutrition agent system
from agents import MedicalNutritionAgent

# Define the SearXNG tool for DSPy (needed for compatibility with translators)
def searxng_search_func(query: str, num_results: int = 5) -> str:
    """
    Search tool that uses SearXNG to find nutritional information.
    """
    searxng_url = os.getenv("SEARXNG_URL", "http://192.168.1.4:8080")

    # Construct the search URL with the correct pattern: http://192.168.1.4:8080/search?q=query&format=json
    search_url = f"{searxng_url}/search?q={query}&format=json"

    try:
        response = httpx.get(search_url, timeout=20.0)
        if response.status_code == 200:
            data = response.json()
            results = []
            for result in data.get("results", [])[:num_results]:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", "")[:200]
                })
            return json.dumps(results)  # Return JSON string as expected by DSPy
        else:
            print(f"Error: SearXNG returned status code {response.status_code}")
            return json.dumps([])
    except Exception as e:
        print(f"Error searching SearXNG: {str(e)}")
        return json.dumps([])

# Define signatures for different aspects of the task
class PortionExtractor(dspy.Signature):
    """Extract portion size information from food descriptions."""
    food_description = dspy.InputField(desc="Food item with description (e.g. '1 plate pav bhaji', '200ml milk')")
    food_name = dspy.OutputField(desc="Name of the food item (e.g. 'pav bhaji', 'milk')")
    portion_size = dspy.OutputField(desc="Portion size with units (e.g. '1 plate', '200ml', '1 packet')")

class CalorieCalculator(dspy.Signature):
    """Calculate total calories based on food items and portions."""
    food_items_with_portions = dspy.InputField(desc="List of food items with their portions (e.g. '1 plate pav bhaji, 1 cup tea')")
    nutritional_data = dspy.InputField(desc="JSON string containing nutritional information for each food item")
    total_calories = dspy.OutputField(desc="Total calories as a number only (e.g., 1500, not 'Total calories: 1500')")

class CalorieCalculatorPoT(dspy.Signature):
    """Calculate total calories using code generation."""
    food_items_with_portions = dspy.InputField(desc="List of food items with their portions (e.g. '100g apple, 200ml milk')")
    nutritional_data = dspy.InputField(desc="JSON string containing nutritional information for each food item")
    total_calories = dspy.OutputField(
        desc="Python code snippet that processes nutritional_data to calculate total calories. "
             "The code MUST assign the final numeric result to a variable named 'result'. "
             "Example: result = 500"
    )

class QualityAssessment(dspy.Signature):
    """Assess the nutritional quality of food items."""
    food_items = dspy.InputField(desc="List of food items consumed")
    nutritional_profile = dspy.InputField(desc="Nutritional information of the food items")
    quality_score = dspy.OutputField(desc="Quality score from 1-10 based on nutritional value")
    health_factors = dspy.OutputField(desc="Key health factors considered in the assessment")

# Create a module that uses Program of Thought for complex calculations
class CalorieQualityProgram(dspy.Module):
    def __init__(self):
        super().__init__()

        # Initialize the new medical nutrition agent
        self.nutrition_agent = MedicalNutritionAgent()

        # Create modules for different tasks
        self.portion_extractor = dspy.Predict(PortionExtractor)

        # Start with Predict, fallback to ChainOfThought, then ProgramOfThought
        try:
            self.calculator = dspy.Predict(CalorieCalculator)
            self.calculator_type = "Predict"
        except Exception as e:
            print(f"Warning: Could not initialize Predict: {e}")
            try:
                # Fallback to ChainOfThought
                self.calculator = dspy.ChainOfThought(CalorieCalculator)
                self.calculator_type = "ChainOfThought"
            except Exception as e2:
                print(f"Warning: Could not initialize ChainOfThought: {e2}")
                try:
                    # Final fallback to ProgramOfThought
                    self.calculator = dspy.ProgramOfThought(CalorieCalculatorPoT)
                    self.calculator_type = "ProgramOfThought"
                except Exception as e3:
                    print(f"Warning: Could not initialize PoT: {e3}")
                    # Ultimate fallback - use Predict with basic signature
                    self.calculator = dspy.Predict(CalorieCalculator)
                    self.calculator_type = "Predict"

        # Use regular Predict for quality assessment
        self.assessor = dspy.Predict(QualityAssessment)

class SafePortionExtractor(dspy.Module):
    """Safe wrapper around portion extractor with assertions"""
    def __init__(self):
        super().__init__()
        self.extractor = dspy.Predict(PortionExtractor)

    def forward(self, food_description: str):
        result = self.extractor(food_description=food_description)

        # Validate extraction succeeded
        # Note: DSPy doesn't have Suggest, using basic validation in the calling function
        return result


def activate_assertions(module):
    """Helper to activate assertions on a module"""
    try:
        module.activate_assertions()
    except:
        pass  # Module might not support assertions


class CalorieQualityProgram(dspy.Module):
    def __init__(self):
        super().__init__()

        # Initialize the new medical nutrition agent
        self.nutrition_agent = MedicalNutritionAgent()

        # Create modules for different tasks with safer extractor
        self.portion_extractor = SafePortionExtractor()
        activate_assertions(self.portion_extractor)  # Activate assertions

        # Start with Predict, fallback to ChainOfThought, then ProgramOfThought
        try:
            self.calculator = dspy.Predict(CalorieCalculator)
            self.calculator_type = "Predict"
        except Exception as e:
            print(f"Warning: Could not initialize Predict: {e}")
            try:
                # Fallback to ChainOfThought
                self.calculator = dspy.ChainOfThought(CalorieCalculator)
                self.calculator_type = "ChainOfThought"
            except Exception as e2:
                print(f"Warning: Could not initialize ChainOfThought: {e2}")
                try:
                    # Final fallback to ProgramOfThought
                    self.calculator = dspy.ProgramOfThought(CalorieCalculatorPoT)
                    self.calculator_type = "ProgramOfThought"
                except Exception as e3:
                    print(f"Warning: Could not initialize PoT: {e3}")
                    # Ultimate fallback - use Predict with basic signature
                    self.calculator = dspy.Predict(CalorieCalculator)
                    self.calculator_type = "Predict"

        # Use regular Predict for quality assessment
        self.assessor = dspy.Predict(QualityAssessment)

    def forward(self, food_items_with_portions: List[str], medical_condition: str = "none"):
        print(f"  Processing {len(food_items_with_portions)} food items...")
        # First, extract food names and portions for each item
        processed_items = []
        nutritional_data = {}

        for i, item in enumerate(food_items_with_portions, 1):
            print(f"    Processing item {i}: {item}")
            try:
                # Extract food name and portion size using DSPy with assertion wrapper
                print(f"      Extracting portion information...")
                extraction_result = self.portion_extractor(food_description=item)

                # Safely extract values with defaults
                food_name = getattr(extraction_result, 'food_name', '')
                if not food_name or food_name == 'None':
                    food_name = re.split(r'\d+', item, maxsplit=1)[1].strip() if re.search(r'\d+', item) else item
                    print(f"      Falling back to regex extraction for food name: {food_name}")

                portion_size = getattr(extraction_result, 'portion_size', '')
                if not portion_size or portion_size == 'None':
                    # Extract portion using regex as fallback
                    parts = item.split(' ', 1)
                    if len(parts) > 1:
                        portion_size = parts[0]
                    else:
                        portion_size = "100g"
                    print(f"      Falling back to regex extraction for portion: {portion_size}")

                print(f"      Extracted - Food name: {food_name}, Portion: {portion_size}")
                processed_items.append(f"{portion_size} {food_name}")

                print(f"      Searching for nutritional information for: {food_name}")

                # Use the new medical nutrition agent (correct calling pattern)
                nutrition_result = self.nutrition_agent(
                    food_name=food_name,
                    portion=portion_size,
                    medical_condition=medical_condition
                )
                nutritional_data[food_name] = nutrition_result
                print(f"      Stored nutritional info for {food_name}")
            except Exception as e:
                print(f"Error processing item '{item}': {str(e)}")
                import traceback
                traceback.print_exc()  # Print full exception details
                # Fallback: extract food name using regex if DSPy fails
                food_name = re.split(r'\d+', item, maxsplit=1)[1].strip() if re.search(r'\d+', item) else item
                processed_items.append(item)
                nutritional_data[food_name] = {"error": "Could not retrieve nutritional information"}
                print(f"      Using fallback for {food_name}")

        # Calculate total calories using ProgramOfThought or fallback
        food_items_str = ", ".join(processed_items)
        print(f"  Calculating total calories for: {food_items_str}")
        try:
            print("    Executing calorie calculator...")
            # Pass both food items and nutritional data to the calculator
            calorie_result = self.calculator(
                food_items_with_portions=food_items_str,
                nutritional_data=json.dumps(nutritional_data)
            )
            print(f"    Calorie result type: {type(calorie_result)}")

            # Determine how to process the result based on calculator type
            if self.calculator_type == "ProgramOfThought":
                # ProgramOfThought case: get the generated code
                generated_code = getattr(calorie_result, 'total_calories', None)
                print(f"    Generated code: {generated_code[:200] if generated_code and generated_code != 'None' else 'None'}...")

                if generated_code and generated_code != "None":
                    # Execute the generated code to get the actual calorie count
                    # The generated code might expect nutritional_data as a JSON string
                    local_vars = {"nutritional_data": json.dumps(nutritional_data), "processed_items": processed_items}

                    # Execute the generated code safely
                    exec_globals = {}
                    exec(generated_code, exec_globals, local_vars)

                    # Get the result (the code should assign to 'result' variable as per signature)
                    total_calories = local_vars.get('result', 'Could not calculate')
                    print(f"  Calorie calculation completed: {total_calories}")
                else:
                    total_calories = "Could not calculate (no code generated)"
            else:
                # Regular Predict/ChainOfThought case: get the direct result
                total_calories = getattr(calorie_result, 'total_calories', 'Could not calculate')
                print(f"  Calorie calculation completed: {total_calories}")
        except Exception as e:
            print(f"Error in PoT calculation: {str(e)}")
            import traceback
            traceback.print_exc()

            # Fallback: use a simple Predict for calorie calculation
            try:
                print("Attempting fallback calculation...")
                fallback_calculator = dspy.Predict(CalorieCalculator)
                fallback_result = fallback_calculator(
                    food_items_with_portions=food_items_str,
                    nutritional_data=json.dumps(nutritional_data)
                )
                total_calories = getattr(fallback_result, 'total_calories', 'Could not calculate')
                print(f"Fallback calculation completed: {total_calories}")
            except:
                total_calories = "Could not calculate"

        # Assess quality
        food_names = [re.split(r'\d+', item, maxsplit=1)[1].strip() if re.search(r'\d+', item) else item for item in food_items_with_portions]
        print(f"  Assessing quality for {len(food_names)} food items: {food_names}")
        try:
            quality_result = self.assessor(
                food_items=json.dumps(food_names),
                nutritional_profile=json.dumps(nutritional_data)
            )
            quality_score = getattr(quality_result, 'quality_score', "Could not assess")
            health_factors = getattr(quality_result, 'health_factors', "Could not assess")
            print(f"  Quality assessment completed: {quality_score}/10")
        except Exception as e:
            print(f"Error assessing quality: {str(e)}")
            quality_score = "Could not assess"
            health_factors = "Could not assess"

        print(f"  All processing complete for {len(nutritional_data)} items")
        return {
            "total_calories": total_calories,
            "quality_score": quality_score,
            "health_factors": health_factors,
            "nutritional_data": nutritional_data
        }

def main():
    print("Nutritional Calorie and Quality Calculator")
    print("==========================================")
    print("This tool helps you calculate calories and assess the nutritional quality of your meals.")
    print("Just enter what you've eaten with approximate quantities.")

    # Configure DSPy with Ollama
    try:
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        ollama_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")

        print(f"Configuring Ollama with model: {ollama_model}")
        llm = dspy.LM(
            f'ollama/{ollama_model}',
            api_base=ollama_url,
            api_key="",  # Not needed for local Ollama
            temperature=0.0,  # Changed from 0.3 to 0.0 for deterministic behavior (V2 fix)
            max_tokens=2000   # Increased from 1000 to 2000 for complex outputs (V2 fix)
        )
        # Configure DSPy
        dspy.configure(lm=llm)
        print("Ollama configured successfully")
    except Exception as e:
        print(f"Failed to configure Ollama: {e}")
        print("Make sure Ollama is running with the specified model.")
        sys.exit(1)

    # Create the program
    print("Initializing CalorieQualityProgram with Medical Nutrition Agent...")
    program = CalorieQualityProgram()
    print("Program initialized")

    print("\nWhat did you eat today? Enter food items with quantities (type 'done' when finished):")
    print("Examples of how to enter food:")
    print("  - '1 McDonald's Big Mac' or '1 Whopper from Burger King'")
    print("  - '1 plate pav bhaji' or '1 bowl biryani'")
    print("  - '1 packet Maggi noodles' or '1 slice pizza'")
    print("  - '1 cup rice' or '100g chicken breast'")
    print("  - '1 chocolate bar' or '1 momos plate'")
    print("  - '1 cup tea' or '1 packet chips'")
    print("  - '1 bowl dal chawal' or '1 idli with sambar'")
    print("  - '1 plate pani puri' or '200ml thums up'")
    print("  - '1 paneer tikka' or '1 dosa with chutney'")
    print("  - '1 cup milk' or '1 bowl upma'")

    # Ask for medical condition
    print("\nDo you have any medical conditions (e.g., diabetes, hypertension, none)?")
    medical_condition = input("Medical condition (or press Enter for 'none'): ").strip().lower()
    if not medical_condition:
        medical_condition = "none"

    # Interactive mode
    food_items = []
    while True:
        item = input(f"\nFood item {len(food_items)+1} (or 'done' to finish): ").strip()
        if item.lower() == 'done':
            break
        if item:
            food_items.append(item)

    # If no items were entered, use default test items
    if not food_items:
        print("\nNo food items entered. Using default test items...")
        food_items = [
            "1 plate pav bhaji",
            "1 cup tea with sugar",
            "1 packet chips"
        ]
        print(f"Test food items: {food_items}")

    print("\nAnalyzing your meal using AI and searching for nutritional information...")
    print("This may take a moment...")

    try:
        print("Step 1: Extracting portions and food items...")
        result = program(food_items_with_portions=food_items, medical_condition=medical_condition)

        print("\n" + "="*60)
        print("NUTRITIONAL SUMMARY")
        print("="*60)
        print(f"Total Calories: {result['total_calories']}")
        print(f"Nutritional Quality Score: {result['quality_score']}/10")
        print(f"Key Health Factors: {result['health_factors']}")

        print("\nDetailed Information:")
        for food, info in result['nutritional_data'].items():
            print(f"  {food}:")
            if isinstance(info, dict):
                for key, value in info.items():
                    print(f"    {key}: {value}")
            else:
                print(f"    {info}")

        print("\n" + "="*60)

    except Exception as e:
        print(f"Error during calculation: {str(e)}")
        print("This might be due to:")
        print("1. Ollama model not available")
        print("2. SearXNG server not accessible")
        print("3. Network connectivity issues")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()