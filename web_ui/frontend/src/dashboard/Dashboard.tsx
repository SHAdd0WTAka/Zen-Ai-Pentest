import { useEffect } from 'react';
import { useAgentStore } from '../store/agentStore';
import { agentApi, scanApi } from '../api/client';
import { AgentList } from './AgentList';
import { AgentDetail } from './AgentDetail';
import { ScanPanel } from './ScanPanel';
import { StatsCards } from './StatsCards';
import { DashboardHeader } from './DashboardHeader';
import { ThemeProvider } from './ThemeProvider';

export function Dashboard() {
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

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-background text-foreground">
        <DashboardHeader />
        
        <main className="container mx-auto p-6 space-y-6">
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
        </main>
      </div>
    </ThemeProvider>
  );
}
