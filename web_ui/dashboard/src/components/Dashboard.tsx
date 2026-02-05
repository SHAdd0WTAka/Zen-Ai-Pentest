import { useEffect, useState } from 'react'
import { 
  Activity, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  Zap,
  Shield
} from 'lucide-react'
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { format } from 'date-fns'
import axios from 'axios'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Utility for tailwind class merging
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Types
interface DashboardStats {
  total_scans: number
  active_scans: number
  completed_scans: number
  failed_scans: number
  cancelled_scans: number
  total_findings: number
  critical_findings: number
  high_findings: number
  medium_findings: number
  low_findings: number
  info_findings: number
  severity_distribution: Array<{ name: string; value: number; color: string }>
  scans_by_status: Record<string, number>
  recent_trends: Array<{ date: string; scans: number; findings: number }>
}

interface RecentFinding {
  id: number
  title: string
  severity: string
  target: string
  tool: string
  scan_id: number
  scan_name: string
  created_at: string
  cvss_score: number | null
}

interface ActiveScan {
  id: number
  name: string
  target: string
  scan_type: string
  status: string
  progress: number
  started_at: string | null
  duration_seconds: number | null
  findings_count: number
}

// Severity badge component
function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-green-500/20 text-green-400 border-green-500/30',
    info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  }

  return (
    <span className={cn(
      'px-2 py-1 rounded-full text-xs font-medium border uppercase',
      colors[severity.toLowerCase()] || colors.info
    )}>
      {severity}
    </span>
  )
}

// Stat card component
function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  trend,
  color = 'blue'
}: { 
  title: string
  value: number
  subtitle: string
  icon: React.ElementType
  trend?: { value: number; positive: boolean }
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple'
}) {
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/10 text-blue-400',
    green: 'from-green-500/20 to-green-600/10 text-green-400',
    red: 'from-red-500/20 to-red-600/10 text-red-400',
    yellow: 'from-yellow-500/20 to-yellow-600/10 text-yellow-400',
    purple: 'from-purple-500/20 to-purple-600/10 text-purple-400',
  }

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 card-hover">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm font-medium">{title}</p>
          <h3 className="text-3xl font-bold text-slate-100 mt-2">{value.toLocaleString()}</h3>
          <div className="flex items-center gap-2 mt-2">
            {trend && (
              <span className={cn(
                'text-xs font-medium',
                trend.positive ? 'text-green-400' : 'text-red-400'
              )}>
                {trend.positive ? '+' : ''}{trend.value}%
              </span>
            )}
            <span className="text-slate-500 text-sm">{subtitle}</span>
          </div>
        </div>
        <div className={cn(
          'w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br',
          colorClasses[color]
        )}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  )
}

// Main Dashboard Component
export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activeScans, setActiveScans] = useState<ActiveScan[]>([])
  const [recentFindings, setRecentFindings] = useState<RecentFinding[]>([])
  const [loading, setLoading] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, activeRes, findingsRes] = await Promise.all([
          axios.get('/api/v1/dashboard/stats'),
          axios.get('/api/v1/dashboard/active-scans'),
          axios.get('/api/v1/dashboard/recent-findings?limit=10'),
        ])
        setStats(statsRes.data)
        setActiveScans(activeRes.data)
        setRecentFindings(findingsRes.data)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/dashboard/ws`)
    
    ws.onopen = () => {
      setWsConnected(true)
      ws.send(JSON.stringify({ action: 'subscribe', events: ['scans', 'findings'] }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'scan_started' || data.type === 'scan_completed') {
        // Refresh data
        axios.get('/api/v1/dashboard/stats').then(r => setStats(r.data))
        axios.get('/api/v1/dashboard/active-scans').then(r => setActiveScans(r.data))
      }
      if (data.type === 'finding_found') {
        axios.get('/api/v1/dashboard/recent-findings?limit=10').then(r => setRecentFindings(r.data))
      }
    }

    ws.onclose = () => setWsConnected(false)

    return () => ws.close()
  }, [])

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
          <p className="text-slate-400 mt-1">Overview of your security testing activities</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border',
            wsConnected 
              ? 'bg-green-500/10 text-green-400 border-green-500/30' 
              : 'bg-red-500/10 text-red-400 border-red-500/30'
          )}>
            <div className={cn('w-2 h-2 rounded-full', wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500')} />
            {wsConnected ? 'Live Updates' : 'Disconnected'}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Scans"
          value={stats.total_scans}
          subtitle="All time scans"
          icon={Target}
          color="blue"
          trend={{ value: 12, positive: true }}
        />
        <StatCard
          title="Active Scans"
          value={stats.active_scans}
          subtitle="Currently running"
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Critical Findings"
          value={stats.critical_findings}
          subtitle="Require immediate attention"
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          title="Total Findings"
          value={stats.total_findings}
          subtitle="All severity levels"
          icon={CheckCircle}
          color="purple"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trends Chart */}
        <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-100">Activity Trends</h3>
              <p className="text-slate-400 text-sm">Scans and findings over the last 30 days</p>
            </div>
            <TrendingUp className="w-5 h-5 text-slate-500" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.recent_trends}>
                <defs>
                  <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFindings" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  dataKey="date" 
                  stroke="#64748b"
                  tickFormatter={(date) => format(new Date(date), 'MMM d')}
                  tick={{ fontSize: 12 }}
                />
                <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                  labelFormatter={(date) => format(new Date(date), 'MMM d, yyyy')}
                />
                <Area 
                  type="monotone" 
                  dataKey="scans" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorScans)" 
                  name="Scans"
                />
                <Area 
                  type="monotone" 
                  dataKey="findings" 
                  stroke="#8b5cf6" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorFindings)" 
                  name="Findings"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-6">Findings by Severity</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.severity_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {stats.severity_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            {stats.severity_distribution.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-slate-400 text-sm">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Scans */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-100">Active Scans</h3>
              <p className="text-slate-400 text-sm">Currently running scans</p>
            </div>
            <Zap className="w-5 h-5 text-yellow-500" />
          </div>
          
          <div className="space-y-4">
            {activeScans.length === 0 ? (
              <p className="text-slate-500 text-center py-8">No active scans</p>
            ) : (
              activeScans.map((scan) => (
                <div key={scan.id} className="bg-slate-700/30 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-slate-100">{scan.name}</h4>
                      <p className="text-slate-400 text-sm">{scan.target}</p>
                    </div>
                    <span className={cn(
                      'px-2 py-1 rounded-full text-xs font-medium uppercase',
                      scan.status === 'running' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                    )}>
                      {scan.status}
                    </span>
                  </div>
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-sm text-slate-400 mb-1">
                      <span>Progress</span>
                      <span>{scan.progress}%</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                        style={{ width: `${scan.progress}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {scan.duration_seconds ? `${Math.floor(scan.duration_seconds / 60)}m` : 'Just started'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Shield className="w-3 h-3" />
                      {scan.findings_count} findings
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Findings */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-100">Recent Findings</h3>
              <p className="text-slate-400 text-sm">Latest security findings</p>
            </div>
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          
          <div className="space-y-3 max-h-80 overflow-auto">
            {recentFindings.length === 0 ? (
              <p className="text-slate-500 text-center py-8">No findings yet</p>
            ) : (
              recentFindings.map((finding) => (
                <div 
                  key={finding.id} 
                  className="flex items-start gap-3 p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                >
                  <div className={cn(
                    'w-2 h-2 rounded-full mt-2',
                    finding.severity === 'critical' ? 'bg-red-500' :
                    finding.severity === 'high' ? 'bg-orange-500' :
                    finding.severity === 'medium' ? 'bg-yellow-500' :
                    finding.severity === 'low' ? 'bg-green-500' : 'bg-blue-500'
                  )} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-slate-100 truncate">{finding.title}</h4>
                      <SeverityBadge severity={finding.severity} />
                    </div>
                    <p className="text-slate-400 text-sm mt-1">{finding.target}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                      <span>{finding.scan_name}</span>
                      <span>•</span>
                      <span>{format(new Date(finding.created_at), 'MMM d, HH:mm')}</span>
                      {finding.cvss_score && (
                        <>
                          <span>•</span>
                          <span>CVSS: {finding.cvss_score}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
