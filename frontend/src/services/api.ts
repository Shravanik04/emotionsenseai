import axios from 'axios';
import type { 
  FullAnalysisWithId, 
  BatchSummary, 
  HistoryItem, 
  StatsResponse,
  SocialAnalyzeResponse,
  SocialBatchResponse,
  TokenResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Axios request interceptor for JWT authentication
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
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
  sarcasm?: string,
  showDeleted?: boolean
): Promise<HistoryItem[]> => {
  const params: any = {};
  if (sentiment && sentiment !== 'all') params.sentiment = sentiment;
  if (search) params.search = search;
  if (emotion && emotion !== 'all') params.emotion = emotion;
  if (language && language !== 'all') params.language = language;
  if (sarcasm && sarcasm !== 'all') params.sarcasm = sarcasm;
  if (showDeleted !== undefined) params.show_deleted = showDeleted;
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

export const exportData = async (): Promise<Blob> => {
  const { data } = await api.get('/export', { responseType: 'blob' });
  return data;
};

// WebSocket URL builder
export const getWebSocketUrl = (): string => {
  const base = API_BASE_URL.replace(/^http/, 'ws');
  return `${base}/ws`;
};

// Authentication login
export const login = async (email: string, password: string): Promise<TokenResponse> => {
  const { data } = await api.post('/auth/login', { email, password });
  return data;
};

// Social single analysis
export const analyzeSocialSingle = async (platform: string, text: string): Promise<SocialAnalyzeResponse> => {
  const { data } = await api.post('/social/analyze', { platform, text });
  return data;
};

// Social batch analysis
export const analyzeSocialBatch = async (platform: string, text: string): Promise<SocialBatchResponse> => {
  const { data } = await api.post('/social/batch', { platform, text });
  return data;
};

// Social history list with sorting, filtering, and trash view support
export const getSocialHistory = async (filters?: {
  platform?: string;
  emotion?: string;
  sentiment?: string;
  language?: string;
  aspect?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
  min_confidence?: number;
  max_confidence?: number;
  show_deleted?: boolean;
  sort_by?: string;
  order?: string;
}): Promise<SocialAnalyzeResponse[]> => {
  const { data } = await api.get('/social/history', { params: filters });
  return data;
};

// Social history detail
export const getSocialHistoryDetail = async (id: number): Promise<SocialAnalyzeResponse> => {
  const { data } = await api.get(`/social/history/${id}`);
  return data;
};

// Social record delete (supports permanent parameter)
export const deleteSocialRecord = async (id: number, permanent = false): Promise<{ message: string }> => {
  const { data } = await api.delete(`/social/${id}`, { params: { permanent } });
  return data;
};

// Social record restore from trash
export const restoreSocialRecord = async (id: number): Promise<{ message: string }> => {
  const { data } = await api.post(`/social/${id}/restore`);
  return data;
};

// Download PDF report
export const downloadReport = async (analysisId: number): Promise<Blob> => {
  const { data } = await api.get(`/report/${analysisId}`, {
    responseType: 'blob'
  });
  return data;
};

// Delete sentiment history record (supports permanent parameter)
export const deleteHistoryRecord = async (recordId: number, permanent = false): Promise<{ status: string; message: string }> => {
  const { data } = await api.delete(`/history/${recordId}`, { params: { permanent } });
  return data;
};

// Restore sentiment history record from trash
export const restoreHistoryRecord = async (recordId: number): Promise<{ status: string; message: string }> => {
  const { data } = await api.post(`/history/${recordId}/restore`);
  return data;
};

// Dashboard Stats
export const getDashboardStats = async (): Promise<any> => {
  const { data } = await api.get('/dashboard');
  return data;
};

// Statistics Breakdown
export const getStatisticsBreakdown = async (batchRunId?: number): Promise<any> => {
  const { data } = await api.get('/statistics', { params: { batch_run_id: batchRunId } });
  return data;
};

// Aspect Analytics
export const getAspectAnalytics = async (batchRunId?: number): Promise<any> => {
  const { data } = await api.get('/aspects', { params: { batch_run_id: batchRunId } });
  return data;
};

// Business Insights
export const getBusinessInsights = async (batchRunId?: number): Promise<any> => {
  const { data } = await api.get('/business', { params: { batch_run_id: batchRunId } });
  return data;
};

// Reviews list analysis upload
export const analyzeReviewsBatch = async (text: string, platform = 'reviews'): Promise<SocialBatchResponse> => {
  const { data } = await api.post('/reviews', { platform, text });
  return data;
};