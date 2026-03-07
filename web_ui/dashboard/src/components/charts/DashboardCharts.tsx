// ============================================
// Zen-AI-Pentest Platform - Dashboard Charts
// ============================================

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useTheme } from '@/components/theme-provider';

// ============================================
// Scan Trend Chart
// ============================================
export function ScanTrendChart() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const data = useMemo(() => [
    { date: '2024-01-01', scans: 12 },
    { date: '2024-01-02', scans: 18 },
    { date: '2024-01-03', scans: 15 },
    { date: '2024-01-04', scans: 25 },
    { date: '2024-01-05', scans: 22 },
    { date: '2024-01-06', scans: 30 },
    { date: '2024-01-07', scans: 28 },
    { date: '2024-01-08', scans: 35 },
    { date: '2024-01-09', scans: 32 },
    { date: '2024-01-10', scans: 40 },
    { date: '2024-01-11', scans: 38 },
    { date: '2024-01-12', scans: 45 },
    { date: '2024-01-13', scans: 42 },
    { date: '2024-01-14', scans: 50 },
  ], []);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          stroke={isDark ? '#9ca3af' : '#6b7280'}
          fontSize={12}
        />
        <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
            borderRadius: '8px',
          }}
          labelFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <Area
          type="monotone"
          dataKey="scans"
          stroke="#6366f1"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#colorScans)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ============================================
// Vulnerability Trend Chart
// ============================================
export function VulnerabilityTrendChart() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const data = useMemo(() => [
    { date: '2024-01-01', critical: 2, high: 5, medium: 12, low: 20 },
    { date: '2024-01-02', critical: 3, high: 7, medium: 15, low: 25 },
    { date: '2024-01-03', critical: 1, high: 4, medium: 10, low: 18 },
    { date: '2024-01-04', critical: 4, high: 8, medium: 18, low: 30 },
    { date: '2024-01-05', critical: 2, high: 6, medium: 14, low: 22 },
    { date: '2024-01-06', critical: 5, high: 10, medium: 20, low: 35 },
    { date: '2024-01-07', critical: 3, high: 7, medium: 16, low: 28 },
    { date: '2024-01-08', critical: 6, high: 12, medium: 25, low: 40 },
    { date: '2024-01-09', critical: 4, high: 9, medium: 19, low: 32 },
    { date: '2024-01-10', critical: 7, high: 15, medium: 30, low: 45 },
    { date: '2024-01-11', critical: 5, high: 11, medium: 22, low: 38 },
    { date: '2024-01-12', critical: 8, high: 18, medium: 35, low: 50 },
    { date: '2024-01-13', critical: 6, high: 13, medium: 28, low: 42 },
    { date: '2024-01-14', critical: 9, high: 20, medium: 40, low: 55 },
  ], []);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          stroke={isDark ? '#9ca3af' : '#6b7280'}
          fontSize={12}
        />
        <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
            borderRadius: '8px',
          }}
          labelFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <Legend />
        <Line type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="high" stroke="#f97316" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="medium" stroke="#eab308" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="low" stroke="#3b82f6" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ============================================
// Severity Distribution Chart
// ============================================
export function SeverityDistributionChart() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const data = [
    { name: 'Critical', value: 15, color: '#ef4444' },
    { name: 'High', value: 35, color: '#f97316' },
    { name: 'Medium', value: 65, color: '#eab308' },
    { name: 'Low', value: 90, color: '#3b82f6' },
    { name: 'Info', value: 120, color: '#6b7280' },
  ];

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ============================================
// Agent Performance Chart
// ============================================
export function AgentPerformanceChart() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const data = useMemo(() => [
    { name: 'Agent-01', scans: 45, cpu: 65, memory: 70 },
    { name: 'Agent-02', scans: 38, cpu: 45, memory: 55 },
    { name: 'Agent-03', scans: 52, cpu: 80, memory: 75 },
    { name: 'Agent-04', scans: 30, cpu: 35, memory: 40 },
    { name: 'Agent-05', scans: 42, cpu: 55, memory: 60 },
  ], []);

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
        <XAxis dataKey="name" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
        <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Bar dataKey="scans" fill="#6366f1" />
        <Bar dataKey="cpu" fill="#10b981" />
        <Bar dataKey="memory" fill="#f59e0b" />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ============================================
// Compliance Score Chart
// ============================================
export function ComplianceScoreChart() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const data = useMemo(() => [
    { framework: 'OWASP Top 10', score: 85 },
    { framework: 'PCI DSS', score: 72 },
    { framework: 'ISO 27001', score: 90 },
    { framework: 'GDPR', score: 68 },
    { framework: 'NIST', score: 78 },
  ], []);

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
        <XAxis type="number" domain={[0, 100]} stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
        <YAxis type="category" dataKey="framework" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} width={100} />
        <Tooltip
          contentStyle={{
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
            borderRadius: '8px',
          }}
          formatter={(value: number) => [`${value}%`, 'Score']}
        />
        <Bar dataKey="score" fill="#10b981" radius={[0, 4, 4, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.score >= 80 ? '#10b981' : entry.score >= 60 ? '#f59e0b' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
