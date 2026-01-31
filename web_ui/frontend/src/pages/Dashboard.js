import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { statsAPI, scansAPI } from '../services/api';
import SeverityChart from '../components/charts/SeverityChart';
import ScanTrendsChart from '../components/charts/ScanTrendsChart';
import ToolUsageChart from '../components/charts/ToolUsageChart';
import { 
  ScanLine, 
  ShieldAlert, 
  Target, 
  Activity,
  ArrowRight,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import './Dashboard.css';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, scansRes] = await Promise.all([
        statsAPI.getOverview(),
        scansAPI.getAll({ limit: 5 }),
      ]);
      
      setStats(statsRes.data);
      setRecentScans(scansRes.data.items || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={18} className="status-completed" />;
      case 'running':
        return <Activity size={18} className="status-running" />;
      case 'failed':
        return <AlertCircle size={18} className="status-failed" />;
      default:
        return <Clock size={18} className="status-pending" />;
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Dashboard</h1>
        <Link to="/scans/new" className="btn-primary">
          <ScanLine size={18} />
          New Scan
        </Link>
      </header>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <ScanLine size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats?.total_scans || 0}</span>
            <span className="stat-label">Total Scans</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <CheckCircle size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats?.completed_scans || 0}</span>
            <span className="stat-label">Completed</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon red">
            <ShieldAlert size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats?.total_findings || 0}</span>
            <span className="stat-label">Findings</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">
            <Target size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats?.critical_findings || 0}</span>
            <span className="stat-label">Critical</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-grid">
        <div className="chart-card">
          <SeverityChart data={stats?.severity_distribution} />
        </div>
        <div className="chart-card">
          <ScanTrendsChart data={stats?.trends} />
        </div>
        <div className="chart-card wide">
          <ToolUsageChart data={stats?.tool_usage} />
        </div>
      </div>

      {/* Recent Scans */}
      <div className="recent-scans-section">
        <div className="section-header">
          <h2>Recent Scans</h2>
          <Link to="/scans" className="view-all">
            View All <ArrowRight size={16} />
          </Link>
        </div>

        <div className="scans-table-container">
          <table className="scans-table">
            <thead>
              <tr>
                <th>Target</th>
                <th>Status</th>
                <th>Tools</th>
                <th>Findings</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {recentScans.length > 0 ? (
                recentScans.map((scan) => (
                  <tr key={scan.id}>
                    <td>
                      <Link to={`/scans/${scan.id}`} className="target-link">
                        {scan.target}
                      </Link>
                    </td>
                    <td>
                      <span className={`status-badge ${scan.status}`}>
                        {getStatusIcon(scan.status)}
                        {scan.status}
                      </span>
                    </td>
                    <td>{scan.tools?.join(', ') || 'N/A'}</td>
                    <td>{scan.findings_count || 0}</td>
                    <td>{new Date(scan.created_at).toLocaleString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="no-data">
                    No scans yet. <Link to="/scans/new">Start your first scan</Link>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
