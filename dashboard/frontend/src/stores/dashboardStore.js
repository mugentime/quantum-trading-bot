import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// Dashboard store using Zustand for global state management
export const useDashboardStore = create(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Connection status
      isConnected: false,
      lastUpdate: null,
      status: 'stopped',

      // Trading data
      positions: [],
      trades: [],
      signals: [],
      
      // Performance metrics
      performance: {
        total_pnl: 0,
        daily_pnl: 0,
        weekly_pnl: 0,
        monthly_pnl: 0,
        win_rate: 0,
        profit_factor: 0,
        sharpe_ratio: 0,
        max_drawdown: 0,
        current_drawdown: 0,
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        avg_win: 0,
        avg_loss: 0,
        best_trade: 0,
        worst_trade: 0,
        roi: 0,
        balance: 10000,
        equity: 10000,
        margin_used: 0,
        free_margin: 10000,
        margin_level: 100,
      },

      // Market data
      volatilityData: {},
      priceData: {},
      correlationMatrix: {},
      equityCurve: [],

      // Alerts
      alerts: [],
      unreadAlerts: 0,

      // UI state
      selectedTimeframe: '1h',
      selectedPair: 'ETH/USDT',
      dashboardLayout: null,
      alertsOpen: false,
      soundEnabled: true,

      // Actions
      setConnectionStatus: (connected) => {
        set({ 
          isConnected: connected,
          lastUpdate: connected ? new Date().toISOString() : null
        });
      },

      setStatus: (status) => {
        set({ status });
      },

      updatePositions: (positions) => {
        set({ positions });
      },

      updatePerformance: (performance) => {
        set((state) => ({
          performance: { ...state.performance, ...performance }
        }));
      },

      updateVolatility: (volatilityData) => {
        set({ volatilityData });
      },

      updatePrices: (priceData) => {
        set({ priceData });
      },

      updateSignals: (signals) => {
        set({ signals });
      },

      updateEquityCurve: (equityCurve) => {
        set({ equityCurve });
      },

      addTrade: (trade) => {
        set((state) => ({
          trades: [trade, ...state.trades.slice(0, 999)] // Keep last 1000 trades
        }));
      },

      addAlert: (alert) => {
        set((state) => ({
          alerts: [alert, ...state.alerts.slice(0, 99)], // Keep last 100 alerts
          unreadAlerts: state.unreadAlerts + 1
        }));
      },

      markAlertRead: (alertId) => {
        set((state) => ({
          alerts: state.alerts.map(alert =>
            alert.id === alertId ? { ...alert, read: true } : alert
          ),
          unreadAlerts: Math.max(0, state.unreadAlerts - 1)
        }));
      },

      clearAllAlerts: () => {
        set({ alerts: [], unreadAlerts: 0 });
      },

      setSelectedTimeframe: (timeframe) => {
        set({ selectedTimeframe: timeframe });
      },

      setSelectedPair: (pair) => {
        set({ selectedPair: pair });
      },

      setDashboardLayout: (layout) => {
        set({ dashboardLayout: layout });
        // Persist layout to localStorage
        localStorage.setItem('dashboardLayout', JSON.stringify(layout));
      },

      loadDashboardLayout: () => {
        const saved = localStorage.getItem('dashboardLayout');
        if (saved) {
          set({ dashboardLayout: JSON.parse(saved) });
        }
      },

      toggleAlerts: () => {
        set((state) => ({ alertsOpen: !state.alertsOpen }));
      },

      setSoundEnabled: (enabled) => {
        set({ soundEnabled: enabled });
        localStorage.setItem('soundEnabled', JSON.stringify(enabled));
      },

      // Handle complete dashboard update from WebSocket
      handleDashboardUpdate: (data) => {
        set((state) => ({
          positions: data.positions || state.positions,
          performance: { ...state.performance, ...data.performance },
          volatilityData: data.volatility || state.volatilityData,
          priceData: data.prices || state.priceData,
          signals: data.signals || state.signals,
          equityCurve: data.equity_curve || state.equityCurve,
          lastUpdate: data.timestamp,
        }));
      },

      // Utility functions
      getTotalPnL: () => {
        const state = get();
        return state.positions.reduce((total, pos) => total + (pos.pnl || 0), 0);
      },

      getTotalPositions: () => {
        const state = get();
        return state.positions.length;
      },

      getActiveSignals: () => {
        const state = get();
        return state.signals.filter(signal => 
          signal.confidence > 0.5 && 
          Date.now() - new Date(signal.timestamp).getTime() < 300000 // 5 minutes
        );
      },

      getPortfolioHeat: () => {
        const state = get();
        const totalMargin = state.performance.margin_used;
        const freeMargin = state.performance.free_margin;
        return totalMargin / (totalMargin + freeMargin) * 100;
      },

      getRiskLevel: () => {
        const state = get();
        const marginLevel = state.performance.margin_level;
        const drawdown = state.performance.current_drawdown;
        
        if (marginLevel < 150 || drawdown > 15) return 'high';
        if (marginLevel < 300 || drawdown > 10) return 'medium';
        return 'low';
      },

      // Data transformation helpers
      getEquityCurveData: () => {
        const state = get();
        return state.equityCurve.map((equity, index) => ({
          x: index,
          y: equity,
          time: new Date(Date.now() - (state.equityCurve.length - index) * 60000).toISOString()
        }));
      },

      getVolatilityHeatMapData: () => {
        const state = get();
        return Object.entries(state.volatilityData).map(([symbol, data]) => ({
          symbol,
          value: data.value,
          level: data.level,
          color: data.color,
          price: state.priceData[symbol]?.last || 0,
          change24h: state.priceData[symbol]?.change_24h || 0
        }));
      },

      getSignalStrength: (symbol) => {
        const state = get();
        const signal = state.signals.find(s => s.symbol === symbol);
        if (!signal) return 0;
        
        return signal.confidence * (signal.correlation ? Math.abs(signal.correlation) : 1);
      },

      // Initialize store
      init: () => {
        const state = get();
        
        // Load saved preferences
        const soundEnabled = localStorage.getItem('soundEnabled');
        if (soundEnabled) {
          set({ soundEnabled: JSON.parse(soundEnabled) });
        }
        
        // Load saved layout
        state.loadDashboardLayout();
      },
    })),
    {
      name: 'dashboard-store',
      getStorage: () => localStorage,
    }
  )
);

// Selectors for better performance
export const usePositions = () => useDashboardStore((state) => state.positions);
export const usePerformance = () => useDashboardStore((state) => state.performance);
export const useVolatilityData = () => useDashboardStore((state) => state.volatilityData);
export const usePriceData = () => useDashboardStore((state) => state.priceData);
export const useSignals = () => useDashboardStore((state) => state.signals);
export const useAlerts = () => useDashboardStore((state) => state.alerts);
export const useConnectionStatus = () => useDashboardStore((state) => state.isConnected);

// Custom hooks for computed values
export const useTotalPnL = () => {
  return useDashboardStore((state) => 
    state.positions.reduce((total, pos) => total + (pos.pnl || 0), 0)
  );
};

export const usePortfolioHeat = () => {
  return useDashboardStore((state) => {
    const totalMargin = state.performance.margin_used;
    const freeMargin = state.performance.free_margin;
    return totalMargin / (totalMargin + freeMargin) * 100;
  });
};

export const useRiskLevel = () => {
  return useDashboardStore((state) => {
    const marginLevel = state.performance.margin_level;
    const drawdown = state.performance.current_drawdown;
    
    if (marginLevel < 150 || drawdown > 15) return 'high';
    if (marginLevel < 300 || drawdown > 10) return 'medium';
    return 'low';
  });
};

// Initialize store on load
useDashboardStore.getState().init();