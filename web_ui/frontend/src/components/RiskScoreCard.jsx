import React from 'react';
import './RiskScoreCard.css';

const RiskScoreCard = ({ score }) => {
  if (!score) return null;

  const getSeverityColor = (severity) => {
    switch(severity?.toLowerCase()) {
      case 'critical': return '#e74c3c';
      case 'high': return '#e67e22';
      case 'medium': return '#f39c12';
      case 'low': return '#27ae60';
      default: return '#95a5a6';
    }
  };

  const {
    risk_score,
    severity,
    sla,
    components = {},
    prioritized_actions = []
  } = score;

  return (
    <div className="risk-score-card">
      <div className="risk-header">
        <div className="risk-value" style={{ color: getSeverityColor(severity) }}>
          {risk_score}/10
        </div>
        <div className="risk-severity">
          <span 
            className="severity-badge"
            style={{ backgroundColor: getSeverityColor(severity) }}
          >
            {severity}
          </span>
          <span className="sla">SLA: {sla}</span>
        </div>
      </div>

      <div className="components-grid">
        <div className="component-item">
          <label>CVSS</label>
          <div className="component-bar">
            <div 
              className="component-fill"
              style={{ width: `${(components.cvss || 0) * 100}%` }}
            />
          </div>
          <span>{((components.cvss || 0) * 10).toFixed(1)}</span>
        </div>

        <div className="component-item">
          <label>EPSS</label>
          <div className="component-bar">
            <div 
              className="component-fill epss"
              style={{ width: `${(components.epss || 0) * 100}%` }}
            />
          </div>
          <span>{((components.epss || 0) * 10).toFixed(1)}</span>
        </div>

        <div className="component-item">
          <label>Business</label>
          <div className="component-bar">
            <div 
              className="component-fill business"
              style={{ width: `${(components.business_impact || 0) * 100}%` }}
            />
          </div>
          <span>{((components.business_impact || 0) * 10).toFixed(1)}</span>
        </div>

        <div className="component-item">
          <label>Validation</label>
          <div className="component-bar">
            <div 
              className="component-fill validation"
              style={{ width: `${(components.exploit_validation || 0) * 100}%` }}
            />
          </div>
          <span>{((components.exploit_validation || 0) * 10).toFixed(1)}</span>
        </div>
      </div>

      {prioritized_actions.length > 0 && (
        <div className="recommendations">
          <h4>Recommended Actions</h4>
          <ul>
            {prioritized_actions.map((action, i) => (
              <li key={i}>{action}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default RiskScoreCard;
