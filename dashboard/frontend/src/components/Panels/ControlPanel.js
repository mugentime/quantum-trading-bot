import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Switch,
  FormControlLabel,
  Slider,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Pause,
  Refresh,
  Settings,
  Download,
  Upload,
  RestartAlt,
  Warning,
  CheckCircle
} from '@mui/icons-material';
import { useDashboardStore, useConnectionStatus } from '../../stores/dashboardStore';

const ControlPanel = () => {
  const isConnected = useConnectionStatus();
  const { status, setStatus } = useDashboardStore();
  
  const [settings, setSettings] = useState({
    autoTrading: false,
    riskPerTrade: 2.0,
    maxPositions: 5,
    defaultLeverage: 15,
    maxLeverage: 30,
    stopLoss: 3.0,
    takeProfit: 5.0,
    enabledPairs: ['ETHUSDT', 'LINKUSDT', 'SOLUSDT'],
    telegramNotifications: true,
    soundAlerts: true,
    minConfidence: 60,
    maxDrawdown: 15,
  });

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: '', message: '' });

  const tradingPairs = [
    'ETHUSDT', 'BTCUSDT', 'LINKUSDT', 'SOLUSDT', 
    'AVAXUSDT', 'INJUSDT', 'WLDUSDT', 'BNBUSDT'
  ];

  const handleStartTrading = () => {
    setConfirmDialog({
      open: true,
      action: 'start',
      message: 'Start automated trading with current settings?'
    });
  };

  const handleStopTrading = () => {
    setConfirmDialog({
      open: true,
      action: 'stop',
      message: 'Stop all automated trading and close positions?'
    });
  };

  const handleEmergencyStop = () => {
    setConfirmDialog({
      open: true,
      action: 'emergency',
      message: 'EMERGENCY STOP: Immediately close all positions and halt trading?'
    });
  };

  const handleConfirmAction = () => {
    const action = confirmDialog.action;
    
    switch (action) {
      case 'start':
        setStatus('running');
        // API call to start trading
        break;
      case 'stop':
        setStatus('stopped');
        // API call to stop trading
        break;
      case 'emergency':
        setStatus('emergency_stop');
        // API call for emergency stop
        break;
      default:
        break;
    }
    
    setConfirmDialog({ open: false, action: '', message: '' });
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handlePairToggle = (pair) => {
    setSettings(prev => ({
      ...prev,
      enabledPairs: prev.enabledPairs.includes(pair)
        ? prev.enabledPairs.filter(p => p !== pair)
        : [...prev.enabledPairs, pair]
    }));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'success.main';
      case 'paused':
        return 'warning.main';
      case 'stopped':
        return 'text.secondary';
      case 'emergency_stop':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <PlayArrow />;
      case 'paused':
        return <Pause />;
      case 'stopped':
        return <Stop />;
      case 'emergency_stop':
        return <Warning />;
      default:
        return <Stop />;
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            Control Panel
          </Typography>
          <Box display="flex" gap={1}>
            <Tooltip title="Download configuration">
              <IconButton size="small">
                <Download fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Upload configuration">
              <IconButton size="small">
                <Upload fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Settings">
              <IconButton size="small" onClick={() => setSettingsOpen(true)}>
                <Settings fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* System Status */}
        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" fontWeight="bold">
              System Status
            </Typography>
            <Chip 
              icon={getStatusIcon(status)}
              label={status.replace('_', ' ').toUpperCase()}
              size="small"
              sx={{ 
                bgcolor: getStatusColor(status),
                color: 'white',
                fontWeight: 'bold'
              }}
            />
          </Box>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="textSecondary">
              Connection: {isConnected ? 'Connected' : 'Disconnected'}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Last Update: {new Date().toLocaleTimeString()}
            </Typography>
          </Box>
        </Box>

        {/* Quick Controls */}
        <Box mb={3}>
          <Typography variant="body2" fontWeight="bold" mb={2}>
            Trading Controls
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={6}>
              <Button 
                variant="contained"
                color="success"
                fullWidth
                disabled={status === 'running'}
                onClick={handleStartTrading}
                startIcon={<PlayArrow />}
              >
                Start
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button 
                variant="contained"
                color="warning"
                fullWidth
                disabled={status === 'stopped'}
                onClick={handleStopTrading}
                startIcon={<Stop />}
              >
                Stop
              </Button>
            </Grid>
            <Grid item xs={12}>
              <Button 
                variant="contained"
                color="error"
                fullWidth
                onClick={handleEmergencyStop}
                startIcon={<Warning />}
                sx={{ mt: 1 }}
              >
                EMERGENCY STOP
              </Button>
            </Grid>
          </Grid>
        </Box>

        {/* Quick Settings */}
        <Box mb={3}>
          <Typography variant="body2" fontWeight="bold" mb={2}>
            Quick Settings
          </Typography>
          
          <Box mb={2}>
            <Typography variant="caption" color="textSecondary">
              Risk Per Trade: {settings.riskPerTrade}%
            </Typography>
            <Slider
              value={settings.riskPerTrade}
              min={0.5}
              max={10}
              step={0.5}
              onChange={(e, value) => handleSettingChange('riskPerTrade', value)}
              size="small"
              sx={{ mt: 1 }}
            />
          </Box>

          <Box mb={2}>
            <Typography variant="caption" color="textSecondary">
              Default Leverage: {settings.defaultLeverage}x
            </Typography>
            <Slider
              value={settings.defaultLeverage}
              min={1}
              max={50}
              step={1}
              onChange={(e, value) => handleSettingChange('defaultLeverage', value)}
              size="small"
              sx={{ mt: 1 }}
            />
          </Box>

          <Box mb={2}>
            <Typography variant="caption" color="textSecondary">
              Min Signal Confidence: {settings.minConfidence}%
            </Typography>
            <Slider
              value={settings.minConfidence}
              min={30}
              max={95}
              step={5}
              onChange={(e, value) => handleSettingChange('minConfidence', value)}
              size="small"
              sx={{ mt: 1 }}
            />
          </Box>

          <FormControlLabel
            control={
              <Switch 
                checked={settings.autoTrading}
                onChange={(e) => handleSettingChange('autoTrading', e.target.checked)}
                size="small"
              />
            }
            label="Auto Trading"
          />
        </Box>

        {/* Enabled Trading Pairs */}
        <Box mb={3}>
          <Typography variant="body2" fontWeight="bold" mb={1}>
            Enabled Pairs ({settings.enabledPairs.length})
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={0.5}>
            {tradingPairs.map(pair => (
              <Chip
                key={pair}
                label={pair}
                size="small"
                onClick={() => handlePairToggle(pair)}
                color={settings.enabledPairs.includes(pair) ? 'primary' : 'default'}
                variant={settings.enabledPairs.includes(pair) ? 'filled' : 'outlined'}
              />
            ))}
          </Box>
        </Box>

        {/* Status Indicators */}
        <Box>
          <Typography variant="body2" fontWeight="bold" mb={1}>
            System Health
          </Typography>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="caption">API Connection</Typography>
            <CheckCircle fontSize="small" color={isConnected ? 'success' : 'error'} />
          </Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="caption">WebSocket</Typography>
            <CheckCircle fontSize="small" color={isConnected ? 'success' : 'error'} />
          </Box>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="caption">Risk Manager</Typography>
            <CheckCircle fontSize="small" color="success" />
          </Box>
        </Box>

        {/* Settings Dialog */}
        <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Trading Settings</DialogTitle>
          <DialogContent>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <Typography variant="h6" mb={2}>Risk Management</Typography>
                
                <TextField
                  label="Risk Per Trade (%)"
                  type="number"
                  value={settings.riskPerTrade}
                  onChange={(e) => handleSettingChange('riskPerTrade', parseFloat(e.target.value))}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />

                <TextField
                  label="Max Positions"
                  type="number"
                  value={settings.maxPositions}
                  onChange={(e) => handleSettingChange('maxPositions', parseInt(e.target.value))}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />

                <TextField
                  label="Stop Loss (%)"
                  type="number"
                  value={settings.stopLoss}
                  onChange={(e) => handleSettingChange('stopLoss', parseFloat(e.target.value))}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />

                <TextField
                  label="Take Profit (%)"
                  type="number"
                  value={settings.takeProfit}
                  onChange={(e) => handleSettingChange('takeProfit', parseFloat(e.target.value))}
                  fullWidth
                  size="small"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography variant="h6" mb={2}>Trading Parameters</Typography>
                
                <TextField
                  label="Default Leverage"
                  type="number"
                  value={settings.defaultLeverage}
                  onChange={(e) => handleSettingChange('defaultLeverage', parseInt(e.target.value))}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />

                <TextField
                  label="Max Leverage"
                  type="number"
                  value={settings.maxLeverage}
                  onChange={(e) => handleSettingChange('maxLeverage', parseInt(e.target.value))}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />

                <TextField
                  label="Min Confidence (%)"
                  type="number"
                  value={settings.minConfidence}
                  onChange={(e) => handleSettingChange('minConfidence', parseInt(e.target.value))}
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                />

                <TextField
                  label="Max Drawdown (%)"
                  type="number"
                  value={settings.maxDrawdown}
                  onChange={(e) => handleSettingChange('maxDrawdown', parseInt(e.target.value))}
                  fullWidth
                  size="small"
                />
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" mb={2}>Notifications</Typography>
                
                <FormControlLabel
                  control={
                    <Switch 
                      checked={settings.telegramNotifications}
                      onChange={(e) => handleSettingChange('telegramNotifications', e.target.checked)}
                    />
                  }
                  label="Telegram Notifications"
                  sx={{ mb: 1, display: 'block' }}
                />

                <FormControlLabel
                  control={
                    <Switch 
                      checked={settings.soundAlerts}
                      onChange={(e) => handleSettingChange('soundAlerts', e.target.checked)}
                    />
                  }
                  label="Sound Alerts"
                  sx={{ display: 'block' }}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
            <Button variant="contained" onClick={() => setSettingsOpen(false)}>
              Save Settings
            </Button>
          </DialogActions>
        </Dialog>

        {/* Confirmation Dialog */}
        <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, action: '', message: '' })}>
          <DialogTitle>
            {confirmDialog.action === 'emergency' ? 'Emergency Stop' : 'Confirm Action'}
          </DialogTitle>
          <DialogContent>
            <Alert severity={confirmDialog.action === 'emergency' ? 'error' : 'warning'}>
              {confirmDialog.message}
            </Alert>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setConfirmDialog({ open: false, action: '', message: '' })}>
              Cancel
            </Button>
            <Button 
              variant="contained" 
              color={confirmDialog.action === 'emergency' ? 'error' : 'primary'}
              onClick={handleConfirmAction}
            >
              Confirm
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default ControlPanel;