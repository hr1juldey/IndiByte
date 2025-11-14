"""Pydantic data models for Bytelense."""

from datetime import datetime
from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Core Domain Models
# ============================================================================

class DailyTargets(BaseModel):
    """Daily nutritional targets based on user goals."""
    calories: int
    sugar_g: float
    sodium_mg: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float


class UserProfile(BaseModel):
    """User health profile stored in JSON file."""
    name: str
    created_at: datetime
    updated_at: datetime
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goals: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    nutritional_focus: List[str] = Field(default_factory=list)
    daily_targets: DailyTargets


class ImageProcessingRequest(BaseModel):
    """Request to process an image."""
    source: Literal["camera", "upload"]
    image_bytes: bytes
    format: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ImageProcessingResult(BaseModel):
    """Result of image processing."""
    barcode: Optional[str] = None
    ocr_text: Optional[str] = None
    confidence: float
    method_used: Literal["barcode", "ocr"]
    processing_time_ms: int


class NutritionData(BaseModel):
    """Nutritional data from various sources."""
    product_name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    serving_size: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    saturated_fat_g: Optional[float] = None
    sugar_g: float
    sodium_mg: float
    fiber_g: Optional[float] = None
    ingredients: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)
    additives: List[str] = Field(default_factory=list)
    data_source: Literal["openfoodfacts", "searxng", "partial"]
    confidence: float
    retrieved_at: datetime = Field(default_factory=datetime.now)


class Citation(BaseModel):
    """Citation for data source (Perplexity-style)."""
    id: int
    url: str
    title: str
    snippet: str
    accessed: datetime
    source_type: Literal["openfoodfacts", "searxng", "who", "fda", "usda"]
    authority_score: float = Field(ge=0.0, le=1.0)


class ScoringResult(BaseModel):
    """Result of AI-powered nutrition scoring."""
    score: float = Field(ge=0.0, le=10.0)
    verdict: Literal["good", "moderate", "avoid"]
    reasoning: str
    warnings: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    data_quality_score: float = Field(ge=0.0, le=1.0)
    reasoning_steps: List[str] = Field(default_factory=list)
    factors_considered: List[str] = Field(default_factory=list)


class ComponentSpec(BaseModel):
    """Specification for a UI component."""
    type: str
    props: Dict[str, Any]
    order: int


class UISchema(BaseModel):
    """Schema for generative UI."""
    layout: Literal["alert", "balanced", "encouraging"]
    theme: Literal["red", "yellow", "green"]
    components: List[ComponentSpec]


class ScanResult(BaseModel):
    """Complete scan result."""
    scan_id: str
    user_name: str
    timestamp: datetime
    image_processing: ImageProcessingResult
    nutrition_data: NutritionData
    scoring: ScoringResult
    ui_schema: UISchema


# ============================================================================
# API Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request."""
    name: str


class LoginResponse(BaseModel):
    """Login response."""
    status: Literal["existing", "new"]
    profile: Optional[UserProfile] = None
    requires_onboarding: bool


class OnboardingRequest(BaseModel):
    """Onboarding request."""
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goals: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    nutritional_focus: List[str] = Field(default_factory=list)


class OnboardingResponse(BaseModel):
    """Onboarding response."""
    profile: UserProfile
    daily_targets: DailyTargets


class ProfileResponse(BaseModel):
    """Profile retrieval response."""
    profile: UserProfile


class ProfileUpdateRequest(BaseModel):
    """Profile update request (partial update)."""
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goals: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    dietary_preferences: Optional[List[str]] = None
    nutritional_focus: Optional[List[str]] = None


class ProfileUpdateResponse(BaseModel):
    """Profile update response."""
    profile: UserProfile
    updated_fields: List[str]


# ============================================================================
# WebSocket Event Payloads
# ============================================================================

class StartScanEvent(BaseModel):
    """Client → Server: start scan event."""
    user: str
    image_data: str  # base64 encoded
    source: Literal["camera", "upload"]
    format: Literal["jpeg", "png"]


class ScanProgressEvent(BaseModel):
    """Server → Client: progress update."""
    stage: str
    progress: int = Field(ge=0, le=100)
    message: str


class ScanCompleteEvent(BaseModel):
    """Server → Client: scan complete."""
    result: ScanResult


class ScanErrorEvent(BaseModel):
    """Server → Client: scan error."""
    stage: str
    error: str
    error_code: str
    retry_suggestion: Optional[str] = None
