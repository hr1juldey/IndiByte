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
13. [Threading & Concurrency](#13-threading--concurrency)
14. [Function-Level Specifications](#14-function-level-specifications)

---

## 1. System Architecture Overview

### 1.1 Core Principle: Modular Independence

**Design Philosophy**: Every module can function as a standalone service. If any component fails, others continue to operate with graceful degradation.

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│         (React + Vite + shadcn/ui + Socket.IO Client)          │
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

This document will be **extremely detailed** (100+ pages) with function-level specifications, data flow diagrams, async patterns, and complete decoupling strategies. Shall I continue?