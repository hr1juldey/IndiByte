# ChandraOCR Quick Start Guide

## Testing the OCR Endpoint

### 1. Health Check

First, verify the OCR service is ready:

```bash
curl https://192.168.1.4:8443/api/label/health
```

Expected response:
```json
{
  "status": "healthy",
  "processor_ready": true,
  "ocr_status": "ready"
}
```

---

## 2. Processing a Local Image

### Option A: Using cURL with Image File

```bash
# Save a food label image as "label.jpg"

# Convert to base64 (all one line)
curl -X POST https://192.168.1.4:8443/api/label/process-with-ocr \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "image_base64": "data:image/jpeg;base64,$(cat label.jpg | base64 -w 0)",
  "metadata": {}
}
EOF
```

### Option B: Using Python

```python
import requests
import base64
import json

# Read image file
with open("label.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Send request
response = requests.post(
    "https://192.168.1.4:8443/api/label/process-with-ocr",
    json={
        "image_base64": f"data:image/jpeg;base64,{img_b64}",
        "metadata": {}
    },
    verify=False  # Ignore self-signed certificate
)

result = response.json()

# Check status
print(f"Status: {result['status']}")
print(f"Quality: {result['quality_analysis']['quality_tier']}")
print(f"Sharpness: {result['quality_analysis']['sharpness']:.1f}")

# Check if OCR succeeded
if result['ocr_result']['error']:
    print("⚠️ OCR had issues")
else:
    print(f"✅ OCR successful: {result['ocr_result']['token_count']} tokens")

# Display OCR text
print("\n--- OCR Output (Markdown) ---")
print(result['ocr_result']['markdown'][:500])  # First 500 chars

# Timing
print(f"\n--- Timings ---")
print(f"Image processing: {result['total_processing_ms']:.0f}ms")
print(f"OCR: {result['ocr_time_ms']:.0f}ms")
print(f"Total: {result['total_time_ms']:.0f}ms")
```

### Option C: Using JavaScript/React

```typescript
async function testOCREndpoint(imageFile: File) {
  const reader = new FileReader();

  reader.onload = async (e) => {
    const base64 = e.target?.result as string;

    const response = await fetch('https://192.168.1.4:8443/api/label/process-with-ocr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: base64,
        metadata: { timestamp: new Date().toISOString() }
      })
    });

    const result = await response.json();

    console.log('Status:', result.status);
    console.log('Quality:', result.quality_analysis.quality_tier);
    console.log('OCR tokens:', result.ocr_result.token_count);
    console.log('OCR text:', result.ocr_result.markdown.substring(0, 200));

    // Display to user
    if (result.ocr_result.error) {
      showWarning('OCR completed with errors');
    } else {
      displayOCRResult(result.ocr_result.html);
    }
  };

  reader.readAsDataURL(imageFile);
}

// Usage
const fileInput = document.getElementById('image-input') as HTMLInputElement;
fileInput.addEventListener('change', (e) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) testOCREndpoint(file);
});
```

---

## 3. API Response Format

### Success Response

```json
{
  "status": "success",
  "enhanced_image_base64": "data:image/jpeg;base64,...",
  "quality_analysis": {
    "quality_tier": "fair",
    "sharpness": 95.2,
    "exposure_score": 0.82,
    "saturation_mean": 0.65,
    "dark_ratio": 0.08,
    "clipped_ratio": 0.05
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
    "markdown": "# Nutrition Facts\n\nServing Size: 1 cup (240g)\n\n**Per Serving:**\n- Calories: 120\n- Total Fat: 2g\n- Carbohydrates: 23g\n- Protein: 3g\n",
    "html": "<div class=\"nutrition-facts\"><h1>Nutrition Facts</h1>...",
    "raw": "[Raw model output]",
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

### Error Response

```json
{
  "status": "error",
  "enhanced_image_base64": "",
  "quality_analysis": {
    "quality_tier": "poor",
    "sharpness": 0.0,
    "exposure_score": 0.0,
    "saturation_mean": 0.0,
    "dark_ratio": 1.0,
    "clipped_ratio": 0.0
  },
  "stages_applied": [],
  "timings": {},
  "total_processing_ms": 0.0,
  "ocr_result": null,
  "ocr_time_ms": 0.0,
  "total_time_ms": 125.3,
  "message": "Processing failed: [error details]"
}
```

---

## 4. Interpreting Results

### Quality Tier

| Tier | Meaning | When to Use |
|------|---------|-----------|
| `good` | Sharp, well-lit, high contrast | Accept immediately, fast processing (~150ms) |
| `fair` | Some blur/glare but acceptable | Process with medium pipeline (~600ms) |
| `poor` | Very blurry, dark, or low contrast | Ask user to retake (heavy pipeline ~1200ms) |

### Sharpness Metric

```
< 50    = Too blurry, ask user to retake
50-100  = Borderline, may work but quality uncertain
> 100   = Sharp, good for OCR
> 120   = Excellent quality
```

### Exposure Score (0-1)

```
< 0.5  = Bad exposure (too dark or overexposed)
0.5-0.7 = Fair exposure
> 0.7  = Good exposure
```

### OCR Output

The OCR result provides three formats:

1. **Markdown** (`markdown`) - Best for semantic parsing
   - Use for nutrition fact extraction
   - Preserves headers, lists, emphasis
   - Easiest to parse with regular expressions

2. **HTML** (`html`) - Best for display
   - Preserves visual layout
   - Can be rendered directly in UI
   - Better for preserving table structure

3. **Raw** (`raw`) - For debugging
   - Complete model output
   - Useful if markdown/HTML parsing fails

---

## 5. Integration with Frontend

### Add to ScanPage.tsx

```typescript
import { BurstCaptureProcessor } from '../lib/burstCapture';

export function ScanPage() {
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [processing, setProcessing] = useState(false);

  const handleCapture = async () => {
    // Capture and fuse frames (existing code)
    const { canvas: fused } = await burstRef.current.processBurst();
    const base64 = fused.toDataURL('image/jpeg', 0.9);

    // NEW: Send to OCR endpoint
    setProcessing(true);
    try {
      const response = await fetch('https://192.168.1.4:8443/api/label/process-with-ocr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: base64 })
      });

      const result = await response.json();

      if (result.status === 'success') {
        // Show enhanced image
        setEnhancedImage(result.enhanced_image_base64);

        // Show OCR results
        setOcrResult(result.ocr_result);

        // Parse nutrition facts (next step)
        parseNutritionFacts(result.ocr_result.markdown);
      }
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div>
      {/* Camera preview */}
      <video ref={videoRef}></video>

      {/* Capture button */}
      <button onClick={handleCapture} disabled={processing}>
        {processing ? 'Processing...' : 'Capture & Analyze'}
      </button>

      {/* Results */}
      {ocrResult && (
        <div>
          <h2>Nutrition Facts</h2>
          <div className="ocr-text">
            {/* Render markdown */}
            <ReactMarkdown>{ocrResult.markdown}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 6. Common Issues & Fixes

### "OCR returned empty output"

**Cause:** Model loading or inference failure

**Fix:**
```bash
# Check health status
curl https://192.168.1.4:8443/api/label/health

# Check backend logs
docker logs bytelense-backend
```

### Timeout (>10 seconds)

**Cause:** Model inference is slow (CPU or loading)

**Expected:** First request loads model (~30-60s), subsequent requests ~4-5s

**Fix:**
- Ensure GPU available: `nvidia-smi`
- Warm up model: Send a test request first

### "Invalid image data"

**Cause:** Base64 encoding error

**Fix:**
```bash
# Make sure base64 includes data URI prefix
"data:image/jpeg;base64,..." ✅
"/9j/4AAQ..." ❌
```

### High error rates in OCR

**Cause:** Poor image quality, unusual label format

**Check:**
```python
if result['quality_analysis']['quality_tier'] == 'poor':
    print("⚠️ Image quality is poor, OCR accuracy may suffer")

if result['ocr_result']['error']:
    print("⚠️ OCR encountered issues")
```

---

## 7. Performance Expectations

### Typical Food Label (Fair Quality)

```
Image enhancement:  ~600ms    (medium pipeline)
OCR model:          ~3500ms   (model inference)
─────────────────────────────
Total:              ~4100ms
```

### Good Quality Image

```
Image enhancement:  ~150ms    (light pipeline)
OCR model:          ~3500ms   (model inference)
─────────────────────────────
Total:              ~3650ms
```

### Poor Quality Image

```
Image enhancement:  ~1200ms   (heavy pipeline)
OCR model:          ~3500ms   (model inference)
─────────────────────────────
Total:              ~4700ms
```

### First Request (Model Loading)

```
Model loading:      ~30-60s   (only first request)
Processing:         ~4000ms
─────────────────────────────
Total:              ~35-65s
```

---

## 8. Next Steps

After testing OCR endpoint:

1. **Integrate with Frontend**
   - Update ScanPage.tsx to use `/process-with-ocr`
   - Show OCR results in UI
   - Add loading indicators for long OCR processing

2. **Build Nutrition Facts Parser**
   - Extract structured data from OCR markdown
   - Parse nutrition facts table
   - Extract ingredients list
   - Return structured JSON

3. **Real-World Testing**
   - Test with 20-50 real food labels
   - Validate OCR accuracy (target > 85%)
   - Measure latency on actual devices
   - Handle edge cases (damaged labels, reflections, etc.)

4. **Optimization**
   - Cache OCR results for duplicate images
   - Implement async OCR (return image immediately, stream results)
   - Add progress events via WebSocket
   - Consider model quantization if needed

---

**Status:** ✅ OCR endpoint ready for testing

For detailed documentation, see `OCR_INTEGRATION.md`
