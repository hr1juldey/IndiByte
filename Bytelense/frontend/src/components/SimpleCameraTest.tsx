import { useEffect, useState } from 'react';
import { useCamera } from '../hooks/useCamera';
import { preprocessImageFull, waitForOpenCV, PreprocessingResult } from '../lib/imagePreprocessing';
import { socketManager } from '../lib/socket';
import type { DetailedAssessment, ScanProgressEvent } from '../types';
import { startSharpnessMonitoring, type SharpnessResult } from '../lib/sharpnessDetector';

export function SimpleCameraTest() {
  const { videoRef, isActive, error, startCamera, stopCamera, captureImage } = useCamera();
  const [processing, setProcessing] = useState(false);
  const [originalImage, setOriginalImage] = useState<string>('');
  const [result, setResult] = useState<PreprocessingResult | null>(null);
  const [opencvReady, setOpencvReady] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState<ScanProgressEvent | null>(null);
  const [assessment, setAssessment] = useState<DetailedAssessment | null>(null);
  const [sharpness, setSharpness] = useState<SharpnessResult | null>(null);

  useEffect(() => {
    console.log('SimpleCameraTest mounted');
    console.log('isActive:', isActive);
    console.log('error:', error);

    // Wait for OpenCV
    waitForOpenCV().then(() => {
      setOpencvReady(true);
      console.log('✓ OpenCV.js ready');
    }).catch(err => {
      console.error('OpenCV.js failed:', err);
    });

    // Connect to WebSocket for backend testing
    socketManager.connect();
    socketManager.onScanProgress((data) => setScanProgress(data));
    socketManager.onScanComplete((data) => {
      setAssessment(data.detailed_assessment);
      setScanning(false);
    });
    socketManager.onScanError((data) => {
      alert(`Scan error: ${data.message}`);
      setScanning(false);
    });

    return () => {
      socketManager.disconnect();
    };
  }, [isActive, error]);

  // Real-time sharpness monitoring
  useEffect(() => {
    if (!isActive || !videoRef.current) {
      setSharpness(null);
      return;
    }

    console.log('Starting sharpness monitoring...');
    const stopMonitoring = startSharpnessMonitoring(
      videoRef.current,
      (result) => {
        setSharpness(result);
        // Log focus changes
        if (result.quality === 'excellent' || result.quality === 'good') {
          console.log('✓ Focus quality:', result.quality, '| Score:', result.score);
        }
      },
      500 // Check every 500ms
    );

    return () => {
      console.log('Stopping sharpness monitoring');
      stopMonitoring();
    };
  }, [isActive, videoRef]);

  const handleSendToBackend = () => {
    if (!result) return;

    try {
      setScanning(true);
      setScanProgress(null);
      setAssessment(null);

      const base64Data = result.processedImage.split(',')[1];
      socketManager.startScan('testuser', base64Data);
      console.log('Sent enhanced image to backend');
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Failed to send'}`);
      setScanning(false);
    }
  };

  const handleCapture = async () => {
    try {
      setResult(null); // Clear previous results

      // Countdown to allow autofocus (increased to 5 seconds)
      console.log('Starting countdown for autofocus...');
      for (let i = 5; i > 0; i--) {
        setCountdown(i);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      setCountdown(null);

      setProcessing(true);
      console.log('Capturing image...');

      const captured = await captureImage();
      setOriginalImage(captured);
      console.log('Image captured, size:', captured.length, 'bytes');
      console.log('Starting preprocessing...');

      const preprocessingResult = await preprocessImageFull(captured);
      setResult(preprocessingResult);
      console.log('Preprocessing complete!', preprocessingResult.steps);
      console.log('Processed image size:', preprocessingResult.processedImage.length, 'bytes');

      setProcessing(false);

      // Scroll to results
      setTimeout(() => {
        const resultsElement = document.getElementById('results-section');
        resultsElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      console.error('Capture/preprocessing failed:', err);
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-4">Simple Camera Test</h1>

        <div className="bg-gray-800 rounded-lg p-4 mb-4">
          <p className="text-white mb-2">Status:</p>
          <p className="text-green-400">Camera active: {isActive ? 'YES' : 'NO'}</p>
          <p className="text-blue-400">OpenCV.js: {opencvReady ? 'READY' : 'Loading...'}</p>
          {sharpness && (
            <p className={
              sharpness.quality === 'excellent' ? 'text-green-400' :
              sharpness.quality === 'good' ? 'text-lime-400' :
              sharpness.quality === 'fair' ? 'text-yellow-400' :
              'text-red-400'
            }>
              Focus Quality: {sharpness.quality.toUpperCase()} (score: {sharpness.score}/100)
            </p>
          )}
          {error && <p className="text-red-400">Error: {error}</p>}
          {processing && <p className="text-yellow-400">Processing image...</p>}
        </div>

        <div className="mb-4 flex gap-2">
          <button
            onClick={() => startCamera('environment')}
            disabled={isActive}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Start Camera (Back)
          </button>
          <button
            onClick={() => startCamera('user')}
            disabled={isActive}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            Start Camera (Front)
          </button>
          <button
            onClick={stopCamera}
            disabled={!isActive}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            Stop Camera
          </button>
          <button
            onClick={handleCapture}
            disabled={!isActive || !opencvReady || processing || countdown !== null}
            className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-bold text-lg"
          >
            {countdown !== null
              ? `📷 Focusing... ${countdown}`
              : processing
              ? '⚙️ Processing...'
              : '📸 Capture & Enhance'}
          </button>
        </div>

        {/* Video element - always rendered */}
        <div
          className="bg-black rounded-lg overflow-hidden relative transition-all duration-300"
          style={{
            minHeight: '480px',
            boxShadow: sharpness
              ? sharpness.quality === 'excellent' ? '0 0 20px 5px #22c55e'  // green
              : sharpness.quality === 'good' ? '0 0 20px 5px #84cc16'       // lime
              : sharpness.quality === 'fair' ? '0 0 20px 5px #eab308'       // yellow
              : '0 0 20px 5px #ef4444'                                       // red
              : 'none'
          }}
        >
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full"
            style={{
              minHeight: '480px',
              maxHeight: '80vh',
              backgroundColor: '#000',
              display: 'block'
            }}
          />

          {/* Countdown overlay */}
          {countdown !== null && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
              <div className="text-center">
                <div className="text-9xl font-bold text-white mb-4 animate-pulse">
                  {countdown}
                </div>
                <p className="text-2xl text-white font-bold">Hold perfectly still...</p>
                <p className="text-lg text-yellow-300 mt-2">⏳ Waiting for autofocus to lock (5 seconds)</p>
                <p className="text-sm text-gray-300 mt-1">Don't move the camera!</p>
              </div>
            </div>
          )}

          {/* Focus quality indicator */}
          {isActive && !countdown && !processing && sharpness && (
            <div className="absolute top-4 left-0 right-0 flex flex-col items-center gap-2 px-4">
              {/* Sharpness status */}
              <div
                className="px-6 py-3 rounded-full text-sm font-bold shadow-lg transition-all duration-300"
                style={{
                  backgroundColor: sharpness.quality === 'excellent' ? '#22c55e'  // green
                    : sharpness.quality === 'good' ? '#84cc16'       // lime
                    : sharpness.quality === 'fair' ? '#eab308'       // yellow
                    : '#ef4444',                                      // red
                  color: 'white'
                }}
              >
                {sharpness.quality === 'excellent' ? '✅ EXCELLENT FOCUS - Capture now!' :
                 sharpness.quality === 'good' ? '✓ Good Focus - Ready to capture' :
                 sharpness.quality === 'fair' ? '⚠️ Fair Focus - Move closer or adjust lighting' :
                 '❌ Poor Focus - Tap on label & hold steady'}
              </div>

              {/* Instructions */}
              <div className="bg-orange-600 bg-opacity-95 text-white px-6 py-3 rounded-lg text-sm font-bold shadow-lg border-2 border-yellow-300">
                🎯 IMPORTANT: Fill the ENTIRE frame with JUST the nutrition label!
              </div>
              <div className="bg-blue-600 bg-opacity-90 text-white px-4 py-2 rounded-full text-xs font-medium shadow-lg">
                💡 Get close (10-15cm) | 📱 TAP on label to focus | Only label, not whole package
              </div>
            </div>
          )}

          {/* Fallback instructions when sharpness not available */}
          {isActive && !countdown && !processing && !sharpness && (
            <div className="absolute top-4 left-0 right-0 flex flex-col items-center gap-2 px-4">
              <div className="bg-orange-600 bg-opacity-95 text-white px-6 py-3 rounded-lg text-sm font-bold shadow-lg border-2 border-yellow-300">
                🎯 IMPORTANT: Fill the ENTIRE frame with JUST the nutrition label!
              </div>
              <div className="bg-green-600 bg-opacity-90 text-white px-4 py-2 rounded-full text-xs font-medium shadow-lg">
                📱 Get close (10-15cm) | TAP on label to focus | Wait 2 seconds before capture
              </div>
            </div>
          )}
        </div>

        {/* Before/After Comparison */}
        {result && (
          <div id="results-section" className="mt-6 border-4 border-green-500 rounded-lg p-4 bg-gray-800">
            <h2 className="text-3xl font-bold text-green-400 mb-4 text-center">✅ Enhancement Complete!</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <div className="bg-gray-900 p-4 rounded-lg">
                <h3 className="text-red-400 font-bold mb-3 text-xl">❌ Before (Blurry)</h3>
                <img
                  src={originalImage}
                  alt="Original"
                  className="w-full rounded-lg border-4 border-red-500"
                  style={{ maxHeight: '600px', objectFit: 'contain' }}
                />
                <p className="text-gray-400 text-sm mt-2">Original size: {result.originalSize.width}x{result.originalSize.height}</p>
              </div>
              <div className="bg-gray-900 p-4 rounded-lg">
                <h3 className="text-green-400 font-bold mb-3 text-xl">✅ After (Enhanced)</h3>
                <img
                  src={result.processedImage}
                  alt="Enhanced"
                  className="w-full rounded-lg border-4 border-green-500"
                  style={{ maxHeight: '600px', objectFit: 'contain' }}
                />
                <p className="text-gray-400 text-sm mt-2">
                  Processed: {result.processedSize.width}x{result.processedSize.height} |
                  Time: {result.processingTime.toFixed(0)}ms
                </p>
              </div>
            </div>
            <div className="flex gap-4 mb-4">
              <button
                onClick={handleSendToBackend}
                disabled={scanning}
                className="flex-1 px-6 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 font-bold text-lg"
              >
                {scanning ? '🔄 Sending to Backend...' : '🚀 Send to Backend for OCR'}
              </button>
            </div>

            {scanProgress && (
              <div className="bg-blue-900 rounded-lg p-4 mb-4">
                <h3 className="text-blue-200 font-bold mb-2">Backend Progress:</h3>
                <p className="text-white">{scanProgress.message}</p>
                <div className="w-full bg-blue-800 rounded-full h-2 mt-2">
                  <div
                    className="bg-blue-400 h-2 rounded-full transition-all"
                    style={{ width: `${scanProgress.progress * 100}%` }}
                  />
                </div>
              </div>
            )}

            {assessment && (
              <div className="bg-green-900 border-4 border-green-400 rounded-lg p-6 mb-4">
                <h3 className="text-green-200 font-bold text-2xl mb-4">✅ Backend Result!</h3>
                <div className="text-white space-y-2">
                  <p><strong>Product:</strong> {assessment.product_name}</p>
                  <p><strong>Score:</strong> {assessment.final_score}/10</p>
                  <p><strong>Verdict:</strong> {assessment.verdict_emoji} {assessment.verdict.toUpperCase()}</p>
                </div>
              </div>
            )}

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-bold mb-2">Processing Steps:</h3>
              <ul className="text-gray-300 text-sm space-y-1">
                {result.steps.map((step, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-green-400 mr-2">✓</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="mt-4 bg-gray-800 rounded-lg p-4">
          <h2 className="text-white font-bold mb-2">Debug Info:</h2>
          <pre className="text-gray-300 text-sm">
            videoRef exists: {videoRef.current ? 'YES' : 'NO'}{'\n'}
            video.srcObject: {videoRef.current?.srcObject ? 'SET' : 'NOT SET'}{'\n'}
            video.videoWidth: {videoRef.current?.videoWidth || 'N/A'}{'\n'}
            video.videoHeight: {videoRef.current?.videoHeight || 'N/A'}{'\n'}
            isActive: {isActive ? 'true' : 'false'}
          </pre>
        </div>
      </div>
    </div>
  );
}
