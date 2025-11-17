#!/usr/bin/env python3
"""
Test script to verify OCR functionality with real food label images.
"""

import base64
import requests
import json
import os

# Choose a test image
test_image_path = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_label_14.jpg"

# Check if image exists
if not os.path.exists(test_image_path):
    print(f"Test image not found: {test_image_path}")
    exit(1)

# Encode image to base64
with open(test_image_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# Prepare the request
url = "http://localhost:8002/api/label/process-with-ocr"  # Using the port we started the server on
headers = {
    "Content-Type": "application/json"
}
payload = {
    "image_base64": encoded_string,
    "metadata": {}
}

try:
    print(f"Sending request to OCR endpoint with image: {os.path.basename(test_image_path)}")
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        print("SUCCESS: OCR endpoint responded with status 200")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Message: {result.get('message', 'no message')}")
        print(f"Processing time: {result.get('total_time_ms', 0):.2f}ms")
        
        if result.get('ocr_result'):
            ocr_result = result['ocr_result']
            print(f"OCR tokens: {ocr_result.get('token_count', 0)}")
            print(f"OCR error: {ocr_result.get('error', 'unknown')}")
        else:
            print("No OCR result returned")
            
    else:
        print(f"FAILED: OCR endpoint returned status {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"ERROR: Failed to contact OCR endpoint: {e}")