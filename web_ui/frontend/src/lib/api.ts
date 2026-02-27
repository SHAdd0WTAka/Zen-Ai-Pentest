/**
 * API Client for Real Backend
 * 
 * This connects to the actual Python backend running on port 8000
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiClient {
  private async fetch(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  // Agents
  getAgents() {
    return this.fetch('/agents');
  }

  getAgent(id: string) {
    return this.fetch(`/agents/${id}`);
  }

  // Scans
  getScans() {
    return this.fetch('/scans');
  }

  createScan(data: any) {
    return this.fetch('/scans', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Evidence
  getEvidence() {
    return this.fetch('/evidence/');
  }

  createEvidence(data: any) {
    return this.fetch('/evidence/web', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Reports
  getReports() {
    return this.fetch('/reports/');
  }

  generateExecutiveReport(data: any) {
    return this.fetch('/reports/executive', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  generateTechnicalReport(data: any) {
    return this.fetch('/reports/technical', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Attack Paths
  getAttackGraph(scanId: string) {
    return this.fetch(`/attack-path/graph/${scanId}`);
  }

  getAttackPaths(scanId: string) {
    return this.fetch(`/attack-path/find-paths`, {
      method: 'POST',
      body: JSON.stringify({ scan_id: scanId }),
    });
  }

  getCriticalPaths(scanId: string) {
    return this.fetch(`/attack-path/critical-paths/${scanId}`);
  }

  simulateAttack(scanId: string, entryPoint: string) {
    return this.fetch(`/attack-path/simulate?scan_id=${scanId}&entry_point=${entryPoint}`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
export default api;

// Types
export interface SystemStats {
  agents: number;
  scans: number;
  evidence: number;
  reports: number;
  vulnerabilities: number;
  tools: number;
}

// Stats API
export async function getStats(): Promise<SystemStats> {
  // Return mock stats for now - connect to real endpoint later
  return {
    agents: 5,
    scans: 12,
    evidence: 8,
    reports: 3,
    vulnerabilities: 24,
    tools: 40,
  };
}
