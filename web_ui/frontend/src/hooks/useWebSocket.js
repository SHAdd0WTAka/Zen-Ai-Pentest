/**
 * WebSocket Hook for Real-time Updates
 * Q2 2026 Feature
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE = `ws://${window.location.host}`;

export function useWebSocket(room = 'dashboard') {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);

  const connect = useCallback(() => {
    const wsUrl = `${WS_BASE}/ws/v2/${room}`;
    
    try {
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        console.log(`WebSocket connected to ${room}`);
        setConnected(true);
        
        // Send ping every 30s
        ws.current.pingInterval = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ action: 'ping' }));
          }
        }, 30000);
      };
      
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      };
      
      ws.current.onclose = () => {
        console.log(`WebSocket disconnected from ${room}`);
        setConnected(false);
        clearInterval(ws.current?.pingInterval);
        
        // Reconnect after 5s
        reconnectTimeout.current = setTimeout(connect, 5000);
      };
      
      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [room]);

  useEffect(() => {
    connect();
    
    return () => {
      clearTimeout(reconnectTimeout.current);
      clearInterval(ws.current?.pingInterval);
      ws.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  }, []);

  return { connected, lastMessage, sendMessage };
}

export function useScanUpdates(scanId) {
  const { connected, lastMessage, sendMessage } = useWebSocket('scans');
  
  useEffect(() => {
    if (scanId && connected) {
      sendMessage({ action: 'subscribe_scan', scan_id: scanId });
    }
  }, [scanId, connected, sendMessage]);
  
  return { connected, lastMessage };
}
