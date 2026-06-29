import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, LogIn, AlertCircle, Sun, Moon } from 'lucide-react';
import { GhostCursor } from '../components/GhostCursor';
import { useTheme } from '../contexts/ThemeContext';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { isDark, toggle } = useTheme();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }
    
    // Very basic email format check
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);

    // Simulate network delay for premium feel loading spinner
    setTimeout(() => {
      setIsLoading(false);
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('userEmail', email);
      navigate('/');
    }, 1000);
  };

  return (
    <div className="relative w-full min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center overflow-hidden font-sans select-none transition-colors duration-300">
      
      {/* Background radial gradient glows */}
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-purple-500/10 dark:bg-purple-500/10 rounded-full blur-[120px] pointer-events-none transition-colors duration-300" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-indigo-500/10 dark:bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none transition-colors duration-300" />
      
      {/* GhostCursor Animation Trail */}
      <GhostCursor
        color={isDark ? "#d8b4fe" : "#8b5cf6"} // lighter purple trail for dark, vibrant purple for light
        brightness={isDark ? 0.55 : 0.45}
        trailLength={16}
        inertia={0.35}
        grainIntensity={0.03}
        bloomStrength={isDark ? 0.25 : 0.18}
        bloomRadius={0.8}
        bloomThreshold={0.01}
        fadeDelayMs={100}
        fadeDurationMs={800}
        zIndex={1}
        mixBlendMode={isDark ? 'screen' : 'normal'}
      />

      {/* Theme Toggle Button */}
      <button
        onClick={toggle}
        type="button"
        className="absolute top-6 right-6 p-3 rounded-xl border border-slate-200 bg-white/80 backdrop-blur-xl text-slate-800 hover:bg-slate-100 hover:border-slate-300 transition-all duration-200 shadow-md cursor-pointer dark:border-white/10 dark:bg-white/[0.03] dark:text-white dark:hover:bg-white/[0.08] dark:hover:border-white/20"
        aria-label="Toggle Theme"
      >
        {isDark ? (
          <Sun size={20} className="text-yellow-500 animate-pulse" />
        ) : (
          <Moon size={20} className="text-indigo-600" />
        )}
      </button>

      {/* Main glassmorphism login card */}
      <div className="relative z-10 w-full max-w-md mx-4 p-8 rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white/70 dark:bg-white/[0.03] backdrop-blur-xl shadow-2xl shadow-purple-500/5 dark:shadow-purple-500/2 transition-all duration-300 hover:border-slate-300 dark:hover:border-white/15">
        
        {/* Branding header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-gradient-to-tr from-purple-500/10 to-indigo-500/10 border border-purple-500/20 dark:border-purple-400/30 mb-3">
            <span className="text-2xl font-bold bg-gradient-to-r from-purple-500 to-indigo-500 dark:from-purple-300 dark:to-indigo-300 bg-clip-text text-transparent">SS</span>
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white transition-colors duration-300">
            Welcome to <span className="bg-gradient-to-r from-purple-500 to-indigo-500 dark:from-purple-300 dark:to-indigo-300 bg-clip-text text-transparent font-black">SentimentScope</span>
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 transition-colors duration-300">
            AI-powered text and CSV sentiment analysis
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-200 text-sm flex items-start gap-2 animate-shake transition-colors duration-300">
            <AlertCircle size={18} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          {/* Email input field */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 block transition-colors duration-300">
              Email Address
            </label>
            <div className="relative group">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 group-focus-within:text-purple-500 dark:group-focus-within:text-purple-400 transition-colors">
                <Mail size={18} />
              </span>
              <input
                type="email"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Password input field */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 block transition-colors duration-300">
                Password
              </label>
              <a href="#" className="text-xs font-medium text-purple-600 dark:text-purple-400 hover:text-purple-500 dark:hover:text-purple-300 transition-colors">
                Forgot password?
              </a>
            </div>
            <div className="relative group">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 group-focus-within:text-purple-500 dark:group-focus-within:text-purple-400 transition-colors">
                <Lock size={18} />
              </span>
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-12 pr-12 py-3 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 hover:text-purple-500 dark:hover:text-purple-400 transition-colors"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Remember me checkbox */}
          <div className="flex items-center">
            <input
              id="remember-me"
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900/50 text-purple-600 focus:ring-purple-500/20 focus:ring-offset-white dark:focus:ring-offset-slate-950 transition-colors cursor-pointer"
            />
            <label htmlFor="remember-me" className="ml-2 text-xs text-slate-600 dark:text-slate-400 cursor-pointer select-none transition-colors duration-300">
              Remember this device
            </label>
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading}
            className="relative overflow-hidden w-full py-3 px-4 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-400 hover:to-indigo-400 active:scale-[0.98] transition-all duration-200 text-white font-semibold text-sm shadow-lg shadow-purple-500/10 flex items-center justify-center gap-2 group cursor-pointer"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>Sign In</span>
                <LogIn size={16} className="group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="text-center mt-6">
          <p className="text-xs text-slate-500">
            Don't have an account?{' '}
            <a href="#" className="font-semibold text-purple-600 dark:text-purple-400 hover:text-purple-500 dark:hover:text-purple-300 transition-colors">
              Create an account
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
