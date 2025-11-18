#!/usr/bin/env python3
"""
Debug version to see what's happening
"""

import litellm
import base64
import os
import time
import threading

def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to a base64-encoded string."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string


# def main():
#     print("🔍 Debug: Testing basic LiteLLM call")
#     print("="*50)
    
#     image_path = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_clean.jpeg"
    
#     if not os.path.exists(image_path):
#         print(f"❌ Image file not found: {image_path}")
#         return

#     print(f"Processing image: {os.path.basename(image_path)}")

#     # Encode image to base64
#     image_base64 = encode_image_to_base64(image_path)
#     print(f"Image encoded, length: {len(image_base64)}")

#     try:
#         print("Making LiteLLM call...")
#         response = litellm.completion(
#             model="ollama/qwen3-vl:8b",
#             messages=[
#                     {
#             "role": "user",
#             "content": [
#                             {
#                                 "type": "text",
#                                 "text": "Perform exact structured OCR of the image and resurn ALL details unchanged return in markdown format"
#                             },
#                             {
#                                 "type": "image_url",
#                                 "image_url": {
#                                 "url": image_base64 }
#                             }
#                         ]
#                         }
#             ],
#         )
#         print("✅ LiteLLM call completed successfully!")
#         result = response.choices[0].message.content
#         print(f"Result length: {len(result) if result else 0}")
#         print(f"Showing result: {result if result else 'None'}")
        
#     except Exception as e:
#         print(f"❌ LiteLLM call failed: {e}")
#         import traceback
#         traceback.print_exc()



def main():
    print("🔍 Debug: Testing basic LiteLLM call")
    print("="*50)
    
    image_path = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_clean.jpeg"
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return

    print(f"Processing image: {os.path.basename(image_path)}")

    # Encode image to base64
    image_base64 = encode_image_to_base64(image_path)
    print(f"Image encoded, length: {len(image_base64)}")

    try:
        print("Making LiteLLM call...")

        # ---------------------------
        # ⏱️ TIME COUNTER THREAD
        # ---------------------------
        running = True

        def timer_thread():
            start = time.time()
            while running:
                elapsed = int(time.time() - start)
                print(f"⏳ Time passed: {elapsed} sec", flush=True)
                time.sleep(1)

        t = threading.Thread(target=timer_thread)
        t.daemon = True
        t.start()
        # ---------------------------

        response = litellm.completion(
            model="ollama/qwen3-vl:8b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Perform exact structured OCR of the image and resurn ALL details unchanged return in markdown format"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64
                            }
                        }
                    ]
                }
            ],
        )

        # stop timer
        running = False
        t.join(timeout=0.1)

        print("✅ LiteLLM call completed successfully!")
        result = response.choices[0].message.content
        print(f"Result length: {len(result) if result else 0}")
        print(f"Showing result: {result if result else 'None'}")
        
    except Exception as e:
        running = False  # stop timer if exception
        print(f"❌ LiteLLM call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()