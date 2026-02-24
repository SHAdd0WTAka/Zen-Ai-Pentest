import React, { useState, useEffect } from 'react';
import './AgentStatus.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AgentStatus = () => {
  const [agents, setAgents] = useState([]);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/agents`)
      .then(r => r.json())
      .then(data => setAgents(data.agents || []));

    const websocket = new WebSocket(`ws://${window.location.host}/ws/agents`);
    websocket.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setAgents(prev => prev.map(a => 
        a.id === update.agent_id ? { ...a, ...update } : a
      ));
    };
    setWs(websocket);

    return () => websocket.close();
  }, []);

  const getStatusIcon = (status) => {
    switch(status) {
      case 'running': return '🟢';
      case 'paused': return '🟡';
      case 'error': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className="agent-status">
      <h2>Active Agents</h2>
      <div className="agents-grid">
        {agents.map(agent => (
          <div key={agent.id} className={`agent-card ${agent.status}`}>
            <div className="agent-header">
              <span className="status-icon">{getStatusIcon(agent.status)}</span>
              <span className="agent-name">{agent.name || agent.id}</span>
            </div>
            
            <div className="agent-stats">
              <div className="stat">
                <label>Status</label>
                <span>{agent.status}</span>
              </div>
              <div className="stat">
                <label>Iteration</label>
                <span>{agent.current_iteration || 0}</span>
              </div>
              <div className="stat">
                <label>Findings</label>
                <span>{agent.findings_count || 0}</span>
              </div>
            </div>

            {agent.current_action && (
              <div className="current-action">
                <label>Current Action</label>
                <span>{agent.current_action}</span>
              </div>
            )}

            {agent.memory_usage && (
              <div className="memory-usage">
                <label>Memory</label>
                <div className="memory-bar">
                  <div 
                    className="memory-fill"
                    style={{ width: `${Math.min(agent.memory_usage, 100)}%` }}
                  />
                </div>
                <span>{agent.memory_usage}%</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentStatus;
