import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { getStats } from '../services/api';
import type { StatsResponse } from '../types';
import { TrendingUp, TrendingDown, Minus, BarChart2, Brain, Activity } from 'lucide-react';

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
};

const EMOTION_COLORS: Record<string, string> = {
  joy: '#10b981',
  love: '#ec4899',
  anger: '#ef4444',
  sadness: '#3b82f6',
  fear: '#8b5cf6',
  surprise: '#f59e0b',
  disgust: '#84cc16',
  neutral: '#6b7280',
};

const cardVariant = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.08, duration: 0.4 } }),
};

export const Dashboard = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getStats().then(setStats).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-28 rounded-xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="skeleton h-72 rounded-xl" />
          <div className="skeleton h-72 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-8 text-center" style={{ color: 'var(--negative)' }}>
        <p className="font-semibold text-lg">Error loading dashboard</p>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>{error}</p>
      </div>
    );
  }

  if (!stats || stats.total_analyses === 0) {
    return (
      <div className="glass-card p-12 text-center" style={{ color: 'var(--text-muted)' }}>
        <Activity size={48} className="mx-auto mb-4 opacity-30" />
        <p className="text-lg font-medium">No analyses yet</p>
        <p className="text-sm mt-1">Start by analyzing text or uploading a CSV.</p>
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
    { title: 'Total Analyses', value: stats.total_analyses, icon: BarChart2, color: '#6366f1' },
    { title: 'Positive', value: stats.positive_count, icon: TrendingUp, color: SENTIMENT_COLORS.positive },
    { title: 'Negative', value: stats.negative_count, icon: TrendingDown, color: SENTIMENT_COLORS.negative },
    { title: 'Neutral', value: stats.neutral_count, icon: Minus, color: SENTIMENT_COLORS.neutral },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              custom={i}
              initial="hidden"
              animate="visible"
              variants={cardVariant}
              className="glass-card p-5 flex items-center gap-4"
            >
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: `${card.color}18` }}>
                <Icon size={24} style={{ color: card.color }} />
              </div>
              <div>
                <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{card.title}</p>
                <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{card.value}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Pie */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card p-6">
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>
            Sentiment Distribution
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={sentimentData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={4} dataKey="value">
                {sentimentData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12, backdropFilter: 'blur(8px)' }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Emotion Bar */}
        {emotionData.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Brain size={16} style={{ color: 'var(--accent-primary)' }} />
              <h3 className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>
                Emotion Distribution
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={260}>
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

      {/* Recent Activity */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="glass-card p-6">
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>
          Recent Activity
        </h3>
        <div className="space-y-3">
          {stats.recent_activity.map(item => (
            <div key={item.id} className="flex justify-between items-start p-3 rounded-xl transition-colors" style={{ background: 'rgba(99,102,241,0.03)' }}>
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate" style={{ color: 'var(--text-primary)' }}>{item.text_preview}</p>
                <div className="flex items-center gap-3 mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                  {item.emotion && <span>· {item.emotion}</span>}
                  {item.language_name && <span>· {item.language_name}</span>}
                </div>
              </div>
              <span
                className="emotion-badge text-xs ml-3 capitalize flex-shrink-0"
                style={{
                  background: `${SENTIMENT_COLORS[item.sentiment]}18`,
                  color: SENTIMENT_COLORS[item.sentiment],
                }}
              >
                {item.sentiment}
              </span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};