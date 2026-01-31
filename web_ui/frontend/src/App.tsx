// ============================================
// Zen-AI-Pentest Dashboard - Main App
// ============================================

import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';

import AdvancedDashboard from './components/Dashboard/AdvancedDashboard';
import AttackGraph from './components/Visualizations/AttackGraph';
import EvidenceViewer from './components/Evidence/EvidenceViewer';
import FindingsTable from './components/Findings/FindingsTable';
import ReportViewer from './components/Reports/ReportViewer';
import ErrorBoundary from './components/ErrorBoundary';
import { useToast, ToastContainer } from './components/Toast';

import { useWebSocket, useAlertUpdates } from './hooks/useWebSocket';
import { wsService } from './services/api';

import {
  AttackGraph as AttackGraphType,
  Evidence,
  Finding,
  Report,
  Alert,
} from './types';

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});

// Navigation Component
const Navigation: React.FC = () => {
  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/findings', label: 'Findings', icon: '🔍' },
    { path: '/attack-graph', label: 'Attack Graph', icon: '🕸️' },
    { path: '/evidence', label: 'Evidence', icon: '📁' },
    { path: '/reports', label: 'Reports', icon: '📄' },
  ];

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-cyan-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">Z</span>
              </div>
              <span className="text-white font-bold text-lg">Zen-AI-Pentest</span>
            </div>
            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-cyan-900/50 text-cyan-400 border border-cyan-700/50'
                        : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`
                  }
                >
                  <span>{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-2 text-sm text-gray-400">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Online
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Mock Data for Demo
const mockAttackGraph: AttackGraphType = {
  nodes: [
    { id: '1', type: 'host', label: '192.168.1.1', data: { ip: '192.168.1.1', hostname: 'gateway' } },
    { id: '2', type: 'host', label: '192.168.1.10', data: { ip: '192.168.1.10', hostname: 'web-server' } },
    { id: '3', type: 'service', label: 'HTTP (80)', data: { port: 80, service: 'http', version: 'Apache/2.4.41' } },
    { id: '4', type: 'service', label: 'SSH (22)', data: { port: 22, service: 'ssh', version: 'OpenSSH 8.2' } },
    { id: '5', type: 'vulnerability', label: 'CVE-2021-41773', data: { cve: 'CVE-2021-41773', cvss: 9.8, severity: 'critical' } },
    { id: '6', type: 'credential', label: 'admin:password', data: {} },
    { id: '7', type: 'data', label: '/etc/passwd', data: {} },
  ],
  edges: [
    { id: 'e1', source: '1', target: '2', type: 'connection' },
    { id: 'e2', source: '2', target: '3', type: 'connection' },
    { id: 'e3', source: '2', target: '4', type: 'connection' },
    { id: 'e4', source: '3', target: '5', type: 'exploit' },
    { id: 'e5', source: '5', target: '6', type: 'leads_to' },
    { id: 'e6', source: '6', target: '7', type: 'leads_to' },
  ],
};

const mockEvidence: Evidence[] = [
  {
    id: '1',
    findingId: 'f1',
    type: 'screenshot',
    content: '',
    metadata: { filename: 'login-page.png', size: 102400, url: '/api/evidence/1/screenshot' },
    createdAt: new Date().toISOString(),
  },
  {
    id: '2',
    findingId: 'f1',
    type: 'http_response',
    content: JSON.stringify({ status: 200, headers: { 'content-type': 'application/json' }, body: { user: 'admin' } }, null, 2),
    metadata: { filename: 'response.json', size: 2048, mimeType: 'application/json' },
    createdAt: new Date().toISOString(),
  },
  {
    id: '3',
    findingId: 'f2',
    type: 'log',
    content: '[ERROR] 2024-01-15 10:30:45 - Authentication failed for user admin',
    metadata: { filename: 'auth.log', size: 5120 },
    createdAt: new Date().toISOString(),
  },
];

const mockReport: Report = {
  id: 'r1',
  scanId: 's1',
  name: 'Penetration Test Report - Q1 2024',
  format: 'markdown',
  status: 'completed',
  content: `# Penetration Test Report

## Executive Summary

Dieser Bericht enthält die Ergebnisse des Penetration Tests für das Zielsystem.

## Kritische Findings

### CVE-2021-41773 - Path Traversal in Apache HTTP Server

**Schweregrad:** Kritisch  
**CVSS Score:** 9.8

Eine Path-Traversal-Schwachstelle wurde in Apache HTTP Server 2.4.49 entdeckt.

## Empfehlungen

1. Sofortige Aktualisierung des Apache HTTP Servers
2. Implementierung von WAF-Regeln
3. Regelmäßige Sicherheitsaudits

\`\`\`bash
# Upgrade Apache
sudo apt update
sudo apt upgrade apache2
\`\`\`
`,
  createdAt: new Date().toISOString(),
  generatedAt: new Date().toISOString(),
  size: 15360,
};

// Attack Graph Page
const AttackGraphPage: React.FC = () => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Attack-Graph Visualisierung</h2>
      <AttackGraph
        data={mockAttackGraph}
        onNodeClick={(node) => console.log('Node clicked:', node)}
        onEdgeClick={(edge) => console.log('Edge clicked:', edge)}
      />
    </div>
  );
};

// Evidence Page
const EvidencePage: React.FC = () => {
  const { success } = useToast();

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Evidence Viewer</h2>
      <EvidenceViewer
        evidence={mockEvidence}
        onDownload={(evidence) => {
          success('Download gestartet', `${evidence.metadata.filename} wird heruntergeladen`);
        }}
        onDelete={(id) => console.log('Delete:', id)}
      />
    </div>
  );
};

// Findings Page
const FindingsPage: React.FC = () => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Findings Verwaltung</h2>
      <FindingsTable
        onFindingClick={(finding) => console.log('Finding clicked:', finding)}
      />
    </div>
  );
};

// Reports Page
const ReportsPage: React.FC = () => {
  const { success } = useToast();

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Report Viewer</h2>
      <ReportViewer
        report={mockReport}
        onDownload={(report) => {
          success('Download gestartet', `${report.name} wird heruntergeladen`);
        }}
        onDelete={(id) => console.log('Delete report:', id)}
      />
    </div>
  );
};

// WebSocket Handler Component
const WebSocketHandler: React.FC = () => {
  const { success, warning, info } = useToast();
  const { isConnected } = useWebSocket();

  useEffect(() => {
    const token = localStorage.getItem('auth_token') || undefined;
    wsService.connect(token);
    
    return () => {
      wsService.disconnect();
    };
  }, []);

  useEffect(() => {
    if (isConnected) {
      info('WebSocket verbunden', 'Echtzeit-Updates sind aktiv');
    }
  }, [isConnected, info]);

  useAlertUpdates((alert) => {
    const alertData = alert as Alert;
    warning(`Neuer Alert: ${alertData.title}`, alertData.message);
  });

  return null;
};

// Main App Component
const App: React.FC = () => {
  const { ToastContainer: AppToastContainer } = useToast();

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Router>
          <div className="min-h-screen bg-gray-900">
            <Navigation />
            <WebSocketHandler />
            <main>
              <Routes>
                <Route path="/" element={<AdvancedDashboard />} />
                <Route path="/findings" element={<FindingsPage />} />
                <Route path="/attack-graph" element={<AttackGraphPage />} />
                <Route path="/evidence" element={<EvidencePage />} />
                <Route path="/reports" element={<ReportsPage />} />
              </Routes>
            </main>
            <AppToastContainer position="top-right" />
          </div>
        </Router>
      </ErrorBoundary>
    </QueryClientProvider>
  );
};

export default App;
