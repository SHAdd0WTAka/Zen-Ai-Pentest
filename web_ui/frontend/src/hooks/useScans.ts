// ============================================
// Scan Management Hooks
// ============================================

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
} from '@tanstack/react-query';
import { scanApi } from '../services/api';
import { Scan, ScanStatistics } from '../types';

const SCAN_KEYS = {
  all: ['scans'] as const,
  lists: () => [...SCAN_KEYS.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...SCAN_KEYS.lists(), filters] as const,
  details: () => [...SCAN_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...SCAN_KEYS.details(), id] as const,
  statistics: () => [...SCAN_KEYS.all, 'statistics'] as const,
  progress: (id: string) => [...SCAN_KEYS.detail(id), 'progress'] as const,
};

// Get all scans with pagination and filters
export const useScans = (
  params?: {
    page?: number;
    perPage?: number;
    status?: string;
    type?: string;
  },
  options?: UseQueryOptions
) => {
  return useQuery({
    queryKey: SCAN_KEYS.list(params || {}),
    queryFn: () => scanApi.getAll(params),
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
    ...options,
  });
};

// Get single scan by ID
export const useScan = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: SCAN_KEYS.detail(id),
    queryFn: () => scanApi.getById(id),
    enabled: !!id,
    refetchInterval: 3000,
    ...options,
  });
};

// Get scan statistics
export const useScanStatistics = (options?: UseQueryOptions) => {
  return useQuery({
    queryKey: SCAN_KEYS.statistics(),
    queryFn: () => scanApi.getStatistics(),
    refetchInterval: 10000,
    ...options,
  });
};

// Get scan progress
export const useScanProgress = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: SCAN_KEYS.progress(id),
    queryFn: () => scanApi.getProgress(id),
    enabled: !!id,
    refetchInterval: 2000,
    ...options,
  });
};

// Create scan mutation
export const useCreateScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Scan>) => scanApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.lists() });
    },
  });
};

// Update scan mutation
export const useUpdateScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Scan> }) =>
      scanApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.lists() });
    },
  });
};

// Delete scan mutation
export const useDeleteScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => scanApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.lists() });
    },
  });
};

// Start scan mutation
export const useStartScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => scanApi.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.lists() });
    },
  });
};

// Pause scan mutation
export const usePauseScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => scanApi.pause(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.detail(id) });
    },
  });
};

// Resume scan mutation
export const useResumeScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => scanApi.resume(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.detail(id) });
    },
  });
};

// Stop scan mutation
export const useStopScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => scanApi.stop(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: SCAN_KEYS.lists() });
    },
  });
};
