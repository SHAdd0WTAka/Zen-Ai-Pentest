// ============================================
// Zen-AI-Pentest Platform - Main Application
// Neural Network Architecture
// ============================================

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from '@/components/ui/sonner';
import { ThemeProvider } from '@/components/theme-provider';

// Layouts
import { MainLayout } from '@/layouts/MainLayout';
import { AuthLayout } from '@/layouts/AuthLayout';

// Pages
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { ScansPage } from '@/pages/scans/ScansPage';
import { ScanDetailPage } from '@/pages/scans/ScanDetailPage';
import { NewScanPage } from '@/pages/scans/NewScanPage';
import { VulnerabilitiesPage } from '@/pages/vulnerabilities/VulnerabilitiesPage';
import { VulnerabilityDetailPage } from '@/pages/vulnerabilities/VulnerabilityDetailPage';
import { ReportsPage } from '@/pages/reports/ReportsPage';
import { ReportDetailPage } from '@/pages/reports/ReportDetailPage';
import { AgentsPage } from '@/pages/agents/AgentsPage';
import { AgentDetailPage } from '@/pages/agents/AgentDetailPage';
import { PluginsPage } from '@/pages/plugins/PluginsPage';
import { PluginDetailPage } from '@/pages/plugins/PluginDetailPage';
import { CompliancePage } from '@/pages/compliance/CompliancePage';
import { MCPPage } from '@/pages/mcp/MCPPage';
import { TwitchTunnelPage } from '@/pages/twitch/TwitchTunnelPage';
import { SettingsPage } from '@/pages/settings/SettingsPage';
import { ProfilePage } from '@/pages/profile/ProfilePage';
import { NetworkGraphPage } from '@/pages/network/NetworkGraphPage';
import { AIAnalysisPage } from '@/pages/ai/AIAnalysisPage';
import { NotificationsPage } from '@/pages/notifications/NotificationsPage';

// Hooks
import { useAuthStore } from '@/store';
import { useWebSocket } from '@/services/websocket';

// Styles
import './App.css';

// ============================================
// Query Client Configuration
// ============================================
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

// ============================================
// Protected Route Component
// ============================================
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// ============================================
// WebSocket Connection Manager
// ============================================
function WebSocketManager() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { connect, disconnect } = useWebSocket();

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, connect, disconnect]);

  return null;
}

// ============================================
// Main App Component
// ============================================
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="zen-theme">
        <BrowserRouter>
          <WebSocketManager />
          <Routes>
            {/* Auth Routes */}
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            {/* Protected Routes */}
            <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
              {/* Dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* Scans */}
              <Route path="/scans" element={<ScansPage />} />
              <Route path="/scans/new" element={<NewScanPage />} />
              <Route path="/scans/:id" element={<ScanDetailPage />} />

              {/* Vulnerabilities */}
              <Route path="/vulnerabilities" element={<VulnerabilitiesPage />} />
              <Route path="/vulnerabilities/:id" element={<VulnerabilityDetailPage />} />

              {/* Reports */}
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/reports/:id" element={<ReportDetailPage />} />

              {/* Agents */}
              <Route path="/agents" element={<AgentsPage />} />
              <Route path="/agents/:id" element={<AgentDetailPage />} />

              {/* Plugins */}
              <Route path="/plugins" element={<PluginsPage />} />
              <Route path="/plugins/:id" element={<PluginDetailPage />} />

              {/* Compliance */}
              <Route path="/compliance" element={<CompliancePage />} />

              {/* MCP */}
              <Route path="/mcp" element={<MCPPage />} />

              {/* Twitch Tunnel */}
              <Route path="/twitch-tunnel" element={<TwitchTunnelPage />} />

              {/* Network Graph */}
              <Route path="/network" element={<NetworkGraphPage />} />

              {/* AI Analysis */}
              <Route path="/ai-analysis" element={<AIAnalysisPage />} />

              {/* Notifications */}
              <Route path="/notifications" element={<NotificationsPage />} />

              {/* Settings */}
              <Route path="/settings" element={<SettingsPage />} />

              {/* Profile */}
              <Route path="/profile" element={<ProfilePage />} />
            </Route>

            {/* 404 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
        <ReactQueryDevtools initialIsOpen={false} />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
