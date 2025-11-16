"""
Unit and Integration Tests for Label Processing Service

Tests all stages of the adaptive image processing pipeline:
- Quality analysis
- Perspective correction
- Glare removal
- Denoising
- Contrast enhancement
- Full end-to-end processing
"""

import numpy as np
import cv2
from app.services.label_processing import (
    LabelProcessor,
    QualityTier,
    DenoiseStrength,
)

try:
    import pytest
except ImportError:
    # Fallback for environments without pytest
    pytest = None


class TestQualityAnalysis:
    """Test image quality assessment."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def create_synthetic_image(self, quality_tier: str) -> np.ndarray:
        """Create synthetic test images with different quality levels."""
        h, w = 480, 640

        if quality_tier == "good":
            # Sharp, well-exposed, colorful
            img = np.ones((h, w, 3), dtype=np.uint8) * 200  # Bright base
            # Add sharp text-like patterns (Laplacian variance will be high)
            for y in range(50, h - 50, 50):
                for x in range(50, w - 50, 50):
                    cv2.rectangle(img, (x, y), (x + 30, y + 30), (50, 100, 150), 2)
            # High saturation colors
            img[:, :w // 2] = (255, 200, 50)  # Yellow region
            img[:, w // 2:] = (50, 100, 200)  # Blue region
            return img

        elif quality_tier == "fair":
            # Moderate blur, some glare
            img = np.ones((h, w, 3), dtype=np.uint8) * 150
            # Add blurred text (Laplacian variance will be medium)
            for y in range(50, h - 50, 50):
                for x in range(50, w - 50, 50):
                    cv2.rectangle(img, (x, y), (x + 30, y + 30), (100, 100, 100), 1)
            # Apply blur
            img = cv2.GaussianBlur(img, (5, 5), 1.0)
            # Add some glare (overexposed region)
            cv2.rectangle(img, (0, 0), (100, 100), (255, 255, 255), -1)
            return img

        else:  # "poor"
            # Very blurry, dark, low saturation
            img = np.ones((h, w, 3), dtype=np.uint8) * 80  # Dark
            # Heavy blur
            img = cv2.GaussianBlur(img, (9, 9), 2.0)
            # Mostly grayscale (low saturation)
            img[:] = img.astype(np.float32).mean(axis=2, keepdims=True).astype(np.uint8)
            return img

    def test_quality_good(self, processor):
        """Test quality detection for good images."""
        img = self.create_synthetic_image("good")
        quality = processor.analyze_quality(img)

        assert quality.quality_tier == QualityTier.GOOD
        assert quality.sharpness > 100
        assert quality.exposure_score > 0.7

    def test_quality_fair(self, processor):
        """Test quality detection for fair images."""
        img = self.create_synthetic_image("fair")
        quality = processor.analyze_quality(img)

        assert quality.quality_tier == QualityTier.FAIR
        assert 50 < quality.sharpness < 100

    def test_quality_poor(self, processor):
        """Test quality detection for poor images."""
        img = self.create_synthetic_image("poor")
        quality = processor.analyze_quality(img)

        assert quality.quality_tier == QualityTier.POOR

    def test_exposure_metrics(self, processor):
        """Test exposure analysis."""
        # Dark image
        dark_img = np.ones((480, 640, 3), dtype=np.uint8) * 50
        quality_dark = processor.analyze_quality(dark_img)
        assert quality_dark.dark_ratio > 0.5

        # Overexposed image
        bright_img = np.ones((480, 640, 3), dtype=np.uint8) * 240
        quality_bright = processor.analyze_quality(bright_img)
        assert quality_bright.clipped_ratio > 0.5

    def test_saturation_metrics(self, processor):
        """Test saturation detection."""
        # Grayscale (low saturation)
        gray_img = np.ones((480, 640, 3), dtype=np.uint8) * 128
        quality_gray = processor.analyze_quality(gray_img)
        assert quality_gray.saturation_mean < 0.3

        # Colorful (high saturation)
        color_img = np.zeros((480, 640, 3), dtype=np.uint8)
        color_img[:, :, 2] = 255  # Red channel
        quality_color = processor.analyze_quality(color_img)
        assert quality_color.saturation_mean > 0.4


class TestPerspectiveCorrection:
    """Test perspective correction."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def test_perspective_correction_with_clear_rectangle(self, processor):
        """Test perspective correction on clear rectangular region."""
        img = np.ones((480, 640, 3), dtype=np.uint8) * 200

        # Draw clear rectangle (label)
        pts = np.array([[100, 100], [500, 80], [520, 400], [90, 420]], dtype=np.int32)
        cv2.polylines(img, [pts], True, (0, 0, 0), 3)
        cv2.fillPoly(img, [pts], (220, 200, 100))  # Fill with yellow

        warped, homography = processor.correct_perspective(img)

        # Should return something (either corrected or fallback)
        assert warped is not None
        assert warped.shape == img.shape

    def test_perspective_correction_fallback_on_blank(self, processor):
        """Test fallback when no contours found."""
        # Blank image
        img = np.ones((480, 640, 3), dtype=np.uint8) * 200

        warped, homography = processor.correct_perspective(img)

        # Should return original image as fallback
        assert warped is not None
        assert homography is None  # Fallback case
        assert np.array_equal(warped, img)


class TestGlareRemoval:
    """Test glare/highlight removal."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def test_glare_detection_and_removal(self, processor):
        """Test glare detection and inpainting."""
        # Create image with bright glare spot
        img = np.ones((480, 640, 3), dtype=np.uint8) * 150
        # Add red text region (for reference)
        img[100:400, 200:600] = (100, 50, 200)  # Reddish text on darker bg
        # Add bright glare spot
        cv2.circle(img, (150, 150), 50, (255, 255, 255), -1)

        inpainted = processor.remove_glare(img)

        # Result should be inpainted
        assert inpainted is not None
        assert inpainted.shape == img.shape
        # Glare region should be less bright
        assert np.mean(inpainted[100:200, 100:200]) < np.mean(img[100:200, 100:200])


class TestDenoising:
    """Test denoising at different strengths."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def test_denoise_light(self, processor):
        """Test light denoising."""
        # Create noisy image
        img = np.ones((480, 640, 3), dtype=np.uint8) * 150
        noise = np.random.normal(0, 20, img.shape)
        noisy_img = np.clip(img + noise, 0, 255).astype(np.uint8)

        denoised = processor.denoise(noisy_img, DenoiseStrength.LIGHT)

        assert denoised is not None
        # Denoised should have lower variance (less noise)
        assert np.std(denoised) < np.std(noisy_img)

    def test_denoise_medium(self, processor):
        """Test medium denoising."""
        img = np.ones((480, 640, 3), dtype=np.uint8) * 150
        noise = np.random.normal(0, 30, img.shape)
        noisy_img = np.clip(img + noise, 0, 255).astype(np.uint8)

        denoised = processor.denoise(noisy_img, DenoiseStrength.MEDIUM)

        assert denoised is not None
        assert np.std(denoised) < np.std(noisy_img)

    def test_denoise_strong(self, processor):
        """Test strong denoising."""
        img = np.ones((480, 640, 3), dtype=np.uint8) * 150
        noise = np.random.normal(0, 40, img.shape)
        noisy_img = np.clip(img + noise, 0, 255).astype(np.uint8)

        denoised = processor.denoise(noisy_img, DenoiseStrength.STRONG)

        assert denoised is not None
        # Strong denoise should reduce noise more
        assert np.std(denoised) < np.std(noisy_img)


class TestColorDetection:
    """Test label color detection."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def test_detect_yellow_label(self, processor):
        """Test detection of yellow label."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Yellow center region
        img[120:360, 160:480] = (0, 255, 255)  # BGR yellow

        color = processor.detect_label_color(img)
        assert color == "yellow"

    def test_detect_white_label(self, processor):
        """Test detection of white label."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # White center region
        img[120:360, 160:480] = (255, 255, 255)

        color = processor.detect_label_color(img)
        assert color == "grayscale"  # White has low saturation

    def test_detect_blue_label(self, processor):
        """Test detection of blue label."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Blue center region
        img[120:360, 160:480] = (255, 0, 0)  # BGR blue

        color = processor.detect_label_color(img)
        assert color == "blue"


class TestContrastEnhancement:
    """Test adaptive contrast enhancement."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def test_enhance_contrast_adaptive(self, processor):
        """Test adaptive contrast enhancement."""
        # Create low-contrast image
        img = np.ones((480, 640, 3), dtype=np.uint8) * 100
        img[100:200, 100:200] = 110  # Slight variation

        enhanced = processor.enhance_contrast_adaptive(img)

        assert enhanced is not None
        # Enhanced should have more contrast
        assert np.std(enhanced) > np.std(img)


class TestSharpening:
    """Test image sharpening."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def test_sharpen_unsharp_mask(self, processor):
        """Test unsharp mask sharpening."""
        # Create image with blurred edge
        img = np.ones((480, 640, 3), dtype=np.uint8) * 150
        img[100:200, 100:200] = 200
        img = cv2.GaussianBlur(img, (5, 5), 1.0)

        sharpened = processor.sharpen_unsharp(img, strength=1.3)

        assert sharpened is not None
        assert sharpened.shape == img.shape
        assert sharpened.dtype == np.uint8  # Clipped to valid range


class TestAdaptiveProcessing:
    """Test full adaptive processing pipeline."""

    @pytest.fixture
    def processor(self):
        return LabelProcessor(enable_sr=False)

    def create_test_image(self, quality_tier: str) -> np.ndarray:
        """Create realistic test images."""
        h, w = 480, 640

        if quality_tier == "good":
            # Yellow food label with red text
            img = np.ones((h, w, 3), dtype=np.uint8)
            img[:, :] = (0, 200, 255)  # Yellow background

            # Add text-like patterns
            for y in range(50, h, 60):
                cv2.line(img, (50, y), (w - 50, y), (50, 50, 150), 2)  # Red lines

            # Well-exposed
            img = np.clip(img.astype(np.float32) * 0.9, 0, 255).astype(np.uint8)
            return img

        elif quality_tier == "fair":
            # Similar but with some blur
            img = np.ones((h, w, 3), dtype=np.uint8) * 180
            img = cv2.GaussianBlur(img, (3, 3), 0.5)
            # Add glare
            cv2.ellipse(img, (100, 100), (40, 40), 0, 0, 360, (255, 255, 255), -1)
            return img

        else:  # "poor"
            # Dark, blurry, low contrast
            img = np.ones((h, w, 3), dtype=np.uint8) * 80
            img = cv2.GaussianBlur(img, (9, 9), 2.0)
            return img

    def test_process_good_quality_image(self, processor):
        """Test processing good quality image."""
        img = self.create_test_image("good")
        result = processor.process_adaptive(img)

        assert result.quality_analysis.quality_tier == QualityTier.GOOD
        assert result.enhanced_image is not None
        assert len(result.stages_applied) >= 2
        assert all(timing > 0 for timing in result.timings.values())

    def test_process_fair_quality_image(self, processor):
        """Test processing fair quality image."""
        img = self.create_test_image("fair")
        result = processor.process_adaptive(img)

        assert result.quality_analysis.quality_tier == QualityTier.FAIR
        assert result.enhanced_image is not None
        assert len(result.stages_applied) >= 3

    def test_process_poor_quality_image(self, processor):
        """Test processing poor quality image."""
        img = self.create_test_image("poor")
        result = processor.process_adaptive(img)

        assert result.quality_analysis.quality_tier == QualityTier.POOR
        assert result.enhanced_image is not None
        assert len(result.stages_applied) >= 4

    def test_processing_timings(self, processor):
        """Test that all stages complete with reasonable timings."""
        img = self.create_test_image("fair")
        result = processor.process_adaptive(img)

        # All timings should be positive
        assert result.timings["quality_analysis"] > 0
        assert sum(result.timings.values()) > 0

        # Processing shouldn't be unreasonably slow
        # (These are loose bounds for CI environments)
        assert result.timings["quality_analysis"] < 1000  # 1 second
        total_time = sum(result.timings.values())
        assert total_time < 5000  # 5 seconds total

    def test_output_image_validity(self, processor):
        """Test that output images are valid."""
        img = self.create_test_image("good")
        result = processor.process_adaptive(img)

        enhanced = result.enhanced_image
        assert enhanced is not None
        assert enhanced.shape[2] == 3  # BGR
        assert enhanced.dtype == np.uint8
        assert np.all((enhanced >= 0) & (enhanced <= 255))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
