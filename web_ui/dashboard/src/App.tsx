import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Scan, 
  ShieldAlert, 
  Bot, 
  Menu,
  X,
  LogOut
} from 'lucide-react'
import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import ScanManager from './components/ScanManager'
import FindingsList from './components/FindingsList'
import AgentMonitor from './components/AgentMonitor'
import Login from './components/Login'
import { authApi } from './api/client'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check auth status on mount
    setIsAuthenticated(authApi.isAuthenticated())
    setLoading(false)
  }, [])

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    authApi.logout()
    setIsAuthenticated(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />
  }

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/scans', icon: Scan, label: 'Scan Manager' },
    { path: '/findings', icon: ShieldAlert, label: 'Findings' },
    { path: '/agents', icon: Bot, label: 'Agent Monitor' },
  ]

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Mobile header */}
      <div className="lg:hidden bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg">Zen AI Pentest</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
        >
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside 
          className={`
            fixed lg:static inset-y-0 left-0 z-40 w-64 bg-slate-800 border-r border-slate-700 
            transform transition-transform duration-300 ease-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}
        >
          {/* Logo */}
          <div className="hidden lg:flex items-center gap-3 px-6 py-5 border-b border-slate-700">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <ShieldAlert className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg">Zen AI Pentest</h1>
              <p className="text-xs text-slate-400">v2.0.0</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) => `
                  flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all duration-200
                  ${isActive 
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                    : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-100'
                  }
                `}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Bottom section */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
            <button 
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-slate-400 hover:bg-slate-700/50 hover:text-slate-100 transition-all"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
            
            {/* Connection status */}
            <div className="mt-4 px-4 flex items-center gap-2 text-xs text-slate-500">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              System Online
            </div>
          </div>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 min-h-screen overflow-auto">
          <div className="p-4 lg:p-8 max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/scans" element={<ScanManager />} />
              <Route path="/findings" element={<FindingsList />} />
              <Route path="/agents" element={<AgentMonitor />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
