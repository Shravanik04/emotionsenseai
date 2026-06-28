export const EmptyState = ({ message }: { message: string }) => (
  <div className="glass-card p-12 text-center" style={{ color: 'var(--text-muted)' }}>
    <p className="text-lg font-medium">{message}</p>
  </div>
);
