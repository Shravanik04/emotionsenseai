import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { getStats } from '../services/api';
import type { StatsResponse } from '../types';
import { BarChart2, Brain, Activity } from 'lucide-react';

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
};

const EMOTION_COLORS: Record<string, string> = {
  joy: '#10b981', love: '#ec4899', anger: '#ef4444', sadness: '#3b82f6',
  fear: '#8b5cf6', surprise: '#f59e0b', disgust: '#84cc16', neutral: '#6b7280',
};

export const Stats = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
        </div>
        <div className="skeleton h-72 rounded-xl" />
      </div>
    );
  }

  if (!stats || stats.total_analyses === 0) {
    return (
      <div className="glass-card p-12 text-center" style={{ color: 'var(--text-muted)' }}>
        <Activity size={48} className="mx-auto mb-4 opacity-30" />
        <p className="text-lg font-medium">No stats available yet.</p>
      </div>
    );
  }

  const sentimentData = [
    { name: 'Positive', value: stats.positive_count, color: SENTIMENT_COLORS.positive },
    { name: 'Negative', value: stats.negative_count, color: SENTIMENT_COLORS.negative },
    { name: 'Neutral', value: stats.neutral_count, color: SENTIMENT_COLORS.neutral },
  ];

  const emotionData = Object.entries(stats.emotion_counts).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value,
    color: EMOTION_COLORS[key] || '#6366f1',
  }));

  const statCards = [
    { label: 'Total', value: stats.total_analyses, color: '#6366f1', icon: BarChart2 },
    { label: 'Positive', value: stats.positive_count, color: SENTIMENT_COLORS.positive },
    { label: 'Negative', value: stats.negative_count, color: SENTIMENT_COLORS.negative },
    { label: 'Neutral', value: stats.neutral_count, color: SENTIMENT_COLORS.neutral },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Stats & Insights</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass-card p-5 text-center"
          >
            <p className="text-3xl font-bold" style={{ color: card.color }}>{card.value}</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{card.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card p-6">
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>
            Sentiment Distribution
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={sentimentData} cx="50%" cy="50%" innerRadius={55} outerRadius={95} paddingAngle={4} dataKey="value">
                {sentimentData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {emotionData.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Brain size={16} style={{ color: 'var(--accent-primary)' }} />
              <h3 className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>
                Emotion Distribution
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={emotionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {emotionData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}
      </div>
    </div>
  );
};
