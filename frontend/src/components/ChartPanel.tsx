import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface ChartPanelProps {
  positive: number;
  negative: number;
  neutral: number;
}

export const ChartPanel = ({ positive, negative, neutral }: ChartPanelProps) => {
  const data = [
    { name: 'Positive', value: positive, color: '#10b981' },
    { name: 'Negative', value: negative, color: '#ef4444' },
    { name: 'Neutral', value: neutral, color: '#f59e0b' },
  ];

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm h-80">
      <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
