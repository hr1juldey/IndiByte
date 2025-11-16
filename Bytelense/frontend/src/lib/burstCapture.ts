/**
 * Burst Capture & Intelligent Fusion Module
 *
 * Implements Stage-1 frontend processing:
 * - Real-time burst capture (5-7 frames)
 * - Frame alignment (translational)
 * - Intelligent weighted fusion (contrast + saturation + exposure)
 * - Light preprocessing (CLAHE + unsharp)
 *
 * This produces OCR-ready preview before backend processing.
 */

export interface BurstCaptureOptions {
  burstCount?: number;      // Number of frames to capture (default: 5)
  alignMaxDim?: number;     // Downscale for alignment (default: 300)
  enableLogging?: boolean;  // Enable debug logging
}

export interface BurstFrame {
  canvas: HTMLCanvasElement;
  timestamp: number;
  sharpness: number;        // Laplacian variance
}

export interface FusionWeights {
  contrast: cv.Mat;         // Laplacian-based contrast weight
  saturation: cv.Mat;       // Per-pixel saturation weight
  exposure: cv.Mat;         // Well-exposedness weight
}

export interface FusionResult {
  fusedImage: cv.Mat;
  weights: FusionWeights;
  processingTime: number;
}

export class BurstCaptureProcessor {
  private cv: typeof window.cv;
  private burstFrames: BurstFrame[] = [];
  private options: Required<BurstCaptureOptions>;
  private logger: (msg: string) => void;

  constructor(options: BurstCaptureOptions = {}) {
    this.cv = window.cv;
    this.options = {
      burstCount: options.burstCount || 5,
      alignMaxDim: options.alignMaxDim || 300,
      enableLogging: options.enableLogging || false,
    };
    this.logger = this.options.enableLogging ? console.log : () => {};
  }

  /**
   * Add a frame to the burst buffer
   */
  addFrame(canvas: HTMLCanvasElement): void {
    if (this.burstFrames.length >= this.options.burstCount) {
      // Remove oldest frame
      this.burstFrames.shift();
    }

    // Compute sharpness
    const sharpness = this.computeSharpness(canvas);

    this.burstFrames.push({
      canvas,
      timestamp: Date.now(),
      sharpness,
    });

    this.logger(`Added frame ${this.burstFrames.length}/${this.options.burstCount} (sharpness=${sharpness.toFixed(1)})`);
  }

  /**
   * Clear burst buffer
   */
  clearBurst(): void {
    this.burstFrames = [];
  }

  /**
   * Get current burst count
   */
  getBurstCount(): number {
    return this.burstFrames.length;
  }

  /**
   * Check if burst is ready for processing
   */
  isBurstReady(): boolean {
    return this.burstFrames.length >= 3; // At least 3 frames for fusion
  }

  // ==================== Sharpness Detection ====================

  /**
   * Compute Laplacian variance (sharpness metric)
   */
  private computeSharpness(canvas: HTMLCanvasElement): number {
    const img = this.cv.imread(canvas);
    const gray = new this.cv.Mat();
    this.cv.cvtColor(img, gray, this.cv.COLOR_RGBA2GRAY);

    const laplacian = new this.cv.Mat();
    this.cv.Laplacian(gray, laplacian, this.cv.CV_64F);

    // Compute variance
    const mean = new this.cv.Mat();
    const stddev = new this.cv.Mat();
    this.cv.meanStdDev(laplacian, mean, stddev);

    const variance = Math.pow(stddev.doubleAt(0, 0), 2);

    // Cleanup
    img.delete();
    gray.delete();
    laplacian.delete();
    mean.delete();
    stddev.delete();

    return variance;
  }

  // ==================== Frame Alignment ====================

  /**
   * Align frames using template matching (translational only)
   */
  private alignFrames(): { shifts: Array<{ dx: number; dy: number }>; reference: cv.Mat } {
    if (this.burstFrames.length < 2) {
      return {
        shifts: this.burstFrames.map(() => ({ dx: 0, dy: 0 })),
        reference: this.cv.imread(this.burstFrames[0].canvas),
      };
    }

    // Find reference frame (sharpest)
    let refIdx = 0;
    let bestSharpness = -1;
    for (let i = 0; i < this.burstFrames.length; i++) {
      if (this.burstFrames[i].sharpness > bestSharpness) {
        bestSharpness = this.burstFrames[i].sharpness;
        refIdx = i;
      }
    }

    const refCanvas = this.burstFrames[refIdx].canvas;
    const refImg = this.cv.imread(refCanvas);

    // Downscale for faster matching
    const refSmall = new this.cv.Mat();
    const refSize = new this.cv.Size(this.options.alignMaxDim, this.options.alignMaxDim);
    this.cv.resize(refImg, refSmall, refSize, 0, 0, this.cv.INTER_AREA);

    const refGray = new this.cv.Mat();
    this.cv.cvtColor(refSmall, refGray, this.cv.COLOR_RGBA2GRAY);

    // Compute shifts for each frame
    const shifts: Array<{ dx: number; dy: number }> = [];

    for (let i = 0; i < this.burstFrames.length; i++) {
      if (i === refIdx) {
        shifts.push({ dx: 0, dy: 0 });
        continue;
      }

      const frameImg = this.cv.imread(this.burstFrames[i].canvas);
      const frameSmall = new this.cv.Mat();
      this.cv.resize(frameImg, frameSmall, refSize, 0, 0, this.cv.INTER_AREA);

      const frameGray = new this.cv.Mat();
      this.cv.cvtColor(frameSmall, frameGray, this.cv.COLOR_RGBA2GRAY);

      // Template matching
      const result = new this.cv.Mat();
      this.cv.matchTemplate(refGray, frameGray, result, this.cv.TM_CCORR_NORMED);

      const mm = this.cv.minMaxLoc(result);
      const maxLoc = mm.maxLoc;

      // Scale back to full resolution
      const scaleX = refImg.cols / refSmall.cols;
      const scaleY = refImg.rows / refSmall.rows;
      const dxFull = Math.round(maxLoc.x * scaleX);
      const dyFull = Math.round(maxLoc.y * scaleY);

      shifts.push({ dx: dxFull, dy: dyFull });

      // Cleanup
      frameImg.delete();
      frameSmall.delete();
      frameGray.delete();
      result.delete();
    }

    // Cleanup
    refSmall.delete();
    refGray.delete();

    this.logger(`Reference frame: ${refIdx}, shifts: ${JSON.stringify(shifts)}`);

    return { shifts, reference: refImg };
  }

  /**
   * Apply translational shift to frame
   */
  private applyTranslation(img: cv.Mat, dx: number, dy: number): cv.Mat {
    const M = this.cv.Mat.eye(2, 3, this.cv.CV_32F);
    M.data32F[2] = -dx;
    M.data32F[5] = -dy;

    const shifted = new this.cv.Mat();
    this.cv.warpAffine(
      img,
      shifted,
      M,
      new this.cv.Size(img.cols, img.rows),
      this.cv.INTER_LINEAR,
      this.cv.BORDER_REPLICATE
    );

    M.delete();
    return shifted;
  }

  // ==================== Weighted Fusion ====================

  /**
   * Compute fusion weights (contrast + saturation + exposure)
   */
  private computeFusionWeights(frames: cv.Mat[]): FusionWeights {
    const K = frames.length;
    const h = frames[0].rows;
    const w = frames[0].cols;

    // 1. Contrast weights (Laplacian-based)
    const contrastWeights: cv.Mat[] = [];
    for (let i = 0; i < K; i++) {
      const gray = new this.cv.Mat();
      this.cv.cvtColor(frames[i], gray, this.cv.COLOR_BGR2GRAY);

      const lap = new this.cv.Mat();
      this.cv.Laplacian(gray, lap, this.cv.CV_32F);

      const absLap = new this.cv.Mat();
      this.cv.absdiff(lap, new this.cv.Scalar(0), absLap);

      // Normalize
      this.cv.normalize(absLap, absLap, 0, 1, this.cv.NORM_MINMAX, this.cv.CV_32F);
      contrastWeights.push(absLap);

      gray.delete();
      lap.delete();
    }

    // 2. Saturation weights (max-min per pixel)
    const saturationWeights: cv.Mat[] = [];
    for (let i = 0; i < K; i++) {
      const planes = new this.cv.MatVector();
      this.cv.split(frames[i], planes);

      const maxc = new this.cv.Mat();
      const minc = new this.cv.Mat();

      this.cv.max(planes.get(0), planes.get(1), maxc);
      this.cv.max(maxc, planes.get(2), maxc);

      this.cv.min(planes.get(0), planes.get(1), minc);
      this.cv.min(minc, planes.get(2), minc);

      const sat = new this.cv.Mat();
      this.cv.subtract(maxc, minc, sat);

      // Normalize
      this.cv.normalize(sat, sat, 0, 1, this.cv.NORM_MINMAX, this.cv.CV_32F);
      saturationWeights.push(sat);

      planes.delete();
      maxc.delete();
      minc.delete();
    }

    // 3. Exposure weights (Gaussian centered at 0.5)
    const exposureWeights: cv.Mat[] = [];
    for (let i = 0; i < K; i++) {
      const lab = new this.cv.Mat();
      this.cv.cvtColor(frames[i], lab, this.cv.COLOR_BGR2Lab);

      const L = new this.cv.Mat();
      this.cv.extractChannel(lab, L, 0);
      L.convertTo(L, this.cv.CV_32F, 1.0 / 255.0);

      // exp_weight = exp(-((L-0.5)^2)/(2*0.2^2))
      const expWeight = new this.cv.Mat(h, w, this.cv.CV_32F);

      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const l = L.floatAt(y, x);
          const diff = l - 0.5;
          const weight = Math.exp(-(diff * diff) / (2 * 0.2 * 0.2));
          expWeight.floatPtr(y, x)[0] = weight;
        }
      }

      // Normalize
      this.cv.normalize(expWeight, expWeight, 0, 1, this.cv.NORM_MINMAX, this.cv.CV_32F);
      exposureWeights.push(expWeight);

      lab.delete();
      L.delete();
    }

    return {
      contrast: contrastWeights[0], // Will be combined in fusion
      saturation: saturationWeights[0],
      exposure: exposureWeights[0],
    };
  }

  /**
   * Fuse aligned frames with weighted averaging
   */
  private fuseFrames(frames: cv.Mat[], shifts: Array<{ dx: number; dy: number }>): cv.Mat {
    const K = frames.length;
    const h = frames[0].rows;
    const w = frames[0].cols;

    // Apply translations
    const alignedFrames: cv.Mat[] = [];
    for (let i = 0; i < K; i++) {
      const aligned = this.applyTranslation(frames[i], shifts[i].dx, shifts[i].dy);
      alignedFrames.push(aligned);
    }

    // Compute weights
    const weights = this.computeFusionWeights(alignedFrames);

    // Combine weights: w = contrast * saturation * exposure
    const combinedWeight = new this.cv.Mat(h, w, this.cv.CV_32F);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const w_c = weights.contrast.floatAt(y, x);
        const w_s = weights.saturation.floatAt(y, x);
        const w_e = weights.exposure.floatAt(y, x);
        combinedWeight.floatPtr(y, x)[0] = w_c * w_s * w_e;
      }
    }

    // Weighted fusion per channel
    const outChannels: cv.Mat[] = [];
    for (let ch = 0; ch < 3; ch++) {
      const acc = new this.cv.Mat(h, w, this.cv.CV_32F, new this.cv.Scalar(0));
      let sumW = new this.cv.Mat(h, w, this.cv.CV_32F, new this.cv.Scalar(0));

      for (let i = 0; i < K; i++) {
        const frameCh = new this.cv.Mat();
        this.cv.extractChannel(alignedFrames[i], frameCh, ch);
        frameCh.convertTo(frameCh, this.cv.CV_32F);

        const weighted = new this.cv.Mat();
        this.cv.multiply(frameCh, combinedWeight, weighted);

        this.cv.add(acc, weighted, acc);
        this.cv.add(sumW, combinedWeight, sumW);

        frameCh.delete();
        weighted.delete();
      }

      // Normalize: acc / sumW
      const eps = 1e-6;
      const epsMat = new this.cv.Mat(h, w, this.cv.CV_32F, new this.cv.Scalar(eps));
      this.cv.add(sumW, epsMat, sumW);
      this.cv.divide(acc, sumW, acc);

      outChannels.push(acc);
      sumW.delete();
      epsMat.delete();
    }

    // Merge channels
    const out = new this.cv.Mat();
    this.cv.merge(outChannels, out);

    // Convert to 8U
    const out8 = new this.cv.Mat();
    out.convertTo(out8, this.cv.CV_8U);

    // Cleanup
    alignedFrames.forEach((f) => f.delete());
    combinedWeight.delete();
    outChannels.forEach((c) => c.delete());
    out.delete();

    return out8;
  }

  // ==================== Light Preprocessing ====================

  /**
   * Apply CLAHE for contrast enhancement
   */
  private applyCLAHE(img: cv.Mat): cv.Mat {
    const lab = new this.cv.Mat();
    this.cv.cvtColor(img, lab, this.cv.COLOR_BGR2Lab);

    const planes = new this.cv.MatVector();
    this.cv.split(lab, planes);

    const L = planes.get(0);
    const a = planes.get(1);
    const b = planes.get(2);

    // Apply CLAHE on L
    const clahe = this.cv.createCLAHE(2.0, new this.cv.Size(8, 8));
    const L_enhanced = new this.cv.Mat();
    clahe.apply(L, L_enhanced);

    // Merge back
    const labEnhanced = new this.cv.Mat();
    this.cv.merge([L_enhanced, a, b], labEnhanced);

    const result = new this.cv.Mat();
    this.cv.cvtColor(labEnhanced, result, this.cv.COLOR_Lab2BGR);

    // Cleanup
    lab.delete();
    planes.delete();
    L_enhanced.delete();
    labEnhanced.delete();

    return result;
  }

  /**
   * Apply unsharp mask for sharpening
   */
  private applyUnsharpMask(img: cv.Mat, strength: number = 1.2): cv.Mat {
    const blurred = new this.cv.Mat();
    this.cv.GaussianBlur(img, blurred, new this.cv.Size(5, 5), 1.0);

    const sharpened = new this.cv.Mat();
    this.cv.addWeighted(img, strength, blurred, -(strength - 1.0), 0, sharpened);

    blurred.delete();
    return sharpened;
  }

  // ==================== Main Processing ====================

  /**
   * Process burst frames to produce fusion + light preprocessing result
   */
  async processBurst(): Promise<{ canvas: HTMLCanvasElement; timings: Record<string, number> }> {
    if (!this.isBurstReady()) {
      throw new Error(`Not enough frames: ${this.burstFrames.length}/${this.options.burstCount}`);
    }

    const timings: Record<string, number> = {};
    const startTotal = performance.now();

    // 1. Align frames
    const alignStart = performance.now();
    const { shifts, reference } = this.alignFrames();
    const framesMats: cv.Mat[] = [];
    framesMats.push(reference);
    for (let i = 1; i < this.burstFrames.length; i++) {
      framesMats.push(this.cv.imread(this.burstFrames[i].canvas));
    }
    timings.alignment = performance.now() - alignStart;

    // 2. Fuse frames
    const fuseStart = performance.now();
    const fused = this.fuseFrames(framesMats, shifts);
    timings.fusion = performance.now() - fuseStart;

    // 3. Apply CLAHE
    const claheStart = performance.now();
    const clahed = this.applyCLAHE(fused);
    timings.clahe = performance.now() - claheStart;

    // 4. Apply unsharp
    const sharpStart = performance.now();
    const sharpened = this.applyUnsharpMask(clahed, 1.2);
    timings.sharpen = performance.now() - sharpStart;

    // Convert to canvas
    const outputCanvas = document.createElement('canvas');
    this.cv.imshow(outputCanvas, sharpened);

    // Cleanup
    framesMats.forEach((m) => m.delete());
    fused.delete();
    clahed.delete();
    sharpened.delete();

    timings.total = performance.now() - startTotal;

    this.logger(`Burst processing complete: ${timings.total.toFixed(0)}ms (${Object.entries(timings).map((e) => `${e[0]}=${e[1].toFixed(0)}ms`).join(', ')})`);

    return { canvas: outputCanvas, timings };
  }

  /**
   * Get burst statistics
   */
  getBurstStats(): { count: number; avgSharpness: number; bestSharpness: number } {
    if (this.burstFrames.length === 0) {
      return { count: 0, avgSharpness: 0, bestSharpness: 0 };
    }

    const sharpnesses = this.burstFrames.map((f) => f.sharpness);
    const avgSharpness = sharpnesses.reduce((a, b) => a + b, 0) / sharpnesses.length;
    const bestSharpness = Math.max(...sharpnesses);

    return {
      count: this.burstFrames.length,
      avgSharpness,
      bestSharpness,
    };
  }
}
