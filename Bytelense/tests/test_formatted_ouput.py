#!/usr/bin/env python3
"""
Food Label Analysis: OCR Processing and Data Formatting

This script processes food label images using DSPy to extract OCR data,
then formats it into structured JSON for backend processing and
well-formatted markdown for frontend display, with computational
capabilities for nutritional analysis.
"""

import dspy
import base64
import json
import re
from typing import Dict, Any, List
import os

# MODEL="qwen3-vl:8b"
MODEL = "qwen2.5vl:7b"

def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to a base64-encoded string."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string


class Scanner(dspy.Signature):
    """Perform exact structured OCR of the image and return ALL details unchanged return in markdown format"""
    image_1: dspy.Image = dspy.InputField(desc="A product package image that might contain food package label and food data")
    answer: str = dspy.OutputField(desc="markdown formatted ocr data in the same layout as image")


class NutritionalInfoSignature(dspy.Signature):
    """Extract nutritional information from OCR text."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
    nutritional_info: str = dspy.OutputField(desc="JSON string containing structured nutritional information")


class IngredientsSignature(dspy.Signature):
    """Extract ingredients list from OCR text."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
    ingredients: str = dspy.OutputField(desc="JSON string containing list of ingredients")


class CookingInstructionsSignature(dspy.Signature):
    """Extract cooking instructions from OCR text."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
    cooking_steps: str = dspy.OutputField(desc="JSON string containing cooking preparation steps")


class AllergenSignature(dspy.Signature):
    """Extract allergen information from OCR text."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
    allergens: str = dspy.OutputField(desc="JSON string containing allergen warnings")


class ProductInfoSignature(dspy.Signature):
    """Extract general product information from OCR text."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
    product_info: str = dspy.OutputField(desc="JSON string containing product name, servings, etc.")


class Formatter(dspy.Signature):
    """Format raw text into clean, structured Markdown."""
    raw_text: str = dspy.InputField(
        desc="The unprocessed or messy text to be cleaned and formatted."
    )
    clean_md: str = dspy.OutputField(
        desc="Well-formatted Markdown output."
    )


class FoodLabelProcessor:
    """Main processor class that orchestrates OCR and data formatting."""

    def __init__(self, save_data: bool = False):
        self.save_data = save_data

        # Setup DSPy with Ollama
        try:
            self.llm = dspy.LM(
                model=f"ollama/{MODEL}",
                api_base="http://localhost:11434",
                api_key=""
            )
            dspy.configure(lm=self.llm)
        except Exception as e:
            print(f"Error configuring DSPy LM: {e}")
            raise

        dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)

        # Initialize DSPy modules
        self.nutritional_extractor = dspy.Predict(NutritionalInfoSignature)
        self.ingredients_extractor = dspy.Predict(IngredientsSignature)
        self.instructions_extractor = dspy.Predict(CookingInstructionsSignature)
        self.allergen_extractor = dspy.Predict(AllergenSignature)
        self.product_extractor = dspy.Predict(ProductInfoSignature)
        
    def extract_nutritional_data(self, ocr_text: str) -> Dict[str, Any]:
        """Extract nutritional information from OCR text."""
        try:
            result = self.nutritional_extractor(ocr_text=ocr_text)
            return json.loads(result.nutritional_info) if result.nutritional_info else {}
        except Exception as e:
            print(f"Error extracting nutritional info: {e}")
            # Fallback: try to parse raw nutritional data from OCR
            return self._parse_nutritional_values_from_text(ocr_text)
    
    def extract_ingredients(self, ocr_text: str) -> List[str]:
        """Extract ingredients list from OCR text."""
        try:
            result = self.ingredients_extractor(ocr_text=ocr_text)
            ingredients = json.loads(result.ingredients) if result.ingredients else []
            return ingredients if isinstance(ingredients, list) else [ingredients]
        except Exception as e:
            print(f"Error extracting ingredients: {e}")
            # Fallback: try to find ingredients in OCR text
            return self._parse_ingredients_from_text(ocr_text)
    
    def extract_cooking_instructions(self, ocr_text: str) -> List[str]:
        """Extract cooking instructions from OCR text."""
        try:
            result = self.instructions_extractor(ocr_text=ocr_text)
            instructions = json.loads(result.cooking_steps) if result.cooking_steps else []
            return instructions if isinstance(instructions, list) else [instructions]
        except Exception as e:
            print(f"Error extracting instructions: {e}")
            # Fallback: try to find cooking instructions in OCR text
            return self._parse_cooking_instructions_from_text(ocr_text)
    
    def extract_allergens(self, ocr_text: str) -> List[str]:
        """Extract allergen information from OCR text."""
        try:
            result = self.allergen_extractor(ocr_text=ocr_text)
            allergens = json.loads(result.allergens) if result.allergens else []
            return allergens if isinstance(allergens, list) else [allergens]
        except Exception as e:
            print(f"Error extracting allergens: {e}")
            # Fallback: try to find allergens in OCR text
            return self._parse_allergens_from_text(ocr_text)
    
    def extract_product_info(self, ocr_text: str) -> Dict[str, str]:
        """Extract general product information from OCR text."""
        try:
            result = self.product_extractor(ocr_text=ocr_text)
            return json.loads(result.product_info) if result.product_info else {}
        except Exception as e:
            print(f"Error extracting product info: {e}")
            # Fallback: try to parse basic product info from OCR
            return self._parse_product_info_from_text(ocr_text)
    
    def _parse_nutritional_values_from_text(self, text: str) -> Dict[str, Any]:
        """Fallback method to extract nutritional values from text."""
        nutritional_info = {}
        
        # Extract energy/calories
        energy_match = re.search(r'Energy \(kcal\)\s*\|?\s*([\d.]+)\s*\|?\s*([\d.]+)', text)
        if energy_match:
            nutritional_info['energy_kcal'] = {
                'per_100g': float(energy_match.group(1)),
                'per_serving': float(energy_match.group(2))
            }
        
        # Extract protein
        protein_match = re.search(r'Protein\s*\(g\)\s*\|?\s*([\d.]+)\s*\|?\s*([\d.]+)', text)
        if protein_match:
            nutritional_info['protein_g'] = {
                'per_100g': float(protein_match.group(1)),
                'per_serving': float(protein_match.group(2))
            }
        
        # Extract carbohydrates
        carb_match = re.search(r'Carbohydrate\s*\(g\)\s*\|?\s*([\d.]+)\s*\|?\s*([\d.]+)', text)
        if carb_match:
            nutritional_info['carbohydrate_g'] = {
                'per_100g': float(carb_match.group(1)),
                'per_serving': float(carb_match.group(2))
            }
        
        # Extract dietary fiber
        fiber_match = re.search(r'Dietary Fibre\s*\(g\)\s*\|?\s*([\d.]+)\s*\|?\s*([\d.]+)', text)
        if fiber_match:
            nutritional_info['dietary_fiber_g'] = {
                'per_100g': float(fiber_match.group(1)),
                'per_serving': float(fiber_match.group(2))
            }
        
        # Extract fats
        fat_match = re.search(r'Total Fat\s*\(g\)\s*\|?\s*([\d.]+)\s*\|?\s*([\d.]+)', text)
        if fat_match:
            nutritional_info['total_fat_g'] = {
                'per_100g': float(fat_match.group(1)),
                'per_serving': float(fat_match.group(2))
            }
        
        # Extract sodium
        sodium_match = re.search(r'Sodium\s*\(mg\)\s*\|?\s*([\d.]+)\s*\|?\s*([\d.]+)', text)
        if sodium_match:
            nutritional_info['sodium_mg'] = {
                'per_100g': float(sodium_match.group(1)),
                'per_serving': float(sodium_match.group(2))
            }
        
        # Extract servings information
        servings_match = re.search(r'No\. of Servings per pack:\s*([\d.]+)', text)
        if servings_match:
            nutritional_info['servings_per_pack'] = float(servings_match.group(1))
        
        serving_size_match = re.search(r'Serving Measure:\s*([\d.]+)\s*g', text)
        if serving_size_match:
            nutritional_info['serving_size_g'] = float(serving_size_match.group(1))
        
        return nutritional_info
    
    def _parse_ingredients_from_text(self, text: str) -> List[str]:
        """Fallback method to extract ingredients from text."""
        ingredients = []
        
        # Look for ingredients section
        ingredients_section = re.search(r'INGREDIENTS:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
        if ingredients_section:
            ingredients_text = ingredients_section.group(1).strip()
            # Split by common separators
            ingredients = [item.strip() for item in re.split(r',\s*|;\s*', ingredients_text) if item.strip()]
        
        return ingredients
    
    def _parse_cooking_instructions_from_text(self, text: str) -> List[str]:
        """Fallback method to extract cooking instructions from text."""
        instructions = []
        
        # Look for cooking instructions section
        cooking_section = re.search(r'Cooking Instructions\s*(.*?)(?=\n\w|\n\s*\*|$)', text, re.DOTALL)
        if not cooking_section:
            # Alternative pattern
            cooking_section = re.search(r'(Put.*?mins\.)', text, re.DOTALL)
        
        if cooking_section:
            instructions_text = cooking_section.group(1)
            # Split by newlines or other delimiters
            potential_steps = re.split(r'\n\s*\n|;\s*|\d+\.\s*|- ', instructions_text)
            for step in potential_steps:
                step = step.strip()
                if step and len(step) > 10:  # Filter out very short fragments
                    instructions.append(step)
        else:
            # Extract basic cooking instructions
            basic_steps = re.findall(r'(Put.*?mins\.)', text)
            instructions.extend(basic_steps)
        
        return instructions
    
    def _parse_allergens_from_text(self, text: str) -> List[str]:
        """Fallback method to extract allergens from text."""
        allergens = []
        
        # Look for allergen section
        allergen_section = re.search(r'Allergen Advice:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
        if allergen_section:
            allergen_text = allergen_section.group(1).strip()
            allergens = [item.strip() for item in re.split(r',\s*|;\s*', allergen_text) if item.strip()]
        
        return allergens
    
    def _parse_product_info_from_text(self, text: str) -> Dict[str, str]:
        """Fallback method to extract product info from text."""
        product_info = {}
        
        # Extract product name if present
        name_match = re.search(r'INGREDIENTS:\s*(\w+)', text)
        if name_match:
            product_info['name'] = name_match.group(1)
        
        # Extract basic product type
        if 'Oats' in text:
            if 'product_info' not in product_info:
                product_info['name'] = 'Oats'
            product_info['category'] = 'Cereal/Groats'
        
        return product_info
    
    def compute_nutritional_analysis(self, nutritional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform computations on nutritional data."""
        analysis = {}
        
        if 'energy_kcal' in nutritional_data and 'per_serving' in nutritional_data['energy_kcal']:
            analysis['energy_per_serving'] = nutritional_data['energy_kcal']['per_serving']
        
        if 'protein_g' in nutritional_data and 'per_serving' in nutritional_data['protein_g']:
            analysis['protein_per_serving'] = nutritional_data['protein_g']['per_serving']
        
        if 'carbohydrate_g' in nutritional_data and 'per_serving' in nutritional_data['carbohydrate_g']:
            analysis['carbs_per_serving'] = nutritional_data['carbohydrate_g']['per_serving']
        
        if 'dietary_fiber_g' in nutritional_data and 'per_serving' in nutritional_data['dietary_fiber_g']:
            analysis['fiber_per_serving'] = nutritional_data['dietary_fiber_g']['per_serving']
        
        if 'total_fat_g' in nutritional_data and 'per_serving' in nutritional_data['total_fat_g']:
            analysis['fat_per_serving'] = nutritional_data['total_fat_g']['per_serving']
        
        # Calculate nutritional density
        if analysis.get('energy_per_serving', 0) > 0:
            if 'protein_per_serving' in analysis:
                analysis['protein_calories_ratio'] = (analysis['protein_per_serving'] * 4) / analysis['energy_per_serving'] if analysis['energy_per_serving'] > 0 else 0
            
            if 'carbs_per_serving' in analysis:
                analysis['carbs_calories_ratio'] = (analysis['carbs_per_serving'] * 4) / analysis['energy_per_serving'] if analysis['energy_per_serving'] > 0 else 0
            
            if 'fat_per_serving' in analysis:
                analysis['fat_calories_ratio'] = (analysis['fat_per_serving'] * 9) / analysis['energy_per_serving'] if analysis['energy_per_serving'] > 0 else 0
        
        return analysis

    def process_food_label(self, image_path: str, debug: bool = False) -> Dict[str, Any]:
        """Main method to process the food label image and return structured data."""
        # Check if image file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        if debug:
            print(f"Debug: Processing image at path {image_path}")

        # Required three lines - DO NOT CHANGE
        image_url = image_path
        classify = dspy.Predict(Scanner)

        try:
            if debug:
                print("Debug: Starting OCR extraction...")
            result = classify(image_1=dspy.Image(image_url, download=True))
            if debug:
                print("Debug: OCR extraction completed.")
        except Exception as e:
            print(f"Error during OCR extraction: {e}")
            # Provide fallback with empty data
            result = type('obj', (object,), {'answer': 'Empty'})()

        ocr_text = result.answer or ""

        if debug:
            print(f"Debug: OCR text length: {len(ocr_text)} characters")
            if len(ocr_text) > 0:
                print(f"Debug: OCR text preview: {ocr_text[:1000]}...\n")

        # If OCR text is empty, provide fallback empty values
        if not ocr_text.strip():
            print("Warning: OCR returned empty text. Using fallback values.")
            structured_data = {
                "product_info": {},
                "ingredients": [],
                "nutritional_info": {},
                "nutritional_analysis": {},
                "cooking_instructions": [],
                "allergens": [],
                "raw_ocr_text": ocr_text
            }
        else:
            # Extract all information
            if debug:
                print("Debug: Extracting nutritional information...")
            nutritional_data = self.extract_nutritional_data(ocr_text)

            if debug:
                print("Debug: Extracting ingredients...")
            ingredients = self.extract_ingredients(ocr_text)

            if debug:
                print("Debug: Extracting cooking instructions...")
            cooking_instructions = self.extract_cooking_instructions(ocr_text)

            if debug:
                print("Debug: Extracting allergen information...")
            allergens = self.extract_allergens(ocr_text)

            if debug:
                print("Debug: Extracting product information...")
            product_info = self.extract_product_info(ocr_text)

            # Perform nutritional computations
            if debug:
                print("Debug: Performing nutritional analysis...")
            nutritional_analysis = self.compute_nutritional_analysis(nutritional_data)

            # Validate and clean structured data
            structured_data = {
                "product_info": product_info or {},
                "ingredients": ingredients or [],
                "nutritional_info": nutritional_data or {},
                "nutritional_analysis": nutritional_analysis or {},
                "cooking_instructions": cooking_instructions or [],
                "allergens": allergens or [],
                "raw_ocr_text": ocr_text
            }

            # Ensure nutritional_info has proper structure
            if 'servings_per_pack' not in structured_data['nutritional_info']:
                structured_data['nutritional_info']['servings_per_pack'] = 0
            if 'serving_size_g' not in structured_data['nutritional_info']:
                structured_data['nutritional_info']['serving_size_g'] = 0

        if debug:
            print("Debug: Generating markdown output...")

        # Generate formatted markdown
        try:
            markdown_output = self._generate_markdown_output(structured_data)
        except Exception as e:
            print(f"Error generating markdown: {e}")
            markdown_output = "# Error\n\nCould not generate markdown output due to processing error."

        if debug:
            print("Debug: Processing completed successfully.")

        # Optionally save data
        if self.save_data:
            try:
                self._save_outputs(structured_data, markdown_output)
            except Exception as e:
                print(f"Error saving outputs: {e}")

        return {
            "json_data": structured_data,
            "markdown": markdown_output
        }
    
    def _generate_markdown_output(self, structured_data: Dict[str, Any]) -> str:
        """Generate properly formatted markdown from structured data."""
        md = []
        md.append("# Food Product Analysis\n")
        
        # Product Info
        product_info = structured_data.get("product_info", {})
        if product_info:
            md.append("## Product Information\n")
            for key, value in product_info.items():
                md.append(f"- **{key.replace('_', ' ').title()}**: {value}\n")
            md.append("")
        
        # Ingredients
        ingredients = structured_data.get("ingredients", [])
        if ingredients:
            md.append("## Ingredients\n")
            for i, ingredient in enumerate(ingredients, 1):
                md.append(f"{i}. {ingredient}\n")
            md.append("")
        
        # Nutritional Information
        nutritional_info = structured_data.get("nutritional_info", {})
        if nutritional_info:
            md.append("## Nutritional Information (Per Serving)\n")
            if 'energy_kcal' in nutritional_info:
                md.append(f"- **Energy**: {nutritional_info['energy_kcal'].get('per_serving', 'N/A')} kcal\n")
            if 'protein_g' in nutritional_info:
                md.append(f"- **Protein**: {nutritional_info['protein_g'].get('per_serving', 'N/A')} g\n")
            if 'carbohydrate_g' in nutritional_info:
                md.append(f"- **Carbohydrate**: {nutritional_info['carbohydrate_g'].get('per_serving', 'N/A')} g\n")
            if 'dietary_fiber_g' in nutritional_info:
                md.append(f"- **Dietary Fiber**: {nutritional_info['dietary_fiber_g'].get('per_serving', 'N/A')} g\n")
            if 'total_fat_g' in nutritional_info:
                md.append(f"- **Total Fat**: {nutritional_info['total_fat_g'].get('per_serving', 'N/A')} g\n")
            
            # Add per 100g info
            md.append("\n### Per 100g\n")
            if 'energy_kcal' in nutritional_info:
                md.append(f"- **Energy**: {nutritional_info['energy_kcal'].get('per_100g', 'N/A')} kcal\n")
            if 'protein_g' in nutritional_info:
                md.append(f"- **Protein**: {nutritional_info['protein_g'].get('per_100g', 'N/A')} g\n")
            if 'carbohydrate_g' in nutritional_info:
                md.append(f"- **Carbohydrate**: {nutritional_info['carbohydrate_g'].get('per_100g', 'N/A')} g\n")
            if 'dietary_fiber_g' in nutritional_info:
                md.append(f"- **Dietary Fiber**: {nutritional_info['dietary_fiber_g'].get('per_100g', 'N/A')} g\n")
            if 'total_fat_g' in nutritional_info:
                md.append(f"- **Total Fat**: {nutritional_info['total_fat_g'].get('per_100g', 'N/A')} g\n")
            
            md.append("")
        
        # Nutritional Analysis
        analysis = structured_data.get("nutritional_analysis", {})
        if analysis:
            md.append("## Nutritional Analysis\n")
            for key, value in analysis.items():
                if isinstance(value, float):
                    md.append(f"- **{key.replace('_', ' ').title()}**: {value:.2f}\n")
                else:
                    md.append(f"- **{key.replace('_', ' ').title()}**: {value}\n")
            md.append("")
        
        # Cooking Instructions
        instructions = structured_data.get("cooking_instructions", [])
        if instructions:
            md.append("## Cooking Instructions\n")
            for i, instruction in enumerate(instructions, 1):
                md.append(f"{i}. {instruction}\n")
            md.append("")
        
        # Allergens
        allergens = structured_data.get("allergens", [])
        if allergens:
            md.append("## Allergen Information\n")
            for allergen in allergens:
                md.append(f"- {allergen}\n")
            md.append("")
        
        # Raw OCR (optional - for debugging)
        md.append("---\n")
        md.append("## Raw OCR Text\n")
        md.append(f"```\n{structured_data.get('raw_ocr_text', '')}\n```\n")
        
        return "\n".join(md)
    
    def _save_outputs(self, structured_data: Dict[str, Any], markdown_output: str):
        """Save JSON and markdown outputs to files."""
        # Create output directory if it doesn't exist
        output_dir = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON
        json_path = os.path.join(output_dir, "food_label_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        # Save Markdown
        md_path = os.path.join(output_dir, "food_label_analysis.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_output)
        
        print(f"Outputs saved to: {json_path} and {md_path}")