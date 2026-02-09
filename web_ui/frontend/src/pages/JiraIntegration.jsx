import React, { useState, useEffect } from 'react';
import { jiraAPI } from '../services/api';
import { 
  Ticket, 
  Save, 
  CheckCircle, 
  AlertCircle, 
  TestTube,
  ExternalLink,
  Folder,
  Settings
} from 'lucide-react';
import './JiraIntegration.css';

function JiraIntegration() {
  const [config, setConfig] = useState({
    base_url: '',
    username: '',
    api_token: ''
  });
  const [enabled, setEnabled] = useState(false);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [fetchingProjects, setFetchingProjects] = useState(false);
  const [message, setMessage] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await jiraAPI.getSettings();
      setEnabled(response.data.enabled);
      if (response.data.base_url) {
        setConfig(prev => ({ ...prev, base_url: response.data.base_url }));
      }
    } catch (error) {
      console.error('Error fetching JIRA settings:', error);
    }
  };

  const handleSave = async () => {
    if (!config.base_url.trim() || !config.username.trim() || !config.api_token.trim()) {
      setMessage({ type: 'error', text: 'Please fill in all fields' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      await jiraAPI.updateSettings(
        config.base_url,
        config.username,
        config.api_token,
        enabled
      );
      setSaved(true);
      setMessage({ type: 'success', text: 'JIRA settings saved successfully' });
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to save settings' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage(null);

    try {
      await jiraAPI.test();
      setMessage({ type: 'success', text: 'Connection successful! JIRA is configured correctly.' });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Connection failed. Please check your credentials.' 
      });
    } finally {
      setTesting(false);
    }
  };

  const fetchProjects = async () => {
    setFetchingProjects(true);
    setMessage(null);

    try {
      const response = await jiraAPI.getProjects();
      setProjects(response.data);
      setMessage({ type: 'success', text: `Found ${response.data.length} projects` });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to fetch projects' 
      });
    } finally {
      setFetchingProjects(false);
    }
  };

  return (
    <div className="jira-page">
      <header className="page-header">
        <div className="header-title">
          <Ticket size={28} />
          <h1>JIRA Integration</h1>
        </div>
      </header>

      <div className="jira-content">
        <div className="info-card">
          <h3>About JIRA Integration</h3>
          <p>
            Connect Zen AI Pentest to JIRA to automatically create tickets for security findings.
            This allows your security team to track and remediate vulnerabilities using your existing workflow.
          </p>
          <ul>
            <li><Ticket size={16} /> Create tickets directly from findings</li>
            <li><Folder size={16} /> Assign to specific projects</li>
            <li><Settings size={16} /> Automatic priority mapping</li>
          </ul>
        </div>

        <div className="config-card">
          <h3>JIRA Configuration</h3>

          {message && (
            <div className={`alert ${message.type}`}>
              {message.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
              {message.text}
            </div>
          )}

          <div className="form-group">
            <label>JIRA Base URL</label>
            <input
              type="text"
              value={config.base_url}
              onChange={(e) => setConfig({...config, base_url: e.target.value})}
              placeholder="https://your-domain.atlassian.net"
            />
            <span className="help-text">
              Your JIRA instance URL (e.g., https://company.atlassian.net)
            </span>
          </div>

          <div className="form-group">
            <label>Username / Email</label>
            <input
              type="text"
              value={config.username}
              onChange={(e) => setConfig({...config, username: e.target.value})}
              placeholder="your.email@example.com"
            />
          </div>

          <div className="form-group">
            <label>API Token</label>
            <input
              type="password"
              value={config.api_token}
              onChange={(e) => setConfig({...config, api_token: e.target.value})}
              placeholder="your-api-token"
            />
            <span className="help-text">
              Create an API token at id.atlassian.com/manage-profile/security/api-tokens
            </span>
          </div>

          <div className="form-group checkbox">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
              />
              <span className="checkmark"></span>
              Enable JIRA integration
            </label>
          </div>

          <div className="form-actions">
            <button 
              className="btn-secondary"
              onClick={handleTest}
              disabled={testing}
            >
              {testing ? (
                <>
                  <span className="spinner-small"></span>
                  Testing...
                </>
              ) : (
                <>
                  <TestTube size={18} />
                  Test Connection
                </>
              )}
            </button>
            <button 
              className="btn-primary"
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner-small"></span>
                  Saving...
                </>
              ) : saved ? (
                <>
                  <CheckCircle size={18} />
                  Saved!
                </>
              ) : (
                <>
                  <Save size={18} />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>

        {enabled && (
          <div className="projects-card">
            <div className="projects-header">
              <h3>Available Projects</h3>
              <button 
                className="btn-secondary"
                onClick={fetchProjects}
                disabled={fetchingProjects}
              >
                {fetchingProjects ? (
                  <>
                    <span className="spinner-small"></span>
                    Loading...
                  </>
                ) : (
                  <>
                    <Folder size={16} />
                    Fetch Projects
                  </>
                )}
              </button>
            </div>

            {projects.length > 0 && (
              <div className="projects-list">
                <table>
                  <thead>
                    <tr>
                      <th>Key</th>
                      <th>Name</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((project) => (
                      <tr key={project.key}>
                        <td>
                          <span className="project-key">{project.key}</span>
                        </td>
                        <td>{project.name}</td>
                        <td>
                          <a 
                            href={`${config.base_url}/browse/${project.key}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="link-btn"
                          >
                            <ExternalLink size={14} />
                            Open
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        <div className="help-card">
          <h3>How to set up</h3>
          <ol>
            <li>
              <strong>Get your JIRA URL</strong>
              <p>This is your Atlassian domain (e.g., https://company.atlassian.net)</p>
            </li>
            <li>
              <strong>Generate API Token</strong>
              <p>Go to <a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noopener noreferrer">id.atlassian.com</a> and create a new API token</p>
            </li>
            <li>
              <strong>Enter Credentials</strong>
              <p>Use your Atlassian email and the API token (not your password)</p>
            </li>
            <li>
              <strong>Test Connection</strong>
              <p>Click "Test Connection" to verify everything works</p>
            </li>
          </ol>
        </div>

        <div className="preview-card">
          <h3>Ticket Preview</h3>
          <div className="jira-preview">
            <div className="jira-ticket">
              <div className="ticket-header">
                <span className="ticket-type bug">Bug</span>
                <span className="ticket-priority high">High</span>
              </div>
              <h4>[Critical] SQL Injection Vulnerability</h4>
              <div className="ticket-fields">
                <div className="field">
                  <span className="label">Severity:</span>
                  <span className="value critical">Critical</span>
                </div>
                <div className="field">
                  <span className="label">Target:</span>
                  <span className="value">example.com/login</span>
                </div>
                <div className="field">
                  <span className="label">Tool:</span>
                  <span className="value">SQLMap</span>
                </div>
              </div>
              <div className="ticket-labels">
                <span className="label-tag">security</span>
                <span className="label-tag">pentest</span>
                <span className="label-tag">zen-ai</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default JiraIntegration;
