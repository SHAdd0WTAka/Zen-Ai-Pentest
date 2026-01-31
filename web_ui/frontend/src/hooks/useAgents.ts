// ============================================
// Agent Management Hooks
// ============================================

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
} from '@tanstack/react-query';
import { agentApi } from '../services/api';
import { Agent } from '../types';

const AGENT_KEYS = {
  all: ['agents'] as const,
  lists: () => [...AGENT_KEYS.all, 'list'] as const,
  details: () => [...AGENT_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...AGENT_KEYS.details(), id] as const,
  metrics: (id: string) => [...AGENT_KEYS.detail(id), 'metrics'] as const,
};

// Get all agents
export const useAgents = (options?: UseQueryOptions) => {
  return useQuery({
    queryKey: AGENT_KEYS.lists(),
    queryFn: () => agentApi.getAll(),
    refetchInterval: 5000,
    ...options,
  });
};

// Get single agent
export const useAgent = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: AGENT_KEYS.detail(id),
    queryFn: () => agentApi.getById(id),
    enabled: !!id,
    refetchInterval: 3000,
    ...options,
  });
};

// Get agent metrics
export const useAgentMetrics = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: AGENT_KEYS.metrics(id),
    queryFn: () => agentApi.getMetrics(id),
    enabled: !!id,
    refetchInterval: 5000,
    ...options,
  });
};

// Register agent mutation
export const useRegisterAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Agent>) => agentApi.register(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AGENT_KEYS.lists() });
    },
  });
};

// Unregister agent mutation
export const useUnregisterAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => agentApi.unregister(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AGENT_KEYS.lists() });
    },
  });
};

// Assign agent to scan mutation
export const useAssignAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, scanId }: { agentId: string; scanId: string }) =>
      agentApi.assignToScan(agentId, scanId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: AGENT_KEYS.detail(variables.agentId) });
      queryClient.invalidateQueries({ queryKey: AGENT_KEYS.lists() });
    },
  });
};

// Release agent from scan mutation
export const useReleaseAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => agentApi.releaseFromScan(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: AGENT_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: AGENT_KEYS.lists() });
    },
  });
};

// Send command to agent mutation
export const useSendAgentCommand = () => {
  return useMutation({
    mutationFn: ({
      id,
      command,
      params,
    }: {
      id: string;
      command: string;
      params?: unknown;
    }) => agentApi.sendCommand(id, command, params),
  });
};
