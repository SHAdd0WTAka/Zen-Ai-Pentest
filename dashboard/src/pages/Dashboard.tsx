import { useEffect } from 'react'
import {
  Activity,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { useScanStore } from '../store/scanStore'

const mockScanData = [
  { name: 'Mon', scans: 4 },
  { name: 'Tue', scans: 6 },
  { name: 'Wed', scans: 8 },
  { name: 'Thu', scans: 5 },
  { name: 'Fri', scans: 9 },
  { name: 'Sat', scans: 3 },
  { name: 'Sun', scans: 2 },
]

const mockVulnData = [
  { name: 'Critical', value: 3, color: '#dc2626' },
  { name: 'High', value: 8, color: '#ea580c' },
  { name: 'Medium', value: 15, color: '#ca8a04' },
  { name: 'Low', value: 24, color: '#16a34a' },
]

const stats = [
  { name: 'Total Scans', value: '156', icon: Activity, change: '+12%', changeType: 'positive' },
  { name: 'Active Targets', value: '42', icon: Target, change: '+4', changeType: 'positive' },
  { name: 'Vulnerabilities', value: '50', icon: AlertTriangle, change: '-8%', changeType: 'positive' },
  { name: 'Secure Score', value: '87%', icon: Shield, change: '+5%', changeType: 'positive' },
]

const recentScans = [
  { id: 1, target: 'example.com', status: 'completed', severity: 'medium', date: '2 min ago' },
  { id: 2, target: 'test.com', status: 'running', severity: null, date: '5 min ago' },
  { id: 3, target: 'demo.org', status: 'completed', severity: 'high', date: '15 min ago' },
  { id: 4, target: 'api.test.com', status: 'failed', severity: null, date: '1 hour ago' },
]

export function Dashboard() {
  const { scans, fetchScans } = useScanStore()

  useEffect(() => {
    fetchScans()
  }, [fetchScans])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your security posture and recent scan activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Icon className="h-6 w-6 text-primary-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
              <div className="mt-4">
                <span className={`text-sm font-medium ${
                  stat.changeType === 'positive' ? 'text-success-600' : 'text-danger-600'
                }`}>
                  {stat.change}
                </span>
                <span className="text-sm text-gray-500"> from last week</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Scan Activity Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Activity</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockScanData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="scans"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={{ fill: '#0ea5e9' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Vulnerability Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Vulnerabilities</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={mockVulnData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {mockVulnData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Scans */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Scans</h3>
          <a href="/scans" className="text-sm text-primary-600 hover:text-primary-700">
            View all
          </a>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {recentScans.map((scan) => (
                <tr key={scan.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{scan.target}</td>
                  <td className="px-4 py-3">
                    <span className={`badge ${
                      scan.status === 'completed' ? 'badge-success' :
                      scan.status === 'running' ? 'badge-info' :
                      scan.status === 'failed' ? 'badge-danger' :
                      'badge-warning'
                    }`}>
                      {scan.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {scan.severity ? (
                      <span className={`badge ${
                        scan.severity === 'critical' ? 'badge-danger' :
                        scan.severity === 'high' ? 'badge-warning' :
                        scan.severity === 'medium' ? 'badge-info' :
                        'badge-success'
                      }`}>
                        {scan.severity}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">{scan.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}