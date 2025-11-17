from enum import Enum


class DenoiseStrength(Enum):
    """Strength levels for image denoising."""
    
    LIGHT = "light"
    MEDIUM = "medium"
    STRONG = "strong"