import { useState } from 'react';

interface BeforeAfterPreviewProps {
  originalImage: string;
  processedImage: string;
  processingTime?: number;
  steps?: string[];
  onConfirm: () => void;
  onRetake: () => void;
}

export function BeforeAfterPreview({
  originalImage,
  processedImage,
  processingTime,
  steps,
  onConfirm,
  onRetake
}: BeforeAfterPreviewProps) {
  const [showProcessed, setShowProcessed] = useState(true);
  const [showSteps, setShowSteps] = useState(false);

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <header className="bg-gray-800 shadow-lg p-4">
        <h1 className="text-xl font-bold text-white">Image Enhanced</h1>
        {processingTime && (
          <p className="text-sm text-gray-400">Processed in {processingTime.toFixed(0)}ms</p>
        )}
      </header>

      <main className="flex-1 flex flex-col p-4">
        {/* Toggle buttons */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setShowProcessed(false)}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              !showProcessed
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Original
          </button>
          <button
            onClick={() => setShowProcessed(true)}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              showProcessed
                ? 'bg-green-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Enhanced
          </button>
        </div>

        {/* Image display */}
        <div className="bg-black rounded-lg overflow-hidden mb-4 flex-1 flex items-center justify-center">
          <img
            src={showProcessed ? processedImage : originalImage}
            alt={showProcessed ? 'Enhanced' : 'Original'}
            className="max-w-full max-h-full object-contain"
          />
        </div>

        {/* Processing steps (collapsible) */}
        {steps && steps.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-4 mb-4">
            <button
              onClick={() => setShowSteps(!showSteps)}
              className="w-full flex items-center justify-between text-white font-medium"
            >
              <span>Processing Steps ({steps.length})</span>
              <span>{showSteps ? '▼' : '▶'}</span>
            </button>
            {showSteps && (
              <ul className="mt-3 space-y-1 text-sm text-gray-300 font-mono">
                {steps.map((step, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-green-400 mr-2">✓</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Info banner */}
        <div className="bg-blue-900 border border-blue-700 rounded-lg p-4 mb-4">
          <p className="text-blue-100 text-sm">
            <strong>Enhanced image improves text recognition:</strong>
            <br />
            • Uneven lighting corrected
            <br />
            • Noise removed
            <br />
            • Text edges sharpened
            <br />• Optimal resolution for OCR
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex gap-4">
          <button
            onClick={onRetake}
            className="flex-1 px-6 py-4 bg-gray-700 text-white rounded-lg shadow-lg hover:bg-gray-600 transition-colors font-medium text-lg"
          >
            ↻ Retake
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-6 py-4 bg-green-600 text-white rounded-lg shadow-lg hover:bg-green-700 transition-colors font-medium text-lg"
          >
            Use Enhanced →
          </button>
        </div>
      </main>
    </div>
  );
}
