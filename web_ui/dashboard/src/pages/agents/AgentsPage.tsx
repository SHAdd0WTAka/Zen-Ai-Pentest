// ============================================
// Zen-AI-Pentest Platform - Agents Page
// ============================================

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  RefreshCw,
  MoreHorizontal,
  Bot,
  PowerOff,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  Activity,
  Settings,
  Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { agentApi } from '@/services/api';
import { useWebSocket } from '@/services/websocket';
import { toast } from 'sonner';
import type { AgentStatus } from '@/types';

// ============================================
// Status Badge Component
// ============================================
function StatusBadge({ status }: { status: AgentStatus }) {
  const config: Record<AgentStatus, { variant: string; icon: React.ElementType; label: string }> = {
    online: { variant: 'success', icon: CheckCircle, label: 'Online' },
    offline: { variant: 'secondary', icon: PowerOff, label: 'Offline' },
    busy: { variant: 'default', icon: Activity, label: 'Busy' },
    error: { variant: 'destructive', icon: AlertCircle, label: 'Error' },
    updating: { variant: 'warning', icon: Clock, label: 'Updating' },
  };

  const { variant, icon: Icon, label } = config[status];

  return (
    <Badge variant={variant as any} className="flex items-center gap-1 w-fit">
      <Icon className="w-3 h-3" />
      {label}
    </Badge>
  );
}

// ============================================
// Main Agents Page
// ============================================
export function AgentsPage() {
  const queryClient = useQueryClient();
  const { restartAgent } = useWebSocket();
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<string | null>(null);

  // Fetch agents
  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentApi.list(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Mutations
  const restartMutation = useMutation({
    mutationFn: agentApi.restart,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent restarted');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to restart agent');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: agentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent deleted');
      setDeleteDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to delete agent');
    },
  });

  const handleRestart = (id: string) => {
    restartAgent(id);
    restartMutation.mutate(id);
  };

  const handleDelete = (id: string) => {
    setAgentToDelete(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (agentToDelete) {
      deleteMutation.mutate(agentToDelete);
    }
  };

  const filteredAgents =
    agents?.filter(
      (agent) =>
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.host.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground">
            Manage scanning agents across your infrastructure
          </p>
        </div>
        <Button asChild>
          <Link to="/agents/new">
            <Plus className="w-4 h-4 mr-2" />
            Register Agent
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search agents..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['agents'] })}
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Agents Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Host</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Version</TableHead>
              <TableHead>CPU / Memory</TableHead>
              <TableHead>Last Seen</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                </TableCell>
              </TableRow>
            ) : filteredAgents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  No agents found
                </TableCell>
              </TableRow>
            ) : (
              filteredAgents.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Bot className="w-4 h-4 text-muted-foreground" />
                      <Link to={`/agents/${agent.id}`} className="font-medium hover:underline">
                        {agent.name}
                      </Link>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{agent.host}</TableCell>
                  <TableCell>
                    <StatusBadge status={agent.status} />
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">v{agent.version}</Badge>
                  </TableCell>
                  <TableCell>
                    {agent.metrics ? (
                      <div className="space-y-1 w-32">
                        <div className="flex items-center justify-between text-xs">
                          <span>CPU</span>
                          <span>{agent.metrics.cpuUsage}%</span>
                        </div>
                        <Progress value={agent.metrics.cpuUsage} className="h-1" />
                        <div className="flex items-center justify-between text-xs">
                          <span>RAM</span>
                          <span>{agent.metrics.memoryUsage}%</span>
                        </div>
                        <Progress value={agent.metrics.memoryUsage} className="h-1" />
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {agent.lastSeen
                      ? new Date(agent.lastSeen).toLocaleString()
                      : 'Never'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem asChild>
                          <Link to={`/agents/${agent.id}`}>View Details</Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleRestart(agent.id)}>
                          <RefreshCw className="w-4 h-4 mr-2" />
                          Restart
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                          <Link to={`/agents/${agent.id}/settings`}>
                            <Settings className="w-4 h-4 mr-2" />
                            Settings
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDelete(agent.id)}
                          className="text-destructive focus:text-destructive"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Agent</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this agent? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
