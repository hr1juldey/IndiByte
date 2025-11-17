import logging
import time
from typing import Optional
import cv2
import numpy as np
from app.types.enums import DenoiseStrength

logger = logging.getLogger(__name__)

class LabelProcessor:
    """
    Improved label processor with better denoising and OCR capabilities
    """

    def __init__(self, enable_sr: bool = False):
        self.enable_sr = enable_sr
        self.logger = logging.getLogger(__name__)

    def analyze_quality(self, img: np.ndarray):
        """
        Analyze image quality for adaptive processing decisions.
        """
        from app.models.responses import QualityAnalysis, QualityTier

        # Calculate quality metrics
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Exposure quality
        mean_brightness = np.mean(gray)
        brightness_score = min(mean_brightness / 128.0, 1.0)  # normalized to 0-1

        # Saturation
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        saturation_mean = np.mean(hsv[:,:,1]) / 255.0  # normalized to 0-1

        # Dark pixel ratio
        dark_ratio = np.sum(gray < 30) / gray.size

        # Clipped (bright) ratio
        clipped_ratio = np.sum(gray > 225) / gray.size

        # Determine quality tier based on sharpness primarily
        if laplacian_var > 200:
            quality_tier = QualityTier.GOOD.value
        elif laplacian_var > 50:
            quality_tier = QualityTier.FAIR.value
        else:
            quality_tier = QualityTier.POOR.value

        return QualityAnalysis(
            quality_tier=quality_tier,
            sharpness=laplacian_var,
            exposure_score=brightness_score,
            saturation_mean=saturation_mean,
            dark_ratio=dark_ratio,
            clipped_ratio=clipped_ratio
        )

    def process_adaptive(self, img: np.ndarray):
        """
        Adaptive image processing pipeline based on quality analysis.
        """
        from app.models.responses import ProcessingResult, QualityAnalysis, QualityTier

        # Analyze image quality first
        quality_analysis = self.analyze_quality(img)

        # Apply processing based on quality tier
        current_img = img.copy()
        stages_applied = []
        timings = {}

        # Denoise if needed based on quality
        start_time = time.time()
        quality_value = quality_analysis.quality_tier
        if quality_value in [QualityTier.POOR.value, QualityTier.FAIR.value]:
            # Apply stronger denoising for lower quality images
            denoise_strength = DenoiseStrength.STRONG if quality_value == QualityTier.POOR.value else DenoiseStrength.MEDIUM
            current_img = self.denoise(current_img, denoise_strength)
            stages_applied.append("denoise")
        else:
            # Light denoising for good quality images
            current_img = self.denoise(current_img, DenoiseStrength.LIGHT)
            stages_applied.append("light_denoise")

        denoise_time = (time.time() - start_time) * 1000
        timings["denoise"] = denoise_time

        # Return processing result with the processed image
        return ProcessingResult(
            enhanced_image=current_img,
            quality_analysis=quality_analysis,
            stages_applied=stages_applied,
            timings=timings
        )

    def denoise(self, img: np.ndarray, strength: DenoiseStrength) -> np.ndarray:
        """
        Denoise image with configurable strength.

        Args:
            img: Input image (BGR)
            strength: Light, medium, or strong denoising

        Returns:
            Denoised image
        """
        if strength == DenoiseStrength.LIGHT:
            # Fast bilateral filter
            denoised = cv2.bilateralFilter(img, 9, 75, 75)
            logger.debug("Applied light bilateral denoising")

        elif strength == DenoiseStrength.MEDIUM:
            # Use positional arguments to avoid OpenCV version compatibility issues
            denoised = cv2.fastNlMeansDenoisingColored(
                img,
                None,  # dst
                10,    # h (filter strength)
                10,    # hForColorComponents
                7,     # templateWindowSize
                21     # searchWindowSize
            )
            logger.debug("Applied medium NLM denoising")

        else:  # STRONG
            # Double NLM denoising for maximum noise reduction
            temp = cv2.fastNlMeansDenoisingColored(
                img,
                None,  # dst
                15,    # h (filter strength)
                15,    # hForColorComponents
                7,     # templateWindowSize
                21     # searchWindowSize
            )
            denoised = cv2.fastNlMeansDenoisingColored(
                temp,
                None,  # dst
                10,    # h (filter strength)
                10,    # hForColorComponents
                7,     # templateWindowSize
                21     # searchWindowSize
            )
            logger.debug("Applied strong double NLM denoising")

        return denoised