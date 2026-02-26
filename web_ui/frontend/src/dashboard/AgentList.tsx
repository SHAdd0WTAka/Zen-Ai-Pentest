import { useMemo } from 'react';
import { Activity, AlertCircle, CheckCircle2, Loader2, Cpu, MemoryStick } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { useAgentStore, type Agent } from '../store/agentStore';

function getStatusIcon(status: Agent['status']) {
  switch (status) {
    case 'online':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case 'busy':
      return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />;
    case 'offline':
      return <Activity className="h-4 w-4 text-gray-400" />;
    case 'error':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
  }
}

function getStatusColor(status: Agent['status']) {
  switch (status) {
    case 'online':
      return 'bg-green-500/10 text-green-500 hover:bg-green-500/20';
    case 'busy':
      return 'bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20';
    case 'offline':
      return 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20';
    case 'error':
      return 'bg-red-500/10 text-red-500 hover:bg-red-500/20';
  }
}

export function AgentList() {
  const { agents, selectedAgent, selectAgent, isLoading } = useAgentStore();

  const sortedAgents = useMemo(() => {
    return [...agents].sort((a, b) => {
      // Online first, then busy, then others
      const statusOrder = { online: 0, busy: 1, offline: 2, error: 3 };
      return statusOrder[a.status] - statusOrder[b.status];
    });
  }, [agents]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Agents</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-48">
          <Loader2 className="h-8 w-8 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[600px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Agents ({agents.length})</CardTitle>
          <Badge variant="outline" className="text-xs">
            {agents.filter((a) => a.status === 'online' || a.status === 'busy').length} active
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[520px]">
          <div className="space-y-2 p-4">
            {sortedAgents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => selectAgent(agent)}
                className={cn(
                  'w-full text-left p-3 rounded-lg border transition-all',
                  'hover:bg-accent hover:border-accent',
                  selectedAgent?.id === agent.id && 'border-primary bg-primary/5'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(agent.status)}
                      <span className="font-medium">{agent.name}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Cpu className="h-3 w-3" />
                        {agent.cpuUsage}%
                      </span>
                      <span className="flex items-center gap-1">
                        <MemoryStick className="h-3 w-3" />
                        {agent.memoryUsage}%
                      </span>
                      {agent.activeTasks > 0 && (
                        <span>{agent.activeTasks} tasks</span>
                      )}
                    </div>
                  </div>
                  <Badge className={cn('text-xs', getStatusColor(agent.status))}>
                    {agent.status}
                  </Badge>
                </div>
                
                {/* Capabilities */}
                <div className="flex flex-wrap gap-1 mt-2">
                  {agent.capabilities.slice(0, 3).map((cap) => (
                    <span
                      key={cap}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground"
                    >
                      {cap}
                    </span>
                  ))}
                  {agent.capabilities.length > 3 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                      +{agent.capabilities.length - 3}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
