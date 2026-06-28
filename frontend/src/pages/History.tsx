import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getHistory } from '../services/api';
import type { HistoryItem } from '../types';
import { Search, Filter, FileJson, FileSpreadsheet, Printer, AlertTriangle } from 'lucide-react';

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
};

const EMOJI_MAP_JS: Record<string, string> = {
  joy: "😊", happiness: "😀", excitement: "🎉", love: "❤️", gratitude: "🙏", pride: "🦁",
  hope: "🌅", optimism: "☀️", relief: "😌", confidence: "😎", admiration: "👏",
  inspiration: "💡", curiosity: "🤔", trust: "🤝", satisfaction: "👍",
  sadness: "😔", anger: "😤", fear: "😨", anxiety: "😟", stress: "😫", frustration: "😒",
  disappointment: "😞", loneliness: "🏚️", confusion: "🤷", disgust: "🤢", jealousy: "💚",
  regret: "🤦", guilt: "🥺", embarrassment: "😳",
  calm: "🧘", neutral: "😐", thoughtful: "💭", analytical: "📊",
  surprise: "😲", nostalgia: "⏳", determination: "✊", sympathy: "💖", compassion: "🤲",
  awe: "🌌", anticipation: "⏳", skepticism: "🤨", overwhelmed: "🤯", shock: "💥"
};

export const History = () => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sentiment, setSentiment] = useState('all');
  const [emotion, setEmotion] = useState('all');
  const [language, setLanguage] = useState('all');
  const [sarcasm, setSarcasm] = useState('all');
  const [search, setSearch] = useState('');

  const fetchHistory = useCallback(() => {
    setLoading(true);
    getHistory(sentiment, search, emotion, language, sarcasm)
      .then(setItems)
      .finally(() => setLoading(false));
  }, [sentiment, search, emotion, language, sarcasm]);

  useEffect(() => {
    const timer = setTimeout(fetchHistory, 300);
    return () => clearTimeout(timer);
  }, [fetchHistory]);

  /* ---------- CSV Export ---------- */
  const exportCSV = () => {
    if (items.length === 0) return;
    const headers = ['ID', 'Text Preview', 'Sentiment', 'Confidence', 'Emotion', 'Language', 'Sarcasm Detected', 'Sarcasm Reason', 'Date'];
    const rows = items.map(item => [
      item.id,
      `"${item.text_preview.replace(/"/g, '""')}"`,
      item.sentiment,
      (item.confidence * 100).toFixed(1) + '%',
      item.emotion || '—',
      item.language_name || '—',
      item.sarcasm_detected ? 'Yes' : 'No',
      `"${(item.sarcasm_reason || '').replace(/"/g, '""')}"`,
      new Date(item.created_at).toLocaleString()
    ]);
    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", encodeURI(csvContent));
    downloadAnchor.setAttribute("download", `sentiment_history_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  /* ---------- JSON Export ---------- */
  const exportJSON = () => {
    if (items.length === 0) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(items, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `sentiment_history_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  /* ---------- PDF Print Export ---------- */
  const exportPDF = () => {
    window.print();
  };

  return (
    <div className="space-y-6 printable-area">
      <div className="flex flex-wrap items-center justify-between gap-4 non-printable">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>History Logs</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Review past sentiment and emotion analysis runs
          </p>
        </div>
        
        {/* Export buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={exportCSV}
            disabled={items.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/20 text-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed border border-emerald-500/20"
            title="Export CSV"
          >
            <FileSpreadsheet size={14} /> Export CSV
          </button>
          <button
            onClick={exportJSON}
            disabled={items.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/20 text-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed border border-indigo-500/20"
            title="Export JSON"
          >
            <FileJson size={14} /> Export JSON
          </button>
          <button
            onClick={exportPDF}
            disabled={items.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/20 text-sky-400 disabled:opacity-50 disabled:cursor-not-allowed border border-sky-500/20"
            title="Print / Save PDF"
          >
            <Printer size={14} /> Print PDF
          </button>
        </div>
      </div>

      {/* Filters (Hidden during print) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 flex-wrap non-printable">
        {/* Search */}
        <div className="relative md:col-span-1">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search text…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-glass w-full pl-10"
          />
        </div>

        {/* Sentiment */}
        <div className="relative">
          <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <select
            value={sentiment}
            onChange={(e) => setSentiment(e.target.value)}
            className="input-glass pl-8 pr-4 cursor-pointer text-xs w-full"
          >
            <option value="all">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="negative">Negative</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>

        {/* Emotion */}
        <div className="relative">
          <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <select
            value={emotion}
            onChange={(e) => setEmotion(e.target.value)}
            className="input-glass pl-8 pr-4 cursor-pointer text-xs w-full"
          >
            <option value="all">All Emotions</option>
            <option value="joy">Joy 😊</option>
            <option value="love">Love ❤️</option>
            <option value="sadness">Sadness 😔</option>
            <option value="anger">Anger 😤</option>
            <option value="fear">Fear 😨</option>
            <option value="surprise">Surprise 😲</option>
            <option value="disgust">Disgust 🤢</option>
            <option value="frustration">Frustration 😒</option>
            <option value="disappointment">Disappointment 😞</option>
            <option value="hope">Hope 🌅</option>
            <option value="confidence">Confidence 😎</option>
          </select>
        </div>

        {/* Language */}
        <div className="relative">
          <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="input-glass pl-8 pr-4 cursor-pointer text-xs w-full"
          >
            <option value="all">All Languages</option>
            <option value="English">English</option>
            <option value="Hindi">Hindi</option>
            <option value="Kannada">Kannada</option>
            <option value="Spanish">Spanish</option>
            <option value="French">French</option>
            <option value="German">German</option>
          </select>
        </div>

        {/* Sarcasm */}
        <div className="relative">
          <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <select
            value={sarcasm}
            onChange={(e) => setSarcasm(e.target.value)}
            className="input-glass pl-8 pr-4 cursor-pointer text-xs w-full"
          >
            <option value="all">All Sarcasm</option>
            <option value="true">Sarcasm Only ⚠️</option>
            <option value="false">No Sarcasm Only</option>
          </select>
        </div>
      </div>

      {/* Table / List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
        </div>
      ) : items.length === 0 ? (
        <div className="glass-card p-12 text-center" style={{ color: 'var(--text-muted)' }}>
          No records found matching current filter query.
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glass)' }}>
                {['Text Preview', 'Sentiment', 'Confidence', 'Dominant Emotion', 'Language', 'Sarcasm', 'Source', 'Date'].map(h => (
                  <th key={h} className="p-4 text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {items.map((item, i) => (
                  <motion.tr
                    key={item.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    className="transition-colors hover:bg-white/5"
                    style={{ borderBottom: '1px solid var(--border-glass)' }}
                  >
                    <td className="p-4 text-sm max-w-xs truncate font-medium" style={{ color: 'var(--text-primary)' }} title={item.text_preview}>
                      {item.text_preview}
                    </td>
                    <td className="p-4">
                      <span
                        className="emotion-badge text-xs capitalize font-bold"
                        style={{
                          background: `${SENTIMENT_COLORS[item.sentiment]}18`,
                          color: SENTIMENT_COLORS[item.sentiment],
                        }}
                      >
                        {item.sentiment}
                      </span>
                    </td>
                    <td className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>
                      {(item.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="p-4 text-sm capitalize" style={{ color: 'var(--text-secondary)' }}>
                      {item.emotion ? (
                        <span className="flex items-center gap-1">
                          <span>{EMOJI_MAP_JS[item.emotion] || '😐'}</span>
                          <span>{item.emotion}</span>
                        </span>
                      ) : '—'}
                    </td>
                    <td className="p-4 text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>
                      {item.language_name || '—'}
                    </td>
                    <td className="p-4 text-sm">
                      {item.sarcasm_detected ? (
                        <span className="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1">
                          <AlertTriangle size={10} /> Sarcastic
                        </span>
                      ) : (
                        <span className="text-gray-500 text-[10px]">None</span>
                      )}
                    </td>
                    <td className="p-4 text-sm capitalize" style={{ color: 'var(--text-muted)' }}>
                      {item.source_type}
                    </td>
                    <td className="p-4 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};