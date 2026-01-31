import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export function useWebSocket(scanId) {
  const [isConnected, setIsConnected] = useState(false);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  const wsRef = useRef(null);

  useEffect(() => {
    if (!scanId) return;

    const token = localStorage.getItem('token');
    const wsUrl = `${WS_BASE_URL}/ws/scans/${scanId}?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'log':
          setLogs((prev) => [...prev, {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            level: data.level || 'info',
            message: data.message,
          }]);
          break;
        case 'progress':
          setProgress(data.progress);
          break;
        case 'status':
          setStatus(data.status);
          break;
        case 'finding':
          // New finding discovered
          break;
        default:
          console.log('WebSocket message:', data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [scanId]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return {
    isConnected,
    logs,
    progress,
    status,
    sendMessage,
    clearLogs,
  };
}

export function useGlobalWebSocket() {
  const [notifications, setNotifications] = useState([]);
  const [systemStatus, setSystemStatus] = useState({});
  const wsRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const wsUrl = `${WS_BASE_URL}/ws/notifications?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'notification':
          setNotifications((prev) => [data, ...prev].slice(0, 50));
          break;
        case 'system_status':
          setSystemStatus(data.status);
          break;
        default:
          break;
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const dismissNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    systemStatus,
    dismissNotification,
    clearAllNotifications,
  };
}
