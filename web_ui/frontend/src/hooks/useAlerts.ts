// ============================================
// Alert Management Hooks
// ============================================

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
} from '@tanstack/react-query';
import { alertApi } from '../services/api';
import { Alert } from '../types';

const ALERT_KEYS = {
  all: ['alerts'] as const,
  lists: () => [...ALERT_KEYS.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...ALERT_KEYS.lists(), filters] as const,
};

// Get all alerts
export const useAlerts = (
  params?: { acknowledged?: boolean },
  options?: UseQueryOptions
) => {
  return useQuery({
    queryKey: ALERT_KEYS.list(params || {}),
    queryFn: () => alertApi.getAll(params),
    refetchInterval: 5000,
    ...options,
  });
};

// Get unacknowledged alerts count
export const useUnacknowledgedAlertsCount = () => {
  return useQuery({
    queryKey: ALERT_KEYS.list({ acknowledged: false }),
    queryFn: async () => {
      const alerts = await alertApi.getAll({ acknowledged: false });
      return alerts.length;
    },
    refetchInterval: 3000,
  });
};

// Acknowledge alert mutation
export const useAcknowledgeAlert = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => alertApi.acknowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ALERT_KEYS.lists() });
    },
  });
};

// Acknowledge all alerts mutation
export const useAcknowledgeAllAlerts = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => alertApi.acknowledgeAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ALERT_KEYS.lists() });
    },
  });
};

// Delete alert mutation
export const useDeleteAlert = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => alertApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ALERT_KEYS.lists() });
    },
  });
};
