import requests
import json

# Read the base64 image
with open('/home/riju279/Documents/Projects/IndiByte/IndiByte/test_image_base64.txt', 'r') as f:
    image_base64 = f.read().strip()

# Create the request payload
payload = {
    "image_base64": image_base64
}

# Send the request to the OCR endpoint
try:
    print("Sending request to OCR endpoint...")
    response = requests.post(
        "http://localhost:8000/api/label/process-with-ocr",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=120  # 2 minute timeout
    )
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("OCR processing successful!")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Message: {result.get('message', 'no message')}")
        print(f"OCR tokens: {result.get('ocr_result', {}).get('token_count', 0) if result.get('ocr_result') else 0}")
        print(f"Total time: {result.get('total_time_ms', 0)}ms")
        print(f"OCR time: {result.get('ocr_time_ms', 0)}ms")
        
        if result.get('ocr_result'):
            print(f"OCR markdown preview: {result['ocr_result']['markdown'][:200]}...")
    else:
        print(f"Request failed with status {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.Timeout:
    print("Request timed out - this might indicate the OCR processing is taking too long or failed silently")
except requests.exceptions.RequestException as e:
    print(f"Request failed with error: {e}")
    print("This might be due to server issues or the OCR processing failing")
except Exception as e:
    print(f"Unexpected error: {e}")