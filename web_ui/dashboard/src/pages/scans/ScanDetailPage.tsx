// ============================================
// Zen-AI-Pentest Platform - Scan Detail Page
// ============================================

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Play,
  Pause,
  Square,
  Download,
  Trash2,
  Clock,
  Target,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  FileText,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { scanApi } from '@/services/api';
import { useWebSocket } from '@/services/websocket';
import { useScanStore } from '@/store';
import { toast } from 'sonner';
import type { Scan, ScanStatus } from '@/types';

// ============================================
// Status Config
// ============================================
const statusConfig: Record<ScanStatus, { label: string; color: string; icon: React.ElementType }> = {
  pending: { label: 'Pending', color: 'bg-gray-500', icon: Clock },
  queued: { label: 'Queued', color: 'bg-blue-500', icon: Clock },
  running: { label: 'Running', color: 'bg-green-500', icon: Activity },
  paused: { label: 'Paused', color: 'bg-yellow-500', icon: Pause },
  completed: { label: 'Completed', color: 'bg-green-600', icon: CheckCircle },
  failed: { label: 'Failed', color: 'bg-red-500', icon: XCircle },
  cancelled: { label: 'Cancelled', color: 'bg-gray-500', icon: AlertCircle },
};

// ============================================
// Main Scan Detail Page
// ============================================
export function ScanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { startScan, stopScan } = useWebSocket();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [logsExpanded, setLogsExpanded] = useState(false);

  // Fetch scan details
  const { data: scan, isLoading } = useQuery({
    queryKey: ['scan', id],
    queryFn: () => scanApi.get(id!),
    refetchInterval: (data: any) =>
      data?.status === 'running' || data?.status === 'queued' ? 2000 : false,
  });

  // Fetch scan logs
  const { data: logs } = useQuery({
    queryKey: ['scan-logs', id],
    queryFn: () => scanApi.getLogs(id!, 100),
    refetchInterval: (data) =>
      scan?.status === 'running' || scan?.status === 'queued' ? 2000 : false,
    enabled: !!id,
  });

  // Mutations
  const startMutation = useMutation({
    mutationFn: scanApi.start,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan', id] });
      toast.success('Scan started');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to start scan');
    },
  });

  const stopMutation = useMutation({
    mutationFn: scanApi.stop,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan', id] });
      toast.success('Scan stopped');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to stop scan');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: scanApi.delete,
    onSuccess: () => {
      toast.success('Scan deleted');
      navigate('/scans');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to delete scan');
    },
  });

  const handleStart = () => {
    startScan(id!);
    startMutation.mutate(id!);
  };

  const handleStop = () => {
    stopScan(id!);
    stopMutation.mutate(id!);
  };

  const handleDelete = () => {
    deleteMutation.mutate(id!);
  };

  const handleExport = async (format: string) => {
    try {
      const blob = await scanApi.export(id!, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan-${id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      toast.error('Failed to export scan');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold">Scan not found</h2>
        <Button asChild className="mt-4">
          <Link to="/scans">Back to Scans</Link>
        </Button>
      </div>
    );
  }

  const status = statusConfig[scan.status];
  const StatusIcon = status.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/scans')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{scan.name}</h1>
            <div className="flex items-center gap-3 mt-2">
              <Badge className={status.color}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {status.label}
              </Badge>
              <span className="text-sm text-muted-foreground font-mono">{scan.target}</span>
              <Badge variant="outline">{scan.type}</Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {(scan.status === 'pending' || scan.status === 'paused') && (
            <Button onClick={handleStart}>
              <Play className="w-4 h-4 mr-2" />
              Start
            </Button>
          )}
          {scan.status === 'running' && (
            <Button variant="destructive" onClick={handleStop}>
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          )}
          <Button variant="outline" onClick={() => handleExport('json')}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Progress */}
      {(scan.status === 'running' || scan.status === 'queued') && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Scan Progress</span>
              <span className="text-sm text-muted-foreground">{scan.progress}%</span>
            </div>
            <Progress value={scan.progress} className="h-2" />
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Target
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-muted-foreground" />
                  <span className="font-mono text-sm">{scan.target}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Created
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">
                    {new Date(scan.createdAt).toLocaleString()}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Duration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">
                    {scan.metrics?.duration
                      ? `${Math.floor(scan.metrics.duration / 60)}m ${scan.metrics.duration % 60}s`
                      : 'N/A'}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Intensity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant="outline" className="capitalize">
                  {scan.config.intensity}
                </Badge>
              </CardContent>
            </Card>
          </div>

          {scan.results?.summary && (
            <Card>
              <CardHeader>
                <CardTitle>Results Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <Target className="w-5 h-5 text-blue-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{scan.results.summary.totalHosts}</p>
                      <p className="text-xs text-muted-foreground">Hosts Discovered</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                      <Activity className="w-5 h-5 text-green-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{scan.results.summary.openPorts}</p>
                      <p className="text-xs text-muted-foreground">Open Ports</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                      <ShieldAlert className="w-5 h-5 text-red-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{scan.results.summary.vulnerabilities}</p>
                      <p className="text-xs text-muted-foreground">Vulnerabilities</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-4 bg-muted rounded-lg">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-purple-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{scan.results.summary.totalPorts}</p>
                      <p className="text-xs text-muted-foreground">Ports Scanned</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="results">
          {scan.results ? (
            <Card>
              <CardHeader>
                <CardTitle>Scan Results</CardTitle>
                <CardDescription>Detailed findings from the scan</CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-sm">
                  {JSON.stringify(scan.results, null, 2)}
                </pre>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">No results yet</h3>
                <p className="text-muted-foreground">
                  Results will appear here once the scan is complete
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Scan Logs</CardTitle>
                <CardDescription>Real-time scan output</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setLogsExpanded(!logsExpanded)}
              >
                {logsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            </CardHeader>
            <CardContent>
              <ScrollArea className={logsExpanded ? 'h-[600px]' : 'h-[300px]'}>
                <div className="font-mono text-sm space-y-1">
                  {logs?.map((log, index) => (
                    <div key={index} className="text-muted-foreground">
                      <span className="text-xs text-muted-foreground/50">
                        {new Date().toLocaleTimeString()}
                      </span>{' '}
                      {log}
                    </div>
                  )) || (
                    <div className="text-muted-foreground">No logs available</div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Delete Dialog */}
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
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
