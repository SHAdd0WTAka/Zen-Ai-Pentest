import React, { useState, useEffect } from 'react';
import { slackAPI } from '../services/api';
import { 
  MessageSquare, 
  Send, 
  CheckCircle, 
  AlertCircle, 
  Save,
  TestTube,
  Bell,
  Shield
} from 'lucide-react';
import './SlackIntegration.css';

function SlackIntegration() {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await slackAPI.getSettings();
      setEnabled(response.data.enabled);
    } catch (error) {
      console.error('Error fetching Slack settings:', error);
    }
  };

  const handleSave = async () => {
    if (!webhookUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter a webhook URL' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      await slackAPI.updateSettings(webhookUrl, enabled);
      setSaved(true);
      setMessage({ type: 'success', text: 'Slack settings saved successfully' });
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
    if (!webhookUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter a webhook URL first' });
      return;
    }

    setTesting(true);
    setMessage(null);

    try {
      await slackAPI.test(webhookUrl);
      setMessage({ type: 'success', text: 'Test notification sent! Check your Slack channel.' });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to send test notification' 
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="slack-page">
      <header className="page-header">
        <div className="header-title">
          <MessageSquare size={28} />
          <h1>Slack Integration</h1>
        </div>
      </header>

      <div className="slack-content">
        <div className="info-card">
          <h3>About Slack Integration</h3>
          <p>
            Connect Zen AI Pentest to your Slack workspace to receive real-time notifications 
            about scan completions, critical findings, and scheduled scan results.
          </p>
          <ul>
            <li><Bell size={16} /> Get notified when scans complete</li>
            <li><Shield size={16} /> Receive alerts for critical findings</li>
            <li><Send size={16} /> Automated scheduled scan reports</li>
          </ul>
        </div>

        <div className="config-card">
          <h3>Configuration</h3>

          {message && (
            <div className={`alert ${message.type}`}>
              {message.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
              {message.text}
            </div>
          )}

          <div className="form-group">
            <label>Slack Webhook URL</label>
            <input
              type="text"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://hooks.slack.com/services/T00/B00/XXXX"
            />
            <span className="help-text">
              Create an Incoming Webhook in your Slack App settings
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
              Enable Slack notifications
            </label>
          </div>

          <div className="form-actions">
            <button 
              className="btn-secondary"
              onClick={handleTest}
              disabled={testing || !webhookUrl.trim()}
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

        <div className="help-card">
          <h3>How to set up</h3>
          <ol>
            <li>
              <strong>Create a Slack App</strong>
              <p>Go to <a href="https://api.slack.com/apps" target="_blank" rel="noopener noreferrer">api.slack.com/apps</a> and create a new app</p>
            </li>
            <li>
              <strong>Enable Incoming Webhooks</strong>
              <p>Navigate to "Incoming Webhooks" and toggle it on</p>
            </li>
            <li>
              <strong>Add to Workspace</strong>
              <p>Click "Add New Webhook to Workspace" and select a channel</p>
            </li>
            <li>
              <strong>Copy Webhook URL</strong>
              <p>Copy the webhook URL and paste it above</p>
            </li>
          </ol>
        </div>

        <div className="preview-card">
          <h3>Notification Preview</h3>
          <div className="slack-preview">
            <div className="slack-header">
              <span className="slack-app">Zen AI Pentest</span>
              <span className="slack-time">Today at 2:30 PM</span>
            </div>
            <div className="slack-attachment">
              <div className="slack-color-bar danger"></div>
              <div className="slack-content">
                <h4>Pentest Scan Completed</h4>
                <div className="slack-fields">
                  <div className="field">
                    <span className="field-title">Scan ID</span>
                    <span className="field-value">#123</span>
                  </div>
                  <div className="field">
                    <span className="field-title">Target</span>
                    <span className="field-value">example.com</span>
                  </div>
                  <div className="field">
                    <span className="field-title">Total Findings</span>
                    <span className="field-value">5</span>
                  </div>
                  <div className="field">
                    <span className="field-title">Critical</span>
                    <span className="field-value critical">2</span>
                  </div>
                </div>
                <div className="slack-footer">
                  Zen AI Pentest
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SlackIntegration;
