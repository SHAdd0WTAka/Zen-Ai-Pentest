/**
 * WebSocket Hook für Echtzeit-Updates
 */
import { useEffect, useRef, useState, useCallback } from 'react';

export function useWebSocket(clientId) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  const heartbeatInterval = useRef(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `ws://${window.location.hostname}:8000/ws/${clientId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket Connected');
      setConnected(true);
      
      // Start heartbeat
      heartbeatInterval.current = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
      setMessages(prev => [...prev, message]);
    };

    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
      setConnected(false);
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
      }
      
      // Auto-reconnect nach 3 Sekunden
      setTimeout(connect, 3000);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
  }, [clientId]);

  const disconnect = useCallback(() => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
    }
    if (ws.current) {
      ws.current.close();
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  const subscribe = useCallback((channel) => {
    sendMessage({ type: 'subscribe', channel });
  }, [sendMessage]);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { 
    connected, 
    messages, 
    lastMessage,
    sendMessage,
    subscribe
  };
}
