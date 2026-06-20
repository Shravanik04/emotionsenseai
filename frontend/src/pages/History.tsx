import { useEffect, useState } from 'react';
import { getHistory } from '../services/api';
import type { HistoryItem } from '../types';
import { HistoryTable } from '../components/HistoryTable';
import { Loader } from '../components/Loader';
import { EmptyState } from '../components/EmptyState';

export const History = () => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sentiment, setSentiment] = useState('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      getHistory(sentiment, search).then(setItems).finally(() => setLoading(false));
    }, 300); // Debounce
    return () => clearTimeout(timer);
  }, [sentiment, search]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">History</h1>
      <div className="flex gap-4 mb-6">
        <input
          type="text"
          placeholder="Search text..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
        />
        <select 
          value={sentiment} 
          onChange={(e) => setSentiment(e.target.value)}
          className="p-2 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
        >
          <option value="all">All Sentiments</option>
          <option value="positive">Positive</option>
          <option value="negative">Negative</option>
          <option value="neutral">Neutral</option>
        </select>
      </div>
      {loading ? <Loader /> : items.length === 0 ? <EmptyState message="No records found." /> : <HistoryTable items={items} />}
    </div>
  );
};