import axios from 'axios';
import type { FullAnalysisWithId, BatchSummary, HistoryItem, StatsResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// REST: full analysis (persists to DB)
export const analyzeText = async (text: string): Promise<FullAnalysisWithId> => {
  const { data } = await api.post('/analyze-text', { text });
  return data;
};

// REST: lightweight real-time analysis (no DB)
export const analyzeRealtime = async (text: string) => {
  const { data } = await api.post('/analyze-realtime', { text });
  return data;
};

// Batch upload
export const analyzeBatch = async (file: File): Promise<BatchSummary> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/analyze-batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

// History
export const getHistory = async (
  sentiment?: string,
  search?: string,
  emotion?: string,
  language?: string,
  sarcasm?: string
): Promise<HistoryItem[]> => {
  const params: any = {};
  if (sentiment && sentiment !== 'all') params.sentiment = sentiment;
  if (search) params.search = search;
  if (emotion && emotion !== 'all') params.emotion = emotion;
  if (language && language !== 'all') params.language = language;
  if (sarcasm && sarcasm !== 'all') params.sarcasm = sarcasm;
  const { data } = await api.get('/history', { params });
  return data;
};

// Stats
export const getStats = async (): Promise<StatsResponse> => {
  const { data } = await api.get('/stats');
  return data;
};

// Export CSV
export const getExportUrl = () => `${API_BASE_URL}/export`;

// WebSocket URL builder
export const getWebSocketUrl = (): string => {
  const base = API_BASE_URL.replace(/^http/, 'ws');
  return `${base}/ws`;
};