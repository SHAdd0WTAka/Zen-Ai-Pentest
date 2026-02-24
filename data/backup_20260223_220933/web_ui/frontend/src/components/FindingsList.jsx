import React, { useState, useEffect } from 'react';
import RiskScoreCard from './RiskScoreCard';
import './FindingsList.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FindingsList = () => {
  const [findings, setFindings] = useState([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetch(`${API_BASE_URL}/findings`)
      .then(r => r.json())
      .then(data => setFindings(data.findings || []));
  }, []);

  const getSeverityColor = (severity) => {
    switch(severity?.toLowerCase()) {
      case 'critical': return '#e74c3c';
      case 'high': return '#e67e22';
      case 'medium': return '#f39c12';
      case 'low': return '#27ae60';
      default: return '#95a5a6';
    }
  };

  const filteredFindings = filter === 'all' 
    ? findings 
    : findings.filter(f => f.severity?.toLowerCase() === filter);

  const severityCounts = findings.reduce((acc, f) => {
    const sev = f.severity?.toLowerCase() || 'unknown';
    acc[sev] = (acc[sev] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="findings-list">
      <h1>Security Findings</h1>
      
      <div className="severity-summary">
        {Object.entries(severityCounts).map(([sev, count]) => (
          <div 
            key={sev}
            className="severity-badge"
            style={{ backgroundColor: getSeverityColor(sev) }}
          >
            {sev}: {count}
          </div>
        ))}
      </div>

      <div className="filter-bar">
        <label>Filter by severity:</label>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="findings">
        {filteredFindings.map(finding => (
          <div key={finding.id} className="finding-card">
            <div className="finding-header">
              <h3>{finding.title || finding.cve_id || 'Unknown'}</h3>
              <span 
                className="severity-label"
                style={{ backgroundColor: getSeverityColor(finding.severity) }}
              >
                {finding.severity}
              </span>
            </div>
            
            {finding.risk_score && (
              <RiskScoreCard score={finding.risk_score} />
            )}
            
            <p className="description">{finding.description}</p>
            
            {finding.prioritized_actions && (
              <div className="recommendations">
                <h4>Recommendations:</h4>
                <ul>
                  {finding.prioritized_actions.map((action, i) => (
                    <li key={i}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FindingsList;
