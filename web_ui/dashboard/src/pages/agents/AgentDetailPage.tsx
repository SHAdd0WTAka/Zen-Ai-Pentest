// ============================================
// Zen-AI-Pentest Platform - Agent Detail Page
// ============================================


import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Bot,
  RefreshCw,
  Settings,
  Activity,
  Cpu,
  HardDrive,
  Network,
  Loader2,
  AlertCircle,
  CheckCircle,
  PowerOff,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { agentApi } from '@/services/api';
import type { AgentStatus } from '@/types';

// ============================================
// Status Config
// ============================================
const statusConfig: Record<AgentStatus, { label: string; color: string; icon: React.ElementType }> = {
  online: { label: 'Online', color: 'bg-green-500', icon: CheckCircle },
  offline: { label: 'Offline', color: 'bg-gray-500', icon: PowerOff },
  busy: { label: 'Busy', color: 'bg-blue-500', icon: Activity },
  error: { label: 'Error', color: 'bg-red-500', icon: AlertCircle },
  updating: { label: 'Updating', color: 'bg-yellow-500', icon: RefreshCw },
};

// ============================================
// Main Agent Detail Page
// ============================================
export function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: agent, isLoading } = useQuery({
    queryKey: ['agent', id],
    queryFn: () => agentApi.get(id!),
    refetchInterval: 5000,
  });

  const { data: metrics } = useQuery({
    queryKey: ['agent-metrics', id],
    queryFn: () => agentApi.getMetrics(id!),
    refetchInterval: 5000,
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold">Agent not found</h2>
        <Button asChild className="mt-4">
          <Link to="/agents">Back to Agents</Link>
        </Button>
      </div>
    );
  }

  const status = statusConfig[agent.status];
  const StatusIcon = status.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/agents">
              <ArrowLeft className="w-5 h-5" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <Bot className="w-8 h-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">{agent.name}</h1>
            </div>
            <div className="flex items-center gap-3 mt-2">
              <Badge className={status.color}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {status.label}
              </Badge>
              <Badge variant="outline">v{agent.version}</Badge>
              <span className="text-sm text-muted-foreground font-mono">{agent.host}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Restart
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/agents/${agent.id}/settings`}>
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Link>
          </Button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              CPU Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.cpuUsage || 0}%</div>
            <Progress value={metrics?.cpuUsage || 0} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Memory Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.memoryUsage || 0}%</div>
            <Progress value={metrics?.memoryUsage || 0} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <HardDrive className="w-4 h-4" />
              Disk Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.diskUsage || 0}%</div>
            <Progress value={metrics?.diskUsage || 0} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Network className="w-4 h-4" />
              Network I/O
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">In:</span>
                <span>{((metrics?.networkIO?.bytesIn || 0) / 1024 / 1024).toFixed(2)} MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Out:</span>
                <span>{((metrics?.networkIO?.bytesOut || 0) / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Agent Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ID</span>
                  <span className="font-mono text-sm">{agent.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type</span>
                  <Badge variant="outline">{agent.type}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Host</span>
                  <span className="font-mono">{agent.host}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Port</span>
                  <span className="font-mono">{agent.port}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Version</span>
                  <span>v{agent.version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Registered</span>
                  <span>{new Date(agent.registeredAt).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last Seen</span>
                  <span>{agent.lastSeen ? new Date(agent.lastSeen).toLocaleString() : 'Never'}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Scans Completed</span>
                  <span className="font-medium">{metrics?.scansCompleted || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Uptime</span>
                  <span className="font-medium">
                    {metrics?.uptime
                      ? `${Math.floor(metrics.uptime / 3600)}h ${Math.floor((metrics.uptime % 3600) / 60)}m`
                      : 'N/A'}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="capabilities">
          <Card>
            <CardHeader>
              <CardTitle>Agent Capabilities</CardTitle>
              <CardDescription>Scanning capabilities of this agent</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {agent.capabilities.map((capability) => (
                  <Badge key={capability} variant="secondary">
                    {capability}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Agent Logs</CardTitle>
              <CardDescription>Recent activity logs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-muted p-4 rounded-lg font-mono text-sm space-y-1">
                <div className="text-muted-foreground">
                  [{new Date().toISOString()}] Agent connected
                </div>
                <div className="text-muted-foreground">
                  [{new Date().toISOString()}] Capabilities registered: {agent.capabilities.join(', ')}
                </div>
                <div className="text-muted-foreground">
                  [{new Date().toISOString()}] Agent ready for scanning
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
