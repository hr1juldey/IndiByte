# Qwen CLI - Start Here

## 30-Second Summary

You're taking over **Bytelense** - an AI food label scanner with OCR integration.

**Status:** Backend + OCR done ✅ | Need: Real-world testing ⏳

**Your main task:** Test with real food labels, validate accuracy > 85%, then integrate frontend.

---

## What You Need to Know

### The System

```
User takes photo → Frontend burst capture → Backend OCR → Nutrition facts
                      (~500ms)               (~4.6s)
```

### What's Done

- ✅ Image processing service (adaptive quality-based)
- ✅ OCR endpoint: `POST /api/label/process-with-ocr`
- ✅ 50+ unit tests
- ✅ Complete documentation

### What's Missing

- ⏳ Real-world testing (20-50 food labels)
- ⏳ OCR accuracy measurement
- ⏳ Frontend integration (ScanPage.tsx)
- ⏳ Mobile validation

---

## How to Start (5 Minutes)

### 1. Read This

```
Read: Bytelense/HANDOFF_TO_QWEN.md (10 min overview)
```

### 2. Start Backend

```bash
cd ~/Documents/Projects/IndiByte/IndiByte/Bytelense/backend
python3 -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000
```

### 3. Test OCR

```bash
# Save a food label image as test.jpg
BASE64=$(base64 -w 0 < test.jpg)

curl -X POST http://localhost:8000/api/label/process-with-ocr \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"data:image/jpeg;base64,'$BASE64'","metadata":{}}'
```

Should return: Enhanced image + OCR markdown + timing

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/api/label_processing.py:324-471` | OCR endpoint (200 lines) |
| `backend/app/services/label_processing.py` | Image processing (600 lines) |
| `backend/tests/test_label_processing.py` | Tests (400 lines) |
| `frontend/src/lib/burstCapture.ts` | Frame fusion (450 lines) |
| `frontend/src/pages/ScanPage.tsx` | Needs update for OCR |

---

## Phase 4 Tasks (Your Work)

### Priority 1: Real-World Testing

```bash
# 1. Get 20-50 food label images
# 2. Test each one
for img in food_labels/*.jpg; do
  BASE64=$(base64 -w 0 < "$img")
  curl -X POST http://localhost:8000/api/label/process-with-ocr \
    -H "Content-Type: application/json" \
    -d '{"image_base64":"data:image/jpeg;base64,'$BASE64'"}' | jq .
done

# 3. Measure accuracy (compare OCR output vs manual)
# Target: > 85% accuracy
```

### Priority 2: Frontend Integration

Update `frontend/src/pages/ScanPage.tsx`:

```typescript
// Add OCR endpoint call
const response = await fetch('/api/label/process-with-ocr', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ image_base64: base64 })
});

const result = await response.json();
// Display OCR results in UI
```

### Priority 3: Mobile Testing

- Test on Android Firefox
- Test on iOS Firefox
- Camera + burst capture responsive?
- OCR display working?

---

## Key API Response

```json
{
  "status": "success",
  "enhanced_image_base64": "...",
  "quality_analysis": {
    "quality_tier": "fair",
    "sharpness": 95.2,
    "exposure_score": 0.82
  },
  "ocr_result": {
    "markdown": "# Nutrition Facts\nServing Size: 1 cup\n...",
    "html": "<h1>Nutrition Facts</h1>...",
    "token_count": 256,
    "error": false
  },
  "total_processing_ms": 598.2,
  "ocr_time_ms": 3420.5,
  "total_time_ms": 4018.7
}
```

---

## Performance Expectations

| Stage | Duration |
|-------|----------|
| Frontend burst | ~500ms |
| Image processing | ~600ms (fair quality) |
| OCR inference | ~3500ms |
| **Total** | **~4.6s** |
| First request | 30-60s (model loading) |

---

## Documentation Guide

**Choose based on what you need:**

- `START_HERE.md` - Quick navigation (5 min)
- `HANDOFF_TO_QWEN.md` - Full context (30 min) ⭐ READ THIS FIRST
- `DEPLOYMENT_GUIDE.md` - Setup guide (15 min)
- `OCR_QUICK_START.md` - Testing guide (10 min)
- `OCR_INTEGRATION.md` - API reference (20 min)

---

## Quick Commands

```bash
# Backend health
curl http://localhost:8000/api/label/health

# Run tests
cd backend && pytest tests/test_label_processing.py -v

# Check logs
tail -f backend.log
```

---

## Success Criteria

- [ ] Real-world testing complete (20-50 labels)
- [ ] OCR accuracy measured (target > 85%)
- [ ] Frontend integrated with OCR endpoint
- [ ] Mobile testing validated
- [ ] No crashes on edge cases
- [ ] Processing time < 6s per image

---

## Troubleshooting

**OCR timeout (>10s)?**

- First request: normal (model loading)
- Check: `nvidia-smi` (GPU available?)
- Pre-warm: Send test image first

**"Invalid image data"?**

- Ensure: `data:image/jpeg;base64,...` format
- Check: Image is valid JPEG/PNG

**Camera not working?**

- Need: HTTPS enabled
- Check: Browser permissions

---

## Next Action

1. Read `HANDOFF_TO_QWEN.md` (full context)
2. Start backend service
3. Test OCR endpoint with a real food label
4. Begin Phase 4 testing

---

**Ready?** Start with `HANDOFF_TO_QWEN.md` → 30 min read → Full context 🚀
