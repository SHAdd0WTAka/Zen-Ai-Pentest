import React, { useState } from 'react';
import ScanDashboard from './components/ScanDashboard';
import FindingsList from './components/FindingsList';
import AgentStatus from './components/AgentStatus';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('scans');

  return (
    <div className="App">
      <nav className="navbar">
        <div className="logo">Zen AI Pentest v2.0</div>
        <div className="nav-tabs">
          <button 
            className={activeTab === 'scans' ? 'active' : ''}
            onClick={() => setActiveTab('scans')}
          >
            Scans
          </button>
          <button 
            className={activeTab === 'agents' ? 'active' : ''}
            onClick={() => setActiveTab('agents')}
          >
            Agents
          </button>
          <button 
            className={activeTab === 'findings' ? 'active' : ''}
            onClick={() => setActiveTab('findings')}
          >
            Findings
          </button>
        </div>
        <div className="version">v2.0.0</div>
      </nav>
      
      <main>
        {activeTab === 'scans' && <ScanDashboard />}
        {activeTab === 'agents' && <AgentStatus />}
        {activeTab === 'findings' && <FindingsList />}
      </main>

      <footer className="footer">
        <p>Zen AI Pentest - Autonomous Red Team Framework</p>
      </footer>
    </div>
  );
}

export default App;
