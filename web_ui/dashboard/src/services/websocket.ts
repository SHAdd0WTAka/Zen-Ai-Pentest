// ============================================
// Zen-AI-Pentest Platform - WebSocket Service
// Real-time Communication
// ============================================

import { io, Socket } from 'socket.io-client';
import { useWebSocketStore, useScanStore, useVulnerabilityStore, useAgentStore, useNotificationStore } from '@/store';
import type { WebSocketMessage, Scan, Vulnerability, Agent, Notification } from '@/types';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelay = 3000;

  // ============================================
  // Connection Management
  // ============================================
  connect(token?: string): void {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    const wsStore = useWebSocketStore.getState();
    wsStore.setConnecting(true);

    this.socket = io(WS_BASE_URL, {
      transports: ['websocket'],
      auth: {
        token: token || localStorage.getItem('access_token'),
      },
      reconnection: false, // We handle reconnection manually
    });

    this.setupEventHandlers();
    this.startPingInterval();
  }

  disconnect(): void {
    this.stopPingInterval();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

    const wsStore = useWebSocketStore.getState();
    wsStore.setConnected(false);
    wsStore.setConnecting(false);
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', this.handleConnect.bind(this));
    this.socket.on('disconnect', this.handleDisconnect.bind(this));
    this.socket.on('connect_error', this.handleConnectError.bind(this));

    // Application events
    this.socket.on('scan_update', this.handleScanUpdate.bind(this));
    this.socket.on('scan_complete', this.handleScanComplete.bind(this));
    this.socket.on('scan_started', this.handleScanStarted.bind(this));
    this.socket.on('scan_stopped', this.handleScanStopped.bind(this));
    this.socket.on('scan_error', this.handleScanError.bind(this));

    this.socket.on('vulnerability_found', this.handleVulnerabilityFound.bind(this));
    this.socket.on('vulnerability_updated', this.handleVulnerabilityUpdated.bind(this));

    this.socket.on('agent_status', this.handleAgentStatus.bind(this));
    this.socket.on('agent_metrics', this.handleAgentMetrics.bind(this));

    this.socket.on('notification', this.handleNotification.bind(this));
    this.socket.on('system_status', this.handleSystemStatus.bind(this));

    // Response to subscriptions
    this.socket.on('subscribed', (data) => {
      console.log('Subscribed to:', data.channel);
    });

    this.socket.on('unsubscribed', (data) => {
      console.log('Unsubscribed from:', data.channel);
    });
  }

  // ============================================
  // Event Handlers
  // ============================================
  private handleConnect(): void {
    console.log('WebSocket connected');
    const wsStore = useWebSocketStore.getState();
    wsStore.setConnected(true);
    wsStore.setConnecting(false);
    wsStore.resetReconnectAttempts();

    // Subscribe to default channels
    this.subscribe('scans');
    this.subscribe('vulnerabilities');
    this.subscribe('agents');
    this.subscribe('notifications');
  }

  private handleDisconnect(reason: string): void {
    console.log('WebSocket disconnected:', reason);
    const wsStore = useWebSocketStore.getState();
    wsStore.setConnected(false);
    wsStore.setConnecting(false);

    // Attempt reconnection if not manually disconnected
    if (reason !== 'io client disconnect') {
      this.attemptReconnect();
    }
  }

  private handleConnectError(error: Error): void {
    console.error('WebSocket connection error:', error);
    const wsStore = useWebSocketStore.getState();
    wsStore.setConnecting(false);
    wsStore.incrementReconnectAttempts();
    this.attemptReconnect();
  }

  private attemptReconnect(): void {
    const wsStore = useWebSocketStore.getState();

    if (wsStore.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    console.log(`Reconnecting... Attempt ${wsStore.reconnectAttempts + 1}/${this.maxReconnectAttempts}`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
  }

  // ============================================
  // Scan Event Handlers
  // ============================================
  private handleScanUpdate(data: { scan_id: string; progress: number; status: string; message?: string }): void {
    console.log('Scan update:', data);

    const scanStore = useScanStore.getState();
    scanStore.updateScanProgress(data.scan_id, data.progress);
    scanStore.updateScanStatus(data.scan_id, data.status as any);

    const message: WebSocketMessage = {
      type: 'scan_update',
      payload: data,
      timestamp: new Date().toISOString(),
    };
    useWebSocketStore.getState().addMessage(message);
  }

  private handleScanComplete(data: { scan_id: string; scan: Scan; results: any }): void {
    console.log('Scan complete:', data.scan_id);

    const scanStore = useScanStore.getState();
    scanStore.updateScan(data.scan_id, {
      status: 'completed',
      progress: 100,
      completedAt: new Date().toISOString(),
      results: data.results,
    });
    scanStore.removeActiveScan(data.scan_id);

    const message: WebSocketMessage = {
      type: 'scan_complete',
      payload: data,
      timestamp: new Date().toISOString(),
    };
    useWebSocketStore.getState().addMessage(message);

    // Show notification
    useNotificationStore.getState().addNotification({
      id: `scan-complete-${data.scan_id}`,
      type: 'success',
      title: 'Scan Completed',
      message: `Scan "${data.scan.name}" has completed successfully`,
      read: false,
      createdAt: new Date().toISOString(),
      link: `/scans/${data.scan_id}`,
    });
  }

  private handleScanStarted(data: { scan_id: string; scan: Scan }): void {
    console.log('Scan started:', data.scan_id);

    const scanStore = useScanStore.getState();
    scanStore.updateScan(data.scan_id, {
      status: 'running',
      startedAt: new Date().toISOString(),
    });
    scanStore.addActiveScan(data.scan_id);
  }

  private handleScanStopped(data: { scan_id: string; reason: string }): void {
    console.log('Scan stopped:', data.scan_id);

    const scanStore = useScanStore.getState();
    scanStore.updateScan(data.scan_id, {
      status: 'cancelled',
    });
    scanStore.removeActiveScan(data.scan_id);
  }

  private handleScanError(data: { scan_id: string; error: string }): void {
    console.error('Scan error:', data);

    const scanStore = useScanStore.getState();
    scanStore.updateScan(data.scan_id, {
      status: 'failed',
    });
    scanStore.removeActiveScan(data.scan_id);

    useNotificationStore.getState().addNotification({
      id: `scan-error-${data.scan_id}`,
      type: 'error',
      title: 'Scan Failed',
      message: data.error,
      read: false,
      createdAt: new Date().toISOString(),
    });
  }

  // ============================================
  // Vulnerability Event Handlers
  // ============================================
  private handleVulnerabilityFound(data: { vulnerability: Vulnerability }): void {
    console.log('Vulnerability found:', data.vulnerability.id);

    const vulnStore = useVulnerabilityStore.getState();
    vulnStore.addVulnerability(data.vulnerability);
    vulnStore.calculateSeverityCounts();

    const message: WebSocketMessage = {
      type: 'vulnerability_found',
      payload: data,
      timestamp: new Date().toISOString(),
    };
    useWebSocketStore.getState().addMessage(message);

    // Show notification for critical/high vulnerabilities
    if (['critical', 'high'].includes(data.vulnerability.severity)) {
      useNotificationStore.getState().addNotification({
        id: `vuln-${data.vulnerability.id}`,
        type: data.vulnerability.severity === 'critical' ? 'error' : 'warning',
        title: `${data.vulnerability.severity.toUpperCase()} Vulnerability Detected`,
        message: data.vulnerability.name,
        read: false,
        createdAt: new Date().toISOString(),
        link: `/vulnerabilities/${data.vulnerability.id}`,
      });
    }
  }

  private handleVulnerabilityUpdated(data: { vulnerability_id: string; updates: Partial<Vulnerability> }): void {
    console.log('Vulnerability updated:', data.vulnerability_id);

    const vulnStore = useVulnerabilityStore.getState();
    vulnStore.updateVulnerability(data.vulnerability_id, data.updates);
  }

  // ============================================
  // Agent Event Handlers
  // ============================================
  private handleAgentStatus(data: { agent_id: string; status: Agent['status']; last_seen: string }): void {
    console.log('Agent status update:', data.agent_id, data.status);

    const agentStore = useAgentStore.getState();
    agentStore.updateAgent(data.agent_id, {
      status: data.status,
      lastSeen: data.last_seen,
    });

    if (data.status === 'offline' || data.status === 'error') {
      useNotificationStore.getState().addNotification({
        id: `agent-${data.agent_id}`,
        type: 'warning',
        title: 'Agent Status Alert',
        message: `Agent is now ${data.status}`,
        read: false,
        createdAt: new Date().toISOString(),
      });
    }
  }

  private handleAgentMetrics(data: { agent_id: string; metrics: Agent['metrics'] }): void {
    const agentStore = useAgentStore.getState();
    agentStore.updateAgentMetrics(data.agent_id, data.metrics);
  }

  // ============================================
  // Notification Handler
  // ============================================
  private handleNotification(data: Notification): void {
    console.log('Notification received:', data.id);
    useNotificationStore.getState().addNotification(data);
  }

  // ============================================
  // System Status Handler
  // ============================================
  private handleSystemStatus(data: { status: string; components: any[] }): void {
    console.log('System status:', data.status);

    const message: WebSocketMessage = {
      type: 'system_status',
      payload: data,
      timestamp: new Date().toISOString(),
    };
    useWebSocketStore.getState().addMessage(message);
  }

  // ============================================
  // Ping/Pong for Connection Health
  // ============================================
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping', { timestamp: Date.now() });
      }
    }, 30000);
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  // ============================================
  // Public Methods
  // ============================================
  subscribe(channel: string, params?: any): void {
    if (this.socket?.connected) {
      this.socket.emit('subscribe', { channel, params });
    }
  }

  unsubscribe(channel: string): void {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe', { channel });
    }
  }

  emit(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Scan control methods
  startScan(scanId: string): void {
    this.emit('scan:start', { scan_id: scanId });
  }

  stopScan(scanId: string): void {
    this.emit('scan:stop', { scan_id: scanId });
  }

  pauseScan(scanId: string): void {
    this.emit('scan:pause', { scan_id: scanId });
  }

  resumeScan(scanId: string): void {
    this.emit('scan:resume', { scan_id: scanId });
  }

  // Agent control methods
  restartAgent(agentId: string): void {
    this.emit('agent:restart', { agent_id: agentId });
  }

  updateAgent(agentId: string): void {
    this.emit('agent:update', { agent_id: agentId });
  }
}

// ============================================
// Singleton Instance
// ============================================
export const websocketService = new WebSocketService();

// ============================================
// React Hook for WebSocket
// ============================================
export function useWebSocket() {
  return {
    connect: (token?: string) => websocketService.connect(token),
    disconnect: () => websocketService.disconnect(),
    subscribe: (channel: string, params?: any) => websocketService.subscribe(channel, params),
    unsubscribe: (channel: string) => websocketService.unsubscribe(channel),
    emit: (event: string, data: any) => websocketService.emit(event, data),
    isConnected: () => websocketService.isConnected(),
    startScan: (scanId: string) => websocketService.startScan(scanId),
    stopScan: (scanId: string) => websocketService.stopScan(scanId),
    pauseScan: (scanId: string) => websocketService.pauseScan(scanId),
    resumeScan: (scanId: string) => websocketService.resumeScan(scanId),
    restartAgent: (agentId: string) => websocketService.restartAgent(agentId),
    updateAgent: (agentId: string) => websocketService.updateAgent(agentId),
  };
}

export default websocketService;
