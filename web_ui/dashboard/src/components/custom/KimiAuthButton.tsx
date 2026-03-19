// ============================================
// Kimi Device Authentication Button
// ============================================

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Zap, Check, AlertCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface KimiAuthStatus {
  authenticated: boolean;
  api_base: string;
  model: string;
  token_preview?: string;
}

export function KimiAuthButton() {
  const [status, setStatus] = useState<KimiAuthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/kimi-auth/status`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to check Kimi auth status:', error);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/kimi-auth/login`, {
        method: 'POST',
      });
      const data = await response.json();

      if (data.success) {
        toast.success('Kimi CLI login successful!');
        checkStatus();
      } else {
        toast.error(data.message || 'Login failed');
      }
    } catch (error) {
      toast.error('Failed to login. Make sure Kimi CLI is installed.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/kimi-auth/logout`, {
        method: 'POST',
      });
      const data = await response.json();

      if (data.success) {
        toast.success('Logged out successfully');
        setStatus(null);
      }
    } catch (error) {
      toast.error('Logout failed');
    } finally {
      setLoading(false);
    }
  };

  const getToken = async () => {
    try {
      const response = await fetch(`${API_URL}/kimi-auth/token`);
      if (response.ok) {
        const data = await response.json();
        toast.success('Token retrieved successfully');
        console.log('Token preview:', data.token_preview);
      } else {
        toast.error('Failed to get token');
      }
    } catch (error) {
      toast.error('Error fetching token');
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={status?.authenticated ? 'border-green-500 text-green-600' : ''}
        >
          <Zap className="w-4 h-4 mr-2" />
          {status?.authenticated ? (
            <>
              <Check className="w-3 h-3 mr-1" />
              Kimi Connected
            </>
          ) : (
            'Connect Kimi'
          )}
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            Kimi CLI Authentication
          </DialogTitle>
          <DialogDescription>
            Connect to Kimi CLI for AI-powered features
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {!status?.authenticated ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Kimi CLI not authenticated. Run 'kimi login' on the server or click Login.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-green-600">
                <Check className="w-5 h-5" />
                <span className="font-medium">Authenticated</span>
              </div>

              <div className="bg-muted p-3 rounded-lg space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">API Base:</span>
                  <span className="font-mono">{status.api_base}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Model:</span>
                  <span>{status.model}</span>
                </div>
                {status.token_preview && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Token:</span>
                    <span className="font-mono">{status.token_preview}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            {status?.authenticated ? (
              <>
                <Button
                  onClick={getToken}
                  variant="outline"
                  className="flex-1"
                >
                  Get Token
                </Button>
                <Button
                  onClick={handleLogout}
                  variant="destructive"
                  disabled={loading}
                  className="flex-1"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Logout'}
                </Button>
              </>
            ) : (
              <Button
                onClick={handleLogin}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Zap className="w-4 h-4 mr-2" />
                )}
                Login with Kimi
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
