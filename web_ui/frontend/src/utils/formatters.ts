// ============================================
// Formatting Utilities
// ============================================

import { SeverityLevel, ConfidenceLevel, FindingStatus, AgentStatus, ScanStatus } from '../types';

// Severity colors for Tailwind
export const severityColors: Record<SeverityLevel, { bg: string; text: string; border: string }> = {
  critical: {
    bg: 'bg-red-900/50',
    text: 'text-red-400',
    border: 'border-red-700',
  },
  high: {
    bg: 'bg-orange-900/50',
    text: 'text-orange-400',
    border: 'border-orange-700',
  },
  medium: {
    bg: 'bg-yellow-900/50',
    text: 'text-yellow-400',
    border: 'border-yellow-700',
  },
  low: {
    bg: 'bg-blue-900/50',
    text: 'text-blue-400',
    border: 'border-blue-700',
  },
  info: {
    bg: 'bg-gray-800/50',
    text: 'text-gray-400',
    border: 'border-gray-600',
  },
};

// Severity labels
export const severityLabels: Record<SeverityLevel, string> = {
  critical: 'Kritisch',
  high: 'Hoch',
  medium: 'Mittel',
  low: 'Niedrig',
  info: 'Info',
};

// Confidence colors
export const confidenceColors: Record<ConfidenceLevel, string> = {
  confirmed: 'text-green-400',
  high: 'text-emerald-400',
  medium: 'text-yellow-400',
  low: 'text-orange-400',
};

// Finding status colors
export const findingStatusColors: Record<FindingStatus, { bg: string; text: string }> = {
  open: { bg: 'bg-red-900/50', text: 'text-red-400' },
  in_review: { bg: 'bg-yellow-900/50', text: 'text-yellow-400' },
  validated: { bg: 'bg-green-900/50', text: 'text-green-400' },
  resolved: { bg: 'bg-blue-900/50', text: 'text-blue-400' },
  false_positive: { bg: 'bg-gray-800/50', text: 'text-gray-400' },
};

// Finding status labels
export const findingStatusLabels: Record<FindingStatus, string> = {
  open: 'Offen',
  in_review: 'In Prüfung',
  validated: 'Validiert',
  resolved: 'Behoben',
  false_positive: 'Falsch Positiv',
};

// Agent status colors
export const agentStatusColors: Record<AgentStatus, string> = {
  idle: 'text-green-400',
  busy: 'text-yellow-400',
  offline: 'text-gray-400',
  error: 'text-red-400',
};

// Agent status labels
export const agentStatusLabels: Record<AgentStatus, string> = {
  idle: 'Bereit',
  busy: 'Beschäftigt',
  offline: 'Offline',
  error: 'Fehler',
};

// Scan status colors
export const scanStatusColors: Record<ScanStatus, { bg: string; text: string; icon: string }> = {
  pending: { bg: 'bg-gray-800/50', text: 'text-gray-400', icon: '⏳' },
  running: { bg: 'bg-blue-900/50', text: 'text-blue-400', icon: '▶️' },
  paused: { bg: 'bg-yellow-900/50', text: 'text-yellow-400', icon: '⏸️' },
  completed: { bg: 'bg-green-900/50', text: 'text-green-400', icon: '✅' },
  failed: { bg: 'bg-red-900/50', text: 'text-red-400', icon: '❌' },
  cancelled: { bg: 'bg-orange-900/50', text: 'text-orange-400', icon: '🚫' },
};

// Scan status labels
export const scanStatusLabels: Record<ScanStatus, string> = {
  pending: 'Ausstehend',
  running: 'Läuft',
  paused: 'Pausiert',
  completed: 'Abgeschlossen',
  failed: 'Fehlgeschlagen',
  cancelled: 'Abgebrochen',
};

// Format date
export const formatDate = (dateString: string, options?: Intl.DateTimeFormatOptions): string => {
  const date = new Date(dateString);
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options,
  };
  return date.toLocaleDateString('de-DE', defaultOptions);
};

// Format relative time
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'Gerade eben';
  if (diffMins < 60) return `Vor ${diffMins} Min.`;
  if (diffHours < 24) return `Vor ${diffHours} Std.`;
  if (diffDays < 7) return `Vor ${diffDays} Tagen`;
  return formatDate(dateString);
};

// Format duration
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
};

// Format bytes
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

// Format number with separators
export const formatNumber = (num: number): string => {
  return num.toLocaleString('de-DE');
};

// Truncate text
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
};

// Get severity order for sorting
export const severityOrder: Record<SeverityLevel, number> = {
  critical: 5,
  high: 4,
  medium: 3,
  low: 2,
  info: 1,
};

// Compare severities
export const compareSeverity = (a: SeverityLevel, b: SeverityLevel): number => {
  return severityOrder[b] - severityOrder[a];
};

// Get risk score color
export const getRiskScoreColor = (score: number): string => {
  if (score >= 9) return 'text-red-500';
  if (score >= 7) return 'text-orange-500';
  if (score >= 4) return 'text-yellow-500';
  if (score >= 1) return 'text-blue-500';
  return 'text-gray-500';
};

// Get risk score background
export const getRiskScoreBg = (score: number): string => {
  if (score >= 9) return 'bg-red-500';
  if (score >= 7) return 'bg-orange-500';
  if (score >= 4) return 'bg-yellow-500';
  if (score >= 1) return 'bg-blue-500';
  return 'bg-gray-500';
};
