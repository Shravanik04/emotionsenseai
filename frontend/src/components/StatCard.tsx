interface StatCardProps {
  title: string;
  value: number | string;
  color: string;
}

export const StatCard = ({ title, value, color }: StatCardProps) => (
  <div className={`bg-white p-6 rounded-xl shadow-sm border-l-4 ${color}`}>
    <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
    <p className="text-3xl font-bold mt-2 text-gray-800">{value}</p>
  </div>
);
