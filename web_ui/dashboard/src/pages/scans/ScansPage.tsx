// ============================================
// Zen-AI-Pentest Platform - Scans Page
// ============================================

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  Play,
  Pause,
  Square,
  Trash2,
  MoreHorizontal,
  RefreshCw,
  Download,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
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
import { scanApi } from '@/services/api';
import { useWebSocket } from '@/services/websocket';
import { useScanStore } from '@/store';
import type { ScanStatus } from '@/types';
import { toast } from 'sonner';

// ============================================
// Status Badge Component
// ============================================
function StatusBadge({ status }: { status: ScanStatus }) {
  const config: Record<ScanStatus, { variant: string; icon: React.ElementType; label: string }> = {
    pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
    queued: { variant: 'secondary', icon: Clock, label: 'Queued' },
    running: { variant: 'default', icon: Loader2, label: 'Running' },
    paused: { variant: 'warning', icon: Pause, label: 'Paused' },
    completed: { variant: 'success', icon: CheckCircle, label: 'Completed' },
    failed: { variant: 'destructive', icon: XCircle, label: 'Failed' },
    cancelled: { variant: 'outline', icon: AlertCircle, label: 'Cancelled' },
  };

  const { variant, icon: Icon, label } = config[status];

  return (
    <Badge variant={variant as any} className="flex items-center gap-1 w-fit">
      <Icon className={`w-3 h-3 ${status === 'running' && 'animate-spin'}`} />
      {label}
    </Badge>
  );
}

// ============================================
// Main Scans Page
// ============================================
export function ScansPage() {
  const queryClient = useQueryClient();
  const { startScan, stopScan, pauseScan, resumeScan } = useWebSocket();
  const { filters, pagination, setFilters, setPagination } = useScanStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScans, setSelectedScans] = useState<string[]>([]);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [scanToDelete, setScanToDelete] = useState<string | null>(null);

  // Fetch scans
  const { data, isLoading } = useQuery({
    queryKey: ['scans', filters, pagination],
    queryFn: () => scanApi.list(filters, pagination),
  });

  // Mutations
  const startMutation = useMutation({
    mutationFn: scanApi.start,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan started successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to start scan');
    },
  });

  const stopMutation = useMutation({
    mutationFn: scanApi.stop,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan stopped');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to stop scan');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: scanApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan deleted successfully');
      setDeleteDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to delete scan');
    },
  });

  const handleStart = (id: string) => {
    startScan(id);
    startMutation.mutate(id);
  };

  const handleStop = (id: string) => {
    stopScan(id);
    stopMutation.mutate(id);
  };

  const handleDelete = (id: string) => {
    setScanToDelete(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (scanToDelete) {
      deleteMutation.mutate(scanToDelete);
    }
  };

  const filteredScans = data?.scans.filter((scan) =>
    scan.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    scan.target.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Scans</h1>
          <p className="text-muted-foreground">
            Manage and monitor your security scans
          </p>
        </div>
        <Button asChild>
          <Link to="/scans/new">
            <Plus className="w-4 h-4 mr-2" />
            New Scan
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search scans..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button variant="outline" size="icon">
          <Filter className="w-4 h-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['scans'] })}
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Scans Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Created</TableHead>
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
            ) : filteredScans.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  No scans found
                </TableCell>
              </TableRow>
            ) : (
              filteredScans.map((scan) => (
                <TableRow key={scan.id}>
                  <TableCell>
                    <Link to={`/scans/${scan.id}`} className="font-medium hover:underline">
                      {scan.name}
                    </Link>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{scan.target}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{scan.type}</Badge>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={scan.status} />
                  </TableCell>
                  <TableCell>
                    <div className="w-full max-w-[100px]">
                      <Progress value={scan.progress} className="h-2" />
                      <span className="text-xs text-muted-foreground">{scan.progress}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(scan.createdAt).toLocaleDateString()}
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
                          <Link to={`/scans/${scan.id}`}>View Details</Link>
                        </DropdownMenuItem>
                        {scan.status === 'pending' || scan.status === 'paused' ? (
                          <DropdownMenuItem onClick={() => handleStart(scan.id)}>
                            <Play className="w-4 h-4 mr-2" />
                            Start
                          </DropdownMenuItem>
                        ) : scan.status === 'running' ? (
                          <DropdownMenuItem onClick={() => handleStop(scan.id)}>
                            <Square className="w-4 h-4 mr-2" />
                            Stop
                          </DropdownMenuItem>
                        ) : null}
                        <DropdownMenuItem asChild>
                          <Link to={`/scans/${scan.id}/clone`}>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Clone
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                          <button
                            onClick={() => scanApi.export(scan.id, 'json')}
                            className="w-full flex items-center"
                          >
                            <Download className="w-4 h-4 mr-2" />
                            Export
                          </button>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDelete(scan.id)}
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Scan</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this scan? This action cannot be undone.
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
