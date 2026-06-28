import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
} from 'recharts';
import { Upload, FileText, Download, AlertCircle } from 'lucide-react';
import { analyzeBatch, getExportUrl } from '../services/api';
import type { BatchSummary } from '../types';

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
};

const EMOTION_COLORS: Record<string, string> = {
  joy: '#10b981', love: '#ec4899', anger: '#ef4444', sadness: '#3b82f6',
  fear: '#8b5cf6', surprise: '#f59e0b', disgust: '#84cc16', neutral: '#6b7280',
};

const ACCEPTED = '.csv,.txt,.xlsx,.xls';

export const UploadCSV = () => {
  const [summary, setSummary] = useState<BatchSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setLoading(true);
    setError('');
    setSummary(null);
    setFileName(file.name);
    setProgress(0);

    // Simulate progress while waiting
    const interval = setInterval(() => {
      setProgress(p => Math.min(p + Math.random() * 15, 90));
    }, 300);

    try {
      const res = await analyzeBatch(file);
      setSummary(res);
      setProgress(100);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process file');
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Batch Analysis</h1>
      <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
        Upload CSV, TXT, or Excel files for bulk sentiment & emotion analysis
      </p>

      {/* Upload Zone */}
      <div
        className="glass-card p-10 text-center cursor-pointer transition-all"
        style={{ border: '2px dashed var(--border-glass)' }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" accept={ACCEPTED} className="hidden" onChange={handleFileSelect} />
        <Upload size={40} className="mx-auto mb-4" style={{ color: 'var(--accent-primary)', opacity: 0.6 }} />
        <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
          Drop a file here or <span style={{ color: 'var(--accent-primary)' }}>browse</span>
        </p>
        <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
          Supports CSV, TXT, Excel (.xlsx, .xls) · Max 500 rows
        </p>
      </div>

      {/* Loading progress */}
      <AnimatePresence>
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="glass-card p-6">
            <div className="flex items-center gap-3 mb-3">
              <FileText size={18} style={{ color: 'var(--accent-primary)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                Processing {fileName}…
              </span>
            </div>
            <div className="confidence-bar-bg">
              <motion.div
                className="confidence-bar-fill"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>{Math.round(progress)}%</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      {error && (
        <div className="glass-card p-4 flex items-center gap-3" style={{ borderColor: 'var(--negative)' }}>
          <AlertCircle size={18} style={{ color: 'var(--negative)' }} />
          <span className="text-sm" style={{ color: 'var(--negative)' }}>{error}</span>
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {summary && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Batch Results</h2>

            {/* Stat cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Total Rows', value: summary.total_rows, color: '#6366f1' },
                { label: 'Processed', value: summary.processed_rows, color: '#10b981' },
                { label: 'Skipped', value: summary.skipped_rows, color: '#ef4444' },
                { label: 'Avg Confidence', value: `${(summary.average_confidence * 100).toFixed(1)}%`, color: '#8b5cf6' },
              ].map(card => (
                <div key={card.label} className="glass-card p-4 text-center">
                  <p className="text-2xl font-bold" style={{ color: card.color }}>{card.value}</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{card.label}</p>
                </div>
              ))}
            </div>

            {/* Sentiment breakdown */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: 'Positive', value: summary.positive_count, color: SENTIMENT_COLORS.positive },
                { label: 'Negative', value: summary.negative_count, color: SENTIMENT_COLORS.negative },
                { label: 'Neutral', value: summary.neutral_count, color: SENTIMENT_COLORS.neutral },
              ].map(card => (
                <div key={card.label} className="glass-card p-4 text-center">
                  <p className="text-2xl font-bold" style={{ color: card.color }}>{card.value}</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{card.label}</p>
                </div>
              ))}
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Sentiment Pie */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>Sentiment</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Positive', value: summary.positive_count },
                        { name: 'Negative', value: summary.negative_count },
                        { name: 'Neutral', value: summary.neutral_count },
                      ]}
                      cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={4} dataKey="value"
                    >
                      <Cell fill={SENTIMENT_COLORS.positive} />
                      <Cell fill={SENTIMENT_COLORS.negative} />
                      <Cell fill={SENTIMENT_COLORS.neutral} />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Emotion Pie */}
              {Object.keys(summary.emotion_counts).length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>Emotions</h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={Object.entries(summary.emotion_counts).map(([k, v]) => ({ name: k, value: v }))}
                        cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3} dataKey="value"
                      >
                        {Object.keys(summary.emotion_counts).map((k, i) => (
                          <Cell key={i} fill={EMOTION_COLORS[k] || '#6366f1'} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Export */}
            <div className="flex justify-end">
              <a
                href={getExportUrl()}
                download
                className="btn-accent flex items-center gap-2 text-sm"
              >
                <Download size={16} /> Download Full Export
              </a>
            </div>

            {/* Errors */}
            {summary.errors.length > 0 && (
              <div className="glass-card p-4" style={{ borderColor: 'rgba(239,68,68,0.3)' }}>
                <p className="font-semibold text-sm mb-2" style={{ color: 'var(--negative)' }}>
                  Errors encountered ({summary.errors.length})
                </p>
                <ul className="text-xs space-y-1" style={{ color: 'var(--text-muted)' }}>
                  {summary.errors.map((e, i) => <li key={i}>• {e}</li>)}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
