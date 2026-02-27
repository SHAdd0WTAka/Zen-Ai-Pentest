import { useState } from 'react';
import {
  Cpu,
  MemoryStick,
  Activity,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Send,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { useAgentStore } from '../store/agentStore';
import { agentApi } from '../api/client';

export function AgentDetail() {
  const { selectedAgent } = useAgentStore();
  const [command, setCommand] = useState('');
  const [logs, setLogs] = useState<string[]>([]);

  if (!selectedAgent) {
    return (
      <Card className="h-[600px] flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Select an agent to view details</p>
        </div>
      </Card>
    );
  }

  const handleSendCommand = async () => {
    if (!command.trim()) return;
    
    try {
      await agentApi.sendCommand(selectedAgent.id, command, {});
      setLogs((prev) => [...prev, `> ${command}`, 'Command sent successfully']);
      setCommand('');
    } catch (error) {
      setLogs((prev) => [...prev, `> ${command}`, `Error: ${error}`]);
    }
  };

  const getStatusIcon = () => {
    switch (selectedAgent.status) {
      case 'online':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'busy':
        return <Loader2 className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'offline':
        return <Activity className="h-5 w-5 text-gray-400" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  return (
    <Card className="h-[600px]">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <div>
              <CardTitle className="text-lg">{selectedAgent.name}</CardTitle>
              <p className="text-xs text-muted-foreground">{selectedAgent.id}</p>
            </div>
          </div>
          <Badge
            variant={selectedAgent.status === 'online' ? 'default' : 'secondary'}
            className={cn(
              selectedAgent.status === 'online' && 'bg-green-500/10 text-green-500',
              selectedAgent.status === 'busy' && 'bg-yellow-500/10 text-yellow-500',
              selectedAgent.status === 'error' && 'bg-red-500/10 text-red-500'
            )}
          >
            {selectedAgent.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <Tabs defaultValue="metrics" className="h-[520px]">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
            <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
            <TabsTrigger value="terminal">Terminal</TabsTrigger>
          </TabsList>

          {/* Metrics Tab */}
          <TabsContent value="metrics" className="space-y-4 mt-4">
            {/* CPU Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <Cpu className="h-4 w-4" />
                  CPU Usage
                </span>
                <span className="font-medium">{selectedAgent.cpuUsage}%</span>
              </div>
              <Progress value={selectedAgent.cpuUsage} className="h-2" />
            </div>

            {/* Memory Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <MemoryStick className="h-4 w-4" />
                  Memory Usage
                </span>
                <span className="font-medium">{selectedAgent.memoryUsage}%</span>
              </div>
              <Progress value={selectedAgent.memoryUsage} className="h-2" />
            </div>

            {/* Active Tasks */}
            <div className="p-4 rounded-lg bg-muted">
              <div className="flex items-center justify-between">
                <span className="text-sm">Active Tasks</span>
                <span className="text-2xl font-bold">{selectedAgent.activeTasks}</span>
              </div>
            </div>

            {/* Version */}
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Version</span>
              <span>{selectedAgent.version}</span>
            </div>

            {/* Last Seen */}
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Last Seen</span>
              <span>{new Date(selectedAgent.lastSeen).toLocaleTimeString()}</span>
            </div>
          </TabsContent>

          {/* Capabilities Tab */}
          <TabsContent value="capabilities" className="mt-4">
            <div className="flex flex-wrap gap-2">
              {selectedAgent.capabilities.map((cap) => (
                <Badge key={cap} variant="secondary" className="px-3 py-1">
                  {cap}
                </Badge>
              ))}
            </div>
          </TabsContent>

          {/* Terminal Tab */}
          <TabsContent value="terminal" className="mt-4 h-[450px] flex flex-col">
            <ScrollArea className="flex-1 bg-slate-950 rounded-lg p-4 font-mono text-sm">
              <div className="space-y-1 text-green-400">
                <p>Connected to {selectedAgent.name}</p>
                <p>Type commands to execute on agent...</p>
                {logs.map((log, i) => (
                  <p key={i} className={log.startsWith('>') ? 'text-white' : 'text-gray-400'}>
                    {log}
                  </p>
                ))}
              </div>
            </ScrollArea>
            
            <div className="flex gap-2 mt-4">
              <Input
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                placeholder="Enter command..."
                className="flex-1"
                onKeyDown={(e) => e.key === 'Enter' && handleSendCommand()}
              />
              <Button onClick={handleSendCommand} size="icon">
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
