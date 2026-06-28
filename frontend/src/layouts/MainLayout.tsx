import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

export const MainLayout = () => (
  <div className="flex min-h-screen" style={{ background: 'var(--bg-primary)' }}>
    <Sidebar />
    <div
      className="flex-1 p-6 md:p-8 transition-all duration-300"
      style={{ marginLeft: 'var(--sidebar-width)', color: 'var(--text-primary)' }}
    >
      <Outlet />
    </div>
  </div>
);