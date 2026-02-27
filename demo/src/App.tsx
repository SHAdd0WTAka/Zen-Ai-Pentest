import { useState, useEffect } from 'react';
import { Shield, Users, FileText, Target, Activity, Settings } from 'lucide-react';
import { mockApi } from './lib/mockData';
import { AgentList } from './components/agents/AgentList';
import { ScanPanel } from './components/agents/ScanPanel';
import { EvidencePanel } from './components/evidence/EvidencePanel';
import { ReportPanel } from './components/reports/ReportPanel';
import { AttackPathPanel } from './components/attack-path/AttackPathPanel';

type Tab = 'agents' | 'evidence' | 'reports' | 'attack-path';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('agents');
  const [agents, setAgents] = useState([]);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const [agentData, scanData] = await Promise.all([
        mockApi.getAgents(),
        mockApi.getScans(),
      ]);
      setAgents(agentData);
      setScans(scanData);
      setLoading(false);
    };
    loadData();
  }, []);

  const tabs = [
    { id: 'agents' as Tab, label: 'Agents & Scans', icon: Users },
    { id: 'evidence' as Tab, label: 'Evidence', icon: Shield },
    { id: 'reports' as Tab, label: 'Reports', icon: FileText },
    { id: 'attack-path' as Tab, label: 'Attack Paths', icon: Target },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-500 flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Zen-AI-Pentest</h1>
                <p className="text-xs text-cyan-400">DEMO MODE - Port 3001</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
                <Activity className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-400">System Online</span>
              </div>
              <button className="p-2 rounded-lg hover:bg-slate-800 transition-colors">
                <Settings className="w-5 h-5 text-slate-400" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-6">
        {/* Navigation */}
        <div className="flex items-center gap-1 p-1 bg-slate-900/50 rounded-lg border border-slate-800 w-fit mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-cyan-500 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
          </div>
        ) : (
          <>
            {activeTab === 'agents' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <AgentList agents={agents} />
                <ScanPanel scans={scans} />
              </div>
            )}
            {activeTab === 'evidence' && <EvidencePanel />}
            {activeTab === 'reports' && <ReportPanel />}
            {activeTab === 'attack-path' && <AttackPathPanel />}
          </>
        )}
      </main>

      {/* Demo Banner */}
      <div className="fixed bottom-4 right-4 px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-lg">
        <p className="text-sm text-amber-400">
          <span className="font-semibold">DEMO MODE</span> - All data is simulated
        </p>
      </div>
    </div>
  );
}

export default App;
