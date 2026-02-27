import { useState } from 'react';
import { ScanLine, Plus, Play, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useAgentStore } from '../store/agentStore';
import { scanApi } from '../api/client';

function getStatusIcon(status: string) {
  switch (status) {
    case 'running':
      return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />;
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-500" />;
    case 'pending':
      return <ScanLine className="h-4 w-4 text-gray-400" />;
    default:
      return <ScanLine className="h-4 w-4" />;
  }
}

export function ScanPanel() {
  const { scans, agents, addScan } = useAgentStore();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newScan, setNewScan] = useState({
    target: '',
    agentId: '',
    type: 'recon',
  });

  const handleCreateScan = async () => {
    try {
      const scan = await scanApi.create({
        target: newScan.target,
        agentId: newScan.agentId,
        status: 'pending',
        progress: 0,
        startedAt: new Date().toISOString(),
        findings: 0,
      });
      addScan(scan);
      setIsDialogOpen(false);
      setNewScan({ target: '', agentId: '', type: 'recon' });
    } catch (error) {
      console.error('Failed to create scan:', error);
    }
  };

  return (
    <Card className="h-[600px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Scans ({scans.length})</CardTitle>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-1" />
                New
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Scan</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Target</Label>
                  <Input
                    placeholder="example.com or 192.168.1.1"
                    value={newScan.target}
                    onChange={(e) => setNewScan({ ...newScan, target: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Agent</Label>
                  <Select
                    value={newScan.agentId}
                    onValueChange={(value) => setNewScan({ ...newScan, agentId: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select agent" />
                    </SelectTrigger>
                    <SelectContent>
                      {agents
                        .filter((a) => a.status === 'online' || a.status === 'busy')
                        .map((agent) => (
                          <SelectItem key={agent.id} value={agent.id}>
                            {agent.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Scan Type</Label>
                  <Select
                    value={newScan.type}
                    onValueChange={(value) => setNewScan({ ...newScan, type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="recon">Reconnaissance</SelectItem>
                      <SelectItem value="port">Port Scan</SelectItem>
                      <SelectItem value="vuln">Vulnerability</SelectItem>
                      <SelectItem value="full">Full Assessment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleCreateScan} className="w-full">
                  <Play className="h-4 w-4 mr-1" />
                  Start Scan
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ScrollArea className="h-[520px]">
          <div className="space-y-3 p-4">
            {scans.map((scan) => (
              <div
                key={scan.id}
                className="p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(scan.status)}
                    <span className="font-medium">{scan.target}</span>
                  </div>
                  <Badge
                    variant={scan.status === 'completed' ? 'default' : 'secondary'}
                    className={cn(
                      scan.status === 'running' && 'bg-yellow-500/10 text-yellow-500',
                      scan.status === 'completed' && 'bg-green-500/10 text-green-500',
                      scan.status === 'failed' && 'bg-red-500/10 text-red-500'
                    )}
                  >
                    {scan.status}
                  </Badge>
                </div>

                {/* Progress */}
                {scan.status === 'running' && (
                  <div className="space-y-1 mb-3">
                    <Progress value={scan.progress} className="h-1.5" />
                    <p className="text-xs text-muted-foreground">{scan.progress}% complete</p>
                  </div>
                )}

                {/* Details */}
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <div className="flex items-center gap-3">
                    <span>Agent: {agents.find((a) => a.id === scan.agentId)?.name || scan.agentId}</span>
                    {scan.findings > 0 && (
                      <span className="text-red-500">{scan.findings} findings</span>
                    )}
                  </div>
                  <span>{new Date(scan.startedAt).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}

            {scans.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <ScanLine className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No scans yet</p>
                <p className="text-sm">Create your first scan to get started</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
