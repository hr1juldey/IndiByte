# Next Steps - Complete Integration Plan

## Current Status

### Backend (Claude Code) ✅

**Status**: Running perfectly at <http://localhost:8000>

- ✅ All services healthy (Ollama, OpenFoodFacts, Storage)
- ⚠️ SearXNG slow/unreachable (not critical for simplified testing)
- ✅ Simplified scan flow active (returns mock DetailedAssessment)
- ✅ WebSocket ready for connections
- ✅ REST API ready

### Frontend (Qwen) 🟡

**Status**: Infrastructure complete, UI missing

- ✅ Phase 1-6 complete (types, API client, WebSocket, camera hook, base components)
- ❌ Actual application UI not built yet
- ❌ Default Vite template still showing (counter button)

---

## What Claude Code (Backend) Should Do Next

### Option 1: Fix SearXNG Status (Optional)

The backend shows "degraded" because SearXNG is unreachable, but this doesn't matter for simplified testing.

**If you want to fix it**:

1. Keep pinging SearXNG every 10 minutes to keep it awake:

   ```bash
   # Add a cron job or background task
   while true; do
     curl -s "http://192.168.1.4/search?q=test&format=json" > /dev/null
     sleep 600  # 10 minutes
   done &
   ```

2. Or modify health check to mark SearXNG as optional:
   - Change `all_ok = False` to only fail on critical services
   - SearXNG failure shouldn't mark backend as "degraded"

**If you don't care**: Leave it as is. The simplified scan flow doesn't use SearXNG anyway.

### Option 2: Monitor Backend Logs

Keep an eye on the backend server for any errors when qwen starts testing:

```bash
# Backend is already running in background
# Check logs if needed
curl http://localhost:8000/health | python -m json.tool
```

### Option 3: Create Test User Profile (For Testing)

When qwen starts testing the scan flow, they'll need a user profile. Create one:

```bash
curl -X POST http://localhost:8000/api/auth/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "name": "testuser",
    "demographics": {
      "age": 30,
      "gender": "male",
      "height_cm": 175,
      "weight_kg": 75
    },
    "lifestyle_habits": {
      "sleep_hours": 7,
      "work_style": "desk_job",
      "exercise_frequency": "3-4_times_week",
      "commute_type": "bike",
      "smoking": "no",
      "alcohol": "light",
      "meals_per_day": 3
    },
    "goals": {
      "fitness_goal": "weight_loss",
      "target_weight_kg": 70,
      "dietary_restrictions": [],
      "condition_focus": []
    },
    "food_preferences": {
      "diet_type": "omnivore",
      "allergies": [],
      "dislikes": [],
      "cultural_restrictions": []
    }
  }'
```

This will create a "testuser" profile that qwen can use for testing scans.

**Recommended**: Do Option 3 now, skip Options 1-2 (not critical).

---

## What Qwen (Frontend) Should Do Next

### Phase 7: Build Actual Application UI

Qwen has built all the infrastructure but not the actual application. They need to build 3 components:

1. **ScanPage.tsx** - Main scanning interface with camera + WebSocket
2. **VerdictDisplay.tsx** - Displays DetailedAssessment results
3. **App.tsx** - Integrate everything together

### Instructions for Qwen

Copy this message to qwen-coder CLI:

```
Your Phase 1-6 infrastructure is complete. Now build the actual application UI.

Read and follow: @QWEN_PHASE_7_BUILD_UI.md

This has 3 steps:
- Step 1: Create ScanPage.tsx (camera + scan flow)
- Step 2: Create VerdictDisplay.tsx (display results)
- Step 3: Update App.tsx (integrate everything)

ONE FILE AT A TIME. Start with Step 1, then STOP and wait for approval.

Begin with Step 1 now.
```

---

## Expected Development Flow

### Step-by-Step Process

1. **You create test user** (backend task above)

2. **You tell qwen** to start Phase 7, Step 1

3. **Qwen creates ScanPage.tsx**
   - Integrates camera hook, WebSocket client, types
   - Builds UI for camera view, capture button, progress bar
   - Handles scan states (idle → scanning → complete)

4. **You verify ScanPage.tsx**
   - Check TypeScript compiles
   - Check code looks reasonable
   - Approve qwen to continue

5. **Qwen creates VerdictDisplay.tsx**
   - Displays DetailedAssessment with all sections
   - Color-coded by verdict type
   - Shows highlights, warnings, nutrition, citations

6. **You verify VerdictDisplay.tsx**
   - Check component handles all assessment fields
   - Approve qwen to continue

7. **Qwen updates App.tsx**
   - Replaces default Vite template
   - Wraps ScanPage with ErrorBoundary
   - Clean integration

8. **End-to-End Testing**:

   ```bash
   # Frontend should already be running
   cd frontend
   pnpm run dev
   ```

   Open <http://localhost:5173> in browser:
   - ✅ Click "Start Camera" → camera activates
   - ✅ Click "Capture" → progress bar shows
   - ✅ Wait 2-3 seconds → verdict displays
   - ✅ See mock data from backend (Lay's Chips example)

---

## Troubleshooting Guide

### If Frontend Can't Connect to Backend

**Check CORS**:
Backend should allow all origins (already configured in main.py):

```python
allow_origins=["*"]
```

**Check WebSocket URL**:
Frontend should connect to: `http://localhost:8000`

### If Camera Doesn't Work

**Browser Permissions**:

- Chrome/Edge: Allow camera access when prompted
- Firefox: Check privacy settings
- HTTPS required for production (localhost is OK for dev)

**Mobile Testing**:

- Use ngrok or similar to expose localhost
- Or deploy to HTTPS server

### If Scan Doesn't Start

**Check Backend Logs**:
Look for WebSocket connection and scan_simple handler logs

**Check Frontend Console**:
Open browser DevTools → Console tab
Should see WebSocket connection messages

### If Progress Bar Doesn't Update

**Check Event Listeners**:
Make sure ScanPage.tsx listens to `scan_progress` event

**Check Backend**:
Simplified scan should emit 5 progress events (see scan_simple.py)

---

## Timeline Estimate

### With Qwen Working Efficiently

- **Step 1 (ScanPage.tsx)**: 15-30 minutes
- **Step 2 (VerdictDisplay.tsx)**: 15-30 minutes
- **Step 3 (App.tsx)**: 5-10 minutes
- **Testing & Fixes**: 15-30 minutes

**Total**: 1-2 hours to complete MVP

### Potential Issues

- TypeScript errors (qwen usually good at this)
- Styling tweaks (Tailwind CSS learning curve)
- WebSocket connection issues (check CORS, URL)

---

## Success Criteria

### When Everything Works

1. **Frontend loads** at <http://localhost:5173>
2. **Camera activates** when button clicked
3. **Capture works** (no errors)
4. **WebSocket connects** to backend
5. **Progress bar updates** through 5 stages
6. **Verdict displays** with:
   - Product name: "Lay's Classic Potato Chips"
   - Verdict: 🟡 MODERATE (score 6.5)
   - Highlights: 3 items
   - Warnings: 4 items
   - Nutrition data table
   - Citations: 3 sources
   - Alternatives: 4 products
7. **No console errors**
8. **Responsive on mobile**

---

## Files to Watch

### Frontend Files Qwen Will Create

- `frontend/src/components/ScanPage.tsx` (Step 1)
- `frontend/src/components/VerdictDisplay.tsx` (Step 2)
- `frontend/src/App.tsx` (Step 3, updated)
- `frontend/src/index.css` (Step 3, updated)

### Backend Files (Already Done)

- `backend/app/api/scan_simple.py` (mock scan handler)
- `backend/app/models/schemas.py` (data models)
- `backend/app/main.py` (server entry point)

---

## After MVP Works

### Optional Enhancements (Future)

1. **Switch to Real Pipeline**:
   - Change `scan_simple` → `scan` in main.py
   - Enable real OCR, LLM, search

2. **Add Authentication**:
   - Login page
   - Profile management
   - User-specific scans

3. **Add History**:
   - Save scan results
   - View past scans
   - Weekly summaries

4. **Add Onboarding**:
   - Interactive questionnaire
   - Health profile setup
   - Goal setting

5. **Polish UI**:
   - Animations
   - Better loading states
   - Mobile optimizations

---

## Quick Commands Reference

### Backend

```bash
# Check health
curl http://localhost:8000/health

# Create test user
curl -X POST http://localhost:8000/api/auth/onboard \
  -H "Content-Type: application/json" \
  -d @test_user.json

# View logs (if running in background)
# Check terminal where uvicorn is running
```

### Frontend

```bash
# Start dev server
cd frontend
pnpm run dev

# Build for production
pnpm run build

# Check TypeScript
pnpm run build  # Will fail if type errors
```

### Both

```bash
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# WebSocket: ws://localhost:8000
```

---

## Summary

**Your immediate next steps**:

1. ✅ Create test user profile (backend, optional but recommended)
2. ✅ Tell qwen to read @QWEN_PHASE_7_BUILD_UI.md and start Step 1
3. ✅ Verify each step as qwen completes it
4. ✅ Test end-to-end when Step 3 is done
5. ✅ Celebrate working MVP! 🎉

**Backend Status**: ✅ Ready and waiting
**Frontend Status**: 🟡 Ready to build UI
**Estimated Time**: 1-2 hours
**Difficulty**: Low (qwen is good at UI implementation)

Let me know if you hit any issues!
