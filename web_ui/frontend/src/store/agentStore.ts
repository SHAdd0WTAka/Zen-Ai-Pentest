import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface Agent {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  lastSeen: string;
  cpuUsage: number;
  memoryUsage: number;
  activeTasks: number;
  capabilities: string[];
  version: string;
}

export interface Scan {
  id: string;
  agentId: string;
  target: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  findings: number;
}

interface AgentState {
  agents: Agent[];
  scans: Scan[];
  selectedAgent: Agent | null;
  isLoading: boolean;
  error: string | null;
  theme: 'dark' | 'light';
  
  // Actions
  setAgents: (agents: Agent[]) => void;
  setScans: (scans: Scan[]) => void;
  selectAgent: (agent: Agent | null) => void;
  updateAgentStatus: (agentId: string, status: Agent['status']) => void;
  updateAgentMetrics: (agentId: string, cpu: number, memory: number, tasks: number) => void;
  addScan: (scan: Scan) => void;
  updateScanProgress: (scanId: string, progress: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  toggleTheme: () => void;
}

export const useAgentStore = create<AgentState>()(
  devtools(
    (set) => ({
      agents: [],
      scans: [],
      selectedAgent: null,
      isLoading: false,
      error: null,
      theme: 'dark',

      setAgents: (agents) => set({ agents }),
      setScans: (scans) => set({ scans }),
      selectAgent: (agent) => set({ selectedAgent: agent }),
      
      updateAgentStatus: (agentId, status) =>
        set((state) => ({
          agents: state.agents.map((a) =>
            a.id === agentId ? { ...a, status, lastSeen: new Date().toISOString() } : a
          ),
        })),
      
      updateAgentMetrics: (agentId, cpu, memory, tasks) =>
        set((state) => ({
          agents: state.agents.map((a) =>
            a.id === agentId ? { ...a, cpuUsage: cpu, memoryUsage: memory, activeTasks: tasks } : a
          ),
        })),
      
      addScan: (scan) =>
        set((state) => ({ scans: [...state.scans, scan] })),
      
      updateScanProgress: (scanId, progress) =>
        set((state) => ({
          scans: state.scans.map((s) =>
            s.id === scanId ? { ...s, progress } : s
          ),
        })),
      
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      
      toggleTheme: () =>
        set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
    }),
    { name: 'AgentStore' }
  )
);
