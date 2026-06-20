import { useEffect, useState } from 'react';
import { getStats } from '../services/api';
import type { StatsResponse } from '../types';
import { ChartPanel } from '../components/ChartPanel';
import { StatCard } from '../components/StatCard';
import { Loader } from '../components/Loader';
import { EmptyState } from '../components/EmptyState';

export const Stats = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;
  if (!stats || stats.total_analyses === 0) return <EmptyState message="No stats available yet." />;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Stats & Insights</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total" value={stats.total_analyses} color="border-blue-500" />
        <StatCard title="Positive" value={stats.positive_count} color="border-green-500" />
        <StatCard title="Negative" value={stats.negative_count} color="border-red-500" />
        <StatCard title="Neutral" value={stats.neutral_count} color="border-yellow-500" />
      </div>
      <ChartPanel positive={stats.positive_count} negative={stats.negative_count} neutral={stats.neutral_count} />
    </div>
  );
};
