#!/usr/bin/env python3
"""
Test the OCR endpoint with collected food label images.
"""

import os
import base64
import json
import requests
import time
from typing import Dict, List


def encode_image_to_base64(image_path: str) -> str:
    """Convert image to base64 string with data URI prefix."""
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"


def test_ocr_endpoint(image_path: str, endpoint_url: str) -> Dict:
    """Test a single image with the OCR endpoint."""
    try:
        # Encode image to base64
        image_base64 = encode_image_to_base64(image_path)
        
        # Prepare request
        payload = {
            "image_base64": image_base64,
            "metadata": {"source": "test", "filename": os.path.basename(image_path)}
        }
        
        # Send request to OCR endpoint
        response = requests.post(
            endpoint_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 seconds timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "result": result,
                "error": None,
                "filename": os.path.basename(image_path),
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "success": False,
                "result": None,
                "error": f"HTTP {response.status_code}: {response.text}",
                "filename": os.path.basename(image_path),
                "response_time": response.elapsed.total_seconds()
            }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "filename": os.path.basename(image_path),
            "response_time": None
        }


def main():
    """Main function to test OCR endpoint with multiple food label images."""
    # Configuration
    endpoint_url = "http://localhost:8000/api/label/process-with-ocr"
    test_images_dir = "data/food_labels"
    
    # Get all test images
    if not os.path.exists(test_images_dir):
        print(f"Test images directory does not exist: {test_images_dir}")
        return
    
    image_files = [f for f in os.listdir(test_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"No image files found in {test_images_dir}")
        return
    
    print(f"Found {len(image_files)} test images to process")
    print("="*80)
    
    # Track results
    results = []
    successful = 0
    failed = 0
    total_tokens = 0
    
    # Process each image
    for i, img_file in enumerate(image_files):
        image_path = os.path.join(test_images_dir, img_file)
        print(f"Processing {i+1}/{len(image_files)}: {img_file}")
        
        result = test_ocr_endpoint(image_path, endpoint_url)
        results.append(result)
        
        if result["success"]:
            successful += 1
            if result["result"]["ocr_result"]:
                tokens = result["result"]["ocr_result"]["token_count"]
                total_tokens += tokens
                print(f"  ✓ Success ({tokens} tokens, {result['response_time']:.2f}s)")
            else:
                print(f"  ⚠ Success but no OCR result ({result['response_time']:.2f}s)")
        else:
            failed += 1
            print(f"  ✗ Failed: {result['error']}")
        
        print()
        time.sleep(0.5)  # Small delay to prevent overwhelming the server
    
    # Print summary
    print("="*80)
    print("TESTING SUMMARY")
    print("="*80)
    print(f"Total images processed: {len(image_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(image_files)*100:.2f}%")
    print(f"Total tokens extracted: {total_tokens}")
    
    if successful > 0:
        avg_tokens = total_tokens / successful
        print(f"Average tokens per successful OCR: {avg_tokens:.2f}")
    
    # Calculate average response time for successful requests
    successful_times = [r["response_time"] for r in results if r["success"] and r["response_time"]]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"Average response time: {avg_time:.2f}s")
    
    # Show the first few results for manual inspection
    print("\nFIRST FEW RESULTS:")
    for i, result in enumerate(results[:3]):  # Show first 3 results
        if result["success"] and result["result"]["ocr_result"]:
            print(f"\n{i+1}. {result['filename']}")
            print(f"   Quality: {result['result']['quality_analysis']['quality_tier']}")
            print(f"   Tokens: {result['result']['ocr_result']['token_count']}")
            print(f"   OCR Text Preview: {result['result']['ocr_result']['markdown'][:200]}...")
        else:
            print(f"\n{i+1}. {result['filename']} - Failed")


if __name__ == "__main__":
    main()