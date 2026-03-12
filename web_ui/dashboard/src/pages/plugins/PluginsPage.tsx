// ============================================
// Zen-AI-Pentest Platform - Plugins Page
// ============================================

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  RefreshCw,
  MoreHorizontal,
  Puzzle,
  Power,
  PowerOff,
  Loader2,
  AlertCircle,
  CheckCircle,
  Trash2,
  Download,
  Store,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { pluginApi } from '@/services/api';
import { toast } from 'sonner';
import type { Plugin, PluginStatus } from '@/types';

// ============================================
// Status Badge Component
// ============================================
function StatusBadge({ status }: { status: PluginStatus }) {
  const config: Record<PluginStatus, { variant: string; icon: React.ElementType; label: string }> = {
    active: { variant: 'success', icon: CheckCircle, label: 'Active' },
    inactive: { variant: 'secondary', icon: PowerOff, label: 'Inactive' },
    error: { variant: 'destructive', icon: AlertCircle, label: 'Error' },
    updating: { variant: 'warning', icon: RefreshCw, label: 'Updating' },
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
// Main Plugins Page
// ============================================
export function PluginsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('installed');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [pluginToDelete, setPluginToDelete] = useState<string | null>(null);

  // Fetch installed plugins
  const { data: plugins, isLoading } = useQuery({
    queryKey: ['plugins'],
    queryFn: () => pluginApi.list(),
  });

  // Fetch marketplace plugins
  const { data: marketplacePlugins } = useQuery({
    queryKey: ['plugins-marketplace'],
    queryFn: () => pluginApi.getMarketplace(),
    enabled: activeTab === 'marketplace',
  });

  // Mutations
  const enableMutation = useMutation({
    mutationFn: pluginApi.enable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      toast.success('Plugin enabled');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to enable plugin');
    },
  });

  const disableMutation = useMutation({
    mutationFn: pluginApi.disable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      toast.success('Plugin disabled');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to disable plugin');
    },
  });

  const uninstallMutation = useMutation({
    mutationFn: pluginApi.uninstall,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      toast.success('Plugin uninstalled');
      setDeleteDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to uninstall plugin');
    },
  });

  const handleToggle = (plugin: Plugin) => {
    if (plugin.status === 'active') {
      disableMutation.mutate(plugin.id);
    } else {
      enableMutation.mutate(plugin.id);
    }
  };

  const handleDelete = (id: string) => {
    setPluginToDelete(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (pluginToDelete) {
      uninstallMutation.mutate(pluginToDelete);
    }
  };

  const filteredPlugins =
    plugins?.filter(
      (plugin) =>
        plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        plugin.description.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Plugins</h1>
          <p className="text-muted-foreground">
            Manage and extend functionality with plugins
          </p>
        </div>
        <Button asChild>
          <Link to="/plugins/install">
            <Plus className="w-4 h-4 mr-2" />
            Install Plugin
          </Link>
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="installed">Installed</TabsTrigger>
          <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
        </TabsList>

        <TabsContent value="installed" className="space-y-6">
          {/* Filters */}
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search plugins..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['plugins'] })}
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>

          {/* Plugins Table */}
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Author</TableHead>
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
                ) : filteredPlugins.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      No plugins found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredPlugins.map((plugin) => (
                    <TableRow key={plugin.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Puzzle className="w-4 h-4 text-muted-foreground" />
                          <div>
                            <Link to={`/plugins/${plugin.id}`} className="font-medium hover:underline">
                              {plugin.name}
                            </Link>
                            <p className="text-xs text-muted-foreground">{plugin.description}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{plugin.type}</Badge>
                      </TableCell>
                      <TableCell>v{plugin.version}</TableCell>
                      <TableCell>
                        <StatusBadge status={plugin.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">{plugin.author}</TableCell>
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
                              <Link to={`/plugins/${plugin.id}`}>View Details</Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleToggle(plugin)}>
                              {plugin.status === 'active' ? (
                                <>
                                  <PowerOff className="w-4 h-4 mr-2" />
                                  Disable
                                </>
                              ) : (
                                <>
                                  <Power className="w-4 h-4 mr-2" />
                                  Enable
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(plugin.id)}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Uninstall
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
        </TabsContent>

        <TabsContent value="marketplace" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {marketplacePlugins?.map((plugin) => (
              <Card key={plugin.id}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Store className="w-5 h-5" />
                    {plugin.name}
                  </CardTitle>
                  <CardDescription>{plugin.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">By {plugin.author}</span>
                    <span className="text-muted-foreground">{plugin.downloads} downloads</span>
                  </div>
                  <Button className="w-full mt-4">
                    <Download className="w-4 h-4 mr-2" />
                    Install
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Uninstall Plugin</DialogTitle>
            <DialogDescription>
              Are you sure you want to uninstall this plugin? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Uninstall
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
