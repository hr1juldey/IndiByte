import { useState, useEffect, useRef } from 'react';
import { useCamera } from '../hooks/useCamera';
import { BurstCaptureProcessor } from '../lib/burstCapture';
import type { DetailedAssessment, ScanProgressEvent } from '../types';

type ScanState = 'idle' | 'preprocessing' | 'scanning' | 'complete' | 'error';

// Define OCR result type to match the backend response
interface OCRResult {
  markdown: string;
  html: string;
  raw: string;
  token_count: number;
  error: boolean;
  chunks: any;
  images: any;
}

// Define the response type for the new endpoint
interface OCRResponse {
  status: string;
  enhanced_image_base64: string;
  quality_analysis: {
    quality_tier: string;
    sharpness: number;
    exposure_score: number;
    saturation_mean: number;
    dark_ratio: number;
    clipped_ratio: number;
  };
  stages_applied: string[];
  timings: Record<string, number>;
  total_processing_ms: number;
  ocr_result: OCRResult | null;
  ocr_time_ms: number;
  total_time_ms: number;
  message: string;
}

export function ScanPage() {
  const { videoRef, isActive, error: cameraError, currentFacingMode, startCamera, switchCamera, stopCamera, captureImage } = useCamera();
  const [scanState, setScanState] = useState<ScanState>('idle');
  const [progress, setProgress] = useState<ScanProgressEvent | null>(null);
  const [assessment, setAssessment] = useState<DetailedAssessment | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enhancedImage, setEnhancedImage] = useState<string | null>(null);

  // Initialize burst capture processor
  const burstProcessorRef = useRef<BurstCaptureProcessor | null>(null);

  useEffect(() => {
    burstProcessorRef.current = new BurstCaptureProcessor({ burstCount: 5 });

    return () => {
      // Stop camera when component unmounts
      if (isActive) {
        stopCamera();
      }
    };
  }, [isActive, stopCamera]);

  // Handle capture button click
  const handleCapture = async () => {
    try {
      setScanState('preprocessing');
      console.log('Starting burst capture...');

      // Capture multiple frames in rapid succession for burst processing
      // Optimized for OCR quality with specific frame timing and metadata
      if (videoRef.current && burstProcessorRef.current) {
        console.log(`Starting burst capture sequence - capturing ${burstProcessorRef.current['options'].burstCount} frames...`);

        // Capture frames rapidly with intentional micro-movements to capture different perspectives
        // This helps in creating a more detailed representation of the label
        for (let i = 0; i < burstProcessorRef.current['options'].burstCount; i++) {
          // Create a canvas to capture the current video frame
          const canvas = document.createElement('canvas');
          canvas.width = videoRef.current.videoWidth;
          canvas.height = videoRef.current.videoHeight;

          const ctx = canvas.getContext('2d');
          if (ctx) {
            // Draw the current video frame to the canvas
            ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

            // Add the captured frame to the burst processor
            burstProcessorRef.current.addFrame(canvas);
            console.log(`Added frame ${i+1}/${burstProcessorRef.current['options'].burstCount} to burst processor`);
          }

          // Brief pause between captures to allow for frame variations
          // Slightly different timing to capture micro-movements
          await new Promise(resolve => setTimeout(resolve, 30 + (i * 5))); // Increase delay slightly for each frame
        }

        // Process burst frames if we have enough frames
        if (burstProcessorRef.current.isBurstReady()) {
          console.log(`Burst ready with ${burstProcessorRef.current['burstFrames'].length} frames. Processing for OCR enhancement...`);
          const startTime = performance.now();
          const result = await burstProcessorRef.current.processBurst();
          const processingTime = performance.now() - startTime;

          console.log('Burst processing complete:', {
            timings: result.timings,
            processingTime: `${processingTime.toFixed(2)}ms`,
            finalDimensions: `${result.canvas.width}x${result.canvas.height}`
          });

          // Use the fused canvas for the OCR request (higher quality than single frame)
          const base64 = result.canvas.toDataURL('image/jpeg', 0.95); // Higher quality output

          // Send to OCR endpoint with enhanced metadata
          setScanState('scanning');
          console.log('Sending burst-processed image to OCR endpoint...');

          const response = await fetch('http://localhost:8002/api/label/process-with-ocr', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Type': 'mobile-burst',  // Indicate burst capture to backend
              'X-Request-ID': `burst-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`  // Unique request ID for tracking
            },
            body: JSON.stringify({
              image_base64: base64,
              metadata: {
                timestamp: Date.now(),
                capture_method: 'burst_fusion',
                burst_frame_count: burstProcessorRef.current['burstFrames'].length,
                processing_time_ms: processingTime,
                original_resolution: `${videoRef.current.videoWidth}x${videoRef.current.videoHeight}`,
                device_orientation: screen.orientation?.angle || window.orientation || 0
              }
            })
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const ocrResult: OCRResponse = await response.json();
          console.log('OCR response received:', {
            status: ocrResult.status,
            tokens_extracted: ocrResult.ocr_result?.token_count || 0,
            processing_time: `${ocrResult.total_time_ms}ms`,
            stages_applied: ocrResult.stages_applied
          });

          if (ocrResult.status === 'success') {
            setEnhancedImage(ocrResult.enhanced_image_base64);
            setOcrResult(ocrResult.ocr_result);

            // If OCR succeeded and we have results to show
            if (ocrResult.ocr_result && !ocrResult.ocr_result.error) {
              console.log(`OCR successful: ${ocrResult.ocr_result.token_count} tokens extracted`);
              setScanState('complete');
            } else {
              console.warn('OCR processing completed but with errors:', ocrResult.ocr_result?.error || ocrResult.message);
              setError(ocrResult.message || 'OCR processing failed');
              setScanState('error');
            }
          } else {
            console.error('Processing failed:', ocrResult.message);
            setError(ocrResult.message || 'Processing failed');
            setScanState('error');
          }
        } else {
          // Fallback: If we don't have enough frames for burst processing, capture one high-quality frame
          const frameCount = burstProcessorRef.current['burstFrames'].length;
          const requiredCount = burstProcessorRef.current['options'].burstCount;
          console.log(`Insufficient frames for burst processing (${frameCount}/${requiredCount}). Using single frame capture.`);

          // Capture a single high-quality frame from video
          const captureCanvas = document.createElement('canvas');
          captureCanvas.width = videoRef.current.videoWidth;
          captureCanvas.height = videoRef.current.videoHeight;

          const captureCtx = captureCanvas.getContext('2d');
          if (captureCtx) {
            // Apply any preprocessing for better OCR before capture
            captureCtx.drawImage(videoRef.current, 0, 0, captureCanvas.width, captureCanvas.height);
            const base64Image = captureCanvas.toDataURL('image/jpeg', 0.95); // Higher quality for single frame

            // Send to OCR endpoint with metadata indicating single frame
            setScanState('scanning');
            console.log('Sending high-quality single frame to OCR endpoint...');

            const response = await fetch('http://localhost:8002/api/label/process-with-ocr', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Client-Type': 'mobile-single',  // Indicate single capture to backend
                'X-Request-ID': `single-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`  // Unique request ID for tracking
              },
              body: JSON.stringify({
                image_base64: base64Image,
                metadata: {
                  timestamp: Date.now(),
                  capture_method: 'single_frame',
                  burst_frame_count: 0, // Explicitly 0 as this is single frame
                  original_resolution: `${videoRef.current.videoWidth}x${videoRef.current.videoHeight}`,
                  device_orientation: screen.orientation?.angle || window.orientation || 0
                }
              })
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            const ocrResult: OCRResponse = await response.json();
            console.log('Single frame OCR response received:', {
              status: ocrResult.status,
              tokens_extracted: ocrResult.ocr_result?.token_count || 0,
              processing_time: `${ocrResult.total_time_ms}ms`
            });

            if (ocrResult.status === 'success') {
              setEnhancedImage(ocrResult.enhanced_image_base64);
              setOcrResult(ocrResult.ocr_result);

              // If OCR succeeded and we have results to show
              if (ocrResult.ocr_result && !ocrResult.ocr_result.error) {
                console.log(`Single frame OCR successful: ${ocrResult.ocr_result.token_count} tokens extracted`);
                setScanState('complete');
              } else {
                console.warn('Single frame OCR completed but with errors:', ocrResult.ocr_result?.error || ocrResult.message);
                setError(ocrResult.message || 'OCR processing failed');
                setScanState('error');
              }
            } else {
              console.error('Single frame processing failed:', ocrResult.message);
              setError(ocrResult.message || 'Processing failed');
              setScanState('error');
            }
          } else {
            throw new Error('Could not get canvas context');
          }
        }
      } else {
        throw new Error('Video reference or burst processor not available');
      }
    } catch (err) {
      console.error('Capture/OCR error:', err);
      setError(err instanceof Error ? err.message : 'Capture or OCR failed');
      setScanState('error');
    }
  };

  // Render different states
  if (scanState === 'complete' && ocrResult) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-xl font-bold text-gray-900">Bytelense - Food Scanner</h1>
        </header>

        <main className="flex-1 flex flex-col p-4">
          <div className="w-full max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-6 text-center">Scan Results</h2>

            {/* Display enhanced image */}
            {enhancedImage && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Enhanced Image</h3>
                <img
                  src={enhancedImage}
                  alt="Processed label"
                  className="max-w-full h-auto rounded-lg border border-gray-300"
                />
              </div>
            )}

            {/* Display OCR results */}
            {ocrResult && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4">Nutrition Information</h3>
                <div
                  className="prose max-w-none border border-gray-200 rounded-lg p-4 bg-gray-50"
                  dangerouslySetInnerHTML={{ __html: ocrResult.html }}
                />

                <div className="mt-4 text-sm text-gray-600">
                  <p>Tokens extracted: {ocrResult.token_count}</p>
                  <p>Processing time: {ocrResult.error ? 'Error occurred' : 'Success'}</p>
                </div>
              </div>
            )}

            <div className="mt-6 text-center">
              <button
                onClick={() => {
                  setScanState('idle');
                  setOcrResult(null);
                  setEnhancedImage(null);
                }}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700"
              >
                Scan Another Label
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Preprocessing state (burst capture and fusion)
  if (scanState === 'preprocessing') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-xl font-bold text-gray-900">Bytelense - Food Scanner</h1>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center p-4">
          <div className="w-full max-w-md">
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-600 mx-auto mb-4"></div>
              <h2 className="text-lg font-semibold mb-2">Capturing Burst Images</h2>
              <p className="text-gray-600 mb-4">Aligning and fusing frames for best quality...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (scanState === 'scanning') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-xl font-bold text-gray-900">Bytelense - Food Scanner</h1>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center p-4">
          <div className="w-full max-w-md">
            <h2 className="text-lg font-semibold text-center mb-6">Processing your food label...</h2>

            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="flex justify-center mb-4">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
              </div>
              <p className="text-center text-gray-600">
                Analyzing image and extracting text with OCR...
              </p>
            </div>

            <div className="text-center">
              <p className="text-gray-600">Please wait while we process your food label...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (scanState === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-xl font-bold text-gray-900">Bytelense - Food Scanner</h1>
        </header>
        
        <main className="flex-1 flex flex-col items-center justify-center p-4">
          <div className="w-full max-w-md">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-red-800 mb-2">Scan Failed</h2>
              <p className="text-red-700 mb-4">{error}</p>
              <button
                onClick={() => setScanState('idle')}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Try Again
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Default: idle state with camera
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm p-4">
        <h1 className="text-xl font-bold text-gray-900">Bytelense - Food Scanner</h1>
      </header>
      
      <main className="flex-1 flex flex-col">
        {!isActive ? (
          <div className="flex-1 flex flex-col items-center justify-center p-4">
            <div className="text-center max-w-md">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Scan Your Food</h2>
              <p className="text-gray-600 mb-8">
                Point your camera at a food product to get a nutritional assessment and health verdict.
              </p>
              <div className="flex flex-col items-center space-y-4">
                <span className="text-gray-600">Select camera to start with:</span>
                <div className="flex flex-col sm:flex-row gap-4">
                  <button
                    onClick={() => startCamera('user')}
                    className="px-6 py-3 bg-gray-600 text-white rounded-lg shadow hover:bg-gray-700 transition-colors text-lg font-medium min-w-[150px]"
                  >
                    Front Camera
                  </button>
                  <button
                    onClick={() => startCamera('environment')}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition-colors text-lg font-medium min-w-[150px]"
                  >
                    Back Camera
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-[500px]">
            <div className="relative flex-1 min-h-[500px]">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="absolute inset-0 w-full h-full object-cover bg-black"
                style={{ minHeight: '500px' }}
              />
              
              {/* Overlay with instructions */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="border-4 border-white border-dashed rounded-lg w-64 h-64 flex items-center justify-center">
                  <div className="text-white text-center">
                    <div className="bg-black bg-opacity-50 rounded-full p-2 inline-block">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </div>
                    <p className="mt-2 bg-black bg-opacity-50 rounded px-2 py-1">Position food here</p>
                  </div>
                </div>
              </div>
              
              <div className="absolute bottom-8 left-0 right-0 flex justify-center">
                <button
                  onClick={handleCapture}
                  disabled={scanState === 'scanning'}
                  className="w-16 h-16 rounded-full bg-white border-4 border-blue-500 flex items-center justify-center shadow-lg disabled:opacity-50"
                >
                  <div className="w-12 h-12 rounded-full bg-blue-500"></div>
                </button>
              </div>

              <div className="absolute bottom-2 left-4">
                <button
                  onClick={switchCamera}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg shadow hover:bg-gray-700 flex items-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586a1 1 0 01-.707-.293l-1.121-1.121A2 2 0 0011.172 3H8.828a2 2 0 00-1.414.586L6.293 4.707A1 1 0 015.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                  {currentFacingMode === 'environment' ? 'Front' : 'Back'}
                </button>
              </div>

              <div className="absolute bottom-2 right-4">
                <button
                  onClick={stopCamera}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg shadow hover:bg-red-600"
                >
                  Stop Camera
                </button>
              </div>
            </div>
          </div>
        )}
        
        {cameraError && (
          <div className="bg-red-100 border border-red-200 rounded-lg p-4 m-4">
            <p className="text-red-700">Camera Error: {cameraError}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Reload Page
            </button>
          </div>
        )}
      </main>
    </div>
  );
}