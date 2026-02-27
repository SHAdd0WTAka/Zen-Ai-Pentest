import { useState, useEffect } from 'react';
import { Filter, Shield, Search, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { EvidenceCard } from './EvidenceCard';
import { EvidenceStats } from './EvidenceStats';

interface Evidence {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  evidence_type: string;
  status: string;
  target: {
    url?: string;
    ip?: string;
    port?: number;
  };
  timestamps: {
    collected: string;
  };
  integrity: {
    verified: boolean;
    hash: string;
  };
  vulnerability_type?: string;
}

const mockEvidence: Evidence[] = [
  {
    id: '1',
    title: 'SQL Injection in Login Form',
    severity: 'critical',
    evidence_type: 'web_vulnerability',
    status: 'collected',
    target: { url: 'https://example.com/login' },
    timestamps: { collected: '2026-02-26T20:30:00Z' },
    integrity: { verified: true, hash: 'a1b2c3d4e5f6...' },
    vulnerability_type: 'SQL Injection',
  },
  {
    id: '2',
    title: 'XSS in Comment Field',
    severity: 'high',
    evidence_type: 'web_vulnerability',
    status: 'collected',
    target: { url: 'https://example.com/comments' },
    timestamps: { collected: '2026-02-26T20:25:00Z' },
    integrity: { verified: true, hash: 'b2c3d4e5f6g7...' },
    vulnerability_type: 'Cross-Site Scripting',
  },
  {
    id: '3',
    title: 'Open SSH Port (22)',
    severity: 'medium',
    evidence_type: 'network_vulnerability',
    status: 'collected',
    target: { ip: '192.168.1.100', port: 22 },
    timestamps: { collected: '2026-02-26T20:20:00Z' },
    integrity: { verified: true, hash: 'c3d4e5f6g7h8...' },
    vulnerability_type: 'Open Port',
  },
  {
    id: '4',
    title: 'API Key Exposure',
    severity: 'critical',
    evidence_type: 'api_vulnerability',
    status: 'collected',
    target: { url: 'https://api.example.com/v1/users' },
    timestamps: { collected: '2026-02-26T20:15:00Z' },
    integrity: { verified: true, hash: 'd4e5f6g7h8i9...' },
    vulnerability_type: 'Information Disclosure',
  },
  {
    id: '5',
    title: 'Missing Security Headers',
    severity: 'low',
    evidence_type: 'web_vulnerability',
    status: 'collected',
    target: { url: 'https://example.com' },
    timestamps: { collected: '2026-02-26T20:10:00Z' },
    integrity: { verified: true, hash: 'e5f6g7h8i9j0...' },
    vulnerability_type: 'Configuration',
  },
];

export function EvidenceList() {
  const [evidence] = useState<Evidence[]>(mockEvidence);
  const [filteredEvidence, setFilteredEvidence] = useState<Evidence[]>(mockEvidence);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  // Filter evidence
  useEffect(() => {
    let filtered = evidence;

    if (searchQuery) {
      filtered = filtered.filter(e =>
        e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.vulnerability_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.target.url?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.target.ip?.includes(searchQuery)
      );
    }

    if (selectedSeverity !== 'all') {
      filtered = filtered.filter(e => e.severity === selectedSeverity);
    }

    if (selectedType !== 'all') {
      filtered = filtered.filter(e => e.evidence_type === selectedType);
    }

    setFilteredEvidence(filtered);
  }, [evidence, searchQuery, selectedSeverity, selectedType]);

  const severityOptions = [
    { value: 'all', label: 'All Severities', color: 'bg-slate-600' },
    { value: 'critical', label: 'Critical', color: 'bg-red-500' },
    { value: 'high', label: 'High', color: 'bg-orange-500' },
    { value: 'medium', label: 'Medium', color: 'bg-yellow-500' },
    { value: 'low', label: 'Low', color: 'bg-green-500' },
    { value: 'info', label: 'Info', color: 'bg-blue-500' },
  ];

  const typeOptions = [
    { value: 'all', label: 'All Types' },
    { value: 'web_vulnerability', label: 'Web' },
    { value: 'api_vulnerability', label: 'API' },
    { value: 'network_vulnerability', label: 'Network' },
  ];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <EvidenceStats evidence={evidence} />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            placeholder="Search evidence..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-slate-900/50 border-slate-800"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-2 rounded-md bg-slate-900/50 border border-slate-800 text-sm text-slate-300"
          >
            {severityOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 rounded-md bg-slate-900/50 border border-slate-800 text-sm text-slate-300"
          >
            {typeOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <Button variant="outline" size="icon" className="border-slate-800">
            <Filter className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Evidence Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Showing {filteredEvidence.length} of {evidence.length} evidence items
        </p>
        <Button variant="outline" size="sm" className="border-slate-800 gap-2">
          <Download className="w-4 h-4" />
          Export All
        </Button>
      </div>

      {/* Evidence Grid */}
      <div className="grid gap-4">
        {filteredEvidence.map(item => (
          <EvidenceCard
            key={item.id}
            evidence={item}
          />
        ))}
      </div>

      {filteredEvidence.length === 0 && (
        <div className="text-center py-12">
          <Shield className="w-12 h-12 mx-auto text-slate-700 mb-4" />
          <p className="text-slate-500">No evidence found matching your filters</p>
        </div>
      )}
    </div>
  );
}
