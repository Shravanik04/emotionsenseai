import type { SentimentResponse } from '../types';

export const ResultCard = ({ result }: { result: SentimentResponse }) => (
  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
    <h3 className="text-lg font-semibold text-gray-800 mb-4">Analysis Result</h3>
    <div className="space-y-3">
      <div className="flex justify-between">
        <span className="text-gray-500">Sentiment:</span>
        <span className={`font-bold capitalize ${
          result.sentiment === 'positive' ? 'text-green-600' : 
          result.sentiment === 'negative' ? 'text-red-600' : 'text-yellow-600'
        }`}>
          {result.sentiment}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-500">Confidence:</span>
        <span className="font-bold text-gray-800">{(result.confidence * 100).toFixed(2)}%</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-500">Processed At:</span>
        <span className="font-medium text-gray-800">{new Date(result.processed_timestamp).toLocaleString()}</span>
      </div>
    </div>
  </div>
);
