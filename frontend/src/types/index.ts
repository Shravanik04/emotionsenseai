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
  aspect?: string;
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

// ---- Social Media Analyzer ----
export interface SocialAnalyzeRequest {
  platform: string;
  text: string;
}

export interface SocialAnalyzeResponse {
  id: number;
  user_id: number;
  platform: string;
  original_text: string;
  detected_language?: string;
  language_code?: string;
  emotion?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  confidence?: number;
  sarcasm_detected: boolean;
  sarcasm_confidence?: number;
  sarcasm_reason?: string;
  processing_time_ms?: number;
  inference_time_ms?: number;
  aspect?: string;
  batch_run_id?: number;
  created_at: string;
}


export interface SocialBatchRequest {
  platform: string;
  text: string;
}

export interface KeywordExtractorItem {
  word: string;
  count: number;
}

export interface KeywordsSummary {
  positive_keywords: KeywordExtractorItem[];
  negative_keywords: KeywordExtractorItem[];
  most_frequent: KeywordExtractorItem[];
  most_emotional: KeywordExtractorItem[];
}

export interface AspectSentimentItem {
  aspect: string;
  positive: number;
  negative: number;
  neutral: number;
}

export interface BusinessInsights {
  total_count: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
  mixed_percentage: number;
  dominant_emotion: string;
  dominant_emotion_emoji: string;
  top_praises: string[];
  top_complaints: string[];
  recommendations: string[];
  aspect_sentiment_table: AspectSentimentItem[];
  executive_summary: string;
}


export interface SocialBatchResponse {
  total_processed: number;
  average_confidence: number;
  sarcasm_rate: number;
  sentiment_distribution: Record<string, number>;
  emotion_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  sarcasm_distribution: Record<string, number>;
  average_processing_time_ms: number;
  average_inference_time_ms: number;
  keywords: KeywordsSummary;
  insights: BusinessInsights;
  results: SocialAnalyzeResponse[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  email: string;
  user_id: number;
}

// ---- Customer Feedback Intelligence Platform ----
export interface BatchAnalysisRun {
  id: number;
  user_id: number;
  platform: string;
  total_processed: number;
  average_confidence: number;
  sarcasm_rate: number;
  sentiment_distribution: Record<string, number>;
  emotion_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  sarcasm_distribution: Record<string, number>;
  keywords_summary: KeywordsSummary;
  aspect_sentiment_table: AspectSentimentItem[];
  executive_summary: string;
  recommendations: string[];
  processing_time_ms?: number;
  inference_time_ms?: number;
  created_at: string;
}

export interface DashboardStatsResponse {
  total_comments: number;
  customer_satisfaction_score: number;
  overall_health_score: number;
  average_confidence: number;
  sarcasm_rate: number;
  average_processing_time_ms: number;
  sentiment_distribution: Record<string, number>;
  emotion_distribution: Record<string, number>;
  recent_runs: BatchAnalysisRun[];
}

export interface StatisticsResponse {
  sentiment_distribution: Record<string, number>;
  emotion_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  sarcasm_distribution: Record<string, number>;
  confidence_intervals: Record<string, number>;
  processing_time_avg: number;
  sarcasm_rate: number;
}

export interface AspectAnalyticsResponse {
  aspect_sentiment_table: AspectSentimentItem[];
  top_praises: string[];
  top_complaints: string[];
}

export interface BusinessInsightsResponse {
  executive_summary: string;
  recommendations: string[];
  total_processed: number;
  csat: number;
  ohs: number;
}

export interface ReviewsBatchRequest {
  platform: string;
  text: string;
}