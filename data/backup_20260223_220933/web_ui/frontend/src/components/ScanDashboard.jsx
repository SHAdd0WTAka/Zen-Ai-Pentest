import React, { useState, useEffect } from 'react';
import './ScanDashboard.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ScanDashboard = () => {
  const [scans, setScans] = useState([]);
  const [ws, setWs] = useState(null);
  const [newScan, setNewScan] = useState({ target: '', scanType: 'web' });

  useEffect(() => {
    // Fetch existing scans
    fetch(`${API_BASE_URL}/scans`)
      .then(r => r.json())
      .then(data => setScans(data.scans || []));

    // WebSocket connection for real-time updates
    const websocket = new WebSocket(`ws://${window.location.host}/ws/scans`);
    websocket.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setScans(prev => prev.map(s => 
        s.id === update.scan_id ? { ...s, ...update } : s
      ));
    };
    setWs(websocket);

    return () => websocket.close();
  }, []);

  const startScan = async (e) => {
    e.preventDefault();
    const response = await fetch(`${API_BASE_URL}/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newScan)
    });
    const data = await response.json();
    setScans([...scans, data]);
    setNewScan({ target: '', scanType: 'web' });
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'running': return '#3498db';
      case 'completed': return '#2ecc71';
      case 'failed': return '#e74c3c';
      default: return '#95a5a6';
    }
  };

  return (
    <div className="scan-dashboard">
      <h1>Zen AI Pentest - Scan Dashboard</h1>
      
      <form onSubmit={startScan} className="new-scan-form">
        <input
          type="text"
          placeholder="Target URL/IP"
          value={newScan.target}
          onChange={(e) => setNewScan({...newScan, target: e.target.value})}
          required
        />
        <select
          value={newScan.scanType}
          onChange={(e) => setNewScan({...newScan, scanType: e.target.value})}
        >
          <option value="web">Web Application</option>
          <option value="api">API Security</option>
          <option value="network">Network</option>
          <option value="cloud">Cloud Infrastructure</option>
        </select>
        <button type="submit">Start Scan</button>
      </form>

      <div className="scans-list">
        <h2>Active & Recent Scans</h2>
        {scans.map(scan => (
          <div key={scan.id} className="scan-card">
            <div className="scan-header">
              <span className="scan-target">{scan.target}</span>
              <span 
                className="scan-status"
                style={{ backgroundColor: getStatusColor(scan.status) }}
              >
                {scan.status}
              </span>
            </div>
            <div className="scan-details">
              <span>Type: {scan.type}</span>
              <span>Started: {new Date(scan.created_at).toLocaleString()}</span>
              {scan.findings_count !== undefined && (
                <span>Findings: {scan.findings_count}</span>
              )}
              {scan.progress !== undefined && (
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ width: `${scan.progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScanDashboard;
