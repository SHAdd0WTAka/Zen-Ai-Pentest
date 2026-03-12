// ============================================
// Zen-AI-Pentest Platform - Plugin Detail Page
// ============================================

import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Puzzle,
  Power,
  PowerOff,
  Settings,
  Trash2,
  Loader2,
  AlertCircle,
  CheckCircle,
  User,
  Tag,
  Calendar,
  Code,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { pluginApi } from '@/services/api';
import { toast } from 'sonner';
import type { Plugin, PluginStatus } from '@/types';

// ============================================
// Status Config
// ============================================
const statusConfig: Record<PluginStatus, { label: string; color: string; icon: React.ElementType }> = {
  active: { label: 'Active', color: 'bg-green-500', icon: CheckCircle },
  inactive: { label: 'Inactive', color: 'bg-gray-500', icon: PowerOff },
  error: { label: 'Error', color: 'bg-red-500', icon: AlertCircle },
  updating: { label: 'Updating', color: 'bg-yellow-500', icon: Loader2 },
};

// ============================================
// Main Plugin Detail Page
// ============================================
export function PluginDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [configValues, setConfigValues] = useState<Record<string, any>>({});

  const { data: plugin, isLoading } = useQuery({
    queryKey: ['plugin', id],
    queryFn: () => pluginApi.get(id!),
  });

  // Mutations
  const enableMutation = useMutation({
    mutationFn: pluginApi.enable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugin', id] });
      toast.success('Plugin enabled');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to enable plugin');
    },
  });

  const disableMutation = useMutation({
    mutationFn: pluginApi.disable,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugin', id] });
      toast.success('Plugin disabled');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to disable plugin');
    },
  });

  const uninstallMutation = useMutation({
    mutationFn: pluginApi.uninstall,
    onSuccess: () => {
      toast.success('Plugin uninstalled');
      window.location.href = '/plugins';
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error?.message || 'Failed to uninstall plugin');
    },
  });

  const handleToggle = () => {
    if (plugin?.status === 'active') {
      disableMutation.mutate(id!);
    } else {
      enableMutation.mutate(id!);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!plugin) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold">Plugin not found</h2>
        <Button asChild className="mt-4">
          <Link to="/plugins">Back to Plugins</Link>
        </Button>
      </div>
    );
  }

  const status = statusConfig[plugin.status];
  const StatusIcon = status.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/plugins">
              <ArrowLeft className="w-5 h-5" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <Puzzle className="w-8 h-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">{plugin.name}</h1>
            </div>
            <div className="flex items-center gap-3 mt-2">
              <Badge className={status.color}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {status.label}
              </Badge>
              <Badge variant="outline">v{plugin.version}</Badge>
              <Badge variant="outline">{plugin.type}</Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={plugin.status === 'active' ? 'destructive' : 'default'}
            onClick={handleToggle}
            disabled={enableMutation.isPending || disableMutation.isPending}
          >
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
          </Button>
          <Button variant="outline" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="w-4 h-4 mr-2" />
            Uninstall
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="manifest">Manifest</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Plugin Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">ID</span>
                <span className="font-mono text-sm">{plugin.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Description</span>
                <span>{plugin.description}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Version</span>
                <span>v{plugin.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Author</span>
                <span className="flex items-center gap-1">
                  <User className="w-4 h-4" />
                  {plugin.author}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type</span>
                <Badge variant="outline">{plugin.type}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Category</span>
                <span>{plugin.category}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Installed</span>
                <span>{plugin.installedAt ? new Date(plugin.installedAt).toLocaleString() : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Updated</span>
                <span>{plugin.updatedAt ? new Date(plugin.updatedAt).toLocaleString() : 'N/A'}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tags</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {plugin.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    <Tag className="w-3 h-3 mr-1" />
                    {tag}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="configuration">
          <Card>
            <CardHeader>
              <CardTitle>Plugin Configuration</CardTitle>
              <CardDescription>Configure plugin settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {plugin.config ? (
                Object.entries(plugin.config.settings).map(([key, value]) => (
                  <div key={key} className="space-y-2">
                    <Label htmlFor={key} className="capitalize">
                      {key.replace(/_/g, ' ')}
                    </Label>
                    <Input
                      id={key}
                      value={configValues[key] ?? value}
                      onChange={(e) =>
                        setConfigValues({ ...configValues, [key]: e.target.value })
                      }
                    />
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Settings className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No configuration options available</p>
                </div>
              )}
              {plugin.config && (
                <Button className="w-full">Save Configuration</Button>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manifest">
          <Card>
            <CardHeader>
              <CardTitle>Plugin Manifest</CardTitle>
              <CardDescription>Technical details and dependencies</CardDescription>
            </CardHeader>
            <CardContent>
              {plugin.manifest ? (
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Entry Point</h4>
                    <code className="bg-muted px-2 py-1 rounded">{plugin.manifest.entryPoint}</code>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Dependencies</h4>
                    <div className="flex flex-wrap gap-2">
                      {plugin.manifest.dependencies.map((dep) => (
                        <Badge key={dep} variant="outline">
                          <Code className="w-3 h-3 mr-1" />
                          {dep}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Permissions</h4>
                    <div className="flex flex-wrap gap-2">
                      {plugin.manifest.permissions.map((perm) => (
                        <Badge key={perm} variant="secondary">
                          {perm}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Hooks</h4>
                    <div className="flex flex-wrap gap-2">
                      {plugin.manifest.hooks.map((hook) => (
                        <Badge key={hook} variant="outline">
                          {hook}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Code className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No manifest available</p>
                </div>
              )}
            </CardContent>
          </Card>
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
            <Button variant="destructive" onClick={() => uninstallMutation.mutate(id!)}>
              Uninstall
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
