import { useState } from 'react';
import { analyzeBatch, getExportUrl } from '../services/api';
import type { BatchSummary } from '../types';
import { UploadZone } from '../components/UploadZone';
import { StatCard } from '../components/StatCard';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';

export const UploadCSV = () => {
  const [summary, setSummary] = useState<BatchSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleUpload = async (file: File) => {
    setLoading(true);
    setError('');
    try {
      const res = await analyzeBatch(file);
      setSummary(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process CSV');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Upload CSV</h1>
      <UploadZone onFileUpload={handleUpload} />
      
      {loading && <div className="mt-6"><Loader /></div>}
      {error && <div className="mt-6"><ErrorState message={error} /></div>}
      
      {summary && (
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">Batch Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard title="Total Rows" value={summary.total_rows} color="border-blue-500" />
            <StatCard title="Processed" value={summary.processed_rows} color="border-green-500" />
            <StatCard title="Skipped" value={summary.skipped_rows} color="border-red-500" />
            <StatCard title="Avg Confidence" value={`${(summary.average_confidence * 100).toFixed(1)}%`} color="border-purple-500" />
          </div>
          
          <div className="grid grid-cols-3 gap-4 mb-6">
            <StatCard title="Positive" value={summary.positive_count} color="border-green-500" />
            <StatCard title="Negative" value={summary.negative_count} color="border-red-500" />
            <StatCard title="Neutral" value={summary.neutral_count} color="border-yellow-500" />
          </div>

          <div className="flex justify-end mb-6">
            <a href={getExportUrl()} download className="bg-gray-800 text-white px-4 py-2 rounded-lg hover:bg-gray-900">
              Download Full Export
            </a>
          </div>

          {summary.errors.length > 0 && (
            <div className="bg-red-50 p-4 rounded-lg text-red-700 text-sm">
              <strong>Errors encountered:</strong>
              <ul className="list-disc ml-6 mt-2">
                {summary.errors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
