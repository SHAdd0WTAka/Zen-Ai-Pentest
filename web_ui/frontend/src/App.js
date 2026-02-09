/**
 * Zen AI Pentest Dashboard
 * React Frontend v2.1.0
 * Q2 2026 Feature
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { 
  ShieldCheckIcon, 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  CogIcon,
  BellIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

// Pages
import Dashboard from './pages/Dashboard';
import Scans from './pages/Scans';
import Findings from './pages/Findings';
import Reports from './pages/Reports';
import SIEM from './pages/SIEM';
import Settings from './pages/Settings';

function App() {
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
          
          {/* System Status */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
              <span className="text-slate-300">System Online</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">API v1.0 Connected</p>
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
