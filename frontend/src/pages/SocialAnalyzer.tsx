import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Youtube, Instagram, Twitter, Linkedin, Facebook, FileText, 
  Send, RefreshCw, Trash2, Search, Smile, AlertTriangle, 
  Brain, Sparkles, AlertCircle, X, Award, Download
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area
} from 'recharts';
import { 
  analyzeSocialSingle, 
  analyzeSocialBatch, 
  getSocialHistory, 
  deleteSocialRecord,
  downloadReport
} from '../services/api';

import type { 
  SocialAnalyzeResponse, 
  SocialBatchResponse
} from '../types';


// Constants
const PLATFORMS = [
  { id: 'youtube', name: 'YouTube', icon: Youtube, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
  { id: 'instagram_comment', name: 'Instagram Comments', icon: Instagram, color: '#ec4899', bg: 'rgba(236, 72, 153, 0.1)' },
  { id: 'instagram_caption', name: 'Instagram Captions', icon: Instagram, color: '#f43f5e', bg: 'rgba(244, 63, 94, 0.1)' },
  { id: 'twitter', name: 'X / Twitter', icon: Twitter, color: '#0f172a', bg: 'rgba(15, 23, 42, 0.1)' },
  { id: 'reddit', name: 'Reddit', icon: Smile, color: '#f97316', bg: 'rgba(249, 115, 22, 0.1)' },
  { id: 'linkedin', name: 'LinkedIn', icon: Linkedin, color: '#0077b5', bg: 'rgba(0, 119, 181, 0.1)' },
  { id: 'facebook', name: 'Facebook', icon: Facebook, color: '#1877f2', bg: 'rgba(24, 119, 242, 0.1)' },
  { id: 'generic', name: 'Generic Text', icon: FileText, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.1)' },
];

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
  mixed: '#8b5cf6',
};


const EMOTION_COLORS: Record<string, string> = {
  joy: '#10b981', love: '#ec4899', anger: '#ef4444', sadness: '#3b82f6',
  fear: '#8b5cf6', surprise: '#f59e0b', disgust: '#84cc16', neutral: '#6b7280',
};

const EMOJI_MAP: Record<string, string> = {
  joy: '😊', love: '❤️', anger: '😤', sadness: '😔', fear: '😨', surprise: '😲', disgust: '🤢', neutral: '😐'
};

export const SocialAnalyzer = () => {
  // Input states
  const [selectedPlatform, setSelectedPlatform] = useState('youtube');
  const [inputMode, setInputMode] = useState<'single' | 'batch'>('batch');
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Results states
  const [batchResult, setBatchResult] = useState<SocialBatchResponse | null>(null);
  const [singleResult, setSingleResult] = useState<SocialAnalyzeResponse | null>(null);
  
  // History Drawer state
  const [showHistory, setShowHistory] = useState(false);
  const [historyItems, setHistoryItems] = useState<SocialAnalyzeResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [filterSentiment, setFilterSentiment] = useState('all');
  const [filterEmotion, setFilterEmotion] = useState('all');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');

  // Pagination for Individual Table
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Report download states
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' | 'info' } | null>(null);

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleDownloadReport = async (id: number) => {
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


  // Load history list when side drawer is opened
  const loadHistory = async () => {
    try {
      const filters: any = {};
      if (filterPlatform !== 'all') filters.platform = filterPlatform;
      if (filterSentiment !== 'all') filters.sentiment = filterSentiment;
      if (filterEmotion !== 'all') filters.emotion = filterEmotion;
      if (searchQuery.trim()) filters.search = searchQuery;
      if (filterStartDate) filters.start_date = filterStartDate;
      if (filterEndDate) filters.end_date = filterEndDate;

      const data = await getSocialHistory(filters);
      setHistoryItems(data);
    } catch (err: any) {
      console.error("Failed to load social history:", err);
    }
  };

  useEffect(() => {
    if (showHistory) {
      loadHistory();
    }
  }, [showHistory, filterPlatform, filterSentiment, filterEmotion, searchQuery, filterStartDate, filterEndDate]);

  // Handle analyze action
  const handleAnalyze = async () => {
    if (!text.trim()) {
      setErrorMessage("Please enter some text or comments to analyze.");
      return;
    }
    setErrorMessage('');
    setIsLoading(true);
    setBatchResult(null);
    setSingleResult(null);

    try {
      if (inputMode === 'single') {
        const res = await analyzeSocialSingle(selectedPlatform, text);
        setSingleResult(res);
      } else {
        const res = await analyzeSocialBatch(selectedPlatform, text);
        setBatchResult(res);
        setCurrentPage(1);
      }
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail || "Network error or analysis timeout occurred.";
      setErrorMessage(detail);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle clear action
  const handleClear = () => {
    setText('');
    setErrorMessage('');
    setBatchResult(null);
    setSingleResult(null);
  };

  // Handle delete history record
  const handleDeleteRecord = async (id: number) => {
    if (window.confirm("Are you sure you want to delete this analysis record?")) {
      try {
        await deleteSocialRecord(id);
        
        // Remove from current batch list if present
        if (batchResult) {
          const updatedResults = batchResult.results.filter(r => r.id !== id);
          if (updatedResults.length === 0) {
            setBatchResult(null);
          } else {
            // Recompute counts and percentages
            const sentiment_distribution = { positive: 0, negative: 0, neutral: 0 };
            const emotion_distribution: Record<string, number> = {};
            const language_distribution: Record<string, number> = {};
            const sarcasm_distribution = { sarcastic: 0, "not sarcastic": 0 };
            let total_confidence = 0;
            let sarcastic_count = 0;

            updatedResults.forEach(r => {
              if (r.sentiment) sentiment_distribution[r.sentiment]++;
              if (r.emotion) emotion_distribution[r.emotion] = (emotion_distribution[r.emotion] || 0) + 1;
              if (r.detected_language) language_distribution[r.detected_language] = (language_distribution[r.detected_language] || 0) + 1;
              if (r.sarcasm_detected) {
                sarcastic_count++;
                sarcasm_distribution["sarcastic"]++;
              } else {
                sarcasm_distribution["not sarcastic"]++;
              }
              total_confidence += r.confidence || 0;
            });

            const total = updatedResults.length;
            const average_confidence = total_confidence / total;
            const sarcasm_rate = (sarcastic_count / total) * 100;

            setBatchResult({
              ...batchResult,
              total_processed: total,
              average_confidence,
              sarcasm_rate,
              sentiment_distribution,
              emotion_distribution,
              language_distribution,
              sarcasm_distribution,
              results: updatedResults,
            });
          }
        }

        // Refresh history list
        if (showHistory) {
          loadHistory();
        }
      } catch (err: any) {
        alert("Failed to delete record: " + (err.response?.data?.detail || err.message));
      }
    }
  };

  // Pagination helper
  const paginatedResults = batchResult
    ? batchResult.results.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
    : [];

  const totalPages = batchResult ? Math.ceil(batchResult.results.length / itemsPerPage) : 0;

  // Chart data calculations
  const sentimentChartData = batchResult ? [
    { name: 'Positive', count: batchResult.sentiment_distribution.positive || 0, fill: SENTIMENT_COLORS.positive },
    { name: 'Negative', count: batchResult.sentiment_distribution.negative || 0, fill: SENTIMENT_COLORS.negative },
    { name: 'Neutral', count: batchResult.sentiment_distribution.neutral || 0, fill: SENTIMENT_COLORS.neutral },
    { name: 'Mixed', count: batchResult.sentiment_distribution.mixed || 0, fill: SENTIMENT_COLORS.mixed },
  ] : [];


  const emotionChartData = batchResult ? Object.entries(batchResult.emotion_distribution).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    count: value,
    fill: EMOTION_COLORS[key] || '#6366f1',
  })) : [];

  const sarcasmChartData = batchResult ? [
    { name: 'Sarcastic', value: batchResult.sarcasm_distribution.sarcastic || 0, fill: '#ec4899' },
    { name: 'Not Sarcastic', value: batchResult.sarcasm_distribution["not sarcastic"] || 0, fill: '#6366f1' },
  ] : [];

  const languageChartData = batchResult ? Object.entries(batchResult.language_distribution).map(([key, value]) => ({
    name: key,
    count: value,
  })) : [];

  // Confidence distribution line chart data
  const confidenceData = batchResult ? batchResult.results.map((r, i) => ({
    comment: `C${i + 1}`,
    confidence: Math.round((r.confidence || 0) * 100),
  })) : [];

  return (
    <div className="space-y-6 relative min-h-[85vh]">
      
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            Social Media Analyzer
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Extract sentiment, emotions, sarcasm, and insights from social channels instantly
          </p>
        </div>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-white/10 bg-white/70 dark:bg-white/[0.03] hover:bg-slate-100 dark:hover:bg-white/[0.08] backdrop-blur-md shadow-sm transition-all text-sm font-semibold select-none cursor-pointer"
          style={{ color: 'var(--text-secondary)' }}
        >
          <Search size={16} />
          <span>Recent Analyses</span>
        </button>
      </div>

      {/* Main dashboard content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side: Input Panel (Takes 1 Column on desktop) */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-card p-6 flex flex-col h-full">
            <h3 className="text-base font-semibold mb-4" style={{ color: 'var(--text-secondary)' }}>
              1. Platform & Format
            </h3>
            
            {/* Platform grid */}
            <div className="grid grid-cols-2 gap-2 mb-6">
              {PLATFORMS.map(platform => {
                const Icon = platform.icon;
                const isSelected = selectedPlatform === platform.id;
                return (
                  <button
                    key={platform.id}
                    onClick={() => setSelectedPlatform(platform.id)}
                    className="flex flex-col items-center justify-center p-3 rounded-xl border transition-all cursor-pointer relative overflow-hidden text-center group"
                    style={{
                      borderColor: isSelected ? platform.color : 'var(--border-glass)',
                      background: isSelected ? platform.bg : 'transparent',
                    }}
                  >
                    <Icon size={20} className="mb-1" style={{ color: isSelected ? platform.color : 'var(--text-secondary)' }} />
                    <span 
                      className="text-xs font-semibold"
                      style={{ color: isSelected ? 'var(--text-primary)' : 'var(--text-muted)' }}
                    >
                      {platform.name}
                    </span>
                    {isSelected && (
                      <span 
                        className="absolute bottom-0 left-0 right-0 h-1 transition-all"
                        style={{ backgroundColor: platform.color }}
                      />
                    )}
                  </button>
                );
              })}
            </div>

            <h3 className="text-base font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>
              2. Input Mode
            </h3>
            
            {/* Mode toggle */}
            <div className="flex p-1 rounded-xl bg-slate-100 dark:bg-white/[0.04] mb-4">
              <button
                onClick={() => setInputMode('single')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${inputMode === 'single' ? 'bg-white dark:bg-slate-800 shadow-sm text-slate-800 dark:text-white' : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white'}`}
              >
                Single Comment
              </button>
              <button
                onClick={() => setInputMode('batch')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${inputMode === 'batch' ? 'bg-white dark:bg-slate-800 shadow-sm text-slate-800 dark:text-white' : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white'}`}
              >
                Multiple Comments
              </button>
            </div>

            {/* Input fields */}
            <div className="flex-1 mb-4">
              {inputMode === 'single' ? (
                <div>
                  <label className="text-xs font-semibold tracking-wider text-slate-500 dark:text-slate-400 uppercase block mb-1.5">
                    Paste Post or Comment
                  </label>
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Enter a single social media comment or post to analyze..."
                    className="w-full h-44 p-3 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none transition-all"
                  />
                </div>
              ) : (
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="text-xs font-semibold tracking-wider text-slate-500 dark:text-slate-400 uppercase">
                      Paste Multiple Comments
                    </label>
                    <span className="text-[10px] text-slate-500" style={{ color: 'var(--text-muted)' }}>
                      One comment per line
                    </span>
                  </div>
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Paste comments here&#10;Line 1: I love this brand!&#10;Line 2: Terrible customer service.&#10;Line 3: Wonderful, another flat tire today..."
                    className="w-full h-64 p-3 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none transition-all font-mono text-xs"
                  />
                </div>
              )}
            </div>

            {errorMessage && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-200 text-xs flex items-start gap-2">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={handleClear}
                disabled={isLoading}
                className="flex-1 min-w-[70px] py-3 px-4 rounded-xl border border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/[0.05] active:scale-[0.98] transition-all font-semibold text-xs shadow-sm cursor-pointer disabled:opacity-50"
              >
                Clear
              </button>

              {(singleResult || batchResult) && (
                <button
                  onClick={() => handleDownloadReport(singleResult ? singleResult.id : (batchResult!.results[0].batch_run_id || batchResult!.results[0].id))}

                  disabled={downloadingId !== null}
                  className="flex-1 min-w-[120px] py-3 px-4 rounded-xl border border-emerald-500/20 text-emerald-500 dark:text-emerald-400 hover:bg-emerald-500/5 active:scale-[0.98] transition-all font-bold text-xs shadow-sm cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {downloadingId !== null ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <Download size={14} />
                      <span>Download Report</span>
                    </>
                  )}
                </button>
              )}

              <button
                onClick={handleAnalyze}
                disabled={isLoading || !text.trim()}
                className="flex-[2] min-w-[140px] py-3 px-4 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-400 hover:to-indigo-400 active:scale-[0.98] transition-all text-white font-semibold text-xs shadow-lg shadow-purple-500/10 flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Send size={14} />
                    <span>Analyze Content</span>
                  </>
                )}
              </button>
            </div>

          </div>
        </div>

        {/* Right Side: Results Dashboards (Takes 2 Columns on desktop) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Skeleton Loaders */}
          {isLoading && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="skeleton h-24 rounded-xl" />
                ))}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="skeleton h-64 rounded-xl" />
                <div className="skeleton h-64 rounded-xl" />
              </div>
              <div className="skeleton h-44 rounded-xl" />
              <div className="skeleton h-56 rounded-xl" />
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !batchResult && !singleResult && (
            <div className="glass-card p-16 text-center flex flex-col items-center justify-center h-full min-h-[60vh]">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-purple-500/10 border border-purple-500/20 mb-4">
                <Sparkles size={32} className="text-purple-500 animate-pulse" />
              </div>
              <h3 className="text-xl font-bold mb-2">No Content Analyzed Yet</h3>
              <p className="text-sm max-w-md mx-auto text-slate-500 dark:text-slate-400" style={{ color: 'var(--text-muted)' }}>
                Select a platform, choose your input mode (single or multiple comments), paste your content, and press the Analyze button to see insights.
              </p>
            </div>
          )}

          {/* SINGLE COMMENT RESPONSE */}
          {singleResult && !isLoading && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              
              {/* Single analysis summary card */}
              <div className="glass-card p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 dark:bg-purple-500/10 rounded-full blur-[40px] pointer-events-none" />
                
                <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                  <Sparkles size={16} className="text-purple-500" />
                  <span>Single Comment Analysis Result</span>
                </h3>
                
                <div className="p-4 rounded-xl mb-6 bg-slate-50 dark:bg-white/[0.02] border border-slate-100 dark:border-white/5 font-mono text-sm leading-relaxed text-slate-800 dark:text-slate-200">
                  "{singleResult.original_text}"
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-white/40 dark:bg-white/[0.02] rounded-xl border border-slate-200 dark:border-white/5 text-center">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Sentiment</span>
                    <p 
                      className="text-lg font-bold capitalize mt-1" 
                      style={{ color: SENTIMENT_COLORS[singleResult.sentiment || 'neutral'] }}
                    >
                      {singleResult.sentiment}
                    </p>
                  </div>
                  <div className="p-3 bg-white/40 dark:bg-white/[0.02] rounded-xl border border-slate-200 dark:border-white/5 text-center">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Emotion</span>
                    <p className="text-lg font-bold capitalize mt-1 text-indigo-500 dark:text-indigo-400">
                      {EMOJI_MAP[singleResult.emotion || 'neutral']} {singleResult.emotion}
                    </p>
                  </div>
                  <div className="p-3 bg-white/40 dark:bg-white/[0.02] rounded-xl border border-slate-200 dark:border-white/5 text-center">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Confidence</span>
                    <p className="text-lg font-bold mt-1 text-slate-800 dark:text-white">
                      {Math.round((singleResult.confidence || 0) * 100)}%
                    </p>
                  </div>
                  <div className="p-3 bg-white/40 dark:bg-white/[0.02] rounded-xl border border-slate-200 dark:border-white/5 text-center">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Sarcasm</span>
                    <p 
                      className="text-lg font-bold mt-1 capitalize" 
                      style={{ color: singleResult.sarcasm_detected ? 'var(--negative)' : 'var(--positive)' }}
                    >
                      {singleResult.sarcasm_detected ? 'Sarcastic' : 'No'}
                    </p>
                  </div>
                  <div className="p-3 bg-white/40 dark:bg-white/[0.02] rounded-xl border border-slate-200 dark:border-white/5 text-center col-span-2">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Detected Language</span>
                    <p className="text-sm font-bold mt-1 text-slate-800 dark:text-white">
                      {singleResult.detected_language || 'Unknown'} ({singleResult.language_code || 'N/A'})
                    </p>
                  </div>
                  <div className="p-3 bg-white/40 dark:bg-white/[0.02] rounded-xl border border-slate-200 dark:border-white/5 text-center col-span-2">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Processing Speed</span>
                    <p className="text-sm font-bold mt-1 text-slate-800 dark:text-white">
                      {singleResult.processing_time_ms || 'N/A'} ms (Inf: {singleResult.inference_time_ms || 'N/A'} ms)
                    </p>
                  </div>
                </div>

                {singleResult.sarcasm_detected && singleResult.sarcasm_reason && (
                  <div className="mt-4 p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-700 dark:text-purple-200 text-xs flex gap-2">
                    <Brain size={16} className="shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block mb-0.5">Sarcasm Context Reasoning:</span>
                      {singleResult.sarcasm_reason}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* BATCH COMMENTS RESPONSE */}
          {batchResult && !isLoading && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              
              {/* Stat summary cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                <div className="glass-card p-4 text-center">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Analyzed</span>
                  <p className="text-2xl font-black text-slate-800 dark:text-white mt-0.5">{batchResult.total_processed}</p>
                </div>
                <div className="glass-card p-4 text-center">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Dominant Sentiment</span>
                  <p 
                    className="text-2xl font-black mt-0.5 capitalize" 
                    style={{ color: SENTIMENT_COLORS[batchResult.insights.dominant_emotion === 'neutral' ? 'neutral' : 'positive'] }}
                  >
                    {batchResult.insights.positive_percentage >= batchResult.insights.negative_percentage 
                      ? (batchResult.insights.positive_percentage >= batchResult.insights.neutral_percentage ? 'Positive' : 'Neutral')
                      : 'Negative'}
                  </p>
                </div>
                <div className="glass-card p-4 text-center">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Dominant Emotion</span>
                  <p className="text-2xl font-black text-indigo-500 dark:text-indigo-400 mt-0.5 capitalize">
                    {batchResult.insights.dominant_emotion_emoji} {batchResult.insights.dominant_emotion}
                  </p>
                </div>
                <div className="glass-card p-4 text-center">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Avg Confidence</span>
                  <p className="text-2xl font-black text-slate-800 dark:text-white mt-0.5">
                    {Math.round(batchResult.average_confidence * 100)}%
                  </p>
                </div>
                <div className="glass-card p-4 text-center">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Sarcasm Rate</span>
                  <p className="text-2xl font-black text-rose-500 dark:text-rose-400 mt-0.5">
                    {batchResult.sarcasm_rate.toFixed(1)}%
                  </p>
                </div>
                <div className="glass-card p-4 text-center col-span-2 md:col-span-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Avg Speed</span>
                  <p className="text-xl font-black text-slate-800 dark:text-white mt-1">
                    {batchResult.average_processing_time_ms.toFixed(1)} ms
                  </p>
                </div>
              </div>

              {/* Business Insights Panel */}
              <div className="glass-card p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-36 h-36 bg-purple-500/5 rounded-full blur-[40px] pointer-events-none" />
                <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                  <Sparkles size={16} className="text-purple-500" />
                  <span>Business Insights & AI Recommendations</span>
                </h3>

                {batchResult.insights.executive_summary && (
                  <div className="mb-6 p-4 rounded-xl bg-indigo-500/[0.03] border border-indigo-500/10 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                    <span className="text-[10px] uppercase tracking-wider font-extrabold text-indigo-500 block mb-1.5">Executive Summary</span>
                    {batchResult.insights.executive_summary}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  
                  {/* Share Stats */}
                  <div className="md:col-span-4 flex flex-col gap-2 bg-slate-50 dark:bg-white/[0.02] p-4 rounded-xl border border-slate-100 dark:border-white/5">
                    <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                      Sentiment Shares
                    </h4>
                    <div className="flex justify-between items-center text-sm">
                      <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Positive</span>
                      <span className="font-bold text-emerald-500">{batchResult.insights.positive_percentage}%</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Negative</span>
                      <span className="font-bold text-red-500">{batchResult.insights.negative_percentage}%</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Neutral</span>
                      <span className="font-bold text-amber-500">{batchResult.insights.neutral_percentage}%</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-violet-500" /> Mixed</span>
                      <span className="font-bold text-violet-500">{batchResult.insights.mixed_percentage || 0}%</span>
                    </div>
                  </div>


                  {/* Recommendations */}
                  <div className="md:col-span-8 space-y-3">
                    <div>
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                        Dynamic Action Plan
                      </span>
                      <ul className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
                        {batchResult.insights.recommendations.map((rec, i) => (
                          <li key={i} className="flex gap-2 items-start bg-purple-500/[0.02] border border-purple-500/10 p-3 rounded-lg">
                            <Award size={16} className="text-purple-500 shrink-0 mt-0.5" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
                
                {/* Praises and complaints */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 pt-4 border-t border-slate-200 dark:border-white/10">
                  <div className="p-3 bg-emerald-500/5 border border-emerald-500/15 rounded-xl">
                    <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 uppercase tracking-wider block mb-1.5">
                      Top Praises (Positive Drivers)
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {batchResult.insights.top_praises.map((p, i) => (
                        <span key={i} className="text-xs font-medium px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 capitalize">
                          {p || 'N/A'}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="p-3 bg-red-500/5 border border-red-500/15 rounded-xl">
                    <span className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wider block mb-1.5">
                      Top Complaints (Negative Drivers)
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {batchResult.insights.top_complaints.map((c, i) => (
                        <span key={i} className="text-xs font-medium px-2 py-0.5 rounded-md bg-red-500/10 text-red-600 dark:text-red-400 capitalize">
                          {c || 'N/A'}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Keywords Panels */}
              <div className="glass-card p-6">
                <h3 className="text-base font-bold mb-4 flex items-center gap-2">
                  <Brain size={16} className="text-indigo-500" />
                  <span>Keyword Extraction</span>
                </h3>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                      Most Frequent
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {batchResult.keywords.most_frequent.slice(0, 5).map((item, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-slate-100 dark:bg-white/[0.04] rounded-md text-slate-700 dark:text-slate-300 flex items-center gap-1">
                          <span className="font-semibold capitalize">{item.word}</span>
                          <span className="opacity-50 text-[10px]">({item.count})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                      Positive Keywords
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {batchResult.keywords.positive_keywords.slice(0, 5).map((item, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-emerald-500/10 rounded-md text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                          <span className="font-semibold capitalize">{item.word}</span>
                          <span className="opacity-50 text-[10px]">({item.count})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                      Negative Keywords
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {batchResult.keywords.negative_keywords.slice(0, 5).map((item, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-red-500/10 rounded-md text-red-600 dark:text-red-400 flex items-center gap-1">
                          <span className="font-semibold capitalize">{item.word}</span>
                          <span className="opacity-50 text-[10px]">({item.count})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                      Most Emotional
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {batchResult.keywords.most_emotional.slice(0, 5).map((item, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-indigo-500/10 rounded-md text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                          <span className="font-semibold capitalize">{item.word}</span>
                          <span className="opacity-50 text-[10px]">({item.count})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Visualizations Charts Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Sentiment Bar Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Sentiment Distribution
                  </h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={sentimentChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                      <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                      <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                      <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                        {sentimentChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Emotion Pie Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Emotion Distribution
                  </h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <PieChart>
                      <Pie data={emotionChartData} cx="50%" cy="50%" innerRadius={50} outerRadius={85} paddingAngle={3} dataKey="count" nameKey="name">
                        {emotionChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Confidence Distribution Area Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Confidence Distribution (%)
                  </h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <AreaChart data={confidenceData}>
                      <defs>
                        <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                      <XAxis dataKey="comment" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                      <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} domain={[0, 100]} />
                      <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                      <Area type="monotone" dataKey="confidence" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorConfidence)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Sarcasm Distribution Donut Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Sarcasm Share
                  </h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <PieChart>
                      <Pie data={sarcasmChartData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value">
                        {sarcasmChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Language Distribution Horizontal Bar Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Language Distribution
                  </h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={languageChartData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                      <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                      <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} width={80} />
                      <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                      <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Emotion Intensity Heatmap Layout */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Emotion Intensity Grid
                  </h3>
                  <div className="grid grid-cols-4 gap-2 h-[200px]">
                    {Object.entries(batchResult.emotion_distribution).slice(0, 8).map(([emotion, count]) => {
                      const color = EMOTION_COLORS[emotion] || '#6366f1';
                      const ratio = count / batchResult.total_processed;
                      return (
                        <div 
                          key={emotion} 
                          className="rounded-xl p-3 flex flex-col justify-between transition-all hover:scale-105"
                          style={{
                            background: color,
                            opacity: Math.max(0.2, ratio * 1.5),
                            color: '#fff'
                          }}
                        >
                          <span className="text-lg">{EMOJI_MAP[emotion] || '😐'}</span>
                          <div>
                            <span className="text-[10px] uppercase font-bold block opacity-80 truncate">{emotion}</span>
                            <span className="text-xs font-black block">{count} ({Math.round(ratio * 100)}%)</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Aspect Sentiment Breakdown Bar Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Aspect Sentiment Breakdown
                  </h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={batchResult.insights.aspect_sentiment_table || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                      <XAxis dataKey="aspect" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                      <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                      <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                      <Legend />
                      <Bar dataKey="positive" fill="#10b981" name="Positive" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="negative" fill="#ef4444" name="Negative" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="neutral" fill="#f59e0b" name="Neutral" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Top Discussed Topics Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-sm font-semibold mb-4 text-slate-600 dark:text-slate-400">
                    Top Discussed Topics
                  </h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={(batchResult.keywords.most_frequent || []).slice(0, 5)} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                      <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                      <YAxis dataKey="word" type="category" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} width={80} />
                      <Tooltip contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 12 }} />
                      <Bar dataKey="count" fill="#3b82f6" name="Frequency" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

              </div>


              {/* INDIVIDUAL COMMENT TABLE */}
              <div className="glass-card p-6 overflow-hidden">
                <h3 className="text-base font-bold mb-4">
                  Individual Comments Details ({batchResult.results.length})
                </h3>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider">
                        <th className="py-3 px-4 font-semibold">Comment</th>
                        <th className="py-3 px-4 font-semibold">Sentiment</th>
                        <th className="py-3 px-4 font-semibold">Emotion</th>
                        <th className="py-3 px-4 font-semibold">Confidence</th>
                        <th className="py-3 px-4 font-semibold">Sarcasm</th>
                        <th className="py-3 px-4 font-semibold">Language</th>
                        <th className="py-3 px-4 font-semibold">Aspect</th>
                        <th className="py-3 px-4 font-semibold text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                      {paginatedResults.map(item => (
                        <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-white/[0.01] transition-colors">
                          <td className="py-3 px-4 max-w-xs truncate text-slate-900 dark:text-white" title={item.original_text}>
                            {item.original_text}
                          </td>
                          <td className="py-3 px-4 capitalize">
                            <span 
                              className="px-2 py-0.5 rounded-full text-xs font-semibold"
                              style={{
                                backgroundColor: `${SENTIMENT_COLORS[item.sentiment || 'neutral']}18`,
                                color: SENTIMENT_COLORS[item.sentiment || 'neutral']
                              }}
                            >
                              {item.sentiment}
                            </span>
                          </td>
                          <td className="py-3 px-4 capitalize text-slate-800 dark:text-slate-200">
                            {EMOJI_MAP[item.emotion || 'neutral']} {item.emotion}
                          </td>
                          <td className="py-3 px-4 font-mono font-medium text-slate-700 dark:text-slate-300">
                            {Math.round((item.confidence || 0) * 100)}%
                          </td>
                          <td className="py-3 px-4">
                            <span 
                              className="px-2 py-0.5 rounded-full text-xs font-semibold capitalize"
                              style={{
                                backgroundColor: item.sarcasm_detected ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                                color: item.sarcasm_detected ? '#ef4444' : '#10b981'
                              }}
                            >
                              {item.sarcasm_detected ? 'Yes' : 'No'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-xs text-slate-600 dark:text-slate-400">
                            {item.detected_language} ({item.language_code})
                          </td>
                          <td className="py-3 px-4 capitalize font-semibold text-slate-700 dark:text-slate-300">
                            {item.aspect || 'General Experience'}
                          </td>
                          <td className="py-3 px-4 text-center">

                            <button
                              onClick={() => handleDeleteRecord(item.id)}
                              className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer"
                              title="Delete comment record"
                            >
                              <Trash2 size={14} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                  <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-200 dark:border-white/10">
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      Showing Page {currentPage} of {totalPages}
                    </span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-white/10 text-xs font-semibold disabled:opacity-50 cursor-pointer"
                      >
                        Prev
                      </button>
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-white/10 text-xs font-semibold disabled:opacity-50 cursor-pointer"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

        </div>
      </div>

      {/* RECENT ANALYSES SIDE DRAWER/PANEL */}
      <AnimatePresence>
        {showHistory && (
          <>
            {/* Backdrop overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowHistory(false)}
              className="fixed inset-0 bg-black z-40"
            />

            {/* Sidebar drawer content */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 h-screen w-full max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-white/10 shadow-2xl z-50 flex flex-col"
            >
              
              {/* Drawer Header */}
              <div className="p-4 border-b border-slate-200 dark:border-white/10 flex justify-between items-center bg-slate-50 dark:bg-white/[0.02]">
                <div>
                  <h3 className="font-bold text-lg text-slate-800 dark:text-white">Recent Analyses</h3>
                  <p className="text-xs text-slate-500" style={{ color: 'var(--text-muted)' }}>
                    Filter and load past social media runs
                  </p>
                </div>
                <button
                  onClick={() => setShowHistory(false)}
                  className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-white/[0.06] text-slate-600 dark:text-slate-400 cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Drawer Filters */}
              <div className="p-4 border-b border-slate-200 dark:border-white/10 space-y-3 bg-slate-50/50 dark:bg-white/[0.01]">
                
                {/* Search Bar */}
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                    <Search size={14} />
                  </span>
                  <input
                    type="text"
                    placeholder="Search comment texts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs focus:outline-none focus:border-purple-500"
                  />
                </div>

                {/* Filter dropdowns */}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                      Platform
                    </label>
                    <select
                      value={filterPlatform}
                      onChange={(e) => setFilterPlatform(e.target.value)}
                      className="w-full p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
                    >
                      <option value="all">All Platforms</option>
                      {PLATFORMS.map(p => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                      Sentiment
                    </label>
                    <select
                      value={filterSentiment}
                      onChange={(e) => setFilterSentiment(e.target.value)}
                      className="w-full p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
                    >
                      <option value="all">All Sentiments</option>
                      <option value="positive">Positive</option>
                      <option value="negative">Negative</option>
                      <option value="neutral">Neutral</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                      Emotion
                    </label>
                    <select
                      value={filterEmotion}
                      onChange={(e) => setFilterEmotion(e.target.value)}
                      className="w-full p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
                    >
                      <option value="all">All Emotions</option>
                      <option value="joy">Joy</option>
                      <option value="love">Love</option>
                      <option value="anger">Anger</option>
                      <option value="sadness">Sadness</option>
                      <option value="fear">Fear</option>
                      <option value="surprise">Surprise</option>
                      <option value="disgust">Disgust</option>
                      <option value="neutral">Neutral</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={filterStartDate}
                      onChange={(e) => setFilterStartDate(e.target.value)}
                      className="w-full p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={filterEndDate}
                      onChange={(e) => setFilterEndDate(e.target.value)}
                      className="w-full p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={() => {
                        setSearchQuery('');
                        setFilterPlatform('all');
                        setFilterSentiment('all');
                        setFilterEmotion('all');
                        setFilterStartDate('');
                        setFilterEndDate('');
                      }}
                      className="w-full py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-lg text-xs font-semibold text-center cursor-pointer"
                    >
                      Reset Filters
                    </button>
                  </div>
                </div>
              </div>

              {/* Drawer List Content */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {historyItems.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 dark:text-slate-400" style={{ color: 'var(--text-muted)' }}>
                    <AlertTriangle className="mx-auto mb-2 opacity-35" size={32} />
                    <p className="text-sm">No analysis history found.</p>
                  </div>
                ) : (
                  historyItems.map(item => (
                    <div 
                      key={item.id} 
                      className="p-3.5 bg-slate-50 hover:bg-slate-100 dark:bg-white/[0.02] dark:hover:bg-white/[0.04] rounded-xl border border-slate-100 dark:border-white/5 flex flex-col justify-between transition-colors text-xs"
                    >
                      <div className="flex justify-between items-start gap-2 mb-1.5">
                        <span className="font-semibold text-slate-800 dark:text-slate-200 capitalize truncate pr-2">
                          {PLATFORMS.find(p => p.id === item.platform)?.name || item.platform}
                        </span>
                        <div className="flex gap-1 flex-shrink-0">
                          <span 
                            className="px-1.5 py-0.5 rounded font-bold capitalize text-[10px]"
                            style={{
                              backgroundColor: `${SENTIMENT_COLORS[item.sentiment || 'neutral']}18`,
                              color: SENTIMENT_COLORS[item.sentiment || 'neutral']
                            }}
                          >
                            {item.sentiment}
                          </span>
                          <span className="px-1.5 py-0.5 rounded font-bold bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 text-[10px] capitalize">
                            {EMOJI_MAP[item.emotion || 'neutral']} {item.emotion}
                          </span>
                        </div>
                      </div>

                      <p className="text-slate-600 dark:text-slate-400 mb-2 truncate italic font-serif">
                        "{item.original_text}"
                      </p>

                      <div className="flex justify-between items-center text-[10px]" style={{ color: 'var(--text-muted)' }}>
                        <span>{new Date(item.created_at).toLocaleString()}</span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              // Load this item as a single result representation in the main view
                              setSingleResult(item);
                              setBatchResult(null);
                              setShowHistory(false);
                            }}
                            className="text-purple-600 dark:text-purple-400 hover:underline font-bold cursor-pointer"
                          >
                            Load
                          </button>
                          <span className="opacity-50">|</span>
                          <button
                            onClick={() => handleDownloadReport(item.batch_run_id || item.id)}

                            disabled={downloadingId === item.id}
                            className="text-emerald-500 hover:text-emerald-700 font-bold cursor-pointer disabled:opacity-50"
                          >
                            {downloadingId === item.id ? 'Report...' : 'Report'}
                          </button>
                          <span className="opacity-50">|</span>
                          <button
                            onClick={() => handleDeleteRecord(item.id)}
                            className="text-red-500 hover:text-red-700 font-bold cursor-pointer"
                          >
                            Delete
                          </button>

                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
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

