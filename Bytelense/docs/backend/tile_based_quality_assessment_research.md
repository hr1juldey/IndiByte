# Tile-Based Image Quality Assessment for OCR Preprocessing

## Overview

This document provides comprehensive research and solutions for implementing local tile-based image quality assessment for OCR preprocessing. The approach involves dividing images into smaller tiles and assessing each tile individually to identify localized issues like glare spots, blurred text areas, or other artifacts that might affect OCR performance in specific regions of an image.

## 1. Techniques for Dividing Images into Tiles

### Grid-Based Tiling
The most common approach is to divide the image into a regular grid of tiles:

```python
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
```

### Overlapping Tiles
Using overlapping tiles helps to:
- Reduce edge artifacts
- Provide better coverage of border regions
- Allow for more robust quality assessment near tile boundaries

### Adaptive Tiling
For images with varying content density, adaptive tiling can be used:
- Larger tiles for uniform regions
- Smaller tiles for complex regions
- Content-aware tile boundaries

## 2. Methods for Assessing Local Quality Metrics

### Sharpness Assessment
Sharpness is critical for OCR performance:

```python
def calculate_sharpness(self, tile: np.ndarray) -> float:
    """
    Calculate sharpness using the Laplacian variance method.
    """
    gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Normalize to 0-1 range (assuming max sharpness around 500)
    return min(laplacian_var / 500.0, 1.0)
```

Alternative methods include:
- Sobel gradient magnitude
- Tenengrad variance
- Brenner gradient

### Contrast Assessment
Contrast is essential for text readability:

```python
def calculate_contrast(self, tile: np.ndarray) -> float:
    """
    Calculate contrast using the standard deviation of pixel intensities.
    """
    gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    contrast = np.std(gray)
    # Normalize to 0-1 range (assuming max contrast around 128)
    return min(contrast / 128.0, 1.0)
```

### Glare Detection
Glare can wash out text and reduce OCR accuracy:

```python
def calculate_glare_score(self, tile: np.ndarray) -> float:
    """
    Calculate glare score based on bright pixels.
    """
    gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    # Count pixels that are very bright (potential glare)
    bright_pixels = np.sum(gray > 220)
    total_pixels = gray.size
    glare_ratio = bright_pixels / total_pixels if total_pixels > 0 else 0.0

    # Invert so that lower glare scores are better
    return 1.0 - glare_ratio
```

### Noise Assessment
Noise can interfere with character recognition:

```python
def calculate_noise_level(self, tile: np.ndarray) -> float:
    """
    Estimate noise level using Laplacian of Gaussian.
    """
    gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    # Apply LoG filter
    log_filtered = cv2.Laplacian(gray, cv2.CV_64F)
    noise_level = np.std(log_filtered)
    # Normalize and invert so higher scores are better (less noise)
    normalized_noise = min(noise_level / 50.0, 1.0)
    return 1.0 - normalized_noise
```

### Saturation Assessment
Color saturation can indicate image quality:

```python
def calculate_saturation(self, tile: np.ndarray) -> float:
    """
    Calculate average saturation in HSV color space.
    """
    hsv = cv2.cvtColor(tile, cv2.COLOR_BGR2HSV)
    saturation = np.mean(hsv[:, :, 1])
    return saturation / 255.0
```

## 3. Algorithms for Combining Tile Scores

### Weighted Average Approach
Combine individual tile metrics into an overall score:

```python
def determine_tile_quality_tier(self, metrics: TileQualityMetrics) -> QualityTier:
    """
    Determine the quality tier based on combined metrics.
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
```

### Statistical Aggregation
Use statistical measures to combine tile scores:

```python
# Calculate overall metrics
overall_sharpness = np.mean([tm.sharpness for tm in tile_metrics])
overall_contrast = np.mean([tm.contrast for tm in tile_metrics])
overall_brightness = np.mean([tm.brightness for tm in tile_metrics])
overall_glare_score = np.mean([tm.glare_score for tm in tile_metrics])
overall_noise_level = np.mean([tm.noise_level for tm in tile_metrics])
overall_saturation = np.mean([tm.saturation for tm in tile_metrics])

# Calculate standard deviations to understand quality consistency
sharpness_std = np.std([tm.sharpness for tm in tile_metrics])
contrast_std = np.std([tm.contrast for tm in tile_metrics])
```

### Quality Tier Classification
Classify the overall image quality based on the distribution of tile qualities:

```python
def determine_overall_quality_tier(self, tile_metrics: List[TileQualityMetrics]) -> QualityTier:
    """
    Determine overall quality based on distribution of tile qualities.
    """
    # Count tiles in each quality tier
    tier_counts = {tier: 0 for tier in QualityTier}
    for tm in tile_metrics:
        tier_counts[tm.quality_tier] += 1

    # Calculate percentages
    total_tiles = len(tile_metrics)
    if total_tiles == 0:
        return QualityTier.BAD

    excellent_pct = tier_counts[QualityTier.EXCELLENT] / total_tiles
    good_pct = tier_counts[QualityTier.GOOD] / total_tiles
    fair_pct = tier_counts[QualityTier.FAIR] / total_tiles
    poor_pct = tier_counts[QualityTier.POOR] / total_tiles
    bad_pct = tier_counts[QualityTier.BAD] / total_tiles

    # Determine overall tier based on majority and critical issues
    if excellent_pct >= 0.8:
        return QualityTier.EXCELLENT
    elif excellent_pct + good_pct >= 0.8:
        return QualityTier.GOOD
    elif bad_pct >= 0.3:  # If 30% or more tiles are bad
        return QualityTier.BAD
    elif poor_pct + bad_pct >= 0.5:  # If 50% or more tiles are poor/bad
        return QualityTier.POOR
    else:
        return QualityTier.FAIR
```

## 4. Existing Implementations of Tile-Based Quality Assessment

### OpenCV-Based Approaches
OpenCV provides efficient implementations for most quality metrics:
- `cv2.Laplacian()` for sharpness assessment
- `cv2.cvtColor()` for color space conversions
- Statistical functions for contrast and noise analysis

### Specialized Libraries
- **scikit-image**: Advanced image analysis tools
- **PIL/Pillow**: Image processing capabilities
- **NumPy**: Efficient array operations

### Commercial Solutions
- Adobe's image quality assessment tools
- Google Vision API quality analysis
- AWS Rekognition quality metrics

## 5. Approaches Effective for OCR Preprocessing

### Text-Specific Quality Assessment
Focus on metrics that directly impact text readability:
- Character stroke width consistency
- Text-background contrast
- Text region sharpness

### Content-Aware Processing
Different regions may require different preprocessing:
- Text regions: Enhance sharpness and contrast
- Image regions: Preserve details without over-enhancement
- Mixed regions: Apply balanced processing

### Adaptive Preprocessing Pipeline
Based on tile quality assessment, apply targeted preprocessing:

```python
def apply_adaptive_processing(image: np.ndarray, assessment: TileQualityAssessment) -> np.ndarray:
    """
    Apply different processing based on tile quality assessment.
    """
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
```

### Quality-Based OCR Confidence Adjustment
Use quality scores to adjust OCR confidence thresholds:
- Lower confidence requirements for high-quality tiles
- Higher confidence requirements for low-quality tiles

## 6. Implementation in the Current Project

The implementation has been added to the existing project in the file:
`/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/backend/app/services/tile_quality_assessment.py`

### Integration Points
1. **Quality Analysis**: Can be integrated with existing `analyze_quality` method
2. **Preprocessing Pipeline**: Can enhance the adaptive processing in `LabelProcessor`
3. **OCR Pipeline**: Can provide quality feedback to improve OCR results

### Usage Example
```python
from app.services.tile_quality_assessment import TileBasedQualityAssessment

# Initialize the quality assessor
quality_assessor = TileBasedQualityAssessment(tile_size=64, overlap=16)

# Load and assess an image
image = cv2.imread('path/to/image.jpg')
assessment = quality_assessor.assess_image_quality(image)

# Get recommendations for preprocessing
recommendations = assessment.recommended_preprocessing

# Apply adaptive processing based on quality assessment
processed_image = apply_adaptive_processing(image, assessment)
```

## 7. Performance Considerations

### Computational Efficiency
- Process tiles in parallel when possible
- Use efficient OpenCV operations
- Consider processing only a subset of tiles for quick assessment

### Memory Management
- Process tiles in chunks to avoid memory issues
- Release intermediate results when no longer needed
- Consider streaming processing for large images

### Accuracy vs. Speed Trade-offs
- Adjust tile size based on required accuracy
- Use faster approximations for initial assessment
- Apply detailed analysis only to problematic regions

## 8. Future Enhancements

### Machine Learning Integration
- Train models to predict OCR success based on tile metrics
- Use deep learning for more sophisticated quality assessment
- Implement feedback loops to improve quality metrics

### Multi-Scale Analysis
- Analyze tiles at multiple scales for better accuracy
- Combine results from different scales for robust assessment

### Specialized Metrics
- Text-specific quality metrics
- Font-size aware assessment
- Layout-aware quality evaluation

This comprehensive approach to tile-based image quality assessment provides a robust foundation for improving OCR preprocessing by identifying and addressing localized quality issues that might be missed by global image analysis methods.