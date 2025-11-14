# Bytelense - High-Level Design Document

**Version:** 1.0
**Last Updated:** 2025-11-14
**Status:** Design Phase

---

## 1. System Overview

### 1.1 Purpose

Bytelense is a real-time food analysis system that provides personalized nutritional verdicts by combining computer vision, multi-source data retrieval, AI-powered reasoning, and dynamic UI generation.

### 1.2 System Boundaries

**In Scope:**

- Image acquisition (camera/upload)
- Barcode detection and OCR text extraction
- Multi-source nutritional data retrieval
- AI-powered personalized scoring
- Real-time communication
- Dynamic UI generation
- Local user profile management

**Out of Scope:**

- Cloud database synchronization
- Text-to-speech synthesis
- Speech-to-text processing
- Multi-user authentication systems
- Historical analytics across sessions
- Payment processing

### 1.3 Key Design Principles

1. **Asynchronous-First**: All I/O operations are non-blocking
2. **Fallback Chains**: Primary → Secondary → Tertiary data sources
3. **Declarative AI**: Use DSPy signatures instead of prompt strings
4. **Schema-Driven UI**: Backend controls frontend presentation
5. **Stateless Sessions**: Each scan is independent
6. **Local-First Storage**: JSON files for user profiles

---

## 2. System Architecture

### 2.1 Architectural Pattern

**Pattern**: Layered Architecture with Event-Driven Communication

```bash
┌─────────────────────────────────────────────────────────┐
│                   CLIENT LAYER                          │
│  (React + Vite + shadcn/ui + WebSocket Client)          │
└──────────────────┬──────────────────────────────────────┘
                   │ WebSocket + HTTP
┌──────────────────┴──────────────────────────────────────┐
│               GATEWAY LAYER                             │
│        (FastAPI + python-socketio)                      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│              SERVICE LAYER                              │
│  ┌──────────────┬──────────────┬──────────────────┐     │
│  │ Image        │ Data         │ AI               │     │
│  │ Processing   │ Retrieval    │ Reasoning        │     │
│  │ Service      │ Service      │ Service          │     │
│  └──────────────┴──────────────┴──────────────────┘     │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│            INTEGRATION LAYER                            │
│  ┌──────────────┬──────────────┬──────────────────┐     │
│  │ OpenFood     │ SearXNG      │ OpenAI           │     │
│  │ Facts API    │ (FastMCP)    │ API (DSPy)       │     │
│  └──────────────┴──────────────┴──────────────────┘     │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│              DATA LAYER                                 │
│        (Local JSON Files + aiofiles)                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Component Distribution

| Layer | Components | Location | Responsibility |
|-------|-----------|----------|----------------|
| **Client** | UI Components, WebSocket Client, State Management | `frontend/` | User interaction, display |
| **Gateway** | FastAPI App, SocketIO Manager, Route Handlers | `backend/app/api/` | Request routing, session management |
| **Service** | Business Logic Modules | `backend/app/services/` | Core operations |
| **Integration** | External API Clients, MCP Tools | `backend/app/services/` | Third-party communication |
| **Data** | JSON File Store, Profile Manager | `backend/app/core/` + `data/` | Persistence |

---

## 3. Subsystem Breakdown

### 3.1 Authentication Subsystem

**Location**: `backend/app/api/auth.py` + `frontend/src/components/auth/`

**Components**:

- **LoginHandler** (Backend): Validates name, checks profile existence
- **ProfileCreator** (Backend): Initializes new user profile JSON
- **LoginForm** (Frontend): Name input UI
- **OnboardingWizard** (Frontend): Multi-step profile creation form

**Responsibilities**:

- Authenticate user by name lookup
- Create new profiles with health data
- Persist profiles to filesystem
- Load existing profiles into session context

**Data Flow**:

```bash
User Input (Name)
  → LoginHandler.check_profile()
  → ProfileStore.load(name)
  → [exists] Return profile | [not exists] Trigger onboarding
```

### 3.2 Image Processing Subsystem

**Location**: `backend/app/services/image_processing.py`

**Components**:

- **BarcodeDetector**: Uses Pillow + opencv for preprocessing, delegates to pyzbar
- **OCRExtractor**: Uses chandra-ocr with transformers backend
- **ImagePreprocessor**: Normalizes image format, resolution, orientation

**Responsibilities**:

- Accept image bytes from WebSocket
- Detect and decode barcodes (UPC, EAN, QR)
- Extract text from labels when barcode fails
- Return structured extraction results

**Technology Mapping**:

- Preprocessing: `Pillow` (resize, convert) + `opencv-python-headless` (denoise, threshold)
- Barcode: `pyzbar` library (requires separate install)
- OCR: `chandra-ocr` via transformers `AutoModel.from_pretrained("datalab-to/chandra")`

**Input/Output Contract**:

```python
# Input
ImageProcessingRequest:
  - image_bytes: bytes
  - source: "camera" | "upload"

# Output
ImageProcessingResult:
  - barcode: Optional[str]  # None if not detected
  - ocr_text: Optional[str]  # None if barcode found
  - confidence: float
  - processing_time_ms: int
```

### 3.3 Nutritional Data Retrieval Subsystem

**Location**: `backend/app/services/nutrition_api.py` + `backend/app/services/searxng_client.py`

**Components**:

- **OpenFoodFactsClient**: httpx-based async client
- **SearXNGClient**: FastMCP-based tool integration
- **DataAggregator**: Merges data from multiple sources
- **NutritionNormalizer**: Standardizes varying data schemas

**Responsibilities**:

- Query OpenFoodFacts API by barcode or text
- Fallback to SearXNG web search when primary fails
- Parse and normalize nutritional data
- Handle incomplete or conflicting data

**Technology Mapping**:

- Primary API: `httpx.AsyncClient` for OpenFoodFacts
- Fallback: `fastmcp` decorators exposing SearXNG as tool
- MCP Integration: FastMCP `@mcp.tool()` decorator with type hints
- SearXNG API: `http://localhost:8888/search?q={query}&format=json` (requires JSON format enabled in settings.yml)

**Fallback Chain**:

```bash
1. OpenFoodFacts Barcode Lookup (< 3s)
   ↓ [404 or incomplete]
2. OpenFoodFacts Text Search (< 3s)
   ↓ [no results]
3. SearXNG Web Search via MCP (< 5s)
   ↓ [parse failure]
4. Return partial data + confidence flag
```

**Data Models**:

```python
NutritionData (Pydantic BaseModel):
  - product_name: str
  - brand: Optional[str]
  - barcode: Optional[str]
  - serving_size: str
  - calories: float
  - protein_g: float
  - carbs_g: float
  - fat_g: float
  - sugar_g: float
  - sodium_mg: float
  - fiber_g: Optional[float]
  - ingredients: List[str]
  - allergens: List[str]
  - data_source: "openfoodfacts" | "searxng" | "partial"
  - confidence: float  # 0.0-1.0
```

### 3.4 AI Reasoning Subsystem

**Location**: `backend/app/services/scoring.py` + `backend/app/models/dspy_modules.py`

**Components**:

- **NutritionScorerAgent** (DSPy ReAct Module): Core agentic reasoning engine with tool access
- **DataCleanerAgent** (DSPy Module): Cleans and normalizes raw nutrition data
- **SummaryGenerator** (DSPy Module): Generates concise, citation-backed summaries
- **CitationManager**: Tracks data sources and generates Perplexity-style references
- **VerdictGenerator**: Orchestrates scoring pipeline
- **AllergenChecker**: Pre-scoring safety validation

**Responsibilities**:

- Clean and normalize raw nutrition data from multiple sources
- Analyze nutrition data against user profile using ReAct reasoning
- Generate personalized score (0-10) with tool-assisted research
- Produce scientific reasoning with inline citations
- Extract actionable highlights with source attribution
- Detect allergen violations
- Format data for optimal user presentation

**Technology Mapping**:

- Framework: `dspy-ai` with `ReAct` module (not ChainOfThought)
- LLM Backend: **Ollama local models** via `dspy.LM('ollama_chat/{model}')`
- Recommended Models (from ollama list):
  - **Primary**: `qwen3:30b` (18GB) - Best reasoning capability
  - **Alternative**: `deepseek-r1:8b` (5.2GB) - Good reasoning, lower resource
  - **Fallback**: `qwen3:8b` (5.2GB) - Balanced performance
- Signature Definition: Typed input/output specs with tool integration

**DSPy ReAct Architecture**:

```python
# LLM Configuration (Ollama local)
lm = dspy.LM(
  'ollama_chat/qwen3:30b',  # or deepseek-r1:8b
  api_base='http://localhost:11434',
  api_key=''  # Not needed for local Ollama
)
dspy.configure(lm=lm)

# Tool Definitions (for ReAct agent)
def search_nutrition_database(product_name: str, barcode: Optional[str] = None) -> Dict:
  """Search OpenFoodFacts and SearXNG for nutritional information.

  Args:
    product_name: Name of the product to search
    barcode: Optional barcode for exact lookup

  Returns:
    Dict containing nutrition data and source URLs
  """
  # Tool implementation via FastMCP

def compare_similar_products(product_name: str, category: str) -> List[Dict]:
  """Find similar products for comparison and context.

  Args:
    product_name: Current product name
    category: Food category (e.g., "cereal", "snack")

  Returns:
    List of similar products with nutrition data
  """
  # Tool implementation

def get_health_guidelines(nutrient: str, user_goal: str) -> Dict:
  """Retrieve official health guidelines for specific nutrients.

  Args:
    nutrient: Nutrient name (e.g., "sodium", "sugar")
    user_goal: User health goal (e.g., "weight_loss", "diabetes")

  Returns:
    Guidelines with citations to authoritative sources
  """
  # Tool implementation

# Signature (declarative spec for ReAct agent)
class ScoreNutrition(dspy.Signature):
  """Analyze food nutrition data against user health profile using available tools.
  Generate a personalized health score with scientific reasoning and citations."""

  nutrition_data: NutritionData = dspy.InputField(desc="Raw nutrition data from sources")
  user_profile: UserProfile = dspy.InputField(desc="User health profile and goals")

  score: float = dspy.OutputField(desc="Health score 0-10 based on analysis")
  verdict: Literal["good", "moderate", "avoid"] = dspy.OutputField(desc="Overall verdict")
  reasoning: str = dspy.OutputField(desc="Step-by-step scientific explanation with inline citations [1], [2]")
  warnings: List[str] = dspy.OutputField(desc="Specific health concerns with citations")
  highlights: List[str] = dspy.OutputField(desc="Key nutritional facts (3-5 items) with citations")
  citations: List[Dict] = dspy.OutputField(desc="List of sources: {id: 1, url: '...', title: '...', snippet: '...'}")
  confidence: float = dspy.OutputField(desc="Confidence in analysis 0-1")

# ReAct Module (strategy with tool use)
class NutritionScorerAgent(dspy.Module):
  def __init__(self):
    super().__init__()
    # ReAct agent with tools (not ChainOfThought)
    self.agent = dspy.ReAct(
      signature=ScoreNutrition,
      tools=[
        search_nutrition_database,
        compare_similar_products,
        get_health_guidelines
      ],
      max_iters=5  # Limit reasoning steps
    )

  def forward(self, nutrition_data, user_profile):
    # Agent will iteratively:
    # 1. Reason about current state
    # 2. Decide which tool to call (or finish)
    # 3. Execute tool and gather info
    # 4. Repeat until confident answer
    return self.agent(
      nutrition_data=nutrition_data,
      user_profile=user_profile
    )
```

**Data Cleaning Pipeline**:

```python
class DataCleanerAgent(dspy.Module):
  """Cleans, normalizes, and validates nutrition data from multiple sources."""

  signature = """
    raw_data: Dict[str, Any]  # Messy data from APIs
    -> cleaned_data: NutritionData,  # Normalized schema
       data_quality_score: float,  # 0-1 quality metric
       missing_fields: List[str],  # Fields with no data
       conflicts: List[Dict]  # Conflicting values across sources
  """

  # Responsibilities:
  # - Normalize units (mg vs g, ml vs oz)
  # - Resolve conflicts (take most recent, authoritative source)
  # - Estimate missing values using ML or category averages
  # - Flag low-quality data (no source, outdated, incomplete)
  # - Extract serving size variations
```

**Citation Management** (Perplexity-style):

```python
class CitationManager:
  """Manages inline citations and reference lists like Perplexity AI."""

  def __init__(self):
    self.sources = []  # List of source dicts
    self.citation_map = {}  # Map content -> citation ID

  def add_source(self, url: str, title: str, snippet: str, timestamp: str) -> int:
    """Add a source and return its citation ID."""
    citation_id = len(self.sources) + 1
    self.sources.append({
      "id": citation_id,
      "url": url,
      "title": title,
      "snippet": snippet,  # Relevant excerpt
      "accessed": timestamp
    })
    return citation_id

  def format_inline_citation(self, text: str, source_id: int) -> str:
    """Format text with inline citation: 'High in sodium [1]'"""
    return f"{text} [{source_id}]"

  def generate_reference_list(self) -> List[Dict]:
    """Generate formatted reference list for UI."""
    return self.sources
```

**Scoring Factors** (DSPy ReAct will reason through with tools):

1. **Goal alignment** - Use tools to fetch health guidelines
2. **Allergen detection** - Auto-fail with citation to ingredient list
3. **Nutritional density** - Compare with similar products via tool
4. **Processing level** - Research additives using tools
5. **Portion appropriateness** - Validate against WHO/FDA guidelines
6. **Data quality** - Penalize low-confidence or conflicting data

**Output Contract**:

```python
ScoringResult:
  - score: float  # 0-10
  - verdict: "good" | "moderate" | "avoid"
  - reasoning: str  # With inline citations: "High sodium [1] exceeds daily limit [2]"
  - warnings: List[str]  # Each with citation: "Contains dairy [3]"
  - highlights: List[str]  # Key facts with citations: "Good protein source [4]"
  - citations: List[Citation]  # Full reference list
  - confidence: float  # Based on data quality and source authority
  - data_quality_score: float  # 0-1, how clean the input data was
  - reasoning_steps: List[str]  # ReAct thought process (for transparency)
```

**Citation Structure**:

```python
Citation:
  - id: int  # [1], [2], [3]
  - url: str  # Source URL
  - title: str  # Source title/description
  - snippet: str  # Relevant excerpt (like Perplexity)
  - accessed: datetime  # When data was retrieved
  - source_type: "openfoodfacts" | "searxng" | "who" | "fda"  # Categorize source
  - authority_score: float  # 0-1, credibility of source
```

### 3.5 Generative UI Subsystem

**Location**: `backend/app/services/ui_generator.py` + `frontend/src/lib/componentRegistry.js`

**Components**:

- **UISchemaBuilder** (Backend): Generates component tree
- **LayoutSelector** (Backend): Chooses layout based on verdict
- **ComponentRegistry** (Frontend): Maps schema to React components
- **DynamicRenderer** (Frontend): Renders schema-driven UI

**Responsibilities**:

- Generate UI schema based on scoring result
- Select appropriate layout and theme
- Map data to component properties
- Render components dynamically on frontend

**Schema Structure**:

```python
UISchema:
  - layout: "alert" | "balanced" | "encouraging"
  - theme: "red" | "yellow" | "green"
  - components: List[ComponentSpec]

ComponentSpec:
  - type: str  # Component identifier
  - props: Dict[str, Any]  # Component properties
  - order: int  # Render order
```

**Component Types**:

- `verdict_badge`: Color-coded status indicator
- `score_display`: Numeric score with visual meter
- `insight_list`: Bulleted highlights with icons (supports inline citations)
- `nutrition_card`: Macro breakdown with bars
- `reasoning_section`: Expandable explanation with inline citations [1], [2]
- `allergen_alert`: Warning banner
- `citation_list`: Perplexity-style reference list at bottom
- `inline_citation`: Clickable citation link [1] → scrolls to reference

**Backend Logic**:

```bash
ScoringResult → UISchemaBuilder
  ├─ verdict="avoid" → layout="alert", theme="red"
  ├─ verdict="moderate" → layout="balanced", theme="yellow"
  └─ verdict="good" → layout="encouraging", theme="green"

Components assembled based on:
  - Available data fields
  - Severity of warnings
  - User profile preferences
```

**Frontend Rendering**:

```javascript
// Component Registry (declarative mapping)
const registry = {
  verdict_badge: VerdictBadge,
  score_display: ScoreDisplay,
  insight_list: InsightList,
  // ...
}

// Dynamic Renderer
schema.components.map(spec => {
  const Component = registry[spec.type] || FallbackComponent
  return <Component {...spec.props} />
})
```

### 3.6 Real-Time Communication Subsystem

**Location**: `backend/app/api/scan.py` + `frontend/src/lib/websocket.js`

**Components**:

- **SocketIOManager** (Backend): python-socketio with FastAPI
- **ScanSessionHandler** (Backend): Per-connection state
- **ProgressEmitter** (Backend): Stage-by-stage updates
- **WebSocketClient** (Frontend): Connection and event handling

**Responsibilities**:

- Establish WebSocket connection on scan initiation
- Emit progress updates for each processing stage
- Stream final result as structured data
- Handle disconnections and errors

**Technology Mapping**:

- Backend: `python-socketio` with `socketio.ASGIApp()`
- Frontend: Native WebSocket or Socket.IO client
- Transport: WebSocket with fallback to polling

**Event Protocol**:

```python
# Client → Server
emit("start_scan", {
  "user": "john",
  "image_data": "base64...",
  "source": "camera"
})

# Server → Client (progressive updates)
emit("scan_progress", {
  "stage": "detecting_barcode",
  "progress": 20,
  "message": "Detecting barcode..."
})

emit("scan_progress", {
  "stage": "fetching_nutrition",
  "progress": 40,
  "message": "Looking up nutrition data..."
})

emit("scan_progress", {
  "stage": "analyzing",
  "progress": 70,
  "message": "Analyzing against your profile..."
})

# Server → Client (final result)
emit("scan_complete", {
  "nutrition": {...},
  "scoring": {...},
  "ui_schema": {...}
})

# Server → Client (error)
emit("scan_error", {
  "stage": "fetching_nutrition",
  "error": "Product not found",
  "retry_suggestion": "Try better lighting"
})
```

**Session Lifecycle**:

```bash
1. Client connects → SID assigned
2. Client emits "start_scan" → Session created
3. Server processes async → Emits progress at each stage
4. Server emits "scan_complete" → Session ends
5. Client disconnects → Session cleaned up
```

### 3.7 Profile Management Subsystem

**Location**: `backend/app/core/profile_store.py` + `data/profiles/`

**Components**:

- **ProfileStore**: JSON file I/O manager
- **ProfileValidator**: Pydantic model validation
- **DailyTargetCalculator**: Computes recommended intakes
- **ProfileMigrator**: Schema version upgrades

**Responsibilities**:

- Create new profile JSON files
- Load profiles by name (async)
- Update profile fields
- Calculate daily nutritional targets based on goals

**Technology Mapping**:

- File I/O: `aiofiles` for async read/write
- Validation: `pydantic.BaseModel` with validators
- Storage: JSON files in `data/profiles/{name}.json`

**Data Model**:

```python
UserProfile (Pydantic BaseModel):
  - name: str
  - created_at: datetime
  - age: Optional[int]
  - gender: Optional[Literal["male", "female", "other"]]
  - height_cm: Optional[float]
  - weight_kg: Optional[float]
  - goals: List[str]  # ["weight_loss", "heart_health"]
  - allergies: List[str]  # ["dairy", "nuts"]
  - dietary_preferences: List[str]  # ["vegetarian"]
  - nutritional_focus: List[str]  # Top 3 priorities
  - daily_targets: DailyTargets

DailyTargets (nested model):
  - calories: int
  - sugar_g: float
  - sodium_mg: float
  - protein_g: float
  - carbs_g: float
  - fat_g: float
  - fiber_g: float
```

**Daily Target Calculation**:

```bash
Based on user goals:
  - weight_loss → -500 cal deficit
  - muscle_building → +200 cal surplus, high protein
  - diabetes_management → low sugar (25g max)
  - heart_health → low sodium (1500mg max)

Formula (declarative, not imperative):
  BMR calculated from age, weight, height
  TDEE = BMR × activity_multiplier
  Target calories = TDEE ± goal_adjustment
  Macros = standard ratios adjusted for goals
```

---

## 4. Data Models

### 4.1 Core Domain Models

All models use `pydantic.BaseModel` for validation and serialization.

#### ImageProcessingRequest

```python
source: Literal["camera", "upload"]
image_bytes: bytes
format: str  # "jpeg", "png"
timestamp: datetime
```

#### ImageProcessingResult

```python
barcode: Optional[str]
ocr_text: Optional[str]
confidence: float
method_used: Literal["barcode", "ocr"]
processing_time_ms: int
```

#### NutritionData

```python
product_name: str
brand: Optional[str]
barcode: Optional[str]
serving_size: str
calories: float
protein_g: float
carbs_g: float
fat_g: float
saturated_fat_g: Optional[float]
sugar_g: float
sodium_mg: float
fiber_g: Optional[float]
ingredients: List[str]
allergens: List[str]
additives: List[str]
data_source: Literal["openfoodfacts", "searxng", "partial"]
confidence: float
retrieved_at: datetime
```

#### UserProfile

```python
name: str
created_at: datetime
updated_at: datetime
age: Optional[int]
gender: Optional[str]
height_cm: Optional[float]
weight_kg: Optional[float]
goals: List[str]
allergies: List[str]
dietary_preferences: List[str]
nutritional_focus: List[str]
daily_targets: DailyTargets
```

#### DailyTargets

```python
calories: int
sugar_g: float
sodium_mg: float
protein_g: float
carbs_g: float
fat_g: float
fiber_g: float
```

#### ScoringResult

```python
score: float  # 0-10
verdict: Literal["good", "moderate", "avoid"]
reasoning: str  # With inline citations: "High sodium [1] exceeds limit [2]"
warnings: List[str]  # With citations: "Contains dairy [3]"
highlights: List[str]  # With citations: "Good protein [4]"
citations: List[Citation]  # Full reference list
confidence: float
data_quality_score: float  # 0-1, input data quality
reasoning_steps: List[str]  # ReAct agent's thought process
factors_considered: List[str]
```

#### Citation

```python
id: int  # Citation number [1], [2], [3]
url: str  # Source URL
title: str  # Source title
snippet: str  # Relevant excerpt (150-200 chars)
accessed: datetime  # When data retrieved
source_type: Literal["openfoodfacts", "searxng", "who", "fda", "usda"]
authority_score: float  # 0-1, source credibility
```

#### UISchema

```python
layout: Literal["alert", "balanced", "encouraging"]
theme: Literal["red", "yellow", "green"]
components: List[ComponentSpec]
```

#### ComponentSpec

```python
type: str
props: Dict[str, Any]
order: int
```

#### ScanResult (aggregate)

```python
scan_id: str
user_name: str
timestamp: datetime
image_processing: ImageProcessingResult
nutrition_data: NutritionData
scoring: ScoringResult
ui_schema: UISchema
```

### 4.2 API Request/Response Models

#### POST /api/auth/login

```python
# Request
LoginRequest:
  name: str

# Response
LoginResponse:
  status: "existing" | "new"
  profile: Optional[UserProfile]
  requires_onboarding: bool
```

#### POST /api/auth/onboard

```python
# Request
OnboardingRequest:
  name: str
  age: Optional[int]
  gender: Optional[str]
  height_cm: Optional[float]
  weight_kg: Optional[float]
  goals: List[str]
  allergies: List[str]
  dietary_preferences: List[str]
  nutritional_focus: List[str]

# Response
OnboardingResponse:
  profile: UserProfile
  daily_targets: DailyTargets
```

#### GET /api/profile/{name}

```python
# Response
ProfileResponse:
  profile: UserProfile
```

#### PATCH /api/profile/{name}

```python
# Request
ProfileUpdateRequest:
  # Any subset of UserProfile fields

# Response
ProfileUpdateResponse:
  profile: UserProfile
  updated_fields: List[str]
```

### 4.3 WebSocket Event Payloads

#### Client → Server

##### **start_scan**

```python
user: str
image_data: str  # base64 encoded
source: "camera" | "upload"
format: "jpeg" | "png"
```

#### Server → Client

##### **scan_progress**

```python
stage: str  # "detecting_barcode", "fetching_nutrition", "analyzing", "generating_ui"
progress: int  # 0-100
message: str
```

##### **scan_complete**

```python
result: ScanResult
```

##### **scan_error**

```python
stage: str
error: str
error_code: str
retry_suggestion: Optional[str]
```

---

## 5. API Specifications

### 5.1 REST Endpoints

All endpoints return JSON. Error responses follow RFC 7807 Problem Details.

#### Authentication & Profile

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| POST | `/api/auth/login` | Check if user exists | `LoginRequest` | `LoginResponse` |
| POST | `/api/auth/onboard` | Create new profile | `OnboardingRequest` | `OnboardingResponse` |
| GET | `/api/profile/{name}` | Get user profile | - | `ProfileResponse` |
| PATCH | `/api/profile/{name}` | Update profile | `ProfileUpdateRequest` | `ProfileUpdateResponse` |

#### Health & Status

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| GET | `/health` | Health check | `{"status": "ok"}` |
| GET | `/api/config` | Client configuration | `{"features": [...]}` |

### 5.2 WebSocket Events

**Namespace**: `/scan`

| Event | Direction | Payload | Purpose |
|-------|-----------|---------|---------|
| `connect` | Client → Server | - | Establish connection |
| `start_scan` | Client → Server | `{user, image_data, source}` | Initiate scan |
| `scan_progress` | Server → Client | `{stage, progress, message}` | Update progress |
| `scan_complete` | Server → Client | `{result}` | Final result |
| `scan_error` | Server → Client | `{stage, error, error_code}` | Error notification |
| `disconnect` | Client → Server | - | Close connection |

### 5.3 External API Integrations

#### OpenFoodFacts API

**Base URL**: `https://world.openfoodfacts.org`

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/api/v2/product/{barcode}.json` | GET | Barcode lookup | < 3s |
| `/cgi/search.pl` | GET | Text search | < 3s |

**Response Handling**:

- Status 200 + product found → Extract data
- Status 200 + product not found → Fallback to search
- Status 404 → Fallback to SearXNG
- Timeout (3s) → Fallback to SearXNG

#### SearXNG Integration (via FastMCP)

**Setup Requirements**:

1. Enable JSON format in SearXNG `settings.yml`:

  ```yaml
  search:
    formats:
      - json```

2. Restart SearXNG service

**MCP Tool Definition**:

```python
@mcp.tool()
def search_nutrition_facts(
  product_name: str,
  max_results: int = 5
) -> List[Dict]:
  """Search web for nutritional information about a food product.

  Args:
    product_name: Name of food product to search
    max_results: Maximum number of results to return

  Returns:
    List of dicts with: {title, url, snippet, nutrition_data}
  """
  # Query SearXNG API
  url = f"http://localhost:8888/search"
  params = {
    "q": f"{product_name} nutrition facts",
    "format": "json",
    "categories": "general",
    "lang": "en"
  }
  response = httpx.get(url, params=params)
  results = response.json()

  # Parse and clean results
  cleaned_results = []
  for result in results['results'][:max_results]:
    # Extract nutrition data from snippet/content
    # Add source citation info
    cleaned_results.append({
      "title": result['title'],
      "url": result['url'],
      "snippet": result['content'][:200],
      "citation_id": None  # Will be assigned by CitationManager
    })
  return cleaned_results
```

**Invocation**: DSPy ReAct agent calls tool when needed during reasoning

#### Ollama API (via DSPy)

**Configuration**:

```python
# Configure local Ollama model
lm = dspy.LM(
  'ollama_chat/qwen3:30b',  # or deepseek-r1:8b, qwen3:8b
  api_base='http://localhost:11434',
  api_key=''  # Not required for local Ollama
)
dspy.configure(lm=lm)
```

**Model Selection Strategy**:

1. **Development**: Use `qwen3:8b` (5.2GB) for fast iteration
2. **Testing**: Use `deepseek-r1:8b` (5.2GB) for reasoning quality checks
3. **Production**: Use `qwen3:30b` (18GB) for best results (if resources allow)

**Usage**: DSPy modules automatically call configured LM

**No OpenAI API costs** - all inference runs locally

---

## 6. Communication Protocols

### 6.1 Client-Server Communication

**Primary Protocol**: WebSocket (Socket.IO)
**Fallback Protocol**: Long Polling (Socket.IO auto-fallback)
**Secondary Protocol**: HTTP/REST (for profile management)

**Why WebSocket for Scanning**:

- Real-time progress updates (barcode → nutrition → scoring → UI)
- Bidirectional communication
- Lower latency than polling
- Persistent connection during multi-stage processing

**Why HTTP for Profiles**:

- Simple request-response pattern
- Infrequent operations
- Cacheable responses

### 6.2 Backend Service Communication

**Pattern**: Direct function calls (same process)

All services run in the same FastAPI process. No inter-process communication needed.

```bash
ScanHandler (async function)
  ├─ await image_processing.process()
  ├─ await nutrition_api.fetch()
  ├─ await scoring.score()
  └─ await ui_generator.generate()
```

### 6.3 External Service Communication

**Protocol**: HTTPS

| Service | Protocol | Client | Timeout |
|---------|----------|--------|---------|
| OpenFoodFacts | HTTPS/REST | `httpx.AsyncClient` | 3s |
| SearXNG | HTTP/REST (local) | FastMCP wrapper | 5s |
| Ollama | HTTP/REST (local) | DSPy wrapper | 30s |

**Error Handling**:

- Network timeout → Fallback to next source
- 4xx/5xx errors → Log + fallback
- Parse errors → Return partial data + low confidence

---

## 7. Processing Flows

### 7.1 User Onboarding Flow

```bash
1. User enters name in LoginForm
   ↓
2. Frontend → POST /api/auth/login {name}
   ↓
3. Backend checks data/profiles/{name}.json exists
   ├─ YES → Return {status: "existing", profile, requires_onboarding: false}
   └─ NO → Return {status: "new", requires_onboarding: true}
   ↓
4. If requires_onboarding:
   Frontend displays OnboardingWizard
   User fills health profile form
   ↓
5. Frontend → POST /api/auth/onboard {name, age, goals, ...}
   ↓
6. Backend:
   a. Validate data (Pydantic)
   b. Calculate daily_targets based on goals
   c. Create UserProfile object
   d. Write to data/profiles/{name}.json (aiofiles)
   ↓
7. Backend → Response {profile, daily_targets}
   ↓
8. Frontend stores profile in localStorage + state
   ↓
9. Navigate to Scan Screen
```

### 7.2 Food Scanning Flow

```bash
1. User clicks "Use Camera" or "Upload Image"
   ↓
2. Frontend:
   Camera: navigator.mediaDevices.getUserMedia() → capture blob
   Upload: File picker → read file
   ↓
3. Frontend → WebSocket connect to /scan namespace
   ↓
4. Frontend → emit("start_scan", {user, image_data, source})
   ↓
5. Backend ScanHandler receives event
   ↓
6. STAGE 1: Image Processing
   emit("scan_progress", {stage: "detecting_barcode", progress: 10})
   ↓
   a. Preprocess image (Pillow: resize, opencv: denoise)
   b. Try barcode detection (pyzbar)
   c. If no barcode: Try OCR (chandra-ocr via transformers)
   ↓
   Result: {barcode: "123456789"} OR {ocr_text: "Product Name"}
   ↓
7. STAGE 2: Nutrition Retrieval
   emit("scan_progress", {stage: "fetching_nutrition", progress: 30})
   ↓
   a. Try OpenFoodFacts barcode API (httpx)
      ├─ Found → Extract nutrition data
      └─ Not found → b
   b. Try OpenFoodFacts text search (httpx)
      ├─ Found → Extract nutrition data
      └─ Not found → c
   c. Try SearXNG search (FastMCP tool)
      ├─ Found → Parse web results
      └─ Not found → Return partial/error
   ↓
   Result: NutritionData object (with confidence score)
   ↓
8. STAGE 3: AI Scoring
   emit("scan_progress", {stage: "analyzing", progress: 60})
   ↓
   a. Load user profile from data/profiles/{user}.json
   b. Check for allergens (auto-fail if found)
   c. Invoke DSPy NutritionScorer module:
      - Input: (nutrition_data, user_profile)
      - DSPy calls OpenAI GPT-4 with ChainOfThought
      - Output: (score, verdict, reasoning, warnings, highlights)
   ↓
   Result: ScoringResult object
   ↓
9. STAGE 4: UI Generation
   emit("scan_progress", {stage: "generating_ui", progress: 85})
   ↓
   a. UISchemaBuilder analyzes verdict:
      - verdict="avoid" → layout="alert", theme="red"
      - verdict="moderate" → layout="balanced", theme="yellow"
      - verdict="good" → layout="encouraging", theme="green"
   b. Assemble component list:
      - Always: verdict_badge, score_display, nutrition_card
      - If warnings: allergen_alert, insight_list (warnings first)
      - If highlights: insight_list (highlights)
      - Always: reasoning_section (collapsible)
   c. Populate component props from ScoringResult
   ↓
   Result: UISchema object
   ↓
10. STAGE 5: Response
    emit("scan_complete", {
      nutrition: NutritionData,
      scoring: ScoringResult,
      ui_schema: UISchema
    })
    ↓
11. Frontend receives scan_complete event
    ↓
12. Frontend DynamicRenderer:
    a. Parse ui_schema
    b. For each component spec:
       - Lookup component in registry
       - Render with props
    c. Display assembled UI
    ↓
13. User sees personalized verdict
```

### 7.3 Error Recovery Flow

```bash
At any stage, if error occurs:
   ↓
Backend: emit("scan_error", {
  stage: current_stage,
  error: error_message,
  error_code: "BARCODE_FAILED" | "PRODUCT_NOT_FOUND" | "API_TIMEOUT" | ...,
  retry_suggestion: "Try better lighting" | "Manual entry" | ...
})
   ↓
Frontend: Display error message + retry button
   ↓
User: Click retry → Restart from stage 1
```

### 7.4 DSPy ReAct Reasoning Flow

```bash
NutritionScorerAgent.forward(nutrition_data, user_profile) called
   ↓
DSPy ReAct internal process:
   1. Serialize inputs to prompt using Signature
      Input schema:
        - nutrition_data: NutritionData (auto-serialized)
        - user_profile: UserProfile (auto-serialized)
      Output schema:
        - score: float (0-10)
        - verdict: "good" | "moderate" | "avoid"
        - reasoning: str (with citations [1], [2])
        - warnings: List[str] (with citations)
        - highlights: List[str] (with citations)
        - citations: List[Citation]
        - confidence: float
   ↓
   2. ReAct Loop (max 5 iterations):
      a. Thought: Analyze current state
         "I need to check if sodium is too high for this user's heart health goal"
      b. Action Decision:
         - Option 1: Call tool (search_nutrition_database, get_health_guidelines, compare_similar_products)
         - Option 2: Finish with answer
      c. If tool call:
         - Execute tool (e.g., get_health_guidelines("sodium", "heart_health"))
         - Tool returns: {"max_daily_mg": 1500, "source": "WHO", "url": "..."}
         - Add to citations via CitationManager
      d. Observation: "WHO recommends max 1500mg sodium for heart health [1]"
      e. Repeat from (a) until confident answer or max iterations
   ↓
   3. Ollama LLM call (local):
      - Model: qwen3:30b (or configured model)
      - API: http://localhost:11434
      - Prompt: Auto-generated by DSPy from Signature + ReAct format
      - Response: Structured JSON matching output schema
      - No API costs, all local inference
   ↓
   4. Citation Processing:
      - Extract all tool call results
      - CitationManager assigns IDs [1], [2], [3]
      - Format reasoning with inline citations
      - Generate reference list
   ↓
   5. Data Quality Check:
      - DataCleanerAgent evaluates input data quality
      - Assigns data_quality_score (0-1)
      - Flags missing/conflicting fields
   ↓
   6. Parse LLM response into Python objects
   ↓
   7. Validate output (Pydantic models)
   ↓
Return ScoringResult (with citations and quality scores)
```

---

## 8. Component Responsibilities Matrix

| Component | Location | Inputs | Outputs | Dependencies | Purpose |
|-----------|----------|--------|---------|--------------|---------|
| **LoginHandler** | `backend/app/api/auth.py` | `LoginRequest` | `LoginResponse` | ProfileStore | Authenticate by name |
| **OnboardingHandler** | `backend/app/api/auth.py` | `OnboardingRequest` | `OnboardingResponse` | ProfileStore, DailyTargetCalculator | Create new profile |
| **ProfileStore** | `backend/app/core/profile_store.py` | Profile name | `UserProfile` | aiofiles, pydantic | JSON file I/O |
| **DailyTargetCalculator** | `backend/app/core/profile_store.py` | UserProfile goals | `DailyTargets` | - | Compute nutritional targets |
| **ScanSessionHandler** | `backend/app/api/scan.py` | WebSocket event | Progress events | All services | Orchestrate scan pipeline |
| **ImagePreprocessor** | `backend/app/services/image_processing.py` | Raw image bytes | Normalized image | Pillow, opencv | Prepare image |
| **BarcodeDetector** | `backend/app/services/image_processing.py` | Preprocessed image | Barcode string | pyzbar | Detect barcode |
| **OCRExtractor** | `backend/app/services/image_processing.py` | Preprocessed image | Text string | chandra-ocr, transformers | Extract label text |
| **OpenFoodFactsClient** | `backend/app/services/nutrition_api.py` | Barcode or query | `NutritionData` | httpx | Query API |
| **SearXNGClient** | `backend/app/services/searxng_client.py` | Product query | Search results | fastmcp | Web search via MCP |
| **DataAggregator** | `backend/app/services/nutrition_api.py` | Multiple sources | Merged data | - | Combine partial data |
| **NutritionNormalizer** | `backend/app/services/nutrition_api.py` | Raw API response | `NutritionData` | pydantic | Standardize schema |
| **DataCleanerAgent** | `backend/app/services/scoring.py` | Raw nutrition data | Cleaned `NutritionData` + quality score | dspy, Ollama | Normalize and validate data |
| **CitationManager** | `backend/app/services/scoring.py` | Source URLs/snippets | Citation list | - | Track sources, assign IDs |
| **AllergenChecker** | `backend/app/services/scoring.py` | Nutrition + Profile | Boolean + warnings | - | Detect allergens |
| **NutritionScorerAgent** | `backend/app/models/dspy_modules.py` | Nutrition + Profile | `ScoringResult` | dspy, Ollama, Tools | ReAct agent reasoning |
| **SummaryGenerator** | `backend/app/models/dspy_modules.py` | ScoringResult | Formatted summary | dspy, Ollama | Generate concise summaries |
| **VerdictGenerator** | `backend/app/services/scoring.py` | Score | Verdict enum | - | Map score to verdict |
| **UISchemaBuilder** | `backend/app/services/ui_generator.py` | `ScoringResult` | `UISchema` | - | Generate UI spec |
| **LayoutSelector** | `backend/app/services/ui_generator.py` | Verdict | Layout type | - | Choose layout |
| **SocketIOManager** | `backend/app/main.py` | FastAPI app | ASGI app | python-socketio | WebSocket server |
| **LoginForm** | `frontend/src/components/auth/LoginForm.jsx` | User input | Name string | - | Capture name |
| **OnboardingWizard** | `frontend/src/components/auth/OnboardingWizard.jsx` | User input | Profile data | shadcn/ui | Multi-step form |
| **CameraCapture** | `frontend/src/components/scan/CameraCapture.jsx` | MediaStream | Image blob | MediaDevices API | Capture photo |
| **ImageUpload** | `frontend/src/components/scan/ImageUpload.jsx` | File input | Image blob | - | Upload file |
| **WebSocketClient** | `frontend/src/lib/websocket.js` | Events | Callbacks | Socket.IO client | Manage connection |
| **ComponentRegistry** | `frontend/src/lib/componentRegistry.js` | Component type | React component | - | Map schema to UI |
| **DynamicRenderer** | `frontend/src/components/verdict/DynamicRenderer.jsx` | `UISchema` | Rendered UI | ComponentRegistry | Render schema |
| **VerdictBadge** | `frontend/src/components/verdict/VerdictBadge.jsx` | Props | Badge UI | shadcn/ui | Display verdict |
| **ScoreDisplay** | `frontend/src/components/verdict/ScoreDisplay.jsx` | Score + max | Score UI | shadcn/ui | Show score |
| **InsightList** | `frontend/src/components/verdict/InsightList.jsx` | Items array | List UI | shadcn/ui | Display highlights |
| **NutritionCard** | `frontend/src/components/verdict/NutritionCard.jsx` | Nutrition data | Card UI | shadcn/ui | Show macros |
| **ReasoningSection** | `frontend/src/components/verdict/ReasoningSection.jsx` | Reasoning text | Collapsible UI | shadcn/ui | Explain score |
| **CitationList** | `frontend/src/components/verdict/CitationList.jsx` | Citations array | Reference list UI | shadcn/ui | Display Perplexity-style references |
| **InlineCitation** | `frontend/src/components/verdict/InlineCitation.jsx` | Citation ID | Clickable [1] link | shadcn/ui | Link to reference |

---

## 9. Technology Stack Mapping

### 9.1 Backend Technologies

| Layer | Technology | Version | Purpose | Configuration |
|-------|-----------|---------|---------|---------------|
| **Web Framework** | FastAPI | ≥0.121.2 | HTTP + WebSocket server | ASGI with uvloop |
| **ASGI Server** | Uvicorn | (via FastAPI) | Production server | `--loop uvloop` |
| **Event Loop** | uvloop | ≥0.22.1 | High-performance async | Auto-configured |
| **Real-time** | python-socketio | ≥5.14.3 | WebSocket communication | ASGIApp wrapper |
| **WebSocket** | websockets | ≥15.0.1 | WS protocol (socketio uses) | Fallback transport |
| **Data Validation** | pydantic | ≥2.12.4 | Model validation | V2 API |
| **HTTP Client** | httpx | ≥0.28.1 | Async API calls | Timeout: 3s |
| **File I/O** | aiofiles | ≥25.1.0 | Async JSON read/write | UTF-8 encoding |
| **Environment** | python-dotenv | ≥1.2.1 | .env file loading | Auto-load on startup |
| **Multipart** | python-multipart | ≥0.0.20 | File upload parsing | FastAPI dependency |
| **AI Framework** | dspy-ai | ≥3.0.4 | LLM orchestration | OpenAI backend |
| **MCP** | fastmcp | ≥2.13.0.2 | Tool integration | Decorator-based |
| **LLM (not used)** | ~~openai~~ | ~~≥2.8.0~~ | ~~GPT-4 API~~ | **Using Ollama instead** |
| **Transformers** | transformers | ≥4.57.1 | Chandra OCR backend | AutoModel loader |
| **LLM Chain** | langchain | ≥1.0.5 | Optional LLM utils | Not core dependency |
| **OCR** | chandra-ocr | ≥0.1.7 | Text extraction | HuggingFace backend |
| **Image Processing** | Pillow | ≥12.0.0 | Image manipulation | Format conversion |
| **Computer Vision** | opencv-python-headless | ≥4.12.0.88 | Image preprocessing | No GUI components |
| **Audio** | openai-whisper | ≥20250625 | STT (future use) | Not used in MVP |
| **Linting** | ruff | ≥0.14.4 | Code quality | Development only |

**Additional (not in requirements.txt but needed)**:

- `pyzbar`: Barcode detection (install separately)

### 9.2 Frontend Technologies

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | React 18+ | UI library |
| **Build Tool** | Vite | Fast dev server + bundler |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **UI Components** | shadcn/ui | Pre-built React components |
| **Real-time** | Socket.IO Client | WebSocket communication |
| **HTTP** | fetch API | REST calls |
| **State** | useState/useContext | Local state management |
| **Routing** | React Router (optional) | Navigation |
| **Camera** | MediaDevices API | Browser camera access |

### 9.3 External Services

| Service | Protocol | Auth | Rate Limit | Fallback |
|---------|----------|------|------------|----------|
| OpenFoodFacts | HTTPS/REST | None | None | SearXNG |
| SearXNG | HTTP/REST (local) | None | None (self-hosted) | Partial data |
| Ollama | HTTP/REST (local) | None | None (local inference) | Rule-based scoring |

### 9.4 Development & Operations

| Tool | Purpose | Configuration |
|------|---------|---------------|
| `ruff` | Linting + formatting | `.ruff.toml` |
| `pytest` | Testing (not in requirements) | Add if needed |
| `docker` | Containerization (optional) | Single container |
| `git` | Version control | Standard workflow |

---

## 10. Data Storage Design

### 10.1 File System Structure

```bash
data/
├── profiles/
│   ├── john.json
│   ├── sarah.json
│   └── mike.json
└── .gitignore  # Ignore all profile data
```

### 10.2 Profile File Schema

**File**: `data/profiles/{name}.json`

**Format**: JSON with UTF-8 encoding

**Schema Version**: Embedded in file for future migrations

```json
{
  "schema_version": "1.0",
  "name": "john",
  "created_at": "2025-11-14T10:30:00Z",
  "updated_at": "2025-11-14T10:30:00Z",
  "age": 35,
  "gender": "male",
  "height_cm": 175.0,
  "weight_kg": 80.0,
  "goals": ["weight_loss", "heart_health"],
  "allergies": ["dairy"],
  "dietary_preferences": ["vegetarian"],
  "nutritional_focus": ["sugar", "calories", "sodium"],
  "daily_targets": {
    "calories": 2000,
    "sugar_g": 25.0,
    "sodium_mg": 1500.0,
    "protein_g": 80.0,
    "carbs_g": 250.0,
    "fat_g": 65.0,
    "fiber_g": 30.0
  }
}
```

### 10.3 File Operations

**Create**:

```bash
1. Validate name (alphanumeric only)
2. Check if file exists → Error if yes
3. Generate profile with defaults
4. Serialize to JSON
5. Write to data/profiles/{name}.json (aiofiles)
6. Fsync to ensure durability
```

**Read**:

```bash
1. Construct path: data/profiles/{name}.json
2. Check file exists → Error if no
3. Read file (aiofiles)
4. Parse JSON
5. Validate against Pydantic model
6. Return UserProfile object
```

**Update**:

```bash
1. Read existing profile
2. Merge updates (partial update)
3. Update updated_at timestamp
4. Validate merged profile
5. Write back to file (atomic write + rename)
```

**No Delete**: Out of scope for MVP

### 10.4 Concurrency Handling

**Issue**: Multiple processes/threads accessing same file

**Solution for MVP**: Single process, async I/O

- All operations in one FastAPI process
- `aiofiles` ensures async but serialized access
- No file locking needed

**Future**: Add file locking (fcntl) or migrate to SQLite

---

## 11. Security Considerations

### 11.1 Authentication

**Current**: Name-only (no password)
**Risk**: Anyone can access any profile by guessing name
**Mitigation for MVP**:

- Local deployment only (not public)
- Educate users: This is demo, not production

**Future**: Add password hashing (bcrypt/argon2)

### 11.2 Input Validation

**All User Inputs Validated**:

- Pydantic models for API requests
- File size limits (10MB for images)
- Name sanitization (alphanumeric only)
- JSON schema validation for profiles

### 11.3 External API Security

**OpenFoodFacts**: Public API, no sensitive data sent
**SearXNG**: Self-hosted, control query content
**OpenAI**: API key in environment, never exposed to client

### 11.4 File System Security

**Profile Data**:

- Stored locally, not exposed via API (except to owner)
- No directory traversal (name validation prevents "../")
- JSON files are world-readable (local deployment only)

**Future**: Encrypt profile files at rest

### 11.5 Client Security

**Image Data**:

- Sent as base64 over WebSocket
- Deleted after processing (not stored)
- No persistent image storage

**XSS Protection**:

- React auto-escapes all rendered content
- shadcn/ui components are safe
- No `dangerouslySetInnerHTML` usage

---

## 12. Performance Targets

### 12.1 Latency Requirements

| Operation | Target | Measurement Point |
|-----------|--------|-------------------|
| Camera activation | < 1s | User click → video stream |
| Barcode detection | < 2s | Image received → barcode decoded |
| Nutrition lookup | < 3s | Barcode → API response |
| DSPy scoring | < 5s | Nutrition data → scoring complete |
| UI generation | < 500ms | Scoring → schema generated |
| Total scan time | < 10s | Image capture → UI displayed |
| Frontend load | < 2s | URL request → interactive |

### 12.2 Throughput Requirements

**MVP**: Single user, sequential scans

- No concurrent scan sessions per user
- One scan at a time per WebSocket connection

**Future**: Multiple users, 10 scans/minute/user

### 12.3 Resource Constraints

**Backend**:

- CPU: 4 cores minimum (async + Ollama inference)
- RAM:
  - With qwen3:30b: 24GB minimum (18GB model + 2GB Chandra + 4GB overhead)
  - With deepseek-r1:8b: 10GB minimum (5.2GB model + 2GB Chandra + 3GB overhead)
  - With qwen3:8b: 10GB minimum (5.2GB model + 2GB Chandra + 3GB overhead)
- GPU: Optional but recommended (reduces inference time 10x)
  - NVIDIA GPU with 8GB+ VRAM for qwen3:8b
  - 16GB+ VRAM for qwen3:30b
- Disk:
  - 100MB for code
  - 18GB for qwen3:30b model
  - 5.2GB for deepseek-r1:8b or qwen3:8b
  - 2GB for Chandra OCR model
  - 1MB per user profile
- Network: Broadband (API calls to OpenFoodFacts, SearXNG)

**Frontend**:

- Modern browser (Chrome/Firefox/Safari)
- Camera access (for camera scanning)
- 1MB JavaScript bundle size target

### 12.4 Scalability Limits (MVP)

**Known Bottlenecks**:

1. **Chandra OCR**: Memory-intensive (transformers model ~2GB RAM)
2. **Ollama LLM**:
   - qwen3:30b requires ~18GB RAM for model + inference
   - deepseek-r1:8b requires ~5.2GB RAM
   - Inference time: 2-10s per request depending on model
   - CPU-only mode is slower (~30-60s)
3. **Local JSON files**: Not suitable for > 1000 users (filesystem I/O)
4. **ReAct iterations**: Multiple tool calls increase latency (5 iterations max)

**Future Optimizations**:

- Cache OpenFoodFacts responses (Redis)
- Optimize Chandra model loading (load once, reuse)
- Migrate to database (SQLite → PostgreSQL)
- Implement Ollama model preloading (reduce cold start)
- Use smaller/quantized models for development (qwen3:8b)
- Batch inference for multiple scans
- GPU acceleration for Ollama (reduces inference to 1-3s)

---

## 13. Error Handling Strategy

### 13.1 Error Categories

| Category | Examples | Response |
|----------|----------|----------|
| **User Error** | Invalid name, missing required fields | 400 + clear message |
| **Not Found** | Profile doesn't exist, product not in DB | 404 + suggestion |
| **External Failure** | API timeout, service unavailable | Fallback + retry |
| **System Error** | File I/O failure, memory error | 500 + generic message |

### 13.2 Fallback Strategy

**Image Processing**:

```bash
Barcode Detection (pyzbar)
  ↓ [no barcode found]
OCR Extraction (chandra)
  ↓ [OCR failed]
Manual Entry (future) or Error
```

**Nutrition Retrieval**:

```bash
OpenFoodFacts Barcode API
  ↓ [404 or timeout]
OpenFoodFacts Text Search
  ↓ [no results]
SearXNG Web Search
  ↓ [no results]
Return partial data + low confidence
```

**Scoring**:

```bash
DSPy with OpenAI
  ↓ [API error]
Retry once (exponential backoff)
  ↓ [still failing]
Fallback to rule-based scoring (hard-coded)
```

### 13.3 Error Response Format

**REST API**:

```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product not found in database",
    "details": "Barcode 123456789 not in OpenFoodFacts",
    "suggestion": "Try manual entry or scan another product"
  }
}
```

**WebSocket**:

```json
{
  "event": "scan_error",
  "payload": {
    "stage": "fetching_nutrition",
    "error": "Product not found",
    "error_code": "PRODUCT_NOT_FOUND",
    "retry_suggestion": "Try better lighting or scan barcode again"
  }
}
```

### 13.4 Logging

**Levels**:

- DEBUG: Internal state, variable values
- INFO: Request received, stage completed
- WARNING: Fallback triggered, low confidence
- ERROR: Exception caught, operation failed

**Log to**: stdout (structured JSON for production)

**Never Log**: API keys, full image data, PII

---

## 14. Testing Strategy (Design)

### 14.1 Unit Testing

**Components to Test**:

- ProfileStore: CRUD operations
- BarcodeDetector: Barcode detection accuracy
- OpenFoodFactsClient: API parsing
- DailyTargetCalculator: Calculation correctness
- UISchemaBuilder: Schema generation logic

**Framework**: pytest (not in requirements, add later)

### 14.2 Integration Testing

**Flows to Test**:

- Onboarding → Profile Creation → Profile Load
- Image Upload → Barcode → Nutrition → Scoring → UI
- Fallback chain: OpenFoodFacts fails → SearXNG succeeds

### 14.3 End-to-End Testing

**Scenarios**:

1. New user: Onboard → Scan → View result
2. Returning user: Login → Scan → View result
3. Allergen detected: Scan → See alert verdict
4. Product not found: Scan → See error + retry

**Tools**: Playwright or Cypress (future)

### 14.4 Performance Testing

**Metrics**:

- Scan latency (p50, p95, p99)
- API response times
- Memory usage during OCR
- Concurrent user capacity

**Tools**: locust or k6 (future)

---

## 15. Deployment Architecture (MVP)

### 15.1 Local Development

**Prerequisites**:

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Pull model: `ollama pull qwen3:8b` (or `deepseek-r1:8b`, `qwen3:30b`)
3. Verify Ollama: `ollama list` should show the model
4. Install SearXNG (Docker):

  ```bash

  docker run -d -p 8888:8080 \
    -v $(pwd)/searxng:/etc/searxng \
    searxng/searxng```

5. Enable JSON in SearXNG settings.yml (see section 5.3)

**Backend**:

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyzbar  # Not in requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev  # Vite dev server on port 5173
```

**Environment Variables** (`.env`):

```bash
# Ollama Configuration
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_MODEL=qwen3:30b  # or deepseek-r1:8b, qwen3:8b

# SearXNG Configuration
SEARXNG_URL=http://localhost:8888
SEARXNG_API_BASE=http://localhost:8888

# Application Settings
PROFILES_DIR=./data/profiles
LOG_LEVEL=INFO
DEBUG=False

# No OPENAI_API_KEY needed - using local Ollama
```

### 15.2 Production (Future)

**Backend Container**:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt pyzbar
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend**: Static build deployed to CDN or served by FastAPI

**Database Migration**: SQLite first, then PostgreSQL

---

## 16. Monitoring & Observability (Future)

### 16.1 Metrics to Track

- Request rate (scans/minute)
- Latency (p50, p95, p99)
- Error rate by stage
- Fallback trigger frequency
- OpenAI API cost per scan
- Cache hit rate (future)

### 16.2 Logging

**Structured Logging**:

```json
{
  "timestamp": "2025-11-14T10:30:00Z",
  "level": "INFO",
  "stage": "nutrition_retrieval",
  "user": "john",
  "barcode": "123456789",
  "source": "openfoodfacts",
  "latency_ms": 234,
  "confidence": 0.95
}
```

### 16.3 Alerting (Future)

- Error rate > 5%
- p95 latency > 15s
- OpenAI API failures
- Disk space < 10%

---

## 17. Open Design Questions

### 17.1 DSPy Optimization

**Question**: Should we use DSPy teleprompters (optimizers) to improve prompts?

**Options**:

1. Start with basic ChainOfThought, no optimization
2. Collect few-shot examples, run BootstrapFewShot optimizer
3. Create labeled dataset, use MIPRO optimizer

**Recommendation**: Start with option 1, add optimization in v0.2

### 17.2 Image Storage

**Question**: Should we store scanned images?

**Options**:

1. Delete immediately after processing (current design)
2. Store temporarily for retry (in-memory cache)
3. Store permanently for history (disk/S3)

**Recommendation**: Option 1 for MVP (privacy + storage)

### 17.3 Barcode Library

**Question**: pyzbar requires system dependencies. Alternatives?

**Options**:

1. pyzbar (current) - Requires zbar C library
2. python-barcode - Pure Python, may be slower
3. Google ML Kit via API - Cloud dependency

**Recommendation**: pyzbar (best accuracy)

### 17.4 SearXNG Deployment

**Question**: How to deploy SearXNG for MVP?

**Options**:

1. Use public instance (searx.be, etc.)
2. Self-host with Docker
3. Skip SearXNG, rely only on OpenFoodFacts

**Recommendation**: Option 2 (Docker Compose with FastAPI)

---

## 18. Future Enhancements (Post-MVP)

### 18.1 Version 0.2 Features

- Scan history (JSON log file per user)
- Profile editing UI
- Manual product entry
- Barcode response cache (Redis)
- Better error messages with recovery flows

### 18.2 Version 0.3 Features

- SQLite database migration
- Simple password authentication
- Export scan history (CSV)
- Improved UI animations
- Dark mode

### 18.3 Version 1.0 Features

- PostgreSQL database
- TTS verdicts (IndexTTS2)
- STT commands (Whisper)
- Multi-device sync
- Mobile native apps (React Native)
- Advanced analytics

---

## 19. Conclusion

This HLD defines a modular, scalable architecture for Bytelense MVP. Key design decisions:

1. **Async-first**: All I/O is non-blocking (httpx, aiofiles, WebSocket)
2. **Fallback chains**: Graceful degradation at each layer
3. **Declarative AI**: DSPy signatures > prompt strings
4. **Schema-driven UI**: Backend controls presentation
5. **Local storage**: JSON files for rapid development

The architecture supports the 6-hour development timeline while maintaining extensibility for future features.

**Next Step**: Begin implementation following this design.

---

## Appendix: Key Design Updates (Latest Revision)

### A.1 LLM Backend Change: OpenAI → Ollama

**Original**: OpenAI GPT-4 via `dspy.OpenAI()`
**Updated**: Local Ollama models via `dspy.LM('ollama_chat/{model}')`

**Rationale**:

- No API costs (free local inference)
- Privacy (data never leaves machine)
- No rate limits
- Faster iteration during development

**Model Recommendations** (from `ollama list`):

1. **qwen3:30b** (18GB) - Best reasoning for production
2. **deepseek-r1:8b** (5.2GB) - Good reasoning, lower resources
3. **qwen3:8b** (5.2GB) - Balanced for development

**Configuration**:

```python
lm = dspy.LM('ollama_chat/qwen3:30b', api_base='http://localhost:11434', api_key='')
dspy.configure(lm=lm)
```

### A.2 Agent Architecture Change: ChainOfThought → ReAct

**Original**: `dspy.ChainOfThought(signature)`
**Updated**: `dspy.ReAct(signature, tools=[...])`

**Rationale**:

- ReAct enables tool use (search_nutrition_database, get_health_guidelines, compare_similar_products)
- Iterative reasoning → action → observation loop
- Better for multi-source data retrieval
- Aligns with agentic paradigm

**Tools Available to Agent**:

1. `search_nutrition_database()` - Query OpenFoodFacts + SearXNG
2. `compare_similar_products()` - Find comparisons for context
3. `get_health_guidelines()` - Fetch WHO/FDA guidelines with citations

### A.3 New Subsystem: Data Cleaning & Citations

**Added Components**:

- **DataCleanerAgent**: Normalizes messy data from multiple sources
- **CitationManager**: Tracks sources, assigns IDs, formats Perplexity-style references
- **SummaryGenerator**: Condenses data for optimal user presentation

**Citation Format** (inspired by Perplexity):

- Inline citations: "High sodium [1] exceeds limit [2]"
- Reference list at bottom with:
  - `[1]` OpenFoodFacts - Product Database
  - `[2]` WHO - Sodium Guidelines
  - Clickable links to sources
  - Relevant snippet excerpts

**Data Quality Scoring**:

- Each data source gets authority_score (0-1)
- Conflicting data flagged and resolved
- Missing fields estimated or marked as "N/A"
- Overall data_quality_score (0-1) affects confidence

### A.4 SearXNG Integration Details

**API Endpoint**: `http://localhost:8888/search?q={query}&format=json`

**Setup Requirement**:

```yaml
# settings.yml
search:
  formats:
    - json  # Enable JSON format (disabled by default)
```

**MCP Tool Integration**:

```python
@mcp.tool()
def search_nutrition_facts(product_name: str, max_results: int = 5) -> List[Dict]:
  """FastMCP tool for SearXNG integration"""
  # Returns: {title, url, snippet, citation_id}
```

**Invocation**: DSPy ReAct agent calls tool when OpenFoodFacts fails

### A.5 Resource Requirements Updated

**Significant Changes**:

- RAM: 10GB → 24GB (depending on model choice)
- GPU: Optional → Recommended (10x speedup)
- Disk: 100MB → 20GB+ (includes models)
- CPU: 2 cores → 4 cores (Ollama inference)

**Performance Impact**:

- Inference time: 2-10s with GPU, 30-60s CPU-only
- Model cold start: ~2s (can be preloaded)
- ReAct iterations: 5 max (balances quality vs speed)

### A.6 New UI Components for Citations

**Added**:

- `citation_list`: Reference list component (bottom of verdict)
- `inline_citation`: Clickable [1] links in text

**Behavior**:

- Click [1] → Scroll to reference + highlight
- Hover [1] → Show tooltip with source title
- Mobile-friendly: Tap to view, swipe to dismiss

### A.7 Deployment Prerequisites

**New Requirements**:

1. Ollama installed locally
2. Model pulled (qwen3:30b or alternatives)
3. SearXNG running via Docker
4. JSON format enabled in SearXNG

**No Longer Required**:

- OpenAI API key
- Cloud API access
- Payment/billing setup

### A.8 Development Recommendations

**Model Selection by Phase**:

- **Hour 1-3**: Use `qwen3:8b` (fast iteration, 5.2GB)
- **Hour 4-5**: Switch to `deepseek-r1:8b` (better reasoning, 5.2GB)
- **Hour 6+**: Use `qwen3:30b` if resources allow (best quality, 18GB)

**Fallback Strategy**:

- If Ollama fails → Rule-based scoring (no AI)
- If SearXNG fails → OpenFoodFacts only
- If both fail → Partial data with low confidence

### A.9 Emphasis on Data Quality

**New Focus Areas**:

1. **Cleaning Pipeline**: Normalize units, resolve conflicts, estimate missing values
2. **Source Authority**: Rank sources by credibility (manufacturer > USDA > crowd)
3. **Confidence Scoring**: Transparent about data quality and uncertainty
4. **Citation Tracking**: Every claim backed by source (like Perplexity)
5. **Summary Formation**: Agent decides what to show vs link as reference

**Example**:

- Show: Top 3 highlights with citations
- Link as reference: Full ingredient list, detailed micronutrients
- User can expand to see full data + reasoning steps

---

## Summary of Core Improvements

1. ✅ **Local-first AI**: Ollama instead of OpenAI (privacy + cost)
2. ✅ **Agentic Reasoning**: ReAct with tools instead of simple ChainOfThought
3. ✅ **Data Quality**: Cleaning, normalization, conflict resolution
4. ✅ **Citations**: Perplexity-style inline references with clickable links
5. ✅ **SearXNG Integration**: Proper API setup and MCP tool definition
6. ✅ **Resource Planning**: Realistic RAM/GPU requirements for local LLMs

**This HLD is now ready for 6-hour implementation with proper library usage.**
