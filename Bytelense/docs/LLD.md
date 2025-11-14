# Bytelense - Low-Level Design Document

**Version:** 2.0 (Enhanced with Conversational Onboarding, History Tracking, and Intelligent Search)
**Last Updated:** 2025-11-14
**Status:** Detailed Implementation Specification

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Data Models](#2-data-models)
3. [Enhanced User Onboarding System](#3-enhanced-user-onboarding-system)
4. [User Health Modeling Engine](#4-user-health-modeling-engine)
5. [Enhanced OCR Processing Pipeline](#5-enhanced-ocr-processing-pipeline)
6. [SearXNG ReAct "Intern" Agent](#6-searxng-react-intern-agent)
7. [Food History Tracking System](#7-food-history-tracking-system)
8. [Context-Aware Scoring Engine](#8-context-aware-scoring-engine)
9. [Assessment Generation System](#9-assessment-generation-system)
10. [API Contracts](#10-api-contracts)
11. [Async Flow Diagrams](#11-async-flow-diagrams)
12. [Module Decoupling Strategy](#12-module-decoupling-strategy)
13. [Threading & Concurrency](#13-threading--concurrency-patterns)
14. [Function-Level Specifications](#14-function-level-specifications)

---

## 1. System Architecture Overview

### 1.1 Core Principle: Modular Independence

**Design Philosophy**: Every module can function as a standalone service. If any component fails, others continue to operate with graceful degradation.

```bash
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│         (React + Vite + shadcn/ui + Socket.IO Client)           │
└─────────────────────────┬───────────────────────────────────────┘
                          │ WebSocket + HTTP
┌─────────────────────────┴───────────────────────────────────────┐
│                      GATEWAY LAYER                              │
│              (FastAPI + python-socketio)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Router       │  WebSocket Handler  │  Auth Handler  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────────┐
│                      SERVICE LAYER                              │
│  ┌─────────────────┬────────────────┬──────────────────────┐    │
│  │ Onboarding      │ OCR Pipeline   │ Scoring Engine       │    │
│  │ Conversation    │ Enhancement    │ (Context-Aware)      │    │
│  │ Engine          │                │                      │    │
│  ├─────────────────┼────────────────┼──────────────────────┤    │
│  │ Health          │ Search Intern  │ History Tracker      │    │
│  │ Modeling        │ Agent          │                      │    │
│  │ (BMI/BMR/TDEE)  │ (ReAct)        │                      │    │
│  └─────────────────┴────────────────┴──────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────────┐
│                   AGENT LAYER (DSPy + Ollama)                   │
│  ┌─────────────────┬────────────────┬──────────────────────┐    │
│  │ Conversational  │ Search Intern  │ Data Extraction      │    │
│  │ Elicitation     │ ReAct Agent    │ Agent                │    │
│  │ Agent           │                │                      │    │
│  └─────────────────┴────────────────┴──────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────────┐
│                    INTEGRATION LAYER                            │
│  ┌─────────────────┬────────────────┬──────────────────────┐    │
│  │ OpenFoodFacts   │ SearXNG        │ Ollama LLM           │    │
│  │ API Client      │ Multi-Query    │ (qwen3:30b)          │    │
│  │                 │ Engine         │                      │    │
│  └─────────────────┴────────────────┴──────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────────┐
│                       DATA LAYER                                │
│  ┌─────────────────┬────────────────┬──────────────────────┐    │
│  │ User Profiles   │ Scan History   │ Conversation State   │    │
│  │ (JSON)          │ (JSON)         │ (In-Memory)          │    │
│  └─────────────────┴────────────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Module Independence Matrix

| Module | Dependencies | Can Run Standalone | Fallback Mode |
|--------|-------------|-------------------|---------------|
| **ConversationalOnboarding** | DSPy, Ollama | ✅ Yes | Simple forms |
| **HealthModeling** | User data | ✅ Yes | Default formulas |
| **OCREnhancement** | Chandra, DSPy | ✅ Yes | Raw OCR text |
| **SearchInternAgent** | SearXNG, DSPy | ✅ Yes | Direct search |
| **HistoryTracker** | User profile | ✅ Yes | No history |
| **ContextScoring** | History, Profile | ✅ Yes | Simple rules |
| **AssessmentGenerator** | Scoring results | ✅ Yes | Template-based |

---

## 2. Data Models

### 2.1 Enhanced User Profile Model

**File**: `backend/app/models/schemas.py`

```python
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator


class LifestyleHabits(BaseModel):
    """Detailed lifestyle information for accurate health modeling."""

    # Sleep patterns
    avg_sleep_hours: float = Field(ge=0, le=24)
    sleep_quality: Literal["poor", "fair", "good", "excellent"] = "fair"

    # Work & activity
    work_style: Literal[
        "sedentary_desk",        # Office worker, mostly sitting
        "light_activity",        # Teacher, retail, some walking
        "moderate_activity",     # Healthcare, warehouse, regular movement
        "heavy_labor"           # Construction, manual labor
    ] = "sedentary_desk"

    daily_commute_minutes: int = Field(ge=0, le=300, default=0)
    commute_type: Literal["walking", "cycling", "driving", "public_transport"] = "driving"

    # Exercise habits
    exercise_type: List[Literal[
        "gym", "cycling", "swimming", "running",
        "yoga", "walking", "sports", "none"
    ]] = Field(default_factory=list)
    exercise_frequency_per_week: int = Field(ge=0, le=21, default=0)  # max 3x/day
    exercise_duration_minutes: int = Field(ge=0, le=300, default=0)

    # Habits
    smoking: Literal["never", "former", "occasional", "regular"] = "never"
    alcohol: Literal["never", "rare", "moderate", "heavy"] = "never"

    # Additional factors
    stress_level: Literal["low", "moderate", "high", "very_high"] = "moderate"
    water_intake_liters: float = Field(ge=0, le=10, default=2.0)


class FoodPreferences(BaseModel):
    """Food preferences for conversational context."""

    favorite_foods: List[str] = Field(default_factory=list, max_items=20)
    disliked_foods: List[str] = Field(default_factory=list, max_items=20)
    cuisine_preferences: List[str] = Field(default_factory=list)
    snacking_habits: Literal["never", "rare", "moderate", "frequent"] = "moderate"


class HealthMetrics(BaseModel):
    """Calculated health metrics based on user data."""

    bmi: float = Field(ge=10, le=50)
    bmi_category: Literal[
        "underweight", "normal", "overweight",
        "obese_class_1", "obese_class_2", "obese_class_3"
    ]

    bmr: float  # Basal Metabolic Rate (calories/day)
    bmr_formula: Literal["mifflin_st_jeor", "harris_benedict"] = "mifflin_st_jeor"

    tdee: float  # Total Daily Energy Expenditure (calories/day)
    activity_multiplier: float = Field(ge=1.2, le=2.5)

    energy_budget: float  # TDEE adjusted for goals (+/- calories)

    # Health risk flags
    health_risks: List[Literal[
        "diabetes_risk", "cardiovascular_risk", "hypertension_risk",
        "obesity_risk", "malnutrition_risk", "none"
    ]] = Field(default_factory=list)

    calculated_at: datetime = Field(default_factory=datetime.now)


class EnhancedUserProfile(BaseModel):
    """Complete user profile with health modeling."""

    # Basic info
    name: str
    created_at: datetime
    updated_at: datetime

    # Demographics
    age: Optional[int] = Field(None, ge=0, le=150)
    biological_gender: Literal["male", "female", "other"] = "other"
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=20, le=500)

    # Lifestyle
    lifestyle: LifestyleHabits
    food_preferences: FoodPreferences

    # Health goals & restrictions
    goals: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    nutritional_focus: List[str] = Field(default_factory=list)

    # Calculated metrics
    health_metrics: Optional[HealthMetrics] = None

    # Daily targets (calculated from goals & metrics)
    daily_targets: Dict[str, float] = Field(default_factory=dict)

    # Onboarding state
    onboarding_completed: bool = False
    onboarding_progress: float = Field(ge=0, le=1, default=0.0)

    @validator('biological_gender')
    def validate_gender(cls, v):
        """Accept common variations."""
        if v.lower() in ['m', 'male', 'man']:
            return 'male'
        elif v.lower() in ['f', 'female', 'woman']:
            return 'female'
        return 'other'
```

### 2.2 Scan History Models

**File**: `backend/app/models/schemas.py`

```python
class FoodScanRecord(BaseModel):
    """Single food scan record."""

    scan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_name: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # Scanned data
    product_name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None

    # Nutritional info
    serving_size: str
    servings_consumed: float = 1.0  # User can specify

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sugar_g: float
    sodium_mg: float
    fiber_g: Optional[float] = None

    # Contextual info
    time_of_day: Literal["morning", "afternoon", "evening", "night"]
    meal_type: Optional[Literal["breakfast", "lunch", "dinner", "snack"]] = None

    # Scoring result
    score: float
    verdict: Literal["good", "moderate", "avoid"]

    # Moderation tracking
    moderation_level: Literal["within", "approaching", "exceeding"] = "within"


class DailySummary(BaseModel):
    """Daily consumption summary."""

    date: str  # YYYY-MM-DD
    user_name: str

    scans: List[FoodScanRecord] = Field(default_factory=list)

    # Totals
    total_calories: float = 0.0
    total_protein_g: float = 0.0
    total_carbs_g: float = 0.0
    total_fat_g: float = 0.0
    total_sugar_g: float = 0.0
    total_sodium_mg: float = 0.0
    total_fiber_g: float = 0.0

    # vs Targets
    calories_vs_target: float = 0.0  # Percentage
    protein_vs_target: float = 0.0
    sugar_vs_target: float = 0.0
    sodium_vs_target: float = 0.0

    # Moderation flags
    exceeded_sugar: bool = False
    exceeded_sodium: bool = False
    exceeded_calories: bool = False


class WeeklySummary(BaseModel):
    """Weekly consumption patterns."""

    week_start: str  # YYYY-MM-DD
    user_name: str

    daily_summaries: List[DailySummary] = Field(default_factory=list)

    # Weekly averages
    avg_daily_calories: float = 0.0
    avg_daily_sugar_g: float = 0.0
    avg_daily_sodium_mg: float = 0.0

    # Patterns
    most_scanned_products: List[Dict[str, Any]] = Field(default_factory=list)
    most_common_meal_time: Literal["morning", "afternoon", "evening", "night"] = "afternoon"

    # Compliance
    days_within_targets: int = 0
    moderation_score: float = Field(ge=0, le=10)  # How well user stayed within limits
```

### 2.3 Enhanced OCR Result Models

**File**: `backend/app/models/schemas.py`

```python
class RawOCRExtraction(BaseModel):
    """Raw text extracted by Chandra OCR."""

    full_text: str
    confidence: float
    processing_time_ms: int

    # Detected regions (if OCR provides)
    text_blocks: List[Dict[str, Any]] = Field(default_factory=list)


class StructuredNutritionExtraction(BaseModel):
    """Structured data extracted from OCR text via DSPy."""

    # Product identification
    product_name: Optional[str] = None
    brand: Optional[str] = None

    # Package size/price hints (for market search)
    package_indicators: List[str] = Field(default_factory=list)  # ["20 Rs", "40g", "500ml"]

    # Nutritional info (per unit)
    nutrients_per_100g: Dict[str, float] = Field(default_factory=dict)
    nutrients_per_serving: Dict[str, float] = Field(default_factory=dict)
    serving_size: Optional[str] = None

    # Total package
    net_quantity: Optional[str] = None
    net_quantity_value: Optional[float] = None
    net_quantity_unit: Optional[Literal["g", "kg", "ml", "l"]] = None

    # Ingredients
    ingredients: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)

    # Extraction confidence
    extraction_quality: Literal["complete", "partial", "poor"] = "partial"
    missing_fields: List[str] = Field(default_factory=list)

    # Source
    extraction_method: Literal["dspy_structured", "regex_patterns", "llm_fallback"]


class ProductSizeEstimate(BaseModel):
    """Market-based size/price estimation from SearXNG."""

    product_name: str
    brand: Optional[str] = None

    # Found variants
    available_sizes: List[Dict[str, Any]] = Field(default_factory=list)
    # Example: [{"price": "₹20", "size": "40g"}, {"price": "₹40", "size": "80g"}]

    # Best match
    estimated_size: Optional[str] = None
    estimated_price: Optional[str] = None

    confidence: float = Field(ge=0, le=1)
    source_urls: List[str] = Field(default_factory=list)
```

### 2.4 Search Intern Agent Models

**File**: `backend/app/models/schemas.py`

```python
class SearchQuery(BaseModel):
    """Single search query generated by intern agent."""

    query_text: str
    query_type: Literal[
        "exact_product", "size_variant", "price_variant",
        "nutrition_facts", "ingredients", "similar_products"
    ]
    search_engine: Literal["searxng", "openfoodfacts"]

    # Query variations
    keywords: List[str]
    must_include: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Single search result."""

    url: str
    title: str
    snippet: str
    source_domain: str
    relevance_score: float = Field(ge=0, le=1)

    # Extracted structured data (if available)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)


class InternAgentReport(BaseModel):
    """Complete report from Search Intern Agent."""

    task: str  # What was being searched

    # Queries executed
    queries_executed: List[SearchQuery] = Field(default_factory=list)
    total_queries: int = 0

    # Results
    all_results: List[SearchResult] = Field(default_factory=list)
    filtered_results: List[SearchResult] = Field(default_factory=list)

    # Aggregated findings
    summary: str  # Natural language summary
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)

    # Source tracking
    sources: List[Dict[str, str]] = Field(default_factory=list)
    # [{"url": "...", "title": "...", "snippet": "..."}]

    # Performance
    total_time_seconds: float
    queries_per_second: float
```

### 2.5 Assessment Models

**File**: `backend/app/models/schemas.py`

```python
class DetailedAssessment(BaseModel):
    """Complete detailed assessment for internal use."""

    # Product info
    product_name: str
    brand: Optional[str] = None

    # User context
    user_name: str
    consumption_context: Dict[str, Any]  # Time, history, moderation level

    # Scoring
    base_score: float  # Nutritional score alone
    context_adjusted_score: float  # After history/time consideration
    final_score: float
    verdict: Literal["good", "moderate", "avoid"]

    # Detailed breakdown
    nutrient_analysis: Dict[str, Dict[str, Any]]
    # {"sugar": {"value": 30, "target": 25, "percentage": 120, "assessment": "high"}}

    allergen_flags: List[str] = Field(default_factory=list)

    # Reasoning
    reasoning_steps: List[str] = Field(default_factory=list)
    scientific_rationale: str

    # Context factors
    moderation_impact: str  # How history affected score
    time_of_day_impact: str

    # Warnings & highlights
    critical_warnings: List[str] = Field(default_factory=list)
    moderate_warnings: List[str] = Field(default_factory=list)
    positive_highlights: List[str] = Field(default_factory=list)

    # Citations
    citations: List[Citation] = Field(default_factory=list)

    # Recommendations
    alternatives: List[str] = Field(default_factory=list)
    timing_recommendations: str
    portion_recommendations: str


class ShortAssessment(BaseModel):
    """Condensed assessment for UI display."""

    score: float
    verdict: Literal["good", "moderate", "avoid"]

    # Simplified messaging
    headline: str  # "Great choice for your goals!" or "Not recommended right now"
    summary: str   # 2-3 sentences

    # Top 3 insights
    key_insights: List[str] = Field(max_items=3)

    # Top 2 warnings (if any)
    warnings: List[str] = Field(max_items=2, default_factory=list)

    # Simple recommendation
    action_item: str  # "Enjoy in moderation" or "Consider alternatives"
```

---

## 3. Enhanced User Onboarding System

### 3.1 Overview

The onboarding system uses **conversational elicitation** techniques inspired by intelligence gathering (adapted civilly) to collect detailed user information without feeling intrusive.

**Core Principles**:

1. **OARS Framework**: Open-ended questions, Affirmations, Reflections, Summaries
2. **Reciprocity**: Share relevant information to encourage user sharing
3. **Autonomy Preservation**: Users feel in control, can skip questions
4. **Progressive Disclosure**: Start broad, get specific naturally

### 3.2 Conversational Question Bank

**File**: `backend/app/services/onboarding/question_bank.py`

```python
"""
Pre-written questions with 3-4 variations for natural conversation flow.
"""

from typing import List, Dict
from enum import Enum


class QuestionCategory(Enum):
    ICEBREAKER = "icebreaker"
    DEMOGRAPHICS = "demographics"
    LIFESTYLE_SLEEP = "lifestyle_sleep"
    LIFESTYLE_WORK = "lifestyle_work"
    LIFESTYLE_EXERCISE = "lifestyle_exercise"
    LIFESTYLE_HABITS = "lifestyle_habits"
    HEALTH_GOALS = "health_goals"
    FOOD_PREFERENCES = "food_preferences"
    DIETARY_RESTRICTIONS = "dietary_restrictions"
    VALIDATION = "validation"


class QuestionBank:
    """Stores question variations for conversational onboarding."""

    QUESTIONS = {
        QuestionCategory.ICEBREAKER: {
            "goal": "Establish rapport, understand primary motivation",
            "variations": [
                "What brings you to Bytelense today? 😊",
                "I'd love to help you make better food choices! What's your main health focus right now?",
                "Let's start simple - what made you interested in tracking your nutrition?"
            ],
            "follow_ups": [
                "That's a great goal! Many people find {goal} challenging. What's been your biggest obstacle so far?",
                "I appreciate you sharing that. Have you tried any approaches to {goal} before?"
            ]
        },

        QuestionCategory.DEMOGRAPHICS: {
            "age": {
                "goal": "Calculate BMR accurately",
                "variations": [
                    "Mind sharing your age? This helps me give you more personalized recommendations.",
                    "What age range are you in? (Don't worry, this stays private! 🔒)",
                    "Just for context - how old are you? This affects your daily energy needs."
                ],
                "justification": "Age affects your basal metabolic rate - basically, how many calories your body burns at rest."
            },
            "gender": {
                "goal": "BMR formula selection",
                "variations": [
                    "What's your biological gender? (This affects metabolism calculations)",
                    "For accurate metabolic calculations, I'll need to know your biological sex. Male, female, or prefer not to say?",
                    "Just for the math - what's your biological gender assigned at birth?"
                ],
                "justification": "Men and women have different metabolic rates due to hormonal and body composition differences."
            },
            "height_weight": {
                "goal": "BMI, BMR, TDEE calculation",
                "variations": [
                    "Could you share your height and current weight? (All data stays on your device! 📱)",
                    "Let's talk numbers - what's your height and weight? This helps calculate your daily calorie needs.",
                    "To personalize everything, I'll need your height and weight. What are they?"
                ],
                "justification": "These help calculate your BMI (Body Mass Index) and daily calorie needs.",
                "optional_note": "If you're not comfortable sharing, we can use general guidelines instead. 😊"
            }
        },

        QuestionCategory.LIFESTYLE_SLEEP: {
            "goal": "Understand energy patterns, stress indicators",
            "sleep_hours": {
                "variations": [
                    "How much sleep do you typically get per night?",
                    "On average, how many hours are you sleeping these days?",
                    "Let's talk sleep - how many hours per night do you usually get?"
                ],
                "follow_ups": [
                    "{{if < 6}} That's on the lower side! Poor sleep can affect cravings and metabolism. Have you noticed that?",
                    "{{if 7-9}} That's solid! Good sleep helps with healthy eating decisions.",
                    "{{if > 9}} Interesting! Are you catching up on sleep debt, or is this your normal?"
                ]
            },
            "sleep_quality": {
                "variations": [
                    "How would you rate your sleep quality - poor, fair, good, or excellent?",
                    "Do you feel rested when you wake up? Would you say your sleep quality is good?",
                    "On a scale from poor to excellent, how's your sleep quality?"
                ],
                "elicitation_note": "Low sleep quality → higher stress → potential emotional eating pattern"
            }
        },

        QuestionCategory.LIFESTYLE_WORK: {
            "goal": "Calculate activity multiplier for TDEE",
            "work_style": {
                "variations": [
                    "What's your work day like? Mostly sitting, or do you move around a lot?",
                    "Tell me about your typical workday - desk job, or more active?",
                    "How would you describe your work: sedentary, lightly active, or heavy labor?"
                ],
                "options": {
                    "sedentary_desk": "Desk job, mostly sitting",
                    "light_activity": "Some walking, light movement",
                    "moderate_activity": "Regular physical activity",
                    "heavy_labor": "Manual labor, very active"
                },
                "follow_ups": [
                    "{{if sedentary}} Got it. Do you take breaks to stretch or walk during the day?",
                    "{{if heavy_labor}} That's intense! Your body needs more fuel. Do you eat more on work days?"
                ]
            },
            "commute": {
                "variations": [
                    "How do you get to work, and how long does it take?",
                    "What's your commute like - walking, driving, public transport?",
                    "Do you have a daily commute? If so, how long and what mode?"
                ],
                "elicitation_note": "Walking/cycling commute → bump up activity level"
            }
        },

        QuestionCategory.LIFESTYLE_EXERCISE: {
            "goal": "Fine-tune TDEE with exercise patterns",
            "exercise_type": {
                "variations": [
                    "Do you exercise regularly? What kind of activities do you enjoy?",
                    "Are you hitting the gym, going for runs, or doing any sports?",
                    "What does your exercise routine look like these days?"
                ],
                "affirmations": {
                    "active": "That's awesome! Regular exercise makes a huge difference. 💪",
                    "none": "No worries! Even small changes in nutrition can have big impacts."
                }
            },
            "frequency": {
                "variations": [
                    "How often do you work out per week?",
                    "On a typical week, how many days are you exercising?",
                    "What's your weekly exercise frequency look like?"
                ],
                "follow_ups": [
                    "{{if 0-1}} Even light activity helps! Have you thought about walking more?",
                    "{{if 3-5}} Solid routine! That definitely affects your calorie needs.",
                    "{{if > 5}} Wow, that's commitment! You're definitely in the active category."
                ]
            },
            "duration": {
                "variations": [
                    "How long are your typical workout sessions?",
                    "When you exercise, how many minutes do you usually go for?",
                    "What's the duration of your workouts - 30 minutes, an hour, more?"
                ]
            }
        },

        QuestionCategory.LIFESTYLE_HABITS: {
            "goal": "Identify health risks, adjust recommendations",
            "smoking": {
                "variations": [
                    "Do you smoke? (No judgment - just helps with health recommendations)",
                    "Are you a smoker, or have you quit, or never smoked?",
                    "What's your smoking status? Never, former, occasional, or regular?"
                ],
                "autonomy_note": "You can skip any question you're not comfortable with.",
                "follow_ups": [
                    "{{if former}} That's great that you quit! How long ago?",
                    "{{if regular}} I understand. This affects metabolism and vitamin needs."
                ]
            },
            "alcohol": {
                "variations": [
                    "How often do you drink alcohol? Never, rarely, moderately, or frequently?",
                    "Do you consume alcohol? If so, how often?",
                    "What's your relationship with alcohol - never, social drinker, regular?"
                ],
                "elicitation_note": "Alcohol = empty calories, affects food choices, liver load"
            },
            "stress": {
                "variations": [
                    "On a scale from low to very high, how stressed would you say you are lately?",
                    "How are your stress levels these days?",
                    "Do you feel stressed often - low, moderate, high, or very high?"
                ],
                "reflection": [
                    "{{if high/very_high}} I hear you. Stress can really affect eating patterns. Have you noticed that?",
                    "{{if low/moderate}} That's good to hear! Lower stress helps with mindful eating."
                ]
            }
        },

        QuestionCategory.FOOD_PREFERENCES: {
            "goal": "Build rapport, personalize recommendations",
            "favorites": {
                "variations": [
                    "What are some of your favorite foods? (No wrong answers! 😊)",
                    "If you could eat anything right now, what would it be?",
                    "What foods do you absolutely love?"
                ],
                "affirmations": [
                    "Great choices! There's always room for foods you enjoy.",
                    "I love that you know what you like! Let's make sure you can still enjoy those."
                ],
                "follow_ups": [
                    "What is it about {food} that you love? Taste, texture, memories?",
                    "Do you eat {food} often, or is it more of a treat?"
                ]
            },
            "dislikes": {
                "variations": [
                    "On the flip side, any foods you really don't like?",
                    "Are there foods you avoid just because you don't like them?",
                    "What foods are an absolute no for you?"
                ],
                "reciprocity_note": "Many people dislike certain textures or tastes - totally normal!"
            }
        },

        QuestionCategory.HEALTH_GOALS: {
            "goal": "Set clear targets, adjust calorie/macro recommendations",
            "primary_goals": {
                "variations": [
                    "What are your main health goals right now? You can select multiple.",
                    "Let's talk about what you want to achieve. What's most important to you?",
                    "What brings you here - weight loss, muscle gain, managing a condition, or general health?"
                ],
                "options": {
                    "weight_loss": "Lose weight",
                    "weight_gain": "Gain weight",
                    "muscle_building": "Build muscle",
                    "diabetes_management": "Manage diabetes/blood sugar",
                    "heart_health": "Improve heart health",
                    "energy_levels": "Boost energy",
                    "general_wellness": "Just be healthier overall"
                },
                "summary": [
                    "So your top goals are: {goals}. That's clear and actionable! Let's build your plan around these."
                ]
            }
        },

        QuestionCategory.DIETARY_RESTRICTIONS: {
            "goal": "Safety (allergens), preference accommodation",
            "allergies": {
                "variations": [
                    "Do you have any food allergies I should know about? This is critical for safety! ⚠️",
                    "Let's talk safety - any allergies to nuts, dairy, gluten, or anything else?",
                    "Are there any foods that trigger allergic reactions for you?"
                ],
                "safety_note": "We'll automatically flag any products containing your allergens.",
                "common_options": [
                    "Peanuts/Tree nuts", "Dairy/Milk", "Eggs", "Soy",
                    "Gluten/Wheat", "Shellfish", "Fish", "None"
                ]
            },
            "preferences": {
                "variations": [
                    "Any dietary preferences? Vegetarian, vegan, keto, etc.?",
                    "Do you follow any specific diet - vegetarian, low-carb, anything like that?",
                    "What kind of eating pattern do you follow?"
                ],
                "affirmations": [
                    "{{if vegetarian}} Great choice! Plant-based diets can be very healthy when balanced.",
                    "{{if keto}} Interesting! We'll make sure to highlight carb content for you."
                ]
            }
        },

        QuestionCategory.VALIDATION: {
            "goal": "Confirm understanding, build trust",
            "summary": {
                "template": """
Let me make sure I've got this right:

- You're {age} years old, {gender}
- Your goal is: {primary_goal}
- You {work_style_description}
- You exercise {exercise_description}
- You want to focus on: {nutritional_focus}
{allergen_warning}

Does that sound accurate? Anything you'd like to change?
                """,
                "affirmation": "Perfect! I've got everything I need to give you personalized recommendations. Let's scan your first food! 🎉"
            }
        }
    }

    @classmethod
    def get_variations(cls, category: QuestionCategory, subcategory: str = None) -> List[str]:
        """Get question variations for a category."""
        if subcategory:
            return cls.QUESTIONS[category][subcategory]["variations"]
        return cls.QUESTIONS[category]["variations"]

    @classmethod
    def get_follow_up(cls, category: QuestionCategory, subcategory: str, condition: str) -> str:
        """Get contextual follow-up based on user response."""
        follow_ups = cls.QUESTIONS[category][subcategory].get("follow_ups", [])
        for follow_up in follow_ups:
            if condition in follow_up:
                return follow_up.replace(f"{{{{if {condition}}}}}", "").strip()
        return ""
```

### 3.3 Conversational DSPy Agent

**File**: `backend/app/services/onboarding/conversational_agent.py`

```python
"""
DSPy-powered conversational agent for natural onboarding flow.

Uses Chain of Thought to:
1. Select appropriate question from bank
2. Customize phrasing based on conversation history
3. Generate natural follow-ups
4. Validate and extract structured data from freeform responses
"""

import dspy
from typing import Dict, Any, List, Optional
from app.services.onboarding.question_bank import QuestionBank, QuestionCategory


class SelectNextQuestion(dspy.Signature):
    """Select the most natural next question based on conversation flow."""

    conversation_history = dspy.InputField(desc="Previous Q&A exchanges (JSON)")
    collected_data = dspy.InputField(desc="Data collected so far (JSON)")
    missing_fields = dspy.InputField(desc="Required fields still missing (list)")

    next_category = dspy.OutputField(desc="Category of next question (enum value)")
    selected_variation = dspy.OutputField(desc="Which variation to use (1-4)")
    customized_question = dspy.OutputField(desc="Final customized question text")
    justification = dspy.OutputField(desc="Why this question makes sense now")


class ExtractStructuredData(dspy.Signature):
    """Extract structured data from user's freeform response."""

    question_category = dspy.InputField(desc="What category was being asked")
    user_response = dspy.InputField(desc="User's freeform text response")
    expected_format = dspy.InputField(desc="Expected data format/schema")

    extracted_value = dspy.OutputField(desc="Structured value extracted")
    confidence = dspy.OutputField(desc="Confidence in extraction (0-1)")
    clarification_needed = dspy.OutputField(desc="True if response was ambiguous")
    clarification_question = dspy.OutputField(desc="Follow-up to ask if ambiguous")


class GenerateFollowUp(dspy.Signature):
    """Generate natural follow-up based on user's response."""

    question_asked = dspy.InputField(desc="Original question")
    user_response = dspy.InputField(desc="User's response")
    response_sentiment = dspy.InputField(desc="Positive/Neutral/Negative/Uncertain")

    follow_up_type = dspy.OutputField(desc="affirmation, reflection, probe, or move_on")
    follow_up_text = dspy.OutputField(desc="Natural follow-up message")


class ConversationalOnboardingAgent:
    """
    Manages conversational onboarding flow using DSPy.

    Flow:
    1. Selects next question from bank
    2. Customizes phrasing
    3. Processes user response
    4. Generates follow-ups
    5. Repeats until profile complete
    """

    def __init__(self, ollama_model: str = "qwen3:8b"):  # Use smaller model for speed
        """Initialize agent with DSPy modules."""
        # Configure DSPy
        lm = dspy.LM(f'ollama_chat/{ollama_model}', api_base='http://localhost:11434')
        dspy.configure(lm=lm)

        # Initialize modules
        self.question_selector = dspy.ChainOfThought(SelectNextQuestion)
        self.data_extractor = dspy.ChainOfThought(ExtractStructuredData)
        self.follow_up_generator = dspy.ChainOfThought(GenerateFollowUp)

        self.question_bank = QuestionBank()

    async def get_next_question(
        self,
        conversation_history: List[Dict[str, str]],
        collected_data: Dict[str, Any],
        missing_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Select and customize next question.

        Args:
            conversation_history: Previous exchanges
            collected_data: Data collected so far
            missing_fields: Required fields not yet filled

        Returns:
            Dict with question text, category, and context
        """
        import json

        # Call DSPy module
        result = self.question_selector(
            conversation_history=json.dumps(conversation_history[-5:]),  # Last 5 exchanges
            collected_data=json.dumps(collected_data),
            missing_fields=json.dumps(missing_fields)
        )

        return {
            "question": result.customized_question,
            "category": result.next_category,
            "variation_index": int(result.selected_variation),
            "justification": result.justification,
            "skip_allowed": self._is_optional_field(result.next_category)
        }

    async def process_response(
        self,
        question_category: str,
        user_response: str,
        expected_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data from freeform response.

        Args:
            question_category: Category that was asked
            user_response: User's freeform answer
            expected_schema: Pydantic schema for the field

        Returns:
            Extracted value, confidence, and clarification if needed
        """
        import json

        result = self.data_extractor(
            question_category=question_category,
            user_response=user_response,
            expected_format=json.dumps(expected_schema)
        )

        return {
            "value": result.extracted_value,
            "confidence": float(result.confidence),
            "needs_clarification": result.clarification_needed.lower() == "true",
            "clarification_question": result.clarification_question if result.clarification_needed else None
        }

    async def generate_follow_up(
        self,
        question: str,
        response: str,
        sentiment: str = "neutral"
    ) -> Dict[str, str]:
        """
        Generate natural follow-up based on response sentiment.

        Uses OARS framework:
        - Affirmations for positive responses
        - Reflections for emotional responses
        - Probes for incomplete responses

        Args:
            question: Original question
            response: User's response
            sentiment: Detected sentiment

        Returns:
            Follow-up type and text
        """
        result = self.follow_up_generator(
            question_asked=question,
            user_response=response,
            response_sentiment=sentiment
        )

        return {
            "type": result.follow_up_type,
            "text": result.follow_up_text
        }

    def _is_optional_field(self, category: str) -> bool:
        """Determine if a field can be skipped."""
        optional_categories = [
            "lifestyle_habits",  # Smoking, alcohol are sensitive
            "food_preferences"   # Nice to have, not required
        ]
        return any(opt in category.lower() for opt in optional_categories)
```

### 3.4 Onboarding WebSocket Handler

**File**: `backend/app/api/onboarding.py`

```python
"""
WebSocket handler for conversational onboarding.

Real-time back-and-forth with user via Socket.IO.
"""

import asyncio
import logging
from typing import Dict, Any
from app.main import sio
from app.services.onboarding.conversational_agent import ConversationalOnboardingAgent
from app.core.profile_store import profile_store

logger = logging.getLogger(__name__)

# In-memory conversation state (keyed by session ID)
onboarding_sessions: Dict[str, Dict[str, Any]] = {}


@sio.event
async def start_onboarding(sid, data):
    """
    Begin conversational onboarding.

    Client sends: {"name": "John"}
    Server starts asking questions one by one.
    """
    name = data.get("name")

    if not name:
        await sio.emit("onboarding_error", {
            "error": "Name is required"
        }, room=sid)
        return

    logger.info(f"Starting onboarding for {name} (session {sid})")

    # Initialize session state
    onboarding_sessions[sid] = {
        "name": name,
        "conversation_history": [],
        "collected_data": {"name": name},
        "missing_fields": [
            "age", "biological_gender", "height_cm", "weight_kg",
            "lifestyle", "goals", "allergies", "dietary_preferences"
        ],
        "progress": 0.0,
        "agent": ConversationalOnboardingAgent()
    }

    # Send first question
    await _send_next_question(sid)


@sio.event
async def onboarding_response(sid, data):
    """
    Handle user's response to a question.

    Client sends: {"response": "I'm 30 years old"}
    Server processes, sends follow-up or next question.
    """
    session = onboarding_sessions.get(sid)

    if not session:
        await sio.emit("onboarding_error", {
            "error": "Session not found. Please start over."
        }, room=sid)
        return

    response_text = data.get("response", "").strip()

    if not response_text:
        await sio.emit("onboarding_prompt", {
            "message": "I didn't catch that. Could you try again?",
            "allow_skip": session.get("current_question_skippable", False)
        }, room=sid)
        return

    # Record exchange
    session["conversation_history"].append({
        "question": session.get("last_question", ""),
        "response": response_text,
        "category": session.get("last_category", "")
    })

    # Extract structured data from response
    agent = session["agent"]
    category = session.get("last_category", "")

    try:
        extraction = await agent.process_response(
            question_category=category,
            user_response=response_text,
            expected_schema={}  # TODO: Get from field definition
        )

        if extraction["needs_clarification"]:
            # Ask clarification
            await sio.emit("onboarding_clarification", {
                "question": extraction["clarification_question"],
                "previous_response": response_text
            }, room=sid)
            return

        # Update collected data
        _update_collected_data(session, category, extraction["value"])

        # Generate follow-up (affirmation, reflection, etc.)
        follow_up = await agent.generate_follow_up(
            question=session.get("last_question", ""),
            response=response_text,
            sentiment="neutral"  # TODO: Sentiment analysis
        )

        if follow_up["type"] in ["affirmation", "reflection"]:
            # Send follow-up, then move to next question
            await sio.emit("onboarding_followup", {
                "message": follow_up["text"],
                "type": follow_up["type"]
            }, room=sid)

            await asyncio.sleep(1.5)  # Brief pause for natural flow

        # Check if complete
        if not session["missing_fields"]:
            await _complete_onboarding(sid, session)
            return

        # Update progress
        session["progress"] = _calculate_progress(session)

        # Send next question
        await _send_next_question(sid)

    except Exception as e:
        logger.error(f"Error processing response: {e}", exc_info=True)
        await sio.emit("onboarding_error", {
            "error": "Something went wrong. Let's try the next question."
        }, room=sid)
        await _send_next_question(sid)


@sio.event
async def skip_question(sid):
    """User chose to skip current question."""
    session = onboarding_sessions.get(sid)

    if not session:
        return

    # Remove from missing fields
    category = session.get("last_category", "")
    field = _category_to_field(category)

    if field in session["missing_fields"]:
        session["missing_fields"].remove(field)

    # Record skip
    session["conversation_history"].append({
        "question": session.get("last_question", ""),
        "response": "[SKIPPED]",
        "category": category
    })

    # Move to next
    await _send_next_question(sid)


async def _send_next_question(sid: str):
    """Select and send next question to user."""
    session = onboarding_sessions.get(sid)

    if not session:
        return

    agent = session["agent"]

    try:
        next_q = await agent.get_next_question(
            conversation_history=session["conversation_history"],
            collected_data=session["collected_data"],
            missing_fields=session["missing_fields"]
        )

        # Store for response processing
        session["last_question"] = next_q["question"]
        session["last_category"] = next_q["category"]
        session["current_question_skippable"] = next_q["skip_allowed"]

        # Send to client
        await sio.emit("onboarding_question", {
            "question": next_q["question"],
            "category": next_q["category"],
            "progress": session["progress"],
            "allow_skip": next_q["skip_allowed"]
        }, room=sid)

    except Exception as e:
        logger.error(f"Error generating question: {e}", exc_info=True)
        # Fallback: complete with partial data
        await _complete_onboarding(sid, session)


async def _complete_onboarding(sid: str, session: Dict[str, Any]):
    """Finalize onboarding and create profile."""
    collected = session["collected_data"]
    name = session["name"]

    logger.info(f"Completing onboarding for {name}")

    # Create profile
    try:
        from app.models.schemas import (
            EnhancedUserProfile, LifestyleHabits,
            FoodPreferences, HealthMetrics
        )
        from app.services.health_modeling import HealthModelingEngine

        # Build profile
        lifestyle = LifestyleHabits(**collected.get("lifestyle", {}))
        food_prefs = FoodPreferences(**collected.get("food_preferences", {}))

        # Calculate health metrics
        engine = HealthModelingEngine()
        metrics = await engine.calculate_metrics(
            age=collected.get("age"),
            biological_gender=collected.get("biological_gender"),
            height_cm=collected.get("height_cm"),
            weight_kg=collected.get("weight_kg"),
            lifestyle=lifestyle,
            goals=collected.get("goals", [])
        )

        # Calculate daily targets
        targets = await engine.calculate_daily_targets(metrics, collected.get("goals", []))

        profile = EnhancedUserProfile(
            name=name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            age=collected.get("age"),
            biological_gender=collected.get("biological_gender", "other"),
            height_cm=collected.get("height_cm"),
            weight_kg=collected.get("weight_kg"),
            lifestyle=lifestyle,
            food_preferences=food_prefs,
            goals=collected.get("goals", []),
            allergies=collected.get("allergies", []),
            dietary_preferences=collected.get("dietary_preferences", []),
            nutritional_focus=collected.get("nutritional_focus", []),
            health_metrics=metrics,
            daily_targets=targets,
            onboarding_completed=True,
            onboarding_progress=1.0
        )

        # Save profile
        await profile_store.save(profile)

        # Success!
        await sio.emit("onboarding_complete", {
            "message": "All set! Your personalized profile is ready. Let's scan your first food! 🎉",
            "profile": profile.model_dump(),
            "summary": _generate_profile_summary(profile)
        }, room=sid)

        # Cleanup session
        del onboarding_sessions[sid]

    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        await sio.emit("onboarding_error", {
            "error": "Failed to create profile. Please try again."
        }, room=sid)


def _update_collected_data(session: Dict[str, Any], category: str, value: Any):
    """Update collected data based on category."""
    field = _category_to_field(category)

    if field:
        session["collected_data"][field] = value

        if field in session["missing_fields"]:
            session["missing_fields"].remove(field)


def _category_to_field(category: str) -> str:
    """Map question category to profile field name."""
    mapping = {
        "demographics.age": "age",
        "demographics.gender": "biological_gender",
        "demographics.height_weight": ["height_cm", "weight_kg"],
        "lifestyle_sleep": "lifestyle",
        "lifestyle_work": "lifestyle",
        "lifestyle_exercise": "lifestyle",
        "lifestyle_habits": "lifestyle",
        "health_goals": "goals",
        "food_preferences": "food_preferences",
        "dietary_restrictions": ["allergies", "dietary_preferences"]
    }

    return mapping.get(category, category)


def _calculate_progress(session: Dict[str, Any]) -> float:
    """Calculate onboarding progress percentage."""
    total_required = len(session.get("missing_fields", [])) + len(session.get("collected_data", {}))
    collected = len(session.get("collected_data", {}))

    if total_required == 0:
        return 1.0

    return collected / total_required


def _generate_profile_summary(profile: EnhancedUserProfile) -> str:
    """Generate friendly summary of user profile."""
    summary_parts = []

    if profile.health_metrics:
        bmi = profile.health_metrics.bmi
        summary_parts.append(f"BMI: {bmi:.1f} ({profile.health_metrics.bmi_category})")
        summary_parts.append(f"Daily calorie target: {profile.health_metrics.energy_budget:.0f} cal")

    if profile.goals:
        summary_parts.append(f"Goals: {', '.join(profile.goals)}")

    if profile.allergies:
        summary_parts.append(f"⚠️ Allergies: {', '.join(profile.allergies)}")

    return " | ".join(summary_parts)
```

---

## 4. User Health Modeling Engine

### 4.1 BMI/BMR/TDEE Calculation Module

**File**: `backend/app/services/health_modeling.py`

```python
"""
Health metrics calculation engine.

Calculates:
- BMI (Body Mass Index)
- BMR (Basal Metabolic Rate) - Mifflin-St Jeor & Harris-Benedict
- TDEE (Total Daily Energy Expenditure) - with activity multipliers
- Energy budget (TDEE adjusted for goals)
- Health risk assessment
"""

import logging
from typing import Optional, List
from datetime import datetime
from app.models.schemas import (
    HealthMetrics, LifestyleHabits, EnhancedUserProfile
)

logger = logging.getLogger(__name__)


class HealthModelingEngine:
    """Calculates health metrics from user data."""

    # Activity multipliers for TDEE calculation
    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,          # Little or no exercise
        "lightly_active": 1.375,   # Light exercise 1-3 days/week
        "moderately_active": 1.55, # Moderate exercise 3-5 days/week
        "very_active": 1.725,      # Hard exercise 6-7 days/week
        "extremely_active": 1.9    # Very hard exercise, physical job
    }

    # BMI categories (WHO standards)
    BMI_CATEGORIES = {
        (0, 18.5): "underweight",
        (18.5, 25): "normal",
        (25, 30): "overweight",
        (30, 35): "obese_class_1",
        (35, 40): "obese_class_2",
        (40, 100): "obese_class_3"
    }

    async def calculate_metrics(
        self,
        age: Optional[int],
        biological_gender: str,
        height_cm: Optional[float],
        weight_kg: Optional[float],
        lifestyle: LifestyleHabits,
        goals: List[str]
    ) -> Optional[HealthMetrics]:
        """
        Calculate complete health metrics.

        Args:
            age: User age
            biological_gender: male, female, or other
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms
            lifestyle: Lifestyle habits
            goals: Health goals

        Returns:
            HealthMetrics or None if insufficient data
        """
        # Validate required data
        if not all([age, height_cm, weight_kg]):
            logger.warning("Insufficient data for health metrics calculation")
            return None

        try:
            # 1. Calculate BMI
            bmi = self._calculate_bmi(height_cm, weight_kg)
            bmi_category = self._get_bmi_category(bmi)

            # 2. Calculate BMR (Mifflin-St Jeor - more accurate)
            bmr = self._calculate_bmr_mifflin(
                age, biological_gender, height_cm, weight_kg
            )

            # 3. Determine activity multiplier from lifestyle
            activity_mult = self._calculate_activity_multiplier(lifestyle)

            # 4. Calculate TDEE
            tdee = bmr * activity_mult

            # 5. Adjust for goals → energy budget
            energy_budget = self._calculate_energy_budget(tdee, goals)

            # 6. Assess health risks
            health_risks = self._assess_health_risks(
                bmi, bmi_category, lifestyle, goals
            )

            return HealthMetrics(
                bmi=round(bmi, 2),
                bmi_category=bmi_category,
                bmr=round(bmr, 0),
                bmr_formula="mifflin_st_jeor",
                tdee=round(tdee, 0),
                activity_multiplier=round(activity_mult, 2),
                energy_budget=round(energy_budget, 0),
                health_risks=health_risks,
                calculated_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error calculating health metrics: {e}", exc_info=True)
            return None

    def _calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        """
        Calculate Body Mass Index.

        Formula: BMI = weight (kg) / (height (m))^2
        """
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)

    def _get_bmi_category(self, bmi: float) -> str:
        """Get BMI category based on WHO standards."""
        for (low, high), category in self.BMI_CATEGORIES.items():
            if low <= bmi < high:
                return category
        return "obese_class_3"  # Default for > 40

    def _calculate_bmr_mifflin(
        self,
        age: int,
        biological_gender: str,
        height_cm: float,
        weight_kg: float
    ) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation.

        More accurate than Harris-Benedict for modern populations.

        For men: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(years) + 5
        For women: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(years) - 161
        """
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age

        if biological_gender.lower() == "male":
            return base + 5
        elif biological_gender.lower() == "female":
            return base - 161
        else:
            # For "other", use average
            return base - 78  # Average of +5 and -161

    def _calculate_bmr_harris_benedict(
        self,
        age: int,
        biological_gender: str,
        height_cm: float,
        weight_kg: float
    ) -> float:
        """
        Alternative: Harris-Benedict Equation (revised 1984).

        For men: BMR = 88.362 + (13.397 × weight) + (4.799 × height) - (5.677 × age)
        For women: BMR = 447.593 + (9.247 × weight) + (3.098 × height) - (4.330 × age)
        """
        if biological_gender.lower() == "male":
            return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        elif biological_gender.lower() == "female":
            return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
        else:
            # Average
            male_bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
            female_bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
            return (male_bmr + female_bmr) / 2

    def _calculate_activity_multiplier(self, lifestyle: LifestyleHabits) -> float:
        """
        Calculate activity multiplier for TDEE based on lifestyle.

        Considers:
        - Work style
        - Commute type & duration
        - Exercise frequency & duration
        - General activity level
        """
        # Base multiplier from work style
        work_multipliers = {
            "sedentary_desk": 1.2,
            "light_activity": 1.3,
            "moderate_activity": 1.5,
            "heavy_labor": 1.7
        }

        base = work_multipliers.get(lifestyle.work_style, 1.2)

        # Adjust for commute
        if lifestyle.commute_type in ["walking", "cycling"]:
            # Add bonus based on duration
            commute_bonus = (lifestyle.daily_commute_minutes / 60) * 0.05
            base += commute_bonus

        # Adjust for exercise
        weekly_exercise_hours = (
            lifestyle.exercise_frequency_per_week *
            lifestyle.exercise_duration_minutes / 60
        )

        if weekly_exercise_hours > 0:
            # Add 0.05 per hour of exercise per week
            exercise_bonus = weekly_exercise_hours * 0.05
            base += exercise_bonus

        # Cap at reasonable maximum
        return min(base, 2.0)

    def _calculate_energy_budget(self, tdee: float, goals: List[str]) -> float:
        """
        Calculate energy budget (calorie target) based on goals.

        Adjusts TDEE up or down depending on goals.
        """
        adjustment = 0.0

        for goal in goals:
            goal_lower = goal.lower()

            if "weight_loss" in goal_lower or "lose" in goal_lower:
                adjustment -= 500  # 500 cal deficit for ~1 lb/week loss

            elif "weight_gain" in goal_lower or "gain" in goal_lower:
                adjustment += 300  # Moderate surplus for lean gain

            elif "muscle" in goal_lower or "building" in goal_lower:
                adjustment += 250  # Slight surplus + high protein

            elif "maintenance" in goal_lower or "maintain" in goal_lower:
                adjustment += 0  # TDEE as-is

        # If multiple conflicting goals, take average
        if len(goals) > 1:
            adjustment = adjustment / len(goals)

        return tdee + adjustment

    def _assess_health_risks(
        self,
        bmi: float,
        bmi_category: str,
        lifestyle: LifestyleHabits,
        goals: List[str]
    ) -> List[str]:
        """
        Assess health risks based on metrics and lifestyle.

        Returns list of risk flags.
        """
        risks = []

        # BMI-based risks
        if bmi_category in ["obese_class_1", "obese_class_2", "obese_class_3"]:
            risks.append("obesity_risk")
            risks.append("diabetes_risk")
            risks.append("cardiovascular_risk")
            risks.append("hypertension_risk")

        elif bmi_category == "underweight":
            risks.append("malnutrition_risk")

        # Lifestyle risks
        if lifestyle.smoking in ["regular", "occasional"]:
            risks.append("cardiovascular_risk")

        if lifestyle.alcohol in ["heavy"]:
            risks.append("cardiovascular_risk")

        if lifestyle.avg_sleep_hours < 6:
            risks.append("metabolic_risk")

        if lifestyle.stress_level in ["high", "very_high"]:
            risks.append("cardiovascular_risk")

        # Goal-based risks (user-identified)
        for goal in goals:
            if "diabetes" in goal.lower():
                risks.append("diabetes_risk")
            if "heart" in goal.lower() or "cardio" in goal.lower():
                risks.append("cardiovascular_risk")

        # Remove duplicates
        risks = list(set(risks))

        return risks if risks else ["none"]

    async def calculate_daily_targets(
        self,
        metrics: HealthMetrics,
        goals: List[str]
    ) -> Dict[str, float]:
        """
        Calculate daily nutritional targets based on metrics and goals.

        Returns targets for:
        - calories, protein, carbs, fat, sugar, sodium, fiber
        """
        energy_budget = metrics.energy_budget

        # Base macro ratios
        protein_ratio = 0.25  # 25% of calories
        carbs_ratio = 0.45    # 45% of calories
        fat_ratio = 0.30      # 30% of calories

        # Adjust for goals
        for goal in goals:
            goal_lower = goal.lower()

            if "muscle" in goal_lower or "gain" in goal_lower:
                protein_ratio = 0.30
                carbs_ratio = 0.40
                fat_ratio = 0.30

            elif "weight_loss" in goal_lower:
                protein_ratio = 0.30  # Higher protein for satiety
                carbs_ratio = 0.35
                fat_ratio = 0.35

            elif "keto" in goal_lower or "low_carb" in goal_lower:
                protein_ratio = 0.25
                carbs_ratio = 0.10   # Very low carb
                fat_ratio = 0.65

        # Calculate macro targets (grams)
        protein_g = (energy_budget * protein_ratio) / 4  # 4 cal/g
        carbs_g = (energy_budget * carbs_ratio) / 4      # 4 cal/g
        fat_g = (energy_budget * fat_ratio) / 9          # 9 cal/g

        # Micronutrient targets
        sugar_g = 30.0  # Default: WHO recommends < 10% of calories
        sodium_mg = 2300.0  # Default: FDA recommendation
        fiber_g = 28.0  # Default: USDA recommendation

        # Adjust for health risks
        if "diabetes_risk" in metrics.health_risks:
            sugar_g = 20.0  # Stricter for diabetes risk
            fiber_g = 35.0  # Higher fiber helps

        if "cardiovascular_risk" in metrics.health_risks or "hypertension_risk" in metrics.health_risks:
            sodium_mg = 1500.0  # AHA recommendation for high risk

        return {
            "calories": round(energy_budget, 0),
            "protein_g": round(protein_g, 1),
            "carbs_g": round(carbs_g, 1),
            "fat_g": round(fat_g, 1),
            "sugar_g": round(sugar_g, 1),
            "sodium_mg": round(sodium_mg, 0),
            "fiber_g": round(fiber_g, 1)
        }


# Global health modeling engine instance
health_modeling_engine = HealthModelingEngine()
```

---

**Due to length constraints, I'll continue in the next part. This LLD is extremely comprehensive and will span multiple parts. Should I continue with:**

- Section 5: Enhanced OCR Processing Pipeline
- Section 6: SearXNG ReAct "Intern" Agent
- Section 7: Food History Tracking System
- Section 8: Context-Aware Scoring Engine
- And the remaining sections?

## 5. Enhanced OCR Processing Pipeline

### 5.1 Overview

The OCR pipeline transforms raw image text into structured nutritional data through a multi-stage process:

1. **Raw OCR Extraction** (Chandra) → Full text with confidence
2. **DSPy Structural Extraction** → Parse text into entities
3. **Missing Data Identification** → Detect incomplete information
4. **Market Search Augmentation** (if needed) → Size/price estimation
5. **OpenFoodFacts Validation** → Cross-reference with database
6. **Final Structured Output** → Complete NutritionData object

**Key Design Principle**: Each stage can be bypassed if data is already complete. Stages are independent and can be tested/debugged separately.

### 5.2 Stage 1: Raw OCR Extraction

**Module**: `backend/app/services/ocr/raw_extraction.py`

**Responsibility**: Extract all visible text from food package image using Chandra OCR.

**Input Contract**:

```python
RawOCRRequest:
    image_bytes: bytes
    image_format: Literal["jpeg", "png", "jpg"]
    preprocessing_level: Literal["none", "basic", "aggressive"] = "basic"
```

**Output Contract**:

```python
RawOCRExtraction:
    full_text: str                          # Complete extracted text
    confidence: float                       # Overall OCR confidence (0-1)
    processing_time_ms: int

    # Optional structured regions (if OCR provides)
    text_blocks: List[Dict[str, Any]]       # [{"text": "...", "bbox": [...], "confidence": 0.9}]

    # Preprocessing metadata
    image_preprocessed: bool
    preprocessing_applied: List[str]        # ["denoise", "contrast", "rotate"]
```

**Processing Steps**:

1. **Image Preprocessing** (if enabled):
   - Convert to grayscale
   - Adaptive thresholding for text clarity
   - Denoise (bilateral filter)
   - Deskew (correct rotation up to ±15°)
   - Contrast enhancement (CLAHE)

2. **Chandra OCR Invocation**:

   ```python
   # Chandra OCR usage pattern
   from chandra_ocr import ChandraOCR

   ocr = ChandraOCR()  # Loads transformers model: datalab-to/chandra

   result = ocr.extract(pil_image)
   # Returns: {"text": str, "confidence": float, "blocks": [...]}
   ```

3. **Post-processing**:
   - Remove noise characters (control chars, excessive whitespace)
   - Normalize encoding (UTF-8)
   - Detect and merge split words (e.g., "CA LORIES" → "CALORIES")

**Error Handling**:

- If Chandra fails → retry with aggressive preprocessing
- If still fails → return empty text with confidence=0.0
- Log failure for monitoring

**Performance Target**: < 2s for 1920x1080 image

**Decoupling**: This module has ZERO dependencies on other services. Can be tested with any image independently.

---

### 5.3 Stage 2: DSPy Structural Extraction

**Module**: `backend/app/services/ocr/structured_extraction.py`

**Responsibility**: Parse unstructured OCR text into structured nutritional entities using DSPy.

**Why DSPy**: Raw text from labels is messy. Regex patterns fail on:

- Typos: "Calorles" instead of "Calories"
- Non-standard formatting: "per 100 gm serving"
- Missing units: "Sugar 10" (is it 10g? 10mg?)
- Multilingual labels: "Sodium/सोडियम 250mg"

DSPy LLM can handle ambiguity and extract intent even from messy text.

**DSPy Signature Definition**:

```python
class ExtractNutritionalEntities(dspy.Signature):
    """
    Extract structured nutritional information from OCR text of food label.

    Handle:
    - Typos and OCR errors
    - Non-standard formatting
    - Multilingual text
    - Missing units (infer from context)
    - Per-serving vs per-100g values
    """

    ocr_text: str = dspy.InputField(
        desc="Raw OCR text extracted from food package label"
    )

    # Outputs
    product_name: str = dspy.OutputField(
        desc="Product name/brand (e.g., 'Lay's Classic Potato Chips')"
    )

    brand: Optional[str] = dspy.OutputField(
        desc="Brand name if separately identifiable"
    )

    net_quantity: Optional[str] = dspy.OutputField(
        desc="Net quantity with unit (e.g., '52g', '500ml', '1kg')"
    )

    serving_size: Optional[str] = dspy.OutputField(
        desc="Serving size mentioned (e.g., '28g', '1 cup', '2 biscuits')"
    )

    nutrients_per_100g: Dict[str, float] = dspy.OutputField(
        desc="""
        Nutrients per 100g/100ml as JSON dict.
        Keys: 'energy_kcal', 'protein_g', 'carbs_g', 'fat_g', 'sugar_g', 'sodium_mg', 'fiber_g'
        Only include if explicitly stated in text.
        """
    )

    nutrients_per_serving: Dict[str, float] = dspy.OutputField(
        desc="""
        Nutrients per serving as JSON dict (same keys as per_100g).
        Only include if explicitly stated.
        """
    )

    ingredients_list: List[str] = dspy.OutputField(
        desc="List of ingredients in order. Empty list if not found."
    )

    allergen_warnings: List[str] = dspy.OutputField(
        desc="Allergens mentioned (e.g., ['milk', 'soy', 'nuts']). Empty if none."
    )

    package_indicators: List[str] = dspy.OutputField(
        desc="""
        Price/size indicators for market search (e.g., ['₹20', '40g pack', '500ml bottle']).
        Extract any text that helps identify product variant in market.
        """
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in extraction quality (0.0 to 1.0)"
    )

    missing_critical_info: List[str] = dspy.OutputField(
        desc="""
        List of critical missing information.
        Options: ['product_name', 'net_quantity', 'nutritional_values', 'ingredients']
        """
    )
```

**DSPy Module Implementation Pattern**:

```python
class NutritionalEntityExtractor(dspy.Module):
    """DSPy module for extracting structured data from OCR text."""

    def __init__(self, model: str = "qwen3:8b"):
        super().__init__()

        # Use smaller, faster model for extraction (not reasoning)
        lm = dspy.LM(f'ollama_chat/{model}', api_base='http://localhost:11434')
        dspy.configure(lm=lm)

        # Use ChainOfThought for reasoning through messy text
        self.extractor = dspy.ChainOfThought(ExtractNutritionalEntities)

    async def forward(self, ocr_text: str) -> dspy.Prediction:
        """
        Extract entities from OCR text.

        Returns DSPy Prediction object with all output fields.
        """
        result = await self.extractor(ocr_text=ocr_text)
        return result
```

**Usage Pattern** (Async):

```python
# In calling code
from app.services.ocr.structured_extraction import NutritionalEntityExtractor

extractor = NutritionalEntityExtractor()

result = await extractor.forward(ocr_text="NUTRITION FACTS per 100g...")

# Access fields
product_name = result.product_name
nutrients = result.nutrients_per_100g  # Dict
missing = result.missing_critical_info  # List
```

**When LLM Call is Needed**:

- OCR text is present but messy
- Standard regex patterns fail
- Units are ambiguous
- Multilingual text
- Non-standard formatting

**When LLM Call is NOT Needed**:

- OCR completely failed (empty text) → skip
- Text is perfectly structured (rare) → simple regex

**Performance Target**: < 3s (includes LLM inference)

**Fallback Strategy**:

- If DSPy fails → attempt regex-based extraction
- If regex fails → return partial data with low confidence
- Always return a result (never throw exception)

---

### 5.4 Stage 3: Missing Data Identification

**Module**: `backend/app/services/ocr/gap_analyzer.py`

**Responsibility**: Analyze extracted data to identify what's missing and how critical it is.

**Input**:

```python
StructuredNutritionExtraction  # From Stage 2
```

**Output**:

```python
DataGapAnalysis:
    completeness_score: float               # 0-1 (1 = all critical data present)

    missing_fields: List[str]              # ['net_quantity', 'sugar_g']

    critical_gaps: List[str]               # Blocking issues: ['product_name', 'calories']
    non_critical_gaps: List[str]           # Nice-to-have: ['fiber_g', 'brand']

    can_proceed_without_search: bool       # True if we have enough data
    requires_market_search: bool           # True if we need size/price estimation
    requires_openfoodfacts: bool           # True if we need database augmentation

    suggested_search_query: Optional[str]  # Best query for market search
```

**Decision Logic** (Rule-Based, No LLM Needed):

```python
def analyze_gaps(extraction: StructuredNutritionExtraction) -> DataGapAnalysis:
    """
    Analyze data completeness and determine next steps.

    Critical fields (must have at least ONE):
    - product_name OR brand
    - calories OR energy_kcal
    - serving_size OR net_quantity

    Non-critical (nice to have):
    - protein, carbs, fat, fiber
    - ingredients
    - allergens
    """

    critical_present = []
    critical_missing = []

    # Check product identification
    if extraction.product_name:
        critical_present.append('product_name')
    else:
        critical_missing.append('product_name')

    # Check calorie data
    has_calories = (
        'energy_kcal' in extraction.nutrients_per_100g or
        'calories' in extraction.nutrients_per_serving
    )

    if has_calories:
        critical_present.append('calories')
    else:
        critical_missing.append('calories')

    # Check quantity (for portion calculation)
    if extraction.net_quantity or extraction.serving_size:
        critical_present.append('quantity')
    else:
        critical_missing.append('quantity')

    # Calculate completeness
    completeness = len(critical_present) / (len(critical_present) + len(critical_missing))

    # Determine next steps
    can_proceed = len(critical_missing) == 0
    needs_search = ('quantity' in critical_missing or
                    'product_name' in critical_missing)
    needs_off = ('calories' in critical_missing)

    return DataGapAnalysis(
        completeness_score=completeness,
        critical_gaps=critical_missing,
        can_proceed_without_search=can_proceed,
        requires_market_search=needs_search,
        requires_openfoodfacts=needs_off,
        suggested_search_query=_build_search_query(extraction)
    )
```

**No LLM Needed**: Simple rule-based logic.

---

### 5.5 Stage 4: Market Search Augmentation

**Module**: `backend/app/services/ocr/market_augmentation.py`

**Responsibility**: If net quantity or product variants are missing, search market to estimate size/price.

**Trigger Condition**: `DataGapAnalysis.requires_market_search == True`

**Why This Stage Exists**:

- OCR might read "Lay's Chips" but miss "52g Net Wt."
- Knowing pack size is critical for calculating total nutritional load
- Market search can find: "Lay's Classic: ₹10 (25g), ₹20 (52g), ₹40 (100g)"

**Search Strategy**:

1. **Build Search Query** from available data:

   ```python
   query_parts = []

   if product_name:
       query_parts.append(product_name)
   if brand:
       query_parts.append(brand)
   if package_indicators:  # e.g., ["₹20", "blue pack"]
       query_parts.extend(package_indicators)

   query = " ".join(query_parts) + " buy online price size variants"
   ```

2. **Delegate to Search Intern Agent** (Section 6):

   ```python
   from app.agents.search_intern import SearchInternAgent

   intern = SearchInternAgent()

   task = {
       "objective": "Find available sizes and prices for this product",
       "product_name": extraction.product_name,
       "hints": extraction.package_indicators
   }

   report = await intern.execute_task(task)
   # Returns: InternAgentReport with available_sizes, prices, sources
   ```

3. **Extract Size Variants**:
   - Parse results for common patterns: "25g", "52g", "100g", "500ml"
   - Associate with prices: "₹10", "₹20", "₹40"
   - Match OCR hints to most likely variant

4. **Estimate Net Quantity**:

   ```python
   # If OCR found "₹20" in package_indicators
   # And search found {"₹20": "52g"}
   # → estimated_net_quantity = "52g"
   ```

**Output**:

```python
ProductSizeEstimate:
    available_sizes: List[Dict]  # [{"price": "₹20", "size": "52g", "source": "url"}]
    best_match: Dict             # Most likely variant based on hints
    confidence: float            # How confident the match is
```

**Performance Target**: < 5s (includes search intern agent)

**Fallback**: If search fails, ask user to manually enter pack size via chat.

---

### 5.6 Stage 5: OpenFoodFacts Validation

**Module**: `backend/app/services/ocr/openfoodfacts_validation.py`

**Responsibility**: Cross-reference extracted data with OpenFoodFacts database to:

- Fill missing nutritional values
- Validate OCR-extracted values
- Get authoritative allergen info

**When to Use**:

- `DataGapAnalysis.requires_openfoodfacts == True`, OR
- Extracted nutritional data has low confidence, OR
- Always (as validation step)

**Search Strategy**:

1. **Try Barcode First** (if available from image):

   ```python
   if barcode:
       url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
       response = await httpx_client.get(url)
       # Parse and extract nutrition
   ```

2. **Fallback to Text Search**:

   ```python
   search_url = "https://world.openfoodfacts.org/cgi/search.pl"
   params = {
       "search_terms": f"{product_name} {brand}",
       "search_simple": 1,
       "json": 1,
       "page_size": 5
   }
   response = await httpx_client.get(search_url, params=params)
   products = response.json()["products"]

   # Pick best match (Section 5.7)
   ```

3. **Data Merging**:
   - OCR data is PRIMARY (it's what user is actually holding)
   - OpenFoodFacts data is SECONDARY (for filling gaps/validation)
   - Merge strategy:

     ```python
     merged = ocr_data.copy()

     for field in ['protein_g', 'carbs_g', 'fat_g', 'fiber_g']:
         if field not in merged or merged[field] is None:
             merged[field] = off_data.get(field)

     # Always prefer OCR ingredients (fresher data)
     # But use OFF allergens if OCR missed them
     if not merged['allergens']:
         merged['allergens'] = off_data.get('allergens', [])
     ```

**Output**: Enhanced `StructuredNutritionExtraction` with filled gaps.

---

### 5.7 Product Matching (OpenFoodFacts Results)

**Challenge**: When text search returns 5 products, which one matches the scanned item?

**Solution**: DSPy-based matching with similarity scoring.

**DSPy Signature**:

```python
class MatchProduct(dspy.Signature):
    """
    Determine which OpenFoodFacts product best matches the scanned item.
    """

    scanned_product_info: str = dspy.InputField(
        desc="""
        Information from scanned product: name, brand, package size, price hints.
        Format as JSON string.
        """
    )

    candidate_products: str = dspy.InputField(
        desc="""
        List of candidate products from OpenFoodFacts as JSON array.
        Each with: name, brand, size, barcode.
        """
    )

    best_match_index: int = dspy.OutputField(
        desc="Index (0-based) of best matching product. -1 if no good match."
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in match (0-1)"
    )

    reasoning: str = dspy.OutputField(
        desc="Why this product was selected"
    )
```

**Usage**:

```python
class ProductMatcher(dspy.Module):
    def __init__(self):
        super().__init__()
        self.matcher = dspy.ChainOfThought(MatchProduct)

    async def find_best_match(
        self,
        scanned_info: Dict,
        candidates: List[Dict]
    ) -> int:
        result = await self.matcher(
            scanned_product_info=json.dumps(scanned_info),
            candidate_products=json.dumps(candidates)
        )
        return int(result.best_match_index)
```

**When LLM Needed**: Multiple search results with ambiguous matches.

**When NOT Needed**: Exact barcode match (index=0, confidence=1.0).

---

### 5.8 Final Assembly

**Module**: `backend/app/services/ocr/pipeline.py`

**Responsibility**: Orchestrate all stages and produce final `NutritionData` object.

**Async Pipeline Execution**:

```python
class OCREnhancementPipeline:
    """
    Orchestrates 5-stage OCR enhancement pipeline.

    Each stage is independent and can be bypassed.
    """

    def __init__(self):
        self.raw_extractor = RawOCRExtractor()
        self.entity_extractor = NutritionalEntityExtractor()
        self.gap_analyzer = DataGapAnalyzer()
        self.market_augmenter = MarketAugmenter()
        self.off_validator = OpenFoodFactsValidator()

    async def process(
        self,
        image_bytes: bytes,
        barcode: Optional[str] = None
    ) -> NutritionData:
        """
        Run full pipeline asynchronously.

        Returns complete NutritionData or raises exception with partial data.
        """

        # Stage 1: Raw OCR
        raw_ocr = await self.raw_extractor.extract(image_bytes)

        if not raw_ocr.full_text or raw_ocr.confidence < 0.5:
            raise OCRFailedException("OCR extraction failed", partial_data=None)

        # Stage 2: Structured extraction
        structured = await self.entity_extractor.forward(raw_ocr.full_text)

        # Stage 3: Gap analysis
        gaps = self.gap_analyzer.analyze_gaps(structured)

        # Stage 4: Market augmentation (if needed)
        if gaps.requires_market_search:
            size_estimate = await self.market_augmenter.estimate_size(structured)
            structured.net_quantity = size_estimate.best_match.get('size')

        # Stage 5: OpenFoodFacts validation
        if barcode or gaps.requires_openfoodfacts:
            enhanced = await self.off_validator.validate_and_enhance(
                structured, barcode
            )
        else:
            enhanced = structured

        # Convert to NutritionData
        nutrition_data = self._to_nutrition_data(enhanced, gaps)

        return nutrition_data

    def _to_nutrition_data(
        self,
        extraction: StructuredNutritionExtraction,
        gaps: DataGapAnalysis
    ) -> NutritionData:
        """Convert structured extraction to final NutritionData model."""
        # Implementation maps fields
        pass
```

**Error Handling Strategy**:

- Each stage logs its output
- If any stage fails, proceed with partial data + low confidence flag
- Never fail the entire scan unless Stage 1 (raw OCR) completely fails

**Performance Targets**:

- Stage 1 (OCR): < 2s
- Stage 2 (Extraction): < 3s
- Stage 3 (Gap Analysis): < 0.1s (rule-based)
- Stage 4 (Market Search): < 5s (if needed)
- Stage 5 (OFF Validation): < 3s (if needed)
- **Total**: < 13s worst case, < 5s typical case

---

## 6. SearXNG ReAct "Intern" Agent

### 6.1 Overview - The "Intern" Metaphor

This is the **most critical intelligent component** of the system.

**Metaphor**: The main food scoring thread is like a senior analyst. It knows WHAT data it needs but not HOW to search the messy internet for it. It delegates search tasks to an "intern" - a specialized ReAct agent that:

1. **Understands the task** (e.g., "Find available sizes of Lay's chips")
2. **Plans multiple search strategies** (keyword variations, different phrasings)
3. **Executes searches** via SearXNG with query variations
4. **Aggregates results** from multiple queries
5. **Cleans and structures data**
6. **Reports back** with links for traceability

**Key Insight**: This agent doesn't just fetch web results - it **makes sense of them**. It's an active researcher, not a passive API caller.

### 6.2 Architecture

**Module**: `backend/app/agents/search_intern.py`

**Technology**: DSPy ReAct module with custom tools

**Ollama Model**: Use reasoning-optimized model (deepseek-r1:8b or qwen3:30b)

**Core Components**:

1. **Task Parser** - Understands what's being asked
2. **Query Planner** - Generates multiple search strategies
3. **Search Executor** - Runs queries via SearXNG
4. **Result Aggregator** - Merges and deduplicates results
5. **Data Extractor** - Parses structured data from web snippets
6. **Report Generator** - Formats findings with citations

### 6.3 DSPy Signature for Search Intern

```python
class SearchInternTask(dspy.Signature):
    """
    You are a research intern. Your job is to search the web for specific information
    about food products and compile a detailed report with source links.

    You have access to tools:
    - search_web(query, max_results): Query SearXNG, returns results
    - extract_from_snippet(snippet, data_type): Extract structured data from text
    - validate_url(url): Check if URL is accessible

    Your approach:
    1. Analyze the task to understand what data is needed
    2. Generate 3-5 different search queries (keyword variations)
    3. Execute each query and collect results
    4. Aggregate findings from all queries
    5. Extract structured data (e.g., sizes, prices, nutrition facts)
    6. Compile report with all source URLs

    Be thorough but efficient. Max 10 total queries.
    """

    task_description: str = dspy.InputField(
        desc="""
        What you need to find. Examples:
        - "Find available package sizes and prices for Lay's Classic chips"
        - "Get nutrition facts for Oreo cookies if not in OpenFoodFacts"
        - "Find WHO guidelines for daily sodium intake for heart health"
        """
    )

    product_hints: Dict[str, Any] = dspy.InputField(
        desc="""
        Any hints about the product (name, brand, price seen on package, etc.)
        Format as JSON dict. Can be empty if task is general (like guidelines).
        """
    )

    data_type: str = dspy.InputField(
        desc="""
        Type of data expected:
        - 'product_variants' (sizes, prices)
        - 'nutrition_facts'
        - 'health_guidelines'
        - 'similar_products'
        - 'ingredients_info'
        """
    )

    # Outputs

    queries_executed: List[str] = dspy.OutputField(
        desc="List of all search queries you ran (for transparency)"
    )

    total_results_found: int = dspy.OutputField(
        desc="Total number of raw results across all queries"
    )

    relevant_results: List[Dict] = dspy.OutputField(
        desc="""
        Filtered relevant results as JSON array.
        Each: {"url": "...", "title": "...", "snippet": "...", "extracted_data": {...}}
        """
    )

    summary: str = dspy.OutputField(
        desc="""
        Natural language summary of findings.
        E.g., "Found 3 size variants: 25g (₹10), 52g (₹20), 100g (₹40).
        Most popular size is 52g based on search frequency."
        """
    )

    structured_data: Dict[str, Any] = dspy.OutputField(
        desc="""
        Extracted structured data as JSON.
        Format depends on data_type:
        - product_variants: {"sizes": [...], "prices": [...]}
        - nutrition_facts: {"per_100g": {...}, "source": "url"}
        - health_guidelines: {"recommendation": "...", "source": "WHO/FDA/USDA"}
        """
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in data quality (0-1)"
    )

    sources: List[Dict] = dspy.OutputField(
        desc="""
        All source URLs with metadata for citations.
        [{"url": "...", "title": "...", "snippet": "...", "accessed": "timestamp"}]
        """
    )
```

### 6.4 Tool Definitions for ReAct Agent

**Tools Available to Intern Agent** (via FastMCP):

```python
# File: backend/app/agents/search_intern_tools.py

from fastmcp import FastMCP

mcp = FastMCP("Search Intern Tools")


@mcp.tool()
async def search_web(
    query: str,
    max_results: int = 10,
    categories: str = "general"
) -> Dict:
    """
    Search the web using SearXNG.

    Args:
        query: Search query string
        max_results: Max results to return (default 10)
        categories: SearXNG categories (default "general")

    Returns:
        Dict with:
        - query: str (query that was executed)
        - num_results: int
        - results: List[Dict] with url, title, content, engine
        - search_time_ms: int
    """
    import httpx
    from app.core.config import settings

    url = f"{settings.searxng_api_base}/search"
    params = {
        "q": query,
        "format": "json",
        "categories": categories,
        "lang": "en"
    }

    start = time.time()

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url, params=params)
        data = response.json()

    elapsed_ms = int((time.time() - start) * 1000)

    results = []
    for r in data.get("results", [])[:max_results]:
        results.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "content": r.get("content", "")[:500],  # Limit snippet length
            "engine": r.get("engine", "unknown"),
            "score": r.get("score", 0)
        })

    return {
        "query": query,
        "num_results": len(results),
        "results": results,
        "search_time_ms": elapsed_ms
    }


@mcp.tool()
async def extract_prices_and_sizes(snippet: str) -> Dict:
    """
    Extract price and size information from text snippet.

    Uses regex + LLM fallback for messy text.

    Args:
        snippet: Text snippet from search result

    Returns:
        Dict with:
        - prices: List[str] (e.g., ["₹20", "$5"])
        - sizes: List[str] (e.g., ["52g", "500ml"])
        - confidence: float
    """
    import re

    # Regex patterns for common price/size formats
    price_patterns = [
        r'₹\s*\d+',          # ₹20
        r'\$\s*\d+\.?\d*',   # $5.99
        r'Rs\.?\s*\d+',      # Rs 20
        r'\d+\s*rupees?',    # 20 rupees
    ]

    size_patterns = [
        r'\d+\.?\d*\s*g(?:rams?)?',  # 52g, 100 grams
        r'\d+\.?\d*\s*kg',           # 1kg
        r'\d+\.?\d*\s*ml',           # 500ml
        r'\d+\.?\d*\s*l(?:iters?)?', # 1 liter
    ]

    prices = []
    for pattern in price_patterns:
        prices.extend(re.findall(pattern, snippet, re.IGNORECASE))

    sizes = []
    for pattern in size_patterns:
        sizes.extend(re.findall(pattern, snippet, re.IGNORECASE))

    # Clean up
    prices = list(set(prices))
    sizes = list(set(sizes))

    confidence = 1.0 if (prices and sizes) else 0.5

    return {
        "prices": prices,
        "sizes": sizes,
        "confidence": confidence
    }


@mcp.tool()
async def extract_nutrition_facts(snippet: str) -> Dict:
    """
    Extract nutritional values from text snippet.

    Args:
        snippet: Text snippet mentioning nutrition

    Returns:
        Dict with nutrients found and confidence
    """
    import re

    nutrients = {}

    # Patterns: "Calories: 150", "Protein 5g", "Sugar: 10 grams"
    patterns = {
        'calories': r'calories?:?\s*(\d+\.?\d*)',
        'protein': r'protein:?\s*(\d+\.?\d*)\s*g',
        'carbs': r'carb(?:ohydrate)?s?:?\s*(\d+\.?\d*)\s*g',
        'fat': r'fat:?\s*(\d+\.?\d*)\s*g',
        'sugar': r'sugar:?\s*(\d+\.?\d*)\s*g',
        'sodium': r'sodium:?\s*(\d+\.?\d*)\s*mg',
        'fiber': r'fiber:?\s*(\d+\.?\d*)\s*g',
    }

    for nutrient, pattern in patterns.items():
        match = re.search(pattern, snippet, re.IGNORECASE)
        if match:
            nutrients[nutrient] = float(match.group(1))

    return {
        "nutrients": nutrients,
        "confidence": len(nutrients) / len(patterns)  # How many we found
    }


@mcp.tool()
async def validate_source_authority(url: str) -> Dict:
    """
    Assess the authority/credibility of a source URL.

    Args:
        url: URL to assess

    Returns:
        Dict with authority_score (0-1) and reason
    """
    from urllib.parse import urlparse

    domain = urlparse(url).netloc.lower()

    # Authoritative sources
    high_authority = [
        'who.int',          # World Health Organization
        'fda.gov',          # US FDA
        'usda.gov',         # USDA
        'nih.gov',          # National Institutes of Health
        'nhs.uk',           # UK National Health Service
        'health.harvard.edu', # Harvard Health
        'mayoclinic.org',   # Mayo Clinic
    ]

    medium_authority = [
        'eatthis.com',
        'healthline.com',
        'webmd.com',
        'medicalnewstoday.com',
    ]

    if any(auth in domain for auth in high_authority):
        return {"authority_score": 0.95, "reason": "Official health authority"}

    elif any(auth in domain for auth in medium_authority):
        return {"authority_score": 0.7, "reason": "Reputable health website"}

    elif 'amazon' in domain or 'flipkart' in domain or 'bigbasket' in domain:
        return {"authority_score": 0.6, "reason": "E-commerce (product info may be accurate)"}

    else:
        return {"authority_score": 0.4, "reason": "Unknown source"}
```

### 6.5 ReAct Agent Implementation

```python
# File: backend/app/agents/search_intern.py

import dspy
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SearchInternAgent(dspy.Module):
    """
    Autonomous ReAct agent that researches information on the web.

    Uses tools:
    - search_web()
    - extract_prices_and_sizes()
    - extract_nutrition_facts()
    - validate_source_authority()

    Follows ReAct pattern: Thought → Action → Observation → Repeat
    """

    def __init__(self, model: str = "deepseek-r1:8b", max_iterations: int = 10):
        super().__init__()

        # Use reasoning-optimized model
        lm = dspy.LM(
            f'ollama_chat/{model}',
            api_base='http://localhost:11434',
            api_key=''
        )
        dspy.configure(lm=lm)

        # Import tools
        from app.agents.search_intern_tools import (
            search_web,
            extract_prices_and_sizes,
            extract_nutrition_facts,
            validate_source_authority
        )

        # Create ReAct agent with tools
        self.agent = dspy.ReAct(
            signature=SearchInternTask,
            tools=[
                search_web,
                extract_prices_and_sizes,
                extract_nutrition_facts,
                validate_source_authority
            ],
            max_iters=max_iterations
        )

        logger.info(f"SearchInternAgent initialized with {model}, max_iters={max_iterations}")

    async def execute_task(
        self,
        task_description: str,
        product_hints: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Execute a search research task.

        Args:
            task_description: What to search for
            product_hints: Product info (name, brand, price hints, etc.)
            data_type: Type of data expected (product_variants, nutrition_facts, etc.)

        Returns:
            Dict with:
            - summary: str
            - structured_data: Dict
            - sources: List[Dict]
            - queries_executed: List[str]
            - confidence: float
        """
        logger.info(f"SearchIntern executing task: {task_description}")

        try:
            # Run ReAct agent
            result = await self.agent(
                task_description=task_description,
                product_hints=product_hints,
                data_type=data_type
            )

            # Parse outputs
            return {
                "summary": result.summary,
                "structured_data": result.structured_data,
                "sources": result.sources,
                "queries_executed": result.queries_executed,
                "total_results": result.total_results_found,
                "confidence": result.confidence
            }

        except Exception as e:
            logger.error(f"SearchIntern error: {e}", exc_info=True)

            # Fallback: single direct search
            from app.agents.search_intern_tools import search_web

            fallback_query = f"{product_hints.get('product_name', '')} {data_type}".strip()
            fallback_results = await search_web(fallback_query, max_results=5)

            return {
                "summary": f"Fallback search executed: {fallback_query}",
                "structured_data": {},
                "sources": fallback_results["results"],
                "queries_executed": [fallback_query],
                "total_results": fallback_results["num_results"],
                "confidence": 0.3  # Low confidence for fallback
            }
```

### 6.6 Example ReAct Agent Reasoning Flow

**Task**: "Find available package sizes and prices for Lay's Classic chips"

**Product Hints**: `{"product_name": "Lay's Classic", "brand": "Lay's", "price_hint": "₹20"}`

**Expected ReAct Trace**:

```bash
Iteration 1:
  Thought: "I need to find different sizes of Lay's Classic chips. Let me start with a broad search."
  Action: search_web("Lay's Classic chips sizes available India", max_results=10)
  Observation: Found 10 results, many from e-commerce sites.

Iteration 2:
  Thought: "I see multiple e-commerce results. Let me try a more specific query for small packs."
  Action: search_web("Lay's Classic 20 rupees pack size", max_results=5)
  Observation: Found results mentioning "₹20 pack is 52g"

Iteration 3:
  Thought: "Good! I found one size. Let me search for other price points."
  Action: search_web("Lay's Classic 10 rupees 40 rupees pack size", max_results=5)
  Observation: Found "₹10 = 25g", "₹40 = 90g" in snippets

Iteration 4:
  Thought: "Now I have multiple sizes. Let me extract structured data from these snippets."
  Action: extract_prices_and_sizes("Lay's Classic chips: ₹10 for 25g pack, ₹20 for 52g...")
  Observation: {"prices": ["₹10", "₹20", "₹40"], "sizes": ["25g", "52g", "90g"]}

Iteration 5:
  Thought: "I should validate the authority of my sources."
  Action: validate_source_authority("https://www.amazon.in/...")
  Observation: {"authority_score": 0.6, "reason": "E-commerce"}

Iteration 6:
  Thought: "I have enough information. Let me compile the report."
  Action: FINISH

Final Output:
  summary: "Found 3 size variants for Lay's Classic chips in India market: 25g (₹10), 52g (₹20), 90g (₹40). Based on the price hint (₹20), the scanned product is most likely the 52g variant."
  structured_data: {
    "sizes": ["25g", "52g", "90g"],
    "prices": ["₹10", "₹20", "₹40"],
    "best_match": {"price": "₹20", "size": "52g"}
  }
  sources: [
    {"url": "https://amazon.in/...", "title": "Lay's Classic 52g"},
    {"url": "https://bigbasket.com/...", "title": "Lay's Chips variants"}
  ]
  queries_executed: [
    "Lay's Classic chips sizes available India",
    "Lay's Classic 20 rupees pack size",
    "Lay's Classic 10 rupees 40 rupees pack size"
  ]
  confidence: 0.85
```

**Key Features**:

1. **Multi-query strategy**: Doesn't rely on single search
2. **Query variation**: Tries different phrasings
3. **Tool usage**: Uses extract_* tools to parse data
4. **Source validation**: Checks authority of sources
5. **Reasoning transparency**: All steps logged
6. **Source linking**: Every finding has URL citation

### 6.7 Async Execution Pattern

**Critical**: This agent must run **asynchronously** without blocking the main food scanning pipeline.

**Pattern** (from DSPy async tutorial):

```python
# In calling code (e.g., OCR pipeline Stage 4)

import asyncio
from app.agents.search_intern import SearchInternAgent

# Create agent instance
intern = SearchInternAgent(model="deepseek-r1:8b", max_iterations=10)

# Run as async task
async def main():
    task = {
        "task_description": "Find sizes for Lay's chips",
        "product_hints": {"product_name": "Lay's Classic"},
        "data_type": "product_variants"
    }

    # This runs in background, doesn't block
    result = await intern.execute_task(**task)

    print(result["summary"])
    print(result["structured_data"])

# Execute
asyncio.run(main())
```

**Timeout Handling**:

- Agent has max 10 iterations (configurable)
- Each search has 5s timeout
- Total agent timeout: 60s
- If timeout exceeded, return partial results with low confidence

### 6.8 Performance Optimization

**Latency Concerns**:

- Each LLM call: ~2-5s (with deepseek-r1:8b on good hardware)
- 10 iterations max = potentially 50s
- Search queries: ~1s each

**Optimization Strategies**:

1. **Reduce Iterations**:
   - For simple tasks (product size): max 5 iterations
   - For complex tasks (nutrition research): max 10 iterations

2. **Parallel Search Queries**:

   ```python
   # Instead of sequential searches, run in parallel
   queries = ["query1", "query2", "query3"]

   results = await asyncio.gather(*[
       search_web(q) for q in queries
   ])
   ```

3. **Cache Common Searches**:
   - If searching for "Lay's Classic sizes", cache result
   - Store in Redis with 24h TTL
   - Key: hash(product_name + task_type)

4. **Use Smaller Model for Simple Tasks**:
   - Product size search: qwen3:8b (faster)
   - Health guidelines: qwen3:30b (better reasoning)

**Target Performance**:

- Simple product search: < 10s
- Complex nutrition research: < 30s
- Cached results: < 1s

---

## 7. Food History Tracking System

### 7.1 Overview

Track user's food consumption over time to enable **context-aware scoring**.

**Key Principle**: The same food can be "good" or "bad" depending on:

- What user already ate today
- Time of day
- How often they eat this item
- Current moderation level

**Example**:

- Chocolate at 9 AM after healthy breakfast → Score: 7/10 (treat is fine)
- Chocolate at 9 PM after 3 sugary items → Score: 3/10 (sugar overload)

### 7.2 Data Storage Structure

**Location**: `backend/data/scan_history/{username}/`

**Files**:

- `2025-11-14.json` - Today's scans
- `2025-11-week46.json` - This week's summary
- `2025-11.json` - This month's summary (optional)

**Daily File Schema**:

```json
{
  "date": "2025-11-14",
  "user_name": "john",
  "scans": [
    {
      "scan_id": "uuid",
      "timestamp": "2025-11-14T09:30:00Z",
      "product_name": "Lay's Classic Chips",
      "brand": "Lay's",
      "serving_size": "52g",
      "servings_consumed": 1.0,

      "calories": 273,
      "protein_g": 3.5,
      "carbs_g": 31.2,
      "fat_g": 15.6,
      "sugar_g": 1.0,
      "sodium_mg": 312,
      "fiber_g": 2.6,

      "time_of_day": "morning",
      "meal_type": "snack",

      "score": 6.5,
      "verdict": "moderate",

      "moderation_level": "within"
    }
  ],

  "daily_totals": {
    "calories": 1450,
    "protein_g": 45.2,
    "carbs_g": 180.5,
    "fat_g": 52.3,
    "sugar_g": 28.5,
    "sodium_mg": 1850,
    "fiber_g": 18.2
  },

  "vs_targets": {
    "calories": 0.725,
    "sugar_g": 1.14,
    "sodium_mg": 0.82
  },

  "flags": {
    "exceeded_sugar": true,
    "exceeded_sodium": false,
    "exceeded_calories": false
  }
}
```

### 7.3 History Tracker Module

**File**: `backend/app/services/history/tracker.py`

```python
"""
Food scan history tracker.

Responsibilities:
- Record each scan
- Calculate daily totals
- Track moderation levels
- Provide context for scoring
"""

import aiofiles
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.models.schemas import FoodScanRecord, DailySummary, WeeklySummary


class HistoryTracker:
    """Manages food scan history for users."""

    def __init__(self, history_dir: str = "./data/scan_history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_dir(self, user_name: str) -> Path:
        """Get user's history directory."""
        user_dir = self.history_dir / user_name
        user_dir.mkdir(exist_ok=True)
        return user_dir

    def _get_daily_file(self, user_name: str, date_str: str) -> Path:
        """Get path to daily history file."""
        user_dir = self._get_user_dir(user_name)
        return user_dir / f"{date_str}.json"

    async def record_scan(
        self,
        user_name: str,
        scan_record: FoodScanRecord
    ) -> DailySummary:
        """
        Record a food scan and update daily summary.

        Args:
            user_name: Username
            scan_record: Scan details

        Returns:
            Updated daily summary
        """
        date_str = scan_record.timestamp.strftime("%Y-%m-%d")
        daily_file = self._get_daily_file(user_name, date_str)

        # Load existing or create new
        if daily_file.exists():
            async with aiofiles.open(daily_file, 'r') as f:
                content = await f.read()
                daily_data = json.loads(content)
                daily_summary = DailySummary(**daily_data)
        else:
            daily_summary = DailySummary(
                date=date_str,
                user_name=user_name
            )

        # Add scan
        daily_summary.scans.append(scan_record)

        # Recalculate totals
        daily_summary = self._calculate_daily_totals(daily_summary)

        # Save
        async with aiofiles.open(daily_file, 'w') as f:
            await f.write(daily_summary.model_dump_json(indent=2))

        return daily_summary

    def _calculate_daily_totals(self, summary: DailySummary) -> DailySummary:
        """Calculate totals from all scans."""
        summary.total_calories = sum(
            scan.calories * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_protein_g = sum(
            scan.protein_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_carbs_g = sum(
            scan.carbs_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_fat_g = sum(
            scan.fat_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_sugar_g = sum(
            scan.sugar_g * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_sodium_mg = sum(
            scan.sodium_mg * scan.servings_consumed
            for scan in summary.scans
        )
        summary.total_fiber_g = sum(
            (scan.fiber_g or 0) * scan.servings_consumed
            for scan in summary.scans
        )

        return summary

    async def get_today_summary(self, user_name: str) -> Optional[DailySummary]:
        """Get today's consumption summary."""
        today_str = date.today().strftime("%Y-%m-%d")
        daily_file = self._get_daily_file(user_name, today_str)

        if not daily_file.exists():
            return None

        async with aiofiles.open(daily_file, 'r') as f:
            content = await f.read()
            return DailySummary(**json.loads(content))

    async def get_week_summary(
        self,
        user_name: str,
        weeks_back: int = 0
    ) -> WeeklySummary:
        """
        Get weekly consumption summary.

        Args:
            user_name: Username
            weeks_back: How many weeks back (0 = current week)

        Returns:
            Weekly summary with daily breakdowns
        """
        # Calculate week start date
        today = date.today()
        week_start = today - timedelta(days=today.weekday() + (weeks_back * 7))

        daily_summaries = []

        for i in range(7):
            day = week_start + timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")

            daily_file = self._get_daily_file(user_name, day_str)

            if daily_file.exists():
                async with aiofiles.open(daily_file, 'r') as f:
                    content = await f.read()
                    daily_summaries.append(DailySummary(**json.loads(content)))

        # Calculate weekly stats
        weekly = WeeklySummary(
            week_start=week_start.strftime("%Y-%m-%d"),
            user_name=user_name,
            daily_summaries=daily_summaries
        )

        if daily_summaries:
            weekly.avg_daily_calories = sum(
                d.total_calories for d in daily_summaries
            ) / len(daily_summaries)

            weekly.avg_daily_sugar_g = sum(
                d.total_sugar_g for d in daily_summaries
            ) / len(daily_summaries)

            weekly.avg_daily_sodium_mg = sum(
                d.total_sodium_mg for d in daily_summaries
            ) / len(daily_summaries)

        return weekly

    async def calculate_moderation_level(
        self,
        user_name: str,
        new_scan: FoodScanRecord,
        user_targets: Dict[str, float]
    ) -> str:
        """
        Calculate if user is within/approaching/exceeding moderation.

        Args:
            user_name: Username
            new_scan: The scan being evaluated
            user_targets: Daily nutritional targets

        Returns:
            "within", "approaching", or "exceeding"
        """
        # Get today's summary (before adding new scan)
        today = await self.get_today_summary(user_name)

        if not today:
            # First scan of the day
            return "within"

        # Calculate what totals would be AFTER this scan
        projected_calories = today.total_calories + (
            new_scan.calories * new_scan.servings_consumed
        )
        projected_sugar = today.total_sugar_g + (
            new_scan.sugar_g * new_scan.servings_consumed
        )
        projected_sodium = today.total_sodium_mg + (
            new_scan.sodium_mg * new_scan.servings_consumed
        )

        # Check against targets
        calories_pct = projected_calories / user_targets.get("calories", 2000)
        sugar_pct = projected_sugar / user_targets.get("sugar_g", 30)
        sodium_pct = projected_sodium / user_targets.get("sodium_mg", 2300)

        # Determine moderation level
        max_pct = max(calories_pct, sugar_pct, sodium_pct)

        if max_pct < 0.8:
            return "within"
        elif max_pct < 1.0:
            return "approaching"
        else:
            return "exceeding"


# Global instance
history_tracker = HistoryTracker()
```

### 7.4 Context Retrieval for Scoring

**Function**: `get_consumption_context()`

**Purpose**: Provide scoring engine with today's and week's context.

```python
async def get_consumption_context(
    user_name: str,
    scan_time: datetime
) -> Dict[str, Any]:
    """
    Get consumption context for scoring.

    Returns:
        Dict with:
        - today_summary: DailySummary
        - week_summary: WeeklySummary
        - time_of_day: str (morning/afternoon/evening/night)
        - recent_scans: List[FoodScanRecord] (last 3)
    """
    from app.services.history.tracker import history_tracker

    today = await history_tracker.get_today_summary(user_name)
    week = await history_tracker.get_week_summary(user_name, weeks_back=0)

    # Determine time of day
    hour = scan_time.hour
    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 21:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    # Get recent scans (for pattern detection)
    recent_scans = today.scans[-3:] if today else []

    return {
        "today_summary": today.model_dump() if today else None,
        "week_summary": week.model_dump(),
        "time_of_day": time_of_day,
        "recent_scans": [s.model_dump() for s in recent_scans]
    }
```

**Usage in Scoring**:

```python
# In scoring engine
context = await get_consumption_context(user_name, datetime.now())

# Pass to DSPy scoring agent
scoring_result = await scoring_agent.score(
    nutrition_data=nutrition_data,
    user_profile=user_profile,
    consumption_context=context  # <-- CONTEXT HERE
)
```

---

## 8. Context-Aware Scoring Engine

### 8.1 Overview

The scoring engine must consider:

1. **Intrinsic nutritional quality** of the food
2. **User's health profile** (goals, risks)
3. **Consumption context** (today's intake, time, patterns)
4. **Moderation principle** (anything is OK in moderation)

**Base Assumption**: Unless toxic/addictive, ALL foods are permitted in moderation. The system guides, not restricts.

### 8.2 Scoring Formula

```bash
Final Score = Base Score × Context Multiplier × Time Multiplier

Where:
- Base Score (0-10): Intrinsic quality + goal alignment
- Context Multiplier (0.5-1.5): Based on today's consumption
- Time Multiplier (0.8-1.2): Based on time of day appropriateness
```

**Example**:

- Chocolate bar: Base Score = 6.0 (moderate sugar, some enjoyment value)
- Context: User already had 25g sugar today (target: 30g)
  - Context Multiplier = 0.7 (approaching limit)
- Time: 9 PM (late for sugar)
  - Time Multiplier = 0.8
- **Final Score = 6.0 × 0.7 × 0.8 = 3.36 → Verdict: "avoid" (for now)**

But same chocolate at 10 AM with only 5g sugar consumed:

- **Final Score = 6.0 × 1.2 × 1.0 = 7.2 → Verdict: "good" (enjoy!)**

### 8.3 DSPy Signature for Context-Aware Scoring

```python
class ContextAwareNutritionScoring(dspy.Signature):
    """
    Score food item against user's health profile AND consumption context.

    Philosophy:
    - Everything is OK in moderation
    - Context matters: same food can be good or bad depending on what user already ate
    - Time matters: breakfast foods vs dinner foods
    - Pattern matters: frequency of consumption affects recommendation

    Output a score (0-10) and verdict (good/moderate/avoid) with reasoning.
    """

    # Inputs

    nutrition_data: str = dspy.InputField(
        desc="Nutritional data of scanned food as JSON string"
    )

    user_profile: str = dspy.InputField(
        desc="""
        User health profile as JSON:
        - goals (weight_loss, muscle_building, diabetes, etc.)
        - daily_targets (calories, sugar, sodium, etc.)
        - health_risks (diabetes_risk, cardiovascular_risk, etc.)
        - allergies
        """
    )

    consumption_context: str = dspy.InputField(
        desc="""
        Today's and week's consumption context as JSON:
        - today_summary: {total_calories, total_sugar_g, total_sodium_mg, ...}
        - time_of_day: morning/afternoon/evening/night
        - recent_scans: last 3 items eaten
        - moderation_level: within/approaching/exceeding
        """
    )

    # Outputs

    base_score: float = dspy.OutputField(
        desc="Intrinsic nutritional quality score (0-10), ignoring context"
    )

    context_adjustment: str = dspy.OutputField(
        desc="""
        How context affects score. Format as reasoning:
        "User already consumed X calories (Y% of target). Sugar at Z (W% of target).
        Therefore, adjusting score down/up by N points."
        """
    )

    final_score: float = dspy.OutputField(
        desc="Final score (0-10) after context adjustment"
    )

    verdict: str = dspy.OutputField(
        desc="Overall verdict: 'good', 'moderate', or 'avoid'"
    )

    reasoning: str = dspy.OutputField(
        desc="""
        Complete reasoning in natural language with citations.
        Format: "This product has X calories and Y sugar [1]. Given your goal of Z,
        and that you've already consumed A calories today, this would bring you to B%
        of your target [2]. Recommendation: ..."
        """
    )

    warnings: List[str] = dspy.OutputField(
        desc="""
        Specific warnings as JSON array.
        Format: ["High sodium (350mg) - you've already had 1200mg today", ...]
        Max 3 warnings.
        """
    )

    highlights: List[str] = dspy.OutputField(
        desc="""
        Positive aspects as JSON array.
        Format: ["Good protein source (12g)", "Low sugar", ...]
        Max 3 highlights.
        """
    )

    moderation_message: str = dspy.OutputField(
        desc="""
        Message about moderation status.
        Examples:
        - "You're well within your limits. Enjoy!"
        - "You're approaching your daily sugar limit. Consider this your last sweet treat today."
        - "You've exceeded your sodium target. Skip salty snacks for the rest of the day."
        """
    )

    timing_recommendation: str = dspy.OutputField(
        desc="""
        Time-based recommendation.
        Examples:
        - "Great breakfast choice! High protein to start your day."
        - "This is quite heavy for late night. Consider a lighter option."
        - "Perfect afternoon snack timing."
        """
    )

    confidence: float = dspy.OutputField(
        desc="Confidence in scoring (0-1)"
    )
```

### 8.4 Scoring Module Implementation

```python
# File: backend/app/services/scoring/context_aware_scorer.py

import dspy
from typing import Dict, Any
import json

from app.models.schemas import (
    NutritionData, EnhancedUserProfile, DetailedAssessment, ShortAssessment
)
from app.services.history.context import get_consumption_context
from app.services.citation_manager import CitationManager


class ContextAwareScoringEngine(dspy.Module):
    """
    Context-aware nutrition scoring using DSPy.

    Considers:
    - Intrinsic nutrition quality
    - User goals and health profile
    - Today's consumption
    - Time of day
    - Recent eating patterns
    """

    def __init__(self, model: str = "qwen3:30b"):
        super().__init__()

        # Use best model for reasoning
        lm = dspy.LM(f'ollama_chat/{model}', api_base='http://localhost:11434')
        dspy.configure(lm=lm)

        # Use ChainOfThought for step-by-step reasoning
        self.scorer = dspy.ChainOfThought(ContextAwareNutritionScoring)

        self.citation_manager = CitationManager()

    async def score(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile,
        scan_time: datetime
    ) -> DetailedAssessment:
        """
        Score food with full context awareness.

        Args:
            nutrition_data: Food nutritional data
            user_profile: User health profile
            scan_time: When scan occurred

        Returns:
            Detailed assessment with context-adjusted score
        """
        # 1. Get consumption context
        context = await get_consumption_context(user_profile.name, scan_time)

        # 2. Check for allergens (immediate block)
        if self._has_allergen_violation(nutrition_data, user_profile):
            return self._create_allergen_block_assessment(
                nutrition_data, user_profile, context
            )

        # 3. Run DSPy scoring
        result = await self.scorer(
            nutrition_data=nutrition_data.model_dump_json(),
            user_profile=user_profile.model_dump_json(),
            consumption_context=json.dumps(context)
        )

        # 4. Parse and structure result
        assessment = DetailedAssessment(
            product_name=nutrition_data.product_name,
            brand=nutrition_data.brand,
            user_name=user_profile.name,

            consumption_context=context,

            base_score=float(result.base_score),
            context_adjusted_score=float(result.final_score),
            final_score=float(result.final_score),

            verdict=self._parse_verdict(result.verdict),

            reasoning_steps=[result.context_adjustment, result.reasoning],
            scientific_rationale=result.reasoning,

            moderation_impact=result.moderation_message,
            time_of_day_impact=result.timing_recommendation,

            moderate_warnings=self._parse_list(result.warnings),
            positive_highlights=self._parse_list(result.highlights),

            citations=self.citation_manager.generate_citation_objects(),

            confidence=float(result.confidence)
        )

        return assessment

    def _has_allergen_violation(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile
    ) -> bool:
        """Check if food contains user's allergens."""
        user_allergens = [a.lower() for a in user_profile.allergies]
        food_allergens = [a.lower() for a in nutrition_data.allergens]

        for allergen in user_allergens:
            if any(allergen in fa for fa in food_allergens):
                return True

            # Also check ingredients
            ingredients_text = " ".join(nutrition_data.ingredients).lower()
            if allergen in ingredients_text:
                return True

        return False

    def _create_allergen_block_assessment(
        self,
        nutrition_data: NutritionData,
        user_profile: EnhancedUserProfile,
        context: Dict
    ) -> DetailedAssessment:
        """Create assessment for allergen violation (auto-block)."""
        matching_allergens = []

        for allergen in user_profile.allergies:
            if any(allergen.lower() in a.lower() for a in nutrition_data.allergens):
                matching_allergens.append(allergen)

        return DetailedAssessment(
            product_name=nutrition_data.product_name,
            brand=nutrition_data.brand,
            user_name=user_profile.name,
            consumption_context=context,

            base_score=0.0,
            context_adjusted_score=0.0,
            final_score=0.0,
            verdict="avoid",

            reasoning_steps=["Allergen check: FAILED"],
            scientific_rationale=f"This product contains allergens you're allergic to: {', '.join(matching_allergens)}. Do NOT consume.",

            critical_warnings=[f"⚠️ ALLERGEN ALERT: Contains {allergen}" for allergen in matching_allergens],

            moderation_impact="N/A - Safety issue",
            time_of_day_impact="N/A - Safety issue",

            citations=[],
            confidence=1.0
        )

    def _parse_verdict(self, verdict_str: str) -> str:
        """Parse verdict from LLM output."""
        v = verdict_str.lower()
        if "good" in v:
            return "good"
        elif "avoid" in v:
            return "avoid"
        else:
            return "moderate"

    def _parse_list(self, list_str: str) -> List[str]:
        """Parse list from LLM output (JSON or comma-separated)."""
        try:
            return json.loads(list_str)
        except:
            return [item.strip() for item in list_str.split(",") if item.strip()]


# Global instance
context_aware_scorer = ContextAwareScoringEngine()
```

---

## 9. Assessment Generation System

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

```bash
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

## 10. API Contracts

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

## 11. Async Flow Diagrams

### 11.1 Onboarding Flow

**Participants**: Client (WebSocket), OnboardingHandler, ConversationalAgent, ProfileStore

```bash
Client                  OnboardingHandler              ConversationalAgent              ProfileStore
  |                              |                              |                              |
  |--start_onboarding----------->|                              |                              |
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
  |                              |--save_profile()-------------------------------------------->|
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

```bash
Client          ScanHandler     ImageProcessor  NutritionRetriever  SearchIntern  HistoryTracker  ScoringEngine  AssessmentBuilder
  |                  |                  |                  |                  |                  |                  |
  |--start_scan----->|                  |                  |                  |                  |                  |
  |                  |--generate UUID   |                  |                  |                  |                  |
  |<--scan_started---|                  |                  |                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 1: Image Processing--------->|                  |                  |                  |
  |<--scan_progress--|                  |                  |                  |                  |                  |
  |                  |                  |--preprocess()    |                  |                  |                  |
  |                  |                  |--detect_barcode()|                  |                  |                  |
  |                  |                  |--ocr_extract()   |                  |                  |                  |
  |                  |                  |--DSPy.ExtractNutritionalEntities()  |                  |                  |
  |                  |<--return (barcode?, ocr_data, gaps)-|                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 2: Nutrition Retrieval------>|                  |                  |                  |
  |<--scan_progress--|                  |                  |                  |                  |                  |
  |                  |                  |                  |--if barcode----->|                  |                  |
  |                  |                  |                  |  lookup_barcode()|                  |                  |
  |                  |                  |                  |<--return product-|                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |                  |                  |--if gaps exist---|                  |                  |
  |                  |                  |                  |  delegate_to_intern()-------------->|                  |
  |                  |                  |                  |                  |--DSPy.ReAct()    |                  |
  |                  |                  |                  |                  |  [10 iterations] |                  |
  |                  |                  |                  |<--return report--|                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |                  |                  |--merge_data()    |                  |                  |
  |                  |<--return nutrition_data-------------|                  |                  |                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 3: Load Context------------->|                  |                  |                  |
  |<--scan_progress--|                  |                  |                  |--get_today()---->|                  |
  |                  |                  |                  |                  |<--return summary-|                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 4: Scoring-------------------------------------------------------->|                  |
  |<--scan_progress--|                  |                  |                  |                  |                  |
  |                  |                  |                  |                  |                  |--DSPy.ContextAwareScoring()
  |                  |                  |                  |                  |                  |<--return result--|
  |                  |<--------------------------------------------------------------------------|                  |
  |                  |                  |                  |                  |                  |                  |
  |                  |--Stage 5: Assessment Generation------------------------------------------------------------->|
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

```bash
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
      |-await aiofiles.open(mode='w')->|
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

## 12. Module Decoupling Strategy

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

## 13. Threading & Concurrency Patterns

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

## 14. Function-Level Specifications

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
