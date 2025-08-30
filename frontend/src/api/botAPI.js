import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const botAPI = {
  // Bot control
  getStatus: async () => {
    try {
      const response = await api.get('/bot/status');
      return response.data;
    } catch (error) {
      // Return mock data for development
      return {
        status: 'running',
        balance: 10250.75,
        pnl: 250.75,
        positions: 3,
        lastUpdate: new Date().toISOString(),
      };
    }
  },

  start: async () => {
    const response = await api.post('/bot/start');
    return response.data;
  },

  stop: async () => {
    const response = await api.post('/bot/stop');
    return response.data;
  },

  // Trading data
  getPositions: async () => {
    try {
      const response = await api.get('/positions');
      return response.data;
    } catch (error) {
      // Return mock data for development
      return [
        {
          id: '1',
          symbol: 'ETHUSDT',
          side: 'long',
          size: 0.5,
          entryPrice: 3250.50,
          markPrice: 3280.25,
          pnl: 14.88,
          pnlPercent: 0.91,
          leverage: 15,
          timestamp: new Date().toISOString(),
        },
        {
          id: '2',
          symbol: 'SOLUSDT',
          side: 'short',
          size: 2.0,
          entryPrice: 205.20,
          markPrice: 203.15,
          pnl: 4.10,
          pnlPercent: 1.00,
          leverage: 10,
          timestamp: new Date(Date.now() - 3600000).toISOString(),
        },
      ];
    }
  },

  getTrades: async (limit = 100) => {
    try {
      const response = await api.get(`/trades?limit=${limit}`);
      return response.data;
    } catch (error) {
      // Return mock data for development
      return [
        {
          id: '1',
          symbol: 'ETHUSDT',
          side: 'long',
          size: 0.3,
          entryPrice: 3200.00,
          exitPrice: 3250.50,
          pnl: 15.15,
          pnlPercent: 1.58,
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          exitTimestamp: new Date(Date.now() - 3600000).toISOString(),
          duration: '1h',
        },
        {
          id: '2',
          symbol: 'LINKUSDT',
          side: 'short',
          size: 5.0,
          entryPrice: 15.80,
          exitPrice: 15.65,
          pnl: 0.75,
          pnlPercent: 0.95,
          timestamp: new Date(Date.now() - 10800000).toISOString(),
          exitTimestamp: new Date(Date.now() - 7200000).toISOString(),
          duration: '1h',
        },
      ];
    }
  },

  // Market data
  getMarketData: async (symbols) => {
    try {
      const response = await api.get('/market/data', {
        params: { symbols: symbols.join(',') },
      });
      return response.data;
    } catch (error) {
      // Return mock data for development
      return symbols.map(symbol => ({
        symbol,
        price: Math.random() * 1000 + 100,
        change24h: (Math.random() - 0.5) * 10,
        volume24h: Math.random() * 1000000,
        correlation: Math.random() * 2 - 1,
      }));
    }
  },

  // Performance data
  getPerformance: async (timeframe = '24h') => {
    try {
      const response = await api.get(`/performance?timeframe=${timeframe}`);
      return response.data;
    } catch (error) {
      // Return mock data for development
      const now = new Date();
      const data = [];
      for (let i = 23; i >= 0; i--) {
        data.push({
          timestamp: new Date(now.getTime() - i * 3600000).toISOString(),
          balance: 10000 + Math.random() * 500 - 250,
          pnl: Math.random() * 100 - 50,
          trades: Math.floor(Math.random() * 5),
        });
      }
      return {
        totalReturn: 2.51,
        totalPnl: 250.75,
        winRate: 68.5,
        sharpeRatio: 1.24,
        maxDrawdown: 1.8,
        data,
      };
    }
  },

  // Settings
  getSettings: async () => {
    try {
      const response = await api.get('/settings');
      return response.data;
    } catch (error) {
      // Return mock data for development
      return {
        riskPerTrade: 0.02,
        maxPositions: 5,
        defaultLeverage: 15,
        maxLeverage: 30,
        stopLoss: 0.03,
        takeProfit: 0.05,
        enabledPairs: ['ETHUSDT', 'LINKUSDT', 'SOLUSDT'],
        telegramNotifications: true,
      };
    }
  },

  updateSettings: async (settings) => {
    const response = await api.put('/settings', settings);
    return response.data;
  },
};

export default api;