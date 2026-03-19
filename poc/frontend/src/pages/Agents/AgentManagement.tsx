import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ServerIcon,
  CpuChipIcon,
  CircleStackIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  PlayIcon,
  PauseIcon,
  TrashIcon,
  PlusIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

import { api } from '@/api/client';
import { useWebSocket } from '@/hooks/useWebSocket';

interface Agent {
  id: string;
  name: string;
  hostname: string;
  ipAddress: string;
  version: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  capabilities: string[];
  currentTask: string | null;
  lastHeartbeat: string;
  tasksCompleted: number;
  tasksFailed: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
}

const statusConfig = {
  online: { color: 'text-low-500 bg-low-500/10', icon: CheckCircleIcon, label: 'Online' },
  offline: { color: 'text-gray-500 bg-gray-500/10', icon: XCircleIcon, label: 'Offline' },
  busy: { color: 'text-brand-500 bg-brand-500/10', icon: ClockIcon, label: 'Busy' },
  error: { color: 'text-critical-500 bg-critical-500/10', icon: XCircleIcon, label: 'Error' },
};

export const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    online: 0,
    busy: 0,
    offline: 0,
    totalTasksCompleted: 0,
    totalTasksFailed: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const { isConnected, subscribeToScan } = useWebSocket({
    onAgentStatus: (payload) => {
      // Update agent status in real-time
      setAgents((prev) =>
        prev.map((agent) =>
          agent.id === payload.agentId
            ? { ...agent, status: payload.status, ...payload.metrics }
            : agent
        )
      );
    },
  });

  useEffect(() => {
    fetchAgents();
    fetchStats();

    // Poll for updates every 30 seconds
    const interval = setInterval(() => {
      fetchAgents();
      fetchStats();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await api.get('/agents');
      if (response.success) {
        setAgents(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/agents/stats');
      if (response.success) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch agent stats:', error);
    }
  };

  const handleRegisterAgent = async () => {
    // This would open a modal to register a new agent
    console.log('Register new agent');
  };

  const handleUpdateStatus = async (agentId: string, newStatus: string) => {
    try {
      await api.patch(`/agents/${agentId}/status`, { status: newStatus });
      fetchAgents();
    } catch (error) {
      console.error('Failed to update agent status:', error);
    }
  };

  const handleUnregisterAgent = async (agentId: string) => {
    if (!confirm('Are you sure you want to unregister this agent?')) return;

    try {
      await api.delete(`/agents/${agentId}`);
      fetchAgents();
    } catch (error) {
      console.error('Failed to unregister agent:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text">Agent Management</h1>
          <p className="text-dark-muted mt-1">
            Manage scanning agents and monitor their performance
          </p>
        </div>
        <button
          onClick={handleRegisterAgent}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors"
        >
          <PlusIcon className="h-5 w-5" />
          Register Agent
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-card border border-dark-border rounded-xl p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Total Agents</p>
              <p className="text-3xl font-bold text-dark-text mt-1">{stats.total}</p>
            </div>
            <div className="h-12 w-12 bg-brand-500/10 rounded-lg flex items-center justify-center">
              <ServerIcon className="h-6 w-6 text-brand-500" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-dark-card border border-dark-border rounded-xl p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Online</p>
              <p className="text-3xl font-bold text-low-500 mt-1">{stats.online}</p>
            </div>
            <div className="h-12 w-12 bg-low-500/10 rounded-lg flex items-center justify-center">
              <CheckCircleIcon className="h-6 w-6 text-low-500" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-dark-card border border-dark-border rounded-xl p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Busy</p>
              <p className="text-3xl font-bold text-brand-500 mt-1">{stats.busy}</p>
            </div>
            <div className="h-12 w-12 bg-brand-500/10 rounded-lg flex items-center justify-center">
              <ClockIcon className="h-6 w-6 text-brand-500" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-dark-card border border-dark-border rounded-xl p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-muted text-sm">Tasks Completed</p>
              <p className="text-3xl font-bold text-dark-text mt-1">
                {stats.totalTasksCompleted.toLocaleString()}
              </p>
            </div>
            <div className="h-12 w-12 bg-dark-bg rounded-lg flex items-center justify-center">
              <ArrowPathIcon className="h-6 w-6 text-dark-muted" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Agents List */}
      <div className="bg-dark-card border border-dark-border rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-dark-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-dark-text">Registered Agents</h2>
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-low-500' : 'bg-critical-500'}`} />
            <span className="text-sm text-dark-muted">
              {isConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
            </span>
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-dark-muted">Loading agents...</div>
        ) : agents.length === 0 ? (
          <div className="p-8 text-center text-dark-muted">
            No agents registered. Register your first agent to get started.
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {agents.map((agent) => {
              const status = statusConfig[agent.status];
              const StatusIcon = status.icon;

              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-6 hover:bg-dark-bg/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`h-12 w-12 rounded-lg flex items-center justify-center ${status.color}`}>
                        <ServerIcon className="h-6 w-6" />
                      </div>

                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="font-medium text-dark-text">{agent.name}</h3>
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                            <StatusIcon className="h-3.5 w-3.5" />
                            {status.label}
                          </span>
                        </div>

                        <div className="flex items-center gap-4 mt-1 text-sm text-dark-muted">
                          <span>{agent.hostname}</span>
                          <span>•</span>
                          <span>{agent.ipAddress}</span>
                          <span>•</span>
                          <span>v{agent.version}</span>
                        </div>

                        <div className="flex items-center gap-2 mt-3">
                          {agent.capabilities.map((cap, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-dark-bg rounded text-xs text-dark-muted"
                            >
                              {cap}
                            </span>
                          ))}
                        </div>

                        {agent.currentTask && (
                          <div className="mt-3 flex items-center gap-2 text-sm text-brand-500">
                            <ClockIcon className="h-4 w-4 animate-pulse" />
                            <span>Executing: {agent.currentTask}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-start gap-6">
                      {/* Metrics */}
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="flex items-center justify-center gap-1 text-dark-muted text-xs mb-1">
                            <CpuChipIcon className="h-3 w-3" />
                            CPU
                          </div>
                          <div className="text-sm font-medium text-dark-text">
                            {agent.cpuUsage.toFixed(1)}%
                          </div>
                          <div className="w-16 h-1 bg-dark-border rounded-full mt-1 mx-auto overflow-hidden">
                            <div
                              className="h-full bg-brand-500 rounded-full"
                              style={{ width: `${agent.cpuUsage}%` }}
                            />
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-center gap-1 text-dark-muted text-xs mb-1">
                            <CircleStackIcon className="h-3 w-3" />
                            RAM
                          </div>
                          <div className="text-sm font-medium text-dark-text">
                            {agent.memoryUsage.toFixed(1)}%
                          </div>
                          <div className="w-16 h-1 bg-dark-border rounded-full mt-1 mx-auto overflow-hidden">
                            <div
                              className="h-full bg-brand-500 rounded-full"
                              style={{ width: `${agent.memoryUsage}%` }}
                            />
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-center gap-1 text-dark-muted text-xs mb-1">
                            <CircleStackIcon className="h-3 w-3" />
                            Disk
                          </div>
                          <div className="text-sm font-medium text-dark-text">
                            {agent.diskUsage.toFixed(1)}%
                          </div>
                          <div className="w-16 h-1 bg-dark-border rounded-full mt-1 mx-auto overflow-hidden">
                            <div
                              className="h-full bg-brand-500 rounded-full"
                              style={{ width: `${agent.diskUsage}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        {agent.status === 'offline' ? (
                          <button
                            onClick={() => handleUpdateStatus(agent.id, 'online')}
                            className="p-2 text-dark-muted hover:text-low-500 hover:bg-low-500/10 rounded-lg transition-colors"
                            title="Mark Online"
                          >
                            <PlayIcon className="h-5 w-5" />
                          </button>
                        ) : agent.status === 'online' ? (
                          <button
                            onClick={() => handleUpdateStatus(agent.id, 'offline')}
                            className="p-2 text-dark-muted hover:text-gray-500 hover:bg-gray-500/10 rounded-lg transition-colors"
                            title="Mark Offline"
                          >
                            <PauseIcon className="h-5 w-5" />
                          </button>
                        ) : null}

                        <button
                          onClick={() => handleUnregisterAgent(agent.id)}
                          className="p-2 text-dark-muted hover:text-critical-500 hover:bg-critical-500/10 rounded-lg transition-colors"
                          title="Unregister"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Task Stats */}
                  <div className="mt-4 pt-4 border-t border-dark-border flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-low-500" />
                      <span className="text-dark-muted">
                        {agent.tasksCompleted} completed
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <XCircleIcon className="h-4 w-4 text-critical-500" />
                      <span className="text-dark-muted">
                        {agent.tasksFailed} failed
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ClockIcon className="h-4 w-4 text-dark-muted" />
                      <span className="text-dark-muted">
                        Last seen: {new Date(agent.lastHeartbeat).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentManagement;
