# Voiceover Automation Plan for IndiByte

## Objective

Create a Python script that dynamically sends pieces of script from the IndiByte workspace to the IndexTTS2 system with appropriate emotion vectors that change according to subject and delivery style, then collects the output .wav files in a folder with programmatic naming for automated voiceover generation.

## Implementation Plan

### 1. System Architecture

```
Input: Markdown script files from IndiByte workspace
    ↓
Parser: Extract text segments from markdown
    ↓
Emotion Mapper: Map content to emotion vectors
    ↓
IndexTTS2: Generate speech with emotion control
    ↓
Output Manager: Organize .wav files systematically
    ↓
Result: Complete voiceover with emotion-appropriate delivery
```

### 2. Core Components

#### 2.1 Markdown Parser

- Use `mistune` library for efficient markdown parsing
- Extract text segments while preserving document structure
- Handle different content types (headings, paragraphs, lists)
- Output structured segments with metadata

```python
import mistune

def parse_markdown_segments(file_path):
    """
    Parse markdown file into text segments for TTS processing
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    md = mistune.create_markdown(renderer=mistune.AstRenderer())
    tokens = md(content)
    
    segments = []
    for token in tokens:
        if token['type'] == 'paragraph':
            text = extract_text_from_token(token)
            if text.strip():
                segments.append({
                    'text': text,
                    'type': 'paragraph',
                    'order': len(segments)
                })
        elif token['type'] == 'heading':
            text = extract_text_from_token(token)
            segments.append({
                'text': text,
                'type': f'heading_{token["level"]}',
                'order': len(segments)
            })
    
    return segments
```

#### 2.2 Emotion Mapping System

- Use HuggingFace Transformers with pre-trained emotion classification models (e.g., GoEmotions fine-tuned models, DistilRoBERTa emotion classifier) instead of VADER for more nuanced emotion detection
- Implement content-to-emotion mapping based on transformer-based emotion classification, keyword matching, and contextual analysis
- Map to IndexTTS2's 8-element emotion vector format:
  - Position 0: Happy/Joy
  - Position 1: Angry  
  - Position 2: Sad
  - Position 3: Afraid/Fear
  - Position 4: Disgusted
  - Position 5: Melancholic (combination of sadness and other emotions)
  - Position 6: Surprised
  - Position 7: Calm/Neutral

```python
from transformers import pipeline

class ContentToEmotionMapper:
    def __init__(self, model_name="j-hartmann/emotion-english-distilroberta-base"):
        # Initialize transformer-based emotion classifier
        # Alternative models: "cardiffnlp/twitter-roberta-base-emotion", "bhadresh-savani/distilbert-base-uncased-emotion"
        self.emotion_classifier = pipeline(
            "text-classification", 
            model=model_name,
            return_all_scores=True
        )
        
        # Map the model's emotion labels to IndexTTS2's 8-element vector
        # IndexTTS2 format: [Happy, Angry, Sad, Afraid, Disgusted, Melancholic, Surprised, Calm]
        self.emotion_mapping = {
            'joy': 0,        # Happy/Joy
            'anger': 1,      # Angry
            'sadness': 2,    # Sad
            'fear': 3,       # Afraid/Fear
            'disgust': 4,    # Disgusted
            'sad': 2,        # Alternative mapping for sadness
            'surprise': 6,   # Surprised
            'neutral': 7,    # Calm/Neutral
            'anticipation': 0,  # Map to happy/joy
            'trust': 7,      # Map to calm
        }
        
        # Additional emotion keywords for more nuanced detection
        self.emotion_keywords = {
            'happy': ['happy', 'joy', 'excited', 'wonderful', 'amazing', 'fantastic', 'great', 'excellent', 'positive', 'good', 'love', 'like', 'wonderful', 'brilliant', 'awesome'],
            'angry': ['angry', 'furious', 'mad', 'rage', 'annoyed', 'frustrated', 'pissed', 'hate', 'terrible', 'horrifying', 'disgusting', 'worst'],
            'sad': ['sad', 'depressed', 'unhappy', 'miserable', 'sorrow', 'grief', 'crying', 'disappointed', 'heartbroken', 'lonely', 'mournful'],
            'afraid': ['scared', 'fear', 'afraid', 'nervous', 'anxious', 'terrified', 'worried', 'frightened', 'panicked', 'apprehensive'],
            'surprised': ['surprised', 'shocked', 'amazed', 'wow', 'incredible', 'unbelievable', 'unexpected', 'astonished', 'stunned'],
            'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'quiet', 'gentle', 'mild', 'soothing', 'contemplative']
        }

    def text_to_emotion_vector(self, text):
        # Use transformer-based emotion classification
        emotion_scores = self.emotion_classifier(text)
        
        # Initialize emotion vector (8 emotions for IndexTTS2)
        emotion_vector = [0.0] * 8
        
        # Process transformer model results
        for emotion_score in emotion_scores[0]:  # Get the first (and typically only) result
            label = emotion_score['label'].lower()
            score = emotion_score['score']
            
            # Map the model's label to our IndexTTS2 vector position
            if label in self.emotion_mapping:
                position = self.emotion_mapping[label]
                emotion_vector[position] = max(emotion_vector[position], score)
        
        # Enhance with keyword-based detection for more nuanced emotions
        text_lower = text.lower()
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Adjust intensity based on presence of keyword
                    if emotion == 'happy':
                        emotion_vector[0] = min(1.0, emotion_vector[0] + 0.3)
                    elif emotion == 'angry':
                        emotion_vector[1] = min(1.0, emotion_vector[1] + 0.3)
                    elif emotion == 'sad':
                        emotion_vector[2] = min(1.0, emotion_vector[2] + 0.3)
                    elif emotion == 'afraid':
                        emotion_vector[3] = min(1.0, emotion_vector[3] + 0.3)
                    elif emotion == 'surprised':
                        emotion_vector[6] = min(1.0, emotion_vector[6] + 0.3)
                    elif emotion == 'calm':
                        emotion_vector[7] = min(1.0, emotion_vector[7] + 0.3)
                    break  # Move to next emotion after finding first keyword match
        
        # Apply normalization to ensure values are within [0.0, 1.0] range
        emotion_vector = [min(1.0, max(0.0, val)) for val in emotion_vector]
        
        # If no emotion is detected, default to calm/neutral
        if sum(emotion_vector) == 0:
            emotion_vector[7] = 0.5  # Default to calm
        
        return emotion_vector
```

#### 2.3 IndexTTS2 Interface

- Direct integration with IndexTTS2's Python API
- Support for emotion vectors and emotion alpha control
- Handle voice cloning from reference audio
- Manage GPU/CUDA resources efficiently

```python
from indextts.infer_v2 import IndexTTS2

class IndexTTS2Wrapper:
    def __init__(self, config_path="checkpoints/config.yaml", model_dir="checkpoints"):
        self.tts = IndexTTS2(
            cfg_path=config_path, 
            model_dir=model_dir, 
            use_fp16=False, 
            use_cuda_kernel=False, 
            use_deepspeed=False
        )
    
    def generate_speech(self, text, output_path, voice_prompt, emotion_vector=None, emotion_alpha=1.0):
        # Implementation using IndexTTS2 API
        pass
```

#### 2.4 Output Management System

- Programmatic naming convention: `{base_name}_{segment_order:03d}_{emotion_type}_{timestamp}.wav`
- Organized directory structure for audio files
- Metadata tracking for each generated segment
- Batch processing capabilities

```python
import os
from datetime import datetime
from pathlib import Path

def create_output_filename(base_name, segment_order, emotion_type, timestamp=True):
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
    filename = f"{base_name}_{segment_order:03d}_{emotion_type}"
    if timestamp:
        filename += f"_{timestamp_str}"
    filename += ".wav"
    return filename

def organize_output_files(output_dir, base_name):
    output_path = Path(output_dir) / base_name
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path
```

### 3. Complete Implementation

```python
import mistune
from transformers import pipeline
from indextts.infer_v2 import IndexTTS2
from pathlib import Path
import os
from datetime import datetime
import re

class ContentToEmotionMapper:
    def __init__(self, model_name="j-hartmann/emotion-english-distilroberta-base"):
        # Initialize transformer-based emotion classifier
        # Alternative models: "cardiffnlp/twitter-roberta-base-emotion", "bhadresh-savani/distilbert-base-uncased-emotion"
        self.emotion_classifier = pipeline(
            "text-classification", 
            model=model_name,
            return_all_scores=True
        )
        
        # Map the model's emotion labels to IndexTTS2's 8-element vector
        # IndexTTS2 format: [Happy, Angry, Sad, Afraid, Disgusted, Melancholic, Surprised, Calm]
        self.emotion_mapping = {
            'joy': 0,        # Happy/Joy
            'anger': 1,      # Angry
            'sadness': 2,    # Sad
            'fear': 3,       # Afraid/Fear
            'disgust': 4,    # Disgusted
            'sad': 2,        # Alternative mapping for sadness
            'surprise': 6,   # Surprised
            'neutral': 7,    # Calm/Neutral
            'anticipation': 0,  # Map to happy/joy
            'trust': 7,      # Map to calm
        }
        
        # Additional emotion keywords for more nuanced detection
        self.emotion_keywords = {
            'happy': ['happy', 'joy', 'excited', 'wonderful', 'amazing', 'fantastic', 'great', 'excellent', 'positive', 'good', 'love', 'like', 'wonderful', 'brilliant', 'awesome'],
            'angry': ['angry', 'furious', 'mad', 'rage', 'annoyed', 'frustrated', 'pissed', 'hate', 'terrible', 'horrifying', 'disgusting', 'worst'],
            'sad': ['sad', 'depressed', 'unhappy', 'miserable', 'sorrow', 'grief', 'crying', 'disappointed', 'heartbroken', 'lonely', 'mournful'],
            'afraid': ['scared', 'fear', 'afraid', 'nervous', 'anxious', 'terrified', 'worried', 'frightened', 'panicked', 'apprehensive'],
            'surprised': ['surprised', 'shocked', 'amazed', 'wow', 'incredible', 'unbelievable', 'unexpected', 'astonished', 'stunned'],
            'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'quiet', 'gentle', 'mild', 'soothing', 'contemplative']
        }

    def text_to_emotion_vector(self, text):
        # Use transformer-based emotion classification
        emotion_scores = self.emotion_classifier(text)
        
        # Initialize emotion vector (8 emotions for IndexTTS2)
        emotion_vector = [0.0] * 8
        
        # Process transformer model results
        for emotion_score in emotion_scores[0]:  # Get the first (and typically only) result
            label = emotion_score['label'].lower()
            score = emotion_score['score']
            
            # Map the model's label to our IndexTTS2 vector position
            if label in self.emotion_mapping:
                position = self.emotion_mapping[label]
                emotion_vector[position] = max(emotion_vector[position], score)
        
        # Enhance with keyword-based detection for more nuanced emotions
        text_lower = text.lower()
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Adjust intensity based on presence of keyword
                    if emotion == 'happy':
                        emotion_vector[0] = min(1.0, emotion_vector[0] + 0.3)
                    elif emotion == 'angry':
                        emotion_vector[1] = min(1.0, emotion_vector[1] + 0.3)
                    elif emotion == 'sad':
                        emotion_vector[2] = min(1.0, emotion_vector[2] + 0.3)
                    elif emotion == 'afraid':
                        emotion_vector[3] = min(1.0, emotion_vector[3] + 0.3)
                    elif emotion == 'surprised':
                        emotion_vector[6] = min(1.0, emotion_vector[6] + 0.3)
                    elif emotion == 'calm':
                        emotion_vector[7] = min(1.0, emotion_vector[7] + 0.3)
                    break  # Move to next emotion after finding first keyword match
        
        # Apply normalization to ensure values are within [0.0, 1.0] range
        emotion_vector = [min(1.0, max(0.0, val)) for val in emotion_vector]
        
        # If no emotion is detected, default to calm/neutral
        if sum(emotion_vector) == 0:
            emotion_vector[7] = 0.5  # Default to calm
        
        return emotion_vector

def parse_markdown_segments(file_path):
    """
    Parse markdown file into text segments for TTS processing
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use mistune to parse markdown
    md = mistune.create_markdown(renderer=mistune.AstRenderer())
    tokens = md(content)
    
    segments = []
    for token in tokens:
        if token['type'] == 'paragraph':
            text = extract_text_from_token(token)
            if text.strip():  # Only add non-empty segments
                segments.append({
                    'text': text,
                    'type': 'paragraph',
                    'order': len(segments)
                })
        elif token['type'] == 'heading':
            text = extract_text_from_token(token)
            segments.append({
                'text': text,
                'type': f'heading_{token["level"]}',
                'order': len(segments)
            })
    
    return segments

def extract_text_from_token(token):
    """
    Recursively extract text from mistune tokens
    """
    if 'children' in token:
        text = ''
        for child in token['children']:
            text += extract_text_from_token(child)
        return text
    elif 'text' in token:
        return token['text']
    return ''

def create_output_filename(base_name, segment_order, emotion_type, timestamp=True):
    """
    Create systematic output filenames for TTS audio files
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
    filename = f"{base_name}_{segment_order:03d}_{emotion_type}"
    if timestamp:
        filename += f"_{timestamp_str}"
    filename += ".wav"
    return filename

class IndexTTS2Processor:
    def __init__(self, config_path="checkpoints/config.yaml", model_dir="checkpoints"):
        self.tts = IndexTTS2(
            cfg_path=config_path, 
            model_dir=model_dir, 
            use_fp16=False, 
            use_cuda_kernel=False, 
            use_deepspeed=False
        )
        self.emotion_mapper = ContentToEmotionMapper()
    
    def process_script(self, script_path, voice_prompt, output_dir="output", base_name=None):
        """
        Process a markdown script and generate TTS audio for each segment
        """
        if base_name is None:
            base_name = Path(script_path).stem
        
        # Parse the script into segments
        segments = parse_markdown_segments(script_path)
        
        # Create output directory
        output_path = Path(output_dir) / base_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for segment in segments:
            # Map content to emotion vector
            emotion_vector = self.emotion_mapper.text_to_emotion_vector(segment['text'])
            
            # Determine emotion type for naming
            emotion_type = self._get_emotion_type(emotion_vector)
            
            # Create output filename
            output_filename = create_output_filename(
                base_name, 
                segment['order'], 
                emotion_type
            )
            output_file_path = output_path / output_filename
            
            # Generate speech with emotion control
            self.tts.infer(
                spk_audio_prompt=voice_prompt,
                text=segment['text'],
                output_path=str(output_file_path),
                emo_vector=emotion_vector,
                emo_alpha=0.8,
                use_random=False,
                verbose=True
            )
            
            results.append({
                'segment_order': segment['order'],
                'text': segment['text'][:100] + "..." if len(segment['text']) > 100 else segment['text'],
                'output_file': str(output_file_path),
                'emotion_vector': emotion_vector,
                'emotion_type': emotion_type
            })
        
        return results
    
    def _get_emotion_type(self, emotion_vector):
        """
        Determine the dominant emotion type from the emotion vector
        """
        emotion_names = ['happy', 'angry', 'sad', 'afraid', 'disgusted', 'melancholic', 'surprised', 'calm']
        max_idx = emotion_vector.index(max(emotion_vector)) if max(emotion_vector) > 0.1 else 7  # Default to calm
        return emotion_names[max_idx]

# Usage example:
if __name__ == "__main__":
    # Initialize the processor
    processor = IndexTTS2Processor()
    
    # Process a markdown script
    results = processor.process_script(
        script_path="input_script.md",
        voice_prompt="reference_voice.wav",
        output_dir="output",
        base_name="my_script"
    )
    
    print(f"Generated {len(results)} audio files:")
    for result in results:
        print(f"  - {result['output_file']} ({result['emotion_type']})")
```

### 4. Integration with IndiByte Workspace

- Scan the `/media/script/HLS.md` file for the main narrative structure
- Process scene descriptions from `/media/scenes/` directory
- Use reference voice from a designated audio file
- Output organized into `/media/voiceover/` directory
- Generate a manifest file mapping text segments to audio files

### 5. Dependencies to Install

```bash
# Install IndexTTS2
git clone https://github.com/index-tts/index-tts.git
cd index-tts
git lfs pull
pip install uv
uv sync --all-extras

# Install additional dependencies for this script
pip install mistune transformers
```

### 6. Execution Workflow

1. Prepare reference voice audio file
2. Identify script files to process (HLS.md and scene files)
3. Run the voiceover automation script
4. Monitor output in the designated directory
5. Verify audio quality and emotion appropriateness
6. Combine audio segments if needed for final voiceover

This plan provides a complete framework for automating voiceover generation with appropriate emotional expression for the IndiByte animation project.
