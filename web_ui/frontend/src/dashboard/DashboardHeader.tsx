import { Activity, Moon, Sun, Shield, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAgentStore } from '../store/agentStore';

export function DashboardHeader() {
  const { theme, toggleTheme } = useAgentStore();

  return (
    <header className="border-b bg-card">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary rounded-lg">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Zen AI Pentest</h1>
              <p className="text-sm text-muted-foreground">Agent Control Center</p>
            </div>
          </div>

          {/* Center - Live Indicator */}
          <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-green-500/10 rounded-full">
            <Activity className="h-4 w-4 text-green-500 animate-pulse" />
            <span className="text-sm font-medium text-green-500">System Online</span>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="rounded-full"
            >
              {theme === 'dark' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>
            
            <Button variant="ghost" size="icon" className="rounded-full">
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
