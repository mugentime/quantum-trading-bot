import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, IconButton, Drawer, useMediaQuery } from '@mui/material';
import { DarkMode, LightMode, Menu as MenuIcon } from '@mui/icons-material';
import { Toaster } from 'react-hot-toast';

// Import dashboard components
import Sidebar from './components/Layout/Sidebar';
import DashboardGrid from './components/Layout/DashboardGrid';
import LiveTradingPanel from './components/Panels/LiveTradingPanel';
import VolatilityHeatMap from './components/Panels/VolatilityHeatMap';
import PerformanceMetrics from './components/Panels/PerformanceMetrics';
import RiskMonitor from './components/Panels/RiskMonitor';
import SignalAnalysis from './components/Panels/SignalAnalysis';
import HistoricalCharts from './components/Panels/HistoricalCharts';
import AlertsPanel from './components/Panels/AlertsPanel';
import ControlPanel from './components/Panels/ControlPanel';

// Import custom hooks and stores
import { useWebSocket } from './hooks/useWebSocket';
import { useDashboardStore } from './stores/dashboardStore';

// Create theme variants
const createAppTheme = (isDark) => createTheme({
  palette: {
    mode: isDark ? 'dark' : 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: isDark ? '#0a0a0a' : '#f5f5f5',
      paper: isDark ? '#1a1a1a' : '#ffffff',
    },
    success: {
      main: '#00e676',
    },
    error: {
      main: '#ff1744',
    },
    warning: {
      main: '#ffb300',
    },
    info: {
      main: '#00bcd4',
    },
  },
  typography: {
    fontFamily: '"Roboto Mono", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(10px)',
          border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid rgba(0, 0, 0, 0.12)',
          borderRadius: 12,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(10px)',
        },
      },
    },
  },
});

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : true;
  });

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useMediaQuery('(max-width:768px)');
  const theme = createAppTheme(darkMode);

  // Global state from Zustand store
  const { 
    positions, 
    performance, 
    isConnected, 
    status,
    setConnectionStatus 
  } = useDashboardStore();

  // WebSocket connection
  const { 
    isConnected: wsConnected,
    lastMessage,
    sendMessage 
  } = useWebSocket('ws://localhost:5000');

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  useEffect(() => {
    setConnectionStatus(wsConnected);
  }, [wsConnected, setConnectionStatus]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Default dashboard layout
  const defaultLayout = [
    { i: 'live-trading', x: 0, y: 0, w: 6, h: 4, minW: 3, minH: 3 },
    { i: 'performance', x: 6, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
    { i: 'risk-monitor', x: 9, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
    { i: 'volatility-heatmap', x: 0, y: 4, w: 4, h: 3, minW: 3, minH: 2 },
    { i: 'signal-analysis', x: 4, y: 4, w: 4, h: 3, minW: 3, minH: 2 },
    { i: 'control-panel', x: 8, y: 4, w: 4, h: 3, minW: 2, minH: 2 },
    { i: 'historical-charts', x: 0, y: 7, w: 8, h: 5, minW: 4, minH: 3 },
    { i: 'alerts', x: 8, y: 7, w: 4, h: 5, minW: 2, minH: 3 },
  ];

  const dashboardComponents = {
    'live-trading': <LiveTradingPanel />,
    'performance': <PerformanceMetrics />,
    'risk-monitor': <RiskMonitor />,
    'volatility-heatmap': <VolatilityHeatMap />,
    'signal-analysis': <SignalAnalysis />,
    'control-panel': <ControlPanel />,
    'historical-charts': <HistoricalCharts />,
    'alerts': <AlertsPanel />,
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh' }}>
        {/* App Bar */}
        <AppBar 
          position="fixed" 
          sx={{ 
            zIndex: (theme) => theme.zIndex.drawer + 1,
            backdropFilter: 'blur(10px)',
            backgroundColor: darkMode ? 'rgba(26, 26, 26, 0.8)' : 'rgba(255, 255, 255, 0.8)',
          }}
        >
          <Toolbar>
            {isMobile && (
              <IconButton
                edge="start"
                color="inherit"
                onClick={handleSidebarToggle}
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
            )}
            
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
              Quantum Trading Dashboard
            </Typography>

            {/* Connection Status */}
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                mr: 2,
                px: 2,
                py: 0.5,
                borderRadius: 1,
                backgroundColor: isConnected ? 'success.main' : 'error.main',
                color: 'white',
                fontSize: '0.875rem',
              }}
            >
              <Box 
                sx={{ 
                  width: 8, 
                  height: 8, 
                  borderRadius: '50%', 
                  backgroundColor: 'white',
                  mr: 1,
                  animation: isConnected ? 'pulse 2s infinite' : 'none',
                }} 
              />
              {isConnected ? 'Live' : 'Offline'}
            </Box>

            {/* P&L Display */}
            <Box sx={{ mr: 2, display: { xs: 'none', sm: 'block' } }}>
              <Typography variant="body2" color="textSecondary">
                Total P&L: 
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ 
                  color: performance?.total_pnl >= 0 ? 'success.main' : 'error.main',
                  fontWeight: 'bold',
                }}
              >
                ${performance?.total_pnl?.toFixed(2) || '0.00'}
              </Typography>
            </Box>

            {/* Dark Mode Toggle */}
            <IconButton color="inherit" onClick={toggleDarkMode}>
              {darkMode ? <LightMode /> : <DarkMode />}
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Sidebar */}
        <Sidebar 
          open={sidebarOpen} 
          onClose={handleSidebarToggle}
          isMobile={isMobile}
        />

        {/* Main Content */}
        <Box 
          component="main" 
          sx={{ 
            flexGrow: 1, 
            p: 2,
            mt: 8, // Account for AppBar height
            ml: isMobile ? 0 : '240px', // Account for Sidebar width
            height: 'calc(100vh - 64px)',
            overflow: 'auto',
          }}
        >
          <DashboardGrid
            layout={defaultLayout}
            components={dashboardComponents}
            cols={12}
            rowHeight={60}
          />
        </Box>

        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 5000,
            style: {
              background: darkMode ? '#333' : '#fff',
              color: darkMode ? '#fff' : '#333',
            },
          }}
        />
      </Box>

      {/* Global Styles */}
      <style jsx global>{`
        @keyframes pulse {
          0% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
          100% {
            opacity: 1;
          }
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }

        ::-webkit-scrollbar-track {
          background: ${darkMode ? '#1a1a1a' : '#f1f1f1'};
        }

        ::-webkit-scrollbar-thumb {
          background: ${darkMode ? '#555' : '#888'};
          border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: ${darkMode ? '#777' : '#555'};
        }

        /* Chart styling */
        .recharts-default-tooltip {
          background-color: ${darkMode ? '#333 !important' : '#fff !important'};
          border: 1px solid ${darkMode ? '#555 !important' : '#ddd !important'};
          border-radius: 8px !important;
        }

        /* Trading view colors */
        .profit {
          color: #00e676 !important;
        }

        .loss {
          color: #ff1744 !important;
        }

        .neutral {
          color: #ffb300 !important;
        }

        /* Responsive grid adjustments */
        @media (max-width: 768px) {
          .react-grid-item {
            min-width: 100% !important;
          }
        }
      `}</style>
    </ThemeProvider>
  );
}

export default App;