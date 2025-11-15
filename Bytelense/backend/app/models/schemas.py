"""
Bytelense Data Models - Pydantic v2 Schemas (ENHANCED VERSION)

Complete implementation of all data models from LLD.md Section 2.
This file replaces schemas.py with full LLD compliance.

Usage:
    After review, replace schemas.py with this file:
    mv schemas.py schemas_old.py
    mv schemas_v2.py schemas.py
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Section 2.1: User Profile Models (LLD Section 2.2)
# ============================================================================

class Demographics(BaseModel):
    """User demographic information."""

    model_config = ConfigDict(str_strip_whitespace=True)

    age: int = Field(..., ge=1, le=120, description="Age in years")
    gender: Literal["male", "female", "other"] = Field(..., description="Biological gender")
    height_cm: float = Field(..., ge=50, le=300, description="Height in centimeters")
    weight_kg: float = Field(..., ge=20, le=500, description="Weight in kilograms")


class LifestyleHabits(BaseModel):
    """User lifestyle and daily habits."""

    sleep_hours: float = Field(..., ge=0, le=24, description="Average sleep hours per night")
    work_style: Literal["desk_job", "light_activity", "physical_job"] = Field(
        ..., description="Primary work activity level"
    )
    exercise_frequency: Literal[
        "rarely", "1-2_times_week", "3-4_times_week", "5_times_week", "daily"
    ] = Field(..., description="Exercise frequency per week")
    commute_type: Literal["car", "public_transport", "bike", "walk"] = Field(
        ..., description="Primary commute method"
    )
    smoking: Literal["yes", "no", "occasionally"] = Field(
        ..., description="Smoking status"
    )
    alcohol: Literal["none", "light", "moderate", "heavy"] = Field(
        ..., description="Alcohol consumption level"
    )
    stress_level: Literal["low", "moderate", "high"] = Field(
        ..., description="Self-reported stress level"
    )


class HealthMetrics(BaseModel):
    """Calculated health metrics (BMI, BMR, TDEE, etc.)."""

    bmi: float = Field(..., ge=10, le=100, description="Body Mass Index")
    bmi_category: Literal["underweight", "normal", "overweight", "obese"] = Field(
        ..., description="BMI category"
    )
    bmr: float = Field(..., ge=800, le=5000, description="Basal Metabolic Rate (kcal/day)")
    tdee: float = Field(..., ge=1000, le=10000, description="Total Daily Energy Expenditure (kcal/day)")
    daily_energy_target: float = Field(
        ..., ge=1200, le=10000, description="Target calories based on goal (kcal/day)"
    )
    health_risks: List[str] = Field(default_factory=list, description="Identified health risk factors")


class HealthGoals(BaseModel):
    """User health and fitness goals."""

    primary_goal: Literal["lose_weight", "maintain_weight", "gain_muscle"] = Field(
        ..., description="Primary health goal"
    )
    target_weight_kg: Optional[float] = Field(
        None, ge=20, le=500, description="Target weight in kg (if applicable)"
    )
    timeline_weeks: Optional[int] = Field(
        None, ge=1, le=104, description="Timeline to achieve goal (weeks)"
    )


class FoodPreferences(BaseModel):
    """User food preferences and restrictions."""

    cuisine_preferences: List[str] = Field(
        default_factory=list, description="Preferred cuisines (e.g., 'indian', 'italian')"
    )
    dietary_restrictions: List[str] = Field(
        default_factory=list, description="Dietary restrictions (e.g., 'vegetarian', 'vegan')"
    )
    allergens: List[str] = Field(
        default_factory=list, description="Allergens to avoid (CRITICAL)"
    )
    disliked_ingredients: List[str] = Field(
        default_factory=list, description="Ingredients user dislikes"
    )


class DailyTargets(BaseModel):
    """Daily nutritional targets based on goals."""

    calories: float = Field(..., ge=1200, le=10000, description="Daily calorie target")
    protein_g: float = Field(..., ge=0, le=500, description="Protein target (grams)")
    carbs_g: float = Field(..., ge=0, le=1000, description="Carbohydrate target (grams)")
    fat_g: float = Field(..., ge=0, le=300, description="Fat target (grams)")
    fiber_g: float = Field(..., ge=0, le=100, description="Fiber target (grams)")
    sugar_g: float = Field(..., ge=0, le=200, description="Sugar limit (grams)")
    sodium_mg: float = Field(..., ge=0, le=5000, description="Sodium limit (milligrams)")


class EnhancedUserProfile(BaseModel):
    """Complete user profile with all data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, description="Unique username")
    demographics: Demographics
    lifestyle_habits: LifestyleHabits
    health_metrics: HealthMetrics
    goals: HealthGoals
    food_preferences: FoodPreferences
    daily_targets: DailyTargets
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Section 2.2: Nutrition Data Models (LLD Section 2.3)
# ============================================================================

class NutritionData(BaseModel):
    """Nutritional information for a food product."""

    product_name: str = Field(..., min_length=1, description="Product name")
    brand: Optional[str] = Field(None, description="Brand name")
    net_quantity: Optional[str] = Field(None, description="Package size (e.g., '100g', '500ml')")
    serving_size: Optional[str] = Field(None, description="Serving size")

    # Nutrition per 100g (standard format)
    calories_per_100g: Optional[float] = Field(None, ge=0, description="Energy (kcal)")
    protein_per_100g: Optional[float] = Field(None, ge=0, description="Protein (g)")
    carbs_per_100g: Optional[float] = Field(None, ge=0, description="Carbohydrates (g)")
    fat_per_100g: Optional[float] = Field(None, ge=0, description="Fat (g)")
    saturated_fat_per_100g: Optional[float] = Field(None, ge=0, description="Saturated fat (g)")
    fiber_per_100g: Optional[float] = Field(None, ge=0, description="Fiber (g)")
    sugar_per_100g: Optional[float] = Field(None, ge=0, description="Sugar (g)")
    sodium_per_100g: Optional[float] = Field(None, ge=0, description="Sodium (mg)")

    # Additional info
    ingredients_list: List[str] = Field(default_factory=list, description="Ingredients")
    allergens: List[str] = Field(default_factory=list, description="Allergen warnings")

    # Metadata
    barcode: Optional[str] = Field(None, description="Product barcode")
    source: Literal["openfoodfacts", "ocr", "searxng", "manual"] = Field(
        ..., description="Data source"
    )
    confidence: float = Field(..., ge=0, le=1, description="Data quality confidence")


# ============================================================================
# Section 2.3: OCR Processing Models (LLD Section 2.4)
# ============================================================================

class StructuredNutritionExtraction(BaseModel):
    """Structured data extracted from OCR using DSPy."""

    product_name: Optional[str] = Field(None, description="Extracted product name")
    brand: Optional[str] = Field(None, description="Extracted brand")
    net_quantity: Optional[str] = Field(None, description="Package size")
    nutrients_per_100g: Dict[str, float] = Field(
        default_factory=dict, description="Extracted nutrition values"
    )
    ingredients_list: List[str] = Field(default_factory=list)
    allergen_warnings: List[str] = Field(default_factory=list)
    package_indicators: List[str] = Field(
        default_factory=list, description="E.g., 'multi-pack', 'family size'"
    )
    confidence: float = Field(..., ge=0, le=1, description="Extraction confidence")
    missing_critical_info: List[str] = Field(
        default_factory=list, description="List of missing critical fields"
    )


class RawOCRExtraction(BaseModel):
    """Complete output from OCR enhancement pipeline."""

    barcode: Optional[str] = Field(None, description="Detected barcode")
    ocr_text: str = Field(..., description="Raw OCR output")
    structured_data: StructuredNutritionExtraction
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence")
    gaps: List[str] = Field(
        default_factory=list, description="Missing fields that need Search Intern"
    )


# ============================================================================
# Section 2.4: Search Intern Agent Models (LLD Section 2.5)
# ============================================================================

class InternAgentReport(BaseModel):
    """Report from Search Intern ReAct agent."""

    queries_executed: List[str] = Field(..., description="Search queries performed")
    total_results_found: int = Field(..., ge=0, description="Total web results examined")
    relevant_results: List[Dict[str, Any]] = Field(..., description="Relevant findings")
    summary: str = Field(..., description="Human-readable summary")
    structured_data: Dict[str, Any] = Field(
        ..., description="Extracted structured data (e.g., size variants)"
    )
    confidence: float = Field(..., ge=0, le=1, description="Research confidence")
    sources: List[Dict[str, Any]] = Field(..., description="Source citations WITH URLs")


# ============================================================================
# Section 2.5: History Tracking Models (LLD Section 2.6)
# ============================================================================

class FoodScanRecord(BaseModel):
    """Single food scan record."""

    scan_id: str = Field(..., description="Unique scan UUID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    product_name: str = Field(...)
    brand: Optional[str] = None
    verdict: Literal["excellent", "good", "moderate", "caution", "avoid"]
    score: float = Field(..., ge=0, le=10)

    # Nutrition consumed (from this scan)
    calories: float = Field(..., ge=0)
    protein_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)
    fat_g: float = Field(..., ge=0)
    fiber_g: float = Field(..., ge=0)
    sugar_g: float = Field(..., ge=0)
    sodium_mg: float = Field(..., ge=0)


class DailySummary(BaseModel):
    """Daily consumption summary."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    scans: List[FoodScanRecord] = Field(default_factory=list)
    totals: Dict[str, float] = Field(
        default_factory=dict, description="Total nutrients consumed today"
    )
    vs_targets: Dict[str, float] = Field(
        default_factory=dict, description="Percentage of daily targets (0-1+)"
    )


class WeeklySummary(BaseModel):
    """Weekly consumption summary."""

    week_start: str = Field(..., description="Monday date (YYYY-MM-DD)")
    week_end: str = Field(..., description="Sunday date (YYYY-MM-DD)")
    daily_summaries: List[DailySummary] = Field(default_factory=list)
    weekly_totals: Dict[str, float] = Field(default_factory=dict)
    weekly_averages: Dict[str, float] = Field(default_factory=dict)


# ============================================================================
# Section 2.6: Scoring and Assessment Models (LLD Section 2.7)
# ============================================================================

class CitationSource(BaseModel):
    """Individual source citation (Perplexity-style)."""

    citation_number: int = Field(..., ge=1, description="Citation number [1], [2], etc.")
    source_type: Literal["openfoodfacts", "searxng_web", "health_guideline", "user_profile"]
    title: str = Field(...)
    url: Optional[str] = Field(None, description="Source URL (for web sources)")
    authority_score: float = Field(..., ge=0, le=1, description="Trustworthiness (WHO=1.0)")
    snippet: Optional[str] = Field(None, description="Relevant excerpt")
    accessed_at: datetime = Field(default_factory=datetime.utcnow)


class DetailedAssessment(BaseModel):
    """Complete assessment with full reasoning and citations."""

    # Core verdict
    scan_id: str = Field(..., description="Scan UUID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    product_name: str = Field(...)
    brand: Optional[str] = None

    # Scoring
    final_score: float = Field(..., ge=0, le=10, description="Final score (0-10)")
    verdict: Literal["excellent", "good", "moderate", "caution", "avoid"]
    verdict_emoji: str = Field(..., description="🟢 🟡 🔴")

    # Reasoning
    base_score: float = Field(..., ge=0, le=10, description="Intrinsic quality score")
    context_adjustment: str = Field(..., description="Human-readable explanation")
    time_multiplier: float = Field(..., ge=0.5, le=1.5, description="Time-based adjustment")
    final_calculation: str = Field(..., description="e.g., '6.0 × 1.2 × 0.8 = 5.76'")

    # Detailed insights
    highlights: List[str] = Field(default_factory=list, description="Positive points")
    warnings: List[str] = Field(default_factory=list, description="Concerns")
    allergen_alerts: List[str] = Field(default_factory=list, description="CRITICAL alerts")

    # Context-aware messaging
    moderation_message: str = Field(..., description="Daily consumption context")
    timing_recommendation: str = Field(..., description="When to consume this")

    # AI reasoning
    reasoning_steps: List[str] = Field(..., description="Step-by-step reasoning")
    confidence: float = Field(..., ge=0, le=1, description="Assessment confidence")

    # Citations (Perplexity-style)
    sources: List[CitationSource] = Field(default_factory=list)
    inline_citations: Dict[str, int] = Field(
        default_factory=dict, description="text_snippet → citation_number"
    )

    # Recommendations
    alternative_products: List[str] = Field(default_factory=list, description="Healthier options")
    portion_suggestion: Optional[str] = Field(None, description="Serving size advice")

    # Nutrition summary
    nutrition_snapshot: Dict[str, Any] = Field(
        default_factory=dict, description="Key metrics for display"
    )


class ShortAssessment(BaseModel):
    """Condensed assessment for quick consumption."""

    scan_id: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    product_name: str = Field(...)

    # Core verdict
    final_score: float = Field(..., ge=0, le=10)
    verdict: Literal["excellent", "good", "moderate", "caution", "avoid"]
    verdict_emoji: str = Field(...)

    # One-sentence summary
    summary: str = Field(..., max_length=150, description="Brief summary")

    # Top 3 insights
    key_points: List[str] = Field(..., max_length=3, description="Most important points")

    # Critical alerts only
    allergen_alerts: List[str] = Field(default_factory=list)

    # Single recommendation
    main_recommendation: Optional[str] = Field(None, description="Primary advice")


# ============================================================================
# Section 2.7: Onboarding Models (LLD Section 2.8)
# ============================================================================

class OnboardingQuestion(BaseModel):
    """Single question in conversational onboarding."""

    question_number: int = Field(..., ge=1, description="Sequential question number")
    total_questions: int = Field(..., ge=1, description="Approximate total")
    category: str = Field(..., description="Question category (e.g., 'demographics_age')")
    question: str = Field(..., description="The actual question text")
    response_type: Literal["text", "choice", "number"] = Field(..., description="Expected response type")
    choices: Optional[List[str]] = Field(None, description="For 'choice' type")
    validation: Dict[str, Any] = Field(
        default_factory=dict, description="Validation rules (min_chars, max_chars, etc.)"
    )
    can_skip: bool = Field(default=True, description="Whether user can skip")
    progress: float = Field(..., ge=0, le=1, description="Progress (0-1)")


class OnboardingResponse(BaseModel):
    """User response to onboarding question."""

    question_number: int = Field(...)
    response: str = Field(..., description="User's free-form response")


# ============================================================================
# Section 2.8: WebSocket Event Models (LLD Section 10.2)
# ============================================================================

class ScanProgressEvent(BaseModel):
    """Progress update during scan processing."""

    scan_id: str = Field(...)
    stage: Literal[
        "image_processing",
        "nutrition_retrieval",
        "profile_loading",
        "scoring",
        "assessment_generation"
    ] = Field(..., description="Current processing stage")
    stage_number: int = Field(..., ge=1, le=5, description="Stage number (1-5)")
    total_stages: int = Field(default=5, description="Total stages")
    message: str = Field(..., description="Human-readable status message")
    progress: float = Field(..., ge=0, le=1, description="Overall progress (0-1)")


class ScanErrorEvent(BaseModel):
    """Error during scan processing."""

    scan_id: str = Field(...)
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    stage: str = Field(..., description="Stage where error occurred")
    retry_suggestions: List[str] = Field(default_factory=list, description="How to fix")
    recoverable: bool = Field(..., description="Whether user can retry")


# ============================================================================
# Section 2.9: API Request/Response Models (LLD Section 10.1)
# ============================================================================

class LoginRequest(BaseModel):
    """Login request payload."""

    name: str = Field(..., min_length=1, max_length=100)


class LoginResponse(BaseModel):
    """Login response."""

    status: Literal["success", "new_user"]
    user_exists: bool
    profile: Optional[EnhancedUserProfile] = None
    message: Optional[str] = None
    redirect_to: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    """Partial profile update request."""

    # Allow partial updates - all fields optional
    demographics: Optional[Demographics] = None
    lifestyle_habits: Optional[LifestyleHabits] = None
    goals: Optional[HealthGoals] = None
    food_preferences: Optional[FoodPreferences] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: Literal["ok", "degraded"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, Dict[str, Any]] = Field(..., description="Service statuses")


class ScanRequest(BaseModel):
    """Scan initiation request via WebSocket."""

    user_name: str = Field(...)
    image_base64: str = Field(..., description="Base64-encoded image")
    source: Literal["camera", "upload"] = Field(...)


class OnboardingRequest(BaseModel):
    """Onboarding request for creating new user profile."""

    name: str = Field(..., min_length=1, max_length=100)
    demographics: Demographics
    lifestyle_habits: LifestyleHabits
    goals: HealthGoals
    food_preferences: FoodPreferences


class OnboardingResponse(BaseModel):
    """Onboarding response after profile creation."""

    profile: EnhancedUserProfile
    daily_targets: DailyTargets


class ProfileResponse(BaseModel):
    """Profile retrieval response."""

    profile: EnhancedUserProfile


class ProfileUpdateResponse(BaseModel):
    """Profile update response."""

    profile: EnhancedUserProfile
    updated_fields: List[str]


# ============================================================================
# Validators
# ============================================================================

# Apply validator to models that have allergen_alerts
DetailedAssessment.model_rebuild()
ShortAssessment.model_rebuild()


# ============================================================================
# Export all models
# ============================================================================

__all__ = [
    # Profile models (Section 2.2)
    "Demographics",
    "LifestyleHabits",
    "HealthMetrics",
    "HealthGoals",
    "FoodPreferences",
    "DailyTargets",
    "EnhancedUserProfile",
    # Nutrition models (Section 2.3)
    "NutritionData",
    "StructuredNutritionExtraction",
    "RawOCRExtraction",
    # Search models (Section 2.5)
    "InternAgentReport",
    # History models (Section 2.6)
    "FoodScanRecord",
    "DailySummary",
    "WeeklySummary",
    # Assessment models (Section 2.7)
    "CitationSource",
    "DetailedAssessment",
    "ShortAssessment",
    # Onboarding models (Section 2.8)
    "OnboardingQuestion",
    "OnboardingResponse",
    # Event models (Section 10.2)
    "ScanProgressEvent",
    "ScanErrorEvent",
    # API models (Section 10.1)
    "LoginRequest",
    "LoginResponse",
    "ProfileUpdateRequest",
    "HealthCheckResponse",
    "ScanRequest",
    "OnboardingRequest",
    "ProfileResponse",
    "ProfileUpdateResponse",
]
