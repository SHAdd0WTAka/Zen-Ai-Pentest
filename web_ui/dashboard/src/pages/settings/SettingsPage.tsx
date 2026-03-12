// ============================================
// Zen-AI-Pentest Platform - Settings Page
// System Settings and Configuration
// ============================================

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings,
  Shield,
  Bell,
  Database,
  Globe,
  Server,
  Save,
  RefreshCw,
  Download,
  Upload,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { settingsApi } from '@/services/api';

// ============================================
// Main Component
// ============================================
export function SettingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('general');

  const { data: settings, isLoading } = useQuery({
    queryKey: ['system-settings'],
    queryFn: settingsApi.get,
  });

  const updateSettings = useMutation({
    mutationFn: settingsApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      toast.success('Settings saved successfully');
    },
    onError: () => {
      toast.error('Failed to save settings');
    },
  });

  const handleSave = (section: string, data: any) => {
    updateSettings.mutate({ [section]: data });
  };

  if (isLoading || !settings) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Settings className="h-8 w-8" />
            Settings
          </h1>
          <p className="text-muted-foreground">
            Configure platform settings and preferences
          </p>
        </div>
      </div>

      {/* Settings Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 lg:w-auto">
          <TabsTrigger value="general">
            <Globe className="mr-2 h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="security">
            <Shield className="mr-2 h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="scanning">
            <Server className="mr-2 h-4 w-4" />
            Scanning
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="mr-2 h-4 w-4" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Platform Information</CardTitle>
              <CardDescription>
                Configure basic platform settings and branding
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="platformName">Platform Name</Label>
                  <Input
                    id="platformName"
                    defaultValue={settings.general?.platformName}
                    onBlur={(e) => handleSave('general', { platformName: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="organization">Organization</Label>
                  <Input
                    id="organization"
                    defaultValue={settings.general?.organization}
                    onBlur={(e) => handleSave('general', { organization: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select
                    defaultValue={settings.general?.timezone}
                    onValueChange={(v) => handleSave('general', { timezone: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">Eastern Time</SelectItem>
                      <SelectItem value="America/Chicago">Central Time</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                      <SelectItem value="Europe/London">London</SelectItem>
                      <SelectItem value="Europe/Berlin">Berlin</SelectItem>
                      <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dateFormat">Date Format</Label>
                  <Select
                    defaultValue={settings.general?.dateFormat}
                    onValueChange={(v) => handleSave('general', { dateFormat: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                      <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                      <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select
                    defaultValue={settings.general?.language}
                    onValueChange={(v) => handleSave('general', { language: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="ja">Japanese</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Management</CardTitle>
              <CardDescription>Manage platform data and backups</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Download className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Export Data</p>
                    <p className="text-sm text-muted-foreground">
                      Download all platform data as JSON
                    </p>
                  </div>
                </div>
                <Button variant="outline" onClick={() => settingsApi.createBackup()}>
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Upload className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Import Data</p>
                    <p className="text-sm text-muted-foreground">
                      Import data from a backup file
                    </p>
                  </div>
                </div>
                <Button variant="outline">
                  <Upload className="mr-2 h-4 w-4" />
                  Import
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Authentication</CardTitle>
              <CardDescription>Configure authentication and access controls</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Multi-Factor Authentication</Label>
                  <p className="text-sm text-muted-foreground">
                    Require MFA for all user accounts
                  </p>
                </div>
                <Switch
                  checked={settings.security?.mfaEnabled}
                  onCheckedChange={(v) => handleSave('security', { mfaEnabled: v })}
                />
              </div>
              <Separator />
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="passwordExpiry">Password Expiry (days)</Label>
                  <Input
                    id="passwordExpiry"
                    type="number"
                    defaultValue={settings.security?.passwordExpiry}
                    onBlur={(e) => handleSave('security', { passwordExpiry: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sessionTimeout">Session Timeout (minutes)</Label>
                  <Input
                    id="sessionTimeout"
                    type="number"
                    defaultValue={settings.security?.sessionTimeout}
                    onBlur={(e) => handleSave('security', { sessionTimeout: parseInt(e.target.value) })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Network Access</CardTitle>
              <CardDescription>Configure IP whitelisting and domain restrictions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="ipWhitelist">IP Whitelist (CIDR notation, one per line)</Label>
                <Textarea
                  id="ipWhitelist"
                  defaultValue={settings.security?.ipWhitelist?.join('\n')}
                  onBlur={(e) => handleSave('security', { ipWhitelist: e.target.value.split('\n') })}
                  rows={3}
                  placeholder="192.168.1.0/24&#10;10.0.0.0/8"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="allowedDomains">Allowed Email Domains</Label>
                <Input
                  id="allowedDomains"
                  defaultValue={settings.security?.allowedDomains?.join(', ')}
                  onBlur={(e) =>
                    handleSave('security', {
                      allowedDomains: e.target.value.split(',').map((d) => d.trim()),
                    })
                  }
                  placeholder="company.com, subsidiary.com"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scanning Settings */}
        <TabsContent value="scanning" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Scan Configuration</CardTitle>
              <CardDescription>Configure default scan behavior and limits</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="defaultScanTimeout">Default Scan Timeout (seconds)</Label>
                  <Input
                    id="defaultScanTimeout"
                    type="number"
                    defaultValue={settings.scanning?.defaultScanTimeout}
                    onBlur={(e) =>
                      handleSave('scanning', { defaultScanTimeout: parseInt(e.target.value) })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="maxConcurrentScans">Max Concurrent Scans</Label>
                  <Input
                    id="maxConcurrentScans"
                    type="number"
                    defaultValue={settings.scanning?.maxConcurrentScans}
                    onBlur={(e) =>
                      handleSave('scanning', { maxConcurrentScans: parseInt(e.target.value) })
                    }
                  />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="scanRetentionDays">Scan Retention (days)</Label>
                  <Input
                    id="scanRetentionDays"
                    type="number"
                    defaultValue={settings.scanning?.scanRetentionDays}
                    onBlur={(e) =>
                      handleSave('scanning', { scanRetentionDays: parseInt(e.target.value) })
                    }
                  />
                </div>
                <div className="flex items-center justify-between pt-6">
                  <div className="space-y-0.5">
                    <Label>Auto-Schedule Scans</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically schedule recurring scans
                    </p>
                  </div>
                  <Switch
                    checked={settings.scanning?.autoSchedule}
                    onCheckedChange={(v) => handleSave('scanning', { autoSchedule: v })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Settings */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Channels</CardTitle>
              <CardDescription>Configure how you receive notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Bell className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Email Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Receive notifications via email
                    </p>
                  </div>
                </div>
                <Switch
                  checked={settings.notifications?.emailEnabled}
                  onCheckedChange={(v) => handleSave('notifications', { emailEnabled: v })}
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Slack Integration</p>
                    <p className="text-sm text-muted-foreground">
                      Send notifications to Slack channels
                    </p>
                  </div>
                </div>
                <Switch
                  checked={settings.notifications?.slackEnabled}
                  onCheckedChange={(v) => handleSave('notifications', { slackEnabled: v })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="webhookUrl">Webhook URL</Label>
                <Input
                  id="webhookUrl"
                  defaultValue={settings.notifications?.webhookUrl}
                  onBlur={(e) => handleSave('notifications', { webhookUrl: e.target.value })}
                  placeholder="https://hooks.slack.com/services/..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="alertThreshold">Minimum Alert Severity</Label>
                <Select
                  defaultValue={settings.notifications?.alertThreshold}
                  onValueChange={(v) => handleSave('notifications', { alertThreshold: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low and above</SelectItem>
                    <SelectItem value="medium">Medium and above</SelectItem>
                    <SelectItem value="high">High and above</SelectItem>
                    <SelectItem value="critical">Critical only</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
