import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

export const MainLayout = () => (
  <div className="flex">
    <Sidebar />
    <div className="flex-1 ml-64 p-8 bg-gray-50 min-h-screen">
      <Outlet />
    </div>
  </div>
);