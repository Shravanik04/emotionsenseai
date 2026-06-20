import { useState } from 'react';
import { analyzeText } from '../services/api';
import type { SentimentResponse } from '../types';
import { ResultCard } from '../components/ResultCard';
import { Loader } from '../components/Loader';

export const AnalyzeText = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState<SentimentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await analyzeText(text);
      setResult(res);
      setText('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze text');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Analyze Text</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm">
          <label className="block text-sm font-medium text-gray-700 mb-2">Enter Review/Comment</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            className="w-full border rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="Type or paste your text here..."
            required
          />
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="mt-4 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Analyze Sentiment'}
          </button>
          {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        </form>
        <div>
          {loading && !result ? <Loader /> : result ? <ResultCard result={result} /> : (
            <div className="bg-gray-50 border-dashed border rounded-xl h-full flex items-center justify-center text-gray-400 p-6">
              Results will appear here
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
