import os
import requests
import time
from pathlib import Path

def process_voiceover_scripts(ref_audio_path, tts_dir, output_dir):
    """
    Process all voiceover script files with IndexTTS2
    
    Args:
        ref_audio_path: Path to the reference audio file for voice cloning
        tts_dir: Directory containing the voiceover script files (.md)
        output_dir: Directory to save the generated audio files
    """
    
    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get all voiceover script files
    script_files = sorted([f for f in os.listdir(tts_dir) if f.endswith('.md')])
    
    print(f"Found {len(script_files)} voiceover script files to process")
    
    # Process each script file
    for idx, script_file in enumerate(script_files, 1):
        script_path = os.path.join(tts_dir, script_file)
        
        print(f"Processing {script_file} ({idx}/{len(script_files)})...")
        
        # Read the text content from the script file
        with open(script_path, 'r', encoding='utf-8') as f:
            text_content = f.read().strip()
        
        # Prepare the API request - different TTS systems may have different endpoints
        # Try multiple possible endpoints for IndexTTS2
        
        # Based on the log data, IndexTTS2 may accept file uploads or text
        # Let's prepare for a request that includes both text and reference audio
        
        # Common API endpoints for TTS systems
        possible_endpoints = [
            "http://localhost:7860/api/tts",  # Standard TTS API
            "http://localhost:7860/tts",      # TTS endpoint
            "http://localhost:7860/api/inference",  # Inference API
            "http://localhost:7860/run/predict",    # Gradio API
            "http://localhost:7860/"               # Root endpoint
        ]
        
        # Try to determine the correct API format based on the log
        # In the log, we see: origin text:... spk_audio_prompt:... 
        # This suggests a form-based upload might be needed
        
        # For now, we'll try the Gradio API approach since IndexTTS2 uses Gradio UI
        url = "http://localhost:7860/run/predict"
        
        # Prepare request data for Gradio API
        payload = {
            "data": [
                text_content,
                ref_audio_path,  # reference audio file
                None,  # emotion audio (if applicable)
                0.65,  # emotion alpha from the log
                None,  # emotion vector
                False, # use_emo_text
                None   # emo_text
            ],
            "event_data": None,
            "fn_index": 0,
            "session_hash": f"session_{idx:05d}"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            # Send the request to IndexTTS2
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Try to handle different response formats
                try:
                    # Check if the response is JSON (Gradio typically returns JSON)
                    response_json = response.json()
                    
                    # In Gradio API responses, audio data might be in a specific field
                    # or the response might contain a URL to the generated audio
                    if 'data' in response_json and len(response_json['data']) > 0:
                        # Extract audio data from response (this varies by implementation)
                        audio_data = response_json['data'][0]  # This is a guess based on Gradio format
                        
                        # If audio_data is a URL or path, download it
                        if isinstance(audio_data, str) and (audio_data.startswith('http') or os.path.exists(audio_data)):
                            if audio_data.startswith('http'):
                                # Download audio from URL
                                audio_response = requests.get(audio_data)
                                audio_content = audio_response.content
                            else:
                                # Read audio file directly
                                with open(audio_data, 'rb') as audio_file:
                                    audio_content = audio_file.read()
                        elif isinstance(audio_data, dict) and 'name' in audio_data:
                            # Handle file-like object response
                            audio_path = audio_data['name']
                            with open(audio_path, 'rb') as audio_file:
                                audio_content = audio_file.read()
                        else:
                            # If we can't extract audio properly, save the JSON response for debugging
                            print(f"  ? Unexpected response format for {script_file}, saving as JSON for debugging")
                            output_filename = f"audio_{idx:03d}_{script_file.replace('.md', '_debug.json')}"
                            output_path = os.path.join(output_dir, output_filename)
                            with open(output_path, 'w') as debug_file:
                                debug_file.write(response.text)
                            continue
                    else:
                        # If response is not in expected JSON format, try to get audio content directly
                        # This is unlikely for Gradio but worth trying
                        audio_content = response.content
                except ValueError:
                    # Response is not JSON, treat as direct audio content
                    audio_content = response.content
                    print("  ! Treating response as direct audio content")
                
                # Generate output filename based on the input script name
                output_filename = f"audio_{idx:03d}_{script_file.replace('.md', '.wav')}"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save the audio file
                with open(output_path, 'wb') as audio_file:
                    audio_file.write(audio_content)
                
                print(f"  ✓ Saved audio to: {output_path}")
            else:
                print(f"  ✗ Error processing {script_file}. Status code: {response.status_code}")
                print(f"  Response: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Cannot connect to IndexTTS2 API. Please make sure the server is running on http://localhost:7860")
            break
        except Exception as e:
            print(f"  ✗ Error processing {script_file}: {str(e)}")
        
        # Add delay to prevent overwhelming the server
        time.sleep(1)

if __name__ == "__main__":
    # Configuration
    REF_AUDIO_PATH = input("Enter the path to your reference audio file: ").strip()
    TTS_DIR = "/home/riju279/Documents/Projects/IndiByte/IndiByte/media/tts"
    OUTPUT_DIR = "/home/riju279/Documents/Projects/IndiByte/IndiByte/media/audio_outputs"
    
    # Validate reference audio file exists
    if not os.path.exists(REF_AUDIO_PATH):
        print(f"Error: Reference audio file does not exist: {REF_AUDIO_PATH}")
        exit(1)
    
    # Start processing
    process_voiceover_scripts(REF_AUDIO_PATH, TTS_DIR, OUTPUT_DIR)
    print("Processing complete!")