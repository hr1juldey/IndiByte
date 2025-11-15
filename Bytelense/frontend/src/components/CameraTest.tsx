import { useState, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { preprocessImageFull, waitForOpenCV, PreprocessingResult } from '../lib/imagePreprocessing';
import { BeforeAfterPreview } from './BeforeAfterPreview';

type TestState = 'idle' | 'camera' | 'processing' | 'preview';

export function CameraTest() {
  const { videoRef, isActive, error: cameraError, startCamera, stopCamera, captureImage } = useCamera();
  const [state, setState] = useState<TestState>('idle');
  const [status, setStatus] = useState('Click Start Camera to begin');
  const [originalImage, setOriginalImage] = useState<string>('');
  const [preprocessingResult, setPreprocessingResult] = useState<PreprocessingResult | null>(null);
  const [opencvReady, setOpencvReady] = useState(false);

  // Check OpenCV status on mount
  useEffect(() => {
    const checkOpenCV = async () => {
      try {
        await waitForOpenCV();
        setOpencvReady(true);
        setStatus('✓ OpenCV.js loaded and ready');
      } catch (err) {
        setStatus('❌ OpenCV.js failed to load. Refresh page to retry.');
      }
    };
    checkOpenCV();
  }, []);

  const handleStartCamera = async () => {
    setStatus('Starting camera with high-resolution settings...');
    await startCamera();
    setState('camera');
    setStatus('Camera active. Position food label and capture.');
  };

  const handleCapture = async () => {
    try {
      setState('processing');
      setStatus('Capturing image...');

      const captured = await captureImage();
      setOriginalImage(captured);
      setStatus('Image captured! Preprocessing with OpenCV.js...');

      // Preprocess with full pipeline
      const result = await preprocessImageFull(captured);
      setPreprocessingResult(result);

      setState('preview');
      setStatus('✓ Preprocessing complete!');

    } catch (err) {
      setStatus(`❌ Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setState('camera');
      console.error('Capture/preprocessing error:', err);
    }
  };

  const handleRetake = () => {
    setOriginalImage('');
    setPreprocessingResult(null);
    setState('camera');
    setStatus('Camera active. Position food label and capture.');
  };

  const handleConfirm = () => {
    setStatus('✓ Enhanced image ready for OCR!');
    console.log('Enhanced image ready:', preprocessingResult?.processedImage.substring(0, 100) + '...');
    // In real app, this would send to backend
  };

  // Show before/after preview
  if (state === 'preview' && preprocessingResult && originalImage) {
    return (
      <BeforeAfterPreview
        originalImage={originalImage}
        processedImage={preprocessingResult.processedImage}
        processingTime={preprocessingResult.processingTime}
        steps={preprocessingResult.steps}
        onConfirm={handleConfirm}
        onRetake={handleRetake}
      />
    );
  }

  // Processing state
  if (state === 'processing') {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
        <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-xl font-bold text-white mb-2">Processing Image</h2>
          <p className="text-gray-400">{status}</p>
          <div className="mt-6 text-left text-sm text-gray-500">
            <p className="mb-2">OpenCV.js pipeline:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Grayscale conversion</li>
              <li>High-resolution scaling</li>
              <li>Noise reduction</li>
              <li>Adaptive thresholding</li>
              <li>Morphological enhancement</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // Camera view
  if (state === 'camera' && isActive) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col">
        <header className="bg-gray-800 shadow-lg p-4">
          <h1 className="text-xl font-bold text-white">Camera Test - Enhanced Quality</h1>
          <p className="text-sm text-gray-400">{status}</p>
        </header>

        <div className="flex-1 relative min-h-[500px]">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="absolute inset-0 w-full h-full object-cover bg-black"
            style={{ minHeight: '500px' }}
          />

          {/* Overlay guide */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="border-4 border-white border-dashed rounded-lg w-80 h-80 flex items-center justify-center">
              <div className="text-white text-center bg-black bg-opacity-70 rounded-lg p-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="font-bold">Position food label here</p>
                <p className="text-sm mt-1">Fill the frame for best results</p>
              </div>
            </div>
          </div>

          {/* Capture button */}
          <div className="absolute bottom-8 left-0 right-0 flex justify-center gap-4">
            <button
              onClick={stopCamera}
              className="px-6 py-3 bg-red-600 text-white rounded-lg shadow-lg hover:bg-red-700 font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleCapture}
              className="w-20 h-20 rounded-full bg-white border-4 border-blue-500 flex items-center justify-center shadow-lg hover:scale-105 transition-transform"
            >
              <div className="w-16 h-16 rounded-full bg-blue-500"></div>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Idle state
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <h1 className="text-4xl font-bold text-white mb-4 text-center">
          Camera Test - Enhanced Quality
        </h1>

        <div className="bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-3">Status</h2>
          <p className="text-gray-300 mb-4">{status}</p>

          <div className="bg-gray-700 rounded p-4 mb-4">
            <h3 className="font-bold text-white mb-2">OpenCV.js Status:</h3>
            <p className={opencvReady ? 'text-green-400' : 'text-yellow-400'}>
              {opencvReady ? '✓ Loaded and ready' : '⏳ Loading...'}
            </p>
          </div>

          <button
            onClick={handleStartCamera}
            disabled={!opencvReady}
            className="w-full px-6 py-4 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition-colors text-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {opencvReady ? 'Start Camera' : 'Waiting for OpenCV.js...'}
          </button>
        </div>

        <div className="bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-3">Enhancements</h2>
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span><strong>High Resolution:</strong> Up to 4K capture (3840x2160)</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span><strong>Auto-Focus:</strong> Continuous focus for sharp text</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span><strong>2x Zoom:</strong> Magnified view of fine print</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span><strong>Adaptive Thresholding:</strong> Handles uneven lighting</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span><strong>Noise Reduction:</strong> Removes blur and artifacts</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-400 mr-2">✓</span>
              <span><strong>Morphological Enhancement:</strong> Sharpens text edges</span>
            </li>
          </ul>
        </div>

        {cameraError && (
          <div className="bg-red-900 border border-red-700 rounded-lg p-4 mt-6">
            <p className="text-red-100">Camera Error: {cameraError}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Reload Page
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
