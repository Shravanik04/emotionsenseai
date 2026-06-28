interface StatCardProps {
  title: string;
  value: string | number;
  color: string;
}

export const StatCard = ({ title, value, color }: StatCardProps) => (
  <div className="glass-card p-5" style={{ borderLeft: `4px solid ${color.replace('border-', '').replace('blue-500', '#6366f1').replace('green-500', '#10b981').replace('red-500', '#ef4444').replace('yellow-500', '#f59e0b').replace('purple-500', '#8b5cf6')}` }}>
    <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{title}</p>
    <p className="text-2xl font-bold mt-1" style={{ color: 'var(--text-primary)' }}>{value}</p>
  </div>
);
