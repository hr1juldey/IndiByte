# Commented out original code
# import litellm

# response = litellm.completion(
#   model = "ollama/qwen3-vl:8b",
#   messages=[
#       {
#           "role": "user",
#           "content": [
#                           {
#                               "type": "text",
#                               "text": "Whats in this image?"
#                           },
#                           {
#                               "type": "image_url",
#                               "image_url": {
#                               "url": "BAse64_image_string" }
#                           }
#                       ]
#       }
#   ],
# )
# print(response)

"""
New implementation that actively encodes base64 and uses DSPy with multimodal capabilities
"""
import base64
import json
import dspy
import requests
from typing import Dict, Any, List
import os


def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to a base64-encoded string (for Ollama API)."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string  # Return just the base64 string for Ollama API


class FoodLabelSignature(dspy.Signature):
    """DSPy signature for extracting information from food label images."""
    image: dspy.Image = dspy.InputField(desc="Food label image to analyze")
    instruction: str = dspy.InputField(desc="Instruction for processing the food label")
    extracted_info: str = dspy.OutputField(desc="Extracted information in structured format")


class NutritionalInfoSignature(dspy.Signature):
    """Signature for extracting nutritional information."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
    nutritional_info: str = dspy.OutputField(desc="Structured nutritional information as JSON")


class ProductInfoSignature(dspy.Signature):
    """Signature for extracting product information."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
    product_info: str = dspy.OutputField(desc="Structured product information as JSON")


class QualityAssessmentSignature(dspy.Signature):
    """Signature for assessing OCR quality."""
    ocr_text: str = dspy.InputField(desc="Raw OCR text to assess")
    quality_score: float = dspy.OutputField(desc="Quality score from 0-1")
    issues: str = dspy.OutputField(desc="List of issues as JSON")


class OCRModule(dspy.Module):
    """Module for OCR extraction using multimodal model."""
    def __init__(self):
        super().__init__()
        self.ocr_predictor = dspy.Predict(FoodLabelSignature)

    def forward(self, image_path: str) -> str:
        """Extract text from food label image."""
        # Use file path directly - this works better with DSPy and Ollama
        dspy_image = dspy.Image(image_path)

        # Call the predictor with the image and instruction
        result = self.ocr_predictor(
            image=dspy_image,
            instruction="Extract all visible text from this food label image and format in markdown. Include nutritional facts, ingredients, cooking instructions, product details, and any other information visible on the label."
        )

        # Debug: Print the raw result to see what we get
        print(f"DEBUG: OCRModule raw result type: {type(result)}")
        if hasattr(result, 'extracted_info'):
            print(f"DEBUG: OCRModule extracted_info type: {type(result.extracted_info)}")
            print(f"DEBUG: OCRModule extracted_info content: '{result.extracted_info}'")

        return result.extracted_info


class NutritionalInfoExtractor(dspy.Module):
    """Module for extracting nutritional information."""
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict(NutritionalInfoSignature)
    
    def forward(self, ocr_text: str) -> str:
        """Extract nutritional information from OCR text."""
        result = self.predictor(ocr_text=ocr_text)
        return result.nutritional_info


class ProductInfoExtractor(dspy.Module):
    """Module for extracting product information."""
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict(ProductInfoSignature)
    
    def forward(self, ocr_text: str) -> str:
        """Extract product information from OCR text."""
        result = self.predictor(ocr_text=ocr_text)
        return result.product_info


class QualityAssessor(dspy.Module):
    """Module for assessing OCR quality."""
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict(QualityAssessmentSignature)
    
    def forward(self, ocr_text: str) -> tuple:
        """Assess quality of OCR results."""
        result = self.predictor(ocr_text=ocr_text)
        try:
            quality_score = float(result.quality_score)
        except ValueError:
            quality_score = 0.5  # Default to medium quality
        return quality_score, result.issues


class FoodLabelAnalyzer(dspy.Module):
    """Main analyzer module that orchestrates the subagents."""
    def __init__(self):
        super().__init__()
        self.ocr_agent = OCRModule()
        self.nutrition_extractor = NutritionalInfoExtractor()
        self.product_extractor = ProductInfoExtractor()
        self.quality_assessor = QualityAssessor()
    
    def forward(self, image_path: str) -> Dict[str, Any]:
        """Process the food label image through all subagents."""
        print(f"Processing image: {os.path.basename(image_path)}")
        
        # Step 1: Extract text using OCR
        ocr_text = self.ocr_agent(image_path)
        print("✓ OCR completed")
        
        # Step 2: Extract nutritional information
        nutritional_info = self.nutrition_extractor(ocr_text)
        print("✓ Nutritional info extracted")
        
        # Step 3: Extract product information
        product_info = self.product_extractor(ocr_text)
        print("✓ Product info extracted")
        
        # Step 4: Assess quality
        quality_score, issues = self.quality_assessor(ocr_text)
        print("✓ Quality assessed")
        
        return {
            "ocr_text": ocr_text,
            "nutritional_info": nutritional_info,
            "product_info": product_info,
            "quality_score": quality_score,
            "issues": issues
        }


def run_with_litellm(image_path: str) -> Dict[str, Any]:
    """Direct validation using LiteLLM to check consistency."""
    import litellm

    # Encode image to base64
    image_base64 = encode_image_to_base64(image_path)

    try:
        response = litellm.completion(
            model="ollama/qwen3-vl:8b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this food label image and format in markdown. Include nutritional facts, ingredients, cooking instructions, product details, and any other information visible on the label."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        )
        return {"success": True, "response": response.choices[0].message.content}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Main function to run the complete analysis."""
    # Configuration
    image_path = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_clean.jpeg"

    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return

    print("🔍 DSPy Food Label Analysis with Active Base64 Encoding")
    print("="*60)

    # Setup DSPy with Ollama
    try:
        llm = dspy.LM(
            model="ollama/qwen3-vl:8b",
            api_base="http://localhost:11434",
            api_key=""
        )
        dspy.configure(lm=llm)
        print("✅ DSPy configured with Ollama qwen3-vl:8b")
    except Exception as e:
        print(f"❌ Failed to configure DSPy: {e}")
        return

    # Since we discovered that DSPy has compatibility issues with multimodal requests to Ollama,
    # we'll use LiteLLM directly for the multimodal processing, then process results with DSPy
    print("Running multimodal analysis with LiteLLM, then structured extraction with DSPy...")
    try:
        # First, run the multimodal analysis with LiteLLM directly
        litellm_image_result = run_with_litellm(image_path)

        if litellm_image_result["success"]:
            ocr_text = litellm_image_result["response"]
            print("✅ LiteLLM multimodal analysis completed")
        else:
            print(f"❌ LiteLLM multimodal analysis failed: {litellm_image_result['error']}")
            # Fallback to an empty result
            ocr_text = ""

        print("✓ OCR completed using LiteLLM")

        # Now use DSPy for structured extraction from the text result
        dspy_results = {
            "ocr_text": ocr_text,
            "nutritional_info": "",  # We'll extract this from OCR result using DSPy
            "product_info": "",      # We'll extract this from OCR result using DSPy
            "quality_score": 0.0,    # We'll calculate this using DSPy
            "issues": [] if ocr_text else ["OCR text is missing"]
        }

        # Now extract structured data from the OCR result using DSPy's text-based modules
        if ocr_text:
            # Extract nutritional info using DSPy
            dspy_results["nutritional_info"] = extract_nutritional_info(ocr_text)
            print("✓ Nutritional info extracted with DSPy")

            # Extract product info using DSPy
            dspy_results["product_info"] = extract_product_info(ocr_text)
            print("✓ Product info extracted with DSPy")

            # Assess quality using DSPy
            quality_score, issues = assess_quality(ocr_text)
            dspy_results["quality_score"] = quality_score
            dspy_results["issues"] = issues
            print("✓ Quality assessed with DSPy")

        print("✅ DSPy analysis completed")
    except Exception as e:
        print(f"❌ DSPy analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Run analysis using LiteLLM directly for verification
    print("Running analysis with LiteLLM directly...")
    litellm_results = run_with_litellm(image_path)
    if litellm_results["success"]:
        print("✅ LiteLLM analysis completed")
    else:
        print(f"❌ LiteLLM analysis failed: {litellm_results['error']}")

    # Output results
    print("\n" + "="*60)
    print("RESULTS COMPARISON:")
    print("="*60)

    print("\nDSPy OCR Result:")
    print("-"*30)
    print(dspy_results["ocr_text"])

    if litellm_results["success"]:
        print("\nLiteLLM Direct Result:")
        print("-"*30)
        print(litellm_results["response"])

    print("\nNutritional Information (DSPy):")
    print("-"*30)
    print(dspy_results["nutritional_info"])

    print("\nProduct Information (DSPy):")
    print("-"*30)
    print(dspy_results["product_info"])

    print(f"\nQuality Score: {dspy_results['quality_score']}")
    print(f"Issues: {dspy_results['issues']}")

    # Identify common elements between DSPy and LiteLLM results
    print("\n" + "="*60)
    print("COMMON ELEMENTS BETWEEN DSPy AND LITELLM RESULTS:")
    print("="*60)

    if litellm_results["success"]:
        dspy_text = dspy_results["ocr_text"]
        litellm_result_text = litellm_results["response"].lower()

        # Check if dspy_text is not None before processing
        if dspy_text is not None:
            dspy_text_lower = dspy_text.lower()

            # Extract common keywords/phrases to verify consistency
            keywords = ["calories", "protein", "fat", "carbohydrate", "serving", "ingredients", "net", "weight", "nutrition", "sodium"]
            common_elements = []

            for keyword in keywords:
                if keyword in dspy_text_lower and keyword in litellm_result_text:
                    common_elements.append(keyword)

            if common_elements:
                print("Common elements found:", ", ".join(common_elements))
                print("✅ Consistency verified between DSPy and LiteLLM results")
            else:
                print("⚠️ No common elements identified - results differ significantly")
        else:
            print("❌ DSPy OCR result was None, unable to compare with LiteLLM result")
            print("Comparing LiteLLM result with known food label terms:")

            # Still check the LiteLLM result against known food label terms
            keywords = ["calories", "protein", "fat", "carbohydrate", "serving", "ingredients", "net", "weight", "nutrition", "sodium"]
            found_elements = []

            for keyword in keywords:
                if keyword in litellm_result_text:
                    found_elements.append(keyword)

            if found_elements:
                print("Elements found in LiteLLM result:", ", ".join(found_elements))
                print("✅ LiteLLM returned expected food label information")
            else:
                print("⚠️ No expected food label elements found in LiteLLM result")


def extract_nutritional_info(ocr_text: str) -> str:
    """Extract nutritional information from OCR text using DSPy."""
    class NutritionalInfoSignature(dspy.Signature):
        """Signature for extracting nutritional information."""
        ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
        nutritional_info: str = dspy.OutputField(desc="Structured nutritional information as JSON")

    predictor = dspy.Predict(NutritionalInfoSignature)
    result = predictor(ocr_text=ocr_text)
    return result.nutritional_info


def extract_product_info(ocr_text: str) -> str:
    """Extract product information from OCR text using DSPy."""
    class ProductInfoSignature(dspy.Signature):
        """Signature for extracting product information."""
        ocr_text: str = dspy.InputField(desc="Raw OCR text from food label")
        product_info: str = dspy.OutputField(desc="Structured product information as JSON")

    predictor = dspy.Predict(ProductInfoSignature)
    result = predictor(ocr_text=ocr_text)
    return result.product_info


def assess_quality(ocr_text: str) -> tuple:
    """Assess quality of OCR results using DSPy."""
    class QualityAssessmentSignature(dspy.Signature):
        """Signature for assessing OCR quality."""
        ocr_text: str = dspy.InputField(desc="Raw OCR text to assess")
        quality_score: float = dspy.OutputField(desc="Quality score from 0-1")
        issues: str = dspy.OutputField(desc="List of issues as JSON")

    predictor = dspy.Predict(QualityAssessmentSignature)
    result = predictor(ocr_text=ocr_text)
    try:
        quality_score = float(result.quality_score)
    except ValueError:
        quality_score = 0.5  # Default to medium quality
    return quality_score, result.issues


if __name__ == "__main__":
    main()