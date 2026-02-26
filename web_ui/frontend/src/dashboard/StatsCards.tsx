import { useMemo } from 'react';
import { Activity, Users, ScanLine, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAgentStore } from '../store/agentStore';

export function StatsCards() {
  const { agents, scans } = useAgentStore();

  const stats = useMemo(() => {
    const onlineAgents = agents.filter((a) => a.status === 'online').length;
    const busyAgents = agents.filter((a) => a.status === 'busy').length;
    const activeScans = scans.filter((s) => s.status === 'running').length;
    const completedScans = scans.filter((s) => s.status === 'completed').length;
    const totalFindings = scans.reduce((acc, s) => acc + s.findings, 0);

    return {
      onlineAgents,
      busyAgents,
      activeScans,
      completedScans,
      totalFindings,
    };
  }, [agents, scans]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Online Agents */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Online Agents</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.onlineAgents}</div>
          <p className="text-xs text-muted-foreground">
            {stats.busyAgents} busy, {agents.length - stats.onlineAgents - stats.busyAgents} offline
          </p>
        </CardContent>
      </Card>

      {/* Active Scans */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Scans</CardTitle>
          <ScanLine className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.activeScans}</div>
          <p className="text-xs text-muted-foreground">
            {stats.completedScans} completed today
          </p>
        </CardContent>
      </Card>

      {/* Total Findings */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Vulnerabilities</CardTitle>
          <AlertCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalFindings}</div>
          <p className="text-xs text-muted-foreground">
            Across all scans
          </p>
        </CardContent>
      </Card>

      {/* System Health */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">System Health</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-500">98%</div>
          <p className="text-xs text-muted-foreground">
            All systems operational
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
