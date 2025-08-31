import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Typography,
  Box,
  Divider,
  Chip,
  Avatar,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Dashboard,
  ShowChart,
  Assessment,
  Notifications,
  Settings,
  Help,
  Security,
  Timeline,
  AccountBalance,
  TrendingUp,
  Warning,
  Info,
  GitHub,
  Telegram,
  Close
} from '@mui/icons-material';
import { useDashboardStore } from '../../stores/dashboardStore';

const Sidebar = ({ open, onClose, isMobile }) => {
  const { performance, alerts, unreadAlerts } = useDashboardStore();

  const menuItems = [
    {
      title: 'Dashboard',
      icon: <Dashboard />,
      active: true,
      badge: null
    },
    {
      title: 'Live Trading',
      icon: <ShowChart />,
      active: false,
      badge: null
    },
    {
      title: 'Performance',
      icon: <Assessment />,
      active: false,
      badge: performance?.total_trades || 0
    },
    {
      title: 'Risk Monitor',
      icon: <Security />,
      active: false,
      badge: null
    },
    {
      title: 'Signals',
      icon: <Timeline />,
      active: false,
      badge: null
    },
    {
      title: 'Alerts',
      icon: <Notifications />,
      active: false,
      badge: unreadAlerts
    }
  ];

  const quickStats = [
    {
      label: 'Balance',
      value: `$${performance?.balance?.toFixed(2) || '10,000.00'}`,
      color: 'primary'
    },
    {
      label: 'P&L',
      value: `${performance?.total_pnl >= 0 ? '+' : ''}$${performance?.total_pnl?.toFixed(2) || '0.00'}`,
      color: performance?.total_pnl >= 0 ? 'success' : 'error'
    },
    {
      label: 'Win Rate',
      value: `${performance?.win_rate?.toFixed(1) || '0.0'}%`,
      color: performance?.win_rate > 50 ? 'success' : 'warning'
    }
  ];

  const drawerContent = (
    <Box sx={{ width: 240, height: '100%', bgcolor: 'background.paper' }}>
      {/* Header */}
      <Box 
        sx={{ 
          p: 2, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderBottom: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box display="flex" alignItems="center" gap={2}>
          <Avatar 
            sx={{ 
              bgcolor: 'primary.main', 
              width: 32, 
              height: 32,
              fontSize: '1rem' 
            }}
          >
            Q
          </Avatar>
          <Box>
            <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '1rem' }}>
              Quantum Bot
            </Typography>
            <Typography variant="caption" color="textSecondary">
              v2.0 Professional
            </Typography>
          </Box>
        </Box>
        {isMobile && (
          <IconButton size="small" onClick={onClose}>
            <Close />
          </IconButton>
        )}
      </Box>

      {/* Quick Stats */}
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" fontWeight="bold" mb={1} color="textSecondary">
          Quick Stats
        </Typography>
        {quickStats.map((stat, index) => (
          <Box key={index} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="caption" color="textSecondary">
              {stat.label}:
            </Typography>
            <Typography 
              variant="caption" 
              fontWeight="bold"
              color={`${stat.color}.main`}
            >
              {stat.value}
            </Typography>
          </Box>
        ))}
      </Box>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ px: 1, py: 2 }}>
        {menuItems.map((item, index) => (
          <ListItem key={index} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={item.active}
              sx={{
                borderRadius: 2,
                '&.Mui-selected': {
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'primary.contrastText',
                  }
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.title}
                primaryTypographyProps={{ 
                  fontSize: '0.875rem',
                  fontWeight: item.active ? 'bold' : 'normal'
                }}
              />
              {item.badge && (
                <Chip 
                  label={item.badge} 
                  size="small"
                  sx={{ 
                    height: 20,
                    fontSize: '0.7rem',
                    bgcolor: item.active ? 'primary.contrastText' : 'primary.main',
                    color: item.active ? 'primary.main' : 'primary.contrastText'
                  }}
                />
              )}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      {/* System Status */}
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" fontWeight="bold" mb={1} color="textSecondary">
          System Status
        </Typography>
        
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <Box 
              sx={{ 
                width: 8, 
                height: 8, 
                borderRadius: '50%', 
                bgcolor: 'success.main',
                animation: 'pulse 2s infinite'
              }} 
            />
            <Typography variant="caption">Connection</Typography>
          </Box>
          <Typography variant="caption" color="success.main" fontWeight="bold">
            Live
          </Typography>
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <TrendingUp fontSize="small" color="primary" />
            <Typography variant="caption">Trading</Typography>
          </Box>
          <Typography variant="caption" color="warning.main" fontWeight="bold">
            Monitoring
          </Typography>
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={1}>
            <AccountBalance fontSize="small" color="info" />
            <Typography variant="caption">Exchange</Typography>
          </Box>
          <Typography variant="caption" color="success.main" fontWeight="bold">
            Connected
          </Typography>
        </Box>
      </Box>

      <Divider />

      {/* Recent Alerts Preview */}
      {alerts.length > 0 && (
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" fontWeight="bold" mb={1} color="textSecondary">
            Recent Alerts
          </Typography>
          {alerts.slice(0, 3).map((alert, index) => (
            <Box key={index} display="flex" alignItems="center" gap={1} mb={1}>
              {alert.type === 'signal' ? <TrendingUp fontSize="small" color="primary" /> :
               alert.priority === 'critical' ? <Warning fontSize="small" color="error" /> :
               <Info fontSize="small" color="info" />}
              <Typography 
                variant="caption" 
                sx={{ 
                  overflow: 'hidden', 
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  flex: 1
                }}
              >
                {alert.message.substring(0, 30)}...
              </Typography>
            </Box>
          ))}
        </Box>
      )}

      <Box sx={{ flexGrow: 1 }} />

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Box display="flex" justifyContent="center" gap={1} mb={2}>
          <Tooltip title="View on GitHub">
            <IconButton size="small" href="https://github.com" target="_blank">
              <GitHub fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Telegram Support">
            <IconButton size="small">
              <Telegram fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Help & Documentation">
            <IconButton size="small">
              <Help fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton size="small">
              <Settings fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Typography variant="caption" color="textSecondary" align="center" display="block">
          High-Volatility Trading System
        </Typography>
        <Typography variant="caption" color="textSecondary" align="center" display="block">
          © 2024 Quantum Trading
        </Typography>
      </Box>

      <style jsx>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </Box>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <Drawer
        variant={isMobile ? "temporary" : "permanent"}
        open={isMobile ? open : true}
        onClose={onClose}
        sx={{
          width: 240,
          flexShrink: 0,
          display: { xs: isMobile ? 'block' : 'none', sm: 'block' },
          '& .MuiDrawer-paper': {
            width: 240,
            boxSizing: 'border-box',
            borderRight: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper',
            backgroundImage: 'none',
          },
        }}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Mobile Backdrop */}
      {isMobile && open && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            bgcolor: 'rgba(0, 0, 0, 0.5)',
            zIndex: (theme) => theme.zIndex.drawer - 1,
          }}
          onClick={onClose}
        />
      )}
    </>
  );
};

export default Sidebar;