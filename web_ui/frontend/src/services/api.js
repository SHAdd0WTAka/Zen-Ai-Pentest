import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

// Scans API
export const scansAPI = {
  getAll: (params) => api.get('/scans', { params }),
  getById: (id) => api.get(`/scans/${id}`),
  create: (data) => api.post('/scans', data),
  update: (id, data) => api.patch(`/scans/${id}`, data),
  delete: (id) => api.delete(`/scans/${id}`),
  getFindings: (id) => api.get(`/scans/${id}/findings`),
  start: (id) => api.post(`/scans/${id}/start`),
  stop: (id) => api.post(`/scans/${id}/stop`),
};

// Findings API
export const findingsAPI = {
  getAll: (params) => api.get('/findings', { params }),
  getById: (id) => api.get(`/findings/${id}`),
  update: (id, data) => api.patch(`/findings/${id}`, data),
  delete: (id) => api.delete(`/findings/${id}`),
};

// Tools API
export const toolsAPI = {
  getAll: () => api.get('/tools'),
  execute: (tool, params) => api.post('/tools/execute', { tool, params }),
};

// Reports API
export const reportsAPI = {
  getAll: () => api.get('/reports'),
  generate: (scanId, format) => api.post('/reports', { scan_id: scanId, format }),
  download: (id) => api.get(`/reports/${id}/download`, { responseType: 'blob' }),
};

// Dashboard Stats API
export const statsAPI = {
  getOverview: () => api.get('/stats/overview'),
  getTrends: (days = 30) => api.get('/stats/trends', { params: { days } }),
  getSeverityDistribution: () => api.get('/stats/severity'),
  getToolUsage: () => api.get('/stats/tools'),
};

// Agents API
export const agentsAPI = {
  getAll: () => api.get('/agents'),
  getStatus: (id) => api.get(`/agents/${id}/status`),
  start: (id) => api.post(`/agents/${id}/start`),
  stop: (id) => api.post(`/agents/${id}/stop`),
};

// Scheduled Scans API
export const schedulesAPI = {
  getAll: () => api.get('/schedules'),
  getById: (id) => api.get(`/schedules/${id}`),
  create: (data) => api.post('/schedules', data),
  update: (id, data) => api.patch(`/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedules/${id}`),
  runNow: (id) => api.post(`/schedules/${id}/run`),
};

// Slack Notifications API
export const slackAPI = {
  getSettings: () => api.get('/settings/slack'),
  updateSettings: (webhook_url, enabled = true) => api.post('/settings/slack', null, {
    params: { webhook_url, enabled }
  }),
  test: (webhook_url) => api.post('/notifications/slack/test', null, {
    params: { webhook_url }
  }),
  notifyScanComplete: (scan_id, webhook_url) => api.post('/notifications/slack/scan-complete', null, {
    params: { scan_id, webhook_url }
  }),
};

// JIRA Integration API
export const jiraAPI = {
  getSettings: () => api.get('/settings/jira'),
  updateSettings: (base_url, username, api_token, enabled = true) => api.post('/settings/jira', null, {
    params: { base_url, username, api_token, enabled }
  }),
  test: () => api.post('/settings/jira/test'),
  getProjects: () => api.get('/settings/jira/projects'),
  createTicket: (finding_id, project_key) => api.post('/integrations/jira/create-ticket', null, {
    params: { finding_id, project_key }
  }),
};

export default api;
