# Backend Implementation Checklist

**Goal**: Get Bytelense backend running and ready to serve the frontend

**Critical Rule**: Test each phase before moving to the next. If it doesn't work, fix it before proceeding.

---

## What Qwen's Frontend Needs from Backend

Based on frontend inspection:

- ✅ Vite project initialized
- ✅ TypeScript + Tailwind configured
- ⏳ Will need: Type definitions, API client, WebSocket client
- ⏳ Frontend expects these backend endpoints operational

**Backend must provide**:

1. `GET /health` - Health check
2. `POST /api/auth/login` - Name-based login
3. `GET /api/profile/{name}` - Get user profile
4. `PATCH /api/profile/{name}` - Update profile
5. WebSocket events: `start_scan`, `scan_progress`, `scan_complete`, `scan_error`

---

## Phase 0: Prerequisites (CHECK FIRST)

### ✅ Task 0.1: Verify External Services

**Commands**:

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check SearXNG is accessible
curl "http://192.168.1.4/search?q=test&format=json"

# Check Python version
python3 --version  # Should be 3.12+
```

**Verification**:

- [ ] Ollama returns list of models (including qwen3:30b or qwen3:8b)
- [ ] SearXNG returns JSON response
- [ ] Python 3.12+ installed

**If any fail**: Refer to VALIDATION_RESULTS.md for setup instructions

---

## Phase 1: Environment Setup (30 minutes)

### ✅ Task 1.1: Create Virtual Environment

**Commands**:

```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/backend

# Create venv
python3.12 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

**Verification**:

- [ ] `which python` shows venv path
- [ ] `python --version` shows 3.12+

---

### ✅ Task 1.2: Install Dependencies

**Commands**:

```bash
# Install from parent requirements.txt
pip install -r ../../requirements.txt

# Install additional backend-specific deps
pip install uvicorn[standard]

# Install pyzbar for barcode detection (system dep first)
sudo apt-get update
sudo apt-get install -y libzbar0
pip install pyzbar
```

**Verification**:

```bash
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import dspy; print('DSPy:', dspy.__version__)"
python -c "import socketio; print('SocketIO:', socketio.__version__)"
python -c "from pyzbar import pyzbar; print('pyzbar: OK')"
python -c "import cv2; print('OpenCV:', cv2.__version__)"
```

**Expected output**: All imports successful, no errors

---

### ✅ Task 1.3: Create .env File

**File**: `/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/backend/.env`

```bash
# Application
APP_NAME=Bytelense
DEBUG=True
LOG_LEVEL=INFO

# Ollama
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
# Use qwen3:8b for development (faster)
# Use qwen3:30b for production (better quality)

# SearXNG
SEARXNG_URL=http://192.168.1.4
SEARXNG_API_BASE=http://192.168.1.4

# Storage
PROFILES_DIR=./data/profiles
SCAN_HISTORY_DIR=./data/scan_history

# Image processing
MAX_IMAGE_SIZE_MB=10

# Development
RELOAD=True
```

**Verification**:

```bash
cat .env
```

**Expected**: File exists with correct values

---

### ✅ Task 1.4: Create Data Directories

**Commands**:

```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/backend

mkdir -p data/profiles
mkdir -p data/scan_history
mkdir -p data/cache/refined_questions

# Test write permissions
touch data/profiles/test.json
rm data/profiles/test.json
```

**Verification**:

- [ ] Directories created
- [ ] Write test successful

---

## Phase 2: Update Data Models (15 minutes)

### ✅ Task 2.1: Replace Schemas with LLD-Compliant Version

**Commands**:

```bash
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/backend/app/models

# Backup old schemas
cp schemas.py schemas_old_backup.py

# Replace with new version
cp schemas_v2.py schemas.py

# Verify syntax
python -c "from app.models.schemas import EnhancedUserProfile; print('✓ Schemas OK')"
```

**Verification**:

- [ ] No syntax errors
- [ ] Can import EnhancedUserProfile
- [ ] Can import DetailedAssessment

---

## Phase 3: Core Services Implementation (1-2 hours)

### ✅ Task 3.1: Implement HealthModelingEngine

**File**: `backend/app/engines/health_modeling.py` (CREATE NEW)

**What to implement** (from LLD Section 4):

1. `calculate_metrics()` - Main entry point
2. `_calculate_bmi()` - BMI calculation
3. `_calculate_bmr_mifflin()` - BMR using Mifflin-St Jeor
4. `_calculate_activity_multiplier()` - From lifestyle habits
5. `_calculate_energy_budget()` - Daily calorie target
6. `_assess_health_risks()` - Risk factor identification
7. `calculate_daily_targets()` - Macro/micro targets

**Reference**: See LLD_PART3.md Section 14.2 for complete function signatures

**Test after implementation**:

```bash
python -c "
from app.engines.health_modeling import HealthModelingEngine
from app.models.schemas import Demographics, LifestyleHabits, HealthGoals

engine = HealthModelingEngine()
demo = Demographics(age=28, gender='male', height_cm=175, weight_kg=72)
lifestyle = LifestyleHabits(
    sleep_hours=7,
    work_style='desk_job',
    exercise_frequency='3-4_times_week',
    commute_type='bike',
    smoking='no',
    alcohol='light',
    stress_level='moderate'
)
goals = HealthGoals(primary_goal='maintain_weight')

# This should work without errors
print('✓ HealthModelingEngine ready for testing')
"
```

**Verification**:

- [ ] File created
- [ ] All functions implemented
- [ ] Test script runs without errors
- [ ] BMI calculation is correct (23.51 for above example)

---

### ✅ Task 3.2: Implement ProfileStore (if not complete)

**File**: `backend/app/core/profile_store.py`

**Check what exists**:

```bash
grep -n "class ProfileStore" backend/app/core/profile_store.py
```

**Verify it has** (from LLD Section 2):

- `create_profile()` - Create new profile
- `get_profile()` - Retrieve by name
- `update_profile()` - Partial update
- `delete_profile()` - Delete profile
- `profile_exists()` - Check existence

**Test**:

```bash
python -c "
from app.core.profile_store import ProfileStore
from app.models.schemas import EnhancedUserProfile, Demographics, LifestyleHabits, HealthMetrics, HealthGoals, FoodPreferences, DailyTargets
import asyncio

async def test():
    store = ProfileStore()

    # Create test profile
    profile = EnhancedUserProfile(
        name='test_user',
        demographics=Demographics(age=28, gender='male', height_cm=175, weight_kg=72),
        lifestyle_habits=LifestyleHabits(
            sleep_hours=7, work_style='desk_job', exercise_frequency='3-4_times_week',
            commute_type='bike', smoking='no', alcohol='light', stress_level='moderate'
        ),
        health_metrics=HealthMetrics(
            bmi=23.5, bmi_category='normal', bmr=1680, tdee=2310,
            daily_energy_target=2000, health_risks=[]
        ),
        goals=HealthGoals(primary_goal='maintain_weight'),
        food_preferences=FoodPreferences(allergens=['peanuts']),
        daily_targets=DailyTargets(
            calories=2000, protein_g=72, carbs_g=250, fat_g=67,
            fiber_g=30, sugar_g=50, sodium_mg=2300
        )
    )

    await store.create_profile(profile)
    retrieved = await store.get_profile('test_user')
    assert retrieved.name == 'test_user'
    print('✓ ProfileStore working')

asyncio.run(test())
"
```

**Verification**:

- [ ] Test passes
- [ ] Profile JSON file created in `data/profiles/test_user.json`
- [ ] Can retrieve and verify profile

---

### ✅ Task 3.3: Implement Auth Endpoints

**File**: `backend/app/api/auth.py`

**Check existing implementation**, should have:

- `POST /api/auth/login` - Name-based login
- Returns `LoginResponse` from schemas

**Test**:

```bash
# Start server in background
cd /home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/backend
source venv/bin/activate
python -m uvicorn app.main:socket_app --reload &
SERVER_PID=$!
sleep 3

# Test login with existing user
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "test_user"}' | jq

# Test login with new user
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "new_user"}' | jq

# Kill server
kill $SERVER_PID
```

**Expected**:

- Existing user: `{"status": "success", "user_exists": true, "profile": {...}}`
- New user: `{"status": "new_user", "user_exists": false, ...}`

**Verification**:

- [ ] Endpoint responds
- [ ] Returns correct status for existing user
- [ ] Returns correct status for new user
- [ ] Profile data matches schema

---

## Phase 4: Image Processing (1 hour)

### ✅ Task 4.1: Verify Image Processing Service

**File**: `backend/app/services/image_processing.py`

**Should have**:

- `process()` - Main entry point
- Barcode detection with pyzbar
- OCR with Chandra
- Base64 decoding

**Create test image** (if needed):

```bash
# Download a test barcode image
curl -o /tmp/test_barcode.jpg "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/UPC-A-036000291452.svg/640px-UPC-A-036000291452.svg.png"

# Convert to base64
BASE64_IMAGE=$(base64 -w 0 /tmp/test_barcode.jpg)
```

**Test**:

```python
# Save as test_image_processing.py
import asyncio
import base64
from app.services.image_processing import ImageProcessor

async def test():
    processor = ImageProcessor()

    # Load test image
    with open('/tmp/test_barcode.jpg', 'rb') as f:
        image_bytes = f.read()

    base64_image = base64.b64encode(image_bytes).decode()

    # Process
    result = await processor.process(f"data:image/jpeg;base64,{base64_image}")

    print(f"Barcode detected: {result.barcode}")
    print(f"OCR confidence: {result.confidence}")
    print(f"Gaps: {result.gaps}")

    assert result.barcode is not None or result.ocr_text != ""
    print("✓ Image processing working")

asyncio.run(test())
```

**Verification**:

- [ ] Barcode detected OR OCR text extracted
- [ ] No crashes
- [ ] Returns RawOCRExtraction object

---

## Phase 5: WebSocket Scanning Pipeline (2 hours)

### ✅ Task 5.1: Implement Scan Handler

**File**: `backend/app/api/scan.py`

**Should implement** (from LLD Section 10.2):

- `@sio.on('start_scan')` handler
- Emit `scan_started` event
- Emit `scan_progress` events (5 stages)
- Emit `scan_complete` with DetailedAssessment
- Emit `scan_error` on failures

**Stages** (from LLD):

1. image_processing
2. nutrition_retrieval
3. profile_loading
4. scoring
5. assessment_generation

**Test with Socket.IO client**:

```python
# Save as test_websocket.py
import socketio
import asyncio
import base64

async def test():
    sio = socketio.AsyncClient()

    events_received = []

    @sio.on('scan_started')
    def on_started(data):
        print(f"✓ Scan started: {data}")
        events_received.append('started')

    @sio.on('scan_progress')
    def on_progress(data):
        print(f"  Progress: {data['stage']} - {data['message']}")
        events_received.append('progress')

    @sio.on('scan_complete')
    def on_complete(data):
        print(f"✓ Scan complete!")
        print(f"  Product: {data['detailed_assessment']['product_name']}")
        print(f"  Score: {data['detailed_assessment']['final_score']}")
        events_received.append('complete')

    @sio.on('scan_error')
    def on_error(data):
        print(f"✗ Error: {data['message']}")
        events_received.append('error')

    # Connect
    await sio.connect('http://localhost:8000')
    print("✓ Connected to server")

    # Load test image
    with open('/tmp/test_barcode.jpg', 'rb') as f:
        image_bytes = f.read()
    base64_image = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"

    # Start scan
    await sio.emit('start_scan', {
        'user_name': 'test_user',
        'image_base64': base64_image,
        'source': 'camera'
    })

    # Wait for completion
    await asyncio.sleep(30)  # Give it time to process

    await sio.disconnect()

    # Verify
    assert 'started' in events_received
    assert 'progress' in events_received
    assert 'complete' in events_received or 'error' in events_received
    print("✓ WebSocket flow working")

asyncio.run(test())
```

**Run test**:

```bash
# Terminal 1: Start server
python -m uvicorn app.main:socket_app --reload

# Terminal 2: Run test
python test_websocket.py
```

**Verification**:

- [ ] Connection established
- [ ] `scan_started` received
- [ ] At least one `scan_progress` received
- [ ] `scan_complete` OR `scan_error` received
- [ ] No server crashes

---

## Phase 6: Minimal Viable Backend (MVP)

### ✅ Task 6.1: Create Simplified Scan Flow (For Testing)

For initial testing, create a simplified scan handler that:

1. Accepts image
2. Returns mock DetailedAssessment
3. Skips actual OCR/LLM processing

**File**: `backend/app/api/scan_simple.py` (CREATE NEW)

```python
"""Simplified scan handler for initial testing."""
import socketio
from datetime import datetime
import uuid
import asyncio

from app.models.schemas import DetailedAssessment, CitationSource

# Get SocketIO instance from main
from app.main import sio


@sio.on('start_scan')
async def handle_start_scan(sid, data):
    """Handle scan request (simplified for testing)."""
    scan_id = str(uuid.uuid4())
    user_name = data.get('user_name')

    # Emit scan started
    await sio.emit('scan_started', {
        'scan_id': scan_id,
        'message': 'Scan started. Processing image...'
    }, room=sid)

    # Stage 1: Image processing
    await sio.emit('scan_progress', {
        'scan_id': scan_id,
        'stage': 'image_processing',
        'stage_number': 1,
        'total_stages': 5,
        'message': 'Detecting barcode and reading label...',
        'progress': 0.2
    }, room=sid)
    await asyncio.sleep(1)

    # Stage 2: Nutrition retrieval
    await sio.emit('scan_progress', {
        'scan_id': scan_id,
        'stage': 'nutrition_retrieval',
        'stage_number': 2,
        'total_stages': 5,
        'message': 'Fetching nutrition data...',
        'progress': 0.4
    }, room=sid)
    await asyncio.sleep(1)

    # Stage 3: Profile loading
    await sio.emit('scan_progress', {
        'scan_id': scan_id,
        'stage': 'profile_loading',
        'stage_number': 3,
        'total_stages': 5,
        'message': 'Loading your profile...',
        'progress': 0.6
    }, room=sid)
    await asyncio.sleep(1)

    # Stage 4: Scoring
    await sio.emit('scan_progress', {
        'scan_id': scan_id,
        'stage': 'scoring',
        'stage_number': 4,
        'total_stages': 5,
        'message': 'Analyzing nutrition and generating score...',
        'progress': 0.8
    }, room=sid)
    await asyncio.sleep(1)

    # Stage 5: Assessment generation
    await sio.emit('scan_progress', {
        'scan_id': scan_id,
        'stage': 'assessment_generation',
        'stage_number': 5,
        'total_stages': 5,
        'message': 'Preparing your personalized verdict...',
        'progress': 0.9
    }, room=sid)
    await asyncio.sleep(1)

    # Create mock DetailedAssessment
    assessment = DetailedAssessment(
        scan_id=scan_id,
        timestamp=datetime.utcnow(),
        product_name="Lay's Classic Potato Chips",
        brand="Lay's",
        final_score=6.5,
        verdict="moderate",
        verdict_emoji="🟡",
        base_score=6.0,
        context_adjustment="Normal consumption, within moderation",
        time_multiplier=1.0,
        final_calculation="6.0 × 1.0 × 1.0 = 6.0",
        highlights=[
            "Good source of energy",
            "Convenient snack option"
        ],
        warnings=[
            "High in sodium (350mg per 100g)",
            "Contains saturated fats"
        ],
        allergen_alerts=[],
        moderation_message="You haven't had chips today. This is within your daily limits.",
        timing_recommendation="Best consumed in moderation as an occasional snack",
        reasoning_steps=[
            "Analyzed nutritional content",
            "Compared to your daily targets",
            "Considered time of day (afternoon)",
            "Checked consumption history"
        ],
        confidence=0.85,
        sources=[
            CitationSource(
                citation_number=1,
                source_type="openfoodfacts",
                title="Lay's Classic - OpenFoodFacts",
                url="https://world.openfoodfacts.org/product/...",
                authority_score=0.9,
                snippet="Official product data"
            )
        ],
        inline_citations={},
        alternative_products=[
            "Baked Lay's (lower fat)",
            "Air-popped popcorn"
        ],
        portion_suggestion="Limit to one serving (28g)",
        nutrition_snapshot={
            "calories": 536,
            "protein_g": 7,
            "fat_g": 34,
            "sodium_mg": 350
        }
    )

    # Emit completion
    await sio.emit('scan_complete', {
        'scan_id': scan_id,
        'detailed_assessment': assessment.model_dump(mode='json')
    }, room=sid)
```

**Register in main.py**:

```python
# In app/main.py, replace:
from app.api import auth, scan

# With:
from app.api import auth
from app.api import scan_simple  # Simplified version for testing
```

**Verification**:

```bash
# Start server
python -m uvicorn app.main:socket_app --reload

# Run WebSocket test
python test_websocket.py
```

- [ ] All 5 progress stages emitted
- [ ] Complete event with DetailedAssessment
- [ ] Frontend can parse the response

---

## Phase 7: Health Check Improvements

### ✅ Task 7.1: Enhanced Health Check

**Update**: `backend/app/main.py`

Replace simple health check with comprehensive one:

```python
import httpx

@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    services = {}

    # Check Ollama
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                services['ollama'] = {
                    'status': 'connected',
                    'models': [m['name'] for m in models]
                }
            else:
                services['ollama'] = {'status': 'error', 'error': f'HTTP {resp.status_code}'}
    except Exception as e:
        services['ollama'] = {'status': 'error', 'error': str(e)}

    # Check SearXNG
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://192.168.1.4/search?q=test&format=json", timeout=5.0)
            if resp.status_code == 200:
                services['searxng'] = {'status': 'connected', 'url': 'http://192.168.1.4'}
            else:
                services['searxng'] = {'status': 'error', 'error': f'HTTP {resp.status_code}'}
    except Exception as e:
        services['searxng'] = {'status': 'error', 'error': str(e)}

    # Check storage
    import os
    profiles_dir = settings.profiles_dir
    services['storage'] = {
        'status': 'ok' if os.path.exists(profiles_dir) else 'error',
        'profiles_dir': profiles_dir
    }

    # Overall status
    all_ok = all(s.get('status') == 'connected' or s.get('status') == 'ok' for s in services.values())

    return {
        'status': 'ok' if all_ok else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'services': services
    }
```

**Test**:

```bash
curl http://localhost:8000/health | jq
```

**Expected**:

```json
{
  "status": "ok",
  "timestamp": "2025-01-14T...",
  "services": {
    "ollama": {
      "status": "connected",
      "models": ["qwen3:30b", "qwen3:8b", ...]
    },
    "searxng": {
      "status": "connected",
      "url": "http://192.168.1.4"
    },
    "storage": {
      "status": "ok",
      "profiles_dir": "./data/profiles"
    }
  }
}
```

**Verification**:

- [ ] All services show "connected" or "ok"
- [ ] Frontend can call this endpoint
- [ ] Useful for debugging

---

## Phase 8: Final Testing & Documentation

### ✅ Task 8.1: Create Backend Test Script

**File**: `backend/test_backend.sh`

```bash
#!/bin/bash
set -e

echo "=== Bytelense Backend Test Suite ==="
echo ""

# Activate venv
source venv/bin/activate

echo "[1/5] Checking Python dependencies..."
python -c "import fastapi, socketio, dspy, httpx, aiofiles, cv2, pyzbar; print('✓ All imports OK')"

echo "[2/5] Checking external services..."
curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Ollama accessible" || echo "✗ Ollama NOT accessible"
curl -s "http://192.168.1.4/search?q=test&format=json" > /dev/null && echo "✓ SearXNG accessible" || echo "✗ SearXNG NOT accessible"

echo "[3/5] Checking data directories..."
test -d data/profiles && echo "✓ Profiles directory exists" || echo "✗ Profiles directory missing"
test -d data/scan_history && echo "✓ Scan history directory exists" || echo "✗ Scan history directory missing"

echo "[4/5] Starting server..."
python -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 3

echo "[5/5] Testing endpoints..."
curl -s http://localhost:8000/health > /dev/null && echo "✓ Health check working" || echo "✗ Health check failed"
curl -s http://localhost:8000/api/config > /dev/null && echo "✓ Config endpoint working" || echo "✗ Config endpoint failed"

echo ""
echo "=== Backend is running on http://localhost:8000 ==="
echo "API docs: http://localhost:8000/docs"
echo "Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop server"

# Wait for interrupt
wait $SERVER_PID
```

**Make executable**:

```bash
chmod +x backend/test_backend.sh
```

**Run**:

```bash
./backend/test_backend.sh
```

**Verification**:

- [ ] All checks pass
- [ ] Server starts without errors
- [ ] Endpoints respond

---

### ✅ Task 8.2: Create Quick Start Guide for Backend

**File**: `backend/README_QUICKSTART.md`

```markdown
# Bytelense Backend - Quick Start

## Prerequisites

1. **Ollama running** with models:
   - `qwen3:8b` (development)
   - `qwen3:30b` (production)

2. **SearXNG accessible** at http://192.168.1.4

3. **Python 3.12+** installed

4. **System dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y libzbar0
   ```

## Setup (First Time)

```bash
# 1. Create virtual environment
cd backend
python3.12 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r ../../requirements.txt
pip install uvicorn[standard] pyzbar

# 3. Create .env file
cp .env.example .env
# Edit .env if needed (default values should work)

# 4. Create data directories
mkdir -p data/profiles data/scan_history data/cache

# 5. Test setup
./test_backend.sh
```

## Running the Server

### Development Mode (with auto-reload)

```bash
source venv/bin/activate
python -m uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
source venv/bin/activate
python -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

### Health Check

```bash
curl http://localhost:8000/health | jq
```

### API Documentation

Visit: <http://localhost:8000/docs>

### WebSocket Test

```bash
python test_websocket.py
```

## Troubleshooting

**Server won't start**:

- Check `.env` file exists
- Check data directories exist
- Check port 8000 is available: `lsof -i :8000`

**Ollama connection error**:

- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check model is available: `ollama list`

**SearXNG connection error**:

- Verify SearXNG is accessible: `curl http://192.168.1.4`
- Check network connectivity

## What Frontend Expects

The backend provides:

**REST Endpoints**:

- `GET /health` - Service health status
- `GET /api/config` - Client configuration
- `POST /api/auth/login` - User login
- `GET /api/profile/{name}` - Get user profile
- `PATCH /api/profile/{name}` - Update profile

**WebSocket Events** (on <http://localhost:8000>):

- Client → Server: `start_scan`
- Server → Client: `scan_started`, `scan_progress`, `scan_complete`, `scan_error`

## Development Checklist

- [ ] Backend starts without errors
- [ ] Health check returns "ok"
- [ ] Can create user profile
- [ ] Can retrieve user profile
- [ ] WebSocket connection works
- [ ] Scan flow completes (even if mocked)

```

---

## Final Checklist: Backend Ready for Frontend

### ✅ Core Functionality

- [ ] Server starts without errors
- [ ] `/health` endpoint returns service status
- [ ] `/api/config` endpoint returns configuration
- [ ] User can login (name-based)
- [ ] Profile can be created and retrieved
- [ ] WebSocket connection accepts connections
- [ ] Scan flow emits all required events
- [ ] DetailedAssessment is returned with correct schema

### ✅ External Services

- [ ] Ollama accessible and responding
- [ ] At least one model available (qwen3:8b or qwen3:30b)
- [ ] SearXNG accessible and returning JSON
- [ ] All data directories created with write permissions

### ✅ Development Ready

- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] `.env` file configured
- [ ] Test scripts run successfully
- [ ] Documentation up to date

### ✅ Frontend Integration Ready

- [ ] CORS allows frontend origin
- [ ] WebSocket accepts cross-origin connections
- [ ] All response formats match TypeScript interfaces
- [ ] Error messages are human-readable

---

## Next Steps

Once all checkboxes above are marked:

1. **Tell qwen-coder frontend is ready to test**
2. **Run backend**: `./test_backend.sh`
3. **Point frontend to**: `http://localhost:8000`
4. **Test end-to-end flow**

---

## Common Issues & Solutions

**Issue**: `ModuleNotFoundError: No module named 'app'`
**Solution**: Make sure you're running from `/backend` directory with venv activated

**Issue**: `Address already in use`
**Solution**: Kill existing process: `lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill`

**Issue**: `Cannot connect to Ollama`
**Solution**: Start Ollama service: `systemctl start ollama` or check if running

**Issue**: WebSocket connection fails
**Solution**: Check CORS settings in main.py, ensure `allow_origins=["*"]` for development

---

**Remember**: Test each phase before moving forward. If something doesn't work, fix it immediately.
