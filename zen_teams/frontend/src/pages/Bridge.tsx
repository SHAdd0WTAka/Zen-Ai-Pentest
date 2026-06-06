import { useState, useEffect } from 'react'
import { Zap, Play, FileText, Activity, Shield, Server, Loader2 } from 'lucide-react'
import { api } from '../services/api'

const scanTypes = [
  { id: 'full', name: 'Full Scan', description: 'Comprehensive security assessment', icon: Shield },
  { id: 'webapp', name: 'WebApp Scan', description: 'OWASP Top 10 assessment', icon: Zap },
  { id: 'api', name: 'API Scan', description: 'API security testing', icon: Server },
  { id: 'network', name: 'Network Scan', description: 'Network infrastructure scan', icon: Activity },
]

export default function BridgePage() {
  const [target, setTarget] = useState('')
  const [selectedScan, setSelectedScan] = useState('full')
  const [scanStatus, setScanStatus] = useState<string | null>(null)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState('')
  const [tools, setTools] = useState<any[]>([])
  const [selectedTool, setSelectedTool] = useState('')
  const [loadingTools, setLoadingTools] = useState(false)

  useEffect(() => {
    setLoadingTools(true)
    api.getBridgeStatus()
      .then((data) => {
        if (data.tools) setTools(data.tools)
        setLoadingTools(false)
      })
      .catch(() => {
        // Fallback tools if bridge is not connected
        setTools([
          { name: 'nmap', description: 'Network discovery and security auditing' },
          { name: 'nikto', description: 'Web server scanner' },
          { name: 'sqlmap', description: 'SQL injection automation' },
          { name: 'nuclei', description: 'Vulnerability scanner' },
          { name: 'ffuf', description: 'Web fuzzer' },
          { name: 'testssl', description: 'SSL/TLS tester' },
        ])
        setLoadingTools(false)
      })
  }, [])

  const handleQuickScan = async () => {
    if (!target) return
    setScanStatus('starting')
    setError('')
    try {
      const data = await api.delegateScan({ target, scan_type: selectedScan })
      setScanStatus('running')
      setResults(data)
    } catch (e: any) {
      setError(e.message)
      setScanStatus(null)
    }
  }

  const handleToolRun = async () => {
    if (!target || !selectedTool) return
    setScanStatus('tool_running')
    setError('')
    try {
      const res = await fetch('/api/v1/bridge/tool/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_name: selectedTool, target }),
      })
      const data = await res.json()
      setScanStatus('completed')
      setResults(data)
    } catch (e: any) {
      setError(e.message)
      setScanStatus(null)
    }
  }

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Zap size={28} className="text-yellow-400" />
          Zen-AI-Pentest Bridge
        </h1>
        <p className="text-gray-400 mt-1">Direct integration with the pentest framework</p>
      </div>

      {error && (
        <div className="card border-red-500">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Quick Scan */}
      <div className="card space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Play size={20} />
          Quick Scan
        </h2>
        <div className="flex gap-4">
          <input
            type="text"
            className="input flex-1"
            placeholder="Enter target URL or IP (e.g., example.com)"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          />
          <select
            className="input w-48"
            value={selectedScan}
            onChange={(e) => setSelectedScan(e.target.value)}
          >
            {scanTypes.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button className="btn-primary flex items-center gap-2" onClick={handleQuickScan}>
            <Play size={18} />
            Start Scan
          </button>
        </div>

        {scanStatus && (
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={16} className={scanStatus === 'completed' ? 'text-green-400' : 'text-blue-400 animate-pulse'} />
              <span className="font-medium capitalize">{scanStatus.replace('_', ' ')}</span>
            </div>
            {results && (
              <div className="space-y-2 mt-3">
                <p className="text-sm text-gray-400">Target: {target}</p>
                {results.message && <p className="text-sm text-green-400">{results.message}</p>}
                {results.data && (
                  <pre className="bg-gray-800 rounded p-3 text-xs overflow-auto max-h-64">
                    {JSON.stringify(results.data, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tool Runner */}
      <div className="card space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Server size={20} />
          Run Specific Tool
        </h2>
        {loadingTools ? (
          <div className="flex items-center gap-2 text-gray-400">
            <Loader2 size={16} className="animate-spin" />
            Loading tools...
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {tools.map((tool: any) => (
              <button
                key={tool.name}
                onClick={() => setSelectedTool(tool.name)}
                className={`p-4 rounded-lg border transition-colors text-left ${
                  selectedTool === tool.name
                    ? 'border-blue-500 bg-blue-900/30'
                    : 'border-gray-700 bg-gray-800 hover:border-gray-500'
                }`}
              >
                <p className="font-semibold">{tool.name}</p>
                <p className="text-xs text-gray-400 mt-1">{tool.description}</p>
              </button>
            ))}
          </div>
        )}
        {selectedTool && (
          <button className="btn-primary" onClick={handleToolRun}>
            Run {selectedTool} on {target || 'target'}
          </button>
        )}
      </div>

      {/* Reports */}
      <div className="card space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <FileText size={20} />
          Reports
        </h2>
        <div className="flex gap-3">
          <button className="btn-secondary">Generate PDF Report</button>
          <button className="btn-secondary">Generate HTML Report</button>
          <button className="btn-secondary">Export JSON</button>
        </div>
      </div>
    </div>
  )
}
