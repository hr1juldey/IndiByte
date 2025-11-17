from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum
import numpy as np


class QualityTier(str, Enum):
    """Quality tiers for image analysis."""
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class QualityAnalysis(BaseModel):
    """Image quality analysis results."""
    quality_tier: str  # "good", "fair", "poor"
    sharpness: float
    exposure_score: float
    saturation_mean: float
    dark_ratio: float
    clipped_ratio: float


class ProcessingResult:
    """Result from adaptive image processing - using regular class for numpy array support."""
    def __init__(
        self,
        enhanced_image: Optional[np.ndarray],
        quality_analysis: QualityAnalysis,
        stages_applied: List[str],
        timings: Dict[str, float]
    ):
        self.enhanced_image = enhanced_image
        self.quality_analysis = quality_analysis
        self.stages_applied = stages_applied
        self.timings = timings