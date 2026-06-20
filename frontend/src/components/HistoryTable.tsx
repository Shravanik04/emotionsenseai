import type { HistoryItem } from '../types';
import { SentimentBadge } from './SentimentBadge';

export const HistoryTable = ({ items }: { items: HistoryItem[] }) => (
  <div className="bg-white rounded-xl shadow-sm overflow-hidden">
    <table className="w-full text-left border-collapse">
      <thead className="bg-gray-50 border-b">
        <tr>
          <th className="p-4 font-medium text-gray-600">Text Preview</th>
          <th className="p-4 font-medium text-gray-600">Sentiment</th>
          <th className="p-4 font-medium text-gray-600">Confidence</th>
          <th className="p-4 font-medium text-gray-600">Source</th>
          <th className="p-4 font-medium text-gray-600">Date</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.id} className="border-b hover:bg-gray-50">
            <td className="p-4 text-sm text-gray-700">{item.text_preview}</td>
            <td className="p-4"><SentimentBadge sentiment={item.sentiment} /></td>
            <td className="p-4 text-sm text-gray-700">{(item.confidence * 100).toFixed(2)}%</td>
            <td className="p-4 text-sm text-gray-700 capitalize">{item.source_type}</td>
            <td className="p-4 text-sm text-gray-700">{new Date(item.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
