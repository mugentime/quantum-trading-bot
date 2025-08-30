import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp as TradingIcon,
  AccountBalance as PositionsIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useBotStatus } from '../hooks/useBotStatus';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { botStatus, toggleBot } = useBotStatus();
  const [anchorEl, setAnchorEl] = useState(null);

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: DashboardIcon },
    { path: '/trading', label: 'Trading', icon: TradingIcon },
    { path: '/positions', label: 'Positions', icon: PositionsIcon },
    { path: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getBotStatusColor = () => {
    switch (botStatus.status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'error';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <AppBar position="static" sx={{ bgcolor: '#1e2329', boxShadow: 'none', borderBottom: '1px solid #2b3139' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 700, color: '#f0b90b', mr: 4 }}>
            Quantum Trading
          </Typography>
          
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1 }}>
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Button
                  key={item.path}
                  startIcon={<Icon />}
                  onClick={() => navigate(item.path)}
                  sx={{
                    color: isActive ? '#f0b90b' : '#848e9c',
                    bgcolor: isActive ? 'rgba(240, 185, 11, 0.1)' : 'transparent',
                    '&:hover': {
                      bgcolor: 'rgba(240, 185, 11, 0.05)',
                      color: '#f0b90b',
                    },
                  }}
                >
                  {item.label}
                </Button>
              );
            })}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            label={`Bot ${botStatus.status?.toUpperCase() || 'UNKNOWN'}`}
            color={getBotStatusColor()}
            size="small"
            sx={{ fontWeight: 600 }}
          />
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ color: '#848e9c' }}>
              Balance: ${botStatus.balance?.toFixed(2) || '0.00'}
            </Typography>
            
            <Button
              variant="contained"
              size="small"
              startIcon={botStatus.status === 'running' ? <StopIcon /> : <PlayIcon />}
              onClick={toggleBot}
              color={botStatus.status === 'running' ? 'error' : 'success'}
              sx={{ minWidth: 100 }}
            >
              {botStatus.status === 'running' ? 'Stop' : 'Start'}
            </Button>
          </Box>

          <IconButton
            sx={{ display: { xs: 'block', md: 'none' }, color: '#848e9c' }}
            onClick={handleMenuClick}
          >
            <MoreIcon />
          </IconButton>
          
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            sx={{ display: { xs: 'block', md: 'none' } }}
          >
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <MenuItem
                  key={item.path}
                  onClick={() => {
                    navigate(item.path);
                    handleMenuClose();
                  }}
                >
                  <Icon sx={{ mr: 2 }} />
                  {item.label}
                </MenuItem>
              );
            })}
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;