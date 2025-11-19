#!/usr/bin/env python3
"""
Test script for the food label processor with user-friendly output.
"""

from test_formatted_ouput import FoodLabelProcessor
import os
import dspy

def main():
    # Test with the required image path
    image_path = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_ocr.jpeg"

    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return

    print("🔍 Testing Food Label Processor")
    print("="*60)

    # Initialize processor without saving data
    processor = FoodLabelProcessor(save_data=False)

    try:
        # Process the food label with debugging enabled
        print(f"Processing image: {os.path.basename(image_path)}")
        results = processor.process_food_label(image_path, debug=True)

        print("\n" + "="*60)
        print("✅ PROCESSING COMPLETED!")
        print("="*60)

        print("\n📋 PROCESSING SUMMARY:")
        product_info = results["json_data"].get("product_info", {})
        ingredients = results["json_data"].get("ingredients", [])
        nutritional_info = results["json_data"].get("nutritional_info", {})
        cooking_instructions = results["json_data"].get("cooking_instructions", [])
        allergens = results["json_data"].get("allergens", [])

        print(f"   • Product Info Found: {'Yes' if product_info else 'No'}")
        print(f"   • Ingredients Count: {len(ingredients)}")
        print(f"   • Nutritional Info Found: {'Yes' if nutritional_info else 'No'}")
        print(f"   • Cooking Instructions Count: {len(cooking_instructions)}")
        print(f"   • Allergens Found: {'Yes' if allergens else 'No'}")

        # Test computational functions
        analysis = results["json_data"].get("nutritional_analysis", {})
        print(f"   • Nutritional Analysis Available: {'Yes' if analysis else 'No'}")

        # Ask user if they want to see full outputs
        print("\n" + "-"*60)
        show_json = input("Show full JSON data? (y/N): ").lower().strip() == 'y'
        if show_json:
            print("\n📊 JSON DATA:")
            print("-"*40)
            print(results["json_data"])

        show_md = input("\nShow full markdown output? (y/N): ").lower().strip() == 'y'
        if show_md:
            print("\n📝 MARKDOWN OUTPUT:")
            print("-"*40)
            print(results["markdown"])

        if not show_json and not show_md:
            print("\n💡 Tip: Run again and answer 'y' to see full outputs")

        print("\n" + "🎉 Analysis complete!")
        
        print("="*80)
        print("\nHistory:")
        print(dspy.inspect_history(n = 1))

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()