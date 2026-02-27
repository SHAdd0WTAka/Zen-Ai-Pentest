import { useState } from 'react';
import { Shield, AlertTriangle, Target, ChevronRight, Skull, Route } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AttackGraph } from './AttackGraph';
import { cn } from '@/lib/utils';

interface AttackPath {
  entry_point: string;
  target: string;
  path: string[];
  length: number;
  difficulty_score: number;
  nodes: Array<{
    id: string;
    name: string;
    type: string;
    criticality: string;
  }>;
}

interface AttackSurface {
  entry_points: number;
  crown_jewels: number;
  total_assets: number;
  total_attack_vectors: number;
  attack_surface_score: string;
}

const mockPaths: AttackPath[] = [
  {
    entry_point: 'web-server',
    target: 'file-server',
    path: ['web-server', 'app-server', 'dc', 'file-server'],
    length: 4,
    difficulty_score: 1.5,
    nodes: [
      { id: 'web-server', name: 'Web Server', type: 'entry_point', criticality: 'medium' },
      { id: 'app-server', name: 'App Server', type: 'server', criticality: 'high' },
      { id: 'dc', name: 'Domain Controller', type: 'domain_controller', criticality: 'critical' },
      { id: 'file-server', name: 'File Server', type: 'crown_jewel', criticality: 'critical' },
    ],
  },
  {
    entry_point: 'web-server',
    target: 'db-server',
    path: ['web-server', 'app-server', 'db-server'],
    length: 3,
    difficulty_score: 2.0,
    nodes: [
      { id: 'web-server', name: 'Web Server', type: 'entry_point', criticality: 'medium' },
      { id: 'app-server', name: 'App Server', type: 'server', criticality: 'high' },
      { id: 'db-server', name: 'Database Server', type: 'database', criticality: 'critical' },
    ],
  },
];

const mockSurface: AttackSurface = {
  entry_points: 2,
  crown_jewels: 3,
  total_assets: 15,
  total_attack_vectors: 24,
  attack_surface_score: 'CRITICAL',
};

const mockNodes = [
  { id: 'web-server', name: 'Web Server', type: 'entry_point', criticality: 'medium', compromised: false },
  { id: 'app-server', name: 'App Server', type: 'server', criticality: 'high', compromised: false },
  { id: 'db-server', name: 'Database Server', type: 'database', criticality: 'critical', compromised: false },
  { id: 'dc', name: 'Domain Controller', type: 'domain_controller', criticality: 'critical', compromised: false },
  { id: 'file-server', name: 'File Server', type: 'crown_jewel', criticality: 'critical', compromised: false },
];

const mockEdges = [
  { source: 'web-server', target: 'app-server', technique_name: 'SQL Injection', difficulty: 'easy' },
  { source: 'app-server', target: 'db-server', technique_name: 'Credential Theft', difficulty: 'easy' },
  { source: 'app-server', target: 'dc', technique_name: 'Pass-the-Hash', difficulty: 'medium' },
  { source: 'dc', target: 'file-server', technique_name: 'Domain Admin', difficulty: 'easy' },
];

export function AttackPathPanel() {
  const [selectedPath, setSelectedPath] = useState<AttackPath | null>(mockPaths[0]);
  const [activeTab, setActiveTab] = useState<'graph' | 'paths' | 'surface'>('graph');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Route className="w-6 h-6 text-red-500" />
          Attack Path Analysis
        </h2>
        <p className="text-slate-500 mt-1">
          Visualize attack paths from entry points to crown jewels
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs text-slate-500 uppercase">Entry Points</p>
            <p className="text-2xl font-bold text-cyan-500">{mockSurface.entry_points}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs text-slate-500 uppercase">Crown Jewels</p>
            <p className="text-2xl font-bold text-red-500">{mockSurface.crown_jewels}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs text-slate-500 uppercase">Total Assets</p>
            <p className="text-2xl font-bold text-slate-200">{mockSurface.total_assets}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900/50">
          <CardContent className="p-4">
            <p className="text-xs text-slate-500 uppercase">Attack Surface</p>
            <p className={cn(
              'text-lg font-bold',
              mockSurface.attack_surface_score === 'CRITICAL' && 'text-red-500',
              mockSurface.attack_surface_score === 'HIGH' && 'text-orange-500',
              mockSurface.attack_surface_score === 'MEDIUM' && 'text-yellow-500',
            )}>
              {mockSurface.attack_surface_score}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-slate-900/50 rounded-lg border border-slate-800 w-fit">
        {[
          { id: 'graph', label: 'Attack Graph', icon: Target },
          { id: 'paths', label: 'Critical Paths', icon: Route },
          { id: 'surface', label: 'Attack Surface', icon: Shield },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2',
              activeTab === tab.id
                ? 'bg-cyan-500 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'graph' && (
        <AttackGraph
          nodes={mockNodes}
          edges={mockEdges}
          highlightedPath={selectedPath?.path}
        />
      )}

      {activeTab === 'paths' && (
        <div className="grid gap-4">
          <h3 className="text-lg font-semibold text-slate-200">Critical Attack Paths</h3>
          {mockPaths.map((path, idx) => (
            <Card
              key={idx}
              className={cn(
                'border-slate-800 cursor-pointer transition-all',
                selectedPath === path
                  ? 'border-cyan-500 bg-cyan-500/10'
                  : 'hover:border-slate-700'
              )}
              onClick={() => setSelectedPath(path)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500/20 text-red-500 font-bold">
                      {idx + 1}
                    </div>
                    <div>
                      <h4 className="font-medium text-slate-200">
                        {path.nodes[0].name} → {path.nodes[path.nodes.length - 1].name}
                      </h4>
                      <p className="text-sm text-slate-500">
                        {path.length} hops • Difficulty: {path.difficulty_score.toFixed(1)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      'px-2 py-1 rounded text-xs font-medium',
                      path.difficulty_score <= 2
                        ? 'bg-red-500/20 text-red-500'
                        : 'bg-yellow-500/20 text-yellow-500'
                    )}>
                      {path.difficulty_score <= 2 ? 'EASY' : 'MEDIUM'}
                    </span>
                    <ChevronRight className="w-5 h-5 text-slate-500" />
                  </div>
                </div>

                {/* Path visualization */}
                <div className="flex items-center gap-2 mt-4">
                  {path.nodes.map((node, nodeIdx) => (
                    <div key={node.id} className="flex items-center">
                      <div className={cn(
                        'px-3 py-1 rounded text-xs',
                        node.criticality === 'critical' && 'bg-red-500/20 text-red-400',
                        node.criticality === 'high' && 'bg-orange-500/20 text-orange-400',
                        node.criticality === 'medium' && 'bg-blue-500/20 text-blue-400',
                      )}>
                        {node.name}
                      </div>
                      {nodeIdx < path.nodes.length - 1 && (
                        <ChevronRight className="w-4 h-4 text-slate-600 mx-1" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'surface' && (
        <div className="grid gap-6">
          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                Risk Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <h4 className="font-semibold text-red-400 mb-2">Critical Attack Surface</h4>
                <p className="text-sm text-slate-400">
                  The network has {mockSurface.entry_points} entry points with direct or indirect
                  access to {mockSurface.crown_jewels} crown jewel assets. Immediate action recommended.
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium text-slate-300">Key Findings:</h4>
                <ul className="space-y-2 text-sm text-slate-400">
                  <li className="flex items-start gap-2">
                    <Skull className="w-4 h-4 text-red-500 mt-0.5" />
                    Critical path from Web Server to File Server (4 hops)
                  </li>
                  <li className="flex items-start gap-2">
                    <Skull className="w-4 h-4 text-red-500 mt-0.5" />
                    Domain Controller is reachable from application server
                  </li>
                  <li className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5" />
                    Database credentials stored in application config
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            <Card className="border-slate-800 bg-slate-900/50">
              <CardContent className="p-4">
                <h4 className="text-sm font-medium text-slate-400 mb-2">Entry Points</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Web Server</span>
                    <span className="text-xs text-red-400">2 vulns</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">VPN Gateway</span>
                    <span className="text-xs text-yellow-400">1 vuln</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-800 bg-slate-900/50">
              <CardContent className="p-4">
                <h4 className="text-sm font-medium text-slate-400 mb-2">Crown Jewels</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Domain Controller</span>
                    <span className="text-xs text-red-400">Critical</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Database Server</span>
                    <span className="text-xs text-red-400">Critical</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">File Server</span>
                    <span className="text-xs text-red-400">Critical</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
