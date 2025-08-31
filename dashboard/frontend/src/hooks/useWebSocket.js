import { useEffect, useRef, useState, useCallback } from 'react';
import { useDashboardStore } from '../stores/dashboardStore';
import toast from 'react-hot-toast';

// Audio context for alert sounds
let audioContext;
let alertSound;

const initAudio = () => {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
  
  if (!alertSound) {
    // Create a simple beep sound
    const createBeep = (frequency, duration, type = 'sine') => {
      return new Promise((resolve) => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = frequency;
        oscillator.type = type;
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + duration);
        
        setTimeout(resolve, duration * 1000);
      });
    };
    
    alertSound = {
      success: () => createBeep(800, 0.2),
      warning: () => createBeep(600, 0.3),
      error: async () => {
        await createBeep(400, 0.2);
        await new Promise(resolve => setTimeout(resolve, 100));
        await createBeep(400, 0.2);
      },
      signal: async () => {
        await createBeep(1000, 0.1);
        await new Promise(resolve => setTimeout(resolve, 50));
        await createBeep(1200, 0.1);
      }
    };
  }
};

export const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  const messageQueueRef = useRef([]);
  
  const {
    handleDashboardUpdate,
    addAlert,
    setConnectionStatus,
    soundEnabled
  } = useDashboardStore();

  const playAlertSound = useCallback(async (type = 'info') => {
    if (!soundEnabled) return;
    
    try {
      if (audioContext?.state === 'suspended') {
        await audioContext.resume();
      }
      
      if (alertSound && alertSound[type]) {
        await alertSound[type]();
      }
    } catch (error) {
      console.warn('Failed to play alert sound:', error);
    }
  }, [soundEnabled]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = url.replace('ws://', '').replace('wss://', '');
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const socketUrl = `${protocol}//${wsUrl}`;
      
      wsRef.current = new WebSocket(socketUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus(true);
        setReconnectCount(0);
        
        // Initialize audio on first connection
        initAudio();
        
        // Send queued messages
        while (messageQueueRef.current.length > 0) {
          const message = messageQueueRef.current.shift();
          wsRef.current.send(JSON.stringify(message));
        }
        
        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Ping every 30 seconds
        
        toast.success('Connected to trading dashboard');
      };

      wsRef.current.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          
          // Handle different message types
          switch (data.type) {
            case 'dashboard_update':
              handleDashboardUpdate(data.data);
              break;
              
            case 'alert':
              addAlert(data.data);
              
              // Play sound based on alert priority/type
              if (data.data.priority === 'critical') {
                await playAlertSound('error');
              } else if (data.data.priority === 'high') {
                await playAlertSound('warning');
              } else if (data.data.type === 'signal') {
                await playAlertSound('signal');
              } else {
                await playAlertSound('success');
              }
              
              // Show toast notification
              const toastOptions = {
                duration: data.data.priority === 'critical' ? 10000 : 5000,
                icon: data.data.type === 'signal' ? '📈' : 
                      data.data.type === 'warning' ? '⚠️' : 
                      data.data.type === 'danger' ? '🚨' : '📊'
              };
              
              if (data.data.priority === 'critical') {
                toast.error(data.data.message, toastOptions);
              } else if (data.data.priority === 'high') {
                toast.error(data.data.message, toastOptions);
              } else {
                toast.success(data.data.message, toastOptions);
              }
              break;
              
            case 'position_update':
              // Handle individual position updates
              break;
              
            case 'trade_executed':
              toast.success(`Trade executed: ${data.data.symbol} ${data.data.side}`, {
                icon: '✅'
              });
              await playAlertSound('success');
              break;
              
            case 'pong':
              // Heartbeat response
              break;
              
            case 'error':
              toast.error(`Error: ${data.message}`);
              await playAlertSound('error');
              break;
              
            default:
              console.log('Unhandled message type:', data.type);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus(false);
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }
        
        // Attempt to reconnect unless it was a normal closure
        if (event.code !== 1000 && event.code !== 1001) {
          const timeout = Math.min(1000 * Math.pow(2, reconnectCount), 30000);
          
          toast.error(`Connection lost. Reconnecting in ${timeout / 1000}s...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount(prev => prev + 1);
            connect();
          }, timeout);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        toast.error('Connection error occurred');
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      toast.error('Failed to connect to server');
    }
  }, [url, reconnectCount, handleDashboardUpdate, addAlert, setConnectionStatus, playAlertSound]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus(false);
  }, [setConnectionStatus]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      // Queue message for when connection is established
      messageQueueRef.current.push(message);
    }
  }, []);

  // Subscribe to specific data streams
  const subscribe = useCallback((stream) => {
    sendMessage({ type: 'subscribe', stream });
  }, [sendMessage]);

  // Send commands to the server
  const sendCommand = useCallback((command, params = {}) => {
    sendMessage({ type: 'command', command, params });
  }, [sendMessage]);

  // Force update data
  const forceUpdate = useCallback(() => {
    sendCommand('force_update');
  }, [sendCommand]);

  // Clear alerts
  const clearAlerts = useCallback(() => {
    sendCommand('clear_alerts');
  }, [sendCommand]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && !isConnected) {
        // Page became visible and we're not connected, try to reconnect
        connect();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isConnected, connect]);

  // Handle online/offline events
  useEffect(() => {
    const handleOnline = () => {
      if (!isConnected) {
        connect();
      }
    };

    const handleOffline = () => {
      toast.error('Internet connection lost');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isConnected, connect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
    sendCommand,
    forceUpdate,
    clearAlerts,
    connect,
    disconnect,
    reconnectCount
  };
};