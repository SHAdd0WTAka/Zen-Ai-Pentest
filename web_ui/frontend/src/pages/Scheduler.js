import React, { useEffect, useState } from 'react';
import { schedulesAPI } from '../services/api';
import { 
  Calendar, 
  Clock, 
  Play, 
  Pause, 
  Trash2, 
  Edit2, 
  Plus,
  CheckCircle,
  AlertCircle,
  Calendar as CalendarIcon
} from 'lucide-react';
import './Scheduler.css';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const FREQUENCIES = [
  { value: 'once', label: 'Once' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' }
];

function Scheduler() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    target: '',
    scan_type: 'comprehensive',
    frequency: 'weekly',
    schedule_time: '02:00',
    schedule_day: 1,
    enabled: true,
    notification_email: '',
    notification_slack: ''
  });

  useEffect(() => {
    fetchSchedules();
    const interval = setInterval(fetchSchedules, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchSchedules = async () => {
    try {
      const response = await schedulesAPI.getAll();
      setSchedules(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editing) {
        await schedulesAPI.update(editing.id, formData);
      } else {
        await schedulesAPI.create(formData);
      }
      setShowForm(false);
      setEditing(null);
      resetForm();
      fetchSchedules();
    } catch (error) {
      console.error('Error saving schedule:', error);
      alert('Failed to save schedule');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this schedule?')) return;
    try {
      await schedulesAPI.delete(id);
      fetchSchedules();
    } catch (error) {
      console.error('Error deleting schedule:', error);
    }
  };

  const handleRunNow = async (id) => {
    try {
      await schedulesAPI.runNow(id);
      alert('Scan triggered!');
      fetchSchedules();
    } catch (error) {
      console.error('Error running schedule:', error);
    }
  };

  const handleToggle = async (schedule) => {
    try {
      await schedulesAPI.update(schedule.id, { enabled: !schedule.enabled });
      fetchSchedules();
    } catch (error) {
      console.error('Error toggling schedule:', error);
    }
  };

  const startEdit = (schedule) => {
    setEditing(schedule);
    setFormData({
      name: schedule.name,
      target: schedule.target,
      scan_type: schedule.scan_type,
      frequency: schedule.frequency,
      schedule_time: schedule.schedule_time,
      schedule_day: schedule.schedule_day,
      enabled: schedule.enabled,
      notification_email: schedule.notification_email || '',
      notification_slack: schedule.notification_slack || ''
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      target: '',
      scan_type: 'comprehensive',
      frequency: 'weekly',
      schedule_time: '02:00',
      schedule_day: 1,
      enabled: true,
      notification_email: '',
      notification_slack: ''
    });
  };

  const getFrequencyLabel = (freq) => {
    return FREQUENCIES.find(f => f.value === freq)?.label || freq;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading schedules...</p>
      </div>
    );
  }

  return (
    <div className="scheduler-page">
      <header className="page-header">
        <div className="header-title">
          <CalendarIcon size={28} />
          <h1>Scheduled Scans</h1>
        </div>
        <button 
          className="btn-primary"
          onClick={() => { setShowForm(true); setEditing(null); resetForm(); }}
        >
          <Plus size={18} />
          New Schedule
        </button>
      </header>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>{editing ? 'Edit Schedule' : 'Create New Schedule'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g., Weekly Security Scan"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Target *</label>
                  <input
                    type="text"
                    value={formData.target}
                    onChange={(e) => setFormData({...formData, target: e.target.value})}
                    placeholder="e.g., example.com"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Scan Type</label>
                  <select
                    value={formData.scan_type}
                    onChange={(e) => setFormData({...formData, scan_type: e.target.value})}
                  >
                    <option value="quick">Quick</option>
                    <option value="standard">Standard</option>
                    <option value="comprehensive">Comprehensive</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Frequency</label>
                  <select
                    value={formData.frequency}
                    onChange={(e) => setFormData({...formData, frequency: e.target.value})}
                  >
                    {FREQUENCIES.map(f => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Time *</label>
                  <input
                    type="time"
                    value={formData.schedule_time}
                    onChange={(e) => setFormData({...formData, schedule_time: e.target.value})}
                    required
                  />
                </div>
                {formData.frequency === 'weekly' && (
                  <div className="form-group">
                    <label>Day of Week</label>
                    <select
                      value={formData.schedule_day}
                      onChange={(e) => setFormData({...formData, schedule_day: parseInt(e.target.value)})}
                    >
                      {WEEKDAYS.map((day, idx) => (
                        <option key={idx} value={idx}>{day}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>Notification Email (optional)</label>
                <input
                  type="email"
                  value={formData.notification_email}
                  onChange={(e) => setFormData({...formData, notification_email: e.target.value})}
                  placeholder="alerts@example.com"
                />
              </div>

              <div className="form-group">
                <label>Slack Webhook (optional)</label>
                <input
                  type="text"
                  value={formData.notification_slack}
                  onChange={(e) => setFormData({...formData, notification_slack: e.target.value})}
                  placeholder="https://hooks.slack.com/..."
                />
              </div>

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editing ? 'Update' : 'Create'} Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="schedules-list">
        {schedules.length > 0 ? (
          schedules.map((schedule) => (
            <div key={schedule.id} className={`schedule-card ${!schedule.enabled ? 'disabled' : ''}`}>
              <div className="schedule-header">
                <div className="schedule-info">
                  <h3>{schedule.name}</h3>
                  <span className="target">{schedule.target}</span>
                </div>
                <div className="schedule-actions">
                  <button 
                    className={`toggle-btn ${schedule.enabled ? 'active' : ''}`}
                    onClick={() => handleToggle(schedule)}
                    title={schedule.enabled ? 'Disable' : 'Enable'}
                  >
                    {schedule.enabled ? <Pause size={16} /> : <Play size={16} />}
                  </button>
                  <button 
                    className="run-btn"
                    onClick={() => handleRunNow(schedule.id)}
                    title="Run Now"
                  >
                    <Play size={16} />
                  </button>
                  <button 
                    className="edit-btn"
                    onClick={() => startEdit(schedule)}
                    title="Edit"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button 
                    className="delete-btn"
                    onClick={() => handleDelete(schedule.id)}
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              <div className="schedule-details">
                <div className="detail-item">
                  <Calendar size={16} />
                  <span>{getFrequencyLabel(schedule.frequency)}</span>
                  {schedule.frequency === 'weekly' && schedule.schedule_day !== undefined && (
                    <span className="day">on {WEEKDAYS[schedule.schedule_day]}</span>
                  )}
                </div>
                <div className="detail-item">
                  <Clock size={16} />
                  <span>at {schedule.schedule_time}</span>
                </div>
                <div className="detail-item">
                  <span className={`status-badge ${schedule.scan_type}`}>{schedule.scan_type}</span>
                </div>
              </div>

              <div className="schedule-footer">
                <div className="last-run">
                  {schedule.last_run_status === 'completed' && <CheckCircle size={14} className="success" />}
                  {schedule.last_run_status === 'failed' && <AlertCircle size={14} className="error" />}
                  <span>Last run: {formatDate(schedule.last_run_at)}</span>
                </div>
                <div className="next-run">
                  <span>Next run: {formatDate(schedule.next_run_at)}</span>
                </div>
              </div>

              {(schedule.notification_email || schedule.notification_slack) && (
                <div className="notifications">
                  {schedule.notification_email && <span className="badge email">Email</span>}
                  {schedule.notification_slack && <span className="badge slack">Slack</span>}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="empty-state">
            <CalendarIcon size={48} />
            <p>No scheduled scans yet</p>
            <button 
              className="btn-primary"
              onClick={() => { setShowForm(true); setEditing(null); resetForm(); }}
            >
              Create your first schedule
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Scheduler;
