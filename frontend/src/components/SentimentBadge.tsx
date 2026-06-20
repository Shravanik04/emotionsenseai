import type { HistoryItem } from '../types';

export const SentimentBadge = ({ sentiment }: { sentiment: HistoryItem['sentiment'] }) => {
  const colors = {
    positive: 'bg-green-100 text-green-800',
    negative: 'bg-red-100 text-red-800',
    neutral: 'bg-yellow-100 text-yellow-800',
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[sentiment]}`}>
      {sentiment.toUpperCase()}
    </span>
  );
};