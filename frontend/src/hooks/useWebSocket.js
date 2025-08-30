import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import { toast } from 'react-toastify';

export const useWebSocket = (url = 'http://localhost:8000') => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [botStatus, setBotStatus] = useState({
    status: 'stopped',
    balance: 10000,
    pnl: 0,
    positions: 0,
    lastUpdate: null,
  });
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    const newSocket = io(url, {
      transports: ['websocket', 'polling'],
      upgrade: true,
      reconnection: true,
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    // Connection events
    newSocket.on('connect', () => {
      console.log('Connected to WebSocket server');
      setConnected(true);
      reconnectAttempts.current = 0;
      
      // Subscribe to updates
      newSocket.emit('subscribe_updates');
      
      toast.success('Connected to trading bot', { toastId: 'ws-connect' });
    });

    newSocket.on('disconnect', (reason) => {
      console.log('Disconnected from WebSocket server:', reason);
      setConnected(false);
      
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        newSocket.connect();
      }
      
      toast.error('Disconnected from trading bot', { toastId: 'ws-disconnect' });
    });

    newSocket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      reconnectAttempts.current++;
      
      if (reconnectAttempts.current >= maxReconnectAttempts) {
        toast.error('Failed to connect to trading bot after multiple attempts');
      }
    });

    newSocket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected after ${attemptNumber} attempts`);
      toast.success('Reconnected to trading bot');
    });

    newSocket.on('reconnect_error', (error) => {
      console.error('Reconnection error:', error);
    });

    newSocket.on('reconnect_failed', () => {
      console.error('Failed to reconnect after maximum attempts');
      toast.error('Unable to reconnect to trading bot');
    });

    // Bot status updates
    newSocket.on('bot_status_update', (data) => {
      setBotStatus(prevStatus => ({
        ...prevStatus,
        ...data,
        lastUpdate: new Date().toISOString(),
      }));
    });

    // Position updates
    newSocket.on('position_update', (data) => {
      console.log('Position update received:', data);
      // Handle position updates here
    });

    // Trade updates
    newSocket.on('trade_update', (data) => {
      console.log('Trade update received:', data);
      toast.success(`New trade: ${data.side.toUpperCase()} ${data.symbol} - P&L: $${data.pnl?.toFixed(2)}`);
    });

    // Error notifications
    newSocket.on('error_notification', (data) => {
      console.error('Bot error:', data);
      toast.error(`Bot Error: ${data.message}`);
    });

    // Market data updates
    newSocket.on('market_update', (data) => {
      // Handle market data updates
      console.log('Market update:', data);
    });

    setSocket(newSocket);

    return () => {
      if (newSocket) {
        newSocket.disconnect();
      }
    };
  }, [url]);

  // Send message to server
  const sendMessage = (event, data) => {
    if (socket && connected) {
      socket.emit(event, data);
    } else {
      console.warn('Socket not connected, cannot send message');
    }
  };

  // Subscribe to specific events
  const subscribe = (event, callback) => {
    if (socket) {
      socket.on(event, callback);
      
      return () => {
        socket.off(event, callback);
      };
    }
  };

  return {
    socket,
    connected,
    botStatus,
    sendMessage,
    subscribe,
  };
};