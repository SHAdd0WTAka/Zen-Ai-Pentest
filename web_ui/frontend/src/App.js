/**
 * Zen AI Pentest Dashboard
 * React Frontend v2.1.0
 * Q2 2026 Feature
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { 
  ShieldCheckIcon, 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  CogIcon,
  BellIcon,
  DocumentTextIcon,
  UserIcon
} from '@heroicons/react/24/outline';

// Pages
import Dashboard from './pages/Dashboard';
import Scans from './pages/Scans';
import Findings from './pages/Findings';
import Reports from './pages/Reports';
import SIEM from './pages/SIEM';
import Settings from './pages/Settings';
import Login from './pages/Login';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check for existing session
  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const role = localStorage.getItem('role');
    
    if (token && username) {
      setUser({ username, role, token });
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Sidebar */}
        <nav className="fixed left-0 top-0 h-full w-64 bg-slate-900 text-white">
          <div className="p-6">
            <h1 className="text-xl font-bold flex items-center gap-2">
              <ShieldCheckIcon className="w-8 h-8 text-emerald-400" />
              Zen AI Pentest
            </h1>
            <p className="text-xs text-slate-400 mt-1">v2.1.0</p>
          </div>
          
          <div className="px-4 py-2">
            <NavItem to="/" icon={ChartBarIcon} label="Dashboard" />
            <NavItem to="/scans" icon={MagnifyingGlassIcon} label="Scans" />
            <NavItem to="/findings" icon={ShieldCheckIcon} label="Findings" />
            <NavItem to="/reports" icon={DocumentTextIcon} label="Reports" />
            <NavItem to="/siem" icon={BellIcon} label="SIEM" />
            <NavItem to="/settings" icon={CogIcon} label="Settings" />
          </div>
          
          {/* User Info */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
            <div className="flex items-center gap-2 mb-3">
              <UserIcon className="w-5 h-5 text-slate-400" />
              <div>
                <p className="text-sm font-medium text-white">{user.username}</p>
                <p className="text-xs text-slate-400 capitalize">{user.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full text-left text-sm text-red-400 hover:text-red-300 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </nav>
        
        {/* Main Content */}
        <main className="ml-64 p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scans" element={<Scans />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/siem" element={<SIEM />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/login" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function NavItem({ to, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
          isActive
            ? 'bg-emerald-600 text-white'
            : 'text-slate-300 hover:bg-slate-800'
        }`
      }
    >
      <Icon className="w-5 h-5" />
      {label}
    </NavLink>
  );
}

export default App;
