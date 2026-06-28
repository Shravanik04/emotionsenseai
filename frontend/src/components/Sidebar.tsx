import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileText, Upload, History, BarChart2, LogOut, Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Analyze Text', path: '/analyze', icon: FileText },
  { name: 'Batch Analysis', path: '/upload', icon: Upload },
  { name: 'History', path: '/history', icon: History },
  { name: 'Stats', path: '/stats', icon: BarChart2 },
];

export const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isDark, toggle } = useTheme();

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('userEmail');
    navigate('/login');
  };

  return (
    <div
      className="glass-sidebar fixed flex flex-col h-screen z-50"
      style={{ width: 'var(--sidebar-width)' }}
    >
      {/* Logo */}
      <div className="p-6" style={{ borderBottom: '1px solid var(--border-glass)' }}>
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg"
            style={{ background: 'var(--accent-gradient)' }}
          >
            S
          </div>
          <div>
            <h1 className="text-lg font-bold" style={{ color: 'var(--accent-primary)' }}>
              SentimentScope
            </h1>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              AI Sentiment & Emotion
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center gap-2.5 py-2.5 px-3 rounded-xl transition-all duration-200"
              style={{
                background: isActive ? 'var(--accent-gradient)' : 'transparent',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 400,
                boxShadow: isActive ? '0 4px 12px rgba(99, 102, 241, 0.25)' : 'none',
              }}
            >
              <Icon size={18} />
              <span className="text-sm">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom controls */}
      <div className="p-4 space-y-2" style={{ borderTop: '1px solid var(--border-glass)' }}>
        {/* Dark / Light toggle */}
        <button
          onClick={toggle}
          className="flex items-center gap-3 p-3 w-full rounded-xl transition-all duration-200 cursor-pointer"
          style={{ color: 'var(--text-secondary)' }}
        >
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
          <span className="font-medium">{isDark ? 'Light Mode' : 'Dark Mode'}</span>
        </button>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 p-3 w-full rounded-xl transition-all duration-200 cursor-pointer"
          style={{ color: '#ef4444' }}
        >
          <LogOut size={20} />
          <span className="font-medium">Log Out</span>
        </button>
      </div>
    </div>
  );
};
