/**
 * Real-time sharpness detection for camera feed
 * Uses Laplacian variance to measure image focus quality
 */

export interface SharpnessResult {
  score: number;      // 0-100 sharpness score
  isFocused: boolean; // true if above threshold
  quality: 'poor' | 'fair' | 'good' | 'excellent';
}

/**
 * Calculate sharpness score using Laplacian variance
 * Higher score = sharper image
 */
export function calculateSharpness(
  videoElement: HTMLVideoElement,
  sampleSize: number = 200
): SharpnessResult {
  // Create a small canvas for sampling
  const canvas = document.createElement('canvas');
  canvas.width = sampleSize;
  canvas.height = sampleSize;
  const ctx = canvas.getContext('2d')!;

  // Draw video frame to canvas (center crop)
  const videoWidth = videoElement.videoWidth;
  const videoHeight = videoElement.videoHeight;

  if (videoWidth === 0 || videoHeight === 0) {
    return { score: 0, isFocused: false, quality: 'poor' };
  }

  // Center crop
  const size = Math.min(videoWidth, videoHeight);
  const x = (videoWidth - size) / 2;
  const y = (videoHeight - size) / 2;

  ctx.drawImage(
    videoElement,
    x, y, size, size,  // source
    0, 0, sampleSize, sampleSize  // destination
  );

  // Get image data
  const imageData = ctx.getImageData(0, 0, sampleSize, sampleSize);
  const pixels = imageData.data;

  // Convert to grayscale and calculate Laplacian variance
  const gray = new Float32Array(sampleSize * sampleSize);
  for (let i = 0; i < sampleSize * sampleSize; i++) {
    const r = pixels[i * 4];
    const g = pixels[i * 4 + 1];
    const b = pixels[i * 4 + 2];
    gray[i] = 0.299 * r + 0.587 * g + 0.114 * b;
  }

  // Calculate Laplacian (edge detection)
  // Kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
  let variance = 0;
  let sum = 0;
  let count = 0;

  for (let y = 1; y < sampleSize - 1; y++) {
    for (let x = 1; x < sampleSize - 1; x++) {
      const idx = y * sampleSize + x;
      const laplacian =
        gray[idx - sampleSize] +  // top
        gray[idx + sampleSize] +  // bottom
        gray[idx - 1] +           // left
        gray[idx + 1] -           // right
        4 * gray[idx];            // center

      sum += laplacian;
      count++;
    }
  }

  const mean = sum / count;

  // Calculate variance
  for (let y = 1; y < sampleSize - 1; y++) {
    for (let x = 1; x < sampleSize - 1; x++) {
      const idx = y * sampleSize + x;
      const laplacian =
        gray[idx - sampleSize] +
        gray[idx + sampleSize] +
        gray[idx - 1] +
        gray[idx + 1] -
        4 * gray[idx];

      variance += Math.pow(laplacian - mean, 2);
    }
  }

  variance = variance / count;

  // Normalize score (0-100)
  // Typical variance ranges: blurry ~100-500, sharp ~1000-5000+
  const rawScore = Math.sqrt(variance);
  const normalizedScore = Math.min(100, (rawScore / 50) * 100);

  // Adjusted thresholds for real-world camera conditions (more lenient)
  const isFocused = rawScore > 300;  // Allow capture at lower threshold

  let quality: 'poor' | 'fair' | 'good' | 'excellent';
  if (rawScore < 200) quality = 'poor';        // Very blurry
  else if (rawScore < 400) quality = 'fair';   // Somewhat blurry but usable
  else if (rawScore < 800) quality = 'good';   // Good focus
  else quality = 'excellent';                   // Excellent focus

  return {
    score: Math.round(normalizedScore),
    isFocused,
    quality
  };
}

/**
 * Start monitoring sharpness in real-time
 */
export function startSharpnessMonitoring(
  videoElement: HTMLVideoElement,
  callback: (result: SharpnessResult) => void,
  intervalMs: number = 500
): () => void {
  const intervalId = setInterval(() => {
    if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
      const result = calculateSharpness(videoElement);
      callback(result);
    }
  }, intervalMs);

  return () => clearInterval(intervalId);
}
