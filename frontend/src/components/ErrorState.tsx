export const ErrorState = ({ message }: { message: string }) => (
  <div className="glass-card p-8 text-center" style={{ borderColor: 'var(--negative)' }}>
    <p className="font-semibold" style={{ color: 'var(--negative)' }}>Error</p>
    <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>{message}</p>
  </div>
);