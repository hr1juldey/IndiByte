# Bytelense MVP - Product Requirements Document

**Version:** 0.1 (6-Hour Technical MVP)
**Last Updated:** 2025-11-14
**Development Time:** 6 hours max

---

## Executive Summary

### Problem

People struggle to understand food labels and make quick, informed decisions about what they eat while considering their personal health goals.

### Solution (MVP Scope)

A web application that:
- Scans food via camera or uploaded image
- Fetches nutritional data from multiple sources (OpenFoodFacts + SearXNG fallback)
- Uses DSPy-powered structured reasoning for scientific scoring
- Generates personalized verdicts based on user health profile
- Displays dynamic, generative UI tailored to the verdict

### What We ARE Building

- Simple name-based authentication
- User health profile (JSON file storage)
- Camera + image upload scanning
- Barcode detection with OCR fallback
- Multi-source nutritional data (OpenFoodFacts → SearXNG)
- DSPy-based scientific scoring
- Generative UI components
- Real-time updates via WebSocket

### What We're NOT Building (Yet)

- Complex multi-user authentication (OAuth, passwords)
- Cloud database (using local JSON files)
- TTS audio verdicts (too resource intensive)
- Speech-to-text commands
- History tracking across sessions
- Mobile native apps
- Meal planning
- Social features

---

## Target User (MVP)

**Health-Conscious Individual with Specific Goals**
- Has dietary goals (weight loss, muscle gain, diabetes management, etc.)
- Wants personalized, scientific guidance
- Comfortable with web apps
- Values transparency in scoring logic

---

## Core User Flow (MVP)

### Flow 1: First-Time Setup

1. **Landing Page**
   - "Welcome to Bytelense"
   - Simple form: "What's your name?"
   - Button: "Get Started"

2. **Health Profile Onboarding**
   - **Basic Info:**
     - Name (already entered)
     - Age, gender (optional)
     - Height, weight

   - **Health Goals (select one or more):**
     - Weight loss
     - Weight gain
     - Muscle building
     - Diabetes management
     - Heart health
     - General wellness

   - **Dietary Restrictions (multi-select):**
     - Allergies (nuts, dairy, gluten, shellfish, eggs, soy)
     - Dietary preferences (vegetarian, vegan, keto, low-carb)

   - **Nutritional Focus (rank top 3):**
     - Calories
     - Sugar
     - Sodium
     - Protein
     - Carbs
     - Fat
     - Fiber

3. **Profile Saved**
   - "Profile created! Ready to scan your first food."
   - Profile saved to `data/profiles/{name}.json`

### Flow 2: Scanning Food

1. **Scan Screen**
   - Two options prominently displayed:
     - "📷 Use Camera" (opens device camera)
     - "📁 Upload Image" (file picker)
   - Recent scans widget (if any)

2. **Camera/Upload**
   - **Camera:** Live camera feed in browser, capture button
   - **Upload:** Drag-drop or click to select image
   - Image preview shown after capture/upload

3. **Processing (WebSocket updates)**
   - "Detecting barcode..." (pyzbar)
   - If barcode found: "Looking up nutrition data..."
   - If no barcode: "Reading label text..." (Chandra OCR)
   - "Analyzing against your health profile..." (DSPy)
   - "Generating verdict..." (Generative UI)

4. **Results - Generative UI**
   - Dynamic layout based on verdict severity:
     - **Green (Good):** Encouraging layout with checkmarks
     - **Yellow (Moderate):** Balanced layout with warnings
     - **Red (Avoid):** Alert-style layout with strong warnings

   - **Components (assembled dynamically):**
     - Verdict badge (color-coded)
     - Score display (e.g., "7.5/10")
     - Product name and image
     - Key insights (3-5 bullet points)
     - Nutritional breakdown (macros)
     - Personalized warnings:
       - "⚠️ High sugar (30g) - exceeds your diabetes management goal"
       - "✓ Good protein (18g) - supports muscle building"
     - Scientific reasoning (from DSPy): "Why this score?"

   - **Actions:**
     - "Scan Another" button
     - "View Detailed Breakdown" (expandable)

### Flow 3: Returning User

1. **Landing Page**
   - "Welcome back, {Name}!"
   - Quick access to scan
   - Option to edit profile

---

## Functional Requirements (MVP)

### F1: Authentication (Simple)

- **Name-based login:**
  - User enters name
  - System checks if `data/profiles/{name}.json` exists
  - If exists: Load profile
  - If not: Trigger onboarding

### F2: User Profile Management

- **Profile Storage:**
  - JSON file per user: `data/profiles/{name}.json`
  - Schema:
    ```json
    {
      "name": "John",
      "created_at": "2025-11-14T10:00:00Z",
      "age": 35,
      "gender": "male",
      "height_cm": 175,
      "weight_kg": 80,
      "goals": ["weight_loss", "heart_health"],
      "allergies": ["dairy", "nuts"],
      "dietary_preferences": ["vegetarian"],
      "nutritional_focus": ["sugar", "calories", "sodium"],
      "daily_targets": {
        "calories": 2000,
        "sugar_g": 25,
        "sodium_mg": 2300,
        "protein_g": 80,
        "carbs_g": 250,
        "fat_g": 65,
        "fiber_g": 30
      }
    }
    ```

- **Profile CRUD:**
  - Create during onboarding
  - Read on login
  - Update via settings (basic form)
  - No delete (out of scope)

### F3: Food Scanning

#### F3.1: Image Acquisition

- **Camera Capture:**
  - Use browser MediaDevices API
  - Display live preview
  - Capture button creates image blob
  - Send to backend via WebSocket

- **Image Upload:**
  - File input accepts JPG, PNG
  - Max size: 10MB
  - Preview before upload
  - Send to backend via WebSocket

#### F3.2: Barcode Detection (Primary)

- **Library:** pyzbar (already working well)
- **Process:**
  - Detect all barcodes in image
  - Use first valid barcode
  - Support UPC, EAN, QR codes
  - Extract barcode number

#### F3.3: OCR Fallback

- **Library:** Chandra OCR (from requirements.txt)
- **Trigger:** If pyzbar finds no barcode
- **Process:**
  - Extract text from label
  - Look for product name, brand
  - Use for search query

### F4: Nutritional Data Retrieval

#### F4.1: OpenFoodFacts API (Primary)

- **Barcode Lookup:**
  - Endpoint: `GET https://world.openfoodfacts.org/api/v2/product/{barcode}.json`
  - Parse response for nutrition facts
  - Extract: name, brand, serving size, calories, macros, ingredients

- **Text Search (if barcode fails):**
  - Endpoint: `GET https://world.openfoodfacts.org/cgi/search.pl?search_terms={query}&json=1`
  - Use top result

#### F4.2: SearXNG Fallback (via FastMCP)

- **Trigger:** If OpenFoodFacts returns no data or incomplete data
- **Process:**
  - Query SearXNG for "{product_name} nutrition facts"
  - Use FastMCP tools for SearXNG integration
  - Parse structured data from results
  - Fallback to LLM extraction if needed

### F5: Scientific Scoring Engine (DSPy)

#### F5.1: DSPy Module Setup

```python
class NutritionScorer(dspy.Module):
    def __init__(self):
        self.score = dspy.ChainOfThought("nutrition_data, user_profile -> score, reasoning, warnings")

    def forward(self, nutrition_data, user_profile):
        result = self.score(
            nutrition_data=nutrition_data,
            user_profile=user_profile
        )
        return {
            "score": result.score,  # 0-10
            "verdict": self.get_verdict(result.score),
            "reasoning": result.reasoning,
            "warnings": result.warnings,
            "highlights": self.extract_highlights(result)
        }
```

#### F5.2: Scoring Factors (DSPy-guided)

DSPy will reason through:
1. **Goal Alignment:**
   - Compare nutritional profile to user goals
   - Penalize misalignments (e.g., high sugar for diabetes)
   - Reward alignments (e.g., high protein for muscle building)

2. **Allergen Detection:**
   - Auto score 0 if contains allergen
   - Flag prominently in warnings

3. **Nutritional Density:**
   - Evaluate nutrient-to-calorie ratio
   - Consider micronutrients if available

4. **Processing Level:**
   - Identify additives, preservatives
   - Consider ingredient list length

5. **Portion Appropriateness:**
   - Evaluate serving size reasonableness
   - Check against daily targets

#### F5.3: Output Format

```python
{
    "score": 7.5,
    "verdict": "good",  # good, moderate, avoid
    "reasoning": "This product aligns well with your weight loss goal due to low calorie density (150 cal/serving). However, sodium is moderately high at 600mg, which is 26% of your daily target. The 12g of protein supports satiety.",
    "warnings": [
        "Moderate sodium - watch portions if managing heart health"
    ],
    "highlights": [
        "✓ Low calorie (150 cal) - good for weight loss",
        "✓ High protein (12g) - supports muscle retention",
        "⚠ Moderate sodium (600mg)",
        "✓ Good fiber (5g)"
    ]
}
```

### F6: Generative UI

#### F6.1: UI Schema Definition

Backend returns structured UI schema based on verdict:

```python
{
    "layout": "alert",  # alert, balanced, encouraging
    "theme": "red",  # red, yellow, green
    "components": [
        {
            "type": "verdict_badge",
            "props": {"text": "Avoid", "color": "red", "icon": "warning"}
        },
        {
            "type": "score_display",
            "props": {"score": 3.5, "max": 10}
        },
        {
            "type": "insight_list",
            "props": {
                "items": [
                    {"text": "Contains dairy", "type": "danger", "icon": "allergen"},
                    {"text": "High sugar (35g)", "type": "warning", "icon": "alert"}
                ]
            }
        },
        {
            "type": "nutrition_card",
            "props": {
                "calories": 280,
                "protein": 8,
                "carbs": 45,
                "fat": 9,
                "sugar": 35,
                "sodium": 450
            }
        },
        {
            "type": "reasoning_section",
            "props": {
                "title": "Why this score?",
                "content": "DSPy-generated reasoning here..."
            }
        }
    ]
}
```

#### F6.2: Frontend Component Rendering

- React components map to schema types
- Props passed directly from backend
- Fallback component for unknown types
- Smooth transitions between layouts

### F7: Real-Time Communication

- **WebSocket Setup:**
  - Client connects on scan initiation
  - Server sends progress updates:
    - `{"status": "detecting_barcode"}`
    - `{"status": "fetching_nutrition"}`
    - `{"status": "analyzing", "progress": 50}`
    - `{"status": "complete", "data": {...}}`
  - Connection closes after result

---

## Non-Functional Requirements (MVP)

### Performance

- Camera activation: < 1 second
- Barcode detection: < 2 seconds
- Nutrition lookup (OpenFoodFacts): < 3 seconds
- DSPy scoring: < 5 seconds
- Total scan-to-verdict: < 10 seconds
- Frontend load: < 2 seconds

### Reliability

- Graceful degradation:
  - Barcode fails → OCR
  - OpenFoodFacts fails → SearXNG
  - SearXNG fails → Manual entry prompt
- Error messages with recovery suggestions

### Usability

- Mobile-responsive (primary target)
- Tablet and desktop support
- Clear visual feedback at each step
- Accessible (basic WCAG AA)

---

## Technical Architecture (MVP)

### Backend

**Stack:** FastAPI + Python 3.12 + FastMCP + DSPy

**Structure:**

```
backend/app/
  ├── main.py                 # FastAPI app + WebSocket setup
  ├── api/
  │   ├── auth.py             # Simple name-based auth
  │   ├── profile.py          # Profile CRUD (JSON files)
  │   └── scan.py             # Scan WebSocket endpoint
  ├── services/
  │   ├── image_processing.py # Barcode (pyzbar) + OCR (Chandra)
  │   ├── nutrition_api.py    # OpenFoodFacts client
  │   ├── searxng_client.py   # SearXNG via FastMCP
  │   ├── scoring.py          # DSPy scoring module
  │   └── ui_generator.py     # Generative UI schema builder
  ├── models/
  │   ├── schemas.py          # Pydantic models
  │   └── dspy_modules.py     # DSPy modules
  ├── core/
  │   ├── config.py           # Settings, env vars
  │   └── profile_store.py    # JSON file I/O
  └── data/
      └── profiles/           # {name}.json files
```

**Key Dependencies (from requirements.txt):**

- fastapi - Web framework
- fastmcp - MCP tool integration
- dspy-ai - Structured LLM reasoning
- python-socketio / websockets - Real-time communication
- httpx - Async HTTP client
- chandra-ocr - OCR
- Pillow, opencv-python-headless - Image processing
- pydantic - Data validation
- python-dotenv - Environment management
- aiofiles - Async file I/O

**Environment Variables:**

```
OPENAI_API_KEY=sk-...          # For DSPy LLM calls
SEARXNG_URL=http://localhost:8080  # SearXNG instance
PROFILES_DIR=./data/profiles
```

### Frontend

**Stack:** React + Vite + Tailwind CSS + shadcn/ui

**Structure:**

```
frontend/src/
  ├── App.jsx                 # Main app, routing
  ├── components/
  │   ├── auth/
  │   │   ├── LoginForm.jsx
  │   │   └── OnboardingWizard.jsx
  │   ├── scan/
  │   │   ├── CameraCapture.jsx
  │   │   ├── ImageUpload.jsx
  │   │   └── ScanButton.jsx
  │   ├── verdict/
  │   │   ├── VerdictBadge.jsx
  │   │   ├── ScoreDisplay.jsx
  │   │   ├── InsightList.jsx
  │   │   ├── NutritionCard.jsx
  │   │   └── ReasoningSection.jsx
  │   ├── profile/
  │   │   └── ProfileEditor.jsx
  │   └── ui/                 # shadcn components
  ├── lib/
  │   ├── api.js              # HTTP client
  │   ├── websocket.js        # WebSocket client
  │   └── componentRegistry.js # Map schema to components
  ├── hooks/
  │   ├── useCamera.js
  │   ├── useWebSocket.js
  │   └── useProfile.js
  └── styles/
      └── index.css           # Tailwind + custom styles
```

**Key Features:**

- Camera access via `navigator.mediaDevices.getUserMedia()`
- WebSocket for real-time updates
- Component registry for generative UI
- shadcn/ui for polished components
- Responsive design (mobile-first)

### External Services

1. **OpenFoodFacts API**
   - Public, free, no auth
   - Product database lookup

2. **SearXNG (via FastMCP)**
   - Self-hosted or public instance
   - Nutritional data search fallback

3. **OpenAI API (for DSPy)**
   - GPT-4 for structured reasoning
   - Can swap for local model later

### Data Storage

**Local JSON Files (No Database):**

```
data/
  └── profiles/
      ├── john.json
      ├── sarah.json
      └── mike.json
```

**Why JSON files?**
- Simple for MVP
- No DB setup overhead
- Easy to inspect/debug
- Sufficient for single-user demo
- Can migrate to SQLite/Postgres later

### Deployment (Local Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Access:** http://localhost:5173

---

## Edge Cases (MVP)

### EC1: Barcode Not Detected

- Try OCR fallback
- If OCR fails: "Can't read label. Try better lighting or different angle."

### EC2: Product Not in OpenFoodFacts

- Fallback to SearXNG search
- If SearXNG fails: "Product not found. Enter manually?" (future feature)

### EC3: SearXNG Returns Incomplete Data

- Use DSPy to estimate missing values based on similar products
- Add confidence score to verdict

### EC4: User Profile Not Found

- Redirect to onboarding
- Create new profile

### EC5: Multiple Barcodes

- Use first detected
- Log for debugging

### EC6: Allergen Detected

- Override score to 0
- Display prominent warning banner
- Require explicit confirmation to proceed

---

## 6-Hour Development Plan

### Hour 1: Backend Setup + Auth + Profiles

- Initialize FastAPI project
- Implement name-based auth endpoint
- Create profile JSON file I/O (CRUD)
- Onboarding data model (Pydantic)
- Test: Create/load profile

### Hour 2: Image Processing + Data Retrieval

- WebSocket endpoint for scan
- Barcode detection (pyzbar)
- OCR fallback (Chandra)
- OpenFoodFacts API client
- SearXNG client via FastMCP (basic)
- Test: Upload image → get nutrition data

### Hour 3: DSPy Scoring Engine

- Define DSPy module for scoring
- Implement scoring logic with user profile
- Generate highlights and warnings
- Test: Nutrition data + profile → verdict

### Hour 4: Generative UI + Backend Integration

- UI schema generator based on verdict
- Complete WebSocket flow with progress updates
- Test end-to-end backend pipeline

### Hour 5: Frontend - Auth + Scanning

- React app setup (Vite + Tailwind)
- Login form + onboarding wizard
- Camera capture component
- Image upload component
- WebSocket client
- Test: Login → scan → connect to backend

### Hour 6: Frontend - Verdict Display + Polish

- Component registry for generative UI
- Verdict components (badge, score, insights, etc.)
- Wire up WebSocket responses to UI
- Error handling and loading states
- Mobile responsiveness
- End-to-end testing

---

## Success Criteria (MVP)

### Must Have

✅ User can enter name and create health profile
✅ Profile persists across sessions (JSON file)
✅ User can capture image via camera OR upload image
✅ System detects barcode via pyzbar
✅ System extracts text via Chandra OCR (if no barcode)
✅ System fetches nutrition from OpenFoodFacts
✅ System falls back to SearXNG if needed
✅ DSPy generates scientific, personalized verdict
✅ Backend sends UI schema for generative display
✅ Frontend renders dynamic UI based on schema
✅ Real-time progress updates via WebSocket
✅ Mobile-responsive interface

### Nice to Have (If Time Permits)

- Better error recovery
- Loading animations
- Profile editing after creation
- Detailed nutritional breakdown (expandable)
- Recent scans widget

### Don't Need

- Multi-user accounts with passwords
- Database (PostgreSQL/MongoDB)
- TTS audio
- Speech-to-text
- History across sessions
- Cloud storage
- Analytics
- Social features

---

## Technical Decisions (Final)

### Backend

- **Framework:** FastAPI (async, WebSocket support)
- **LLM Reasoning:** DSPy with GPT-4 (swap to local later)
- **OCR:** Chandra OCR (from requirements)
- **Barcode:** pyzbar (simple, reliable)
- **MCP:** FastMCP for SearXNG tools
- **Storage:** JSON files (local filesystem)
- **Real-time:** python-socketio or native WebSockets

### Frontend

- **Framework:** React + Vite
- **UI Library:** shadcn/ui + Tailwind CSS
- **State:** useState/useContext (no Redux)
- **Camera:** MediaDevices API
- **Real-time:** WebSocket client

### APIs

- **Primary:** OpenFoodFacts (free, public)
- **Fallback:** SearXNG via FastMCP
- **LLM:** OpenAI GPT-4 (via DSPy)

### What Makes This Feasible in 6 Hours

1. **No complex auth:** Just name entry
2. **No database setup:** JSON files are instant
3. **Existing libraries:** All heavy lifting done by dependencies
4. **Clear scope:** One core flow (scan → verdict)
5. **DSPy handles complexity:** No manual prompt engineering
6. **Generative UI is simple:** Just JSON schema → components

---

## Risk Mitigation

### High Risk: DSPy Setup Time

- **Mitigation:** Start with simple DSPy module, iterate
- **Fallback:** Hard-coded scoring rules if DSPy takes too long

### Medium Risk: SearXNG Integration

- **Mitigation:** Use FastMCP examples, keep query simple
- **Fallback:** Skip SearXNG, rely on OpenFoodFacts only

### Medium Risk: Camera API

- **Mitigation:** Test on target device early
- **Fallback:** Upload-only if camera fails

### Low Risk: JSON File I/O

- **Mitigation:** Use aiofiles for async, simple error handling

---

## Post-MVP Roadmap

### Version 0.2 (Next 6-12 hours)

- History tracking (JSON log file per user)
- Recent scans display
- Manual product entry
- Better error messages
- Offline barcode cache

### Version 0.3 (Another 12 hours)

- SQLite database migration
- User authentication (simple passwords)
- Multi-device sync (cloud storage)
- Export scan history (CSV/PDF)
- Improved UI/UX

### Version 1.0 (Full Vision - Original PRD)

- TTS audio verdicts (IndexTTS2)
- Speech-to-text (Whisper)
- Raw food recognition (computer vision)
- Alternative product suggestions
- Meal planning
- Social features
- Mobile native apps
- Advanced analytics

---

## Conclusion

This MVP strikes a balance between **technical sophistication** and **rapid development**:

**Sophisticated:**
- DSPy for scientific, explainable scoring
- Generative UI for dynamic UX
- Multi-source data with intelligent fallbacks
- Personalized to user health goals

**Rapid:**
- No complex authentication
- No database setup
- No resource-heavy TTS/STT
- Clear, focused scope
- Leverages existing dependencies

The goal is a **functional, impressive demo** in 6 hours that showcases the core innovation: AI-powered, personalized food analysis with real-time feedback.

**Next Step:** Begin Hour 1 - Backend setup, auth, and profile management.
