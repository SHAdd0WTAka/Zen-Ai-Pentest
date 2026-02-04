/**
 * Dashboard Page - Main Overview
 * Q2 2026 Feature
 */

import React, { useState, useEffect } from 'react';
import { 
  ShieldCheckIcon, 
  ExclamationTriangleIcon, 
  BugAntIcon,
  ClockIcon 
} from '@heroicons/react/24/outline';
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
  Cell
} from 'recharts';
import axios from 'axios';

const API_BASE = '/api/v1';

const severityColors = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  info: '#3b82f6'
};

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalScans: 0,
    activeScans: 0,
    criticalFindings: 0,
    totalFindings: 0
  });
  const [recentScans, setRecentScans] = useState([]);
  const [findingsBySeverity, setFindingsBySeverity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch stats from API
      const [scansRes, findingsRes] = await Promise.all([
        axios.get(`${API_BASE}/scans?limit=5`),
        axios.get(`${API_BASE}/findings?limit=100`)
      ]);

      const scans = scansRes.data || [];
      const findings = findingsRes.data || [];

      // Calculate stats
      const criticalCount = findings.filter(f => f.severity === 'critical').length;
      const activeCount = scans.filter(s => s.status === 'running').length;

      setStats({
        totalScans: scans.length,
        activeScans: activeCount,
        criticalFindings: criticalCount,
        totalFindings: findings.length
      });

      setRecentScans(scans.slice(0, 5));

      // Group findings by severity for pie chart
      const severityCounts = findings.reduce((acc, f) => {
        acc[f.severity] = (acc[f.severity] || 0) + 1;
        return acc;
      }, {});

      setFindingsBySeverity(
        Object.entries(severityCounts).map(([name, value]) => ({
          name,
          value,
          color: severityColors[name] || '#94a3b8'
        }))
      );

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Scans"
          value={stats.totalScans}
          icon={ShieldCheckIcon}
          color="bg-blue-500"
          subtitle="All time scans"
        />
        <StatCard
          title="Active Scans"
          value={stats.activeScans}
          icon={ClockIcon}
          color="bg-emerald-500"
          subtitle="Currently running"
        />
        <StatCard
          title="Critical Findings"
          value={stats.criticalFindings}
          icon={ExclamationTriangleIcon}
          color="bg-red-500"
          subtitle="Requires immediate action"
        />
        <StatCard
          title="Total Findings"
          value={stats.totalFindings}
          icon={BugAntIcon}
          color="bg-amber-500"
          subtitle="All vulnerabilities"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Findings by Severity */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Findings by Severity
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={findingsBySeverity}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {findingsBySeverity.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-4 mt-4 justify-center">
            {findingsBySeverity.map(item => (
              <div key={item.name} className="flex items-center gap-2">
                <span 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                ></span>
                <span className="text-sm text-gray-600 capitalize">
                  {item.name}: {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Scans */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Recent Scans
          </h3>
          <div className="space-y-3">
            {recentScans.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No scans yet</p>
            ) : (
              recentScans.map(scan => (
                <div 
                  key={scan.id} 
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-800">{scan.name}</p>
                    <p className="text-sm text-gray-500">{scan.target}</p>
                  </div>
                  <StatusBadge status={scan.status} />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* SIEM Status */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          SIEM Integration Status
        </h3>
        <SIEMStatus />
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color, subtitle }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-800">{value}</p>
          <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
        </div>
        <div className={`${color} p-3 rounded-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    running: 'bg-emerald-100 text-emerald-700',
    completed: 'bg-blue-100 text-blue-700',
    failed: 'bg-red-100 text-red-700',
    pending: 'bg-amber-100 text-amber-700'
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status] || 'bg-gray-100'}`}>
      {status}
    </span>
  );
}

function SIEMStatus() {
  const [siems, setSiems] = useState([]);

  useEffect(() => {
    fetchSIEMStatus();
  }, []);

  const fetchSIEMStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/siem/status`);
      setSiems(response.data || []);
    } catch (error) {
      console.error('Failed to fetch SIEM status:', error);
    }
  };

  if (siems.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No SIEM integrations configured</p>
        <a href="/siem" className="text-emerald-600 hover:underline mt-2 inline-block">
          Configure SIEM →
        </a>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {siems.map(siem => (
        <div key={siem.name} className="flex items-center gap-3 p-4 border rounded-lg">
          <span className={`w-3 h-3 rounded-full ${siem.connected ? 'bg-emerald-400' : 'bg-red-400'}`}></span>
          <div>
            <p className="font-medium text-gray-800">{siem.name}</p>
            <p className="text-xs text-gray-500 capitalize">{siem.type}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
