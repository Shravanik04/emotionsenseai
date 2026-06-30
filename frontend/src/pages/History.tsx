import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getHistory, deleteHistoryRecord, downloadReport, restoreHistoryRecord } from '../services/api';
import type { HistoryItem } from '../types';
import { Search, Filter, FileJson, FileSpreadsheet, Printer, AlertTriangle, Eye, Trash2, Download, X, RotateCcw } from 'lucide-react';



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
  const [showDeleted, setShowDeleted] = useState(false);
  const [restoringId, setRestoringId] = useState<number | null>(null);

  // New action states
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' | 'info' } | null>(null);
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchHistory = useCallback(() => {
    setLoading(true);
    getHistory(sentiment, search, emotion, language, sarcasm, showDeleted)
      .then(setItems)
      .finally(() => setLoading(false));
  }, [sentiment, search, emotion, language, sarcasm, showDeleted]);


  useEffect(() => {
    const timer = setTimeout(fetchHistory, 300);
    return () => clearTimeout(timer);
  }, [fetchHistory]);

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Download Handler
  const handleDownload = async (id: number) => {
    setDownloadingId(id);
    try {
      const blob = await downloadReport(id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `emotionsense_report_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setToast({ message: "Report downloaded successfully.", type: 'success' });
    } catch (error) {
      console.error(error);
      setToast({ message: "Failed to download report.", type: 'error' });
    } finally {
      setDownloadingId(null);
    }
  };

  // Delete Handler (supports soft vs permanent)
  const handleDelete = async (id: number) => {
    const confirmMessage = showDeleted 
      ? "Are you sure you want to permanently delete this record? This action cannot be undone."
      : "Are you sure you want to move this record to the Trash?";
    if (!window.confirm(confirmMessage)) return;
    setDeletingId(id);
    try {
      await deleteHistoryRecord(id, showDeleted);
      setItems(prev => prev.filter(item => item.id !== id));
      setToast({ message: showDeleted ? "Record permanently deleted." : "Record moved to Trash.", type: 'success' });
    } catch (error) {
      console.error(error);
      setToast({ message: "Failed to delete record.", type: 'error' });
    } finally {
      setDeletingId(null);
    }
  };

  // Restore Handler
  const handleRestore = async (id: number) => {
    setRestoringId(id);
    try {
      await restoreHistoryRecord(id);
      setItems(prev => prev.filter(item => item.id !== id));
      setToast({ message: "Record restored successfully.", type: 'success' });
    } catch (error) {
      console.error(error);
      setToast({ message: "Failed to restore record.", type: 'error' });
    } finally {
      setRestoringId(null);
    }
  };


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
          <button
            onClick={() => setShowDeleted(!showDeleted)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              showDeleted 
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 hover:bg-rose-500/30' 
                : 'bg-white/10 text-slate-300 border-white/10 hover:bg-white/20'
            }`}
            title="Toggle Trash Manager"
          >
            <Trash2 size={14} /> {showDeleted ? "Exit Trash" : "View Trash"}
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
                {['Text Preview', 'Sentiment', 'Confidence', 'Dominant Emotion', 'Language', 'Sarcasm', 'Source', 'Date', 'Actions'].map(h => (
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
                    <td className="p-4 flex items-center gap-1">
                      <button
                        onClick={() => setSelectedItem(item)}
                        className="p-1.5 rounded bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 transition-colors"
                        title="View Details"
                      >
                        <Eye size={13} />
                      </button>
                      {showDeleted && (
                        <button
                          onClick={() => handleRestore(item.id)}
                          disabled={restoringId === item.id}
                          className="p-1.5 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 disabled:opacity-50 transition-colors inline-flex items-center justify-center min-w-[26px]"
                          title="Restore Record"
                        >
                          {restoringId === item.id ? (
                            <div className="w-3 h-3 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <RotateCcw size={13} />
                          )}
                        </button>
                      )}
                      <button
                        onClick={() => handleDownload(item.id)}
                        disabled={downloadingId === item.id}
                        className="p-1.5 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 disabled:opacity-50 transition-colors inline-flex items-center justify-center min-w-[26px]"
                        title="Download PDF Report"
                      >
                        {downloadingId === item.id ? (
                          <div className="w-3 h-3 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Download size={13} />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={deletingId === item.id}
                        className="p-1.5 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 disabled:opacity-50 transition-colors inline-flex items-center justify-center min-w-[26px]"
                        title={showDeleted ? "Delete Permanently" : "Move to Trash"}
                      >
                        {deletingId === item.id ? (
                          <div className="w-3 h-3 border-2 border-rose-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Trash2 size={13} />
                        )}
                      </button>
                    </td>

                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedItem && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 pointer-events-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-2xl w-full border border-white/10 shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between p-5 border-b border-white/10">
                <h3 className="text-lg font-bold text-white">Analysis Log Detail</h3>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-6 space-y-5 max-h-[65vh] overflow-y-auto">
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Analyzed Text</h4>
                  <div className="bg-white/5 p-4 rounded-xl text-sm leading-relaxed text-gray-200 border border-white/5 whitespace-pre-wrap">
                    {selectedItem.text_preview}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Sentiment</h4>
                    <span
                      className="emotion-badge text-xs capitalize font-bold px-2.5 py-1 inline-block"
                      style={{
                        background: `${SENTIMENT_COLORS[selectedItem.sentiment]}18`,
                        color: SENTIMENT_COLORS[selectedItem.sentiment],
                      }}
                    >
                      {selectedItem.sentiment} ({(selectedItem.confidence * 100).toFixed(1)}%)
                    </span>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Dominant Emotion</h4>
                    <span className="text-sm font-semibold text-gray-200 flex items-center gap-1.5">
                      <span>{EMOJI_MAP_JS[selectedItem.emotion || ''] || '😐'}</span>
                      <span className="capitalize">{selectedItem.emotion || 'None'}</span>
                    </span>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Detected Language</h4>
                    <span className="text-sm text-gray-200 font-medium">{selectedItem.language_name || '—'}</span>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Sarcasm Analytics</h4>
                    {selectedItem.sarcasm_detected ? (
                      <div className="space-y-1">
                        <span className="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded text-xs font-bold inline-flex items-center gap-1">
                          <AlertTriangle size={12} /> Sarcastic
                        </span>
                        {selectedItem.sarcasm_reason && (
                          <p className="text-xs text-amber-300/80 italic leading-snug">{selectedItem.sarcasm_reason}</p>
                        )}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">No sarcasm detected</span>
                    )}
                  </div>
                </div>

                <div className="flex justify-between items-center text-xs text-gray-500 pt-4 border-t border-white/5">
                  <span>Source: <span className="capitalize text-gray-400">{selectedItem.source_type}</span></span>
                  <span>Analyzed: {new Date(selectedItem.created_at).toLocaleString()}</span>
                </div>
              </div>

              <div className="flex justify-end gap-3 p-5 border-t border-white/10 bg-white/5">
                <button
                  onClick={() => setSelectedItem(null)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold hover:bg-white/10 text-gray-300 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    handleDownload(selectedItem.id);
                    setSelectedItem(null);
                  }}
                  disabled={downloadingId === selectedItem.id}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-bold bg-emerald-500 hover:bg-emerald-600 text-white disabled:opacity-50 transition-colors"
                >
                  <Download size={15} /> Download PDF
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="fixed bottom-6 right-6 z-50 pointer-events-auto"
          >
            <div className={`flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg backdrop-blur-md border ${
              toast.type === 'error'
                ? 'bg-red-500/10 border-red-500/30 text-red-200'
                : toast.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
                : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-200'
            }`}>
              <AlertTriangle size={18} className={toast.type === 'error' ? 'text-red-400' : toast.type === 'success' ? 'text-emerald-400' : 'text-indigo-400'} />
              <span className="text-sm font-medium">{toast.message}</span>
              <button
                onClick={() => setToast(null)}
                className="ml-2 text-xs opacity-70 hover:opacity-100 p-0.5 rounded-full hover:bg-white/10 transition-colors"
              >
                &times;
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};