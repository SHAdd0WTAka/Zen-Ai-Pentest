/**
 * WebSocket Hook for Zen-AI-Pentest
 * Manages WebSocket connection and real-time updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/store';

interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp?: string;
}

interface UseWebSocketOptions {
  onScanUpdate?: (payload: any) => void;
  onVulnerabilityFound?: (payload: any) => void;
  onScanCompleted?: (payload: any) => void;
  onAgentStatus?: (payload: any) => void;
  onNotification?: (payload: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const token = useAuthStore((state) => state.token);

  const connect = useCallback(() => {
    if (!token || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);

    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;

        // Send authentication
        ws.send(JSON.stringify({
          type: 'auth',
          token: token
        }));

        options.onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'connection_established':
              console.log('WebSocket authenticated:', message.payload);
              break;

            case 'scan_update':
              options.onScanUpdate?.(message.payload);
              break;

            case 'vulnerability_found':
              options.onVulnerabilityFound?.(message.payload);
              break;

            case 'scan_completed':
              options.onScanCompleted?.(message.payload);
              break;

            case 'agent_status':
              options.onAgentStatus?.(message.payload);
              break;

            case 'notification':
              options.onNotification?.(message.payload);
              break;

            case 'pong':
              // Heartbeat response
              break;

            case 'error':
              console.error('WebSocket error:', message.payload);
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        wsRef.current = null;

        options.onDisconnect?.();

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);

          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        options.onError?.(error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setIsConnecting(false);
    }
  }, [token, options]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback((type: string, payload?: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type,
        payload,
        timestamp: new Date().toISOString()
      }));
      return true;
    }
    return false;
  }, []);

  const subscribeToScan = useCallback((scanId: string) => {
    return sendMessage('subscribe_scan', { scanId });
  }, [sendMessage]);

  const unsubscribeFromScan = useCallback((scanId: string) => {
    return sendMessage('unsubscribe_scan', { scanId });
  }, [sendMessage]);

  const ping = useCallback(() => {
    return sendMessage('ping', { timestamp: Date.now() });
  }, [sendMessage]);

  // Connect on mount
  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [token, connect, disconnect]);

  // Heartbeat
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      ping();
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(interval);
  }, [isConnected, ping]);

  return {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    sendMessage,
    subscribeToScan,
    unsubscribeFromScan,
    ping,
  };
};

export default useWebSocket;
