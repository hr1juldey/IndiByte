# Image Quality Assessment for OCR Pipeline

This module provides mathematical methods using OpenCV to assess image quality for OCR processing. It evaluates blur, noise, contrast, and glare to help determine if an image is suitable for OCR and optimize processing time.

## Features

- **Blur Detection**: Uses variance of Laplacian method to detect blur in images
- **Noise Assessment**: Calculates entropy to measure image detail/content
- **Contrast Assessment**: Uses standard deviation of pixel intensities
- **Glare Detection**: Measures percentage of bright pixels that might indicate glare
- **Composite Quality Score**: Combines all metrics with appropriate weights to produce a 0-100 quality score
- **Processing Recommendations**: Provides suggestions for image enhancement when needed

## Files

- `image_quality_assessor.py`: Main implementation of the quality assessment system
- `test_image_quality_assessment.py`: Comprehensive test and validation script
- `image_analyzer.py`: Initial script used to understand quality differences between test images

## Usage

### Basic Usage
```python
from image_quality_assessor import ImageQualityAssessor

assessor = ImageQualityAssessor()
result = assess_image_quality("/path/to/your/image.jpg")

print(f"Quality Score: {result['composite_score']:.2f}/100")
print(f"Category: {result['quality_category']}")
print(f"OCR Recommended: {result['ocr_recommended']}")
```

### Batch Assessment
```python
image_paths = ["/path/to/img1.jpg", "/path/to/img2.jpg", "/path/to/img3.jpg"]
results = assessor.batch_assess(image_paths)

# Results are sorted by quality score (highest first)
for result in results:
    print(f"{result['image_path']}: {result['composite_score']:.2f}")
```

### Output Format
Each assessment returns a dictionary with:
- `image_path`: Path to the analyzed image
- `blur_metric`: Variance of Laplacian (higher = sharper)
- `noise_metric`: Entropy of the image (higher = more detail)
- `contrast_metric`: Standard deviation of pixel intensities (higher = more contrast)
- `glare_metric`: Ratio of very bright pixels (higher = more glare)
- `brightness_metric`: Average brightness of the image
- `saturation_metric`: Average saturation in HSV space
- `uniformity_metric`: Local variance of brightness (lower = more uniform lighting)
- `composite_score`: Overall quality score (0-100)
- `quality_category`: Quality category (Excellent, Good, Fair, Poor)
- `ocr_recommended`: Whether OCR is recommended for this image
- `processing_recommendation`: Suggestions for image enhancement

## Quality Categories

- **Excellent (≥70)**: High quality, ready for OCR
- **Good (50-69)**: Good quality, suitable for OCR
- **Fair (30-49)**: Moderate quality, OCR may work but enhancement recommended
- **Poor (<30)**: Low quality, enhancement necessary before OCR

## Algorithm Details

### Blur Detection
Uses the variance of the Laplacian method. A convolution with the Laplacian operator is applied to the image and the variance of the response indicates the focus measure.

### Noise Detection
Calculates the entropy of the grayscale image, which measures the amount of information in the image. Higher entropy generally indicates more detail and less noise.

### Contrast Assessment
Computes the standard deviation of pixel intensities in the grayscale image. Higher values indicate higher contrast.

### Glare Detection
Measures the percentage of pixels with intensity values above 240 (out of 255) in the grayscale image, indicating potential glare areas.

### Composite Score
The overall quality score is calculated with the following weights:
- Blur: 40% (most important for OCR accuracy)
- Contrast: 25% (affects text readability)
- Noise/Entropy: 15% (affects readability)
- Glare: 10% (affects OCR accuracy)
- Brightness: 10% (affects readability)

## Test Images Analysis

The system was tested with these images:
- `test_real.jpeg`: Real-world image (dirty, blurry, readable by humans)
- `test_clean.jpeg`: Cleaner with some glare and warp
- `test_ocr.jpeg`: Good image with good lighting and no glare
- `test_ocr_clean.jpeg`: Good image but with scaled dimensions
- `test_processed_1.jpeg`: Processed image that might be of lower quality

## Performance Benefits

By assessing image quality before OCR processing, the system can:

1. **Reduce processing time** by avoiding OCR on images that will take >180 seconds due to large size or poor quality
2. **Optimize image preprocessing** by applying appropriate enhancement techniques based on the detected issues
3. **Improve OCR accuracy** by suggesting enhancement of poor quality images before processing
4. **Provide user feedback** about image quality and recommendations

## Integration with OCR Pipeline

The system can be integrated into the OCR pipeline to:
1. Pre-screen images before OCR processing
2. Automatically apply enhancement techniques based on quality assessment
3. Skip OCR on images that are too low quality to process effectively
4. Adjust processing parameters based on quality metrics