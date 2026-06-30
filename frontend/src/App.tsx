import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { AnalyzeText } from './pages/AnalyzeText';
import { UploadCSV } from './pages/UploadCSV';
import { History } from './pages/History';
import { Stats } from './pages/Stats';
import { Login } from './pages/Login';
import { SocialAnalyzer } from './pages/SocialAnalyzer';

const ProtectedRoute = () => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyze" element={<AnalyzeText />} />
            <Route path="/upload" element={<UploadCSV />} />
            <Route path="/history" element={<History />} />
            <Route path="/stats" element={<Stats />} />
            <Route path="/social" element={<SocialAnalyzer />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}


export default App;