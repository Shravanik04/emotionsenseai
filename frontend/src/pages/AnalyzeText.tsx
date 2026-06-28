import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Share2, Download, Zap, Globe, Brain, Clock, Hash, Type, Volume2, Mic, MicOff, AlertTriangle, Layers, Tag } from 'lucide-react';
import { getWebSocketUrl } from '../services/api';
import type { FullAnalysisResult } from '../types';

/* ------------------------------------------------------------------ */
/* Emotion color palette                                               */
/* ------------------------------------------------------------------ */
const EMOTION_COLORS: Record<string, string> = {
  // Positive
  joy: '#10b981',
  happiness: '#059669',
  excitement: '#34d399',
  love: '#ec4899',
  gratitude: '#06b6d4',
  pride: '#3b82f6',
  hope: '#14b8a6',
  optimism: '#f59e0b',
  relief: '#10b981',
  confidence: '#3b82f6',
  admiration: '#8b5cf6',
  inspiration: '#d946ef',
  curiosity: '#f59e0b',
  trust: '#06b6d4',
  satisfaction: '#10b981',
  validation: '#10b981',
  belonging: '#ec4899',
  collaboration: '#06b6d4',

  // Negative
  sadness: '#3b82f6',
  anger: '#ef4444',
  fear: '#8b5cf6',
  anxiety: '#a855f7',
  stress: '#f43f5e',
  frustration: '#f43f5e',
  disappointment: '#6366f1',
  loneliness: '#475569',
  confusion: '#64748b',
  disgust: '#84cc16',
  jealousy: '#a855f7',
  regret: '#6366f1',
  guilt: '#64748b',
  embarrassment: '#f43f5e',
  fatigue: '#475569',
  discomfort: '#f43f5e',

  // Neutral
  calm: '#10b981',
  neutral: '#6b7280',
  thoughtful: '#6366f1',
  analytical: '#0ea5e9',

  // Complex
  surprise: '#f59e0b',
  nostalgia: '#d946ef',
  determination: '#f43f5e',
  sympathy: '#ec4899',
  compassion: '#14b8a6',
  awe: '#8b5cf6',
  anticipation: '#f59e0b',
  skepticism: '#64748b',
  overwhelmed: '#f43f5e',
  shock: '#ef4444',
  resilience: '#10b981'
};

const EMOJI_MAP_JS: Record<string, string> = {
  joy: "😊", happiness: "😀", excitement: "🎉", love: "❤️", gratitude: "🙏", pride: "🦁",
  hope: "🌅", optimism: "☀️", relief: "😌", confidence: "😎", admiration: "👏",
  inspiration: "💡", curiosity: "🤔", trust: "🤝", satisfaction: "👍", validation: "🛡️",
  belonging: "🤝", collaboration: "👥",
  sadness: "😔", anger: "😤", fear: "😨", anxiety: "😟", stress: "😫", frustration: "😒",
  disappointment: "😞", loneliness: "🏚️", confusion: "🤷", disgust: "🤢", jealousy: "💚",
  regret: "🤦", guilt: "🥺", embarrassment: "😳", fatigue: "🥱", discomfort: "😣",
  calm: "🧘", neutral: "😐", thoughtful: "💭", analytical: "📊",
  surprise: "😲", nostalgia: "⏳", determination: "✊", sympathy: "💖", compassion: "🤲",
  awe: "🌌", anticipation: "⏳", skepticism: "🤨", overwhelmed: "🤯", shock: "💥", resilience: "🦾"
};

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
};

/* ------------------------------------------------------------------ */
/* Sub-components                                                     */
/* ------------------------------------------------------------------ */

const RadialGauge = ({ value, color, label, emoji }: { value: number, color: string, label: string, emoji: string }) => {
  const radius = 45;
  const strokeWidth = 8;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-3 glass-card bg-white/5 border-white/10">
      <div className="relative flex items-center justify-center w-24 h-24">
        <svg className="w-full h-full transform -rotate-90">
          <circle
            className="text-gray-200"
            strokeWidth={strokeWidth}
            stroke="currentColor"
            fill="transparent"
            r={normalizedRadius}
            cx="48"
            cy="48"
            style={{ color: 'rgba(255,255,255,0.06)' }}
          />
          <motion.circle
            strokeWidth={strokeWidth}
            strokeDasharray={circumference + ' ' + circumference}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: "easeOut" }}
            strokeLinecap="round"
            stroke={color}
            fill="transparent"
            r={normalizedRadius}
            cx="48"
            cy="48"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-2xl">{emoji}</span>
          <span className="text-[10px] font-bold text-gray-600 dark:text-gray-400 mt-0.5">{value.toFixed(0)}%</span>
        </div>
      </div>
      <span className="text-xs font-semibold capitalize mt-2 text-center" style={{ color: 'var(--text-secondary)' }}>
        Dominant: {label}
      </span>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Main component                                                     */
/* ------------------------------------------------------------------ */
export const AnalyzeText = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState<FullAnalysisResult | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'emotions' | 'sentences' | 'metadata'>('overview');

  const wsRef = useRef<WebSocket | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const recognitionRef = useRef<any>(null);

  /* ---------- WebSocket connection ---------- */
  const connectWs = useCallback(() => {
    try {
      const ws = new WebSocket(getWebSocketUrl());
      ws.onopen = () => setIsConnected(true);
      ws.onclose = () => {
        setIsConnected(false);
        setTimeout(connectWs, 2000);
      };
      ws.onerror = () => setIsConnected(false);
      ws.onmessage = (event) => {
        try {
          const data: FullAnalysisResult = JSON.parse(event.data);
          if (!data.error) {
            setResult(data);
          }
        } catch { /* ignore */ }
        setIsAnalyzing(false);
      };
      wsRef.current = ws;
    } catch {
      setTimeout(connectWs, 2000);
    }
  }, []);

  useEffect(() => {
    connectWs();
    return () => {
      wsRef.current?.close();
      if (isSpeaking) window.speechSynthesis.cancel();
    };
  }, [connectWs]);

  /* ---------- Speech-to-Text ---------- */
  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = result?.language.code === 'hi' ? 'hi-IN' : result?.language.code === 'kn' ? 'kn-IN' : 'en-US';

    rec.onstart = () => setIsListening(true);
    rec.onend = () => setIsListening(false);
    rec.onerror = () => setIsListening(false);
    rec.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      const updatedText = text ? `${text} ${transcript}` : transcript;
      setText(updatedText);
      handleTextChange(updatedText);
    };

    recognitionRef.current = rec;
    rec.start();
  };

  /* ---------- Text-to-Speech ---------- */
  const toggleSpeech = () => {
    if (!result) return;
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(result.insights.explanation);
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v => v.lang.startsWith(result.language.code)) || voices[0];
    if (voice) utterance.voice = voice;

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  /* ---------- Debounced send ---------- */
  const handleTextChange = (value: string) => {
    setText(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!value.trim()) { setResult(null); return; }

    setIsAnalyzing(true);
    debounceRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ text: value }));
      }
    }, 400);
  };

  /* ---------- Download Report ---------- */
  const handleDownload = () => {
    if (!result) return;
    const reportText = `=====================================================
SENTIMENTSCOPE EMOTION & SENTIMENT ANALYSIS REPORT
Generated on: ${new Date().toLocaleString()}
=====================================================

OVERALL SUMMARY:
-----------------------------------------------------
Input Preview: "${text.slice(0, 100)}${text.length > 100 ? '...' : ''}"
Dominant Sentiment: ${result.sentiment.toUpperCase()} (${(result.sentiment_confidence * 100).toFixed(1)}%)
Dominant Emotion: ${result.emotion.toUpperCase()} ${result.emotion_emoji} (${(result.emotion_confidence * 100).toFixed(1)}%)
Language: ${result.language.name} ${result.language.flag}
Sarcasm: ${result.sarcasm.detected ? `⚠️ DETECTED (${result.sarcasm.reason})` : 'None Detected'}
Readability score: ${result.readability.score} (${result.readability.complexity})

AI INSIGHTS:
-----------------------------------------------------
${result.insights.explanation}

SENTENCE-BY-SENTENCE BREAKDOWN:
-----------------------------------------------------
${result.sentences.map((s, idx) => `${idx + 1}. [${s.sentiment.toUpperCase()}] [${s.emotion_emoji} ${s.emotion.toUpperCase()}] ${s.sarcasm.detected ? '(Sarcastic) ' : ''}"${s.text}"`).join('\n')}

=====================================================`;

    const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", url);
    downloadAnchor.setAttribute("download", `analysis_report_${result.id || 'realtime'}.txt`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    if (!result) return;
    const report = `Sentiment: ${result.sentiment.toUpperCase()} (${(result.sentiment_confidence * 100).toFixed(1)}%)\nEmotion: ${result.emotion.toUpperCase()} ${result.emotion_emoji} (${(result.emotion_confidence * 100).toFixed(1)}%)\nSarcasm: ${result.sarcasm.detected ? 'DETECTED' : 'NOT DETECTED'}\nReadability: ${result.readability.complexity} (Score: ${result.readability.score})\n\nReport:\n${result.insights.explanation}`;
    navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = () => {
    if (!result) return;
    const shareText = `Emotion & Sentiment Analysis Report:\n${result.insights.explanation}`;
    if (navigator.share) {
      navigator.share({ title: 'Emotion & Sentiment Report', text: shareText });
    } else {
      navigator.clipboard.writeText(shareText);
    }
  };

  /* ---------- Highlighting helper ---------- */
  const highlightWords = (sentText: string, posWords: any[], negWords: any[]) => {
    const pSet = new Set(posWords.map(w => w.word.toLowerCase()));
    const nSet = new Set(negWords.map(w => w.word.toLowerCase()));
    const words = sentText.split(/(\b\w+\b)/g);

    return words.map((w, idx) => {
      const lower = w.toLowerCase();
      if (pSet.has(lower)) {
        return <span key={idx} className="font-semibold text-emerald-400 bg-emerald-500/10 px-1 rounded">{w}</span>;
      }
      if (nSet.has(lower)) {
        return <span key={idx} className="font-semibold text-rose-400 bg-rose-500/10 px-1 rounded">{w}</span>;
      }
      return w;
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            Real-Time Analysis
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Type, paste, or speak text — results upgrade instantly
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
            <div className={isConnected ? 'live-pulse' : 'w-2.5 h-2.5 rounded-full bg-red-500'} />
            {isConnected ? 'Live Engine' : 'Reconnecting…'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* ================= LEFT — Input & Heuristics ================= */}
        <div className="space-y-4">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>
                Input Text
              </label>
              <div className="flex items-center gap-3">
                <button
                  onClick={toggleListening}
                  className={`p-1.5 rounded-full transition-colors ${isListening ? 'bg-rose-500 text-white animate-pulse' : 'bg-white/10 hover:bg-white/20 text-gray-600 dark:text-gray-300'}`}
                  title={isListening ? "Stop listening" : "Start Voice Input"}
                >
                  {isListening ? <MicOff size={16} /> : <Mic size={16} />}
                </button>
                {isAnalyzing && (
                  <div className="flex items-center gap-1.5 text-xs text-indigo-400">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span>Analyzing…</span>
                  </div>
                )}
              </div>
            </div>
            <textarea
              value={text}
              onChange={(e) => handleTextChange(e.target.value)}
              rows={9}
              className="input-glass w-full resize-none"
              placeholder="Start typing or click the microphone to run real-time sentiment, sarcasm, and emotion analysis…"
            />
            {/* Stats Bar */}
            <div className="flex flex-wrap items-center gap-4 mt-3 text-xs" style={{ color: 'var(--text-muted)' }}>
              <span className="flex items-center gap-1"><Hash size={12} /> {text.split(/\s+/).filter(Boolean).length} words</span>
              <span className="flex items-center gap-1"><Type size={12} /> {text.length} chars</span>
              {result && (
                <>
                  <span className="flex items-center gap-1"><Clock size={12} /> {result.insights.reading_time_seconds}s read</span>
                  <span className="flex items-center gap-1"><Zap size={12} /> {result.inference_time_ms}ms</span>
                  <span className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                    Readability: {result.readability.complexity}
                  </span>
                  <span className="flex items-center gap-1 text-emerald-400 font-semibold ml-auto animate-pulse">
                    ✓ Auto-saved (ID: #{result.id})
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={handleDownload} disabled={!result} className="btn-accent flex items-center gap-2 text-sm">
              <Download size={16} /> Download Report
            </button>
            <button onClick={handleCopy} disabled={!result} className="btn-accent flex items-center gap-2 text-sm" style={{ background: copied ? 'rgba(16,185,129,0.12)' : 'rgba(99,102,241,0.12)', color: copied ? 'var(--positive)' : 'var(--accent-primary)', boxShadow: 'none' }}>
              <Copy size={16} /> {copied ? "Copied!" : "Copy Report"}
            </button>
            <button onClick={handleShare} disabled={!result} className="btn-accent flex items-center gap-2 text-sm" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--accent-primary)', boxShadow: 'none' }}>
              <Share2 size={16} /> Share
            </button>
          </div>

        </div>

        {/* ================= RIGHT — Advanced Rich Results ================= */}
        <div className="space-y-4">
          {!result && !isAnalyzing ? (
            <div className="glass-card p-12 flex flex-col items-center justify-center text-center text-gray-600 dark:text-gray-400" style={{ minHeight: 380 }}>
              <Brain size={48} className="mb-4 opacity-25" />
              <p className="text-lg font-semibold">Results will appear here</p>
              <p className="text-sm mt-1">Start typing or click the microphone to run real-time analysis</p>
            </div>
          ) : isAnalyzing && !result ? (
            <div className="glass-card p-6 space-y-4" style={{ minHeight: 380 }}>
              <div className="skeleton h-8 w-48" />
              <div className="skeleton h-4 w-full" />
              <div className="skeleton h-4 w-3/4" />
              <div className="skeleton h-32 w-full" />
            </div>
          ) : result ? (
            <AnimatePresence mode="wait">
              <motion.div
                key={result.sentiment + result.emotion + result.inference_time_ms}
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                {/* Custom Tab Bar */}
                <div className="flex flex-wrap items-center gap-1.5 bg-white/5 border border-white/10 p-1.5 rounded-xl">
                  {[
                    { id: 'overview', name: 'Overview', icon: Brain },
                    { id: 'emotions', name: 'Emotions', icon: Zap },
                    { id: 'sentences', name: 'Sentences', icon: Layers },
                    { id: 'metadata', name: 'Metadata & Entities', icon: Globe },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                          isActive
                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-white/5'
                        }`}
                      >
                        <Icon size={14} />
                        {tab.name}
                      </button>
                    );
                  })}
                </div>

                {/* Tab content rendering */}
                {activeTab === 'overview' && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                  >
                    {/* Sarcasm Flag Card */}
                    <div className={`glass-card p-4 border-l-4 ${result.sarcasm.detected ? 'border-amber-500 bg-amber-500/5' : 'border-emerald-500 bg-emerald-500/5'}`}>
                      <div className="flex items-center gap-2">
                        <AlertTriangle size={18} className={result.sarcasm.detected ? 'text-amber-500 animate-bounce' : 'text-emerald-500'} />
                        <span className="font-bold text-xs">
                          {result.sarcasm.detected ? '⚠️ Sarcasm Detected' : '✓ No Sarcasm Detected'}
                        </span>
                        {result.sarcasm.detected && (
                          <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">
                            {(result.sarcasm.confidence * 100).toFixed(0)}% confidence
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-gray-700 dark:text-gray-300 mt-1 leading-relaxed">
                        {result.sarcasm.reason}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Sentiment Card */}
                      <div className="glass-card p-4 flex flex-col justify-between">
                        <div>
                          <h3 className="text-xs font-bold mb-2 text-gray-500 dark:text-gray-400">
                            Sentiment
                          </h3>
                          <div className="flex items-center gap-2 mb-2">
                            <div className="text-xl font-bold capitalize" style={{ color: SENTIMENT_COLORS[result.sentiment] }}>
                              {result.sentiment}
                            </div>
                            <span className="text-sm font-bold text-gray-700 dark:text-gray-300">
                              {(result.sentiment_confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        {/* Bars */}
                        <div className="space-y-1">
                          {result.sentiment_distribution.map((d) => (
                            <div key={d.label} className="flex items-center gap-2">
                              <span className="text-[9px] capitalize w-12 text-gray-500 dark:text-gray-400">{d.label}</span>
                              <div className="flex-1 confidence-bar-bg h-1.5">
                                <motion.div
                                  className="confidence-bar-fill h-full"
                                  initial={{ width: 0 }}
                                  animate={{ width: `${(d.score * 100).toFixed(1)}%` }}
                                  style={{ background: SENTIMENT_COLORS[d.label] }}
                                />
                              </div>
                              <span className="text-[9px] font-medium w-8 text-right text-gray-700 dark:text-gray-300">
                                {(d.score * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Primary Emotion Circular radial gauge */}
                      <RadialGauge
                        value={result.emotion_confidence * 100}
                        color={EMOTION_COLORS[result.emotion] || '#6366f1'}
                        label={result.emotion}
                        emoji={result.emotion_emoji}
                      />
                    </div>

                    {/* AI Insights Summary Card */}
                    <div className="glass-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1.5">
                          <Brain size={16} style={{ color: 'var(--accent-primary)' }} />
                          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400">
                            AI Insights & Emotion Journey
                          </h3>
                        </div>
                        <button
                          onClick={toggleSpeech}
                          className={`p-1 rounded-full transition-colors ${isSpeaking ? 'bg-indigo-500 text-white animate-pulse' : 'hover:bg-white/10 text-gray-600 dark:text-gray-300'}`}
                          title="Read aloud"
                        >
                          <Volume2 size={14} />
                        </button>
                      </div>
                      <p className="text-[11px] leading-relaxed max-h-24 overflow-y-auto pr-1" style={{ color: 'var(--text-primary)' }}>
                        {result.insights.explanation}
                      </p>
                      <div className="grid grid-cols-2 gap-3 mt-3">
                        <div className="glass-card p-2 text-center" style={{ background: 'rgba(99,102,241,0.04)', borderRadius: '8px' }}>
                          <div className="text-sm font-bold" style={{ color: 'var(--accent-primary)' }}>
                            {result.insights.overall_sentiment_score > 0 ? '+' : ''}{result.insights.overall_sentiment_score}
                          </div>
                          <div className="text-[9px]" style={{ color: 'var(--text-muted)' }}>Score</div>
                        </div>
                        <div className="glass-card p-2 text-center" style={{ background: 'rgba(99,102,241,0.04)', borderRadius: '8px' }}>
                          <div className="text-sm font-bold" style={{ color: 'var(--accent-primary)' }}>
                            {result.insights.emotional_intensity}
                          </div>
                          <div className="text-[9px]" style={{ color: 'var(--text-muted)' }}>Intensity</div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'emotions' && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                    className="grid grid-cols-1 md:grid-cols-2 gap-4"
                  >
                    {/* Other Detected Emotions */}
                    <div className="glass-card p-4">
                      <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2.5">Other Detected Emotions</h3>
                      {result.secondary_emotions && result.secondary_emotions.length > 0 ? (
                        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                          {result.secondary_emotions.map((se) => (
                            <div key={se.label} className="bg-white/[0.02] hover:bg-white/[0.04] p-2.5 rounded-lg border border-white/5 transition-colors">
                              <div className="flex items-center justify-between mb-0.5">
                                <div className="flex items-center gap-1.5">
                                  <span className="text-base">{se.emoji}</span>
                                  <span className="text-[11px] font-semibold capitalize text-gray-800 dark:text-gray-200">{se.label}</span>
                                </div>
                                <span className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400">{(se.score * 100).toFixed(1)}%</span>
                              </div>
                              {se.explanation && (
                                <p className="text-[9px] text-gray-600 dark:text-gray-400 leading-snug italic">
                                  {se.explanation}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-[10px] text-gray-500 dark:text-gray-400 italic">No secondary emotions exceed the threshold.</span>
                      )}
                    </div>

                    {/* Top 3 Ranked Emotions Chart */}
                    <div className="glass-card p-4 flex flex-col justify-between">
                      <div>
                        <h3 className="text-xs font-bold mb-3 text-gray-500 dark:text-gray-400">
                          Emotion Distribution
                        </h3>
                        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                          {result.emotion_distribution.slice(0, 5).map((d) => (
                            <div key={d.label} className="flex items-center gap-2">
                              <span className="text-xs w-4">{EMOJI_MAP_JS[d.label] || '😐'}</span>
                              <span className="text-[10px] capitalize w-16 text-gray-700 dark:text-gray-300 font-medium truncate">{d.label}</span>
                              <div className="flex-1 confidence-bar-bg h-2">
                                <motion.div
                                  className="confidence-bar-fill h-full rounded"
                                  initial={{ width: 0 }}
                                  animate={{ width: `${(d.score * 100).toFixed(1)}%` }}
                                  style={{ background: EMOTION_COLORS[d.label] || '#6366f1' }}
                                />
                              </div>
                              <span className="text-[10px] font-bold w-8 text-right text-gray-700 dark:text-gray-300">
                                {(d.score * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'sentences' && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                  >
                    {/* Emotion Flow Timeline */}
                    <div className="glass-card p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Layers size={16} className="text-indigo-600 dark:text-indigo-400" />
                        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400">
                          Sentence Emotion Flow Timeline
                        </h3>
                      </div>
                      <div className="flex items-center gap-2 overflow-x-auto py-2 pr-2 border border-white/5 bg-white/5 rounded-lg px-3">
                        {result.timeline.map((emo, index) => (
                          <div key={index} className="flex items-center gap-2 shrink-0">
                            {index > 0 && <span className="text-gray-600 dark:text-gray-400 font-bold text-xs">→</span>}
                            <motion.div
                              initial={{ scale: 0.9 }}
                              animate={{ scale: 1 }}
                              className="px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 text-[10px] font-medium"
                              style={{
                                background: (EMOTION_COLORS[emo] || '#6366f1') + '15',
                                border: `1px solid ${(EMOTION_COLORS[emo] || '#6366f1')}40`,
                                color: EMOTION_COLORS[emo] || 'var(--text-primary)',
                              }}
                            >
                              <span>{EMOJI_MAP_JS[emo] || '😐'}</span>
                              <span className="capitalize">{emo}</span>
                            </motion.div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Sentence-by-Sentence Breakdown Table */}
                    <div className="glass-card p-4">
                      <h3 className="text-xs font-bold mb-3 text-gray-500 dark:text-gray-400">
                        Sentence Breakdown
                      </h3>
                      <div className="max-h-60 overflow-y-auto pr-1">
                        <table className="w-full text-left text-[11px] border-collapse">
                          <thead>
                            <tr className="border-b border-white/10 text-gray-500 dark:text-gray-400">
                              <th className="py-2 font-semibold">Sentence</th>
                              <th className="py-2 px-3 font-semibold w-24">Sentiment</th>
                              <th className="py-2 font-semibold w-24">Dominant Emotion</th>
                            </tr>
                          </thead>
                          <tbody>
                            {result.sentences.map((s, idx) => (
                              <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                <td className="py-2 text-gray-800 dark:text-gray-300 pr-4 italic leading-relaxed max-w-md break-words">
                                  {highlightWords(s.text, result.keywords.positive_words, result.keywords.negative_words)}
                                </td>
                                <td className="py-2 px-3">
                                  <span
                                    className="font-semibold capitalize text-[10px] px-1.5 py-0.5 rounded"
                                    style={{
                                      background: (SENTIMENT_COLORS[s.sentiment] || '#f59e0b') + '15',
                                      color: SENTIMENT_COLORS[s.sentiment] || '#f59e0b',
                                      border: `1px solid ${(SENTIMENT_COLORS[s.sentiment] || '#f59e0b')}30`
                                    }}
                                  >
                                    {s.sentiment} · {(s.sentiment_confidence * 100).toFixed(0)}%
                                  </span>
                                </td>
                                <td className="py-2">
                                  <span className="flex items-center gap-1 capitalize font-medium text-gray-800 dark:text-gray-200">
                                    <span>{s.emotion_emoji || EMOJI_MAP_JS[s.emotion] || '😐'}</span>
                                    <span>{s.emotion}</span>
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'metadata' && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Language Detection */}
                      <div className="glass-card p-4">
                        <div className="flex items-center gap-2">
                          <Globe size={14} style={{ color: 'var(--accent-primary)' }} />
                          <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400">Language Detection</h3>
                        </div>
                        <div className="flex items-center gap-2.5 mt-2.5">
                          <span className="text-xl">{result.language.flag}</span>
                          <div>
                            <div className="text-xs font-bold text-gray-800 dark:text-gray-200">{result.language.name}</div>
                            <div className="text-[9px] text-gray-500 dark:text-gray-400">
                              {result.language.code.toUpperCase()} · {(result.language_confidence * 100).toFixed(1)}% confidence
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Named Entities (NER) */}
                      <div className="glass-card p-4">
                        <div className="flex items-center gap-2">
                          <Tag size={14} style={{ color: 'var(--accent-primary)' }} />
                          <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400">Named Entities (NER)</h3>
                        </div>
                        <div className="mt-2.5 space-y-1.5 max-h-24 overflow-y-auto pr-1">
                          {Object.entries(result.entities).some(([_, vals]) => vals.length > 0) ? (
                            Object.entries(result.entities).map(([type, values]) => {
                              if (values.length === 0) return null;
                              return (
                                <div key={type} className="flex flex-wrap items-center gap-1">
                                  <span className="text-[8px] font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-300 bg-indigo-500/10 px-1 py-0.5 rounded">
                                    {type}:
                                  </span>
                                  {values.map((v, idx) => (
                                    <span key={idx} className="text-[9px] text-gray-800 dark:text-gray-300 bg-white/5 border border-white/10 px-1.5 py-0.5 rounded font-medium">
                                      {v}
                                    </span>
                                  ))}
                                </div>
                              );
                            })
                          ) : (
                            <span className="text-[9px] text-gray-500 dark:text-gray-400 italic">No named entities detected.</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Word Cloud */}
                    {result.keywords.word_cloud.length > 0 && (
                      <div className="glass-card p-4">
                        <h3 className="text-xs font-semibold mb-2.5 text-gray-500 dark:text-gray-400">
                          Word Cloud
                        </h3>
                        <div className="flex flex-wrap gap-1">
                          {result.keywords.word_cloud.slice(0, 25).map((w, i) => {
                            const isPositive = result.keywords.positive_words.some(p => p.word === w.text);
                            const isNegative = result.keywords.negative_words.some(n => n.word === w.text);
                            const cls = isPositive ? 'word-tag-positive' : isNegative ? 'word-tag-negative' : 'word-tag-neutral';
                            return (
                              <span key={i} className={`word-tag ${cls}`} style={{ fontSize: `${Math.min(1.0, 0.7 + w.value * 0.06)}rem`, padding: '2px 6px' }}>
                                {w.text}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </motion.div>
            </AnimatePresence>
          ) : null}
        </div>
      </div>
    </div>
  );
};
