import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, Download, Search } from 'lucide-react';
import { mockApi } from '../../lib/mockData';

interface Evidence {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  evidence_type: string;
  target: { url?: string; ip?: string; port?: number };
  timestamps: { collected: string };
  integrity: { verified: boolean; hash: string };
  vulnerability_type: string;
  proof_of_concept: string;
}

const severityColors = {
  critical: 'bg-red-500 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-500 text-slate-900',
  low: 'bg-green-500 text-white',
};

export function EvidencePanel() {
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('all');

  useEffect(() => {
    mockApi.getEvidence().then(setEvidence);
  }, []);

  const filteredEvidence = evidence.filter((e) => {
    const matchesSearch = e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         e.vulnerability_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeverity = selectedSeverity === 'all' || e.severity === selectedSeverity;
    return matchesSearch && matchesSeverity;
  });

  const stats = {
    total: evidence.length,
    critical: evidence.filter((e) => e.severity === 'critical').length,
    high: evidence.filter((e) => e.severity === 'high').length,
    verified: evidence.filter((e) => e.integrity.verified).length,
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">Total Evidence</p>
          <p className="text-2xl font-bold text-cyan-400">{stats.total}</p>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">Critical</p>
          <p className="text-2xl font-bold text-red-500">{stats.critical}</p>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">High</p>
          <p className="text-2xl font-bold text-orange-500">{stats.high}</p>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">Verified</p>
          <p className="text-2xl font-bold text-green-500">{stats.verified}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search evidence..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-sm focus:outline-none focus:border-cyan-500"
          />
        </div>
        <select
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          className="px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-sm"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Evidence List */}
      <div className="grid gap-4">
        {filteredEvidence.map((item) => (
          <div
            key={item.id}
            className="p-4 rounded-xl border border-slate-800 bg-slate-900/50 hover:border-slate-700 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-lg ${severityColors[item.severity]}`}>
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-slate-200">{item.title}</h3>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${severityColors[item.severity]}`}>
                      {item.severity}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 mt-1">
                    {item.target.url || `${item.target.ip}:${item.target.port}`}
                  </p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(item.timestamps.collected).toLocaleString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                      Verified
                    </span>
                  </div>
                  {item.proof_of_concept && (
                    <div className="mt-3 p-3 bg-slate-950 rounded-lg font-mono text-xs text-slate-400">
                      <span className="text-slate-600">PoC:</span> {item.proof_of_concept}
                    </div>
                  )}
                </div>
              </div>
              <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                <Download className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
