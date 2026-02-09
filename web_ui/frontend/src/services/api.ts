// ============================================
// Zen-AI-Pentest API Service
// ============================================

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Scan,
  Finding,
  Agent,
  Report,
  AttackGraph,
  TimelineEvent,
  Alert,
  ScanStatistics,
  ApiResponse,
  PaginatedResponse,
  FindingsFilter,
  SortConfig,
  Evidence,
} from '../types';

// Axios Instance Configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor - Add Auth Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor - Error Handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// Scan Management Endpoints
// ============================================

export const scanApi = {
  getAll: async (params?: {
    page?: number;
    perPage?: number;
    status?: string;
    type?: string;
  }): Promise<PaginatedResponse<Scan>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<Scan>>>('/scans', { params });
    return response.data.data;
  },

  getById: async (id: string): Promise<Scan> => {
    const response = await apiClient.get<ApiResponse<Scan>>(`/scans/${id}`);
    return response.data.data;
  },

  create: async (data: Partial<Scan>): Promise<Scan> => {
    const response = await apiClient.post<ApiResponse<Scan>>('/scans', data);
    return response.data.data;
  },

  update: async (id: string, data: Partial<Scan>): Promise<Scan> => {
    const response = await apiClient.patch<ApiResponse<Scan>>(`/scans/${id}`, data);
    return response.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/scans/${id}`);
  },

  start: async (id: string): Promise<Scan> => {
    const response = await apiClient.post<ApiResponse<Scan>>(`/scans/${id}/start`);
    return response.data.data;
  },

  pause: async (id: string): Promise<Scan> => {
    const response = await apiClient.post<ApiResponse<Scan>>(`/scans/${id}/pause`);
    return response.data.data;
  },

  resume: async (id: string): Promise<Scan> => {
    const response = await apiClient.post<ApiResponse<Scan>>(`/scans/${id}/resume`);
    return response.data.data;
  },

  stop: async (id: string): Promise<Scan> => {
    const response = await apiClient.post<ApiResponse<Scan>>(`/scans/${id}/stop`);
    return response.data.data;
  },

  getProgress: async (id: string): Promise<{ progress: number; status: string }> => {
    const response = await apiClient.get<ApiResponse<{ progress: number; status: string }>>(
      `/scans/${id}/progress`
    );
    return response.data.data;
  },

  getStatistics: async (): Promise<ScanStatistics> => {
    const response = await apiClient.get<ApiResponse<ScanStatistics>>('/scans/statistics');
    return response.data.data;
  },
};

// ============================================
// Finding Management Endpoints
// ============================================

export const findingsApi = {
  getAll: async (params?: {
    scanId?: string;
    page?: number;
    perPage?: number;
    filter?: FindingsFilter;
    sort?: SortConfig;
  }): Promise<PaginatedResponse<Finding>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<Finding>>>('/findings', {
      params,
    });
    return response.data.data;
  },

  getById: async (id: string): Promise<Finding> => {
    const response = await apiClient.get<ApiResponse<Finding>>(`/findings/${id}`);
    return response.data.data;
  },

  update: async (id: string, data: Partial<Finding>): Promise<Finding> => {
    const response = await apiClient.patch<ApiResponse<Finding>>(`/findings/${id}`, data);
    return response.data.data;
  },

  updateNotes: async (id: string, notes: string): Promise<Finding> => {
    const response = await apiClient.patch<ApiResponse<Finding>>(`/findings/${id}/notes`, {
      notes,
    });
    return response.data.data;
  },

  validate: async (id: string, validated: boolean): Promise<Finding> => {
    const response = await apiClient.post<ApiResponse<Finding>>(`/findings/${id}/validate`, {
      validated,
    });
    return response.data.data;
  },

  markAsFalsePositive: async (id: string, isFalsePositive: boolean): Promise<Finding> => {
    const response = await apiClient.post<ApiResponse<Finding>>(`/findings/${id}/false-positive`, {
      isFalsePositive,
    });
    return response.data.data;
  },

  bulkUpdate: async (
    ids: string[],
    data: Partial<Finding>
  ): Promise<{ updated: number }> => {
    const response = await apiClient.post<ApiResponse<{ updated: number }>>('/findings/bulk-update', {
      ids,
      data,
    });
    return response.data.data;
  },

  bulkDelete: async (ids: string[]): Promise<{ deleted: number }> => {
    const response = await apiClient.post<ApiResponse<{ deleted: number }>>('/findings/bulk-delete', {
      ids,
    });
    return response.data.data;
  },

  export: async (
    ids: string[],
    format: 'json' | 'csv' | 'xml'
  ): Promise<Blob> => {
    const response = await apiClient.post(`/findings/export`, { ids, format }, {
      responseType: 'blob',
    });
    return response.data;
  },

  getByScan: async (scanId: string): Promise<Finding[]> => {
    const response = await apiClient.get<ApiResponse<Finding[]>>(`/scans/${scanId}/findings`);
    return response.data.data;
  },

  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get<ApiResponse<string[]>>('/findings/categories');
    return response.data.data;
  },
};

// ============================================
// Evidence Management Endpoints
// ============================================

export const evidenceApi = {
  getByFinding: async (findingId: string): Promise<Evidence[]> => {
    const response = await apiClient.get<ApiResponse<Evidence[]>>(`/findings/${findingId}/evidence`);
    return response.data.data;
  },

  getById: async (id: string): Promise<Evidence> => {
    const response = await apiClient.get<ApiResponse<Evidence>>(`/evidence/${id}`);
    return response.data.data;
  },

  upload: async (
    findingId: string,
    file: File,
    type: string,
    metadata?: Record<string, unknown>
  ): Promise<Evidence> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    const response = await apiClient.post<ApiResponse<Evidence>>(
      `/findings/${findingId}/evidence`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/evidence/${id}`);
  },

  download: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/evidence/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  getScreenshot: async (id: string): Promise<string> => {
    const response = await apiClient.get<ApiResponse<{ url: string }>>(`/evidence/${id}/screenshot`);
    return response.data.data.url;
  },
};

// ============================================
// Agent Control Endpoints
// ============================================

export const agentApi = {
  getAll: async (): Promise<Agent[]> => {
    const response = await apiClient.get<ApiResponse<Agent[]>>('/agents');
    return response.data.data;
  },

  getById: async (id: string): Promise<Agent> => {
    const response = await apiClient.get<ApiResponse<Agent>>(`/agents/${id}`);
    return response.data.data;
  },

  register: async (data: Partial<Agent>): Promise<Agent> => {
    const response = await apiClient.post<ApiResponse<Agent>>('/agents/register', data);
    return response.data.data;
  },

  unregister: async (id: string): Promise<void> => {
    await apiClient.delete(`/agents/${id}`);
  },

  assignToScan: async (agentId: string, scanId: string): Promise<Agent> => {
    const response = await apiClient.post<ApiResponse<Agent>>(
      `/agents/${agentId}/assign`,
      { scanId }
    );
    return response.data.data;
  },

  releaseFromScan: async (agentId: string): Promise<Agent> => {
    const response = await apiClient.post<ApiResponse<Agent>>(`/agents/${agentId}/release`);
    return response.data.data;
  },

  getMetrics: async (id: string): Promise<Agent['metrics']> => {
    const response = await apiClient.get<ApiResponse<Agent['metrics']>>(`/agents/${id}/metrics`);
    return response.data.data;
  },

  sendCommand: async (id: string, command: string, params?: unknown): Promise<void> => {
    await apiClient.post(`/agents/${id}/command`, { command, params });
  },
};

// ============================================
// Report Generation Endpoints
// ============================================

export const reportApi = {
  getAll: async (params?: { scanId?: string }): Promise<Report[]> => {
    const response = await apiClient.get<ApiResponse<Report[]>>('/reports', { params });
    return response.data.data;
  },

  getById: async (id: string): Promise<Report> => {
    const response = await apiClient.get<ApiResponse<Report>>(`/reports/${id}`);
    return response.data.data;
  },

  create: async (data: {
    scanId: string;
    name: string;
    format: string;
    template?: string;
  }): Promise<Report> => {
    const response = await apiClient.post<ApiResponse<Report>>('/reports', data);
    return response.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/reports/${id}`);
  },

  download: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/reports/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  preview: async (id: string): Promise<string> => {
    const response = await apiClient.get<ApiResponse<{ content: string }>>(
      `/reports/${id}/preview`
    );
    return response.data.data.content;
  },

  generate: async (scanId: string, format: string): Promise<Report> => {
    const response = await apiClient.post<ApiResponse<Report>>('/reports/generate', {
      scanId,
      format,
    });
    return response.data.data;
  },

  getTemplates: async (): Promise<string[]> => {
    const response = await apiClient.get<ApiResponse<string[]>>('/reports/templates');
    return response.data.data;
  },
};

// ============================================
// Attack Graph Endpoints
// ============================================

export const attackGraphApi = {
  getByScan: async (scanId: string): Promise<AttackGraph> => {
    const response = await apiClient.get<ApiResponse<AttackGraph>>(
      `/scans/${scanId}/attack-graph`
    );
    return response.data.data;
  },

  calculatePaths: async (
    scanId: string,
    source: string,
    target: string
  ): Promise<string[][]> => {
    const response = await apiClient.post<ApiResponse<string[][]>>(
      `/scans/${scanId}/attack-graph/paths`,
      { source, target }
    );
    return response.data.data;
  },

  export: async (scanId: string, format: 'png' | 'svg' | 'json'): Promise<Blob> => {
    const response = await apiClient.get(`/scans/${scanId}/attack-graph/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
};

// ============================================
// Timeline Endpoints
// ============================================

export const timelineApi = {
  getByScan: async (scanId: string): Promise<TimelineEvent[]> => {
    const response = await apiClient.get<ApiResponse<TimelineEvent[]>>(
      `/scans/${scanId}/timeline`
    );
    return response.data.data;
  },

  getAll: async (params?: { from?: string; to?: string }): Promise<TimelineEvent[]> => {
    const response = await apiClient.get<ApiResponse<TimelineEvent[]>>('/timeline', { params });
    return response.data.data;
  },
};

// ============================================
// Alert Endpoints
// ============================================

export const alertApi = {
  getAll: async (params?: { acknowledged?: boolean }): Promise<Alert[]> => {
    const response = await apiClient.get<ApiResponse<Alert[]>>('/alerts', { params });
    return response.data.data;
  },

  acknowledge: async (id: string): Promise<Alert> => {
    const response = await apiClient.post<ApiResponse<Alert>>(`/alerts/${id}/acknowledge`);
    return response.data.data;
  },

  acknowledgeAll: async (): Promise<{ acknowledged: number }> => {
    const response = await apiClient.post<ApiResponse<{ acknowledged: number }>>(
      '/alerts/acknowledge-all'
    );
    return response.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/alerts/${id}`);
  },
};

// ============================================
// WebSocket Service
// ============================================

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private listeners: Map<string, Set<(data: unknown) => void>> = new Map();

  connect(token?: string): void {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
    const url = token ? `${wsUrl}?token=${token}` : wsUrl;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => {
        const token = localStorage.getItem('auth_token') || undefined;
        this.connect(token);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  private handleMessage(message: { type: string; payload: unknown }): void {
    const listeners = this.listeners.get(message.type);
    if (listeners) {
      listeners.forEach((callback) => callback(message.payload));
    }
  }

  subscribe(type: string, callback: (data: unknown) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(callback);

    return () => {
      this.listeners.get(type)?.delete(callback);
    };
  }

  send(type: string, payload: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}

// Export singleton instance
export const wsService = new WebSocketService();

// Default export
export default apiClient;
