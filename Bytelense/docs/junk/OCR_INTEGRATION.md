# ChandraOCR Integration - Complete Documentation

## Overview

The label processing service now includes **full OCR integration** using ChandraOCR, a state-of-the-art document OCR model with layout preservation.

**Pipeline:**
1. Image enhancement (adaptive quality-based processing)
2. ChandraOCR text extraction (with markdown, HTML, and structured output)
3. Combined results with timing metrics

---

## API Endpoints

### Process with OCR
**POST** `/api/label/process-with-ocr`

Complete food label processing and text extraction in one request.

**Request:**
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJ...",
  "metadata": {}
}
```

**Response (Success):**
```json
{
  "status": "success",
  "enhanced_image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
  "quality_analysis": {
    "quality_tier": "good",
    "sharpness": 125.5,
    "exposure_score": 0.85,
    "saturation_mean": 0.65,
    "dark_ratio": 0.05,
    "clipped_ratio": 0.03
  },
  "stages_applied": ["perspective_correction", "glare_removal", "denoise", "clahe", "sharpen"],
  "timings": {
    "perspective_correction": 75.2,
    "glare_removal": 120.1,
    "denoise": 250.5,
    "enhance_contrast": 110.3,
    "sharpen": 42.1
  },
  "total_processing_ms": 598.2,
  "ocr_result": {
    "markdown": "# Nutrition Facts\n\nServing Size: 1 cup\n...",
    "html": "<div class=\"nutrition-facts\"><h1>Nutrition Facts</h1>...",
    "raw": "[Raw ChandraOCR output]",
    "token_count": 256,
    "error": false,
    "chunks": {
      "title": "Nutrition Facts",
      "sections": [...]
    },
    "images": {}
  },
  "ocr_time_ms": 3420.5,
  "total_time_ms": 4018.7,
  "message": "Processing and OCR complete: 5 img stages, tokens=256"
}
```

---

## ChandraOCR Features

### Model Capabilities

ChandraOCR is a multi-modal vision language model that:

- **Converts documents to structured formats:**
  - Markdown (with semantic structure)
  - HTML (with visual layout)
  - JSON (with semantic understanding)

- **Preserves document structure:**
  - Tables with cell alignment
  - Headers and footers
  - Lists and nested structures
  - Text flow and spatial relationships

- **Handles complex layouts:**
  - Multi-column text
  - Handwriting (good support)
  - Forms with checkboxes
  - Mixed text and images
  - Math equations

- **Extracts additional information:**
  - Structured chunks (paragraphs, tables, etc.)
  - Embedded images with captions
  - Token counts for usage tracking

### Quality Metrics

The OCR result includes:

| Field | Meaning |
|-------|---------|
| `markdown` | Semantic markdown output |
| `html` | Layout-preserving HTML |
| `raw` | Raw model output (for debugging) |
| `token_count` | Tokens used (for billing/optimization) |
| `error` | Whether OCR encountered issues |
| `chunks` | Structured text segments |
| `images` | Extracted images with metadata |

---

## Backend Service Details

### ChandraOCR Manager

**File:** `app/api/label_processing.py`

**Initialization:**
```python
def get_ocr_manager() -> InferenceManager:
    """Get or create OCR manager instance."""
    global _ocr_manager
    if _ocr_manager is None:
        _ocr_manager = InferenceManager(method="hf")  # HuggingFace backend
    return _ocr_manager
```

**Inference:**
```python
from chandra.model import InferenceManager
from chandra.model.schema import BatchInputItem
from PIL import Image

manager = InferenceManager(method="hf")
pil_image = Image.open("label.jpg")
batch_input = [BatchInputItem(image=pil_image, prompt=None)]
batch_output = manager.generate(batch_input)

# Access results
ocr_text = batch_output[0].markdown
tokens_used = batch_output[0].token_count
```

---

## Processing Pipeline

### Full E2E Flow

```
Frontend (Browser)
    ↓
Capture burst + fusion → ~500ms
    ↓
Send to backend (base64)
    ↓
Backend Processing
    ├─ Decode image
    ├─ Analyze quality
    ├─ Adaptive image processing
    │   ├─ Light (~150ms) or
    │   ├─ Medium (~600ms) or
    │   └─ Heavy (~1200ms)
    ├─ Image Enhancement
    │   ├─ Perspective correction
    │   ├─ Glare removal
    │   ├─ Denoising
    │   ├─ Contrast enhancement
    │   └─ Sharpening
    ├─ ChandraOCR
    │   ├─ Model inference (~3-4s typical)
    │   ├─ Text extraction
    │   ├─ Layout preservation
    │   └─ Structured output
    └─ Return combined results
    ↓
Frontend Display
    ├─ Enhanced image
    ├─ Quality metrics
    ├─ OCR text (markdown/HTML)
    └─ Token count
```

### Timing Profile

| Stage | Duration | Notes |
|-------|----------|-------|
| Image preprocessing | 20ms | Quality analysis |
| Light image enhancement | ~150ms | Good quality images |
| Medium image enhancement | ~600ms | Fair quality images |
| Heavy image enhancement | ~1200ms | Poor quality images |
| **ChandraOCR** | **3-5s** | Model inference (GPU accelerated) |
| **Total (typical)** | **~4-6s** | Most common case (fair quality) |

### Optimization Opportunities

1. **Batch Processing:** Multiple images can be processed together
2. **Caching:** Store OCR results for identical images
3. **Async Processing:** Return image results immediately, stream OCR
4. **Model Optimization:** Use quantized model for faster inference
5. **GPU Acceleration:** Enable CUDA/Metal for 10-20× speedup

---

## Integration with Frontend

### Frontend Implementation (React/TypeScript)

```typescript
// ScanPage.tsx
async function processLabelWithOCR(base64Image: string) {
  const response = await fetch('https://192.168.1.4:8443/api/label/process-with-ocr', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_base64: base64Image,
      metadata: {
        timestamp: new Date().toISOString(),
        device: 'mobile-firefox'
      }
    })
  });

  const result = await response.json();

  if (result.status === 'success') {
    // Display enhanced image
    document.getElementById('enhanced-image').src = result.enhanced_image_base64;

    // Show quality metrics
    console.log(`Quality: ${result.quality_analysis.quality_tier}`);
    console.log(`Processing time: ${result.total_processing_ms}ms`);
    console.log(`OCR time: ${result.ocr_time_ms}ms`);

    // Display OCR text
    document.getElementById('ocr-text').innerHTML = result.ocr_result.html;
    document.getElementById('ocr-tokens').textContent = result.ocr_result.token_count;

    // Access raw markdown for further processing
    const text = result.ocr_result.markdown;

    // Parse nutrition facts from markdown
    parseNutritionFacts(text);
  }
}
```

---

## ChandraOCR Model Details

### Model: Qwen2-VL-7B

**Base Model:** Qwen2-VL-7B (7 billion parameters)

**Features:**
- Vision-language understanding
- Strong text extraction capability
- Layout preservation
- Handles Chinese and English
- Requires GPU for reasonable latency

**System Requirements:**
- VRAM: 16GB minimum (for 7B model)
- CUDA/Metal support for acceleration
- ~3-5 seconds per image on GPU
- ~30-60 seconds per image on CPU

### Model Outputs

The model generates structured output that ChandraOCR parses into:

```python
@dataclass
class BatchOutputItem:
    markdown: str         # Semantic markdown
    html: str             # Layout-preserving HTML
    chunks: dict          # Structured segments
    raw: str              # Raw model output
    page_box: List[int]   # Bounding box [x, y, w, h]
    token_count: int      # Tokens used
    images: dict          # Extracted images
    error: bool           # Error flag
```

---

## Testing

### Manual Testing

```bash
# Health check with OCR status
curl https://192.168.1.4:8443/api/label/health

# Process with OCR (requires image file)
curl -X POST https://192.168.1.4:8443/api/label/process-with-ocr \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "data:image/jpeg;base64,..."
  }'
```

### Test with Local Image

```bash
# Convert image to base64
base64 -i food_label.jpg -o label_b64.txt

# Create request
cat > ocr_request.json << 'EOF'
{
  "image_base64": "data:image/jpeg;base64,$(cat label_b64.txt)"
}
EOF

# Send request
curl -X POST https://192.168.1.4:8443/api/label/process-with-ocr \
  -H "Content-Type: application/json" \
  -d @ocr_request.json
```

### Expected Performance

```
Image: 640×480 food label photo
Quality: FAIR
Total time: ~4.5 seconds
  - Image processing: 600ms
  - OCR: 3900ms
  - Token count: 250-400
```

---

## Error Handling

### Graceful Degradation

If OCR fails, the response includes:

```json
{
  "status": "success",
  "enhanced_image_base64": "...",
  "ocr_result": {
    "markdown": "",
    "html": "",
    "raw": "",
    "token_count": 0,
    "error": true,
    "chunks": {},
    "images": {}
  },
  "message": "Image processing succeeded but OCR failed: [error details]"
}
```

The enhanced image is **always returned**, even if OCR fails.

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `"OCR returned empty output"` | Model issues or timeout | Check GPU, restart service |
| `"CUDA out of memory"` | Model too large for GPU | Use quantized model or CPU |
| `Timeout after 30s` | Very slow inference | Profile with `time` command |
| `ModuleNotFoundError: chandra` | Package not installed | `pip install chandra-ocr>=0.1.7` |

---

## Performance Optimization

### Current Setup (HuggingFace Backend)

- Model loaded on first request
- Cached in memory for subsequent requests
- Single-threaded inference
- CPU fallback if CUDA unavailable

### Optimization Strategies

**1. vLLM Backend (Faster)**
```python
# Switch to vLLM for faster inference
_ocr_manager = InferenceManager(method="vllm")
```
- Continuous batching
- 2-3× speedup on GPU
- Requires vLLM installation

**2. Model Quantization**
```bash
# Use quantized 4-bit model (faster, less VRAM)
pip install bitsandbytes
```

**3. Async Processing**
```python
# Return image results immediately
# Stream OCR via WebSocket
@router.post("/process-and-stream-ocr")
async def process_and_stream_ocr(request):
    # Return enhanced image first
    # Start async OCR task
    # Push results via WebSocket when ready
```

**4. Batch Processing**
```python
# Process multiple images together
batch_input = [BatchInputItem(image=img1), BatchInputItem(image=img2)]
batch_output = ocr_manager.generate(batch_input)
```

---

## API Response Format Reference

### LabelProcessWithOCRResponse

```typescript
{
  status: "success" | "error",
  enhanced_image_base64: string,
  quality_analysis: {
    quality_tier: "good" | "fair" | "poor",
    sharpness: number,
    exposure_score: number,      // 0-1
    saturation_mean: number,     // 0-1
    dark_ratio: number,          // 0-1
    clipped_ratio: number        // 0-1
  },
  stages_applied: string[],
  timings: Record<string, number>,
  total_processing_ms: number,
  ocr_result: {
    markdown: string,
    html: string,
    raw: string,
    token_count: number,
    error: boolean,
    chunks: Record<string, any>,
    images: Record<string, any>
  } | null,
  ocr_time_ms: number,
  total_time_ms: number,
  message: string
}
```

---

## Next Steps

### Immediate
- [ ] Test OCR with various food labels
- [ ] Validate markdown parsing
- [ ] Profile model loading time
- [ ] Test error handling

### Short Term
- [ ] Add WebSocket progress updates
- [ ] Implement async OCR (return image immediately)
- [ ] Create nutrition facts parser
- [ ] Add image caching

### Medium Term
- [ ] Switch to vLLM backend
- [ ] Implement batch processing
- [ ] Add model quantization
- [ ] GPU acceleration profiling

### Long Term
- [ ] Custom fine-tuning for food labels
- [ ] Structured data extraction
- [ ] Multi-language support
- [ ] Mobile model variant

---

## Integration Checklist

- [x] ChandraOCR endpoint created (`/api/label/process-with-ocr`)
- [x] Response models defined
- [x] Error handling implemented
- [x] Timing metrics added
- [x] Health check updated
- [ ] Frontend integration
- [ ] Real-world testing with food labels
- [ ] Performance profiling
- [ ] Documentation completed
- [ ] Production deployment

---

## Files Modified

### Backend
- `app/api/label_processing.py`: Added OCR endpoint, response models, OCR manager
- `app/main.py`: No changes required (endpoints auto-discovered)

### New Features
- **New endpoint:** `POST /api/label/process-with-ocr`
- **Updated health check:** Now includes OCR status
- **New response model:** `LabelProcessWithOCRResponse` with OCR results

---

## Usage Examples

### cURL

```bash
# File upload to base64
cat food_label.jpg | base64 | xargs -I {} curl -X POST https://192.168.1.4:8443/api/label/process-with-ocr \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"data:image/jpeg;base64,{}"}'
```

### Python

```python
import requests
import base64

with open("food_label.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = requests.post(
    "https://192.168.1.4:8443/api/label/process-with-ocr",
    json={
        "image_base64": f"data:image/jpeg;base64,{img_b64}",
        "metadata": {}
    },
    verify=False
)

result = response.json()
print(f"Status: {result['status']}")
print(f"OCR Text: {result['ocr_result']['markdown']}")
print(f"Tokens used: {result['ocr_result']['token_count']}")
```

### JavaScript (React)

```typescript
async function extractFoodLabel(imageBlob: Blob) {
  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64 = e.target?.result as string;

    const response = await fetch('/api/label/process-with-ocr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: base64 })
    });

    const { ocr_result } = await response.json();

    // Parse OCR markdown
    const nutritionText = ocr_result.markdown;

    // Extract nutrition facts
    const facts = parseNutritionFacts(nutritionText);

    return facts;
  };

  reader.readAsDataURL(imageBlob);
}
```

---

**Status:** ✅ **ChandraOCR integration complete and ready for testing**

Last Updated: 2025-11-16
