import { useEffect, useState } from 'react';
import { useAgentStore } from '../store/agentStore';
import { agentApi, scanApi } from '../api/client';
import { AgentList } from './AgentList';
import { AgentDetail } from './AgentDetail';
import { ScanPanel } from './ScanPanel';
import { StatsCards } from './StatsCards';
import { DashboardHeader } from './DashboardHeader';
import { ThemeProvider } from './ThemeProvider';
import { EvidencePanel } from './EvidencePanel';
import { ReportGenerator, ReportList } from '@/components/reports';
import { AttackPathPanel } from '@/components/attack-path/AttackPathPanel';
import { cn } from '@/lib/utils';

type Tab = 'agents' | 'evidence' | 'reports' | 'attack-path';

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('agents');
  const { setAgents, setScans, setLoading, setError } = useAgentStore();

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [agents, scans] = await Promise.all([
          agentApi.getAll(),
          scanApi.getAll(),
        ]);
        setAgents(agents);
        setScans(scans);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [setAgents, setScans, setLoading, setError]);

  const tabs = [
    { id: 'agents' as Tab, label: 'Agents & Scans', count: null },
    { id: 'evidence' as Tab, label: 'Evidence', count: 5 },
    { id: 'reports' as Tab, label: 'Reports', count: null },
    { id: 'attack-path' as Tab, label: 'Attack Paths', count: null },
  ];

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-background text-foreground">
        <DashboardHeader />
        
        <main className="container mx-auto p-6 space-y-6">
          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 p-1 bg-slate-900/50 rounded-lg border border-slate-800 w-fit">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'px-4 py-2 rounded-md text-sm font-medium transition-all',
                  activeTab === tab.id
                    ? 'bg-cyan-500 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                )}
              >
                {tab.label}
                {tab.count && (
                  <span className={cn(
                    'ml-2 px-1.5 py-0.5 rounded text-xs',
                    activeTab === tab.id ? 'bg-white/20' : 'bg-slate-800'
                  )}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'agents' && (
            <>
              {/* Stats Overview */}
              <StatsCards />
              
              {/* Main Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Agent List */}
                <div className="lg:col-span-1">
                  <AgentList />
                </div>
                
                {/* Agent Detail */}
                <div className="lg:col-span-1">
                  <AgentDetail />
                </div>
                
                {/* Scan Panel */}
                <div className="lg:col-span-1">
                  <ScanPanel />
                </div>
              </div>
            </>
          )}

          {activeTab === 'evidence' && <EvidencePanel />}

          {activeTab === 'reports' && (
            <div className="space-y-6">
              {/* Report Generator */}
              <div>
                <h2 className="text-2xl font-bold text-slate-100 mb-2">Generate Report</h2>
                <p className="text-slate-500 mb-6">Create professional penetration test reports for different audiences</p>
                <ReportGenerator />
              </div>
              
              {/* Generated Reports */}
              <div>
                <h2 className="text-xl font-bold text-slate-100 mb-4">Generated Reports</h2>
                <ReportList />
              </div>
            </div>
          )}

          {activeTab === 'attack-path' && <AttackPathPanel />}
        </main>
      </div>
    </ThemeProvider>
  );
}
