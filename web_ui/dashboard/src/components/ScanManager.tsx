import { useState, useEffect, useCallback } from 'react'
import { 
  Plus, 
  Search, 
  Filter, 
  Play, 
  StopCircle, 
  RotateCw,
  Clock,
  Target,
  FileText,
  ChevronDown,
  ChevronRight,
  Terminal
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import axios from 'axios'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import toast from 'react-hot-toast'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Types
interface Scan {
  id: number
  name: string
  target: string
  scan_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  started_at: string | null
  completed_at: string | null
  findings_count: number
  config?: Record<string, any>
}

interface ScanLog {
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  phase: string
  message: string
  details?: Record<string, any>
}

interface NewScanForm {
  name: string
  target: string
  scan_type: string
  objective: string
  priority: number
}

const SCAN_TYPES = [
  { value: 'quick', label: 'Quick Scan', description: 'Fast reconnaissance (5-10 min)' },
  { value: 'standard', label: 'Standard', description: 'Standard security assessment (30-60 min)' },
  { value: 'comprehensive', label: 'Comprehensive', description: 'Full penetration test (2-4 hours)' },
  { value: 'web', label: 'Web Application', description: 'Focused web app testing' },
  { value: 'network', label: 'Network', description: 'Network infrastructure scan' },
]

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  running: 'bg-green-500/20 text-green-400 border-green-500/30',
  completed: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  failed: 'bg-red-500/20 text-red-400 border-red-500/30',
  cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
}

// Create Scan Modal
function CreateScanModal({ 
  isOpen, 
  onClose, 
  onCreate 
}: { 
  isOpen: boolean
  onClose: () => void
  onCreate: (scan: NewScanForm) => Promise<void>
}) {
  const [form, setForm] = useState<NewScanForm>({
    name: '',
    target: '',
    scan_type: 'standard',
    objective: '',
    priority: 2,
  })
  const [submitting, setSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await onCreate(form)
      onClose()
      setForm({ name: '', target: '', scan_type: 'standard', objective: '', priority: 2 })
    } catch (error) {
      console.error('Failed to create scan:', error)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-lg max-h-[90vh] overflow-auto">
        <div className="p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-slate-100">Create New Scan</h2>
          <p className="text-slate-400 text-sm mt-1">Configure your penetration test</p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Scan Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Production API Security Test"
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Target</label>
            <input
              type="text"
              value={form.target}
              onChange={(e) => setForm({ ...form, target: e.target.value })}
              placeholder="https://example.com or 192.168.1.1"
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Scan Type</label>
            <div className="space-y-2">
              {SCAN_TYPES.map((type) => (
                <label
                  key={type.value}
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all',
                    form.scan_type === type.value
                      ? 'bg-blue-500/10 border-blue-500/50'
                      : 'bg-slate-700/50 border-slate-600 hover:border-slate-500'
                  )}
                >
                  <input
                    type="radio"
                    name="scan_type"
                    value={type.value}
                    checked={form.scan_type === type.value}
                    onChange={(e) => setForm({ ...form, scan_type: e.target.value })}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium text-slate-200">{type.label}</div>
                    <div className="text-sm text-slate-400">{type.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Objective (Optional)</label>
            <textarea
              value={form.objective}
              onChange={(e) => setForm({ ...form, objective: e.target.value })}
              placeholder="Describe the specific goals for this scan..."
              rows={3}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Priority</label>
            <select
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: parseInt(e.target.value) })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={1}>Low - Background scan</option>
              <option value={2}>Normal - Standard priority</option>
              <option value={3}>High - Expedited</option>
              <option value={4}>Critical - Immediate attention</option>
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {submitting && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              Start Scan
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Scan Logs Panel
function ScanLogsPanel({ 
  scanId, 
  isOpen, 
  onClose 
}: { 
  scanId: number | null
  isOpen: boolean
  onClose: () => void 
}) {
  const [logs, setLogs] = useState<ScanLog[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const logsEndRef = useState<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!scanId || !isOpen) return

    // Fetch existing logs
    axios.get(`/api/v1/scans/${scanId}/logs?limit=100`).then((res) => {
      setLogs(res.data.logs.reverse())
    })

    // Connect WebSocket for real-time logs
    const websocket = new WebSocket(`ws://${window.location.host}/api/v1/scans/${scanId}/ws`)
    
    websocket.onopen = () => {
      websocket.send(JSON.stringify({ action: 'subscribe', events: ['logs'] }))
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'log' || data.type === 'logs') {
        setLogs((prev) => [...prev, ...(Array.isArray(data.logs) ? data.logs : [data])])
      }
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [scanId, isOpen])

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-400'
      case 'WARNING': return 'text-yellow-400'
      case 'DEBUG': return 'text-slate-400'
      default: return 'text-green-400'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 w-full max-w-4xl h-[80vh] sm:h-[600px] sm:rounded-xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <Terminal className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-slate-100">Scan Logs #{scanId}</h3>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-lg text-slate-400">
            ×
          </button>
        </div>
        
        <div className="flex-1 overflow-auto p-4 font-mono text-sm space-y-1">
          {logs.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No logs yet...</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="flex gap-3 hover:bg-slate-700/30 rounded px-2 -mx-2">
                <span className="text-slate-500 shrink-0">
                  {format(new Date(log.timestamp), 'HH:mm:ss')}
                </span>
                <span className={cn('shrink-0 w-16 font-bold', getLevelColor(log.level))}>
                  {log.level}
                </span>
                <span className="text-slate-400 shrink-0 w-24">[{log.phase}]</span>
                <span className="text-slate-200">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// Main Component
export default function ScanManager() {
  const [scans, setScans] = useState<Scan[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [selectedScan, setSelectedScan] = useState<number | null>(null)
  const [logsOpen, setLogsOpen] = useState(false)
  const [expandedScan, setExpandedScan] = useState<number | null>(null)

  const fetchScans = useCallback(async () => {
    try {
      const res = await axios.get('/api/v1/scans-extended/')
      setScans(res.data)
    } catch (error) {
      console.error('Failed to fetch scans:', error)
      toast.error('Failed to load scans')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchScans()
    const interval = setInterval(fetchScans, 10000)
    return () => clearInterval(interval)
  }, [fetchScans])

  const handleCreateScan = async (form: NewScanForm) => {
    const res = await axios.post('/api/v1/scans/', form)
    toast.success('Scan created successfully')
    fetchScans()
    return res.data
  }

  const handleStopScan = async (scanId: number) => {
    try {
      await axios.post(`/api/v1/scans/${scanId}/action`, { action: 'stop', reason: 'User requested' })
      toast.success('Scan stopped')
      fetchScans()
    } catch (error) {
      toast.error('Failed to stop scan')
    }
  }

  const handleRestartScan = async (scanId: number) => {
    try {
      await axios.post(`/api/v1/scans/${scanId}/action`, { action: 'restart' })
      toast.success('Scan restarted')
      fetchScans()
    } catch (error) {
      toast.error('Failed to restart scan')
    }
  }

  const filteredScans = scans.filter((scan) => {
    const matchesSearch = 
      scan.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      scan.target.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || scan.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Scan Manager</h1>
          <p className="text-slate-400 mt-1">Manage and monitor security scans</p>
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          New Scan
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search scans..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-slate-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Scans Table */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="text-center py-16">
            <Target className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-300">No scans found</h3>
            <p className="text-slate-500 mt-1">Create a new scan to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Scan</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Type</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Findings</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase">Created</th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-slate-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {filteredScans.map((scan) => (
                  <>
                    <tr key={scan.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setExpandedScan(expandedScan === scan.id ? null : scan.id)}
                          className="flex items-center gap-3 text-left"
                        >
                          {expandedScan === scan.id ? (
                            <ChevronDown className="w-4 h-4 text-slate-500" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-slate-500" />
                          )}
                          <div>
                            <div className="font-medium text-slate-200">{scan.name}</div>
                            <div className="text-sm text-slate-500">{scan.target}</div>
                          </div>
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <span className={cn(
                          'px-2 py-1 rounded-full text-xs font-medium border uppercase',
                          STATUS_COLORS[scan.status]
                        )}>
                          {scan.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-300 capitalize">{scan.scan_type}</td>
                      <td className="px-6 py-4">
                        <span className="text-slate-300">{scan.findings_count}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-400 text-sm">
                        {formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setSelectedScan(scan.id)
                              setLogsOpen(true)
                            }}
                            className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-blue-400 transition-colors"
                            title="View Logs"
                          >
                            <FileText className="w-4 h-4" />
                          </button>
                          {scan.status === 'running' && (
                            <button
                              onClick={() => handleStopScan(scan.id)}
                              className="p-2 hover:bg-red-500/10 rounded-lg text-slate-400 hover:text-red-400 transition-colors"
                              title="Stop Scan"
                            >
                              <StopCircle className="w-4 h-4" />
                            </button>
                          )}
                          {(scan.status === 'completed' || scan.status === 'failed' || scan.status === 'cancelled') && (
                            <button
                              onClick={() => handleRestartScan(scan.id)}
                              className="p-2 hover:bg-green-500/10 rounded-lg text-slate-400 hover:text-green-400 transition-colors"
                              title="Restart Scan"
                            >
                              <RotateCw className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {expandedScan === scan.id && (
                      <tr className="bg-slate-800/50">
                        <td colSpan={6} className="px-6 py-4">
                          <div className="pl-7 space-y-3">
                            <div className="grid grid-cols-3 gap-4 text-sm">
                              <div>
                                <span className="text-slate-500">Started:</span>
                                <span className="text-slate-300 ml-2">
                                  {scan.started_at ? format(new Date(scan.started_at), 'PPp') : 'Not started'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-500">Completed:</span>
                                <span className="text-slate-300 ml-2">
                                  {scan.completed_at ? format(new Date(scan.completed_at), 'PPp') : 'N/A'}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-500">Scan ID:</span>
                                <span className="text-slate-300 ml-2 font-mono">#{scan.id}</span>
                              </div>
                            </div>
                            {scan.config && (
                              <div className="bg-slate-900/50 rounded-lg p-3">
                                <span className="text-slate-500 text-sm">Configuration:</span>
                                <pre className="mt-1 text-xs text-slate-400 font-mono overflow-auto">
                                  {JSON.stringify(scan.config, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      <CreateScanModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreate={handleCreateScan}
      />
      <ScanLogsPanel
        scanId={selectedScan}
        isOpen={logsOpen}
        onClose={() => setLogsOpen(false)}
      />
    </div>
  )
}
