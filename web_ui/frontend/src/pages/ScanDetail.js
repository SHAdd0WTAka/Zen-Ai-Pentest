import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { scansAPI } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { 
  ArrowLeft, 
  CheckCircle, 
  Activity, 
  AlertCircle, 
  Clock,
  ShieldAlert,
  Terminal,
  Download
} from 'lucide-react';
import './ScanDetail.css';

function ScanDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [scan, setScan] = useState(null);
    const [findings, setFindings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');
    
    const { isConnected, logs, progress, status } = useWebSocket(
        scan?.status === 'running' ? id : null
    );

    useEffect(() => {
        fetchScanDetails();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id]);

    const fetchScanDetails = async () => {
        try {
            const [scanRes, findingsRes] = await Promise.all([
                scansAPI.getById(id),
                scansAPI.getFindings(id),
            ]);
            setScan(scanRes.data);
            setFindings(findingsRes.data || []);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching scan details:', error);
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircle size={20} className="status-icon completed" />;
            case 'running':
                return <Activity size={20} className="status-icon running" />;
            case 'failed':
                return <AlertCircle size={20} className="status-icon failed" />;
            default:
                return <Clock size={20} className="status-icon pending" />;
        }
    };

    const getSeverityClass = (severity) => {
        return `severity-badge ${severity?.toLowerCase() || 'info'}`;
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading scan details...</p>
            </div>
        );
    }

    if (!scan) {
        return (
            <div className="error-container">
                <AlertCircle size={48} />
                <p>Scan not found</p>
                <button onClick={() => navigate('/scans')} className="btn-primary">
                    Back to Scans
                </button>
            </div>
        );
    }

    return (
        <div className="scan-detail-page">
            <header className="detail-header">
                <button onClick={() => navigate('/scans')} className="btn-back">
                    <ArrowLeft size={18} />
                    Back
                </button>
                <div className="header-info">
                    <h1>{scan.target}</h1>
                    <div className="header-meta">
                        <span className={getSeverityClass(scan.status)}>
                            {getStatusIcon(scan.status)}
                            {status || scan.status}
                        </span>
                        {isConnected && (
                            <span className="ws-indicator connected">
                                ● Live
                            </span>
                        )}
                    </div>
                </div>
            </header>

            {scan.status === 'running' && (
                <div className="progress-section">
                    <div className="progress-header">
                        <span>Progress</span>
                        <span>{Math.round(progress || scan.progress || 0)}%</span>
                    </div>
                    <div className="progress-bar-large">
                        <div 
                            className="progress-fill"
                            style={{ width: `${progress || scan.progress || 0}%` }}
                        ></div>
                    </div>
                </div>
            )}

            <div className="tabs">
                <button 
                    className={activeTab === 'overview' ? 'active' : ''}
                    onClick={() => setActiveTab('overview')}
                >
                    <ShieldAlert size={16} />
                    Findings ({findings.length})
                </button>
                <button 
                    className={activeTab === 'logs' ? 'active' : ''}
                    onClick={() => setActiveTab('logs')}
                >
                    <Terminal size={16} />
                    Logs ({logs.length})
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'overview' && (
                    <div className="findings-section">
                        {findings.length > 0 ? (
                            <div className="findings-list">
                                {findings.map((finding) => (
                                    <div key={finding.id} className="finding-card">
                                        <div className="finding-header">
                                            <span className={getSeverityClass(finding.severity)}>
                                                {finding.severity}
                                            </span>
                                            <span className="finding-date">
                                                {new Date(finding.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                        <h3>{finding.title}</h3>
                                        <p>{finding.description}</p>
                                        {finding.remediation && (
                                            <div className="remediation">
                                                <strong>Remediation:</strong> {finding.remediation}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <ShieldAlert size={48} />
                                <p>No findings yet</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'logs' && (
                    <div className="logs-section">
                        <div className="logs-header">
                            <span>Real-time Logs</span>
                            <button className="btn-icon">
                                <Download size={16} />
                            </button>
                        </div>
                        <div className="logs-container">
                            {logs.length > 0 ? (
                                logs.map((log) => (
                                    <div key={log.id} className={`log-line ${log.level}`}>
                                        <span className="log-time">
                                            {new Date(log.timestamp).toLocaleTimeString()}
                                        </span>
                                        <span className={`log-level ${log.level}`}>
                                            {log.level.toUpperCase()}
                                        </span>
                                        <span className="log-message">{log.message}</span>
                                    </div>
                                ))
                            ) : (
                                <div className="empty-logs">
                                    <Terminal size={32} />
                                    <p>Waiting for logs...</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ScanDetail;
