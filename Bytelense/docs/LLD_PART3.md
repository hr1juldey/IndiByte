# Bytelense Low-Level Design - Part 3

**Sections 9-14: Assessment Generation, API Contracts, Async Flows, Decoupling, Concurrency, Function Specifications**

---

## Section 9: Assessment Generation System

### 9.1 Overview

The Assessment Generation System transforms the raw scoring output from the Context-Aware Scoring Engine into two presentation formats:

1. **DetailedAssessment**: Comprehensive analysis with full reasoning, citations, and recommendations (for main verdict screen)
2. **ShortAssessment**: Condensed summary for quick consumption (for notifications, history view, voice TTS)

**Key Design Principle**: The detailed assessment is the source of truth. Short assessment is always derived from the detailed version using DSPy-based summarization.

### 9.2 Data Models

#### 9.2.1 DetailedAssessment

```python
class DetailedAssessment(BaseModel):
    """Complete assessment with full reasoning and citations."""

    # Core verdict
    scan_id: str  # UUID
    timestamp: datetime
    product_name: str
    brand: Optional[str]

    # Scoring
    final_score: float  # 0-10
    verdict: Literal["excellent", "good", "moderate", "caution", "avoid"]
    verdict_emoji: str  # 🟢 🟡 🔴

    # Reasoning
    base_score: float
    context_adjustment: str  # Human-readable explanation
    time_multiplier: float
    final_calculation: str  # e.g., "6.0 × 1.2 × 0.8 = 5.76"

    # Detailed insights
    highlights: List[str]  # Positive points (e.g., "High in fiber")
    warnings: List[str]  # Concerns (e.g., "High sodium for your BP")
    allergen_alerts: List[str]  # Critical alerts

    # Context-aware messaging
    moderation_message: str  # e.g., "You've had 25g sugar today (83% of limit)"
    timing_recommendation: str  # e.g., "Better suited for morning consumption"

    # AI reasoning
    reasoning_steps: List[str]  # Step-by-step thought process
    confidence: float  # 0-1

    # Citations (Perplexity-style)
    sources: List[CitationSource]
    inline_citations: Dict[str, int]  # text_snippet -> citation_number

    # Recommendations
    alternative_products: List[str]  # Healthier alternatives
    portion_suggestion: Optional[str]  # e.g., "Limit to 1 serving (25g)"

    # Nutrition summary
    nutrition_snapshot: Dict[str, Any]  # Key metrics for display
```

#### 9.2.2 ShortAssessment

```python
class ShortAssessment(BaseModel):
    """Condensed assessment for quick consumption."""

    scan_id: str
    timestamp: datetime
    product_name: str

    # Core verdict
    final_score: float
    verdict: Literal["excellent", "good", "moderate", "caution", "avoid"]
    verdict_emoji: str

    # One-sentence summary
    summary: str  # e.g., "Good choice for breakfast, but watch sodium intake"

    # Top 3 insights (max)
    key_points: List[str]  # Max 3 items

    # Critical alerts only
    allergen_alerts: List[str]

    # Single recommendation
    main_recommendation: Optional[str]
```

#### 9.2.3 CitationSource

```python
class CitationSource(BaseModel):
    """Individual source citation."""

    citation_number: int  # [1], [2], etc.
    source_type: Literal["openfoodfacts", "searxng_web", "health_guideline", "user_profile"]
    title: str
    url: Optional[str]  # For web sources
    authority_score: float  # 0-1 (WHO=1.0, random blog=0.3)
    snippet: Optional[str]  # Relevant excerpt
    accessed_at: datetime
```

### 9.3 DSPy Modules

#### 9.3.1 DetailedAssessmentBuilder (Rule-Based)

**Purpose**: Assemble DetailedAssessment from scoring engine output. No LLM needed here - pure data aggregation.

**Class Definition**:
```python
class DetailedAssessmentBuilder:
    """Builds detailed assessment from scoring output (rule-based)."""

    def __init__(self):
        pass

    async def build(
        self,
        scan_id: str,
        nutrition_data: NutritionData,
        scoring_result: Dict[str, Any],  # From DSPy scoring module
        consumption_context: Dict[str, Any],
        sources: List[CitationSource]
    ) -> DetailedAssessment:
        """Assemble detailed assessment."""
        # Pure data transformation - no LLM calls
```

**Logic Steps**:
1. Extract core fields from `scoring_result`
2. Map score to verdict category:
   - 8.0-10.0 → "excellent" 🟢
   - 6.0-7.9 → "good" 🟢
   - 4.0-5.9 → "moderate" 🟡
   - 2.0-3.9 → "caution" 🟡
   - 0.0-1.9 → "avoid" 🔴
3. Format calculation string from base_score, multipliers
4. Build moderation_message from consumption_context
5. Assign sources to inline_citations based on text mentions
6. Return complete DetailedAssessment

**No LLM Required**: This is pure data assembly. All reasoning already done by scoring engine.

#### 9.3.2 AssessmentSummarizer (DSPy-Based)

**Purpose**: Generate ShortAssessment from DetailedAssessment using LLM-based summarization.

**DSPy Signature**:
```python
class SummarizeAssessment(dspy.Signature):
    """Condense detailed assessment into short form for quick consumption."""

    # Input: The full detailed assessment as JSON string
    detailed_assessment: str = dspy.InputField(
        desc="Complete assessment with reasoning, insights, and warnings"
    )

    # Constraint: Character limits
    max_summary_chars: int = dspy.InputField(
        desc="Maximum characters for summary (typically 150)"
    )
    max_key_points: int = dspy.InputField(
        desc="Maximum number of key points (typically 3)"
    )

    # Output: Condensed version
    summary: str = dspy.OutputField(
        desc="One-sentence summary capturing verdict and main insight"
    )
    key_points: List[str] = dspy.OutputField(
        desc="Top insights/warnings, ordered by importance"
    )
    main_recommendation: Optional[str] = dspy.OutputField(
        desc="Single actionable recommendation (if applicable)"
    )
```

**DSPy Module**:
```python
class AssessmentSummarizer(dspy.Module):
    """Summarize detailed assessment using DSPy ChainOfThought."""

    def __init__(self, model: str = "qwen3:8b"):
        super().__init__()
        self.model = dspy.OllamaLocal(model=model, base_url="http://localhost:11434")
        dspy.configure(lm=self.model)

        # Use ChainOfThought for better summarization
        self.summarizer = dspy.ChainOfThought(SummarizeAssessment)

    async def forward(
        self,
        detailed: DetailedAssessment,
        max_summary_chars: int = 150,
        max_key_points: int = 3
    ) -> ShortAssessment:
        """Generate short assessment."""

        # Convert detailed assessment to JSON string
        detailed_json = detailed.model_dump_json(indent=2)

        # Run DSPy prediction
        result = self.summarizer(
            detailed_assessment=detailed_json,
            max_summary_chars=max_summary_chars,
            max_key_points=max_key_points
        )

        # Build short assessment
        return ShortAssessment(
            scan_id=detailed.scan_id,
            timestamp=detailed.timestamp,
            product_name=detailed.product_name,
            final_score=detailed.final_score,
            verdict=detailed.verdict,
            verdict_emoji=detailed.verdict_emoji,
            summary=result.summary,
            key_points=result.key_points[:max_key_points],
            allergen_alerts=detailed.allergen_alerts,
            main_recommendation=result.main_recommendation
        )
```

**Performance**:
- Model: qwen3:8b (fast summarization, 4.9 GB)
- Expected latency: <2s
- Can run in parallel with UI generation

### 9.4 UI Assembly Instructions

The DetailedAssessment contains all data needed for frontend rendering. The backend DOES NOT generate UI schemas in this version - frontend reads DetailedAssessment and renders appropriate components.

#### 9.4.1 Frontend Rendering Strategy

**Component Mapping** (for frontend implementation):

```typescript
// Frontend pseudocode (not in backend)
function renderAssessment(assessment: DetailedAssessment) {
  return (
    <VerdictScreen>
      {/* Header */}
      <VerdictBadge
        score={assessment.final_score}
        verdict={assessment.verdict}
        emoji={assessment.verdict_emoji}
      />

      {/* Allergen alerts (if any) - CRITICAL */}
      {assessment.allergen_alerts.length > 0 && (
        <AllergenAlert alerts={assessment.allergen_alerts} />
      )}

      {/* Moderation context */}
      {assessment.moderation_message && (
        <ModerationBanner message={assessment.moderation_message} />
      )}

      {/* Key insights */}
      <InsightSection
        highlights={assessment.highlights}
        warnings={assessment.warnings}
      />

      {/* Nutrition snapshot */}
      <NutritionCard data={assessment.nutrition_snapshot} />

      {/* AI reasoning (expandable) */}
      <ReasoningSection
        steps={assessment.reasoning_steps}
        confidence={assessment.confidence}
      />

      {/* Citations (Perplexity-style) */}
      <CitationList sources={assessment.sources} />

      {/* Recommendations */}
      <RecommendationSection
        alternatives={assessment.alternative_products}
        portion={assessment.portion_suggestion}
        timing={assessment.timing_recommendation}
      />
    </VerdictScreen>
  )
}
```

**Backend Responsibility**: Return complete DetailedAssessment JSON via WebSocket
**Frontend Responsibility**: Render components based on assessment data

### 9.5 Flow Integration

```
Context-Aware Scoring Engine
    ↓ (scoring_result + sources)
DetailedAssessmentBuilder.build()
    ↓ (DetailedAssessment)
    ├─→ AssessmentSummarizer.forward() → ShortAssessment
    └─→ WebSocket emit("scan_complete", detailed_assessment)
            ↓
        Frontend renders UI
```

**Parallel Execution**:
- ShortAssessment generation can run in background
- Emit DetailedAssessment immediately for UI rendering
- Emit ShortAssessment separately for history/notifications

---

## Section 10: API Contracts

### 10.1 REST API Endpoints

#### 10.1.1 Health Check

**Endpoint**: `GET /health`

**Purpose**: Verify server is running and all services are accessible.

**Request**: None

**Response**:
```json
{
  "status": "ok",
  "timestamp": "2025-01-14T10:30:00Z",
  "services": {
    "ollama": {
      "status": "connected",
      "model": "qwen3:30b",
      "available_models": ["qwen3:30b", "qwen3:8b", "deepseek-r1:8b"]
    },
    "searxng": {
      "status": "connected",
      "url": "http://192.168.1.4",
      "format": "json"
    },
    "openfoodfacts": {
      "status": "connected"
    },
    "storage": {
      "status": "ok",
      "profiles_dir": "./data/profiles"
    }
  }
}
```

**Error Response** (503):
```json
{
  "status": "degraded",
  "timestamp": "2025-01-14T10:30:00Z",
  "services": {
    "ollama": {
      "status": "error",
      "error": "Connection refused"
    },
    // ... other services
  }
}
```

#### 10.1.2 Authentication

**Endpoint**: `POST /api/auth/login`

**Purpose**: Simple name-based login (MVP - no password).

**Request**:
```json
{
  "name": "john_doe"
}
```

**Response** (200):
```json
{
  "status": "success",
  "user_exists": true,
  "profile": {
    "name": "john_doe",
    "created_at": "2025-01-01T00:00:00Z",
    "last_updated": "2025-01-14T10:30:00Z",
    "is_onboarded": true
  }
}
```

**Response** (404 - new user):
```json
{
  "status": "new_user",
  "user_exists": false,
  "message": "User not found. Please complete onboarding.",
  "redirect_to": "/onboarding"
}
```

#### 10.1.3 Profile Retrieval

**Endpoint**: `GET /api/profile/{name}`

**Purpose**: Retrieve user profile with computed health metrics.

**Request**: Path parameter `name`

**Response** (200):
```json
{
  "status": "success",
  "profile": {
    // EnhancedUserProfile structure
    "name": "john_doe",
    "demographics": {
      "age": 28,
      "gender": "male",
      "height_cm": 175,
      "weight_kg": 72
    },
    "lifestyle_habits": {
      "sleep_hours": 7,
      "work_style": "desk_job",
      // ... full LifestyleHabits
    },
    "health_metrics": {
      "bmi": 23.5,
      "bmi_category": "normal",
      "bmr": 1680.5,
      "tdee": 2310.7,
      "daily_energy_target": 2000.0,
      "health_risks": []
    },
    "goals": {
      "primary_goal": "maintain_weight",
      "target_weight_kg": 72,
      "timeline_weeks": null
    },
    "food_preferences": {
      "cuisine_preferences": ["indian", "italian"],
      "dietary_restrictions": [],
      "allergens": ["peanuts"],
      "disliked_ingredients": ["mushrooms"]
    },
    "daily_targets": {
      "calories": 2000.0,
      "protein_g": 72.0,
      "carbs_g": 250.0,
      "fat_g": 67.0,
      "fiber_g": 30.0,
      "sugar_g": 50.0,
      "sodium_mg": 2300.0
    }
  }
}
```

**Error Response** (404):
```json
{
  "status": "error",
  "error": "profile_not_found",
  "message": "No profile found for user 'john_doe'"
}
```

#### 10.1.4 Profile Update

**Endpoint**: `PATCH /api/profile/{name}`

**Purpose**: Partial update of user profile (after onboarding, for preference changes).

**Request**:
```json
{
  "weight_kg": 71.5,
  "lifestyle_habits": {
    "exercise_frequency": "5_times_week"
  }
}
```

**Response** (200):
```json
{
  "status": "success",
  "message": "Profile updated successfully",
  "updated_fields": ["weight_kg", "lifestyle_habits.exercise_frequency"],
  "profile": {
    // Updated EnhancedUserProfile
  }
}
```

**Error Response** (422):
```json
{
  "status": "error",
  "error": "validation_error",
  "details": [
    {
      "field": "weight_kg",
      "message": "Weight must be between 20 and 300 kg"
    }
  ]
}
```

#### 10.1.5 Scan History

**Endpoint**: `GET /api/history/{name}`

**Purpose**: Retrieve scan history for a user.

**Query Parameters**:
- `date` (optional): ISO date string (YYYY-MM-DD), defaults to today
- `range` (optional): "day" | "week" | "month", defaults to "day"

**Request**: `GET /api/history/john_doe?date=2025-01-14&range=day`

**Response** (200):
```json
{
  "status": "success",
  "user_name": "john_doe",
  "date": "2025-01-14",
  "range": "day",
  "summary": {
    // DailySummary or WeeklySummary structure
    "date": "2025-01-14",
    "scans": [
      {
        "scan_id": "uuid-123",
        "timestamp": "2025-01-14T08:30:00Z",
        "product_name": "Oats",
        "verdict": "excellent",
        "score": 8.5
      },
      // ... more scans
    ],
    "totals": {
      "calories": 1450.0,
      "protein_g": 65.0,
      // ... all nutrients
    },
    "vs_targets": {
      "calories": 0.725,  // 72.5% of daily target
      "protein_g": 0.903,
      // ...
    }
  }
}
```

### 10.2 WebSocket Events

All WebSocket communication uses Socket.IO protocol.

#### 10.2.1 Connection

**Event**: `connect`

**Client → Server**: Establish connection

**Server → Client**: Acknowledge connection
```json
{
  "event": "connected",
  "data": {
    "message": "Connected to Bytelense server",
    "server_time": "2025-01-14T10:30:00Z"
  }
}
```

#### 10.2.2 Onboarding Flow

**Event 1**: `start_onboarding`

**Client → Server**:
```json
{
  "user_name": "john_doe"
}
```

**Server → Client**: First question
```json
{
  "event": "onboarding_question",
  "data": {
    "question_number": 1,
    "total_questions": 15,  // Approximate
    "category": "icebreaker",
    "question": "Hi John! I'm here to help you make healthier food choices. To get started, could you tell me a bit about yourself? What brings you here today?",
    "response_type": "text",  // or "choice", "number"
    "choices": null,  // For "choice" type
    "validation": {
      "min_chars": 10,
      "max_chars": 500
    },
    "can_skip": true,
    "progress": 0.067  // 1/15
  }
}
```

**Event 2**: `onboarding_response`

**Client → Server**:
```json
{
  "question_number": 1,
  "response": "I want to lose some weight and eat healthier"
}
```

**Server → Client**: Next question (same format as above)

**Special Event**: `skip_question`

**Client → Server**:
```json
{
  "question_number": 3
}
```

**Server → Client**: Next question (skipping current)

**Final Event**: `onboarding_complete`

**Server → Client**:
```json
{
  "event": "onboarding_complete",
  "data": {
    "message": "Onboarding complete! Your profile has been created.",
    "profile": {
      // Complete EnhancedUserProfile
    },
    "redirect_to": "/scan"
  }
}
```

**Error Event**: `onboarding_error`

**Server → Client**:
```json
{
  "event": "onboarding_error",
  "data": {
    "error": "extraction_failed",
    "message": "Could not understand your response. Please try again.",
    "question_number": 5,
    "retry": true
  }
}
```

#### 10.2.3 Scanning Flow

**Event 1**: `start_scan`

**Client → Server**:
```json
{
  "user_name": "john_doe",
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "source": "camera"  // or "upload"
}
```

**Server → Client**: Acknowledge
```json
{
  "event": "scan_started",
  "data": {
    "scan_id": "uuid-123",
    "message": "Scan started. Processing image..."
  }
}
```

**Event 2**: `scan_progress` (emitted multiple times)

**Server → Client**:
```json
{
  "event": "scan_progress",
  "data": {
    "scan_id": "uuid-123",
    "stage": "image_processing",  // or "nutrition_retrieval", "scoring", etc.
    "stage_number": 1,
    "total_stages": 5,
    "message": "Detecting barcode and reading label...",
    "progress": 0.2  // 0.0 to 1.0
  }
}
```

**Stage Values**:
1. `image_processing`: Barcode detection + OCR
2. `nutrition_retrieval`: OpenFoodFacts + SearXNG Intern
3. `profile_loading`: Load user profile and history
4. `scoring`: Context-aware scoring with DSPy
5. `assessment_generation`: Build detailed assessment

**Event 3**: `scan_complete`

**Server → Client**:
```json
{
  "event": "scan_complete",
  "data": {
    "scan_id": "uuid-123",
    "detailed_assessment": {
      // Complete DetailedAssessment structure
    },
    "short_assessment": {
      // Complete ShortAssessment structure
    }
  }
}
```

**Error Event**: `scan_error`

**Server → Client**:
```json
{
  "event": "scan_error",
  "data": {
    "scan_id": "uuid-123",
    "error": "no_barcode_detected",
    "message": "Could not detect barcode or read label. Please try again with better lighting.",
    "stage": "image_processing",
    "retry_suggestions": [
      "Ensure the barcode is clearly visible",
      "Improve lighting conditions",
      "Hold camera steady and closer"
    ],
    "recoverable": true
  }
}
```

**Error Types**:
- `no_barcode_detected`: OCR failed to find product info
- `nutrition_not_found`: No data in OpenFoodFacts or web
- `profile_not_found`: User profile missing
- `scoring_failed`: DSPy module error
- `server_error`: Internal server error

#### 10.2.4 Disconnection

**Event**: `disconnect`

**Client → Server**: Close connection

**Server Cleanup**: Cancel any ongoing scans for this connection

### 10.3 Error Response Format

All errors follow consistent format:

```json
{
  "status": "error",
  "error_code": "validation_error",  // Machine-readable
  "message": "Weight must be between 20 and 300 kg",  // Human-readable
  "details": {
    // Optional additional context
  },
  "timestamp": "2025-01-14T10:30:00Z"
}
```

**Standard Error Codes**:
- `validation_error`: Input validation failed
- `profile_not_found`: User profile does not exist
- `authentication_required`: Missing user credentials
- `service_unavailable`: External service (Ollama, SearXNG) down
- `rate_limit_exceeded`: Too many requests (future)
- `internal_error`: Unexpected server error

---

## Section 11: Async Flow Diagrams

### 11.1 Onboarding Flow

**Participants**: Client (WebSocket), OnboardingHandler, ConversationalAgent, ProfileStore

```
Client                  OnboardingHandler              ConversationalAgent              ProfileStore
  |                              |                              |                              |
  |--start_onboarding---------->|                              |                              |
  |                              |--init_conversation---------->|                              |
  |                              |                              |--load_question_bank()        |
  |                              |                              |<--return bank                |
  |                              |<--first_question-------------|                              |
  |<--onboarding_question--------|                              |                              |
  |                              |                              |                              |
  |--onboarding_response-------->|                              |                              |
  |                              |--extract_data()------------->|                              |
  |                              |                              |--DSPy.ExtractStructuredData()|
  |                              |                              |<--return extracted           |
  |                              |<--return (value, confidence)-|                              |
  |                              |                              |                              |
  |                              |--if confidence < 0.7-------->|                              |
  |                              |                              |--DSPy.GenerateFollowUp()     |
  |                              |                              |<--return clarification       |
  |                              |<--followup_question----------|                              |
  |<--onboarding_question--------|                              |                              |
  |                              |                              |                              |
  |--onboarding_response-------->|                              |                              |
  |                              |--extract_data() [retry]----->|                              |
  |                              |<--return (value, OK)---------|                              |
  |                              |                              |                              |
  |                              |--select_next()-------------->|                              |
  |                              |                              |--check_missing_fields()      |
  |                              |                              |--if cached question exist--->|
  |                              |                              |<--return cached              |
  |                              |                              |--else: Best-of-N refine()    |
  |                              |                              |<--return refined (cache)     |
  |                              |<--next_question--------------|                              |
  |<--onboarding_question--------|                              |                              |
  |                              |                              |                              |
  [...repeat until all fields collected...]                     |                              |
  |                              |                              |                              |
  |--onboarding_response-------->|                              |                              |
  |                              |--check_complete()----------->|                              |
  |                              |<--return True----------------|                              |
  |                              |                              |                              |
  |                              |--build_profile()                                            |
  |                              |--calculate_health_metrics()                                 |
  |                              |--save_profile()------------------------------------------------>|
  |                              |                              |                              |--write JSON
  |                              |                              |                              |<--return OK
  |                              |<---------------------------------------------------------------------|
  |<--onboarding_complete--------|                              |                              |
  |                              |                              |                              |
```

**Key Async Points**:
1. **DSPy Extraction**: `await dspy_module.forward()` - LLM inference (2-5s)
2. **Best-of-N Refinement**: Parallel generation of 5 candidates - `await asyncio.gather()` (10-15s, cached)
3. **Profile Save**: `await aiofiles.open()` + `json.dump()` (< 100ms)

**Error Handling**:
- If DSPy extraction fails 3 times → skip question, mark field as incomplete
- If Best-of-N refinement times out (>20s) → use standard question from bank
- If profile save fails → retry once, then emit error

### 11.2 Scanning Pipeline Flow

**Participants**: Client, ScanHandler, ImageProcessor, NutritionRetriever, SearchIntern, HistoryTracker, ScoringEngine, AssessmentBuilder

```
Client          ScanHandler     ImageProcessor  NutritionRetriever  SearchIntern  HistoryTracker  ScoringEngine  AssessmentBuilder
  |                  |                  |                  |                  |                  |                  |
  |--start_scan----->|                  |                  |                  |                  |                  |
  |                  |--generate UUID   |                  |                  |                  |                  |
  |<--scan_started---|                  |                  |                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 1: Image Processing-------->|                  |                  |                  |
  |<--scan_progress--|                  |                  |                  |                  |                  |
  |                  |                  |--preprocess()    |                  |                  |                  |
  |                  |                  |--detect_barcode()|                  |                  |                  |
  |                  |                  |--ocr_extract()   |                  |                  |                  |
  |                  |                  |--DSPy.ExtractNutritionalEntities()  |                  |                  |
  |                  |<--return (barcode?, ocr_data, gaps)-|                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 2: Nutrition Retrieval----->|                  |                  |                  |
  |<--scan_progress--|                  |                  |                  |                  |                  |
  |                  |                  |                  |--if barcode----->|                  |                  |
  |                  |                  |                  |  lookup_barcode()|                  |                  |
  |                  |                  |                  |<--return product-|                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |                  |                  |--if gaps exist---|                  |                  |
  |                  |                  |                  |  delegate_to_intern()------------>|                  |
  |                  |                  |                  |                  |--DSPy.ReAct()    |                  |
  |                  |                  |                  |                  |  [10 iterations] |                  |
  |                  |                  |                  |<--return report--|                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |                  |                  |--merge_data()    |                  |                  |
  |                  |<--return nutrition_data-------------|                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 3: Load Context------------>|                  |                  |                  |
  |<--scan_progress--|                  |                  |                  |--get_today()---->|                  |
  |                  |                  |                  |                  |<--return summary-|                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 4: Scoring-------------------------------------------------->|                  |
  |<--scan_progress--|                  |                  |                  |                  |                  |
  |                  |                  |                  |                  |                  |--DSPy.ContextAwareScoring()
  |                  |                  |                  |                  |                  |<--return result--|
  |                  |<---------------------------------------------------------------------------|                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 5: Assessment Generation----------------------------------------------------------->|
  |<--scan_progress--|                  |                  |                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |--build_detailed()
  |                  |                  |                  |                  |                  |                  |--DSPy.Summarize()
  |                  |<--return (detailed, short)-------------------------------------------------------------------------|
  |                  |                  |                  |                  |                  |                  |
  |                  |--save_scan()------------------>|                  |                  |                  |
  |                  |                  |                  |                  |--update_history()->                  |
  |                  |                  |                  |                  |<--return OK------|                  |
  |                  |                  |                  |                  |                  |                  |
  |<--scan_complete--|                  |                  |                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |
```

**Parallel Execution Opportunities**:

1. **Stage 2**: If barcode found AND gaps exist:
   ```python
   barcode_task = lookup_barcode(barcode)
   intern_task = search_intern.forward(gaps)
   results = await asyncio.gather(barcode_task, intern_task)
   ```

2. **Stage 4 + 5**: While scoring runs, can preload history:
   ```python
   scoring_task = scoring_engine.score(nutrition_data, profile, context)
   history_task = history_tracker.get_today_summary(user_name)
   scoring_result, history = await asyncio.gather(scoring_task, history_task)
   ```

3. **Stage 5**: Detailed assessment build (sync) + Short assessment (async):
   ```python
   detailed = assessment_builder.build(scoring_result, sources)
   short_task = asyncio.create_task(summarizer.forward(detailed))

   # Emit detailed immediately
   await sio.emit("scan_complete", {"detailed_assessment": detailed})

   # Wait for short in background
   short = await short_task
   await sio.emit("short_assessment", {"short_assessment": short})
   ```

**Performance Targets**:
- **Stage 1**: 2-5s (image processing + DSPy extraction)
- **Stage 2**: 1-30s (barcode: 1s, intern: 10-30s if needed)
- **Stage 3**: <500ms (file read)
- **Stage 4**: 3-10s (DSPy scoring with context)
- **Stage 5**: 1-2s (build + summarize)

**Total**: 7-47s (typical: 10-15s with barcode, 25-35s with intern search)

### 11.3 History Update Flow

**Participants**: HistoryTracker, FileSystem

```
HistoryTracker                   FileSystem
      |                                |
      |--record_scan()                 |
      |  input: (user_name, scan_record)
      |                                |
      |--construct path: data/scan_history/{user_name}/{date}.json
      |                                |
      |--check if file exists--------->|
      |<--return True/False------------|
      |                                |
      |--if exists:                    |
      |    await aiofiles.open()------>|
      |    <--return file handle-------|
      |    json.loads(content)         |
      |    summary = DailySummary.parse()
      |                                |
      |--else:                         |
      |    summary = DailySummary(     |
      |      date=today,               |
      |      scans=[],                 |
      |      totals={}                 |
      |    )                           |
      |                                |
      |--append scan_record to scans   |
      |--recalculate totals            |
      |--recalculate vs_targets        |
      |                                |
      |--await aiofiles.open(mode='w')->|
      |<--return file handle-----------|
      |--json.dumps(summary)           |
      |--await file.write()----------->|
      |<--return bytes written---------|
      |                                |
      |<--return updated summary       |
      |                                |
```

**Concurrency Handling**:
- **File Locking**: Use `aiofiles` with OS-level advisory locks (fcntl on Linux)
- **Race Condition**: If two scans happen simultaneously, second write wins (acceptable for MVP)
- **Future**: Migrate to SQLite with transaction support

**Error Handling**:
- If directory doesn't exist → create it (makedirs with exist_ok=True)
- If JSON parse fails → backup corrupted file, create new summary
- If write fails → retry once, then raise exception

---

## Section 12: Module Decoupling Strategy

### 12.1 Independence Matrix

Each module MUST be testable in isolation. This table defines input requirements and fallback behaviors.

| Module | Required Inputs | External Dependencies | Standalone Testable? | Fallback Behavior |
|--------|----------------|----------------------|---------------------|------------------|
| **QuestionBank** | None (hardcoded questions) | None | ✅ Yes | N/A |
| **ConversationalAgent** | Question bank, user response | Ollama LLM | ✅ Yes (mock LLM) | Return default extraction |
| **HealthModelingEngine** | User demographics, lifestyle | None (pure calculation) | ✅ Yes | N/A |
| **ImageProcessor** | Image bytes | Chandra OCR, pyzbar | ✅ Yes (test images) | Return "no data found" |
| **OpenFoodFactsClient** | Barcode or product name | OpenFoodFacts API | ✅ Yes (mock HTTP) | Return None |
| **SearchInternAgent** | Search query, product hints | SearXNG, Ollama | ✅ Yes (mock both) | Return empty report |
| **HistoryTracker** | User name, scan record | File system | ✅ Yes (temp dir) | N/A |
| **ScoringEngine** | Nutrition data, profile, context | Ollama LLM | ✅ Yes (mock LLM) | Use rule-based scoring |
| **AssessmentBuilder** | Scoring result, sources | None (pure assembly) | ✅ Yes | N/A |
| **AssessmentSummarizer** | Detailed assessment | Ollama LLM | ✅ Yes (mock LLM) | Return truncated detailed text |

### 12.2 Interface Contracts

Each module exposes a clear interface. Other modules interact ONLY through these interfaces.

#### 12.2.1 ConversationalAgent Interface

```python
class IConversationalAgent(Protocol):
    """Interface for conversational onboarding agent."""

    async def select_next_question(
        self,
        conversation_history: List[Dict],
        collected_data: Dict[str, Any],
        missing_fields: List[str]
    ) -> Tuple[str, str]:  # (category, question_text)
        """Select and optionally refine next question."""
        ...

    async def extract_data(
        self,
        question_category: str,
        user_response: str,
        expected_format: str
    ) -> Tuple[Any, float]:  # (extracted_value, confidence)
        """Extract structured data from user response."""
        ...

    async def generate_followup(
        self,
        original_question: str,
        user_response: str,
        clarification_needed: str
    ) -> str:  # Followup question
        """Generate clarifying followup question."""
        ...
```

**Implementation**: `ConversationalOnboardingAgent` (DSPy-based)

**Mock Implementation** (for testing):
```python
class MockConversationalAgent(IConversationalAgent):
    """Mock agent that returns predefined responses."""

    def __init__(self, mock_responses: Dict[str, Any]):
        self.mock_responses = mock_responses

    async def select_next_question(self, *args, **kwargs):
        return ("demographics", "What is your age?")

    async def extract_data(self, category, response, format):
        return (self.mock_responses.get(category), 1.0)

    async def generate_followup(self, *args, **kwargs):
        return "Could you please clarify?"
```

#### 12.2.2 NutritionRetriever Interface

```python
class INutritionRetriever(Protocol):
    """Interface for nutrition data retrieval."""

    async def retrieve(
        self,
        barcode: Optional[str],
        ocr_data: Optional[Dict],
        gaps: List[str]
    ) -> Tuple[NutritionData, List[CitationSource]]:
        """Retrieve nutrition data from all available sources."""
        ...
```

**Implementation**: `NutritionDataAggregator`

**Fallback Chain**:
1. OpenFoodFacts barcode lookup (if barcode available)
2. OpenFoodFacts text search (if product name available)
3. SearchIntern agent (if gaps exist)
4. Return partial data with low confidence

#### 12.2.3 ScoringEngine Interface

```python
class IScoringEngine(Protocol):
    """Interface for food scoring."""

    async def score(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile,
        consumption_context: Dict[str, Any]
    ) -> Dict[str, Any]:  # Scoring result
        """Score food product based on nutrition, profile, and context."""
        ...
```

**Implementation**: `ContextAwareScoringEngine` (DSPy-based)

**Fallback**: If DSPy fails, use `RuleBasedScoringEngine`:
```python
class RuleBasedScoringEngine(IScoringEngine):
    """Fallback scoring without LLM."""

    async def score(self, nutrition_data, profile, context):
        # Simple rule-based scoring
        score = 5.0  # Neutral start

        # Allergen check
        if any(allergen in profile.allergens for allergen in nutrition_data.allergens):
            return {"score": 0.0, "verdict": "avoid", "reasoning": "Contains allergen"}

        # High protein → +1
        if nutrition_data.protein_per_100g > 10:
            score += 1

        # High sugar → -2
        if nutrition_data.sugar_per_100g > 20:
            score -= 2

        # ... more rules

        return {
            "base_score": score,
            "final_score": max(0, min(10, score)),
            "verdict": self._score_to_verdict(score),
            "reasoning": "Rule-based scoring (LLM unavailable)"
        }
```

### 12.3 Dependency Injection Pattern

All modules use constructor injection for dependencies. This allows easy mocking and testing.

**Example**: `ScanHandler` depends on multiple services:

```python
class ScanHandler:
    """WebSocket handler for scanning pipeline."""

    def __init__(
        self,
        image_processor: IImageProcessor,
        nutrition_retriever: INutritionRetriever,
        history_tracker: IHistoryTracker,
        scoring_engine: IScoringEngine,
        assessment_builder: IAssessmentBuilder,
        profile_store: IProfileStore
    ):
        self.image_processor = image_processor
        self.nutrition_retriever = nutrition_retriever
        self.history_tracker = history_tracker
        self.scoring_engine = scoring_engine
        self.assessment_builder = assessment_builder
        self.profile_store = profile_store

    async def handle_scan(self, user_name: str, image_base64: str):
        # Uses injected dependencies
        ...
```

**Production Initialization** (in `app/main.py`):
```python
# Initialize all services
image_processor = ImageProcessor()
nutrition_retriever = NutritionDataAggregator(
    openfoodfacts_client=OpenFoodFactsClient(),
    search_intern=SearchInternAgent(model="deepseek-r1:8b")
)
history_tracker = HistoryTracker(base_dir="./data/scan_history")
scoring_engine = ContextAwareScoringEngine(model="qwen3:30b")
assessment_builder = DetailedAssessmentBuilder()
profile_store = ProfileStore(profiles_dir="./data/profiles")

# Inject into handler
scan_handler = ScanHandler(
    image_processor=image_processor,
    nutrition_retriever=nutrition_retriever,
    history_tracker=history_tracker,
    scoring_engine=scoring_engine,
    assessment_builder=assessment_builder,
    profile_store=profile_store
)

# Register with Socket.IO
@sio.on("start_scan")
async def on_start_scan(sid, data):
    await scan_handler.handle_scan(data["user_name"], data["image_base64"])
```

**Test Initialization** (with mocks):
```python
def test_scan_handler():
    # Create mocks
    mock_image_processor = MockImageProcessor()
    mock_nutrition_retriever = MockNutritionRetriever()
    mock_history_tracker = MockHistoryTracker()
    mock_scoring_engine = MockScoringEngine()
    mock_assessment_builder = MockAssessmentBuilder()
    mock_profile_store = MockProfileStore()

    # Inject mocks
    handler = ScanHandler(
        image_processor=mock_image_processor,
        nutrition_retriever=mock_nutrition_retriever,
        history_tracker=mock_history_tracker,
        scoring_engine=mock_scoring_engine,
        assessment_builder=mock_assessment_builder,
        profile_store=mock_profile_store
    )

    # Test behavior
    result = await handler.handle_scan("test_user", "base64_image")
    assert result is not None
```

### 12.4 Configuration Isolation

Each module has its own configuration section, loaded independently.

**Example**: `backend/app/core/config.py`
```python
class OllamaConfig(BaseModel):
    """Ollama-specific configuration."""
    api_base: str = "http://localhost:11434"
    model_default: str = "qwen3:30b"
    model_fast: str = "qwen3:8b"
    model_reasoning: str = "deepseek-r1:8b"
    timeout: int = 120

class SearXNGConfig(BaseModel):
    """SearXNG-specific configuration."""
    api_base: str = "http://192.168.1.4"
    timeout: int = 10
    max_results: int = 10

class Settings(BaseSettings):
    """Global application settings."""
    ollama: OllamaConfig = OllamaConfig()
    searxng: SearXNGConfig = SearXNGConfig()
    # ... other config sections

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
```

**Environment Variable Override**:
```bash
# .env file
OLLAMA__MODEL_DEFAULT=qwen3:8b
SEARXNG__API_BASE=http://custom-searxng:8080
```

**Module Access**:
```python
from app.core.config import settings

class SearchInternAgent:
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.ollama.model_reasoning
        self.searxng_url = settings.searxng.api_base
```

---

## Section 13: Threading & Concurrency Patterns

### 13.1 Async Architecture

**Core Principle**: All I/O operations MUST be async. CPU-bound operations can be sync (run in executor if needed).

#### 13.1.1 Event Loop

Bytelense uses a single-threaded async event loop powered by `uvloop` (high-performance asyncio replacement).

**Setup** (in `app/main.py`):
```python
import uvloop
import asyncio

# Set uvloop as default event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# FastAPI + Socket.IO runs on this loop
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)
```

**Benefits**:
- 2-4x faster than standard asyncio
- Better scalability for I/O-bound workloads
- Lower memory overhead

#### 13.1.2 I/O Operation Patterns

**File I/O** (always async with aiofiles):
```python
import aiofiles
import json

async def load_profile(name: str) -> EnhancedUserProfile:
    path = f"./data/profiles/{name}.json"
    async with aiofiles.open(path, mode='r') as f:
        content = await f.read()
        data = json.loads(content)
        return EnhancedUserProfile(**data)
```

**HTTP Requests** (always async with httpx):
```python
import httpx

async def fetch_openfoodfacts(barcode: str) -> Dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        )
        response.raise_for_status()
        return response.json()
```

**LLM Inference** (DSPy with Ollama):
```python
import dspy

# DSPy automatically handles async when using async models
class MyModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.model = dspy.OllamaLocal(model="qwen3:30b")
        dspy.configure(lm=self.model)
        self.predictor = dspy.ChainOfThought(MySignature)

    async def forward(self, input_text: str):
        # DSPy handles async internally
        result = self.predictor(input=input_text)
        return result
```

### 13.2 Parallel Execution Patterns

#### 13.2.1 asyncio.gather (Parallel Wait)

**Use Case**: Run multiple independent async operations simultaneously and wait for all to complete.

**Example 1**: Parallel data retrieval in ScanHandler
```python
async def handle_scan(self, user_name: str, image_base64: str):
    # Stage 1: Image processing (sequential - depends on image)
    image_result = await self.image_processor.process(image_base64)

    # Stage 2: Parallel retrieval if we have both barcode AND gaps
    if image_result.barcode and image_result.gaps:
        barcode_task = self.openfoodfacts.lookup_barcode(image_result.barcode)
        intern_task = self.search_intern.research(image_result.product_name, image_result.gaps)

        # Wait for both concurrently
        barcode_result, intern_result = await asyncio.gather(
            barcode_task,
            intern_task,
            return_exceptions=True  # Don't fail if one fails
        )

        # Merge results (handling potential exceptions)
        nutrition_data = self._merge_results(barcode_result, intern_result)
    else:
        # Sequential fallback
        nutrition_data = await self._retrieve_sequentially(image_result)

    # Continue with scoring...
```

**Example 2**: Parallel question refinement (Best-of-N)
```python
async def refine_question(self, base_question: str) -> str:
    """Generate 5 variations in parallel, score them, pick best."""

    # Generate 5 variations concurrently
    tasks = [
        self._generate_variation(base_question, seed=i)
        for i in range(5)
    ]
    variations = await asyncio.gather(*tasks)

    # Score variations concurrently
    scoring_tasks = [
        self._score_politeness(variation)
        for variation in variations
    ]
    scores = await asyncio.gather(*scoring_tasks)

    # Pick best (highest score)
    best_idx = scores.index(max(scores))
    return variations[best_idx]
```

#### 13.2.2 asyncio.create_task (Fire and Forget)

**Use Case**: Start async operation without blocking current execution. Monitor later if needed.

**Example**: Short assessment generation in background
```python
async def emit_scan_complete(self, detailed_assessment: DetailedAssessment):
    # Emit detailed assessment immediately
    await sio.emit("scan_complete", {
        "detailed_assessment": detailed_assessment.dict()
    })

    # Start short assessment generation in background (don't wait)
    short_task = asyncio.create_task(
        self.summarizer.forward(detailed_assessment)
    )

    # Register callback for when it completes
    short_task.add_done_callback(
        lambda task: asyncio.create_task(
            sio.emit("short_assessment", {"short_assessment": task.result().dict()})
        )
    )

    # Return immediately (short assessment sent later)
```

#### 13.2.3 asyncio.wait_for (Timeout)

**Use Case**: Enforce timeout on async operations to prevent hanging.

**Example**: SearXNG search with timeout
```python
async def search_web(self, query: str) -> Dict:
    """Search with 10-second timeout."""
    try:
        result = await asyncio.wait_for(
            self._do_search(query),
            timeout=10.0
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Search timeout for query: {query}")
        return {"results": [], "error": "timeout"}
```

### 13.3 Concurrency Control

#### 13.3.1 Semaphore (Rate Limiting)

**Use Case**: Limit concurrent LLM requests to prevent overwhelming Ollama.

**Implementation**:
```python
class OllamaRateLimiter:
    """Limit concurrent Ollama requests."""

    def __init__(self, max_concurrent: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def request(self, model: str, prompt: str):
        async with self.semaphore:
            # Only 3 requests can run simultaneously
            return await self._call_ollama(model, prompt)

    async def _call_ollama(self, model: str, prompt: str):
        # Actual Ollama API call
        ...

# Global rate limiter
ollama_limiter = OllamaRateLimiter(max_concurrent=3)

# Usage in DSPy modules
class MyDSPyModule(dspy.Module):
    async def forward(self, input):
        # Acquire semaphore before LLM call
        result = await ollama_limiter.request(
            model="qwen3:30b",
            prompt=input
        )
        return result
```

#### 13.3.2 Lock (Shared State Protection)

**Use Case**: Protect shared mutable state (e.g., in-memory caches).

**Implementation**:
```python
class RefinedQuestionCache:
    """Thread-safe cache for refined questions."""

    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self.lock:
            return self.cache.get(key)

    async def set(self, key: str, value: str):
        async with self.lock:
            self.cache[key] = value

# Global cache
question_cache = RefinedQuestionCache()

# Usage
async def get_refined_question(category: str) -> str:
    # Check cache first
    cached = await question_cache.get(category)
    if cached:
        return cached

    # Generate if not cached
    refined = await expensive_refinement(category)

    # Store in cache
    await question_cache.set(category, refined)
    return refined
```

### 13.4 CPU-Bound Operations

Some operations (image preprocessing, large JSON parsing) are CPU-bound and block the event loop.

**Solution**: Run in executor (thread pool or process pool).

**Example**: Image preprocessing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np

# Create thread pool (reuse across app lifetime)
executor = ThreadPoolExecutor(max_workers=4)

def _preprocess_image_sync(image_bytes: bytes) -> np.ndarray:
    """CPU-bound image processing (sync function)."""
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Preprocessing (CPU-intensive)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray)
    enhanced = cv2.equalizeHist(denoised)

    return enhanced

async def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Async wrapper for CPU-bound preprocessing."""
    loop = asyncio.get_event_loop()

    # Run sync function in thread pool
    result = await loop.run_in_executor(
        executor,
        _preprocess_image_sync,
        image_bytes
    )
    return result
```

**When to Use Executor**:
- ✅ Image preprocessing (OpenCV operations)
- ✅ Large JSON parsing (>1MB files)
- ✅ Cryptographic operations
- ❌ Network I/O (use async/await instead)
- ❌ File I/O (use aiofiles instead)
- ❌ LLM calls (DSPy handles async internally)

### 13.5 Error Propagation

In async context, exceptions can be tricky. Use proper error handling.

**Pattern 1**: Handle errors in gather
```python
async def parallel_with_error_handling():
    tasks = [task1(), task2(), task3()]

    # return_exceptions=True prevents one failure from cancelling others
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check each result
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Task {i} failed: {result}")
            # Use fallback value
            results[i] = get_fallback_value(i)

    return results
```

**Pattern 2**: Wrap tasks in try-except
```python
async def safe_task(task_func, *args, **kwargs):
    """Wrapper that catches and logs exceptions."""
    try:
        return await task_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        return None

# Usage
async def main():
    results = await asyncio.gather(
        safe_task(task1),
        safe_task(task2),
        safe_task(task3)
    )
    # All tasks complete even if some fail
```

---

## Section 14: Function-Level Specifications

This section provides complete function signatures and behavioral specifications for all modules.

### 14.1 ConversationalOnboardingAgent

**File**: `backend/app/agents/conversational_onboarding.py`

#### 14.1.1 QuestionBank

```python
class QuestionBank:
    """Repository of onboarding questions with variations."""

    def __init__(self):
        """Initialize with hardcoded question sets."""
        self.questions: Dict[str, List[str]] = self._load_questions()
        self.categories: List[str] = list(self.questions.keys())

    def _load_questions(self) -> Dict[str, List[str]]:
        """
        Load question bank (hardcoded).

        Returns:
            Dict mapping category to list of question variations.

        Categories:
            - icebreaker: 4 variations
            - demographics_age: 3 variations
            - demographics_gender: 3 variations
            - demographics_height: 3 variations
            - demographics_weight: 3 variations
            - lifestyle_sleep: 4 variations
            - lifestyle_work: 4 variations
            - lifestyle_exercise: 4 variations
            - lifestyle_habits: 3 variations (smoking, alcohol)
            - goals: 4 variations
            - food_preferences: 3 variations
            - allergens: 3 variations
            - validation: 2 variations (confirmation questions)
        """
        # Return hardcoded question dict (see Section 3 for full list)

    def get_random_variation(self, category: str) -> str:
        """
        Get random question variation for category.

        Args:
            category: Question category (e.g., "demographics_age")

        Returns:
            Random question string from category's variations.

        Raises:
            KeyError: If category doesn't exist.
        """

    def get_all_variations(self, category: str) -> List[str]:
        """
        Get all question variations for category.

        Args:
            category: Question category

        Returns:
            List of all question variations.
        """
```

#### 14.1.2 ConversationalOnboardingAgent

```python
class ConversationalOnboardingAgent:
    """
    DSPy-based agent for conversational user onboarding.

    Responsibilities:
        1. Select next question based on conversation state
        2. Extract structured data from natural language responses
        3. Generate followup questions for clarification
        4. Use Best-of-N refinement for improved question quality (cached)
    """

    def __init__(
        self,
        model: str = "qwen3:8b",
        question_bank: Optional[QuestionBank] = None,
        cache_dir: str = "./data/cache/refined_questions"
    ):
        """
        Initialize conversational agent.

        Args:
            model: Ollama model name (use fast model for onboarding)
            question_bank: QuestionBank instance (creates default if None)
            cache_dir: Directory for caching refined questions

        Side Effects:
            - Initializes DSPy with Ollama model
            - Creates cache directory if doesn't exist
            - Loads refined question cache from disk
        """

    async def select_next_question(
        self,
        conversation_history: List[Dict[str, str]],
        collected_data: Dict[str, Any],
        missing_fields: List[str]
    ) -> Tuple[str, str]:
        """
        Select next question to ask based on conversation state.

        Args:
            conversation_history: List of {role, content} dicts
                Example: [
                    {"role": "assistant", "content": "Hi! What brings you here?"},
                    {"role": "user", "content": "I want to lose weight"}
                ]
            collected_data: Already extracted data
                Example: {"goal": "lose_weight", "age": 28}
            missing_fields: List of fields still needed
                Example: ["height_cm", "weight_kg", "exercise_frequency"]

        Returns:
            Tuple of (category, question_text)
                category: e.g., "demographics_height"
                question_text: Either standard, cached, or refined question

        Logic:
            1. Determine next category from missing_fields (priority order)
            2. Check cache for refined question for this category
            3. If cached, return cached question
            4. If not cached and early in conversation, use standard question
            5. If not cached and user has been engaged (>5 exchanges), refine with Best-of-N
            6. Cache refined question for future use

        Performance:
            - Standard: <10ms
            - Cached: <50ms (file read)
            - Refined: 10-20s (Best-of-N with 5 candidates)
        """

    async def extract_data(
        self,
        question_category: str,
        user_response: str,
        expected_format: str
    ) -> Tuple[Any, float, Optional[str]]:
        """
        Extract structured data from user's natural language response.

        Args:
            question_category: Category of question asked
                Example: "demographics_age"
            user_response: User's free-form text response
                Example: "I'm 28 years old"
            expected_format: Description of expected data format
                Example: "integer between 1 and 120"

        Returns:
            Tuple of (extracted_value, confidence, clarification_needed)
                extracted_value: Typed value (int, float, str, etc.) or None
                confidence: Float 0.0-1.0 indicating extraction certainty
                clarification_needed: None if confident, else string describing what needs clarification

        Examples:
            Input: category="demographics_age", response="I'm 28 years old"
            Output: (28, 0.95, None)

            Input: category="demographics_age", response="late twenties"
            Output: (27, 0.5, "Please provide your exact age in years")

            Input: category="lifestyle_exercise", response="I go to the gym sometimes"
            Output: (None, 0.3, "How many times per week do you exercise?")

        DSPy Module Used:
            ExtractStructuredData signature with ChainOfThought

        Performance:
            - 2-5s per extraction (LLM call)

        Error Handling:
            - If DSPy fails (exception), returns (None, 0.0, "Could not understand response")
            - If timeout (>10s), returns (None, 0.0, "Request timeout, please try again")
        """

    async def generate_followup(
        self,
        original_question: str,
        user_response: str,
        clarification_needed: str
    ) -> str:
        """
        Generate clarifying followup question.

        Args:
            original_question: The question that was asked
            user_response: User's ambiguous response
            clarification_needed: What aspect needs clarification

        Returns:
            Followup question string

        Example:
            Input:
                original_question="How often do you exercise?"
                user_response="Sometimes"
                clarification_needed="Need specific frequency (times per week)"
            Output:
                "Thanks! To be more specific, how many times per week would you say you exercise? Even a rough estimate helps!"

        DSPy Module Used:
            GenerateFollowUpQuestion signature with ChainOfThought

        Performance:
            - 2-4s per generation
        """

    async def refine_question_best_of_n(
        self,
        base_question: str,
        category: str,
        n: int = 5
    ) -> str:
        """
        Refine question using Best-of-N with politeness scoring.

        Args:
            base_question: Standard question from QuestionBank
            category: Question category
            n: Number of variations to generate and evaluate (default 5)

        Returns:
            Best refined question

        Process:
            1. Generate N variations of base_question in parallel
            2. Score each variation on 3 dimensions:
                - Warmth (0-3): Friendly, approachable tone
                - Respect (0-3): Acknowledges autonomy, uses "you can skip"
                - Clarity (0-3): Clear, unambiguous, easy to answer
            3. Calculate total score (0-9)
            4. Return highest scoring variation

        DSPy Modules Used:
            - RefineQuestion signature for generation (N times in parallel)
            - ScorePoliteness signature for scoring (N times in parallel)

        Performance:
            - ~10-15s for N=5 (parallel generation + scoring)
            - Should be cached after first use

        Caching:
            - Cache key: f"{category}__refined"
            - Cache location: {cache_dir}/{category}.json
            - Cache TTL: Indefinite (manually invalidated)
        """

    async def _score_politeness(self, question: str) -> Dict[str, Any]:
        """
        Score question on politeness dimensions.

        Args:
            question: Question text to score

        Returns:
            Dict with keys:
                - warmth: int 0-3
                - respect: int 0-3
                - clarity: int 0-3
                - total: int 0-9
                - reasoning: str (brief explanation)

        DSPy Module Used:
            ScorePoliteness signature

        Scoring Rubric:
            Warmth:
                3: Very friendly, uses positive language, encouraging
                2: Polite and professional
                1: Neutral, no warmth
                0: Cold or demanding

            Respect:
                3: Acknowledges autonomy, offers skip option, no pressure
                2: Respectful tone, doesn't pressure
                1: Neutral, no autonomy language
                0: Demanding or judgmental

            Clarity:
                3: Crystal clear, easy to answer, provides context/examples
                2: Clear and understandable
                1: Slightly ambiguous
                0: Confusing or vague
        """
```

### 14.2 HealthModelingEngine

**File**: `backend/app/engines/health_modeling.py`

```python
class HealthModelingEngine:
    """
    Calculate user health metrics (BMI, BMR, TDEE, targets).

    NO external dependencies. Pure calculation engine.
    """

    def __init__(self):
        """Initialize engine with constants."""
        self.BMI_CATEGORIES = {
            "underweight": (0, 18.5),
            "normal": (18.5, 25.0),
            "overweight": (25.0, 30.0),
            "obese": (30.0, float('inf'))
        }

        self.ACTIVITY_MULTIPLIERS = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9
        }

    async def calculate_metrics(
        self,
        demographics: Demographics,
        lifestyle: LifestyleHabits,
        goals: HealthGoals
    ) -> HealthMetrics:
        """
        Calculate all health metrics.

        Args:
            demographics: User's age, gender, height, weight
            lifestyle: Sleep, work style, exercise, habits
            goals: Primary goal, target weight, timeline

        Returns:
            HealthMetrics object with BMI, BMR, TDEE, targets, risks

        Calculations Performed:
            1. BMI = weight(kg) / height(m)²
            2. BMR using Mifflin-St Jeor (preferred)
            3. Activity multiplier from lifestyle
            4. TDEE = BMR × activity_multiplier
            5. Daily energy target based on goal
            6. Health risk assessment
            7. Daily nutrient targets

        Performance:
            - <10ms (pure calculation, no I/O)
        """

    def _calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        """
        Calculate BMI.

        Args:
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms

        Returns:
            BMI value (float)

        Formula:
            BMI = weight(kg) / (height(m) ** 2)

        Example:
            Input: height_cm=175, weight_kg=72
            Output: 23.51 (normal weight)
        """

    def _get_bmi_category(self, bmi: float) -> str:
        """
        Categorize BMI.

        Args:
            bmi: BMI value

        Returns:
            Category string: "underweight", "normal", "overweight", or "obese"
        """

    def _calculate_bmr_mifflin(
        self,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: Literal["male", "female", "other"]
    ) -> float:
        """
        Calculate BMR using Mifflin-St Jeor equation (primary method).

        Args:
            weight_kg: Weight in kg
            height_cm: Height in cm
            age: Age in years
            gender: Biological gender for calculation

        Returns:
            BMR in kcal/day

        Formula:
            Male: BMR = (10 × weight) + (6.25 × height) - (5 × age) + 5
            Female: BMR = (10 × weight) + (6.25 × height) - (5 × age) - 161
            Other: Use average of male and female

        Example:
            Input: weight=72, height=175, age=28, gender="male"
            Calculation: (10 × 72) + (6.25 × 175) - (5 × 28) + 5
                       = 720 + 1093.75 - 140 + 5
                       = 1678.75 kcal/day
        """

    def _calculate_bmr_harris_benedict(
        self,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: Literal["male", "female", "other"]
    ) -> float:
        """
        Calculate BMR using Harris-Benedict equation (alternative method).

        Used for validation/comparison only. Not primary method.

        Formula:
            Male: BMR = 88.362 + (13.397 × weight) + (4.799 × height) - (5.677 × age)
            Female: BMR = 447.593 + (9.247 × weight) + (3.098 × height) - (4.330 × age)
        """

    def _calculate_activity_multiplier(self, lifestyle: LifestyleHabits) -> float:
        """
        Calculate activity multiplier based on lifestyle.

        Args:
            lifestyle: Complete lifestyle habits

        Returns:
            Activity multiplier (1.2 to 2.5)

        Logic:
            1. Start with base from work_style:
                - "desk_job" → base 1.2
                - "light_activity" → base 1.375
                - "physical_job" → base 1.55

            2. Adjust for exercise_frequency:
                - "rarely": +0.0
                - "1-2_times_week": +0.1
                - "3-4_times_week": +0.2
                - "5_times_week": +0.3
                - "daily": +0.4

            3. Adjust for commute_type:
                - "car": +0.0
                - "public_transport": +0.05
                - "bike": +0.15
                - "walk": +0.1

            4. Penalties:
                - sleep_hours < 6: -0.05 (fatigue reduces activity)
                - smoking "yes": -0.05 (reduced cardiovascular efficiency)

            5. Cap final result between 1.2 and 2.5

        Example:
            Input: work_style="desk_job", exercise="3-4_times_week", commute="bike", sleep=7
            Calculation: 1.2 (base) + 0.2 (exercise) + 0.15 (bike) = 1.55
        """

    def _calculate_energy_budget(
        self,
        tdee: float,
        goal: Literal["lose_weight", "maintain_weight", "gain_muscle"]
    ) -> float:
        """
        Calculate daily energy target based on goal.

        Args:
            tdee: Total Daily Energy Expenditure
            goal: User's primary health goal

        Returns:
            Daily calorie target

        Logic:
            - lose_weight: TDEE - 500 (creates ~0.5 kg/week deficit)
            - maintain_weight: TDEE (no change)
            - gain_muscle: TDEE + 300 (controlled surplus)

        Constraints:
            - Never below 1200 kcal (minimum safe intake)
            - Never below BMR * 0.8 (preserve metabolic health)
        """

    def _assess_health_risks(
        self,
        bmi: float,
        lifestyle: LifestyleHabits,
        age: int
    ) -> List[str]:
        """
        Identify health risk factors.

        Args:
            bmi: Calculated BMI
            lifestyle: Lifestyle habits
            age: User's age

        Returns:
            List of risk messages (empty if no risks)

        Risk Factors Checked:
            1. BMI < 18.5: "Underweight may indicate malnutrition"
            2. BMI > 30: "Obesity increases risk of cardiovascular disease"
            3. sleep_hours < 6: "Chronic sleep deprivation linked to multiple health issues"
            4. exercise_frequency == "rarely": "Sedentary lifestyle increases disease risk"
            5. smoking == "yes": "Smoking is major risk factor for cancer and heart disease"
            6. alcohol == "heavy": "Heavy alcohol use damages liver and other organs"
            7. stress == "high" AND sleep_hours < 7: "Combined stress and poor sleep strongly linked to burnout"
            8. age > 60 AND bmi > 27: "Excess weight in older age increases fall risk"
        """

    async def calculate_daily_targets(
        self,
        energy_target: float,
        goal: Literal["lose_weight", "maintain_weight", "gain_muscle"],
        weight_kg: float
    ) -> Dict[str, float]:
        """
        Calculate daily macronutrient and micronutrient targets.

        Args:
            energy_target: Daily calorie target
            goal: User's health goal
            weight_kg: Current weight

        Returns:
            Dict with keys:
                - calories: Same as energy_target
                - protein_g: Based on goal (1.6-2.2g/kg for muscle gain)
                - carbs_g: Fill remaining calories
                - fat_g: 25-30% of calories
                - fiber_g: 30-35g (standard recommendation)
                - sugar_g: <10% of calories (WHO guideline)
                - sodium_mg: <2300mg (FDA guideline)

        Protein Targets:
            - lose_weight: 1.6g/kg (preserve muscle during deficit)
            - maintain_weight: 1.2g/kg (maintenance)
            - gain_muscle: 2.0g/kg (support muscle synthesis)

        Example:
            Input: energy_target=2000, goal="lose_weight", weight=72kg
            Output: {
                "calories": 2000,
                "protein_g": 115.2,  # 1.6 * 72
                "carbs_g": 200,      # Remainder after protein and fat
                "fat_g": 67,         # ~30% of calories
                "fiber_g": 30,
                "sugar_g": 50,       # <10% of 2000
                "sodium_mg": 2300
            }
        """
```

### 14.3 ImageProcessor

**File**: `backend/app/services/image_processing.py`

```python
class ImageProcessor:
    """
    Process food product images: barcode detection, OCR, DSPy extraction.

    Dependencies:
        - cv2 (OpenCV) for preprocessing
        - pyzbar for barcode detection
        - chandra_ocr for text extraction
        - DSPy for structured data extraction
    """

    def __init__(self, model: str = "qwen3:8b"):
        """
        Initialize image processor.

        Args:
            model: Ollama model for DSPy extraction (use fast model)

        Side Effects:
            - Initializes DSPy with Ollama
            - Creates DSPy.ExtractNutritionalEntities module
        """

    async def process(
        self,
        image_base64: str
    ) -> RawOCRExtraction:
        """
        Process image through full 5-stage pipeline.

        Args:
            image_base64: Base64-encoded image (with or without data URI prefix)

        Returns:
            RawOCRExtraction object containing:
                - barcode: Detected barcode (or None)
                - ocr_text: Raw OCR text
                - structured_data: DSPy extracted StructuredNutritionExtraction
                - confidence: Overall confidence (0-1)
                - gaps: List of missing critical fields

        Pipeline:
            1. Decode base64 → bytes
            2. Preprocess image (async in executor)
            3. Detect barcode (async in executor)
            4. Run OCR (Chandra)
            5. DSPy structural extraction
            6. Identify gaps

        Performance:
            - Stage 1-4: 2-3s (image operations)
            - Stage 5: 3-5s (DSPy extraction)
            - Total: 5-8s

        Error Handling:
            - If barcode detection fails: Continue with OCR
            - If OCR returns empty: Return extraction with confidence=0.0
            - If DSPy fails: Return raw OCR with confidence=0.2
        """

    async def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess image for better OCR/barcode detection.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Preprocessed image as numpy array

        Steps:
            1. Decode image from bytes
            2. Convert to grayscale
            3. Apply adaptive thresholding
            4. Denoise (fastNlMeansDenoising)
            5. Deskew if needed
            6. Enhance contrast (equalizeHist)

        Runs in executor (CPU-bound).
        """

    async def _detect_barcode(self, image: np.ndarray) -> Optional[str]:
        """
        Detect barcode from preprocessed image.

        Args:
            image: Preprocessed numpy array

        Returns:
            Barcode string (e.g., "5449000000996") or None

        Strategy:
            1. Try pyzbar on original orientation
            2. If failed, try rotated 90°, 180°, 270°
            3. If failed, try with different preprocessing
            4. Return first successful detection

        Barcode Types Supported:
            - EAN-13 (most common in India)
            - EAN-8
            - UPC-A
            - UPC-E
            - Code-128

        Runs in executor (CPU-bound).
        """

    async def _ocr_extract(self, image: np.ndarray) -> str:
        """
        Extract text from image using Chandra OCR.

        Args:
            image: Preprocessed numpy array

        Returns:
            Extracted text as string

        Uses:
            chandra_ocr library (Transformers-based)

        Performance:
            - ~1-2s per image
        """

    async def _dspy_extract(self, ocr_text: str) -> StructuredNutritionExtraction:
        """
        Extract structured nutrition data from OCR text using DSPy.

        Args:
            ocr_text: Raw OCR output

        Returns:
            StructuredNutritionExtraction object with:
                - product_name
                - brand
                - net_quantity
                - nutrients_per_100g (Dict)
                - ingredients_list
                - allergen_warnings
                - package_indicators (e.g., "multi-pack", "family size")
                - confidence
                - missing_critical_info

        DSPy Module:
            ExtractNutritionalEntities signature with ChainOfThought

        Handles:
            - Typos (e.g., "protien" → "protein")
            - Non-standard units (e.g., "10 gms" → 10.0)
            - Multilingual text (Hindi + English mix)
            - Ambiguous formatting

        Performance:
            - 3-5s with qwen3:8b
        """

    def _identify_gaps(self, structured: StructuredNutritionExtraction) -> List[str]:
        """
        Identify missing critical information.

        Args:
            structured: DSPy extracted data

        Returns:
            List of missing field names

        Critical Fields:
            - product_name (always required)
            - calories (required for scoring)
            - net_quantity OR serving_size (required for portion estimation)

        Nice-to-Have (not critical):
            - brand
            - ingredients_list
            - allergen_warnings

        Logic:
            If critical fields missing → return list for Search Intern
            If only nice-to-have missing → return empty (proceed without)
        """
```

(Continuing with remaining modules in next section due to length...)

### 14.4 SearchInternAgent

**File**: `backend/app/agents/search_intern.py`

```python
class SearchInternAgent:
    """
    Intelligent web research agent using DSPy ReAct with SearXNG tools.

    Metaphor: Research intern who autonomously searches the web,
              compiles reports, and provides source links.
    """

    def __init__(
        self,
        model: str = "deepseek-r1:8b",
        max_iterations: int = 10,
        timeout: int = 60
    ):
        """
        Initialize Search Intern Agent.

        Args:
            model: Ollama model for reasoning (deepseek-r1 recommended for reasoning)
            max_iterations: Max ReAct iterations (default 10)
            timeout: Overall timeout in seconds (default 60)

        Side Effects:
            - Initializes DSPy with Ollama
            - Registers FastMCP tools (search_web, extract_prices, etc.)
            - Creates ReAct module
        """

    async def research(
        self,
        task_description: str,
        product_hints: Dict[str, Any],
        data_type: Literal["size_variants", "nutrition_facts", "general"]
    ) -> InternAgentReport:
        """
        Conduct web research and compile report.

        Args:
            task_description: What to research
                Example: "Find size variants and prices for Lay's Classic potato chips in India"
            product_hints: Known product information
                Example: {"product_name": "Lay's Classic", "brand": "Lay's"}
            data_type: Type of data to extract

        Returns:
            InternAgentReport containing:
                - queries_executed: List of search queries tried
                - total_results_found: Total web results examined
                - relevant_results: List of relevant findings
                - summary: Human-readable summary
                - structured_data: Extracted data (e.g., size variants dict)
                - confidence: 0-1
                - sources: List of CitationSource objects WITH URLs

        Process (ReAct Loop):
            1. Thought: "I need to find size variants for Lay's Classic chips"
            2. Action: search_web("Lay's Classic chips sizes India")
            3. Observation: [10 results returned]
            4. Thought: "Results mention 25g, 52g, 100g sizes. Let me search for prices"
            5. Action: search_web("Lay's Classic 25g price India")
            6. Observation: [8 results, mentions ₹10]
            7. Thought: "Now I'll extract structured data from snippets"
            8. Action: extract_prices_and_sizes(snippets)
            9. Observation: {sizes: [{size: "25g", price: "₹10"}, ...]}
            10. Thought: "I have enough data. Compiling report."
            11. Return report with sources

        Performance:
            - Simple search (barcode lookup): 5-10s
            - Complex research (size variants + prices): 20-40s

        Error Handling:
            - If timeout: Return partial results with confidence < 0.5
            - If no results: Return empty report with confidence = 0.0
            - If SearXNG down: Raise exception (handled by caller)
        """

    async def _run_react_loop(
        self,
        task: str,
        hints: Dict,
        data_type: str
    ) -> Dict[str, Any]:
        """
        Run DSPy ReAct loop (internal).

        Returns:
            Raw DSPy ReAct output dict

        DSPy Module:
            ReAct with SearchInternTask signature and 4 tools
        """
```

**FastMCP Tools** (in same file):

```python
from fastmcp import FastMCP

mcp = FastMCP("SearXNG Tools")

@mcp.tool()
async def search_web(
    query: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search the web using SearXNG.

    Args:
        query: Search query string
        max_results: Maximum results to return (default 10)

    Returns:
        Dict with keys:
            - query: Original query
            - total_results: Number of results found
            - results: List of dicts with keys:
                - title: Page title
                - url: Page URL
                - content: Snippet/description
                - engine: Search engine source (e.g., "duckduckgo")
                - score: Relevance score (optional)

    Makes HTTP request to:
        http://192.168.1.4/search?q={query}&format=json&engines=...

    Timeout: 10 seconds

    Error Handling:
        - If SearXNG down: Raise ConnectionError
        - If timeout: Return {"results": [], "error": "timeout"}
        - If invalid JSON: Raise ValueError
    """

@mcp.tool()
async def extract_prices_and_sizes(
    snippet: str
) -> Dict[str, List[Dict]]:
    """
    Extract price and size information from text snippet.

    Args:
        snippet: Text containing price/size mentions
            Example: "Lay's Classic available in ₹10 (25g), ₹20 (52g) packs"

    Returns:
        Dict with key "variants":
            [{
                "size": "25g",
                "price": "₹10",
                "confidence": 0.9
            }, ...]

    Uses:
        Regex patterns for common price/size formats
        - Sizes: "\d+\s?(g|kg|ml|l|oz)"
        - Prices: "₹\d+|Rs\.?\s?\d+|\d+\s?rupees"

    Performance:
        - <100ms (regex-based, no LLM)
    """

@mcp.tool()
async def extract_nutrition_facts(
    snippet: str
) -> Dict[str, Any]:
    """
    Extract nutrition facts from text snippet.

    Args:
        snippet: Text containing nutrition information

    Returns:
        Dict with nutrition data:
            {
                "calories": 150,
                "protein_g": 2.0,
                "fat_g": 10.0,
                ...
            }

    Uses:
        Combination of regex and heuristics
        - Handles "per 100g" and "per serving" formats
        - Normalizes to per-100g

    Performance:
        - <100ms
    """

@mcp.tool()
async def validate_source_authority(
    url: str
) -> Dict[str, Any]:
    """
    Assess trustworthiness of a source URL.

    Args:
        url: Source URL to validate

    Returns:
        Dict with:
            - authority_score: 0-1 (1 = highly authoritative)
            - source_type: "official_brand" | "retailer" | "news" | "blog" | "unknown"
            - reasoning: Brief explanation

    Heuristics:
        - *.gov, *.edu, who.int, fda.gov → 1.0 (official)
        - Official brand domains → 0.9
        - amazon.in, flipkart.com → 0.8 (major retailers)
        - news sites → 0.7
        - blogs, forums → 0.3-0.5
        - Unknown → 0.2

    Performance:
        - <50ms (domain parsing, no HTTP request)
    """
```

### 14.5 HistoryTracker

**File**: `backend/app/services/history_tracker.py`

```python
class HistoryTracker:
    """
    Track daily/weekly food consumption history.

    Storage: JSON files in data/scan_history/{username}/{date}.json
    """

    def __init__(self, base_dir: str = "./data/scan_history"):
        """
        Initialize history tracker.

        Args:
            base_dir: Base directory for history files

        Side Effects:
            - Creates base_dir if doesn't exist
        """

    async def record_scan(
        self,
        user_name: str,
        scan_record: FoodScanRecord
    ) -> DailySummary:
        """
        Record a new scan and update daily summary.

        Args:
            user_name: Username
            scan_record: Complete scan record with nutrition data

        Returns:
            Updated DailySummary for today

        Process:
            1. Load today's summary (or create new if first scan)
            2. Append scan_record to scans list
            3. Recalculate totals (sum all nutrients from all scans)
            4. Save updated summary to disk
            5. Return summary

        File Locking:
            Uses aiofiles with OS advisory locks (fcntl)

        Performance:
            - <100ms (file read + write)

        Error Handling:
            - If file corrupted: Backup corrupted file, create fresh summary
            - If write fails: Retry once
        """

    async def get_today_summary(
        self,
        user_name: str,
        targets: Optional[Dict[str, float]] = None
    ) -> DailySummary:
        """
        Get today's consumption summary.

        Args:
            user_name: Username
            targets: Daily targets (if provided, calculates vs_targets)

        Returns:
            DailySummary object

        If today's file doesn't exist:
            Returns empty summary (no scans today)
        """

    async def get_week_summary(
        self,
        user_name: str,
        weeks_back: int = 0
    ) -> WeeklySummary:
        """
        Get weekly consumption summary.

        Args:
            user_name: Username
            weeks_back: 0 = current week, 1 = last week, etc.

        Returns:
            WeeklySummary aggregating 7 days

        Process:
            1. Calculate date range (Mon-Sun)
            2. Load DailySummary for each day (if exists)
            3. Aggregate all scans
            4. Calculate weekly totals and averages

        Performance:
            - <500ms (reads 7 files)
        """

    async def calculate_moderation_level(
        self,
        user_name: str,
        new_scan: FoodScanRecord,
        targets: Dict[str, float]
    ) -> str:
        """
        Calculate moderation level for a specific nutrient (e.g., sugar).

        Args:
            user_name: Username
            new_scan: The scan being evaluated
            targets: Daily targets

        Returns:
            Moderation level: "within" | "approaching" | "exceeding"

        Logic:
            1. Get today's summary
            2. Add new_scan nutrients to today's totals
            3. Compare to targets
            4. Return level:
                - "within": < 80% of daily target
                - "approaching": 80-100% of target
                - "exceeding": > 100% of target

        Example:
            Sugar target: 50g/day
            Today so far: 35g
            New scan: 15g
            Total: 50g (100%)
            Result: "approaching"
        """

    async def get_consumption_context(
        self,
        user_name: str,
        targets: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Get complete consumption context for scoring.

        Args:
            user_name: Username
            targets: Daily targets

        Returns:
            Dict with keys:
                - today_summary: DailySummary
                - week_summary: WeeklySummary (current week)
                - time_of_day: "morning" | "afternoon" | "evening" | "night"
                - recent_scans: Last 3 scans (chronological)

        Used by:
            ContextAwareScoringEngine to make informed decisions

        Performance:
            - <500ms (reads today + last 7 days)
        """
```

### 14.6 ContextAwareScoringEngine

**File**: `backend/app/engines/context_aware_scoring.py`

```python
class ContextAwareScoringEngine:
    """
    Score food products with full context awareness.

    Uses DSPy ChainOfThought with consumption history and timing.
    """

    def __init__(self, model: str = "qwen3:30b"):
        """
        Initialize scoring engine.

        Args:
            model: Ollama model (use powerful model for quality scoring)

        Side Effects:
            - Initializes DSPy with Ollama
            - Creates ChainOfThought module with ContextAwareNutritionScoring signature
        """

    async def score(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile,
        consumption_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score food product with context awareness.

        Args:
            nutrition_data: Product nutrition information
            user_profile: User's complete profile with health metrics
            consumption_context: From HistoryTracker.get_consumption_context()

        Returns:
            Dict with keys:
                - base_score: Intrinsic nutritional quality (0-10)
                - context_adjustment: Explanation of context-based adjustments
                - final_score: Base score × context multiplier × time multiplier
                - verdict: "excellent" | "good" | "moderate" | "caution" | "avoid"
                - reasoning: Step-by-step reasoning
                - warnings: List of concerns
                - highlights: List of positive points
                - moderation_message: Context-aware moderation advice
                - timing_recommendation: When this food is better consumed
                - confidence: 0-1

        Scoring Formula:
            Final Score = Base Score × Context Multiplier × Time Multiplier

            Base Score (0-10):
                - Intrinsic nutritional quality
                - Considers protein, fiber, vitamins vs sugar, sodium, saturated fat

            Context Multiplier (0.5-1.5):
                - 1.5: Far below daily targets, food helps meet goals
                - 1.0: Normal consumption, within moderation
                - 0.7: Approaching daily limits
                - 0.5: Already exceeded limits

            Time Multiplier (0.8-1.2):
                - Morning: 1.2 for complex carbs, 1.0 for others
                - Afternoon: 1.0 for most
                - Evening: 0.9 for high-sugar foods
                - Night: 0.8 for high-calorie foods

        Allergen Check (Priority):
            If product contains allergen from user profile → Immediate score 0.0, verdict "avoid"

        Process:
            1. Check allergens (auto-fail if violation)
            2. DSPy ChainOfThought reasoning:
                a. Assess base nutritional quality
                b. Compare to user's daily targets
                c. Consider today's consumption
                d. Adjust for time of day
                e. Generate final score and verdict
                f. Provide reasoning and recommendations
            3. Return complete scoring result

        Performance:
            - 5-10s with qwen3:30b (thorough reasoning)
            - 3-5s with qwen3:8b (faster but less nuanced)

        Fallback:
            If DSPy fails (timeout, error) → Use RuleBasedScoringEngine

        Error Handling:
            - If profile missing allergen data: Log warning, proceed without allergen check
            - If consumption_context incomplete: Use partial data
            - If DSPy timeout (>30s): Fallback to rule-based
        """

    async def _fallback_rule_based_score(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile,
        consumption_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback scoring without LLM (if DSPy fails).

        Uses simple rule-based heuristics.
        """
```

### 14.7 AssessmentBuilder & Summarizer

**File**: `backend/app/engines/assessment_generation.py`

```python
class DetailedAssessmentBuilder:
    """
    Build detailed assessment from scoring output (rule-based, no LLM).
    """

    def __init__(self):
        """Initialize builder with verdict thresholds."""
        self.VERDICT_THRESHOLDS = {
            "excellent": 8.0,
            "good": 6.0,
            "moderate": 4.0,
            "caution": 2.0,
            "avoid": 0.0
        }

        self.VERDICT_EMOJIS = {
            "excellent": "🟢",
            "good": "🟢",
            "moderate": "🟡",
            "caution": "🟡",
            "avoid": "🔴"
        }

    async def build(
        self,
        scan_id: str,
        nutrition_data: NutritionData,
        scoring_result: Dict[str, Any],
        consumption_context: Dict[str, Any],
        sources: List[CitationSource]
    ) -> DetailedAssessment:
        """
        Assemble detailed assessment (pure data transformation).

        Args:
            scan_id: UUID of scan
            nutrition_data: Product nutrition information
            scoring_result: Output from ContextAwareScoringEngine
            consumption_context: Consumption history
            sources: Data sources used (for citations)

        Returns:
            Complete DetailedAssessment object

        Process:
            1. Extract fields from scoring_result
            2. Map score to verdict category and emoji
            3. Format calculation string
            4. Build moderation message from context
            5. Assign sources to inline citations (match text snippets)
            6. Assemble complete assessment

        Performance:
            - <50ms (pure data assembly)

        No LLM calls - all data is already available from scoring engine.
        """

    def _score_to_verdict(self, score: float) -> str:
        """Map score to verdict category."""
        if score >= 8.0:
            return "excellent"
        elif score >= 6.0:
            return "good"
        elif score >= 4.0:
            return "moderate"
        elif score >= 2.0:
            return "caution"
        else:
            return "avoid"

    def _build_moderation_message(
        self,
        context: Dict[str, Any],
        warnings: List[str]
    ) -> str:
        """
        Build context-aware moderation message.

        Example:
            "You've consumed 35g of sugar today (70% of your 50g limit). This product adds 15g more."
        """

    def _assign_inline_citations(
        self,
        reasoning_text: str,
        sources: List[CitationSource]
    ) -> Dict[str, int]:
        """
        Match text snippets to citation numbers.

        Returns:
            Dict mapping text_snippet → citation_number
            Example: {"According to WHO guidelines": 1}
        """


class AssessmentSummarizer:
    """
    Summarize detailed assessment to short form using DSPy.
    """

    def __init__(self, model: str = "qwen3:8b"):
        """
        Initialize summarizer.

        Args:
            model: Ollama model for summarization (use fast model)
        """

    async def forward(
        self,
        detailed: DetailedAssessment,
        max_summary_chars: int = 150,
        max_key_points: int = 3
    ) -> ShortAssessment:
        """
        Generate short assessment from detailed.

        Args:
            detailed: Complete detailed assessment
            max_summary_chars: Max length for summary sentence
            max_key_points: Max number of key points (default 3)

        Returns:
            ShortAssessment object

        DSPy Module:
            SummarizeAssessment signature with ChainOfThought

        Process:
            1. Convert detailed assessment to JSON string
            2. Run DSPy summarization
            3. Extract summary, key_points, main_recommendation
            4. Build ShortAssessment object

        Performance:
            - 2-3s with qwen3:8b

        Can run in parallel with UI rendering (fire-and-forget).
        """
```

---

## Conclusion

This completes the comprehensive Low-Level Design document for Bytelense.

**Document Statistics**:
- **Total Sections**: 14
- **Total Pages**: ~150+ (combined across 3 parts)
- **Function Specifications**: 50+ detailed function signatures
- **Data Models**: 15+ Pydantic models
- **DSPy Modules**: 8 specialized modules
- **FastMCP Tools**: 4 research tools

**Coverage**:
✅ Architecture and module independence
✅ Complete data models with examples
✅ Conversational onboarding with OARS framework
✅ Health metrics calculation (BMI/BMR/TDEE)
✅ 5-stage OCR enhancement pipeline
✅ Search Intern ReAct agent with intelligent reasoning
✅ Food history tracking and moderation levels
✅ Context-aware scoring with formula
✅ Assessment generation (detailed + short)
✅ Complete API contracts (REST + WebSocket)
✅ Async flow diagrams
✅ Module decoupling strategy with interfaces
✅ Threading & concurrency patterns
✅ Function-level specifications for all modules

**Next Steps**:
1. Implement modules following this LLD
2. Write unit tests for each module (using mock implementations)
3. Write integration tests for pipelines
4. Test end-to-end flow with real food products
5. Implement frontend to consume WebSocket API

**This LLD is designed to be implemented by following each section sequentially, with clear specifications that even a small LLM can understand and translate into working code.**
