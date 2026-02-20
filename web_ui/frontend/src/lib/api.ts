// API Client für Zen-AI-Pentest Backend
const API_BASE = '/api';

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  components: {
    database: string;
    redis: string;
    celery: string;
  };
}

export interface SystemStats {
  total_scans: number;
  active_scans: number;
  total_findings: number;
  critical_findings: number;
  high_findings: number;
  agents_online: number;
}

export async function getHealth(): Promise<HealthStatus | null> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    return null;
  }
}

export async function getStats(): Promise<SystemStats | null> {
  try {
    const response = await fetch(`${API_BASE}/v1/stats`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Stats fetch failed:', error);
    return null;
  }
}

export async function getScans(): Promise<any[] | null> {
  try {
    const response = await fetch(`${API_BASE}/v1/scans`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Scans fetch failed:', error);
    return null;
  }
}
