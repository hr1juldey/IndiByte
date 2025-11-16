"""
Comprehensive Label Image Processing Service

Implements the two-stage adaptive pipeline for OCR-ready image enhancement:
- Stage 1 (Frontend): Burst fusion, light preprocessing
- Stage 2 (Backend): Adaptive heavy processing based on image quality

This service handles:
- Quality analysis (sharpness, exposure, saturation)
- Adaptive processing path selection (light/medium/heavy)
- Perspective correction with edge detection
- Glare/specular highlight removal
- Multi-strength denoising
- Color-aware contrast enhancement (CLAHE)
- Optional super-resolution for poor images
"""

import logging
import cv2
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

logger = logging.getLogger(__name__)


class QualityTier(str, Enum):
    """Image quality assessment tiers."""
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class DenoiseStrength(str, Enum):
    """Denoising intensity levels."""
    LIGHT = "light"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass
class ImageQuality:
    """Image quality metrics."""
    sharpness: float  # Laplacian variance
    exposure_score: float  # 0-1, higher is better
    dark_ratio: float  # Ratio of dark pixels
    clipped_ratio: float  # Ratio of clipped pixels
    saturation_mean: float  # 0-1, color vibrancy
    quality_tier: QualityTier


@dataclass
class ProcessingResult:
    """Result of label processing."""
    enhanced_image: np.ndarray
    original_size: Tuple[int, int]
    processed_size: Tuple[int, int]
    quality_analysis: ImageQuality
    stages_applied: List[str]
    timings: Dict[str, float]  # Stage name -> milliseconds


class LabelProcessor:
    """
    Comprehensive label image processing service.

    Handles both frontend and backend processing stages with adaptive
    quality-based pipeline selection.
    """

    def __init__(self, enable_sr: bool = False):
        """
        Initialize label processor.

        Args:
            enable_sr: Whether to use super-resolution (requires model)
        """
        self.enable_sr = enable_sr
        self.sr_model = None
        if enable_sr:
            self._load_sr_model()

    def _load_sr_model(self):
        """Load super-resolution model (SwinIR or ESRGAN lightweight)."""
        try:
            # Placeholder - real implementation would load TensorFlow/PyTorch model
            logger.info("Super-resolution model loading not implemented in this version")
            self.enable_sr = False
        except Exception as e:
            logger.warning(f"Failed to load SR model: {e}, disabling SR")
            self.enable_sr = False

    # ==================== Quality Analysis ====================

    def analyze_quality(self, img: np.ndarray) -> ImageQuality:
        """
        Comprehensive image quality analysis.

        Analyzes sharpness, exposure, saturation to determine processing tier.

        Args:
            img: Input image (BGR)

        Returns:
            ImageQuality dataclass with metrics
        """

        # 1. Sharpness (Laplacian variance)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = np.var(laplacian)

        # 2. Exposure analysis
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
        L = lab[:, :, 0]
        dark_ratio = np.sum(L < 50) / L.size
        clipped_ratio = np.sum(L > 240) / L.size
        exposure_score = 1.0 - (dark_ratio + clipped_ratio)

        # 3. Saturation (color vibrancy)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:, :, 1]
        saturation_mean = np.mean(s_channel) / 255.0

        # 4. Determine quality tier
        if sharpness > 100 and exposure_score > 0.7 and saturation_mean > 0.3:
            quality_tier = QualityTier.GOOD
        elif sharpness > 60 and exposure_score > 0.5:
            quality_tier = QualityTier.FAIR
        else:
            quality_tier = QualityTier.POOR

        return ImageQuality(
            sharpness=sharpness,
            exposure_score=exposure_score,
            dark_ratio=dark_ratio,
            clipped_ratio=clipped_ratio,
            saturation_mean=saturation_mean,
            quality_tier=quality_tier
        )

    # ==================== Perspective Correction ====================

    def correct_perspective(self, img: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Detect label region and correct perspective.

        Uses edge detection + contour approximation to find label corners
        and applies homography warp for frontal alignment.

        Args:
            img: Input image (BGR)

        Returns:
            (warped_image, homography_matrix) or (original_image, None) if detection fails
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            logger.warning("No contours found for perspective correction")
            return img, None

        # Find largest contour (likely label)
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        # Sanity check: contour should be reasonable size
        img_area = img.shape[0] * img.shape[1]
        if area < img_area * 0.05:  # Less than 5% of image
            logger.warning(f"Largest contour too small ({area} < {img_area * 0.05})")
            return img, None

        # Approximate as quadrilateral
        epsilon = 0.02 * cv2.arcLength(largest, True)
        quad = cv2.approxPolyDP(largest, epsilon, True)

        if len(quad) != 4:
            logger.debug(f"Contour has {len(quad)} points, expected 4")
            return img, None

        # Extract corners in consistent order
        pts_src = self._order_points(quad.reshape(4, 2).astype(np.float32))

        # Define destination (frontal rectangle)
        h, w = gray.shape
        pts_dst = np.array(
            [[0, 0], [w, 0], [w, h], [0, h]],
            dtype=np.float32
        )

        # Compute and apply homography
        try:
            M = cv2.getPerspectiveTransform(pts_src, pts_dst)
            warped = cv2.warpPerspective(
                img, M, (w, h),
                borderMode=cv2.BORDER_REPLICATE,
                flags=cv2.INTER_CUBIC
            )
            logger.debug("Perspective correction successful")
            return warped, M
        except Exception as e:
            logger.warning(f"Homography failed: {e}")
            return img, None

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        """
        Order quadrilateral points consistently (TL, TR, BR, BL).

        Args:
            pts: Unordered 4 points (Nx2)

        Returns:
            Ordered points (4x2)
        """
        # Sort by x + y (top-left), then separate top/bottom by y
        sum_vals = pts.sum(axis=1)
        tl = pts[sum_vals.argmin()]
        br = pts[sum_vals.argmax()]

        diff_vals = np.diff(pts, axis=1)
        tr = pts[diff_vals.argmin()]
        bl = pts[diff_vals.argmax()]

        return np.array([tl, tr, br, bl], dtype=np.float32)

    # ==================== Glare Removal ====================

    def remove_glare(self, img: np.ndarray) -> np.ndarray:
        """
        Detect and remove specular highlights (glare).

        Analyzes L channel in LAB color space, detects bright pixels,
        and inpaints to reduce glare impact.

        Args:
            img: Input image (BGR)

        Returns:
            Inpainted image with reduced glare
        """
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
        L = lab[:, :, 0]

        # Adaptive threshold based on overall brightness
        mean_L = np.mean(L)
        glare_threshold = 220 if mean_L < 100 else 240

        # Create glare mask
        glare_mask = (L > glare_threshold).astype(np.uint8) * 255

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        glare_mask = cv2.morphologyEx(glare_mask, cv2.MORPH_CLOSE, kernel)
        glare_mask = cv2.morphologyEx(glare_mask, cv2.MORPH_OPEN, kernel)

        # Inpaint bright regions
        try:
            inpainted = cv2.inpaint(img, glare_mask, 5, cv2.INPAINT_TELEA)
            logger.debug(f"Glare inpainting applied (threshold={glare_threshold})")
            return inpainted
        except Exception as e:
            logger.warning(f"Inpainting failed: {e}")
            return img

    # ==================== Denoising ====================

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
            # fastNlMeansDenoisingColored
            denoised = cv2.fastNlMeansDenoisingColored(
                img,
                h=10,
                hForColorComponents=10,
                templateWindowSize=7,
                searchWindowSize=21
            )
            logger.debug("Applied medium NLM denoising")

        else:  # STRONG
            # Double NLM denoising
            temp = cv2.fastNlMeansDenoisingColored(
                img,
                h=15,
                hForColorComponents=15,
                templateWindowSize=7,
                searchWindowSize=21
            )
            denoised = cv2.fastNlMeansDenoisingColored(
                temp,
                h=10,
                hForColorComponents=10,
                templateWindowSize=7,
                searchWindowSize=21
            )
            logger.debug("Applied strong double NLM denoising")

        return denoised

    # ==================== Contrast Enhancement ====================

    def detect_label_color(self, img: np.ndarray) -> str:
        """
        Detect dominant label color for adaptive processing.

        Analyzes center region of image to determine color category.

        Args:
            img: Input image (BGR)

        Returns:
            Color category: 'yellow', 'white', 'blue', 'red', 'green', 'grayscale', 'other'
        """
        h, w = img.shape[:2]

        # Sample center region
        center = img[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]

        # Convert to HSV
        hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
        h_chan, s_chan, _ = cv2.split(hsv)

        # Compute means
        mean_hue = np.mean(h_chan)
        mean_sat = np.mean(s_chan)

        # Classify by hue
        if mean_sat < 30:
            return "grayscale"
        elif 15 < mean_hue < 25:
            return "yellow"
        elif 25 < mean_hue < 40:
            return "orange"
        elif 150 < mean_hue < 180:
            return "blue"
        elif mean_hue < 15 or mean_hue > 165:
            return "red"
        elif 40 < mean_hue < 80:
            return "green"
        else:
            return "other"

    def enhance_contrast_adaptive(self, img: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        with color-aware tuning.

        Different colors get different clip limits for optimal contrast.

        Args:
            img: Input image (BGR)

        Returns:
            Enhanced image
        """
        # Detect label color
        color = self.detect_label_color(img)

        # Color-specific CLAHE parameters
        color_config = {
            "yellow": {"clip_limit": 2.5, "tile_size": 8},
            "white": {"clip_limit": 2.0, "tile_size": 8},
            "blue": {"clip_limit": 2.5, "tile_size": 8},
            "red": {"clip_limit": 2.3, "tile_size": 8},
            "green": {"clip_limit": 2.2, "tile_size": 8},
            "grayscale": {"clip_limit": 2.0, "tile_size": 8},
            "orange": {"clip_limit": 2.4, "tile_size": 8},
            "other": {"clip_limit": 2.0, "tile_size": 8},
        }

        config = color_config.get(color, color_config["grayscale"])

        # Convert to LAB, enhance L channel
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
        L, a, b = cv2.split(lab)

        # Apply CLAHE
        clahe = cv2.createCLAHE(
            clipLimit=config["clip_limit"],
            tileGridSize=(config["tile_size"], config["tile_size"])
        )
        L_enhanced = clahe.apply(L)

        # Merge back and convert to BGR
        lab_enhanced = cv2.merge([L_enhanced, a, b])
        result = cv2.cvtColor(lab_enhanced, cv2.COLOR_Lab2BGR)

        logger.debug(f"Applied color-aware CLAHE (color={color}, clip_limit={config['clip_limit']})")
        return result

    # ==================== Sharpening ====================

    def sharpen_unsharp(self, img: np.ndarray, strength: float = 1.3) -> np.ndarray:
        """
        Apply unsharp mask for edge enhancement.

        Args:
            img: Input image (BGR)
            strength: Sharpening strength (1.0 = no sharpening, >1.0 = more)

        Returns:
            Sharpened image
        """
        gaussian = cv2.GaussianBlur(img, (5, 5), 1.0)
        sharpened = cv2.addWeighted(img, strength, gaussian, -(strength - 1.0), 0)

        # Clip to valid range
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

        logger.debug(f"Applied unsharp mask (strength={strength})")
        return sharpened

    # ==================== Super-Resolution (Optional) ====================

    def super_resolve(self, img: np.ndarray, scale: int = 2) -> np.ndarray:
        """
        Optional super-resolution upsampling.

        If SR model not available, falls back to bicubic interpolation.

        Args:
            img: Input image (BGR)
            scale: Upsampling factor (2x or 4x)

        Returns:
            Upsampled image
        """
        if self.enable_sr and self.sr_model is not None:
            try:
                result = self.sr_model.infer(img, scale=scale)
                logger.debug(f"Applied ML-based super-resolution ({scale}x)")
                return result
            except Exception as e:
                logger.warning(f"SR inference failed: {e}, falling back to bicubic")

        # Fallback: bicubic interpolation
        h, w = img.shape[:2]
        new_h, new_w = h * scale, w * scale
        result = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        logger.debug(f"Applied bicubic upsampling ({scale}x)")
        return result

    # ==================== Main Processing Pipelines ====================

    def process_adaptive(self, img: np.ndarray) -> ProcessingResult:
        """
        Adaptive processing based on quality analysis.

        Selects light, medium, or heavy processing tier based on image quality.

        Args:
            img: Input image (BGR)

        Returns:
            ProcessingResult with enhanced image and metadata
        """
        import time

        original_size = img.shape[:2]
        stages = []
        timings = {}

        # 1. Quality analysis
        start = time.time()
        quality = self.analyze_quality(img)
        timings["quality_analysis"] = (time.time() - start) * 1000
        logger.info(f"Quality tier: {quality.quality_tier.value} (sharpness={quality.sharpness:.1f})")

        # Select processing path
        if quality.quality_tier == QualityTier.GOOD:
            # Light processing
            processing_stages = self._pipeline_light()
        elif quality.quality_tier == QualityTier.FAIR:
            # Medium processing
            processing_stages = self._pipeline_medium()
        else:
            # Heavy processing
            processing_stages = self._pipeline_heavy()

        # Execute stages
        current_img = img
        for stage_name, stage_func in processing_stages:
            start = time.time()
            current_img = stage_func(current_img)
            elapsed = (time.time() - start) * 1000
            timings[stage_name] = elapsed
            stages.append(stage_name)
            logger.debug(f"Stage '{stage_name}' completed in {elapsed:.1f}ms")

        processed_size = current_img.shape[:2]

        return ProcessingResult(
            enhanced_image=current_img,
            original_size=original_size,
            processed_size=processed_size,
            quality_analysis=quality,
            stages_applied=stages,
            timings=timings
        )

    def _pipeline_light(self) -> List[Tuple[str, callable]]:
        """Light processing for good quality images."""
        return [
            ("enhance_contrast", lambda x: self.enhance_contrast_adaptive(x)),
            ("sharpen", lambda x: self.sharpen_unsharp(x, strength=1.2)),
        ]

    def _pipeline_medium(self) -> List[Tuple[str, callable]]:
        """Medium processing for fair quality images."""
        return [
            ("perspective_correction", lambda x: self.correct_perspective(x)[0]),
            ("glare_removal", lambda x: self.remove_glare(x)),
            ("denoise", lambda x: self.denoise(x, DenoiseStrength.MEDIUM)),
            ("enhance_contrast", lambda x: self.enhance_contrast_adaptive(x)),
            ("sharpen", lambda x: self.sharpen_unsharp(x, strength=1.3)),
        ]

    def _pipeline_heavy(self) -> List[Tuple[str, callable]]:
        """Heavy processing for poor quality images."""
        return [
            ("perspective_correction", lambda x: self.correct_perspective(x)[0]),
            ("glare_removal", lambda x: self.remove_glare(x)),
            ("denoise", lambda x: self.denoise(x, DenoiseStrength.STRONG)),
            ("enhance_contrast", lambda x: self.enhance_contrast_adaptive(x)),
            ("sharpen", lambda x: self.sharpen_unsharp(x, strength=1.4)),
            ("upsampling", lambda x: self.super_resolve(x, scale=2)),
        ]

    # ==================== Utility ====================

    def process_to_base64(self, img: np.ndarray, quality: int = 85) -> str:
        """
        Convert processed image to base64 JPEG.

        Args:
            img: Input image (BGR)
            quality: JPEG quality (1-100)

        Returns:
            Base64 encoded JPEG string with data URI prefix
        """
        import base64

        _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        b64 = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def process_to_bytes(self, img: np.ndarray, quality: int = 85) -> bytes:
        """
        Convert processed image to JPEG bytes.

        Args:
            img: Input image (BGR)
            quality: JPEG quality (1-100)

        Returns:
            JPEG bytes
        """
        _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buffer.tobytes()
