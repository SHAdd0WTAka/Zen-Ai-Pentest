// ============================================
// Finding Management Hooks
// ============================================

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
} from '@tanstack/react-query';
import { findingsApi } from '../services/api';
import { Finding, FindingsFilter, SortConfig } from '../types';

const FINDING_KEYS = {
  all: ['findings'] as const,
  lists: () => [...FINDING_KEYS.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...FINDING_KEYS.lists(), filters] as const,
  details: () => [...FINDING_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...FINDING_KEYS.details(), id] as const,
  byScan: (scanId: string) => [...FINDING_KEYS.all, 'scan', scanId] as const,
  categories: () => [...FINDING_KEYS.all, 'categories'] as const,
};

// Get all findings with filters
export const useFindings = (
  params?: {
    scanId?: string;
    page?: number;
    perPage?: number;
    filter?: FindingsFilter;
    sort?: SortConfig;
  },
  options?: UseQueryOptions
) => {
  return useQuery({
    queryKey: FINDING_KEYS.list(params || {}),
    queryFn: () => findingsApi.getAll(params),
    refetchInterval: 5000,
    ...options,
  });
};

// Get single finding
export const useFinding = (id: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: FINDING_KEYS.detail(id),
    queryFn: () => findingsApi.getById(id),
    enabled: !!id,
    ...options,
  });
};

// Get findings by scan
export const useFindingsByScan = (scanId: string, options?: UseQueryOptions) => {
  return useQuery({
    queryKey: FINDING_KEYS.byScan(scanId),
    queryFn: () => findingsApi.getByScan(scanId),
    enabled: !!scanId,
    ...options,
  });
};

// Get finding categories
export const useFindingCategories = (options?: UseQueryOptions) => {
  return useQuery({
    queryKey: FINDING_KEYS.categories(),
    queryFn: () => findingsApi.getCategories(),
    ...options,
  });
};

// Update finding mutation
export const useUpdateFinding = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Finding> }) =>
      findingsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.lists() });
    },
  });
};

// Update finding notes mutation
export const useUpdateFindingNotes = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      findingsApi.updateNotes(id, notes),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.detail(variables.id) });
    },
  });
};

// Validate finding mutation
export const useValidateFinding = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, validated }: { id: string; validated: boolean }) =>
      findingsApi.validate(id, validated),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.lists() });
    },
  });
};

// Mark as false positive mutation
export const useMarkFalsePositive = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, isFalsePositive }: { id: string; isFalsePositive: boolean }) =>
      findingsApi.markAsFalsePositive(id, isFalsePositive),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.lists() });
    },
  });
};

// Bulk update findings mutation
export const useBulkUpdateFindings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ids, data }: { ids: string[]; data: Partial<Finding> }) =>
      findingsApi.bulkUpdate(ids, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.lists() });
    },
  });
};

// Bulk delete findings mutation
export const useBulkDeleteFindings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: string[]) => findingsApi.bulkDelete(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FINDING_KEYS.lists() });
    },
  });
};

// Export findings mutation
export const useExportFindings = () => {
  return useMutation({
    mutationFn: ({
      ids,
      format,
    }: {
      ids: string[];
      format: 'json' | 'csv' | 'xml';
    }) => findingsApi.export(ids, format),
  });
};
