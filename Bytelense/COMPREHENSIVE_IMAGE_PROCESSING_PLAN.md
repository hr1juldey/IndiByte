# Comprehensive Image Processing Strategy for Bytelense
## Frontend + Backend Architecture for Robust Label Scanning

---

## Executive Summary

The challenge: Users will capture **unpredictable, poor-quality images** (glare, blur, perspective, color variation, low contrast). No single preprocessing approach works for all.

**Solution: Two-Stage Adaptive Pipeline**
- **Frontend (Client):** Real-time burst capture + intelligent fusion → fast preview
- **Backend (Server):** Heavy processing + ML-driven enhancement → publication-quality result

This design balances:
- ✅ **Responsiveness** — User sees preview in <1s
- ✅ **Resilience** — Works with dirty/unexpected images
- ✅ **Latency Hiding** — Backend processes while user reviews
- ✅ **Adaptability** — Processing adjusts based on image content

---

## Part 1: Frontend Architecture (Browser-Side)

### 1.1 Real-Time Detection Layer

#### Option A: MediaPipe Object Detector (Recommended)
```
Pros:
- Real-time on-device (no server calls during capture)
- TFLite quantized → ~30-50ms per frame
- Learns what "label" looks like from training data
- Robust to color, orientation, partial visibility

Cons:
- Requires model training on your label images (1-2h with MediaPipe Model Maker)
- Initial setup effort, but pays off long-term

Implementation:
- Use EfficientDet-Lite0 or EfficientDet-Lite2 (faster vs. more accurate trade-off)
- Input: Full video frame (native resolution)
- Output: Bounding box (x, y, w, h) + confidence
- Latency: ~30-50ms per frame (on mobile CPU)
```

#### Option B: Color Mask Fallback (HSV + Morphology)
```
Pros:
- No model needed
- <10ms per frame
- Immediate deployment

Cons:
- Breaks if colors are non-standard (blue/red packaging, dark backgrounds)
- Less robust to glare, shadows

Implementation:
- HSV range tuning (H, S, V bounds)
- Morphological cleanup (dilate/erode)
- Fallback for when MediaPipe fails or on slower devices
```

#### Recommendation: **Hybrid**
1. Try MediaPipe first (fast on modern phones)
2. Fallback to HSV mask on older devices or if model fails
3. If neither detects label → show UI hint "Adjust angle/lighting"

---

### 1.2 Real-Time Frame Quality Assessment

**Goal:** Only capture frames worth processing (not blurry, not underexposed).

#### Sharpness Check
```
Algorithm: Laplacian Variance

let gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
let laplacian = cv.Laplacian(gray, cv.CV_64F)
let variance = stddev(laplacian)^2

Thresholds (tune per camera):
- variance < 50:     Too blurry (reject)
- 50 < variance < 100: Borderline (capture but mark)
- variance > 100:     Sharp (definitely capture)
```

Latency: **~5ms per frame** (very fast in OpenCV.js)

#### Exposure Check
```
Algorithm: Histogram analysis on L channel (LAB)

let lab = cv.cvtColor(frame, cv.COLOR_BGR2Lab)
let L = extractChannel(lab, 0)  // Luminance
let histogram = cv.calcHist([L], [0], 256, [0, 256])

Metrics:
- Dark pixels (L < 30):  > 20% → Too dark, warn user
- Clipped pixels (L > 240): > 10% → Glare/overexposed
- Well-exposed (90-160): > 50% → Good exposure
```

Latency: **~8ms per frame**

#### Saturation Check (For Colored Text)
```
Algorithm: Color saturation per pixel

for each pixel:
  max_channel = max(R, G, B)
  min_channel = min(R, G, B)
  saturation = (max - min) / max

mean_saturation = average across all pixels

Threshold:
- saturation < 0.15: Washed out (weak colors)
- saturation > 0.4:  Good color distinction
```

Latency: **~10ms per frame**

---

### 1.3 Burst Capture Strategy

#### When to Capture
```
Trigger burst capture when ALL pass:
1. Label detected (confidence > 0.7)
2. Sharpness OK (variance > 80)
3. Exposure OK (not too dark, not too clipped)
4. Saturation OK (mean saturation > 0.25)

Then: Capture N=5-7 frames over 150-200ms window
(Timing: at 30 fps, 150ms = ~4-5 frames naturally)
```

#### Why Burst?
- Compensates for hand tremor + focus hunting
- Allows weighted fusion (pick best per-pixel)
- Multi-frame denoising (reduces sensor noise)
- HDR-like effect (combine well-exposed regions)

---

### 1.4 Burst Frame Alignment

**Problem:** 5 frames are slightly offset (user's hand moved ~10-50px).

#### Strategy: Cheap Translational Alignment
```
Algorithm: Template Matching (Normalized Cross-Correlation)

1. Downscale all frames to 300px (faster matching)
2. Pick sharpest frame as reference
3. For each other frame:
   - Compute NCC with reference
   - Find peak offset (dx, dy)
   - Apply integer shift on full-resolution frame

Pseudo-code:
let refSmall = downscale(ref, 300)
let refGray = cvtColor(refSmall, CV_BGR2GRAY)

for each frame in burst:
  let fSmall = downscale(frame, 300)
  let fGray = cvtColor(fSmall, CV_BGR2GRAY)

  result = cv.matchTemplate(refGray, fGray, CV_TM_CCORR_NORMED)
  {dx, dy} = findPeak(result)

  // Scale back to full resolution
  dxFull = dx * (orig_width / 300)
  dyFull = dy * (orig_height / 300)

  // Apply shift on full-res
  aligned = cv.warpAffine(frame, translationMatrix(dxFull, dyFull), size)
```

**Latency: ~100-150ms** for 5-frame burst (all on client in Web Worker)

#### Why Not Homography?
- Homography (perspective) alignment takes 500+ms in browser
- Most hand tremor is translational (small shifts), not rotation
- If large rotation detected → use sharpest frame only

---

### 1.5 Intelligent Frame Fusion

**Goal:** Combine N aligned frames into 1 best image using per-pixel weighting.

#### Three Weight Maps

**1. Contrast Weight** (Favors textured/text regions)
```
Algorithm: Laplacian-based

for each frame:
  gray = cvtColor(frame, CV_BGR2GRAY)
  laplacian = cv.Laplacian(gray, CV_32F)
  contrast_map = abs(laplacian)

  // Normalize to [0, 1]
  contrast_map /= max(contrast_map)
```

**2. Saturation Weight** (Preserves colors)
```
Algorithm: Per-pixel color spread

for each pixel (R, G, B):
  saturation = (max(R,G,B) - min(R,G,B)) / max(R,G,B)

saturation_map = normalized saturation across all pixels
// Favors pixels with distinct colors (good for red-on-yellow text)
```

**3. Well-Exposedness Weight** (Avoids dark/bright extremes)
```
Algorithm: Gaussian weight centered at mid-range

for each frame:
  lab = cvtColor(frame, CV_BGR2Lab)
  L = extractChannel(lab, 0)  // Luminance
  L_norm = L / 255.0           // [0, 1]

  // Gaussian centered at 0.5 (mid-gray), sigma=0.2
  exp_weight = exp(-((L_norm - 0.5)^2) / (2 * 0.2^2))

// Result: bright pixels get lower weight, mid-range gets higher
```

#### Fusion
```
for each pixel position (x, y):
  final_pixel = weighted_average of all frames

  w_contrast = contrast_map[x,y] across frames
  w_saturation = saturation_map[x,y] across frames
  w_exposure = exp_weight[x,y] across frames

  combined_weight = w_contrast * w_saturation * w_exposure
  combined_weight /= sum(combined_weight)  // normalize

  final_pixel = sum(frame[x,y] * combined_weight[frame])
```

**Latency: ~200-300ms** for 600-pixel crop on modern device

**Result:**
- Sharper (contrast fusion)
- Better colors (saturation-aware)
- Less glare/dark (exposure fusion)
- Lower noise (multi-frame averaging)

---

### 1.6 Light Preprocessing (Frontend)

After fusion, apply cheap enhancements:

#### CLAHE (Contrast Limited Adaptive Histogram Equalization)
```
let lab = cvtColor(fused, CV_BGR2Lab)
let L = extractChannel(lab, 0)

let clahe = cv.createCLAHE(2.0, {width: 8, height: 8})
let L_enhanced = clahe.apply(L)

let result = cvtColor(merge([L_enhanced, a, b]), CV_Lab2BGR)

Latency: ~50ms for 600px crop
Result: Local contrast boost without destroying colors
```

#### Unsharp Mask (Light)
```
let blurred = cv.GaussianBlur(result, {width: 5, height: 5}, 1.0)
let sharpened = cv.addWeighted(result, 1.2, blurred, -0.2, 0)

Latency: ~30ms
Result: Crispness for small text without halos
```

#### Upsampling (Optional)
```
if crop is small (< 500px height):
  upsampled = cv.resize(result, size, 2.0)  // 2x cubic
else:
  upsampled = result

Latency: ~40ms for 2x upsampling
Result: More pixels for OCR to work with
```

**Total Frontend Heavy Ops: ~400-500ms** (runs in Web Worker, UI stays responsive)

---

### 1.7 Frontend UX Flow

```
User starts app
    ↓
[Live Camera Feed]
  - MediaPipe detects label bbox
  - Show rectangle overlay
  - Live sharpness/exposure bars below
    ↓
[Sharpness & Exposure OK?]
  - Auto-trigger burst capture (silent)
  - Fill 5-7 frame buffer (~150ms)
    ↓
[Show Preview Button]
  - User sees fused + CLAHE preview
  - Quality scores: Sharpness ★★★, Exposure ★★☆, Saturation ★★★
    ↓
[Approve/Retake]
  - Approve → Send to backend
  - Retake → Back to live camera
    ↓
[Uploading Preview... (spinner)]
  - Meanwhile, backend starts heavy processing
    ↓
[Backend Processing (100-500ms)]
  - User sees "Analyzing..." with progress
    ↓
[Results Page]
  - Show backend-enhanced image
  - Display OCR result
  - Confidence badge + "Looks good? / Edit / Retake"
```

---

## Part 2: Backend Architecture (Server-Side)

### 2.1 Entry Point: Stage-1 Image Arrival

Frontend sends:
```json
POST /api/label/process
{
  "stage1_image": "base64_jpeg",
  "metadata": {
    "sharpness": 125,
    "exposure_score": 0.8,
    "saturation_score": 0.6,
    "frame_count": 5,
    "timestamp": "2025-11-16T..."
  },
  "optionally_raw_frames": null  // if user has good bandwidth
}
```

### 2.2 Adaptive Processing Pipeline

**Strategy:** Analyze image quality → pick appropriate processing level.

#### Quality Analysis
```python
def analyze_image_quality(img):
    """Assess incoming image"""

    # Compute sharpness (Laplacian variance)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    laplacian = cv.Laplacian(gray, cv.CV_64F)
    sharpness = np.var(laplacian)

    # Exposure analysis
    lab = cv.cvtColor(img, cv.COLOR_BGR2Lab)
    L = lab[:,:,0]
    dark_ratio = np.sum(L < 50) / L.size
    clipped_ratio = np.sum(L > 240) / L.size
    exposure_score = 1 - (dark_ratio + clipped_ratio)

    # Text contrast (blue/green channel analysis)
    # to detect red-on-yellow, green-on-white, etc.

    return {
        'sharpness': sharpness,
        'exposure': exposure_score,
        'dark_ratio': dark_ratio,
        'clipped_ratio': clipped_ratio,
        'quality_tier': 'good' | 'fair' | 'poor'
    }
```

#### Processing Path Selection
```python
quality = analyze_image_quality(img)

if quality['quality_tier'] == 'good':
    # Already decent from frontend
    # Light backend processing
    pipeline = [
        'glare_removal',
        'light_denoise',
        'final_contrast',
        'upsampling_optional'
    ]

elif quality['quality_tier'] == 'fair':
    # Needs moderate enhancement
    pipeline = [
        'perspective_correction',
        'glare_removal',
        'denoise_medium',
        'clahe_contrast',
        'unsharp_mask',
        'upsampling_2x'
    ]

else:  # 'poor'
    # Heavy processing needed
    pipeline = [
        'auto_rotate_deskew',
        'perspective_correction_homography',
        'specular_inpainting',
        'denoise_strong',
        'color_balance',
        'clahe_aggressive',
        'unsharp_mask_strong',
        'super_resolution_swinir',  # ML model
        'ocr_confidence_check'
    ]
```

---

### 2.3 Stage-by-Stage Backend Processing

#### Stage 1: Label Region Refinement & Perspective Correction

```python
def perspective_correct(img):
    """
    Detect label corners using edge detection + contour approximation.
    Correct perspective so text aligns horizontally.
    """

    # Convert to grayscale
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Edge detection
    edges = cv.Canny(gray, 50, 150)

    # Find contours
    contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    # Find largest contour (likely label)
    largest = max(contours, key=cv.contourArea)

    # Approximate as quadrilateral
    epsilon = 0.02 * cv.arcLength(largest, True)
    quad = cv.approxPolyDP(largest, epsilon, True)

    if len(quad) != 4:
        return img, None  # Fallback: return original

    # Extract corners in order (TL, TR, BR, BL)
    pts_src = order_points(quad)

    # Define destination (frontal rectangle)
    h, w = gray.shape
    pts_dst = np.array([
        [0, 0],
        [w, 0],
        [w, h],
        [0, h]
    ], dtype='float32')

    # Compute homography
    M = cv.getPerspectiveTransform(pts_src, pts_dst)

    # Warp perspective
    warped = cv.warpPerspective(img, M, (w, h),
                                 borderMode=cv.BORDER_REPLICATE)

    return warped, M
```

**Latency: ~50-100ms** (contour detection is fast)

#### Stage 2: Glare/Specular Highlight Removal

```python
def remove_glare(img):
    """
    Detect bright specular highlights in L channel.
    Inpaint to remove glare.
    """

    # Convert to LAB
    lab = cv.cvtColor(img, cv.COLOR_BGR2Lab)
    L = lab[:,:,0]

    # Detect bright pixels (glare)
    # Threshold depends on lighting; adjust per image
    # Heuristic: if mean(L) < 100 (dark overall), glare threshold = 220
    #            if mean(L) > 150 (bright overall), glare threshold = 240

    mean_L = np.mean(L)
    glare_threshold = 220 if mean_L < 100 else 240

    glare_mask = (L > glare_threshold).astype(np.uint8) * 255

    # Morphological cleanup (remove specks, fill holes)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (7, 7))
    glare_mask = cv.morphologyEx(glare_mask, cv.MORPH_CLOSE, kernel)
    glare_mask = cv.morphologyEx(glare_mask, cv.MORPH_OPEN, kernel)

    # Inpaint bright regions
    inpainted = cv.inpaint(img, glare_mask, 5, cv.INPAINT_TELEA)

    return inpainted
```

**Latency: ~100-150ms** (inpainting can be slow on large regions)

#### Stage 3: Denoising

```python
def denoise_image(img, strength='light'):
    """
    Multi-scale denoising: preserve edges, remove sensor noise.
    """

    if strength == 'light':
        # Fast: Bilateral filter
        denoised = cv.bilateralFilter(img, 9, 75, 75)

    elif strength == 'medium':
        # Slower: fastNlMeansDenoisingColored
        denoised = cv.fastNlMeansDenoisingColored(
            img,
            h=10,           # Filter strength for luminance
            hForColorComponents=10,
            templateWindowSize=7,
            searchWindowSize=21
        )

    else:  # 'strong'
        # Very slow: Apply NLM twice
        temp = cv.fastNlMeansDenoisingColored(img, h=15, hForColorComponents=15,
                                               templateWindowSize=7, searchWindowSize=21)
        denoised = cv.fastNlMeansDenoisingColored(temp, h=10, hForColorComponents=10,
                                                   templateWindowSize=7, searchWindowSize=21)

    return denoised
```

**Latency:**
- Light: ~50ms
- Medium: ~200-300ms
- Strong: ~500-800ms

#### Stage 4: Color-Adaptive Contrast Enhancement

```python
def enhance_contrast_adaptive(img):
    """
    Apply CLAHE differently based on detected text color.

    Strategy:
    - Red text on yellow: boost L channel heavily
    - Blue text on white: boost L mildly
    - etc.
    """

    # Convert to LAB
    lab = cv.cvtColor(img, cv.COLOR_BGR2Lab)
    L, a, b = cv.split(lab)

    # Detect dominant colors (heuristic: sample center region)
    center_a = np.mean(a[a.shape[0]//4:3*a.shape[0]//4,
                          a.shape[1]//4:3*a.shape[1]//4])
    center_b = np.mean(b[b.shape[0]//4:3*b.shape[0]//4,
                          b.shape[1]//4:3*b.shape[1]//4])

    # Determine color category (crude heuristic)
    if center_a > 130:  # Reddish/magenta
        clip_limit = 2.5  # More aggressive
    elif center_a < 110:  # Greenish
        clip_limit = 2.0
    else:  # Neutral
        clip_limit = 2.0

    # Apply CLAHE on L
    clahe = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    L_enhanced = clahe.apply(L)

    # Merge back
    lab_enhanced = cv.merge([L_enhanced, a, b])
    result = cv.cvtColor(lab_enhanced, cv.COLOR_Lab2BGR)

    return result
```

**Latency: ~100-150ms**

#### Stage 5: Sharpening & Final Tweaks

```python
def final_sharpen(img):
    """
    Light unsharp mask to restore edge crispness.
    """

    gaussian = cv.GaussianBlur(img, (5, 5), 1.0)
    sharpened = cv.addWeighted(img, 1.3, gaussian, -0.3, 0)

    return sharpened
```

**Latency: ~40ms**

#### Stage 6: Optional Super-Resolution (ML)

```python
def super_resolve(img):
    """
    Load lightweight super-resolution model (SwinIR lightweight or ESRGAN-small).
    Upscale 2-4x for small text.

    Only run on 'poor' quality images or very small crops.
    """

    # Pseudo-code (real implementation requires TensorFlow/PyTorch)
    if use_sr:
        model = load_pretrained_model('swinir_lightweight')
        output = model.infer(img, scale=2)
    else:
        output = cv.resize(img, None, fx=2.0, fy=2.0, interpolation=cv.INTER_CUBIC)

    return output
```

**Latency: 500-1500ms** (heavy, only for poor images)

---

### 2.4 OCR & Result Validation

```python
def ocr_and_validate(img):
    """
    Run OCR, validate against food label patterns.
    """

    # Run Tesseract or cloud OCR API
    text = pytesseract.image_to_string(img, config='--psm 6')

    # Regex extraction (nutrition values, ingredients)
    nutrition_lines = extract_nutrition_block(text)
    ingredients = extract_ingredients(text)

    # Confidence scoring
    confidence = calculate_confidence(text, nutrition_lines)

    return {
        'text': text,
        'nutrition': nutrition_lines,
        'ingredients': ingredients,
        'confidence': confidence,
        'readable': confidence > 0.6
    }
```

**Latency: 200-400ms** (OCR is CPU-intensive)

---

### 2.5 Backend Response

```json
{
  "status": "success",
  "stages_applied": [
    "perspective_correction",
    "glare_removal",
    "denoise_medium",
    "clahe_contrast",
    "unsharp_mask"
  ],
  "enhanced_image_base64": "...",
  "ocr": {
    "raw_text": "...",
    "nutrition": {...},
    "ingredients": [...],
    "confidence": 0.87
  },
  "timings": {
    "perspective_correction_ms": 75,
    "glare_removal_ms": 120,
    "denoise_ms": 250,
    "contrast_ms": 110,
    "ocr_ms": 350,
    "total_ms": 905
  },
  "quality_hints": [
    "image quality was fair - used medium denoise",
    "detected red text - applied color-adaptive contrast",
    "ocr confidence 0.87 - good, but verify numbers manually"
  ]
}
```

---

## Part 3: Latency Handling & UX Strategy

### 3.1 Perceived Performance

**Problem:** Backend processing takes 0.5-2 seconds. User sees spinner and gets frustrated.

**Solution: Progressive feedback**

```
Timeline:

T+0ms:    Preview image shown (from frontend fusion)
          Spinner: "Sending to backend..."

T+100ms:  ✓ Server received
          Spinner: "Analyzing structure..."
          [Progress bar: 20%]

T+300ms:  ✓ Perspective corrected
          [Progress bar: 40%]

T+500ms:  ✓ Glare removed
          [Progress bar: 60%]

T+900ms:  ✓ Enhanced & OCR ready
          [Progress bar: 100%]

T+1000ms: Results page appears
          Show enhanced image
          Show OCR with confidence
```

**Implementation:**
1. Backend sends progress events via WebSocket
2. Frontend updates progress bar in real-time
3. User sees they're not stuck (perceived latency drops 50%)

### 3.2 Latency Hiding Strategies

#### Strategy A: Optimistic UI
```
While backend processes:
- Show frontend-enhanced preview immediately
- Show placeholder OCR ("Analyzing...")
- When backend returns, swap in final result

User perceives: No delay, content is always visible
```

#### Strategy B: Parallel Processing
```
Frontend sends:
- Stage-1 JPEG (for quick preview)
- Raw burst frames (optional, if user opts-in)

Backend:
- Immediately show preview
- Meanwhile, do heavy processing on burst frames
- Replace preview with final result when ready
```

#### Strategy C: Adaptive Quality
```
if (network_speed_slow):
    process_lightweight = true  // Skip SR, reduce denoise
    eta_ms = 300
else:
    process_heavyweight = true  // Use all stages
    eta_ms = 1200

Show user: "Processing (≈{eta}ms expected)"
```

### 3.3 Device-Specific Latency Tuning

#### Mobile (Weak GPU, Decent CPU)
```
Frontend:
- Burst: 5 frames (not 7)
- Alignment: Translational only
- Fusion: Light (skip well-exposedness, use contrast+saturation)
- CLAHE: 6x6 tiles (not 8x8)
Total: ~300ms

Backend:
- Skip SR unless explicitly needed
- Use light denoise (bilateral only)
- Total: ~400-600ms
```

#### Desktop/Laptop (Strong GPU/CPU)
```
Frontend:
- Burst: 7 frames
- Alignment: Full translational + rotation detection
- Fusion: Full three-weight model
- CLAHE: 8x8 tiles + unsharp
Total: ~500ms

Backend:
- Full pipeline
- Optional SR for poor images
- Total: ~800-1500ms
```

---

## Part 4: Handling Unpredictable Images

### 4.1 Color Variation Handling

**Problem:** Labels come in all colors (yellow, orange, red, white, blue, black).
Single preprocessing approach fails.

**Solution: Color-Aware Adaptive Processing**

```python
def detect_label_color(img):
    """
    Sample label region, determine dominant colors.
    Return color category.
    """

    # Sample center 30% of image (likely label)
    h, w = img.shape[:2]
    center = img[h//4:3*h//4, w//4:3*w//4]

    # Convert to HSV
    hsv = cv.cvtColor(center, cv.COLOR_BGR2HSV)
    h_chan, s_chan, v_chan = cv.split(hsv)

    # Compute mean hue
    mean_hue = np.mean(h_chan)
    mean_sat = np.mean(s_chan)
    mean_val = np.mean(v_chan)

    # Classify
    if mean_sat < 30:
        return 'grayscale'  # B/W or gray label
    elif 15 < mean_hue < 25:
        return 'yellow'      # Yellow/gold labels
    elif 25 < mean_hue < 40:
        return 'orange'      # Orange labels
    elif 150 < mean_hue < 180:
        return 'blue'        # Blue labels
    elif mean_hue < 15 or mean_hue > 165:
        return 'red'         # Red/magenta labels
    elif 40 < mean_hue < 80:
        return 'green'       # Green labels
    else:
        return 'other'
```

#### Color-Specific Processing Pipelines

```python
COLOR_PIPELINES = {
    'yellow': {
        'extract_channel': 'green',      # Red text on yellow
        'contrast_clip_limit': 2.5,
        'denoise_strength': 'medium',
        'notes': 'Red-on-yellow has low contrast; boost aggressively'
    },
    'white': {
        'extract_channel': 'value',      # Any color on white shows up
        'contrast_clip_limit': 2.0,
        'denoise_strength': 'light',
        'notes': 'High contrast already; avoid over-processing'
    },
    'blue': {
        'extract_channel': 'red',        # Yellow text on blue is low contrast
        'contrast_clip_limit': 2.5,
        'denoise_strength': 'medium',
        'notes': 'Yellow-on-blue needs boost'
    },
    'grayscale': {
        'extract_channel': 'value',      # Just use luminance
        'contrast_clip_limit': 2.0,
        'denoise_strength': 'medium',
        'notes': 'Neutral, standard processing'
    }
}

# Select pipeline based on detected color
color = detect_label_color(img)
pipeline_config = COLOR_PIPELINES.get(color, COLOR_PIPELINES['grayscale'])

# Apply color-specific contrast
clahe = cv.createCLAHE(clipLimit=pipeline_config['contrast_clip_limit'],
                       tileGridSize=(8, 8))
# ... rest of processing
```

### 4.2 Handling Dirt, Wrinkles, Curved Surfaces

#### Dirt/Scratches
```
Frontend denoising handles light dirt.
Backend: Strong denoise + inpainting if needed.
Fallback: Show quality warning ("Image has dirt, OCR may be less accurate").
```

#### Wrinkles/Texture
```
These distort text geometry.
If detected (via edge density), apply:
- Morphological smoothing (closing)
- Light blur before thresholding
- Warn user: "Label is wrinkled; retake for better results"
```

#### Curved Surface (Bottle/Can)
```
Simple approach: Perspective correction + light local warp
Advanced: Train a dewarp model (harder, ML-based)

For MVP: Detect curvature via line detection
If too curved, warn user: "Angle the label flat"
```

### 4.3 Glare Variation

```
Low glare (clear):
  → Threshold: L > 240
  → Inpaint radius: 3

Medium glare (some bright spots):
  → Threshold: L > 220
  → Inpaint radius: 5
  → Also apply tone-mapping to compress highlights

Heavy glare (overexposed region):
  → Threshold: L > 200
  → Inpaint radius: 7
  → Use exemplar-based inpainting or fallback to reconstruction
```

---

## Part 5: Implementation Roadmap

### Phase 1: MVP (Week 1-2)
```
Frontend:
✅ MediaPipe detector (train custom model OR use color mask fallback)
✅ Sharpness check (Laplacian variance)
✅ Burst capture (5 frames)
✅ Cheap alignment (template matching, downscaled)
✅ Weighted fusion (3 weights: contrast, saturation, exposure)
✅ CLAHE + unsharp (light)

Backend:
✅ Perspective correction
✅ Light denoise
✅ CLAHE adaptive
✅ Unsharp mask
✅ Tesseract OCR
✅ Progress events (WebSocket)

UX:
✅ Live camera with bbox overlay
✅ Sharpness/exposure quality bars
✅ Capture button
✅ Preview page (approve/retake)
✅ Progress spinner with %
✅ Results page with OCR

Total latency target: 1.5s (frontend 0.5s, backend 1s)
```

### Phase 2: Robustness (Week 3-4)
```
Frontend:
✅ Rotation detection (if detected, skip rotation align)
✅ Adaptive quality thresholds per device
✅ Fallback to single frame if fusion fails

Backend:
✅ Color detection & adaptive pipelines
✅ Glare variation handling
✅ Curv ature detection + warning
✅ Dirt detection + denoise tuning

Testing:
- 100+ images with varied lighting, colors, angles
- Measure OCR accuracy vs. manual ground truth
- Latency profiling on different devices
```

### Phase 3: Polish (Week 5+)
```
Frontend:
✅ Burst on weak devices (3 frames, light fusion)
✅ Low-CPU mode toggle

Backend:
✅ Optional SR for poor images (SwinIR lightweight)
✅ Color balance preprocessing
✅ Multi-language OCR hints
✅ User confidence feedback ("Retake for better OCR")

Analytics:
✅ Track OCR confidence per image
✅ Monitor latency percentiles
✅ Flag images that need manual review
```

---

## Part 6: Performance Budget

### Target Latencies

| Stage | Time | Device |
|-------|------|--------|
| Burst capture (5 frames) | 150ms | Mobile |
| Alignment (downscaled) | 50ms | Mobile |
| Fusion | 250ms | Mobile |
| CLAHE + unsharp | 80ms | Mobile |
| **Total Frontend** | **530ms** | Mobile |
| | | |
| Perspective | 75ms | Server |
| Glare removal | 120ms | Server |
| Denoise | 250ms | Server |
| CLAHE + sharpen | 110ms | Server |
| OCR | 350ms | Server |
| **Total Backend** | **905ms** | Server |
| | | |
| Network upload | 200ms | Avg WiFi |
| Network download | 150ms | Avg WiFi |
| **Total E2E** | **~1.8s** | WiFi |

### Optimization Levers (if latency budget exceeded)

1. **Reduce burst to 3 frames** → -100ms frontend
2. **Skip fusion, pick sharpest frame** → -200ms frontend
3. **Skip SR on poor images** → -1000ms backend
4. **Use lightweight denoise only** → -200ms backend
5. **Run OCR async (show preview first)** → Perceived latency -350ms
6. **Compress upload JPEG to 0.7 quality** → -50ms network

---

## Part 7: Fallback Strategies

### If Frontend Fails

```
Scenario: MediaPipe model not loading, HSV color mask fails, burst alignment broken

Fallback 1:
  - Skip burst, capture single best frame
  - Send to backend as-is
  - Let backend do all processing
  → Latency: frontend 200ms, backend 1200ms (heavy processing)

Fallback 2:
  - Capture + light CLAHE only
  - Send to backend
  - Show user: "Detection failed; manual image processing"
  → Latency: frontend 100ms, backend full
```

### If Backend Fails

```
Scenario: Perspective correction fails, OCR confidence too low

Action:
  - Show frontend preview (already good)
  - Flag image as "needs manual review"
  - Offer: "Send to human reviewer" button
  - OR: "Try different angle & retake"

OCR confidence < 0.5:
  - Mark with warning badge
  - Show raw OCR text + "(Low confidence - please verify)"
  - Offer edit field to correct
```

---

## Part 8: Testing Strategy

### Unit Tests (Frontend)

```javascript
// Test sharpness detection
test('Laplacian variance correctly identifies blur', () => {
  let blurry = gaussianBlur(testImage, 7);
  let sharp = testImage;

  assert(variance(blurry) < variance(sharp));
});

// Test burst alignment
test('Template matching finds correct offset', () => {
  let ref = testFrame1;
  let shifted = warpAffine(testFrame1, {dx: 10, dy: 5});

  let {dx, dy} = alignTranslate(ref, shifted);
  assert(abs(dx - 10) < 2);  // Allow 2px error
  assert(abs(dy - 5) < 2);
});

// Test fusion weighting
test('Fusion produces reasonable per-pixel weights', () => {
  let fused = weightedFuse([frame1, frame2, frame3]);

  assert(fused is valid cv.Mat);
  assert(fused.channels == 3);  // BGR
});
```

### Integration Tests (End-to-End)

```python
# Test on 50 real food labels (varied colors, lighting, angles)
test_images = [
  'yellow_cereal_box.jpg',
  'red_sauce_jar.jpg',
  'white_milk_bottle.jpg',
  'blue_snacks_bag.jpg',
  'glare_heavy.jpg',
  'blurry_mobile.jpg',
  'curved_can.jpg',
  # ... 43 more
]

for img_path in test_images:
    img = cv.imread(img_path)

    # Frontend processing
    fused = frontend_process(img)

    # Backend processing
    result = backend_process(fused)

    # Validate OCR
    ocr_text = result['ocr_text']
    ground_truth = load_ground_truth(img_path)

    # Compute character error rate (CER)
    cer = levenshtein_distance(ocr_text, ground_truth) / len(ground_truth)

    assert(cer < 0.15)  # < 15% character error is acceptable
    assert(result['confidence'] > 0.5)
```

### Performance Profiling

```python
# Measure latency by stage
import time

timings = {}

# Frontend
start = time.time()
fused = frontend_process(img)
timings['frontend'] = (time.time() - start) * 1000

# Backend
start = time.time()
result = backend_process(fused)
timings['backend'] = (time.time() - start) * 1000

# Percentiles
p50 = np.percentile(all_latencies['backend'], 50)
p95 = np.percentile(all_latencies['backend'], 95)
p99 = np.percentile(all_latencies['backend'], 99)

print(f"Backend latency: p50={p50}ms, p95={p95}ms, p99={p99}ms")

# Target: p95 < 1200ms
assert(p95 < 1200)
```

---

## Summary Table

| Component | Technology | Latency | Handles |
|-----------|-----------|---------|---------|
| **Label Detection** | MediaPipe + HSV fallback | 30-50ms | Any color, orientation |
| **Sharpness Check** | Laplacian variance | 5ms | Blur detection |
| **Burst Capture** | N=5-7 frames | 150-200ms | Hand tremor, focus |
| **Alignment** | Template matching (downscale) | 50-100ms | Translational motion |
| **Fusion** | Contrast + saturation + exposure weights | 200-300ms | Noise, glare, underexposure |
| **CLAHE + Sharpen** | OpenCV.js | 80ms | Contrast boost, crispness |
| **Perspective** | Homography + edge detection | 75ms | Tilted labels |
| **Glare Removal** | LAB thresholding + inpaint | 120ms | Specular highlights |
| **Denoise** | fastNlMeansDenoising | 250ms | Sensor noise |
| **Adaptive Contrast** | Color-aware CLAHE | 110ms | Red-on-yellow, etc. |
| **OCR** | Tesseract | 350ms | Text extraction |

---

## Next Steps

1. **Train MediaPipe custom model** (if not using HSV fallback)
   - Collect 100+ label images
   - Annotate bounding boxes
   - Use MediaPipe Model Maker (1-2 hours)
   - Export TFLite + integrate

2. **Implement Phase 1 MVP**
   - Frontend: Burst + fusion + CLAHE
   - Backend: Perspective + denoise + OCR
   - E2E test on 30 images

3. **Profile & optimize**
   - Measure real latencies
   - Identify bottlenecks
   - Apply optimization levers

4. **Collect real user data**
   - Launch MVP
   - Track OCR accuracy, latencies, error rates
   - Use feedback to refine Phase 2

---

**Questions for refinement:**

- Do you want to train a custom MediaPipe model, or use HSV color mask fallback for now?
- What's your budget for SR model (SwinIR) – is 1.5s backend latency acceptable for best quality?
- Should we prioritize mobile latency (keep frontend heavy, backend light) or balanced?
- Do you have labeled test data for evaluation, or should we collect it?
