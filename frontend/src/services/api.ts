import axios from 'axios';
import type { SentimentResponse, BatchSummary, HistoryItem, StatsResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const analyzeText = async (text: string): Promise<SentimentResponse> => {
  const { data } = await api.post('/analyze-text', { text });
  return data;
};

export const analyzeBatch = async (file: File): Promise<BatchSummary> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/analyze-batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getHistory = async (sentiment?: string, search?: string): Promise<HistoryItem[]> => {
  const params: any = {};
  if (sentiment && sentiment !== 'all') params.sentiment = sentiment;
  if (search) params.search = search;
  const { data } = await api.get('/history', { params });
  return data;
};

export const getStats = async (): Promise<StatsResponse> => {
  const { data } = await api.get('/stats');
  return data;
};

export const getExportUrl = () => `${API_BASE_URL}/export`;