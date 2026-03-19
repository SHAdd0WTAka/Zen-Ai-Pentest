// ============================================
// Zen-AI-Pentest Platform - API Services
// RESTful API Integration
// ============================================

import axios, { AxiosError } from 'axios';
import type { AxiosInstance, AxiosRequestConfig } from 'axios';
import type {
  ApiResponse,
  ApiError,
  User,
  Scan,
  ScanConfig,
  Vulnerability,
  Report,
  ReportConfig,
  Agent,
  Plugin,
  DashboardStats,
  SystemSettings,
  ComplianceFramework,
  MCPServer,
  SearchFilters,
  PaginationParams,
  ApiMeta,
  NetworkGraph,
} from '@/types';

// ============================================
// Axios Instance Configuration
// ============================================
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data.data;
          localStorage.setItem('access_token', access_token);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }

          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// ============================================
// Generic API Methods
// ============================================
async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.get<ApiResponse<T>>(url, config);
  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Request failed');
  }
  return response.data.data as T;
}

async function post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.post<ApiResponse<T>>(url, data, config);
  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Request failed');
  }
  return response.data.data as T;
}

async function patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.patch<ApiResponse<T>>(url, data, config);
  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Request failed');
  }
  return response.data.data as T;
}

async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.delete<ApiResponse<T>>(url, config);
  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Request failed');
  }
  return response.data.data as T;
}

// ============================================
// Auth API
// ============================================
export const authApi = {
  login: (username: string, password: string) =>
    post<{ user: User; access_token: string; refresh_token: string }>('/auth/login', {
      username,
      password,
    }),

  register: (data: { username: string; email: string; password: string }) =>
    post<{ user: User; access_token: string; refresh_token: string }>('/auth/register', data),

  logout: () => post('/auth/logout', {}),

  refresh: (refreshToken: string) =>
    post<{ access_token: string }>('/auth/refresh', { refresh_token: refreshToken }),

  me: () => get<User>('/auth/me'),

  updateProfile: (data: Partial<User>) => patch<User>('/auth/me', data),

  changePassword: (oldPassword: string, newPassword: string) =>
    post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),

  requestPasswordReset: (email: string) =>
    post('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    post('/auth/reset-password', { token, new_password: newPassword }),

  // OAuth Device Flow
  initiateDeviceAuth: () =>
    post<{ device_code: string; user_code: string; verification_uri: string; expires_in: number }>(
      '/auth/device'
    ),

  pollDeviceAuth: (deviceCode: string) =>
    post<{ access_token?: string; refresh_token?: string; status: string }>(
      '/auth/device/poll',
      { device_code: deviceCode }
    ),

  // API Key Management
  generateApiKey: (name: string) =>
    post<{ key: string; id: string }>('/auth/api-keys', { name }),

  listApiKeys: () =>
    get<{ id: string; name: string; created_at: string; last_used?: string }[]>('/auth/api-keys'),

  revokeApiKey: (id: string) =>
    del(`/auth/api-keys/${id}`),
};

// ============================================
// Scan API
// ============================================
export const scanApi = {
  list: (filters?: SearchFilters, pagination?: PaginationParams) =>
    get<{ scans: Scan[]; meta: ApiMeta }>('/scans', {
      params: { ...filters, ...pagination },
    }),

  get: (id: string) => get<Scan>(`/scans/${id}`),

  create: (data: { name: string; target: string; type: string; config: ScanConfig }) =>
    post<Scan>('/scans', data),

  update: (id: string, updates: Partial<Scan>) =>
    patch<Scan>(`/scans/${id}`, updates),

  delete: (id: string) => del(`/scans/${id}`),

  start: (id: string) =>
    post<Scan>(`/scans/${id}/start`),

  stop: (id: string) =>
    post<Scan>(`/scans/${id}/stop`),

  pause: (id: string) =>
    post<Scan>(`/scans/${id}/pause`),

  resume: (id: string) =>
    post<Scan>(`/scans/${id}/resume`),

  getResults: (id: string) =>
    get<Scan['results']>(`/scans/${id}/results`),

  getLogs: (id: string, lines?: number) =>
    get<string[]>(`/scans/${id}/logs`, { params: { lines } }),

  export: (id: string, format: string) =>
    get<Blob>(`/scans/${id}/export`, {
      params: { format },
      responseType: 'blob',
    }),

  // Bulk operations
  bulkDelete: (ids: string[]) =>
    post('/scans/bulk-delete', { ids }),

  bulkStart: (ids: string[]) =>
    post('/scans/bulk-start', { ids }),

  // Schedule
  schedule: (id: string, schedule: { cron: string; enabled: boolean }) =>
    post(`/scans/${id}/schedule`, schedule),

  // Clone scan
  clone: (id: string, newName?: string) =>
    post<Scan>(`/scans/${id}/clone`, { name: newName }),
};

// ============================================
// Vulnerability API
// ============================================
export const vulnerabilityApi = {
  list: (filters?: SearchFilters, pagination?: PaginationParams) =>
    get<{ vulnerabilities: Vulnerability[]; meta: ApiMeta }>('/vulnerabilities', {
      params: { ...filters, ...pagination },
    }),

  get: (id: string) => get<Vulnerability>(`/vulnerabilities/${id}`),

  update: (id: string, updates: Partial<Vulnerability>) =>
    patch<Vulnerability>(`/vulnerabilities/${id}`, updates),

  updateStatus: (id: string, status: string, comment?: string) =>
    patch<Vulnerability>(`/vulnerabilities/${id}/status`, { status, comment }),

  addComment: (id: string, comment: string) =>
    post(`/vulnerabilities/${id}/comments`, { comment }),

  getComments: (id: string) =>
    get<Array<{ id: string; user: string; comment: string; created_at: string }>>(
      `/vulnerabilities/${id}/comments`
    ),

  // AI Analysis
  analyze: (id: string) =>
    post<Vulnerability['aiAnalysis']>(`/vulnerabilities/${id}/analyze`),

  // Bulk operations
  bulkUpdateStatus: (ids: string[], status: string) =>
    post('/vulnerabilities/bulk-status', { ids, status }),

  // Export
  export: (filters?: SearchFilters, format?: string) =>
    get<Blob>('/vulnerabilities/export', {
      params: { ...filters, format },
      responseType: 'blob',
    }),

  // Statistics
  getStats: () =>
    get<{
      bySeverity: Record<string, number>;
      byStatus: Record<string, number>;
      byType: Record<string, number>;
      trend: Array<{ date: string; count: number }>;
    }>('/vulnerabilities/stats'),
};

// ============================================
// Report API
// ============================================
export const reportApi = {
  list: (pagination?: PaginationParams) =>
    get<{ reports: Report[]; meta: ApiMeta }>('/reports', {
      params: pagination,
    }),

  get: (id: string) => get<Report>(`/reports/${id}`),

  create: (data: {
    name: string;
    type: string;
    format: string;
    scanIds: string[];
    config?: ReportConfig;
  }) => post<Report>('/reports', data),

  delete: (id: string) => del(`/reports/${id}`),

  download: (id: string) =>
    get<Blob>(`/reports/${id}/download`, { responseType: 'blob' }),

  // Templates
  getTemplates: () =>
    get<Array<{ id: string; name: string; description: string }>>('/reports/templates'),

  // Preview
  preview: (id: string) =>
    get<string>(`/reports/${id}/preview`),
};

// ============================================
// Agent API
// ============================================
export const agentApi = {
  list: (filters?: { status?: string[]; type?: string[] }) =>
    get<Agent[]>('/agents', { params: filters }),

  get: (id: string) => get<Agent>(`/agents/${id}`),

  register: (data: { name: string; type: string; host: string; port: number }) =>
    post<Agent>('/agents', data),

  update: (id: string, updates: Partial<Agent>) =>
    patch<Agent>(`/agents/${id}`, updates),

  delete: (id: string) => del(`/agents/${id}`),

  // Actions
  restart: (id: string) => post(`/agents/${id}/restart`),

  updateSoftware: (id: string) => post(`/agents/${id}/update`),

  getLogs: (id: string, lines?: number) =>
    get<string[]>(`/agents/${id}/logs`, { params: { lines } }),

  // Metrics
  getMetrics: (id: string) =>
    get<Agent['metrics']>(`/agents/${id}/metrics`),

  // Bulk operations
  bulkRestart: (ids: string[]) =>
    post('/agents/bulk-restart', { ids }),

  bulkUpdate: (ids: string[]) =>
    post('/agents/bulk-update', { ids }),
};

// ============================================
// Plugin API
// ============================================
export const pluginApi = {
  list: (filters?: { type?: string[]; status?: string[] }) =>
    get<Plugin[]>('/plugins', { params: filters }),

  get: (id: string) => get<Plugin>(`/plugins/${id}`),

  install: (data: { source: string; config?: Record<string, any> }) =>
    post<Plugin>('/plugins', data),

  update: (id: string, updates?: Partial<Plugin>) =>
    patch<Plugin>(`/plugins/${id}`, updates),

  uninstall: (id: string) => del(`/plugins/${id}`),

  // Actions
  enable: (id: string) => post<Plugin>(`/plugins/${id}/enable`),

  disable: (id: string) => post<Plugin>(`/plugins/${id}/disable`),

  configure: (id: string, config: Record<string, any>) =>
    post<Plugin>(`/plugins/${id}/configure`, config),

  // Marketplace
  getMarketplace: () =>
    get<Array<{ id: string; name: string; description: string; author: string; downloads: number; rating: number }>>(
      '/plugins/marketplace'
    ),

  // Repository
  getRepositories: () =>
    get<Array<{ id: string; name: string; url: string; enabled: boolean }>>('/plugins/repositories'),

  addRepository: (name: string, url: string) =>
    post('/plugins/repositories', { name, url }),

  removeRepository: (id: string) =>
    del(`/plugins/repositories/${id}`),
};

// ============================================
// Dashboard API
// ============================================
export const dashboardApi = {
  getStats: () => get<DashboardStats>('/dashboard/stats'),

  getNetworkGraph: () => get<NetworkGraph>('/dashboard/network-graph'),

  getScanTrend: (days: number = 30) =>
    get<Array<{ date: string; count: number }>>(`/dashboard/scan-trend`, {
      params: { days },
    }),

  getVulnerabilityTrend: (days: number = 30) =>
    get<Array<{ date: string; critical: number; high: number; medium: number; low: number }>>(
      `/dashboard/vulnerability-trend`,
      { params: { days } }
    ),

  getTopVulnerabilities: (limit: number = 10) =>
    get<Array<{ name: string; count: number; severity: string }>>(
      `/dashboard/top-vulnerabilities`,
      { params: { limit } }
    ),

  getComplianceScore: () =>
    get<{ overall: number; frameworks: Array<{ id: string; name: string; score: number }> }>(
      '/dashboard/compliance-score'
    ),

  getRecentActivity: (limit: number = 20) =>
    get<Array<{ type: string; description: string; timestamp: string; user?: string }>>(
      '/dashboard/recent-activity',
      { params: { limit } }
    ),

  getSystemHealth: () =>
    get<{
      status: string;
      components: Array<{ name: string; status: string; latency?: number }>;
    }>('/dashboard/health'),
};

// ============================================
// Compliance API
// ============================================
export const complianceApi = {
  getFrameworks: () => get<ComplianceFramework[]>('/compliance/frameworks'),

  getFramework: (id: string) => get<ComplianceFramework>(`/compliance/frameworks/${id}`),

  runAssessment: (frameworkId: string, scanId: string) =>
    post(`/compliance/assessments`, { framework_id: frameworkId, scan_id: scanId }),

  getAssessment: (id: string) =>
    get<{
      id: string;
      framework: ComplianceFramework;
      scan: Scan;
      results: any[];
      score: number;
      createdAt: string;
    }>(`/compliance/assessments/${id}`),

  getGapAnalysis: (frameworkId: string, scanId: string) =>
    get<{
      gaps: Array<{ control: string; status: string; findings: string[] }>;
      recommendations: string[];
    }>(`/compliance/gap-analysis`, { params: { framework_id: frameworkId, scan_id: scanId } }),

  generateReport: (frameworkId: string, scanId: string, format: string) =>
    get<Blob>(`/compliance/reports`, {
      params: { framework_id: frameworkId, scan_id: scanId, format },
      responseType: 'blob',
    }),
};

// ============================================
// MCP (Model Context Protocol) API
// ============================================
export const mcpApi = {
  getServers: () => get<MCPServer[]>('/mcp/servers'),

  getServer: (id: string) => get<MCPServer>(`/mcp/servers/${id}`),

  registerServer: (data: { name: string; url: string; auth?: any }) =>
    post<MCPServer>('/mcp/servers', data),

  updateServer: (id: string, updates: Partial<MCPServer>) =>
    patch<MCPServer>(`/mcp/servers/${id}`, updates),

  deleteServer: (id: string) => del(`/mcp/servers/${id}`),

  testConnection: (id: string) =>
    post<{ success: boolean; latency: number }>(`/mcp/servers/${id}/test`),

  invokeCapability: (serverId: string, capability: string, params: any) =>
    post<any>(`/mcp/servers/${serverId}/invoke`, { capability, params }),

  // AI Analysis
  analyzeVulnerability: (vulnerabilityId: string, context?: any) =>
    post<any>(`/mcp/ai/analyze-vulnerability`, { vulnerability_id: vulnerabilityId, context }),

  suggestRemediation: (vulnerabilityId: string) =>
    post<{ suggestions: string[] }>(`/mcp/ai/suggest-remediation`, { vulnerability_id: vulnerabilityId }),

  generateReport: (scanIds: string[], template?: string) =>
    post<{ content: string }>(`/mcp/ai/generate-report`, { scan_ids: scanIds, template }),
};

// ============================================
// Settings API
// ============================================
export const settingsApi = {
  get: () => get<SystemSettings>('/settings'),

  update: (settings: Partial<SystemSettings>) =>
    patch<SystemSettings>('/settings', settings),

  updateGeneral: (settings: Partial<SystemSettings['general']>) =>
    patch('/settings/general', settings),

  updateSecurity: (settings: Partial<SystemSettings['security']>) =>
    patch('/settings/security', settings),

  updateScanning: (settings: Partial<SystemSettings['scanning']>) =>
    patch('/settings/scanning', settings),

  updateNotifications: (settings: Partial<SystemSettings['notifications']>) =>
    patch('/settings/notifications', settings),

  updateIntegrations: (settings: Partial<SystemSettings['integrations']>) =>
    patch('/settings/integrations', settings),

  // Backup & Restore
  createBackup: () =>
    post<{ id: string; download_url: string }>('/settings/backup'),

  restoreBackup: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return post('/settings/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Maintenance
  runMaintenance: () =>
    post('/settings/maintenance'),

  clearCache: () =>
    post('/settings/clear-cache'),

  // Logs
  getLogs: (type: string, lines?: number) =>
    get<string[]>(`/settings/logs`, { params: { type, lines } }),
};

// ============================================
// Search API
// ============================================
export const searchApi = {
  global: (query: string, filters?: SearchFilters, pagination?: PaginationParams) =>
    get<{
      results: Array<{ type: string; item: any; score: number }>;
      meta: ApiMeta;
    }>('/search', {
      params: { q: query, ...filters, ...pagination },
    }),

  suggestions: (query: string) =>
    get<string[]>('/search/suggestions', { params: { q: query } }),

  advanced: (params: {
    query: string;
    types: string[];
    filters: SearchFilters;
    sort: { field: string; order: 'asc' | 'desc' };
    pagination: PaginationParams;
  }) =>
    post<{
      results: Array<{ type: string; item: any }>;
      facets: any;
      meta: ApiMeta;
    }>('/search/advanced', params),
};

// ============================================
// File Upload API
// ============================================
export const uploadApi = {
  uploadPlugin: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return post<Plugin>('/upload/plugin', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  uploadTargetList: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return post<{ targets: string[]; count: number }>('/upload/targets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  importScan: (file: File, format: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);
    return post<Scan>('/upload/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ============================================
// AI Analysis API
// ============================================
export const aiApi = {
  analyze: (data: { message: string; context?: any; model?: string }) =>
    post<{
      response: string;
      tokens: number;
      confidence: number;
      sources?: string[];
    }>('/ai/analyze', data),

  getInsights: () =>
    get<Array<{
      id: string;
      title: string;
      description: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      category: string;
      confidence: number;
    }>>('/ai/insights'),

  getHistory: () =>
    get<Array<{
      id: string;
      title: string;
      date: string;
    }>>('/ai/history'),

  analyzeVulnerability: (vulnerabilityId: string) =>
    post<{
      analysis: string;
      recommendations: string[];
      confidence: number;
    }>(`/ai/analyze-vulnerability/${vulnerabilityId}`),

  analyzeCode: (code: string, language: string) =>
    post<{
      findings: Array<{
        line: number;
        severity: string;
        description: string;
        recommendation: string;
      }>;
      summary: string;
    }>('/ai/analyze-code', { code, language }),

  explainCVE: (cveId: string) =>
    post<{
      description: string;
      impact: string;
      remediation: string;
      references: string[];
    }>(`/ai/explain-cve/${cveId}`),
};

// ============================================
// Notifications API
// ============================================
export const notificationApi = {
  list: (filters?: { read?: boolean; type?: string[] }) =>
    get<{
      notifications: Array<{
        id: string;
        title: string;
        message: string;
        type: string;
        severity: string;
        read: boolean;
        timestamp: string;
        link?: string;
      }>;
      meta: ApiMeta;
    }>('/notifications', { params: filters }),

  markAsRead: (id: string) =>
    patch(`/notifications/${id}/read`),

  markAllAsRead: () =>
    post('/notifications/mark-all-read'),

  delete: (id: string) =>
    del(`/notifications/${id}`),

  getPreferences: () =>
    get<{
      email: boolean;
      push: boolean;
      slack: boolean;
      webhook: boolean;
      vulnerabilityAlerts: boolean;
      scanCompleted: boolean;
      systemUpdates: boolean;
      weeklyReports: boolean;
    }>('/notifications/preferences'),

  updatePreferences: (preferences: any) =>
    patch('/notifications/preferences', preferences),
};

// ============================================
// Export default API client
// ============================================
export default apiClient;
