import { useState, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { socketManager } from '../lib/socket';
import type { DetailedAssessment, ScanProgressEvent } from '../types';
import { VerdictDisplay } from './VerdictDisplay';
import { preprocessImageFull } from '../lib/imagePreprocessing';

type ScanState = 'idle' | 'preprocessing' | 'scanning' | 'complete' | 'error';

export function ScanPage() {
  const { videoRef, isActive, error: cameraError, currentFacingMode, startCamera, switchCamera, stopCamera, captureImage } = useCamera();
  const [scanState, setScanState] = useState<ScanState>('idle');
  const [progress, setProgress] = useState<ScanProgressEvent | null>(null);
  const [assessment, setAssessment] = useState<DetailedAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Connect to WebSocket on mount (OpenCV is now initialized in handleCapture)
  useEffect(() => {
    socketManager.connect();

    // Listen for scan events
    socketManager.onScanProgress((data) => {
      setProgress(data);
    });

    socketManager.onScanComplete((data) => {
      setScanState('complete');
      setAssessment(data.detailed_assessment);
      stopCamera();
    });

    socketManager.onScanError((data) => {
      setScanState('error');
      setError(data.message);
      stopCamera();
    });

    return () => {
      socketManager.disconnect();
      stopCamera();
    };
  }, [stopCamera]);

  // Handle capture button click
  const handleCapture = async () => {
    try {
      // Step 1: Capture image
      const base64 = await captureImage();

      // Step 2: Preprocess with OpenCV.js for better OCR
      setScanState('preprocessing');
      console.log('Preprocessing image with OpenCV.js...');

      const preprocessingResult = await preprocessImageFull(base64);
      console.log('Preprocessing complete:', preprocessingResult.steps);

      // Step 3: Send enhanced image to backend
      setScanState('scanning');

      // Remove data:image/jpeg;base64, prefix
      const base64Data = preprocessingResult.processedImage.split(',')[1];

      // Start scan with enhanced image
      socketManager.startScan('testuser', base64Data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Capture failed');
      setScanState('error');
    }
  };

  // Render different states
  if (scanState === 'complete' && assessment) {
    return <VerdictDisplay assessment={assessment} />;
  }

  // Preprocessing state (OpenCV.js enhancement)
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
              <h2 className="text-lg font-semibold mb-2">Enhancing Image Quality</h2>
              <p className="text-gray-600 mb-4">Applying OpenCV.js preprocessing...</p>
              <ul className="text-sm text-gray-500 text-left space-y-1">
                <li>✓ Grayscale conversion</li>
                <li>✓ High-resolution scaling</li>
                <li>✓ Noise reduction</li>
                <li>✓ Adaptive thresholding</li>
                <li>✓ Text enhancement</li>
              </ul>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (scanState === 'scanning' && progress) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-xl font-bold text-gray-900">Bytelense - Food Scanner</h1>
        </header>
        
        <main className="flex-1 flex flex-col items-center justify-center p-4">
          <div className="w-full max-w-md">
            <h2 className="text-lg font-semibold text-center mb-6">Scanning your food...</h2>
            
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Progress</span>
                <span className="text-sm font-medium text-gray-700">{Math.round(progress.progress * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
                  style={{ width: `${progress.progress * 100}%` }}
                ></div>
              </div>
              <p className="mt-3 text-center text-gray-600">
                {progress.message}
              </p>
              <p className="text-center text-sm text-gray-500 mt-2">
                Stage {progress.stage_number} of {progress.total_stages}
              </p>
            </div>
            
            <div className="text-center">
              <p className="text-gray-600">Please wait while we analyze your food...</p>
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
                <div className="flex space-x-4">
                  <button
                    onClick={() => startCamera('user')}
                    className="px-6 py-3 bg-gray-600 text-white rounded-lg shadow hover:bg-gray-700 transition-colors text-lg font-medium"
                  >
                    Front Camera
                  </button>
                  <button
                    onClick={() => startCamera('environment')}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition-colors text-lg font-medium"
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