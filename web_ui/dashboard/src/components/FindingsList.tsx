import { useState, useEffect } from 'react'
import { 
  Search, 
  ShieldAlert, 
  Download,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import axios from 'axios'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Types
interface Finding {
  id: number
  title: string
  description: string | null
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  cvss_score: number | null
  cve_id: string | null
  evidence: string | null
  remediation: string | null
  tool: string | null
  target: string | null
  port: number | null
  service: string | null
  scan_id: number
  created_at: string
  verified: number
  scan?: {
    name: string
    target: string
  }
}

interface FindingStats {
  total: number
  by_severity: Record<string, number>
  by_tool: Record<string, number>
  verified_count: number
  false_positive_count: number
}

const SEVERITY_CONFIG = {
  critical: { 
    color: 'text-red-400', 
    bg: 'bg-red-500/20', 
    border: 'border-red-500/30',
    icon: AlertTriangle,
    label: 'Critical'
  },
  high: { 
    color: 'text-orange-400', 
    bg: 'bg-orange-500/20', 
    border: 'border-orange-500/30',
    icon: ShieldAlert,
    label: 'High'
  },
  medium: { 
    color: 'text-yellow-400', 
    bg: 'bg-yellow-500/20', 
    border: 'border-yellow-500/30',
    icon: AlertTriangle,
    label: 'Medium'
  },
  low: { 
    color: 'text-green-400', 
    bg: 'bg-green-500/20', 
    border: 'border-green-500/30',
    icon: CheckCircle2,
    label: 'Low'
  },
  info: { 
    color: 'text-blue-400', 
    bg: 'bg-blue-500/20', 
    border: 'border-blue-500/30',
    icon: FileText,
    label: 'Info'
  },
}

// Finding Detail Modal
function FindingDetailModal({ 
  finding, 
  isOpen, 
  onClose 
}: { 
  finding: Finding | null
  isOpen: boolean
  onClose: () => void 
}) {
  const [verified, setVerified] = useState(finding?.verified || 0)

  if (!isOpen || !finding) return null

  const severity = SEVERITY_CONFIG[finding.severity]
  const SeverityIcon = severity.icon

  const handleVerify = async (status: number) => {
    try {
      await axios.patch(`/api/findings/${finding.id}`, { verified: status })
      setVerified(status)
    } catch (error) {
      console.error('Failed to update finding:', error)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className={cn('p-6 border-b border-slate-700', severity.bg)}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <SeverityIcon className={cn('w-6 h-6', severity.color)} />
              <div>
                <span className={cn('text-xs font-bold uppercase tracking-wide', severity.color)}>
                  {severity.label} Severity
                </span>
                <h2 className="text-xl font-bold text-slate-100 mt-1">{finding.title}</h2>
              </div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-slate-700/50 rounded-lg text-slate-400">
              ×
            </button>
          </div>
          
          {finding.cvss_score && (
            <div className="mt-4 flex items-center gap-2">
              <div className="bg-slate-900/50 px-3 py-1 rounded-lg">
                <span className="text-slate-400 text-sm">CVSS Score:</span>
                <span className={cn('ml-2 font-bold', severity.color)}>{finding.cvss_score}</span>
              </div>
              {finding.cve_id && (
                <div className="bg-slate-900/50 px-3 py-1 rounded-lg">
                  <span className="text-slate-400 text-sm">CVE:</span>
                  <span className="ml-2 font-mono text-slate-200">{finding.cve_id}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Target Info */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="bg-slate-700/30 rounded-lg p-3">
              <span className="text-slate-500">Target</span>
              <p className="text-slate-200 font-medium mt-1">{finding.target || 'N/A'}</p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3">
              <span className="text-slate-500">Tool</span>
              <p className="text-slate-200 font-medium mt-1">{finding.tool || 'N/A'}</p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3">
              <span className="text-slate-500">Discovered</span>
              <p className="text-slate-200 font-medium mt-1">
                {formatDistanceToNow(new Date(finding.created_at), { addSuffix: true })}
              </p>
            </div>
          </div>

          {/* Description */}
          {finding.description && (
            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Description</h3>
              <div className="bg-slate-700/30 rounded-lg p-4 text-slate-300 text-sm leading-relaxed">
                {finding.description}
              </div>
            </div>
          )}

          {/* Evidence */}
          {finding.evidence && (
            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Evidence</h3>
              <div className="bg-slate-900/50 rounded-lg p-4 font-mono text-xs text-slate-400 overflow-auto max-h-64">
                <pre>{finding.evidence}</pre>
              </div>
            </div>
          )}

          {/* Remediation */}
          {finding.remediation && (
            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-2">Remediation</h3>
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-green-100 text-sm">
                {finding.remediation}
              </div>
            </div>
          )}

          {/* Verification */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-700">
            <div className="text-sm text-slate-400">
              Verification Status: 
              <span className={cn(
                'ml-2 font-medium',
                verified === 1 ? 'text-green-400' : 
                verified === 2 ? 'text-red-400' : 'text-yellow-400'
              )}>
                {verified === 1 ? 'Verified' : verified === 2 ? 'False Positive' : 'Unverified'}
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleVerify(1)}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  verified === 1 
                    ? 'bg-green-600 text-white' 
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                )}
              >
                <CheckCircle2 className="w-4 h-4 inline mr-1" />
                Verified
              </button>
              <button
                onClick={() => handleVerify(2)}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  verified === 2 
                    ? 'bg-red-600 text-white' 
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                )}
              >
                <XCircle className="w-4 h-4 inline mr-1" />
                False Positive
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Main Component
export default function FindingsList() {
  const [findings, setFindings] = useState<Finding[]>([])
  const [stats, setStats] = useState<FindingStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [verifiedFilter, setVerifiedFilter] = useState<string>('all')
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  useEffect(() => {
    fetchFindings()
  }, [severityFilter, verifiedFilter])

  const fetchFindings = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (severityFilter !== 'all') params.append('severity', severityFilter)
      
      // In a real implementation, this would fetch from the API
      // const res = await axios.get(`/api/findings?${params}`)
      
      // Mock data for demonstration
      const mockFindings: Finding[] = [
        {
          id: 1,
          title: 'SQL Injection in Login Form',
          description: 'The login form is vulnerable to SQL injection attacks. An attacker could bypass authentication or extract sensitive data.',
          severity: 'critical',
          cvss_score: 9.8,
          cve_id: null,
          evidence: "POST /login HTTP/1.1\nusername=admin' OR '1'='1'--&password=test\n\nResponse: HTTP 200 OK\nSet-Cookie: session=abc123",
          remediation: 'Use parameterized queries or prepared statements. Validate all user input.',
          tool: 'sqlmap',
          target: 'https://example.com/login',
          port: 443,
          service: 'https',
          scan_id: 1,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          verified: 0,
          scan: { name: 'Web App Scan #1', target: 'example.com' }
        },
        {
          id: 2,
          title: 'Outdated OpenSSL Version',
          description: 'The server is running OpenSSL 1.0.1 which contains known vulnerabilities.',
          severity: 'high',
          cvss_score: 7.5,
          cve_id: 'CVE-2014-0160',
          evidence: 'OpenSSL/1.0.1e-fips',
          remediation: 'Upgrade to OpenSSL 1.1.1 or later.',
          tool: 'nmap',
          target: '192.168.1.100',
          port: 443,
          service: 'https',
          scan_id: 1,
          created_at: new Date(Date.now() - 7200000).toISOString(),
          verified: 1,
          scan: { name: 'Network Scan #1', target: '192.168.1.0/24' }
        },
        {
          id: 3,
          title: 'Missing Security Headers',
          description: 'The application is missing important security headers such as X-Frame-Options and Content-Security-Policy.',
          severity: 'medium',
          cvss_score: 5.3,
          cve_id: null,
          evidence: 'Headers: Server: nginx/1.18.0\nMissing: X-Frame-Options, CSP, HSTS',
          remediation: 'Add security headers to the web server configuration.',
          tool: 'nuclei',
          target: 'https://example.com',
          port: 443,
          service: 'https',
          scan_id: 2,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          verified: 0,
          scan: { name: 'Web App Scan #2', target: 'example.com' }
        },
      ]
      
      setFindings(mockFindings)
      
      // Calculate stats
      const stats: FindingStats = {
        total: mockFindings.length,
        by_severity: {},
        by_tool: {},
        verified_count: mockFindings.filter(f => f.verified === 1).length,
        false_positive_count: mockFindings.filter(f => f.verified === 2).length
      }
      
      mockFindings.forEach(f => {
        stats.by_severity[f.severity] = (stats.by_severity[f.severity] || 0) + 1
        if (f.tool) {
          stats.by_tool[f.tool] = (stats.by_tool[f.tool] || 0) + 1
        }
      })
      
      setStats(stats)
    } catch (error) {
      console.error('Failed to fetch findings:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredFindings = findings.filter((finding) => {
    const matchesSearch = 
      finding.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      finding.target?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      finding.description?.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesSeverity = severityFilter === 'all' || finding.severity === severityFilter
    
    const matchesVerified = verifiedFilter === 'all' || 
      (verifiedFilter === 'verified' && finding.verified === 1) ||
      (verifiedFilter === 'unverified' && finding.verified === 0) ||
      (verifiedFilter === 'false-positive' && finding.verified === 2)
    
    return matchesSearch && matchesSeverity && matchesVerified
  })

  const handleExport = (format: 'json' | 'csv') => {
    const data = JSON.stringify(filteredFindings, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `findings-export-${format(new Date(), 'yyyy-MM-dd')}.json`
    a.click()
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Findings</h1>
          <p className="text-slate-400 mt-1">Review and manage security findings</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('json')}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
          {(['critical', 'high', 'medium', 'low', 'info'] as const).map((sev) => {
            const config = SEVERITY_CONFIG[sev]
            const count = stats.by_severity[sev] || 0
            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(severityFilter === sev ? 'all' : sev)}
                className={cn(
                  'p-4 rounded-xl border transition-all text-left',
                  severityFilter === sev
                    ? cn(config.bg, config.border, 'ring-2 ring-offset-2 ring-offset-slate-900', config.color.replace('text-', 'ring-'))
                    : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                )}
              >
                <config.icon className={cn('w-5 h-5 mb-2', config.color)} />
                <div className="text-2xl font-bold text-slate-100">{count}</div>
                <div className={cn('text-sm font-medium', config.color)}>{config.label}</div>
              </button>
            )
          })}
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700">
            <CheckCircle2 className="w-5 h-5 mb-2 text-green-400" />
            <div className="text-2xl font-bold text-slate-100">{stats.verified_count}</div>
            <div className="text-sm text-slate-400">Verified</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search findings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <select
          value={verifiedFilter}
          onChange={(e) => setVerifiedFilter(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Status</option>
          <option value="verified">Verified</option>
          <option value="unverified">Unverified</option>
          <option value="false-positive">False Positive</option>
        </select>
      </div>

      {/* Findings List */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
          </div>
        ) : filteredFindings.length === 0 ? (
          <div className="text-center py-16">
            <ShieldAlert className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-300">No findings found</h3>
            <p className="text-slate-500 mt-1">Try adjusting your filters</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {filteredFindings.map((finding) => {
              const severity = SEVERITY_CONFIG[finding.severity]
              const SeverityIcon = severity.icon
              
              return (
                <div
                  key={finding.id}
                  onClick={() => {
                    setSelectedFinding(finding)
                    setDetailOpen(true)
                  }}
                  className="p-4 hover:bg-slate-700/30 transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-4">
                    <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center shrink-0', severity.bg)}>
                      <SeverityIcon className={cn('w-5 h-5', severity.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h4 className="font-medium text-slate-200">{finding.title}</h4>
                          <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
                            <span>{finding.target}</span>
                            <span>•</span>
                            <span>{finding.tool}</span>
                            <span>•</span>
                            <span>{formatDistanceToNow(new Date(finding.created_at), { addSuffix: true })}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className={cn(
                            'px-2 py-1 rounded-full text-xs font-medium border',
                            severity.bg,
                            severity.border,
                            severity.color
                          )}>
                            {finding.severity}
                          </span>
                          {finding.verified === 1 && (
                            <CheckCircle2 className="w-5 h-5 text-green-400" />
                          )}
                        </div>
                      </div>
                      {finding.description && (
                        <p className="mt-2 text-sm text-slate-400 line-clamp-2">
                          {finding.description}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      <FindingDetailModal
        finding={selectedFinding}
        isOpen={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </div>
  )
}
