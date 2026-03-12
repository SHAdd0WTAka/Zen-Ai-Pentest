// ============================================
// Zen-AI-Pentest Platform - Recent Activity
// ============================================

import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/services/api';
import {
  Scan,
  ShieldAlert,
  FileText,
  Bot,
  User,
  Settings,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';

interface Activity {
  type: string;
  description: string;
  timestamp: string;
  user?: string;
}

const iconMap: Record<string, React.ElementType> = {
  scan: Scan,
  vulnerability: ShieldAlert,
  report: FileText,
  agent: Bot,
  user: User,
  settings: Settings,
};

const colorMap: Record<string, string> = {
  scan: 'text-blue-500',
  vulnerability: 'text-red-500',
  report: 'text-purple-500',
  agent: 'text-green-500',
  user: 'text-orange-500',
  settings: 'text-gray-500',
};

export function RecentActivity() {
  const { data: activities, isLoading } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: () => dashboardApi.getRecentActivity(10),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activities.map((activity: Activity, index: number) => {
        const Icon = iconMap[activity.type] || AlertCircle;
        const color = colorMap[activity.type] || 'text-gray-500';

        return (
          <div key={index} className="flex items-start gap-3">
            <div className={`mt-0.5 ${color}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm">{activity.description}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-muted-foreground">
                  {new Date(activity.timestamp).toLocaleString()}
                </span>
                {activity.user && (
                  <span className="text-xs text-muted-foreground">
                    by {activity.user}
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
