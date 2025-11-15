import type { DetailedAssessment } from '../types';

interface Props {
  assessment: DetailedAssessment;
}

export function VerdictDisplay({ assessment }: Props) {
  const verdictColors = {
    excellent: 'bg-green-100 text-green-800 border-green-200',
    good: 'bg-green-50 text-green-700 border-green-200',
    moderate: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    caution: 'bg-orange-100 text-orange-800 border-orange-200',
    avoid: 'bg-red-100 text-red-800 border-red-200',
  };

  const verdictColor = verdictColors[assessment.verdict] || verdictColors.moderate;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm p-4">
        <h1 className="text-xl font-bold text-gray-900">Bytelense - Food Scanner</h1>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-6 pb-16">
        {/* Product Name */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {assessment.product_name}
          </h1>
          {assessment.brand && (
            <p className="text-gray-600 mt-1">{assessment.brand}</p>
          )}
        </div>

        {/* Verdict Badge */}
        <div className={`inline-flex items-center px-6 py-3 rounded-full ${verdictColor} border`}>
          <span className="text-4xl mr-2">{assessment.verdict_emoji}</span>
          <span className="text-xl font-bold uppercase">{assessment.verdict}</span>
        </div>

        {/* Score */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-2">Health Score</h2>
          <div className="flex items-center gap-4">
            <span className="text-4xl font-bold">{assessment.final_score.toFixed(1)}</span>
            <span className="text-gray-500">/ 10</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div
              className={`h-2 rounded-full ${
                assessment.final_score >= 7 ? 'bg-green-500' :
                assessment.final_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${(assessment.final_score / 10) * 100}%` }}
            />
          </div>
        </div>

        {/* Context Adjustment Explanation */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Scoring</h3>
          <p className="text-gray-700">{assessment.context_adjustment}</p>
          <p className="text-gray-600 mt-2">Calculation: {assessment.final_calculation}</p>
        </div>

        {/* Allergen Alerts */}
        {assessment.allergen_alerts && assessment.allergen_alerts.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-800 mb-3">🚨 Allergen Alerts</h3>
            <ul className="space-y-2">
              {assessment.allergen_alerts.map((alert, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-red-500 mr-2">•</span>
                  <span className="text-red-700">{alert}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Moderation Message */}
        {assessment.moderation_message && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">💡 Moderation Message</h3>
            <p className="text-yellow-700">{assessment.moderation_message}</p>
          </div>
        )}

        {/* Timing Recommendation */}
        {assessment.timing_recommendation && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">⏱️ Timing Recommendation</h3>
            <p className="text-blue-700">{assessment.timing_recommendation}</p>
          </div>
        )}

        {/* Highlights and Warnings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Highlights */}
          {assessment.highlights && assessment.highlights.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-800 mb-3">✅ Highlights</h3>
              <ul className="space-y-2">
                {assessment.highlights.map((highlight, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-green-500 mr-2">•</span>
                    <span className="text-green-700">{highlight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {assessment.warnings && assessment.warnings.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-orange-800 mb-3">⚠️ Warnings</h3>
              <ul className="space-y-2">
                {assessment.warnings.map((warning, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-orange-500 mr-2">•</span>
                    <span className="text-orange-700">{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Nutrition Snapshot */}
        {assessment.nutrition_snapshot && Object.keys(assessment.nutrition_snapshot).length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4"> Nutrition Information</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {Object.entries(assessment.nutrition_snapshot).map(([key, value]) => (
                <div key={key} className="border border-gray-200 rounded-lg p-3 text-center">
                  <p className="text-sm text-gray-600 capitalize">{key.replace(/_/g, ' ')}</p>
                  <p className="font-semibold">{value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reasoning Steps */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-3">AI Reasoning</h3>
          <ol className="list-decimal list-inside space-y-2">
            {assessment.reasoning_steps.map((step, index) => (
              <li key={index} className="text-gray-700">{step}</li>
            ))}
          </ol>
        </div>

        {/* Alternative Products */}
        {assessment.alternative_products && assessment.alternative_products.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-3"> 🔄 Healthier Alternatives</h3>
            <ul className="space-y-2">
              {assessment.alternative_products.map((product, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  <span className="text-gray-700">{product}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Citations */}
        {assessment.sources && assessment.sources.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-3">📚 Sources & Citations</h3>
            <div className="space-y-4">
              {assessment.sources.map((source) => (
                <div key={source.citation_number} className="border-l-4 border-blue-500 pl-4 py-1">
                  <p className="font-medium">
                    [{source.citation_number}] {source.title}
                  </p>
                  {source.url && (
                    <a 
                      href={source.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm block mt-1"
                    >
                      {source.url}
                    </a>
                  )}
                  <p className="text-sm text-gray-600 mt-1">
                    Authority: {(source.authority_score * 100).toFixed(0)}%
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="bg-white border-t py-4 text-center text-gray-600">
        <p>Powered by Bytelense AI Food Scanner</p>
      </footer>
    </div>
  );
}