import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { 
  LayoutDashboard, 
  ScanLine, 
  ShieldAlert, 
  Settings, 
  LogOut,
  PlusCircle,
  Calendar,
  MessageSquare
} from 'lucide-react';
import './Layout.css';

function Layout() {
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const isActive = (path) => location.pathname === path;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <ShieldAlert size={28} />
            <span>Zen AI Pentest</span>
          </div>
          <div className="version">v2.0.0</div>
        </div>

        <nav className="sidebar-nav">
          <Link 
            to="/" 
            className={`nav-item ${isActive('/') ? 'active' : ''}`}
          >
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </Link>

          <Link 
            to="/scans" 
            className={`nav-item ${location.pathname.startsWith('/scans') ? 'active' : ''}`}
          >
            <ScanLine size={20} />
            <span>Scans</span>
          </Link>

          <Link 
            to="/scans/new" 
            className={`nav-item ${isActive('/scans/new') ? 'active' : ''}`}
          >
            <PlusCircle size={20} />
            <span>New Scan</span>
          </Link>

          <Link 
            to="/findings" 
            className={`nav-item ${isActive('/findings') ? 'active' : ''}`}
          >
            <ShieldAlert size={20} />
            <span>Findings</span>
          </Link>

          <Link 
            to="/scheduler" 
            className={`nav-item ${isActive('/scheduler') ? 'active' : ''}`}
          >
            <Calendar size={20} />
            <span>Scheduler</span>
          </Link>

          <Link 
            to="/slack" 
            className={`nav-item ${isActive('/slack') ? 'active' : ''}`}
          >
            <MessageSquare size={20} />
            <span>Slack</span>
          </Link>

          <Link 
            to="/settings" 
            className={`nav-item ${isActive('/settings') ? 'active' : ''}`}
          >
            <Settings size={20} />
            <span>Settings</span>
          </Link>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="user-details">
              <span className="username">{user?.username || 'User'}</span>
              <span className="role">{user?.role || 'Operator'}</span>
            </div>
          </div>
          <button onClick={logout} className="logout-btn" title="Logout">
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
