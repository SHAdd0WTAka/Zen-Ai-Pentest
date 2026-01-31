import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { scansAPI } from '../services/api';
import { 
  ScanLine, 
  Eye, 
  Trash2, 
  Plus, 
  CheckCircle, 
  Activity, 
  AlertCircle, 
  Clock,
  ArrowRight
} from 'lucide-react';
import './Scans.css';

function Scans() {
    const navigate = useNavigate();
    const [scans, setScans] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchScans();
        const interval = setInterval(fetchScans, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchScans = async () => {
        try {
            const response = await scansAPI.getAll();
            setScans(response.data.items || []);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching scans:', error);
        }
    };

    const handleDelete = async (scanId) => {
        if (!window.confirm('Are you sure you want to delete this scan?')) return;
        try {
            await scansAPI.delete(scanId);
            fetchScans();
        } catch (error) {
            console.error('Error deleting scan:', error);
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircle size={16} className="status-icon completed" />;
            case 'running':
                return <Activity size={16} className="status-icon running" />;
            case 'failed':
                return <AlertCircle size={16} className="status-icon failed" />;
            default:
                return <Clock size={16} className="status-icon pending" />;
        }
    };

    const getStatusClass = (status) => {
        return `status-badge ${status}`;
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading scans...</p>
            </div>
        );
    }

    return (
        <div className="scans-page">
            <header className="page-header">
                <div className="header-title">
                    <ScanLine size={28} />
                    <h1>Scans</h1>
                </div>
                <button
                    className="btn-primary"
                    onClick={() => navigate('/scans/new')}
                >
                    <Plus size={18} />
                    New Scan
                </button>
            </header>

            <div className="scans-table-container">
                <table className="scans-data-table">
                    <thead>
                        <tr>
                            <th>Target</th>
                            <th>Status</th>
                            <th>Progress</th>
                            <th>Findings</th>
                            <th>Start Time</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {scans.length > 0 ? (
                            scans.map((scan) => (
                                <tr key={scan.id}>
                                    <td>
                                        <Link to={`/scans/${scan.id}`} className="target-link">
                                            {scan.target}
                                        </Link>
                                    </td>
                                    <td>
                                        <span className={getStatusClass(scan.status)}>
                                            {getStatusIcon(scan.status)}
                                            {scan.status}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="progress-cell">
                                            <div className="progress-bar">
                                                <div 
                                                    className="progress-fill"
                                                    style={{ width: `${scan.progress || 0}%` }}
                                                ></div>
                                            </div>
                                            <span className="progress-text">
                                                {Math.round(scan.progress || 0)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td>{scan.findings_count || 0}</td>
                                    <td>
                                        {scan.created_at 
                                            ? new Date(scan.created_at).toLocaleString() 
                                            : '-'}
                                    </td>
                                    <td>
                                        <div className="actions">
                                            <button
                                                className="action-btn view"
                                                onClick={() => navigate(`/scans/${scan.id}`)}
                                                title="View Details"
                                            >
                                                <Eye size={16} />
                                            </button>
                                            {scan.status !== 'running' && (
                                                <button
                                                    className="action-btn delete"
                                                    onClick={() => handleDelete(scan.id)}
                                                    title="Delete"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="6" className="empty-state">
                                    <ScanLine size={48} />
                                    <p>No scans yet</p>
                                    <button 
                                        className="btn-primary"
                                        onClick={() => navigate('/scans/new')}
                                    >
                                        Start your first scan
                                        <ArrowRight size={16} />
                                    </button>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default Scans;
