/**
 * Image Preprocessing Utilities using OpenCV.js
 *
 * Full pipeline for enhancing food label images before OCR:
 * - High-resolution scaling
 * - Grayscale conversion
 * - Noise reduction
 * - Adaptive thresholding (handles uneven lighting)
 * - Morphological operations (remove noise, enhance text)
 * - Sharpening
 */

export interface PreprocessingOptions {
  scaleFactor?: number;      // Default: 2.0 (scale to 200% for small text)
  denoise?: boolean;         // Default: true
  useBilateral?: boolean;    // Default: true (better edge preservation)
  adaptiveThreshold?: boolean; // Default: true
  morphology?: boolean;      // Default: true
  sharpen?: boolean;         // Default: true (apply after thresholding)
  debug?: boolean;           // Default: false (show intermediate steps)
}

export interface PreprocessingResult {
  processedImage: string;    // Base64 encoded result
  originalSize: { width: number; height: number };
  processedSize: { width: number; height: number };
  steps: string[];           // Log of steps performed
  processingTime: number;    // Milliseconds
}

/**
 * Wait for OpenCV.js to be loaded
 */
export async function waitForOpenCV(timeout = 10000): Promise<boolean> {
  const startTime = Date.now();

  while (!window.cv || !window.cv.Mat) {
    if (Date.now() - startTime > timeout) {
      throw new Error('OpenCV.js failed to load within timeout');
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  console.log('✓ OpenCV.js ready');
  return true;
}

/**
 * Check if OpenCV.js is loaded and ready
 */
export function isOpenCVReady(): boolean {
  return typeof window !== 'undefined' &&
         typeof window.cv !== 'undefined' &&
         typeof window.cv.Mat !== 'undefined';
}

/**
 * Preprocess image for OCR using full OpenCV.js pipeline
 */
export async function preprocessImage(
  imageData: string,
  options: PreprocessingOptions = {}
): Promise<PreprocessingResult> {
  const startTime = performance.now();
  const steps: string[] = [];

  // Default options
  const {
    scaleFactor = 2.0,      // Scale to 200% for better small text recognition
    denoise = true,
    useBilateral = true,    // Use bilateral filter for edge preservation
    adaptiveThreshold = true,
    morphology = true,
    sharpen = true,         // Enable sharpening by default
    debug = false
  } = options;

  // Ensure OpenCV is loaded
  if (!isOpenCVReady()) {
    await waitForOpenCV();
  }

  const cv = window.cv;

  // Load image into canvas
  const img = new Image();
  img.src = imageData;
  await new Promise((resolve) => { img.onload = resolve; });

  const canvas = document.createElement('canvas');
  canvas.width = img.width;
  canvas.height = img.height;
  const ctx = canvas.getContext('2d')!;
  ctx.drawImage(img, 0, 0);

  steps.push(`Loaded image: ${img.width}x${img.height}`);

  try {
    // Create OpenCV matrix from canvas
    let src = cv.imread(canvas);
    steps.push('Created OpenCV matrix');

    // Step 1: Color channel extraction (better for colored text)
    let gray = new cv.Mat();

    // For colored text on colored background, use channel separation
    // Extract individual channels and find the one with best contrast
    const channels = new cv.MatVector();
    cv.split(src, channels);

    // Try blue channel (often best for red/yellow text)
    const blue = channels.get(2);  // B channel from RGBA
    gray = blue.clone();

    // Clean up
    for (let i = 0; i < channels.size(); i++) {
      channels.get(i).delete();
    }
    channels.delete();

    steps.push('Extracted blue channel (for colored text)');

    // Step 2: Scale up for better small text recognition
    let resized = new cv.Mat();
    const newWidth = Math.round(gray.cols * scaleFactor);
    const newHeight = Math.round(gray.rows * scaleFactor);
    cv.resize(gray, resized, new cv.Size(newWidth, newHeight), 0, 0, cv.INTER_CUBIC);
    steps.push(`Scaled to ${newWidth}x${newHeight} (${scaleFactor}x = ${(scaleFactor * 100).toFixed(0)}%)`);
    gray.delete();

    // Step 3: Denoise with Bilateral Filter (preserves edges better than Gaussian)
    let denoised = new cv.Mat();
    if (denoise) {
      if (useBilateral) {
        // Bilateral filter: preserves edges while removing noise
        // Parameters: d=5, sigmaColor=75, sigmaSpace=75
        cv.bilateralFilter(resized, denoised, 5, 75, 75);
        steps.push('Applied bilateral filtering (edge-preserving denoising)');
      } else {
        cv.GaussianBlur(resized, denoised, new cv.Size(3, 3), 0);
        steps.push('Applied Gaussian blur denoising');
      }
      resized.delete();
    } else {
      denoised = resized;
    }

    // Step 4: Adaptive Thresholding (CRITICAL for uneven lighting)
    let thresholded = new cv.Mat();
    if (adaptiveThreshold) {
      cv.adaptiveThreshold(
        denoised,
        thresholded,
        255,
        cv.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv.THRESH_BINARY,
        31,  // Block size (balanced for colored backgrounds)
        2    // Constant (lower to avoid washing out)
      );
      steps.push('Applied adaptive thresholding (block=31, C=2 for colored text)');
      denoised.delete();
    } else {
      thresholded = denoised;
    }

    // Step 5: Morphological Operations (remove small noise, enhance text)
    let morphed = new cv.Mat();
    if (morphology) {
      const kernel = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(1, 1));

      // Opening: erosion followed by dilation (removes small white noise)
      cv.morphologyEx(thresholded, morphed, cv.MORPH_OPEN, kernel);

      // Closing: dilation followed by erosion (fills small black holes)
      cv.morphologyEx(morphed, morphed, cv.MORPH_CLOSE, kernel);

      steps.push('Applied morphological operations (opening + closing)');
      kernel.delete();
      thresholded.delete();
    } else {
      morphed = thresholded;
    }

    // Step 6: Sharpening (CRITICAL for small text - apply AFTER thresholding)
    let final = new cv.Mat();
    if (sharpen) {
      // Stronger sharpening kernel recommended for OCR: [[0,-1,0], [-1,5,-1], [0,-1,0]]
      const sharpenKernel = cv.matFromArray(3, 3, cv.CV_32F, [
         0, -1,  0,
        -1,  5, -1,
         0, -1,  0
      ]);
      cv.filter2D(morphed, final, cv.CV_8U, sharpenKernel);
      steps.push('Applied strong sharpening filter (for small text)');
      sharpenKernel.delete();
      morphed.delete();
    } else {
      final = morphed;
    }

    // Convert back to canvas
    cv.imshow(canvas, final);

    // Clean up OpenCV matrices
    src.delete();
    final.delete();

    // Convert canvas to base64
    const processedImage = canvas.toDataURL('image/jpeg', 0.95);

    const processingTime = performance.now() - startTime;
    steps.push(`Total processing time: ${processingTime.toFixed(0)}ms`);

    if (debug) {
      console.log('Image preprocessing steps:', steps);
    }

    return {
      processedImage,
      originalSize: { width: img.width, height: img.height },
      processedSize: { width: canvas.width, height: canvas.height },
      steps,
      processingTime
    };

  } catch (error) {
    console.error('Image preprocessing failed:', error);
    throw new Error(`Preprocessing error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Quick preprocessing for real-time preview (lighter processing)
 */
export async function preprocessImageQuick(imageData: string): Promise<string> {
  const result = await preprocessImage(imageData, {
    scaleFactor: 1.5,      // 150% scaling for preview
    denoise: false,
    useBilateral: false,
    adaptiveThreshold: true,
    morphology: false,
    sharpen: false
  });
  return result.processedImage;
}

/**
 * Full preprocessing for final OCR submission (max quality for small text)
 */
export async function preprocessImageFull(imageData: string): Promise<PreprocessingResult> {
  return preprocessImage(imageData, {
    scaleFactor: 3.0,      // 300% scaling for very small text on labels
    denoise: true,
    useBilateral: true,    // Edge-preserving denoising
    adaptiveThreshold: true,
    morphology: true,
    sharpen: true,         // Enable strong sharpening
    debug: true
  });
}
