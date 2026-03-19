// ============================================
// Zen-AI-Pentest Platform - Zustand Store
// Neural Network State Management
// ============================================

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type {
  User,
  UserSettings,
  Scan,
  Vulnerability,
  Agent,
  Plugin,
  DashboardStats,
  Notification,
  SystemSettings,
  NetworkGraph,
  WebSocketMessage,
  SearchFilters,
  PaginationParams,
  ApiMeta,
  Severity,
  ScanStatus,
  AgentStatus,
  PluginStatus,
  VulnerabilityStatus,
} from '@/types';

// ============================================
// Auth Store
// ============================================
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  refreshToken: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setRefreshToken: (token: string | null) => void;
  login: (user: User, token: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  updateSettings: (settings: Partial<UserSettings>) => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      immer((set) => ({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        token: null,
        refreshToken: null,

        setUser: (user) =>
          set((state) => {
            state.user = user;
            state.isAuthenticated = !!user;
          }),

        setToken: (token) =>
          set((state) => {
            state.token = token;
          }),

        setRefreshToken: (token) =>
          set((state) => {
            state.refreshToken = token;
          }),

        login: (user, token, refreshToken) =>
          set((state) => {
            state.user = user;
            state.token = token;
            state.refreshToken = refreshToken;
            state.isAuthenticated = true;
          }),

        logout: () =>
          set((state) => {
            state.user = null;
            state.token = null;
            state.refreshToken = null;
            state.isAuthenticated = false;
          }),

        updateUser: (updates) =>
          set((state) => {
            if (state.user) {
              Object.assign(state.user, updates);
            }
          }),

        updateSettings: (settings) =>
          set((state) => {
            if (state.user) {
              Object.assign(state.user.settings, settings);
            }
          }),
      })),
      {
        name: 'zen-auth-storage',
        partialize: (state) => ({
          user: state.user,
          token: state.token,
          refreshToken: state.refreshToken,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
);

// ============================================
// Scan Store
// ============================================
interface ScanState {
  scans: Scan[];
  selectedScan: Scan | null;
  activeScans: string[];
  filters: SearchFilters;
  pagination: PaginationParams;
  meta: ApiMeta | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setScans: (scans: Scan[]) => void;
  addScan: (scan: Scan) => void;
  updateScan: (id: string, updates: Partial<Scan>) => void;
  removeScan: (id: string) => void;
  setSelectedScan: (scan: Scan | null) => void;
  setActiveScans: (ids: string[]) => void;
  addActiveScan: (id: string) => void;
  removeActiveScan: (id: string) => void;
  updateScanProgress: (id: string, progress: number) => void;
  updateScanStatus: (id: string, status: ScanStatus) => void;
  setFilters: (filters: SearchFilters) => void;
  setPagination: (pagination: Partial<PaginationParams>) => void;
  setMeta: (meta: ApiMeta | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useScanStore = create<ScanState>()(
  devtools(
    immer((set) => ({
      scans: [],
      selectedScan: null,
      activeScans: [],
      filters: {},
      pagination: { page: 1, limit: 20 },
      meta: null,
      isLoading: false,
      error: null,

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
        }),

      removeScan: (id) =>
        set((state) => {
          state.scans = state.scans.filter((s) => s.id !== id);
        }),

      setSelectedScan: (scan) =>
        set((state) => {
          state.selectedScan = scan;
        }),

      setActiveScans: (ids) =>
        set((state) => {
          state.activeScans = ids;
        }),

      addActiveScan: (id) =>
        set((state) => {
          if (!state.activeScans.includes(id)) {
            state.activeScans.push(id);
          }
        }),

      removeActiveScan: (id) =>
        set((state) => {
          state.activeScans = state.activeScans.filter((scanId) => scanId !== id);
        }),

      updateScanProgress: (id, progress) =>
        set((state) => {
          const scan = state.scans.find((s) => s.id === id);
          if (scan) {
            scan.progress = progress;
          }
        }),

      updateScanStatus: (id, status) =>
        set((state) => {
          const scan = state.scans.find((s) => s.id === id);
          if (scan) {
            scan.status = status;
          }
        }),

      setFilters: (filters) =>
        set((state) => {
          state.filters = { ...state.filters, ...filters };
        }),

      setPagination: (pagination) =>
        set((state) => {
          state.pagination = { ...state.pagination, ...pagination };
        }),

      setMeta: (meta) =>
        set((state) => {
          state.meta = meta;
        }),

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),
    })),
    { name: 'ScanStore' }
  )
);

// ============================================
// Vulnerability Store
// ============================================
interface VulnerabilityState {
  vulnerabilities: Vulnerability[];
  selectedVulnerability: Vulnerability | null;
  filters: SearchFilters;
  pagination: PaginationParams;
  meta: ApiMeta | null;
  isLoading: boolean;
  error: string | null;
  severityCounts: Record<Severity, number>;

  // Actions
  setVulnerabilities: (vulns: Vulnerability[]) => void;
  addVulnerability: (vuln: Vulnerability) => void;
  updateVulnerability: (id: string, updates: Partial<Vulnerability>) => void;
  removeVulnerability: (id: string) => void;
  setSelectedVulnerability: (vuln: Vulnerability | null) => void;
  updateStatus: (id: string, status: VulnerabilityStatus) => void;
  setFilters: (filters: SearchFilters) => void;
  setPagination: (pagination: Partial<PaginationParams>) => void;
  setMeta: (meta: ApiMeta | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  calculateSeverityCounts: () => void;
}

export const useVulnerabilityStore = create<VulnerabilityState>()(
  devtools(
    immer((set, get) => ({
      vulnerabilities: [],
      selectedVulnerability: null,
      filters: {},
      pagination: { page: 1, limit: 20 },
      meta: null,
      isLoading: false,
      error: null,
      severityCounts: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },

      setVulnerabilities: (vulns) =>
        set((state) => {
          state.vulnerabilities = vulns;
        }),

      addVulnerability: (vuln) =>
        set((state) => {
          state.vulnerabilities.unshift(vuln);
        }),

      updateVulnerability: (id, updates) =>
        set((state) => {
          const vuln = state.vulnerabilities.find((v) => v.id === id);
          if (vuln) {
            Object.assign(vuln, updates);
          }
        }),

      removeVulnerability: (id) =>
        set((state) => {
          state.vulnerabilities = state.vulnerabilities.filter((v) => v.id !== id);
        }),

      setSelectedVulnerability: (vuln) =>
        set((state) => {
          state.selectedVulnerability = vuln;
        }),

      updateStatus: (id, status) =>
        set((state) => {
          const vuln = state.vulnerabilities.find((v) => v.id === id);
          if (vuln) {
            vuln.status = status;
          }
        }),

      setFilters: (filters) =>
        set((state) => {
          state.filters = { ...state.filters, ...filters };
        }),

      setPagination: (pagination) =>
        set((state) => {
          state.pagination = { ...state.pagination, ...pagination };
        }),

      setMeta: (meta) =>
        set((state) => {
          state.meta = meta;
        }),

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),

      calculateSeverityCounts: () => {
        const { vulnerabilities } = get();
        const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
        vulnerabilities.forEach((v) => {
          counts[v.severity]++;
        });
        set((state) => {
          state.severityCounts = counts;
        });
      },
    })),
    { name: 'VulnerabilityStore' }
  )
);

// ============================================
// Dashboard Store
// ============================================
interface DashboardState {
  stats: DashboardStats | null;
  networkGraph: NetworkGraph;
  isLoading: boolean;
  error: string | null;
  realtimeUpdates: boolean;
  selectedTimeRange: string;

  // Actions
  setStats: (stats: DashboardStats | null) => void;
  updateStats: (updates: Partial<DashboardStats>) => void;
  setNetworkGraph: (graph: NetworkGraph) => void;
  addNetworkNode: (node: NetworkGraph['nodes'][0]) => void;
  addNetworkEdge: (edge: NetworkGraph['edges'][0]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setRealtimeUpdates: (enabled: boolean) => void;
  setSelectedTimeRange: (range: string) => void;
}

export const useDashboardStore = create<DashboardState>()(
  devtools(
    immer((set) => ({
      stats: null,
      networkGraph: { nodes: [], edges: [] },
      isLoading: false,
      error: null,
      realtimeUpdates: true,
      selectedTimeRange: '7d',

      setStats: (stats) =>
        set((state) => {
          state.stats = stats;
        }),

      updateStats: (updates) =>
        set((state) => {
          if (state.stats) {
            Object.assign(state.stats, updates);
          }
        }),

      setNetworkGraph: (graph) =>
        set((state) => {
          state.networkGraph = graph;
        }),

      addNetworkNode: (node) =>
        set((state) => {
          state.networkGraph.nodes.push(node);
        }),

      addNetworkEdge: (edge) =>
        set((state) => {
          state.networkGraph.edges.push(edge);
        }),

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),

      setRealtimeUpdates: (enabled) =>
        set((state) => {
          state.realtimeUpdates = enabled;
        }),

      setSelectedTimeRange: (range) =>
        set((state) => {
          state.selectedTimeRange = range;
        }),
    })),
    { name: 'DashboardStore' }
  )
);

// ============================================
// Agent Store
// ============================================
interface AgentState {
  agents: Agent[];
  selectedAgent: Agent | null;
  filters: { status?: AgentStatus[]; type?: string[] };
  isLoading: boolean;
  error: string | null;

  // Actions
  setAgents: (agents: Agent[]) => void;
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  removeAgent: (id: string) => void;
  setSelectedAgent: (agent: Agent | null) => void;
  updateAgentStatus: (id: string, status: AgentStatus) => void;
  updateAgentMetrics: (id: string, metrics: Partial<Agent['metrics']>) => void;
  setFilters: (filters: { status?: AgentStatus[]; type?: string[] }) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAgentStore = create<AgentState>()(
  devtools(
    immer((set) => ({
      agents: [],
      selectedAgent: null,
      filters: {},
      isLoading: false,
      error: null,

      setAgents: (agents) =>
        set((state) => {
          state.agents = agents;
        }),

      addAgent: (agent) =>
        set((state) => {
          state.agents.push(agent);
        }),

      updateAgent: (id, updates) =>
        set((state) => {
          const agent = state.agents.find((a) => a.id === id);
          if (agent) {
            Object.assign(agent, updates);
          }
        }),

      removeAgent: (id) =>
        set((state) => {
          state.agents = state.agents.filter((a) => a.id !== id);
        }),

      setSelectedAgent: (agent) =>
        set((state) => {
          state.selectedAgent = agent;
        }),

      updateAgentStatus: (id, status) =>
        set((state) => {
          const agent = state.agents.find((a) => a.id === id);
          if (agent) {
            agent.status = status;
          }
        }),

      updateAgentMetrics: (id, metrics) =>
        set((state) => {
          const agent = state.agents.find((a) => a.id === id);
          if (agent && agent.metrics) {
            Object.assign(agent.metrics, metrics);
          }
        }),

      setFilters: (filters) =>
        set((state) => {
          state.filters = { ...state.filters, ...filters };
        }),

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),
    })),
    { name: 'AgentStore' }
  )
);

// ============================================
// Plugin Store
// ============================================
interface PluginState {
  plugins: Plugin[];
  selectedPlugin: Plugin | null;
  filters: { type?: string[]; status?: PluginStatus[] };
  isLoading: boolean;
  error: string | null;

  // Actions
  setPlugins: (plugins: Plugin[]) => void;
  addPlugin: (plugin: Plugin) => void;
  updatePlugin: (id: string, updates: Partial<Plugin>) => void;
  removePlugin: (id: string) => void;
  setSelectedPlugin: (plugin: Plugin | null) => void;
  togglePluginStatus: (id: string) => void;
  setFilters: (filters: { type?: string[]; status?: PluginStatus[] }) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const usePluginStore = create<PluginState>()(
  devtools(
    immer((set) => ({
      plugins: [],
      selectedPlugin: null,
      filters: {},
      isLoading: false,
      error: null,

      setPlugins: (plugins) =>
        set((state) => {
          state.plugins = plugins;
        }),

      addPlugin: (plugin) =>
        set((state) => {
          state.plugins.push(plugin);
        }),

      updatePlugin: (id, updates) =>
        set((state) => {
          const plugin = state.plugins.find((p) => p.id === id);
          if (plugin) {
            Object.assign(plugin, updates);
          }
        }),

      removePlugin: (id) =>
        set((state) => {
          state.plugins = state.plugins.filter((p) => p.id !== id);
        }),

      setSelectedPlugin: (plugin) =>
        set((state) => {
          state.selectedPlugin = plugin;
        }),

      togglePluginStatus: (id) =>
        set((state) => {
          const plugin = state.plugins.find((p) => p.id === id);
          if (plugin) {
            plugin.status = plugin.status === 'active' ? 'inactive' : 'active';
          }
        }),

      setFilters: (filters) =>
        set((state) => {
          state.filters = { ...state.filters, ...filters };
        }),

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),
    })),
    { name: 'PluginStore' }
  )
);

// ============================================
// Notification Store
// ============================================
interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;

  // Actions
  setNotifications: (notifications: Notification[]) => void;
  addNotification: (notification: Notification) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  setLoading: (loading: boolean) => void;
}

export const useNotificationStore = create<NotificationState>()(
  devtools(
    immer((set, get) => ({
      notifications: [],
      unreadCount: 0,
      isLoading: false,

      setNotifications: (notifications) =>
        set((state) => {
          state.notifications = notifications;
          state.unreadCount = notifications.filter((n) => !n.read).length;
        }),

      addNotification: (notification) =>
        set((state) => {
          state.notifications.unshift(notification);
          if (!notification.read) {
            state.unreadCount++;
          }
        }),

      markAsRead: (id) =>
        set((state) => {
          const notification = state.notifications.find((n) => n.id === id);
          if (notification && !notification.read) {
            notification.read = true;
            state.unreadCount--;
          }
        }),

      markAllAsRead: () =>
        set((state) => {
          state.notifications.forEach((n) => {
            n.read = true;
          });
          state.unreadCount = 0;
        }),

      removeNotification: (id) =>
        set((state) => {
          const notification = state.notifications.find((n) => n.id === id);
          if (notification && !notification.read) {
            state.unreadCount--;
          }
          state.notifications = state.notifications.filter((n) => n.id !== id);
        }),

      clearAll: () =>
        set((state) => {
          state.notifications = [];
          state.unreadCount = 0;
        }),

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),
    })),
    { name: 'NotificationStore' }
  )
);

// ============================================
// Settings Store
// ============================================
interface SettingsState {
  settings: SystemSettings | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setSettings: (settings: SystemSettings) => void;
  updateSettings: (updates: Partial<SystemSettings>) => void;
  updateGeneralSettings: (settings: Partial<SystemSettings['general']>) => void;
  updateSecuritySettings: (settings: Partial<SystemSettings['security']>) => void;
  updateScanningSettings: (settings: Partial<SystemSettings['scanning']>) => void;
  updateNotificationSettings: (settings: Partial<SystemSettings['notifications']>) => void;
  updateIntegrationSettings: (settings: Partial<SystemSettings['integrations']>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      immer((set) => ({
        settings: null,
        isLoading: false,
        error: null,

        setSettings: (settings) =>
          set((state) => {
            state.settings = settings;
          }),

        updateSettings: (updates) =>
          set((state) => {
            if (state.settings) {
              Object.assign(state.settings, updates);
            }
          }),

        updateGeneralSettings: (settings) =>
          set((state) => {
            if (state.settings) {
              Object.assign(state.settings.general, settings);
            }
          }),

        updateSecuritySettings: (settings) =>
          set((state) => {
            if (state.settings) {
              Object.assign(state.settings.security, settings);
            }
          }),

        updateScanningSettings: (settings) =>
          set((state) => {
            if (state.settings) {
              Object.assign(state.settings.scanning, settings);
            }
          }),

        updateNotificationSettings: (settings) =>
          set((state) => {
            if (state.settings) {
              Object.assign(state.settings.notifications, settings);
            }
          }),

        updateIntegrationSettings: (settings) =>
          set((state) => {
            if (state.settings) {
              Object.assign(state.settings.integrations, settings);
            }
          }),

        setLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),

        setError: (error) =>
          set((state) => {
            state.error = error;
          }),
      })),
      {
        name: 'zen-settings-storage',
        partialize: (state) => ({ settings: state.settings }),
      }
    ),
    { name: 'SettingsStore' }
  )
);

// ============================================
// WebSocket Store
// ============================================
interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  lastMessage: WebSocketMessage | null;
  messages: WebSocketMessage[];
  reconnectAttempts: number;

  // Actions
  setConnected: (connected: boolean) => void;
  setConnecting: (connecting: boolean) => void;
  addMessage: (message: WebSocketMessage) => void;
  clearMessages: () => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

export const useWebSocketStore = create<WebSocketState>()(
  devtools(
    immer((set) => ({
      isConnected: false,
      isConnecting: false,
      lastMessage: null,
      messages: [],
      reconnectAttempts: 0,

      setConnected: (connected) =>
        set((state) => {
          state.isConnected = connected;
        }),

      setConnecting: (connecting) =>
        set((state) => {
          state.isConnecting = connecting;
        }),

      addMessage: (message) =>
        set((state) => {
          state.messages.push(message);
          state.lastMessage = message;
        }),

      clearMessages: () =>
        set((state) => {
          state.messages = [];
          state.lastMessage = null;
        }),

      incrementReconnectAttempts: () =>
        set((state) => {
          state.reconnectAttempts++;
        }),

      resetReconnectAttempts: () =>
        set((state) => {
          state.reconnectAttempts = 0;
        }),
    })),
    { name: 'WebSocketStore' }
  )
);

// ============================================
// UI Store (Theme, Sidebar, etc.)
// ============================================
interface UIState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  activeModal: string | null;
  modalData: any;
  breadcrumbs: { label: string; href?: string }[];

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  openModal: (modal: string, data?: any) => void;
  closeModal: () => void;
  setBreadcrumbs: (breadcrumbs: { label: string; href?: string }[]) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      immer((set) => ({
        sidebarOpen: true,
        sidebarCollapsed: false,
        theme: 'system',
        activeModal: null,
        modalData: null,
        breadcrumbs: [],

        toggleSidebar: () =>
          set((state) => {
            state.sidebarOpen = !state.sidebarOpen;
          }),

        setSidebarOpen: (open) =>
          set((state) => {
            state.sidebarOpen = open;
          }),

        setSidebarCollapsed: (collapsed) =>
          set((state) => {
            state.sidebarCollapsed = collapsed;
          }),

        setTheme: (theme) =>
          set((state) => {
            state.theme = theme;
          }),

        openModal: (modal, data) =>
          set((state) => {
            state.activeModal = modal;
            state.modalData = data;
          }),

        closeModal: () =>
          set((state) => {
            state.activeModal = null;
            state.modalData = null;
          }),

        setBreadcrumbs: (breadcrumbs) =>
          set((state) => {
            state.breadcrumbs = breadcrumbs;
          }),
      })),
      {
        name: 'zen-ui-storage',
        partialize: (state) => ({
          sidebarCollapsed: state.sidebarCollapsed,
          theme: state.theme,
        }),
      }
    ),
    { name: 'UIStore' }
  )
);
