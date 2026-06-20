export interface SentimentResponse {
  id: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  processed_timestamp: string;
}

export interface BatchSummary {
  total_rows: number;
  processed_rows: number;
  skipped_rows: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  average_confidence: number;
  errors: string[];
}

export interface HistoryItem {
  id: number;
  text_preview: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  source_type: string;
  created_at: string;
}

export interface StatsResponse {
  total_analyses: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  recent_activity: HistoryItem[];
}