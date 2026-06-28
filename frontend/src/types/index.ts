// ---- Sentiment ----
export interface ProbabilityItem {
  label: string;
  score: number;
}

export interface SentimentResponse {
  id: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  processed_timestamp: string;
}

// ---- Keywords ----
export interface KeywordItem {
  word: string;
  count: number;
}

export interface WordCloudItem {
  text: string;
  value: number;
}

export interface KeywordsResult {
  top_keywords: KeywordItem[];
  positive_words: KeywordItem[];
  negative_words: KeywordItem[];
  word_cloud: WordCloudItem[];
  word_frequencies: KeywordItem[];
}

// ---- Language ----
export interface LanguageInfo {
  code: string;
  name: string;
  flag: string;
}

// ---- AI Insights ----
export interface InsightsResult {
  overall_sentiment_score: number;
  dominant_emotion: string;
  dominant_emotion_emoji: string;
  emotional_intensity: string;
  explanation: string;
  word_count: number;
  char_count: number;
  reading_time_seconds: number;
}

export interface SarcasmResult {
  detected: boolean;
  confidence: number;
  reason: string;
}

export interface ReadabilityResult {
  score: number;
  complexity: string;
}

export interface SentenceAnalysisItem {
  text: string;
  sentiment: string;
  sentiment_confidence: number;
  emotion: string;
  emotion_confidence: number;
  emotion_emoji: string;
  sarcasm: SarcasmResult;
}

// ---- Full Analysis (real-time + REST) ----
export interface FullAnalysisResult {
  sentiment: string;
  sentiment_confidence: number;
  sentiment_distribution: ProbabilityItem[];
  emotion: string;
  emotion_confidence: number;
  emotion_emoji: string;
  emotion_distribution: ProbabilityItem[];
  language: LanguageInfo;
  language_confidence: number;
  keywords: KeywordsResult;
  insights: InsightsResult;
  inference_time_ms: number;
  processing_time_ms?: number;
  word_count: number;
  char_count: number;
  cache_hit: boolean;
  sarcasm: SarcasmResult;
  readability: ReadabilityResult;
  entities: Record<string, string[]>;
  sentences: SentenceAnalysisItem[];
  timeline: string[];
  id?: number;
  processed_timestamp?: string;
  emotion_ranking?: ProbabilityItem[];
  mixed_sentiment?: boolean;
  positive_score?: number;
  negative_score?: number;
  neutral_score?: number;
  contradictory_emotions?: string[];
  emotion_summary?: string;
  emotion_confidences?: Record<string, number>;
  top_emotions?: string[];
  primary_emotion?: { label: string; score: number; emoji: string; explanation: string };
  secondary_emotions?: Array<{ label: string; score: number; emoji: string; explanation: string }>;
  emotion_explanations?: Record<string, string>;
  error?: string;
}

export interface FullAnalysisWithId extends FullAnalysisResult {
  id: number;
  processed_timestamp: string;
}

// ---- Batch ----
export interface BatchSummary {
  total_rows: number;
  processed_rows: number;
  skipped_rows: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  average_confidence: number;
  emotion_counts: Record<string, number>;
  errors: string[];
}

// ---- History ----
export interface HistoryItem {
  id: number;
  text_preview: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  source_type: string;
  created_at: string;
  emotion?: string;
  emotion_confidence?: number;
  language_name?: string;
  sarcasm_detected?: boolean;
  sarcasm_confidence?: number;
  sarcasm_reason?: string;
  language_code?: string;
}

// ---- Stats ----
export interface StatsResponse {
  total_analyses: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  emotion_counts: Record<string, number>;
  recent_activity: HistoryItem[];
}