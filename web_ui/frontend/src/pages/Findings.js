import React, { useEffect, useState } from 'react';
import { findingsAPI } from '../services/api';
import { ShieldAlert, Filter, Search, AlertTriangle } from 'lucide-react';
import './Findings.css';

const SEVERITY_OPTIONS = ['all', 'critical', 'high', 'medium', 'low', 'info'];

function Findings() {
    const [findings, setFindings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [search, setSearch] = useState('');

    useEffect(() => {
        fetchFindings();
    }, []);

    const fetchFindings = async () => {
        try {
            const response = await findingsAPI.getAll();
            setFindings(response.data.items || []);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching findings:', error);
        }
    };

    const filteredFindings = findings.filter(finding => {
        const matchesSeverity = filter === 'all' || finding.severity?.toLowerCase() === filter;
        const matchesSearch = !search || 
            finding.title?.toLowerCase().includes(search.toLowerCase()) ||
            finding.description?.toLowerCase().includes(search.toLowerCase());
        return matchesSeverity && matchesSearch;
    });

    const getSeverityClass = (severity) => `severity-badge ${severity?.toLowerCase() || 'info'}`;

    const getSeverityCount = (severity) => {
        return findings.filter(f => f.severity?.toLowerCase() === severity).length;
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading findings...</p>
            </div>
        );
    }

    return (
        <div className="findings-page">
            <header className="page-header">
                <div className="header-title">
                    <ShieldAlert size={28} />
                    <h1>Findings</h1>
                </div>
            </header>

            <div className="findings-stats">
                {SEVERITY_OPTIONS.slice(1).map(sev => (
                    <div key={sev} className={`stat-pill ${sev}`}>
                        <span className="stat-name">{sev}</span>
                        <span className="stat-count">{getSeverityCount(sev)}</span>
                    </div>
                ))}
            </div>

            <div className="findings-toolbar">
                <div className="search-box">
                    <Search size={18} />
                    <input
                        type="text"
                        placeholder="Search findings..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                <div className="filter-group">
                    <Filter size={18} />
                    <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                        {SEVERITY_OPTIONS.map(opt => (
                            <option key={opt} value={opt}>
                                {opt.charAt(0).toUpperCase() + opt.slice(1)}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="findings-list">
                {filteredFindings.length > 0 ? (
                    filteredFindings.map((finding) => (
                        <div key={finding.id} className="finding-card">
                            <div className="finding-main">
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
                                {finding.target && (
                                    <div className="finding-target">
                                        Target: <span>{finding.target}</span>
                                    </div>
                                )}
                            </div>
                            {finding.remediation && (
                                <div className="finding-remediation">
                                    <div className="remediation-header">
                                        <AlertTriangle size={14} />
                                        Remediation
                                    </div>
                                    <p>{finding.remediation}</p>
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="empty-state">
                        <ShieldAlert size={48} />
                        <p>No findings found</p>
                        {search && <p className="hint">Try adjusting your search or filter</p>}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Findings;
