# Backend Label Processing - Quick Start

## Services Deployed ✅

### 1. Label Processing Service
**Location:** `app/services/label_processing.py`

**Main Class:** `LabelProcessor`

```python
from app.services.label_processing import LabelProcessor

processor = LabelProcessor(enable_sr=False)
result = processor.process_adaptive(image_cv2)

# Access results
quality = result.quality_analysis.quality_tier  # "good", "fair", "poor"
enhanced = result.enhanced_image
stages = result.stages_applied  # List of processing stages
timings = result.timings  # Dict of stage latencies
```

### 2. SearXNG Keep-Alive Service
**Location:** `app/services/searxng_keepalive.py`

**Main Class:** `SearXNGKeepAlive`

```python
from app.services.searxng_keepalive import init_keepalive, shutdown_keepalive

# Auto-initialized in app/main.py lifespan
init_keepalive(searxng_url)  # Start pinging SearXNG every 10min

# Cleanup on shutdown
await shutdown_keepalive()
```

---

## API Endpoints

### Base URL
```
https://192.168.1.4:8443/api/label
```

### 1. Process Image
**POST** `/api/label/process`

```bash
curl -X POST https://192.168.1.4:8443/api/label/process \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJ...",
    "metadata": {}
  }'
```

**Response:**
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
  "stages_applied": ["enhance_contrast", "sharpen"],
  "timings": {
    "enhance_contrast": 105.2,
    "sharpen": 42.1
  },
  "total_processing_ms": 205.3,
  "message": "Processing successful with 2 stages"
}
```

### 2. Analyze Quality Only
**POST** `/api/label/analyze-quality`

```bash
curl -X POST https://192.168.1.4:8443/api/label/analyze-quality \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "data:image/jpeg;base64,..."}'
```

**Response:** Returns `QualityAnalysisResponse` (see above)

### 3. Test with File Upload
**POST** `/api/label/test-image`

```bash
curl -X POST https://192.168.1.4:8443/api/label/test-image \
  -F "file=@food_label.jpg"
```

### 4. Health Check
**GET** `/api/label/health`

```bash
curl https://192.168.1.4:8443/api/label/health
```

---

## Processing Pipelines

### Automatic Quality Detection → Pipeline Selection

```
Image Quality Analysis
    ↓
┌─────────────────────────────────────────┐
│ sharpness > 100                         │
│ AND exposure_score > 0.7                │  ✅ GOOD
│ AND saturation_mean > 0.3               │     (~150ms)
└─────────────────────────────────────────┘
    ↓ No
┌─────────────────────────────────────────┐
│ sharpness > 60                          │
│ AND exposure_score > 0.5                │  ⚠️ FAIR
└─────────────────────────────────────────┘     (~600ms)
    ↓ No
                                          ❌ POOR
                                             (~1200ms)
```

### Light Pipeline (Good Quality)
```
Image
  ↓
Enhance Contrast (CLAHE color-aware)
  ↓
Sharpen (Unsharp mask, strength=1.2)
  ↓
Output (~150ms total)
```

### Medium Pipeline (Fair Quality)
```
Image
  ↓
Perspective Correction (homography)
  ↓
Glare Removal (LAB inpainting)
  ↓
Denoise (Medium strength NLM)
  ↓
Enhance Contrast (CLAHE color-aware)
  ↓
Sharpen (Unsharp mask, strength=1.3)
  ↓
Output (~600ms total)
```

### Heavy Pipeline (Poor Quality)
```
Image
  ↓
Perspective Correction
  ↓
Glare Removal
  ↓
Denoise (Strong - double NLM)
  ↓
Enhance Contrast (CLAHE color-aware)
  ↓
Sharpen (Unsharp mask, strength=1.4)
  ↓
Upsampling (2x bicubic)
  ↓
Output (~1200ms total)
```

---

## Quality Metrics Explained

### Sharpness (Laplacian Variance)
```
< 50   = Too blurry, reject
50-100 = Borderline, capture but mark
> 100  = Sharp, good to process
```

### Exposure Score (0.0 - 1.0)
```
Formula: 1.0 - (dark_pixels + clipped_pixels)

< 0.5  = Bad exposure (too dark or glare)
0.5-0.7 = Fair exposure
> 0.7  = Good exposure
```

### Saturation Mean (0.0 - 1.0)
```
< 0.25 = Washed out, low color distinction
0.25-0.5 = Moderate color
> 0.5  = Good color saturation
```

### Dark Ratio
```
Percentage of pixels with L < 50 (in LAB)
> 0.3 = Image too dark
```

### Clipped Ratio
```
Percentage of pixels with L > 240 (in LAB)
> 0.2 = Too much glare/overexposure
```

---

## Color-Aware CLAHE Tuning

The processor automatically detects label color and adjusts contrast enhancement:

| Color | Clip Limit | Reason |
|-------|-----------|--------|
| Yellow | 2.5 | Red text on yellow = low contrast |
| White | 2.0 | Already high contrast |
| Blue | 2.5 | Yellow text on blue = low contrast |
| Red | 2.3 | Varied contrast scenarios |
| Green | 2.2 | Balanced |
| Orange | 2.4 | Similar to yellow |
| Grayscale | 2.0 | Standard |

---

## Integration with Frontend

### Expected Flow

```
Frontend (Browser)
  ↓
1. Capture burst (5 frames)
2. Align & fuse frames
3. Light CLAHE + sharpen
4. Show preview to user
  ↓
5. User approves
  ↓
6. Send to backend via POST /api/label/process
  ↓
Backend
  ↓
7. Analyze quality tier
8. Apply adaptive pipeline
9. Return enhanced image + metadata
  ↓
10. Frontend displays result
11. Show OCR (future: Tesseract integration)
```

### Frontend Request Example (JavaScript)

```javascript
async function processLabel(canvasElement) {
  // Get base64 image from canvas
  const imageBase64 = canvasElement.toDataURL('image/jpeg', 0.9);

  // Send to backend
  const response = await fetch('https://192.168.1.4:8443/api/label/process', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_base64: imageBase64,
      metadata: {
        frame_count: 5,
        timestamp: new Date().toISOString()
      }
    })
  });

  const result = await response.json();

  if (result.status === 'success') {
    // Display enhanced image
    document.getElementById('enhanced-image').src = result.enhanced_image_base64;

    // Show quality info
    console.log(`Quality: ${result.quality_analysis.quality_tier}`);
    console.log(`Processing time: ${result.total_processing_ms}ms`);
    console.log(`Stages: ${result.stages_applied.join(' → ')}`);
  }
}
```

---

## Performance Targets

| Scenario | Latency | Notes |
|----------|---------|-------|
| Good quality image | ~150ms | Light pipeline |
| Fair quality image | ~600ms | Medium pipeline |
| Poor quality image | ~1200ms | Heavy pipeline + 2x upsampling |
| Network (WiFi) | ~200-350ms | Upload + download |
| **Total E2E (Fair)** | **~800-950ms** | Most common case |

---

## Troubleshooting

### Image Not Processing
```python
# Check quality
POST /api/label/analyze-quality

# Check if image decodes properly
# Ensure base64 includes data URI prefix: "data:image/jpeg;base64,..."
```

### Slow Processing
```python
# Check which stages ran
response['stages_applied']

# If "upsampling" in stages, image was poor quality
# Suggest user retake with better lighting
```

### Service Not Responding
```bash
# Check health
curl https://192.168.1.4:8443/api/label/health

# Check logs
docker logs bytelense-caddy
```

---

## Testing Checklist

- [ ] Test with good quality image (sharp, well-lit)
- [ ] Test with fair quality image (some blur/glare)
- [ ] Test with poor quality image (very blurry/dark)
- [ ] Test with different label colors (yellow, white, blue, red)
- [ ] Test with curved surfaces (bottles, cans)
- [ ] Test with heavy glare
- [ ] Verify latency < 1.5s on WiFi
- [ ] Check base64 encoding from frontend works correctly
- [ ] Validate enhanced image quality
- [ ] Test on both desktop and mobile Firefox

---

## What's Next

### Immediate
- [ ] Integration test with real food labels
- [ ] Verify color detection on various packaging
- [ ] Performance profiling on different devices

### Short Term
- [ ] Add Tesseract OCR integration
- [ ] Create `/api/label/process-with-ocr` endpoint
- [ ] Return OCR confidence scores

### Medium Term
- [ ] Train MediaPipe label detector for frontend
- [ ] Implement SwinIR super-resolution (optional, for poor images)
- [ ] Add multi-frame support (burst processing on backend)

### Long Term
- [ ] GPU acceleration (CUDA for OpenCV)
- [ ] WebSocket progress events for long processing
- [ ] Caching layer for repeated images

---

**Status:** ✅ Ready for production testing
