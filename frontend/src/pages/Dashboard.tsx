import { useEffect, useState } from 'react';
import { getStats } from '../services/api';
import type { StatsResponse } from '../types';
import { StatCard } from '../components/StatCard';
import { ChartPanel } from '../components/ChartPanel';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export const Dashboard = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getStats().then(setStats).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;
  if (error) return <ErrorState message={error} />;
  if (!stats || stats.total_analyses === 0) return <EmptyState message="No analyses yet. Start by analyzing text or uploading a CSV." />;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Analyses" value={stats.total_analyses} color="border-blue-500" />
        <StatCard title="Positive" value={stats.positive_count} color="border-green-500" />
        <StatCard title="Negative" value={stats.negative_count} color="border-red-500" />
        <StatCard title="Neutral" value={stats.neutral_count} color="border-yellow-500" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartPanel positive={stats.positive_count} negative={stats.negative_count} neutral={stats.neutral_count} />
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {stats.recent_activity.map(item => (
              <div key={item.id} className="flex justify-between items-start border-b pb-2">
                <div>
                  <p className="text-sm text-gray-700">{item.text_preview}</p>
                  <p className="text-xs text-gray-400">{new Date(item.created_at).toLocaleString()}</p>
                </div>
                <span className={`text-xs font-bold capitalize px-2 py-1 rounded
                  ${item.sentiment === 'positive' ? 'bg-green-100 text-green-800' : 
                    item.sentiment === 'negative' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                  {item.sentiment}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};