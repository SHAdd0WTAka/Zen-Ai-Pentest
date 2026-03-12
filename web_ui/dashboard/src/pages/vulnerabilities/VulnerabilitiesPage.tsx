// ============================================
// Zen-AI-Pentest Platform - Vulnerabilities Page
// ============================================

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Search,
  Filter,
  RefreshCw,
  MoreHorizontal,
  ShieldAlert,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Download,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { vulnerabilityApi } from '@/services/api';
import { useVulnerabilityStore } from '@/store';
import { toast } from 'sonner';
import type { Severity, VulnerabilityStatus } from '@/types';

// ============================================
// Severity Badge Component
// ============================================
function SeverityBadge({ severity }: { severity: Severity }) {
  const config: Record<Severity, { color: string; icon: React.ElementType }> = {
    critical: { color: 'bg-red-500', icon: XCircle },
    high: { color: 'bg-orange-500', icon: AlertTriangle },
    medium: { color: 'bg-yellow-500', icon: AlertTriangle },
    low: { color: 'bg-blue-500', icon: Info },
    info: { color: 'bg-gray-500', icon: Info },
  };

  const { color, icon: Icon } = config[severity];

  return (
    <Badge className={`${color} text-white flex items-center gap-1 w-fit`}>
      <Icon className="w-3 h-3" />
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </Badge>
  );
}

// ============================================
// Status Badge Component
// ============================================
function StatusBadge({ status }: { status: VulnerabilityStatus }) {
  const config: Record<VulnerabilityStatus, { variant: string; label: string }> = {
    open: { variant: 'destructive', label: 'Open' },
    confirmed: { variant: 'default', label: 'Confirmed' },
    false_positive: { variant: 'secondary', label: 'False Positive' },
    mitigated: { variant: 'success', label: 'Mitigated' },
    accepted: { variant: 'outline', label: 'Accepted' },
  };

  const { variant, label } = config[status];

  return <Badge variant={variant as any}>{label}</Badge>;
}

// ============================================
// Main Vulnerabilities Page
// ============================================
export function VulnerabilitiesPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedVulnerability, setSelectedVulnerability] = useState<string | null>(null);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);

  // Fetch vulnerabilities
  const { data, isLoading } = useQuery({
    queryKey: ['vulnerabilities', severityFilter, statusFilter],
    queryFn: () =>
      vulnerabilityApi.list(
        {
          severity: severityFilter !== 'all' ? [severityFilter as Severity] : undefined,
          status: statusFilter !== 'all' ? [statusFilter as VulnerabilityStatus] : undefined,
        },
        { page: 1, limit: 50 }
      ),
  });

  // Mutations
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      vulnerabilityApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vulnerabilities'] });
      toast.success('Status updated');
      setStatusDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to update status');
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: vulnerabilityApi.analyze,
    onSuccess: () => {
      toast.success('AI analysis completed');
      queryClient.invalidateQueries({ queryKey: ['vulnerabilities'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to analyze');
    },
  });

  const filteredVulnerabilities =
    data?.vulnerabilities.filter(
      (v) =>
        v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        v.host.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

  const handleStatusChange = (status: string) => {
    if (selectedVulnerability) {
      updateStatusMutation.mutate({ id: selectedVulnerability, status });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Vulnerabilities</h1>
          <p className="text-muted-foreground">
            Manage and track discovered vulnerabilities
          </p>
        </div>
        <Button variant="outline" onClick={() => vulnerabilityApi.export()}>
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search vulnerabilities..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Severities</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="info">Info</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="confirmed">Confirmed</SelectItem>
            <SelectItem value="mitigated">Mitigated</SelectItem>
            <SelectItem value="false_positive">False Positive</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="icon"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['vulnerabilities'] })}
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Vulnerabilities Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Host</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>CVSS</TableHead>
              <TableHead>Discovered</TableHead>
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
            ) : filteredVulnerabilities.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  No vulnerabilities found
                </TableCell>
              </TableRow>
            ) : (
              filteredVulnerabilities.map((vuln) => (
                <TableRow key={vuln.id}>
                  <TableCell>
                    <Link to={`/vulnerabilities/${vuln.id}`} className="font-medium hover:underline">
                      {vuln.name}
                    </Link>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{vuln.host}</TableCell>
                  <TableCell>
                    <SeverityBadge severity={vuln.severity} />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={vuln.status} />
                  </TableCell>
                  <TableCell>
                    {vuln.cvss ? (
                      <span
                        className={`font-mono ${
                          vuln.cvss >= 9
                            ? 'text-red-500'
                            : vuln.cvss >= 7
                            ? 'text-orange-500'
                            : vuln.cvss >= 4
                            ? 'text-yellow-500'
                            : 'text-blue-500'
                        }`}
                      >
                        {vuln.cvss.toFixed(1)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(vuln.createdAt).toLocaleDateString()}
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
                          <Link to={`/vulnerabilities/${vuln.id}`}>View Details</Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => analyzeMutation.mutate(vuln.id)}>
                          <ShieldAlert className="w-4 h-4 mr-2" />
                          AI Analysis
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedVulnerability(vuln.id);
                            setStatusDialogOpen(true);
                          }}
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Change Status
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

      {/* Status Change Dialog */}
      <Dialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Status</DialogTitle>
            <DialogDescription>Select the new status for this vulnerability</DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-4">
            {['open', 'confirmed', 'mitigated', 'false_positive', 'accepted'].map((status) => (
              <Button
                key={status}
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleStatusChange(status)}
              >
                <StatusBadge status={status as VulnerabilityStatus} />
              </Button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
