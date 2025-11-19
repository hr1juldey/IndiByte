"""
Tile-based Image Quality Assessment for OCR Preprocessing

This module provides functionality for dividing images into tiles and assessing
the quality of each tile based on blur, contrast, glare, and noise metrics.
The approach helps identify localized issues that might affect OCR performance
in specific regions of an image.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class QualityTier(Enum):
    """Quality tiers for tile analysis."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    BAD = "bad"


@dataclass
class TileQualityMetrics:
    """Quality metrics for a single tile."""
    tile_id: int
    x: int
    y: int
    width: int
    height: int
    sharpness: float
    contrast: float
    brightness: float
    glare_score: float
    noise_level: float
    saturation: float
    quality_tier: QualityTier
    ocr_suitability_score: float  # Combined score for OCR suitability (0-1)


@dataclass
class TileQualityAssessment:
    """Overall assessment of tile-based image quality."""
    overall_sharpness: float
    overall_contrast: float
    overall_brightness: float
    overall_glare_score: float
    overall_noise_level: float
    overall_saturation: float
    quality_tier: QualityTier
    tile_metrics: List[TileQualityMetrics]
    recommended_preprocessing: List[str]


class TileBasedQualityAssessment:
    """
    Implements tile-based image quality assessment for OCR preprocessing.
    """

    def __init__(self, tile_size: int = 64, overlap: int = 16):
        """
        Initialize the tile-based quality assessment.

        Args:
            tile_size: Size of each tile (square) in pixels
            overlap: Overlap between adjacent tiles in pixels
        """
        self.tile_size = tile_size
        self.overlap = overlap

    def divide_into_tiles(self, image: np.ndarray) -> List[Tuple[np.ndarray, int, int, int, int]]:
        """
        Divide the image into overlapping tiles.

        Args:
            image: Input image as numpy array (BGR)

        Returns:
            List of tuples containing (tile_image, x, y, width, height)
        """
        h, w = image.shape[:2]
        tiles = []

        # Calculate step size (tile_size - overlap to create overlap)
        step = self.tile_size - self.overlap

        # Generate tiles
        for y in range(0, h - self.tile_size + 1, step):
            for x in range(0, w - self.tile_size + 1, step):
                # Extract tile
                tile = image[y:y + self.tile_size, x:x + self.tile_size]
                tiles.append((tile, x, y, self.tile_size, self.tile_size))

        # Also add edge tiles if the image doesn't divide evenly
        # Right edge tiles
        if w % step != 0:
            for y in range(0, h - self.tile_size + 1, step):
                x = max(0, w - self.tile_size)
                tile = image[y:y + self.tile_size, x:x + self.tile_size]
                tiles.append((tile, x, y, self.tile_size, self.tile_size))

        # Bottom edge tiles
        if h % step != 0:
            for x in range(0, w - self.tile_size + 1, step):
                y = max(0, h - self.tile_size)
                tile = image[y:y + self.tile_size, x:x + self.tile_size]
                tiles.append((tile, x, y, self.tile_size, self.tile_size))

        # Bottom-right corner if needed
        if h % step != 0 and w % step != 0:
            x = max(0, w - self.tile_size)
            y = max(0, h - self.tile_size)
            tile = image[y:y + self.tile_size, x:x + self.tile_size]
            tiles.append((tile, x, y, self.tile_size, self.tile_size))

        return tiles

    def calculate_sharpness(self, tile: np.ndarray) -> float:
        """
        Calculate sharpness using the Laplacian variance method.

        Args:
            tile: Image tile as numpy array

        Returns:
            Sharpness score (higher is sharper)
        """
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normalize to 0-1 range (assuming max sharpness around 500)
        return min(laplacian_var / 500.0, 1.0)

    def calculate_contrast(self, tile: np.ndarray) -> float:
        """
        Calculate contrast using the standard deviation of pixel intensities.

        Args:
            tile: Image tile as numpy array

        Returns:
            Contrast score (higher is more contrast)
        """
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        # Normalize to 0-1 range (assuming max contrast around 128)
        return min(contrast / 128.0, 1.0)

    def calculate_brightness(self, tile: np.ndarray) -> float:
        """
        Calculate average brightness of the tile.

        Args:
            tile: Image tile as numpy array

        Returns:
            Brightness score (0-1, where 0 is dark, 1 is bright)
        """
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        return mean_brightness / 255.0

    def calculate_glare_score(self, tile: np.ndarray) -> float:
        """
        Calculate glare score based on bright pixels.

        Args:
            tile: Image tile as numpy array

        Returns:
            Glare score (higher means more glare)
        """
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        # Count pixels that are very bright (potential glare)
        bright_pixels = np.sum(gray > 220)
        total_pixels = gray.size
        glare_ratio = bright_pixels / total_pixels if total_pixels > 0 else 0.0

        # Invert so that lower glare scores are better
        return 1.0 - glare_ratio

    def calculate_noise_level(self, tile: np.ndarray) -> float:
        """
        Estimate noise level using Laplacian of Gaussian.

        Args:
            tile: Image tile as numpy array

        Returns:
            Noise level (lower is less noisy)
        """
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        # Apply LoG filter
        log_filtered = cv2.Laplacian(gray, cv2.CV_64F)
        noise_level = np.std(log_filtered)
        # Normalize and invert so higher scores are better (less noise)
        normalized_noise = min(noise_level / 50.0, 1.0)
        return 1.0 - normalized_noise

    def calculate_saturation(self, tile: np.ndarray) -> float:
        """
        Calculate average saturation in HSV color space.

        Args:
            tile: Image tile as numpy array

        Returns:
            Saturation score (higher is more saturated)
        """
        hsv = cv2.cvtColor(tile, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])
        return saturation / 255.0

    def determine_tile_quality_tier(self, metrics: TileQualityMetrics) -> QualityTier:
        """
        Determine the quality tier based on combined metrics.

        Args:
            metrics: Tile quality metrics

        Returns:
            Quality tier for the tile
        """
        # Weighted combination of metrics for OCR suitability
        # OCR benefits from sharpness, contrast, and moderate brightness
        score = (
            0.3 * metrics.sharpness +
            0.25 * metrics.contrast +
            0.15 * metrics.glare_score +  # Lower glare is better
            0.15 * metrics.noise_level +  # Lower noise is better
            0.1 * metrics.saturation +
            0.05 * (1.0 - abs(metrics.brightness - 0.5))  # Prefer moderate brightness
        )

        if score >= 0.8:
            return QualityTier.EXCELLENT
        elif score >= 0.6:
            return QualityTier.GOOD
        elif score >= 0.4:
            return QualityTier.FAIR
        elif score >= 0.2:
            return QualityTier.POOR
        else:
            return QualityTier.BAD

    def assess_tile_quality(self, tile: np.ndarray, x: int, y: int, width: int, height: int, tile_id: int) -> TileQualityMetrics:
        """
        Assess the quality of a single tile.

        Args:
            tile: Image tile as numpy array
            x, y: Position of the tile in the original image
            width, height: Dimensions of the tile
            tile_id: Unique ID for the tile

        Returns:
            TileQualityMetrics object with all quality metrics
        """
        # Calculate individual metrics
        sharpness = self.calculate_sharpness(tile)
        contrast = self.calculate_contrast(tile)
        brightness = self.calculate_brightness(tile)
        glare_score = self.calculate_glare_score(tile)
        noise_level = self.calculate_noise_level(tile)
        saturation = self.calculate_saturation(tile)

        # Calculate OCR suitability score
        ocr_suitability_score = (
            0.3 * sharpness +
            0.25 * contrast +
            0.15 * glare_score +
            0.15 * noise_level +
            0.1 * saturation +
            0.05 * (1.0 - abs(brightness - 0.5))
        )

        # Determine quality tier
        quality_tier = self.determine_tile_quality_tier(
            TileQualityMetrics(
                tile_id=tile_id, x=x, y=y, width=width, height=height,
                sharpness=sharpness, contrast=contrast, brightness=brightness,
                glare_score=glare_score, noise_level=noise_level, saturation=saturation,
                quality_tier=QualityTier.GOOD, ocr_suitability_score=ocr_suitability_score
            )
        )

        return TileQualityMetrics(
            tile_id=tile_id,
            x=x,
            y=y,
            width=width,
            height=height,
            sharpness=sharpness,
            contrast=contrast,
            brightness=brightness,
            glare_score=glare_score,
            noise_level=noise_level,
            saturation=saturation,
            quality_tier=quality_tier,
            ocr_suitability_score=ocr_suitability_score
        )

    def assess_image_quality(self, image: np.ndarray) -> TileQualityAssessment:
        """
        Assess the quality of the entire image using tile-based analysis.

        Args:
            image: Input image as numpy array (BGR)

        Returns:
            TileQualityAssessment object with overall assessment
        """
        # Divide image into tiles
        tiles = self.divide_into_tiles(image)

        # Assess each tile
        tile_metrics = []
        for idx, (tile, x, y, width, height) in enumerate(tiles):
            tile_metrics.append(self.assess_tile_quality(tile, x, y, width, height, idx))

        # Calculate overall metrics
        overall_sharpness = np.mean([tm.sharpness for tm in tile_metrics])
        overall_contrast = np.mean([tm.contrast for tm in tile_metrics])
        overall_brightness = np.mean([tm.brightness for tm in tile_metrics])
        overall_glare_score = np.mean([tm.glare_score for tm in tile_metrics])
        overall_noise_level = np.mean([tm.noise_level for tm in tile_metrics])
        overall_saturation = np.mean([tm.saturation for tm in tile_metrics])

        # Determine overall quality tier based on average metrics
        overall_score = (
            0.3 * overall_sharpness +
            0.25 * overall_contrast +
            0.15 * overall_glare_score +
            0.15 * overall_noise_level +
            0.1 * overall_saturation +
            0.05 * (1.0 - abs(overall_brightness - 0.5))
        )

        if overall_score >= 0.8:
            overall_tier = QualityTier.EXCELLENT
        elif overall_score >= 0.6:
            overall_tier = QualityTier.GOOD
        elif overall_score >= 0.4:
            overall_tier = QualityTier.FAIR
        elif overall_score >= 0.2:
            overall_tier = QualityTier.POOR
        else:
            overall_tier = QualityTier.BAD

        # Determine recommended preprocessing based on quality issues
        recommendations = self._determine_preprocessing_recommendations(tile_metrics)

        return TileQualityAssessment(
            overall_sharpness=overall_sharpness,
            overall_contrast=overall_contrast,
            overall_brightness=overall_brightness,
            overall_glare_score=overall_glare_score,
            overall_noise_level=overall_noise_level,
            overall_saturation=overall_saturation,
            quality_tier=overall_tier,
            tile_metrics=tile_metrics,
            recommended_preprocessing=recommendations
        )

    def _determine_preprocessing_recommendations(self, tile_metrics: List[TileQualityMetrics]) -> List[str]:
        """
        Determine preprocessing recommendations based on tile quality metrics.

        Args:
            tile_metrics: List of tile quality metrics

        Returns:
            List of recommended preprocessing steps
        """
        recommendations = []

        # Check if sharpness is generally low
        avg_sharpness = np.mean([tm.sharpness for tm in tile_metrics])
        if avg_sharpness < 0.3:
            recommendations.append("apply_sharpening_filter")

        # Check if contrast is generally low
        avg_contrast = np.mean([tm.contrast for tm in tile_metrics])
        if avg_contrast < 0.3:
            recommendations.append("apply_contrast_enhancement")

        # Check if brightness is too high (potential glare)
        avg_brightness = np.mean([tm.brightness for tm in tile_metrics])
        if avg_brightness > 0.8:
            recommendations.append("apply_brightness_reduction")

        # Check if there are specific glare issues
        avg_glare = np.mean([tm.glare_score for tm in tile_metrics])
        if avg_glare < 0.7:  # Inverted scale, so < 0.7 means high glare
            recommendations.append("apply_glare_reduction")

        # Check if noise is high
        avg_noise = np.mean([tm.noise_level for tm in tile_metrics])
        if avg_noise < 0.5:  # Inverted scale, so < 0.5 means high noise
            recommendations.append("apply_noise_reduction")

        # Check for low saturation
        avg_saturation = np.mean([tm.saturation for tm in tile_metrics])
        if avg_saturation < 0.3:
            recommendations.append("apply_saturation_enhancement")

        # If there are significant variations in quality across tiles,
        # recommend adaptive processing per region
        sharpness_std = np.std([tm.sharpness for tm in tile_metrics])
        if sharpness_std > 0.2:
            recommendations.append("apply_adaptive_processing_per_region")

        return recommendations

    def get_low_quality_regions(self, assessment: TileQualityAssessment, quality_threshold: QualityTier = QualityTier.FAIR) -> List[TileQualityMetrics]:
        """
        Get regions that have quality below the specified threshold.

        Args:
            assessment: Tile quality assessment
            quality_threshold: Minimum acceptable quality tier

        Returns:
            List of tiles with quality below the threshold
        """
        threshold_map = {
            QualityTier.EXCELLENT: 5,
            QualityTier.GOOD: 4,
            QualityTier.FAIR: 3,
            QualityTier.POOR: 2,
            QualityTier.BAD: 1
        }

        threshold_value = threshold_map[quality_threshold]

        low_quality_tiles = []
        for tile_metric in assessment.tile_metrics:
            tile_value = threshold_map[tile_metric.quality_tier]
            if tile_value < threshold_value:
                low_quality_tiles.append(tile_metric)

        return low_quality_tiles

    def visualize_tile_quality(self, image: np.ndarray, assessment: TileQualityAssessment, 
                              output_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        Create a visualization showing the quality of each tile overlaid on the original image.

        Args:
            image: Original image
            assessment: Tile quality assessment
            output_size: Optional output size for the visualization

        Returns:
            Visualization image with quality overlay
        """
        # Create a copy of the image for visualization
        vis_image = image.copy()

        # Color mapping for quality tiers
        color_map = {
            QualityTier.EXCELLENT: (0, 255, 0),    # Green
            QualityTier.GOOD: (64, 255, 64),       # Light green
            QualityTier.FAIR: (255, 255, 0),       # Yellow
            QualityTier.POOR: (255, 165, 0),       # Orange
            QualityTier.BAD: (255, 0, 0)           # Red
        }

        # Draw rectangles for each tile with color based on quality
        for tile_metric in assessment.tile_metrics:
            color = color_map[tile_metric.quality_tier]
            start_point = (tile_metric.x, tile_metric.y)
            end_point = (tile_metric.x + tile_metric.width, tile_metric.y + tile_metric.height)
            cv2.rectangle(vis_image, start_point, end_point, color, 2)

        # Resize if requested
        if output_size:
            vis_image = cv2.resize(vis_image, output_size)

        return vis_image


# Example usage and testing functions
def create_sample_quality_assessment():
    """
    Create a sample quality assessment with example code.
    This demonstrates how to use the tile-based quality assessment.
    """
    # Example usage code as documentation
    sample_code = """
    # Initialize the tile-based quality assessment
    quality_assessor = TileBasedQualityAssessment(tile_size=64, overlap=16)

    # Load an image (BGR format as expected by OpenCV)
    image = cv2.imread('path/to/your/image.jpg')

    # Assess the quality of the image
    assessment = quality_assessor.assess_image_quality(image)

    # Print overall quality metrics
    print(f"Overall Sharpness: {assessment.overall_sharpness:.3f}")
    print(f"Overall Contrast: {assessment.overall_contrast:.3f}")
    print(f"Overall Quality Tier: {assessment.quality_tier.value}")

    # Print quality metrics for each tile
    for tile_metric in assessment.tile_metrics:
        print(f"Tile {tile_metric.tile_id}: "
              f"Sharpness={tile_metric.sharpness:.3f}, "
              f"Contrast={tile_metric.contrast:.3f}, "
              f"Quality={tile_metric.quality_tier.value}")

    # Get recommendations for preprocessing
    print(f"Recommended preprocessing steps: {assessment.recommended_preprocessing}")

    # Get low quality regions
    low_quality_regions = quality_assessor.get_low_quality_regions(assessment, QualityTier.FAIR)
    print(f"Number of low quality regions: {len(low_quality_regions)}")

    # Create visualization
    vis_image = quality_assessor.visualize_tile_quality(image, assessment)
    cv2.imwrite('quality_visualization.jpg', vis_image)
    """

    return sample_code


def advanced_tile_processing_example():
    """
    Example of advanced processing based on tile quality assessment.
    """
    example_code = """
    def apply_adaptive_processing(image: np.ndarray, assessment: TileQualityAssessment) -> np.ndarray:
        # Create a copy of the image
        processed_image = image.copy()
        
        # Process each tile based on its quality
        for tile_metric in assessment.tile_metrics:
            # Extract the tile from the image
            tile = processed_image[
                tile_metric.y:tile_metric.y + tile_metric.height,
                tile_metric.x:tile_metric.x + tile_metric.width
            ]
            
            # Apply different processing based on quality tier
            if tile_metric.quality_tier in [QualityTier.POOR, QualityTier.BAD]:
                # Apply strong enhancement for low quality tiles
                enhanced_tile = cv2.detailEnhance(tile, sigma_s=10, sigma_r=0.15)
            elif tile_metric.quality_tier == QualityTier.FAIR:
                # Apply moderate enhancement for fair quality tiles
                enhanced_tile = cv2.detailEnhance(tile, sigma_s=5, sigma_r=0.15)
            else:
                # For good/excellent tiles, apply minimal processing
                enhanced_tile = tile  # Or apply slight sharpening if needed
            
            # Put the processed tile back into the image
            processed_image[
                tile_metric.y:tile_metric.y + tile_metric.height,
                tile_metric.x:tile_metric.x + tile_metric.width
            ] = enhanced_tile
        
        return processed_image
    """
    
    return example_code


if __name__ == "__main__":
    # Example usage
    print("Tile-based Image Quality Assessment Module")
    print("This module provides functionality for assessing image quality at the tile level.")
    print("\nKey features:")
    print("- Divides images into overlapping tiles")
    print("- Assesses blur, contrast, glare, noise, and saturation in each tile")
    print("- Provides overall quality assessment and recommendations")
    print("- Identifies low-quality regions for targeted processing")
    print("- Creates visualizations of quality across the image")