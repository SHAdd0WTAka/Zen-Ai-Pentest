// ============================================
// Zen-AI-Pentest Platform - Profile Page
// User Profile Management
// ============================================

import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Shield,
  Key,
  Camera,
  Save,
  RefreshCw,
  Lock,
  Smartphone,
  Bell,
  History,
  Edit3,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { authApi } from '@/services/api';

// ============================================
// Types
// ============================================
interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: string;
  department: string;
  phone?: string;
  timezone: string;
  language: string;
  joinedAt: string;
  lastLogin: string;
  mfaEnabled: boolean;
}

interface Activity {
  id: string;
  action: string;
  target: string;
  timestamp: string;
  ip: string;
}

// ============================================
// Helper Functions
// ============================================
const formatDate = (date: string): string => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
};

const formatTimeAgo = (date: string): string => {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

// ============================================
// Main Component
// ============================================
export function ProfilePage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [show2FADialog, setShow2FADialog] = useState(false);
  const [passwordData, setPasswordData] = useState({
    current: '',
    new: '',
    confirm: '',
  });

  const { data: profile, isLoading } = useQuery({
    queryKey: ['user-profile'],
    queryFn: authApi.me,
  });

  const updateProfile = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      setIsEditing(false);
      toast.success('Profile updated successfully');
    },
  });

  const changePassword = useMutation({
    mutationFn: ({ oldPassword, newPassword }: { oldPassword: string; newPassword: string }) =>
      authApi.changePassword(oldPassword, newPassword),
    onSuccess: () => {
      setPasswordData({ current: '', new: '', confirm: '' });
      toast.success('Password changed successfully');
    },
    onError: () => {
      toast.error('Failed to change password');
    },
  });

  const handlePasswordChange = () => {
    if (passwordData.new !== passwordData.confirm) {
      toast.error('New passwords do not match');
      return;
    }
    if (passwordData.new.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    changePassword.mutate({
      oldPassword: passwordData.current,
      newPassword: passwordData.new,
    });
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      toast.success('Avatar uploaded successfully');
    }
  };

  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase();
  };

  if (isLoading || !profile) {
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
          <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
          <p className="text-muted-foreground">
            Manage your account settings and preferences
          </p>
        </div>
        {isEditing && (
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => updateProfile.mutate(profile)}
              disabled={updateProfile.isPending}
            >
              {updateProfile.isPending ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Changes
            </Button>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Profile Sidebar */}
        <div className="space-y-6">
          {/* Avatar Card */}
          <Card>
            <CardContent className="pt-6 text-center">
              <div className="relative inline-block">
                <Avatar className="h-32 w-32 mx-auto">
                  <AvatarImage src={profile.avatar} />
                  <AvatarFallback className="text-3xl bg-primary text-primary-foreground">
                    {getInitials(profile.name || profile.username || 'U')}
                  </AvatarFallback>
                </Avatar>
                <Button
                  size="icon"
                  variant="secondary"
                  className="absolute bottom-0 right-0 rounded-full"
                  onClick={handleAvatarClick}
                >
                  <Camera className="h-4 w-4" />
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
              <h3 className="mt-4 text-xl font-semibold">{profile.name || profile.username}</h3>
              <p className="text-muted-foreground">{profile.email}</p>
              <Badge className="mt-2">{profile.role}</Badge>
              <div className="mt-4 flex justify-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                  <Edit3 className="mr-2 h-4 w-4" />
                  Edit Profile
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Account Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Member Since</span>
                <span>{profile.joinedAt ? formatDate(profile.joinedAt) : 'N/A'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Last Login</span>
                <span>{profile.lastLogin ? formatTimeAgo(profile.lastLogin) : 'N/A'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Department</span>
                <span>{profile.department || 'N/A'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Timezone</span>
                <span>{profile.timezone || 'UTC'}</span>
              </div>
            </CardContent>
          </Card>

          {/* Security Status */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Security Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-500" />
                  <span className="text-sm">2FA Enabled</span>
                </div>
                <Badge variant={profile.mfaEnabled ? 'default' : 'secondary'}>
                  {profile.mfaEnabled ? 'Active' : 'Disabled'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Password</span>
                </div>
                <Badge variant="default">Strong</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Notifications</span>
                </div>
                <Badge variant="default">Enabled</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2">
          <Tabs defaultValue="profile" className="space-y-6">
            <TabsList>
              <TabsTrigger value="profile">
                <User className="mr-2 h-4 w-4" />
                Profile
              </TabsTrigger>
              <TabsTrigger value="security">
                <Shield className="mr-2 h-4 w-4" />
                Security
              </TabsTrigger>
              <TabsTrigger value="activity">
                <History className="mr-2 h-4 w-4" />
                Activity
              </TabsTrigger>
            </TabsList>

            {/* Profile Tab */}
            <TabsContent value="profile" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Personal Information</CardTitle>
                  <CardDescription>
                    Update your personal details and contact information
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="name">Full Name</Label>
                      <Input
                        id="name"
                        defaultValue={profile.name}
                        disabled={!isEditing}
                        onChange={(e) =>
                          updateProfile.mutate({ ...profile, name: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input
                        id="email"
                        type="email"
                        defaultValue={profile.email}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone Number</Label>
                      <Input
                        id="phone"
                        defaultValue={profile.phone}
                        disabled={!isEditing}
                        onChange={(e) =>
                          updateProfile.mutate({ ...profile, phone: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="department">Department</Label>
                      <Input
                        id="department"
                        defaultValue={profile.department}
                        disabled={!isEditing}
                        onChange={(e) =>
                          updateProfile.mutate({ ...profile, department: e.target.value })
                        }
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Change Password</CardTitle>
                  <CardDescription>
                    Update your password to keep your account secure
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="currentPassword">Current Password</Label>
                    <div className="relative">
                      <Input
                        id="currentPassword"
                        type={showPassword ? 'text' : 'password'}
                        value={passwordData.current}
                        onChange={(e) =>
                          setPasswordData({ ...passwordData, current: e.target.value })
                        }
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute right-2 top-1/2 -translate-y-1/2"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                    <Input
                      id="newPassword"
                      type="password"
                      value={passwordData.new}
                      onChange={(e) =>
                        setPasswordData({ ...passwordData, new: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      value={passwordData.confirm}
                      onChange={(e) =>
                        setPasswordData({ ...passwordData, confirm: e.target.value })
                      }
                    />
                  </div>
                  <Button
                    onClick={handlePasswordChange}
                    disabled={
                      changePassword.isPending ||
                      !passwordData.current ||
                      !passwordData.new ||
                      !passwordData.confirm
                    }
                  >
                    {changePassword.isPending ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Key className="mr-2 h-4 w-4" />
                    )}
                    Change Password
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Two-Factor Authentication</CardTitle>
                  <CardDescription>
                    Add an extra layer of security to your account
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/10">
                        <Shield className="h-5 w-5 text-green-500" />
                      </div>
                      <div>
                        <p className="font-medium">Authenticator App</p>
                        <p className="text-sm text-muted-foreground">
                          {profile.mfaEnabled ? 'Using Google Authenticator' : 'Not configured'}
                        </p>
                      </div>
                    </div>
                    <Badge variant={profile.mfaEnabled ? 'default' : 'secondary'}>
                      {profile.mfaEnabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <Separator className="my-4" />
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setShow2FADialog(true)}>
                      {profile.mfaEnabled ? 'Reconfigure 2FA' : 'Enable 2FA'}
                    </Button>
                    {profile.mfaEnabled && (
                      <Button variant="outline" className="text-destructive">
                        Disable 2FA
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Active Sessions</CardTitle>
                  <CardDescription>
                    Manage your active login sessions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {[
                      {
                        device: 'Chrome on macOS',
                        location: 'New York, USA',
                        current: true,
                      },
                      {
                        device: 'Safari on iPhone',
                        location: 'New York, USA',
                        current: false,
                      },
                    ].map((session, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                            <Smartphone className="h-5 w-5" />
                          </div>
                          <div>
                            <p className="font-medium flex items-center gap-2">
                              {session.device}
                              {session.current && (
                                <Badge variant="default" className="text-xs">
                                  Current
                                </Badge>
                              )}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {session.location}
                            </p>
                          </div>
                        </div>
                        {!session.current && (
                          <Button variant="outline" size="sm">
                            Revoke
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Activity Tab */}
            <TabsContent value="activity">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>
                    View your recent account activity and login history
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[
                      { id: '1', action: 'Logged in', target: 'Web Application', timestamp: new Date().toISOString(), ip: '192.168.1.100' },
                      { id: '2', action: 'Updated profile', target: 'Account Settings', timestamp: new Date(Date.now() - 86400000).toISOString(), ip: '192.168.1.100' },
                    ].map((activity) => (
                      <div
                        key={activity.id}
                        className="flex items-start gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                          <History className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <p className="font-medium">{activity.action}</p>
                            <span className="text-sm text-muted-foreground">
                              {formatTimeAgo(activity.timestamp)}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {activity.target}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            IP: {activity.ip}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* 2FA Dialog */}
      <Dialog open={show2FADialog} onOpenChange={setShow2FADialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Two-Factor Authentication</DialogTitle>
            <DialogDescription>
              Scan the QR code with your authenticator app to enable 2FA.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col items-center py-4">
            <div className="w-48 h-48 bg-muted rounded-lg flex items-center justify-center">
              <span className="text-muted-foreground">QR Code Placeholder</span>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              Enter the 6-digit code from your authenticator app
            </p>
            <Input className="w-32 mt-2 text-center" placeholder="000000" maxLength={6} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShow2FADialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShow2FADialog(false)}>Verify</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
