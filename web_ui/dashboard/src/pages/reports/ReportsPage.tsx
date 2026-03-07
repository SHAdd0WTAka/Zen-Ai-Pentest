// ============================================
// Zen-AI-Pentest Platform - Reports Page
// ============================================

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  Download,
  Trash2,
  MoreHorizontal,
  Loader2,
  Clock,
  CheckCircle,
  AlertCircle,
  FileIcon,
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
import { reportApi } from '@/services/api';
import { toast } from 'sonner';
import type { ReportStatus, ReportFormat } from '@/types';

// ============================================
// Status Badge Component
// ============================================
function StatusBadge({ status }: { status: ReportStatus }) {
  const config: Record<ReportStatus, { variant: string; icon: React.ElementType; label: string }> = {
    pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
    generating: { variant: 'default', icon: Loader2, label: 'Generating' },
    completed: { variant: 'success', icon: CheckCircle, label: 'Completed' },
    failed: { variant: 'destructive', icon: AlertCircle, label: 'Failed' },
  };

  const { variant, icon: Icon, label } = config[status];

  return (
    <Badge variant={variant as any} className="flex items-center gap-1 w-fit">
      <Icon className={`w-3 h-3 ${status === 'generating' && 'animate-spin'}`} />
      {label}
    </Badge>
  );
}

// ============================================
// Format Icon Component
// ============================================
function FormatIcon({ format }: { format: ReportFormat }) {
  const colors: Record<ReportFormat, string> = {
    pdf: 'text-red-500',
    html: 'text-orange-500',
    json: 'text-blue-500',
    xml: 'text-purple-500',
    csv: 'text-green-500',
  };

  return <FileIcon className={`w-4 h-4 ${colors[format]}`} />;
}

// ============================================
// Main Reports Page
// ============================================
export function ReportsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<string | null>(null);

  // Fetch reports
  const { data, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportApi.list({ page: 1, limit: 50 }),
  });

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: reportApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Report deleted');
      setDeleteDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to delete report');
    },
  });

  const handleDelete = (id: string) => {
    setReportToDelete(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (reportToDelete) {
      deleteMutation.mutate(reportToDelete);
    }
  };

  const handleDownload = async (id: string, name: string) => {
    try {
      const blob = await reportApi.download(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      toast.error('Failed to download report');
    }
  };

  const filteredReports =
    data?.reports.filter((report) =>
      report.name.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            Generate and manage security reports
          </p>
        </div>
        <Button asChild>
          <Link to="/reports/new">
            <Plus className="w-4 h-4 mr-2" />
            New Report
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search reports..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Reports Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Format</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                </TableCell>
              </TableRow>
            ) : filteredReports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  No reports found
                </TableCell>
              </TableRow>
            ) : (
              filteredReports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>
                    <Link to={`/reports/${report.id}`} className="font-medium hover:underline">
                      {report.name}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{report.type}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <FormatIcon format={report.format} />
                      <span className="uppercase">{report.format}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={report.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(report.createdAt).toLocaleDateString()}
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
                          <Link to={`/reports/${report.id}`}>View Details</Link>
                        </DropdownMenuItem>
                        {report.status === 'completed' && (
                          <DropdownMenuItem
                            onClick={() => handleDownload(report.id, report.name)}
                          >
                            <Download className="w-4 h-4 mr-2" />
                            Download
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDelete(report.id)}
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
            <DialogTitle>Delete Report</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this report? This action cannot be undone.
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
