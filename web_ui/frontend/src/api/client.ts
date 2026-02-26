import axios from 'axios';
import type { Agent, Scan } from '../store/agentStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Agent API
export const agentApi = {
  getAll: async (): Promise<Agent[]> => {
    // Mock data for now - replace with actual API call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          {
            id: 'agent-001',
            name: 'Recon Agent',
            status: 'online',
            lastSeen: new Date().toISOString(),
            cpuUsage: 45,
            memoryUsage: 60,
            activeTasks: 2,
            capabilities: ['nmap', 'subfinder', 'dns'],
            version: '1.0.0',
          },
          {
            id: 'agent-002',
            name: 'Exploit Agent',
            status: 'busy',
            lastSeen: new Date().toISOString(),
            cpuUsage: 78,
            memoryUsage: 82,
            activeTasks: 1,
            capabilities: ['metasploit', 'sqlmap', 'xss'],
            version: '1.0.0',
          },
          {
            id: 'agent-003',
            name: 'Scan Agent',
            status: 'online',
            lastSeen: new Date().toISOString(),
            cpuUsage: 23,
            memoryUsage: 35,
            activeTasks: 0,
            capabilities: ['nuclei', 'nmap', 'zap'],
            version: '1.0.0',
          },
        ]);
      }, 500);
    });
  },

  getById: async (id: string): Promise<Agent> => {
    const response = await apiClient.get(`/api/agents/${id}`);
    return response.data;
  },

  sendCommand: async (agentId: string, command: string, params: Record<string, unknown>): Promise<void> => {
    await apiClient.post(`/api/agents/${agentId}/command`, { command, params });
  },
};

// Scan API
export const scanApi = {
  getAll: async (): Promise<Scan[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          {
            id: 'scan-001',
            agentId: 'agent-001',
            target: 'example.com',
            status: 'running',
            progress: 45,
            startedAt: new Date().toISOString(),
            findings: 3,
          },
          {
            id: 'scan-002',
            agentId: 'agent-002',
            target: '192.168.1.1',
            status: 'completed',
            progress: 100,
            startedAt: new Date(Date.now() - 3600000).toISOString(),
            completedAt: new Date().toISOString(),
            findings: 12,
          },
        ]);
      }, 500);
    });
  },

  create: async (scan: Partial<Scan>): Promise<Scan> => {
    const response = await apiClient.post('/api/scans', scan);
    return response.data;
  },
};

// WebSocket connection for real-time updates
export const createWebSocket = (onMessage: (data: unknown) => void): WebSocket => {
  const ws = new WebSocket(`ws://${API_BASE_URL.replace('http://', '')}/ws`);
  
  ws.onopen = () => {
    console.log('WebSocket connected');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };
  
  return ws;
};
