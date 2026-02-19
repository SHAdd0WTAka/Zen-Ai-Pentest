// ============================================
// Advanced Dashboard Component
// ============================================

import React, { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
} from 'recharts';
import { useScans, useScanStatistics } from '../../hooks/useScans';
import { useAlerts, useAcknowledgeAlert } from '../../hooks/useAlerts';
import { useAgents } from '../../hooks/useAgents';
import { useRealTimeUpdates } from '../../hooks/useWebSocket';
import {
  severityColors,
  severityLabels,
  scanStatusColors,
  scanStatusLabels,
  agentStatusColors,
  agentStatusLabels,
  formatDate,
  formatRelativeTime,
  formatNumber,
} from '../../utils/formatters';
import { ScanStatus, SeverityLevel, Alert as AlertType } from '../../types';
import { LoadingCard, LoadingTable } from '../Loading';

// Severity distribution colors for charts
const SEVERITY_CHART_COLORS: Record<SeverityLevel, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#6b7280',
};

// Stats Card Component
interface StatsCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: { value: number; positive: boolean };
  color: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  color,
}) => (
  <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 hover:border-gray-600 transition-colors">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-gray-400 text-sm font-medium">{title}</p>
        <p className="text-3xl font-bold text-white mt-2">{value}</p>
        {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
        {trend && (
          <div className={`flex items-center gap-1 mt-2 ${trend.positive ? 'text-green-400' : 'text-red-400'}`}>
            <span className="text-sm font-medium">
              {trend.positive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </span>
            <span className="text-gray-500 text-xs">vs. letzte Woche</span>
          </div>
        )}
      </div>
      <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
    </div>
  </div>
);

// Scan Status Badge
const ScanStatusBadge: React.FC<{ status: ScanStatus }> = ({ status }) => {
  const colors = scanStatusColors[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}
    >
      <span>{colors.icon}</span>
      {scanStatusLabels[status]}
    </span>
  );
};

// Alert Panel Component
const AlertPanel: React.FC = () => {
  const { data: alertsData, isLoading } = useAlerts({ acknowledged: false });
  const alerts = (alertsData || []) as any[];
  const acknowledgeMutation = useAcknowledgeAlert();

  if (isLoading) return <LoadingCard title="Aktive Alerts" />;

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          Aktive Alerts
        </h3>
        <span className="bg-red-900/50 text-red-400 px-2 py-1 rounded-full text-xs font-medium">
          {alerts.length}
        </span>
      </div>
      <div className="max-h-80 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>Keine aktiven Alerts</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {alerts.slice(0, 10).map((alert) => (
              <div key={alert.id} className="p-4 hover:bg-gray-700/50 transition-colors">
                <div className="flex items-start gap-3">
                  <div className={`w-2 h-2 rounded-full mt-2 ${severityColors[alert.severity].bg.replace('/50', '')}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium text-sm truncate">{alert.title}</p>
                    <p className="text-gray-400 text-xs mt-1">{alert.message}</p>
                    <p className="text-gray-500 text-xs mt-2">{formatRelativeTime(alert.createdAt)}</p>
                  </div>
                  <button
                    onClick={() => acknowledgeMutation.mutate(alert.id)}
                    className="text-gray-400 hover:text-white transition-colors"
                    aria-label="Alert bestätigen"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Agent Status Panel
const AgentStatusPanel: React.FC = () => {
  const { data: agentsData, isLoading } = useAgents();
  const agents = (agentsData || []) as any[];

  if (isLoading) return <LoadingCard title="Agent Status" />;

  const statusCounts = agents.reduce((acc, agent) => {
    acc[agent.status] = (acc[agent.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">Agent Status</h3>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-2 gap-3 mb-4">
          {(['idle', 'busy', 'offline', 'error'] as const).map((status) => (
            <div key={status} className="bg-gray-900 rounded-lg p-3">
              <p className={`text-2xl font-bold ${agentStatusColors[status]}`}>
                {statusCounts[status] || 0}
              </p>
              <p className="text-gray-500 text-xs">{agentStatusLabels[status]}</p>
            </div>
          ))}
        </div>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {agents.slice(0, 5).map((agent) => (
            <div key={agent.id} className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${agentStatusColors[agent.status].replace('text-', 'bg-')}`} />
                <span className="text-white text-sm">{agent.name}</span>
              </div>
              <span className={`text-xs ${agentStatusColors[agent.status]}`}>
                {agentStatusLabels[agent.status]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Recent Scans Table
const RecentScansTable: React.FC = () => {
  const { data: scansData, isLoading } = useScans({ page: 1, perPage: 5 });

  if (isLoading) return <LoadingTable rows={5} columns={4} />;

  const scans = scansData?.items || [];

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">Letzte Scans</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-900/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Ziel</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Fortschritt</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Zeit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {scans.map((scan) => (
              <tr key={scan.id} className="hover:bg-gray-700/50 transition-colors">
                <td className="px-4 py-3">
                  <span className="text-white text-sm font-medium">{scan.name}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-400 text-sm">{scan.target}</span>
                </td>
                <td className="px-4 py-3">
                  <ScanStatusBadge status={scan.status} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-cyan-500 rounded-full transition-all"
                        style={{ width: `${scan.progress}%` }}
                      />
                    </div>
                    <span className="text-gray-400 text-xs">{scan.progress}%</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-400 text-sm">
                    {formatRelativeTime(scan.updatedAt)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Main Dashboard Component
const AdvancedDashboard: React.FC = () => {
  const { data: stats, isLoading: statsLoading } = useScanStatistics();
  const { data: agents } = useAgents();
  const { data: alerts } = useAlerts();

  // Real-time updates
  useRealTimeUpdates();

  // Memoized chart data
  const severityData = useMemo(() => {
    if (!stats?.findingsBySeverity) return [];
    return Object.entries(stats.findingsBySeverity).map(([severity, count]) => ({
      name: severityLabels[severity as SeverityLevel],
      value: count,
      color: SEVERITY_CHART_COLORS[severity as SeverityLevel],
    }));
  }, [stats?.findingsBySeverity]);

  const scansByTypeData = useMemo(() => {
    if (!stats?.scansByType) return [];
    return Object.entries(stats.scansByType).map(([type, count]) => ({
      name: type,
      value: count,
    }));
  }, [stats?.scansByType]);

  // Timeline data (mock for now)
  const timelineData = [
    { time: '00:00', scans: 4, findings: 12 },
    { time: '04:00', scans: 3, findings: 8 },
    { time: '08:00', scans: 7, findings: 23 },
    { time: '12:00', scans: 5, findings: 15 },
    { time: '16:00', scans: 8, findings: 31 },
    { time: '20:00', scans: 6, findings: 19 },
    { time: '24:00', scans: 4, findings: 10 },
  ];

  if (statsLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingCard key={i} />
          ))}
        </div>
        <LoadingCard />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400">Übersicht über alle Pentest-Aktivitäten</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            Echtzeit-Updates aktiv
          </span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Aktive Scans"
          value={stats?.activeScans || 0}
          subtitle={`${stats?.completedScans || 0} abgeschlossen`}
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
          trend={{ value: 12, positive: true }}
          color="bg-cyan-600"
        />
        <StatsCard
          title="Kritische Findings"
          value={stats?.findingsBySeverity?.critical || 0}
          subtitle={`${formatNumber(Object.values(stats?.findingsBySeverity || {}).reduce((a, b) => a + b, 0))} insgesamt`}
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
          trend={{ value: 5, positive: false }}
          color="bg-red-600"
        />
        <StatsCard
          title="Aktive Agents"
          value={agents?.filter(a => a.status === 'busy').length || 0}
          subtitle={`${agents?.length || 0} registriert`}
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          }
          color="bg-emerald-600"
        />
        <StatsCard
          title="Unbestätigte Alerts"
          value={alerts?.filter(a => !a.acknowledged).length || 0}
          subtitle="Erfordern Aufmerksamkeit"
          icon={
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          }
          color="bg-amber-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Findings by Severity */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Findings nach Schweregrad</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  itemStyle={{ color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            {severityData.map((item) => (
              <div key={item.name} className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-gray-400 text-xs">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-white mb-4">Aktivitäts-Timeline (24h)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData}>
                <defs>
                  <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorFindings" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area
                  type="monotone"
                  dataKey="scans"
                  stroke="#06b6d4"
                  fillOpacity={1}
                  fill="url(#colorScans)"
                  name="Scans"
                />
                <Area
                  type="monotone"
                  dataKey="findings"
                  stroke="#f97316"
                  fillOpacity={1}
                  fill="url(#colorFindings)"
                  name="Findings"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Scans */}
        <div className="lg:col-span-2">
          <RecentScansTable />
        </div>

        {/* Side Panels */}
        <div className="space-y-6">
          <AlertPanel />
          <AgentStatusPanel />
        </div>
      </div>
    </div>
  );
};

export default AdvancedDashboard;
