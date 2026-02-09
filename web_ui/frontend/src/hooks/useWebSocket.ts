// ============================================
// WebSocket Hooks
// ============================================

import { useEffect, useRef, useCallback, useState } from 'react';
import { wsService } from '../services/api';
import { WebSocketMessage } from '../types';

// Hook for WebSocket connection
export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token') || undefined;
    wsService.connect(token);

    // Connection status check
    const checkConnection = setInterval(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ws = (wsService as any).ws;
      setIsConnected(ws?.readyState === WebSocket.OPEN);
    }, 1000);

    return () => {
      clearInterval(checkConnection);
    };
  }, []);

  return { isConnected };
};

// Hook for subscribing to specific message types
export const useWebSocketSubscription = <T = unknown>(
  messageType: string,
  callback: (data: T) => void
) => {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const unsubscribe = wsService.subscribe(messageType, (data) => {
      callbackRef.current(data as T);
    });

    return () => {
      unsubscribe();
    };
  }, [messageType]);
};

// Hook for scan updates
export const useScanUpdates = (scanId: string, callback: (update: unknown) => void) => {
  useWebSocketSubscription(
    'scan_update',
    useCallback(
      (data: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if ((data as any)?.scanId === scanId) {
          callback(data);
        }
      },
      [scanId, callback]
    )
  );
};

// Hook for real-time findings
export const useFindingUpdates = (callback: (finding: unknown) => void) => {
  useWebSocketSubscription('finding_update', callback);
};

// Hook for agent status updates
export const useAgentUpdates = (callback: (agent: unknown) => void) => {
  useWebSocketSubscription('agent_update', callback);
};

// Hook for alerts
export const useAlertUpdates = (callback: (alert: unknown) => void) => {
  useWebSocketSubscription('alert', callback);
};

// Hook for sending messages
export const useWebSocketSender = () => {
  return useCallback((type: string, payload: unknown) => {
    wsService.send(type, payload);
  }, []);
};

// Combined hook for all real-time updates
export const useRealTimeUpdates = () => {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useWebSocketSubscription('scan_update', (data) => {
    setLastMessage({
      type: 'scan_update',
      payload: data,
      timestamp: new Date().toISOString(),
    });
  });

  useWebSocketSubscription('finding_update', (data) => {
    setLastMessage({
      type: 'finding_update',
      payload: data,
      timestamp: new Date().toISOString(),
    });
  });

  useWebSocketSubscription('agent_update', (data) => {
    setLastMessage({
      type: 'agent_update',
      payload: data,
      timestamp: new Date().toISOString(),
    });
  });

  useWebSocketSubscription('alert', (data) => {
    setLastMessage({
      type: 'alert',
      payload: data,
      timestamp: new Date().toISOString(),
    });
  });

  return { lastMessage };
};
