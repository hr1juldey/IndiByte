#!/usr/bin/env python3
"""
End-to-end test for food label OCR processing.

This script simulates the complete workflow from image capture to OCR results
to validate the integrated system functionality with real food label images.
"""

import base64
import requests
import json
import os
import time
from typing import Dict, Any


def load_test_images(image_dir: str) -> list:
    """Load all food label images from the test directory."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    images = []

    for filename in os.listdir(image_dir):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            images.append(os.path.join(image_dir, filename))

    return images


def image_to_base64(image_path: str) -> str:
    """Convert an image to base64 string."""
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"


def run_end_to_end_test(image_path: str, backend_url: str) -> Dict[str, Any]:
    """Run a complete end-to-end test with a single food label image."""
    try:
        print(f"Running end-to-end test with image: {os.path.basename(image_path)}")

        # Convert image to base64
        image_base64 = image_to_base64(image_path)
        
        # Time the complete request
        start_time = time.time()
        
        # Make the OCR request to the backend
        response = requests.post(
            f"{backend_url}/api/label/process-with-ocr",
            headers={"Content-Type": "application/json"},
            json={
                "image_base64": image_base64,
                "metadata": {
                    "source": "end_to_end_test",
                    "timestamp": int(time.time()),
                    "original_filename": os.path.basename(image_path)
                }
            },
            timeout=300  # 5 minute timeout for processing
        )
        
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for successful OCR processing
            if result.get("status") == "success" and result.get("ocr_result"):
                ocr_result = result["ocr_result"]
                
                print(f"  ✓ Success - Time: {total_time:.2f}s")
                print(f"  - Quality tier: {result.get('quality_analysis', {}).get('quality_tier', 'unknown')}")
                print(f"  - OCR tokens: {ocr_result.get('token_count', 0)}")
                print(f"  - Error: {ocr_result.get('error', 'none')}")
                
                return {
                    "success": True,
                    "processing_time": total_time,
                    "token_count": ocr_result.get("token_count", 0),
                    "quality_tier": result.get("quality_analysis", {}).get("quality_tier"),
                    "has_error": ocr_result.get("error", False),
                    "response": result
                }
            else:
                print(f"  ✗ Partial success - Status: {result.get('status', 'unknown')}")
                print(f"  - Message: {result.get('message', 'No message')}")
                
                return {
                    "success": False,
                    "error": result.get("message", "Processing failed"),
                    "processing_time": total_time,
                    "response": result
                }
        else:
            print(f"  ✗ Failed - HTTP {response.status_code}")
            print(f"  - Error: {response.text[:200]}...")
            
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}...",
                "processing_time": total_time,
                "response": None
            }
    
    except Exception as e:
        print(f"  ✗ Error - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "processing_time": time.time() - start_time if 'start_time' in locals() else 0,
            "response": None
        }


def main():
    """Run end-to-end tests with real food label images."""
    # Configuration
    BACKEND_URL = "http://localhost:8002"
    IMAGE_DIR = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels"
    
    # Verify image directory exists
    if not os.path.exists(IMAGE_DIR):
        print(f"Error: Image directory does not exist: {IMAGE_DIR}")
        return
    
    # Get test images
    test_images = load_test_images(IMAGE_DIR)
    
    if not test_images:
        print(f"No test images found in {IMAGE_DIR}")
        return
    
    print(f"Found {len(test_images)} test images")
    print(f"Using backend URL: {BACKEND_URL}")
    print("="*80)
    
    # Results tracking
    results = []
    successful = 0
    total_tokens = 0
    total_time = 0
    
    # Process each image
    for i, img_path in enumerate(test_images):
        print(f"Processing {i+1}/{len(test_images)}")
        
        result = run_end_to_end_test(img_path, BACKEND_URL)
        results.append(result)
        
        if result["success"]:
            successful += 1
            total_tokens += result["token_count"]
            total_time += result["processing_time"]
        else:
            print(f"    Error: {result['error']}")
        
        print("")  # Empty line between results
    
    # Generate summary
    print("="*80)
    print("END-TO-END TEST SUMMARY")
    print("="*80)
    print(f"Total images processed: {len(test_images)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(test_images) - successful}")
    print(f"Success rate: {successful/len(test_images)*100:.1f}%")
    
    if successful > 0:
        print(f"Average processing time: {total_time/successful:.2f}s")
        print(f"Total tokens extracted: {total_tokens}")
        print(f"Average tokens per successful OCR: {total_tokens/successful:.1f}")
    
    print("")
    
    # Check if we meet the target success rate (>85%)
    success_rate = successful / len(test_images) * 100
    meets_target = success_rate >= 85
    
    print(f"Target success rate (>85%): {'✓ MET' if meets_target else '✗ NOT MET'}")
    print(f"Actual success rate: {success_rate:.1f}%")
    
    # Save detailed results
    with open("e2e_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total_images": len(test_images),
                "successful": successful,
                "failed": len(test_images) - successful,
                "success_rate": success_rate,
                "average_processing_time": total_time/successful if successful > 0 else 0,
                "total_tokens_extracted": total_tokens,
                "average_tokens_per_success": total_tokens/successful if successful > 0 else 0,
                "meets_target": meets_target
            },
            "detailed_results": [
                {
                    "image": os.path.basename(r.get("image_path", "unknown")),
                    **{k: v for k, v in r.items() if k != "response"}  # Exclude full response to keep file size manageable
                } for r in results
            ]
        }, f, indent=2)
    
    print("Detailed results saved to e2e_test_results.json")


if __name__ == "__main__":
    main()