/**
 * Zustand Store for Zen-AI-Pentest Frontend
 * Centralized state management using Zustand
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

import {
  AuthState,
  DashboardStats,
  FilterParams,
  Notification,
  Scan,
  SortParams,
  User,
  UserSettings,
  Vulnerability,
} from '@/types';

// ============================================
// Auth Store
// ============================================
interface AuthStore extends AuthState {
  login: (user: User, token: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      immer((set) => ({
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: true,

        login: (user, token, refreshToken) =>
          set((state) => {
            state.user = user;
            state.token = token;
            state.refreshToken = refreshToken;
            state.isAuthenticated = true;
            state.isLoading = false;
          }),

        logout: () =>
          set((state) => {
            state.user = null;
            state.token = null;
            state.refreshToken = null;
            state.isAuthenticated = false;
            state.isLoading = false;
          }),

        updateUser: (userData) =>
          set((state) => {
            if (state.user) {
              state.user = { ...state.user, ...userData };
            }
          }),

        setLoading: (isLoading) =>
          set((state) => {
            state.isLoading = isLoading;
          }),
      })),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          token: state.token,
          refreshToken: state.refreshToken,
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
);

// ============================================
// Dashboard Store
// ============================================
interface DashboardStore {
  stats: DashboardStats | null;
  isLoading: boolean;
  error: string | null;
  selectedTimeRange: string;
  setStats: (stats: DashboardStats) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setTimeRange: (range: string) => void;
  updateStats: (updates: Partial<DashboardStats>) => void;
}

export const useDashboardStore = create<DashboardStore>()(
  devtools(
    immer((set) => ({
      stats: null,
      isLoading: false,
      error: null,
      selectedTimeRange: '7d',

      setStats: (stats) =>
        set((state) => {
          state.stats = stats;
        }),

      setLoading: (isLoading) =>
        set((state) => {
          state.isLoading = isLoading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),

      setTimeRange: (range) =>
        set((state) => {
          state.selectedTimeRange = range;
        }),

      updateStats: (updates) =>
        set((state) => {
          if (state.stats) {
            Object.assign(state.stats, updates);
          }
        }),
    })),
    { name: 'DashboardStore' }
  )
);

// ============================================
// Scans Store
// ============================================
interface ScansStore {
  scans: Scan[];
  selectedScan: Scan | null;
  isLoading: boolean;
  error: string | null;
  filters: FilterParams;
  sort: SortParams;
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
  setScans: (scans: Scan[]) => void;
  addScan: (scan: Scan) => void;
  updateScan: (id: string, updates: Partial<Scan>) => void;
  removeScan: (id: string) => void;
  selectScan: (scan: Scan | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: FilterParams) => void;
  setSort: (sort: SortParams) => void;
  setPagination: (pagination: { page: number; limit: number; total: number }) => void;
  updateScanProgress: (scanId: string, progress: number, status: string) => void;
}

export const useScansStore = create<ScansStore>()(
  devtools(
    immer((set) => ({
      scans: [],
      selectedScan: null,
      isLoading: false,
      error: null,
      filters: {},
      sort: { field: 'createdAt', order: 'desc' },
      pagination: {
        page: 1,
        limit: 10,
        total: 0,
      },

      setScans: (scans) =>
        set((state) => {
          state.scans = scans;
        }),

      addScan: (scan) =>
        set((state) => {
          state.scans.unshift(scan);
        }),

      updateScan: (id, updates) =>
        set((state) => {
          const scan = state.scans.find((s) => s.id === id);
          if (scan) {
            Object.assign(scan, updates);
          }
          if (state.selectedScan?.id === id) {
            Object.assign(state.selectedScan, updates);
          }
        }),

      removeScan: (id) =>
        set((state) => {
          state.scans = state.scans.filter((s) => s.id !== id);
          if (state.selectedScan?.id === id) {
            state.selectedScan = null;
          }
        }),

      selectScan: (scan) =>
        set((state) => {
          state.selectedScan = scan;
        }),

      setLoading: (isLoading) =>
        set((state) => {
          state.isLoading = isLoading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),

      setFilters: (filters) =>
        set((state) => {
          state.filters = filters;
        }),

      setSort: (sort) =>
        set((state) => {
          state.sort = sort;
        }),

      setPagination: (pagination) =>
        set((state) => {
          state.pagination = pagination;
        }),

      updateScanProgress: (scanId, progress, status) =>
        set((state) => {
          const scan = state.scans.find((s) => s.id === scanId);
          if (scan) {
            scan.progress = progress;
            scan.status = status as Scan['status'];
          }
          if (state.selectedScan?.id === scanId) {
            state.selectedScan.progress = progress;
            state.selectedScan.status = status as Scan['status'];
          }
        }),
    })),
    { name: 'ScansStore' }
  )
);

// ============================================
// Vulnerabilities Store
// ============================================
interface VulnerabilitiesStore {
  vulnerabilities: Vulnerability[];
  selectedVulnerability: Vulnerability | null;
  isLoading: boolean;
  error: string | null;
  filters: FilterParams;
  sort: SortParams;
  severityCounts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  setVulnerabilities: (vulnerabilities: Vulnerability[]) => void;
  addVulnerability: (vulnerability: Vulnerability) => void;
  updateVulnerability: (id: string, updates: Partial<Vulnerability>) => void;
  removeVulnerability: (id: string) => void;
  selectVulnerability: (vulnerability: Vulnerability | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: FilterParams) => void;
  setSort: (sort: SortParams) => void;
  setSeverityCounts: (counts: { critical: number; high: number; medium: number; low: number; info: number }) => void;
}

export const useVulnerabilitiesStore = create<VulnerabilitiesStore>()(
  devtools(
    immer((set) => ({
      vulnerabilities: [],
      selectedVulnerability: null,
      isLoading: false,
      error: null,
      filters: {},
      sort: { field: 'createdAt', order: 'desc' },
      severityCounts: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        info: 0,
      },

      setVulnerabilities: (vulnerabilities) =>
        set((state) => {
          state.vulnerabilities = vulnerabilities;
        }),

      addVulnerability: (vulnerability) =>
        set((state) => {
          state.vulnerabilities.unshift(vulnerability);
          state.severityCounts[vulnerability.severity]++;
        }),

      updateVulnerability: (id, updates) =>
        set((state) => {
          const vuln = state.vulnerabilities.find((v) => v.id === id);
          if (vuln) {
            Object.assign(vuln, updates);
          }
          if (state.selectedVulnerability?.id === id) {
            Object.assign(state.selectedVulnerability, updates);
          }
        }),

      removeVulnerability: (id) =>
        set((state) => {
          const vuln = state.vulnerabilities.find((v) => v.id === id);
          if (vuln) {
            state.severityCounts[vuln.severity]--;
          }
          state.vulnerabilities = state.vulnerabilities.filter((v) => v.id !== id);
          if (state.selectedVulnerability?.id === id) {
            state.selectedVulnerability = null;
          }
        }),

      selectVulnerability: (vulnerability) =>
        set((state) => {
          state.selectedVulnerability = vulnerability;
        }),

      setLoading: (isLoading) =>
        set((state) => {
          state.isLoading = isLoading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),

      setFilters: (filters) =>
        set((state) => {
          state.filters = filters;
        }),

      setSort: (sort) =>
        set((state) => {
          state.sort = sort;
        }),

      setSeverityCounts: (counts) =>
        set((state) => {
          state.severityCounts = counts;
        }),
    })),
    { name: 'VulnerabilitiesStore' }
  )
);

// ============================================
// UI Store
// ============================================
interface UIStore {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  globalSearchOpen: boolean;
  scanWizardOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  addNotification: (notification: Notification) => void;
  markNotificationAsRead: (id: string) => void;
  markAllNotificationsAsRead: () => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  setGlobalSearchOpen: (open: boolean) => void;
  setScanWizardOpen: (open: boolean) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      immer((set) => ({
        sidebarOpen: true,
        theme: 'system',
        notifications: [],
        unreadCount: 0,
        isLoading: false,
        globalSearchOpen: false,
        scanWizardOpen: false,

        toggleSidebar: () =>
          set((state) => {
            state.sidebarOpen = !state.sidebarOpen;
          }),

        setSidebarOpen: (open) =>
          set((state) => {
            state.sidebarOpen = open;
          }),

        setTheme: (theme) =>
          set((state) => {
            state.theme = theme;
          }),

        addNotification: (notification) =>
          set((state) => {
            state.notifications.unshift(notification);
            if (!notification.isRead) {
              state.unreadCount++;
            }
          }),

        markNotificationAsRead: (id) =>
          set((state) => {
            const notification = state.notifications.find((n) => n.id === id);
            if (notification && !notification.isRead) {
              notification.isRead = true;
              state.unreadCount--;
            }
          }),

        markAllNotificationsAsRead: () =>
          set((state) => {
            state.notifications.forEach((n) => {
              n.isRead = true;
            });
            state.unreadCount = 0;
          }),

        removeNotification: (id) =>
          set((state) => {
            const notification = state.notifications.find((n) => n.id === id);
            if (notification && !notification.isRead) {
              state.unreadCount--;
            }
            state.notifications = state.notifications.filter((n) => n.id !== id);
          }),

        clearNotifications: () =>
          set((state) => {
            state.notifications = [];
            state.unreadCount = 0;
          }),

        setGlobalSearchOpen: (open) =>
          set((state) => {
            state.globalSearchOpen = open;
          }),

        setScanWizardOpen: (open) =>
          set((state) => {
            state.scanWizardOpen = open;
          }),

        setLoading: (isLoading) =>
          set((state) => {
            state.isLoading = isLoading;
          }),
      })),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          sidebarOpen: state.sidebarOpen,
          theme: state.theme,
        }),
      }
    ),
    { name: 'UIStore' }
  )
);

// ============================================
// Settings Store
// ============================================
interface SettingsStore {
  settings: UserSettings;
  isLoading: boolean;
  error: string | null;
  updateSettings: (settings: Partial<UserSettings>) => void;
  updateNotificationSettings: (settings: Partial<UserSettings['notifications']>) => void;
  updateDashboardSettings: (settings: Partial<UserSettings['dashboard']>) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  resetSettings: () => void;
}

const defaultSettings: UserSettings = {
  theme: 'system',
  language: 'en',
  timezone: 'UTC',
  dateFormat: 'YYYY-MM-DD',
  notifications: {
    email: true,
    push: true,
    slack: false,
    scanCompleted: true,
    vulnerabilityFound: true,
    criticalAlert: true,
  },
  dashboard: {
    defaultView: 'overview',
    widgets: ['stats', 'recentScans', 'vulnerabilities', 'trends'],
    refreshInterval: 30,
  },
};

export const useSettingsStore = create<SettingsStore>()(
  devtools(
    persist(
      immer((set) => ({
        settings: defaultSettings,
        isLoading: false,
        error: null,

        updateSettings: (newSettings) =>
          set((state) => {
            state.settings = { ...state.settings, ...newSettings };
          }),

        updateNotificationSettings: (notificationSettings) =>
          set((state) => {
            state.settings.notifications = {
              ...state.settings.notifications,
              ...notificationSettings,
            };
          }),

        updateDashboardSettings: (dashboardSettings) =>
          set((state) => {
            state.settings.dashboard = {
              ...state.settings.dashboard,
              ...dashboardSettings,
            };
          }),

        setLoading: (isLoading) =>
          set((state) => {
            state.isLoading = isLoading;
          }),

        setError: (error) =>
          set((state) => {
            state.error = error;
          }),

        resetSettings: () =>
          set((state) => {
            state.settings = defaultSettings;
          }),
      })),
      {
        name: 'settings-storage',
      }
    ),
    { name: 'SettingsStore' }
  )
);
