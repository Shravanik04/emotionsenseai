import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, Upload, History, BarChart2 } from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Analyze Text', path: '/analyze', icon: FileText },
  { name: 'Upload CSV', path: '/upload', icon: Upload },
  { name: 'History', path: '/history', icon: History },
  { name: 'Stats', path: '/stats', icon: BarChart2 },
];

export const Sidebar = () => {
  const location = useLocation();
  
  return (
    <div className="w-64 bg-white h-screen border-r fixed flex flex-col">
      <div className="p-6 border-b">
        <h1 className="text-xl font-bold text-blue-600">SentimentScope</h1>
        <p className="text-xs text-gray-500">AI Sentiment Analyzer</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 p-3 rounded-lg transition-colors
              ${isActive ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <Icon size={20} />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
};
