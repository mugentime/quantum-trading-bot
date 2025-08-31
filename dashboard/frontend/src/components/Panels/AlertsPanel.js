import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondary,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  Collapse,
  Badge,
  Switch,
  FormControlLabel,
  Divider,
  Button
} from '@mui/material';
import {
  Notifications,
  NotificationsOff,
  Warning,
  Error,
  Info,
  CheckCircle,
  TrendingUp,
  DeleteSweep,
  ExpandMore,
  ExpandLess,
  VolumeUp,
  VolumeOff,
  Circle,
  Clear
} from '@mui/icons-material';
import { format, isToday, isThisWeek, differenceInMinutes } from 'date-fns';
import { useAlerts, useDashboardStore } from '../../stores/dashboardStore';

const AlertsPanel = () => {
  const alerts = useAlerts();
  const { 
    soundEnabled, 
    setSoundEnabled, 
    clearAllAlerts, 
    markAlertRead,
    unreadAlerts 
  } = useDashboardStore();
  
  const [filter, setFilter] = useState('all');
  const [expanded, setExpanded] = useState(true);
  const [groupedView, setGroupedView] = useState(false);

  // Group alerts by type or time
  const processedAlerts = React.useMemo(() => {
    let filtered = alerts;

    // Apply filters
    switch (filter) {
      case 'unread':
        filtered = alerts.filter(alert => !alert.read);
        break;
      case 'critical':
        filtered = alerts.filter(alert => alert.priority === 'critical');
        break;
      case 'signals':
        filtered = alerts.filter(alert => alert.type === 'signal');
        break;
      case 'today':
        filtered = alerts.filter(alert => isToday(new Date(alert.timestamp)));
        break;
      default:
        break;
    }

    if (groupedView) {
      const grouped = {};
      filtered.forEach(alert => {
        const key = alert.type || 'general';
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(alert);
      });
      return grouped;
    }

    return filtered.slice(0, 50); // Limit to 50 most recent
  }, [alerts, filter, groupedView]);

  const alertStats = React.useMemo(() => {
    const today = alerts.filter(alert => isToday(new Date(alert.timestamp)));
    const critical = alerts.filter(alert => alert.priority === 'critical');
    const signals = alerts.filter(alert => alert.type === 'signal');
    const unread = alerts.filter(alert => !alert.read);

    return {
      total: alerts.length,
      today: today.length,
      critical: critical.length,
      signals: signals.length,
      unread: unread.length
    };
  }, [alerts]);

  const getAlertIcon = (alert) => {
    if (alert.type === 'signal') return <TrendingUp />;
    
    switch (alert.priority) {
      case 'critical':
        return <Error color="error" />;
      case 'high':
        return <Warning color="warning" />;
      case 'normal':
        return <Info color="info" />;
      default:
        return <CheckCircle color="success" />;
    }
  };

  const getAlertColor = (alert) => {
    if (alert.type === 'signal') return 'primary.main';
    
    switch (alert.priority) {
      case 'critical':
        return 'error.main';
      case 'high':
        return 'warning.main';
      case 'normal':
        return 'info.main';
      default:
        return 'success.main';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const minutesAgo = differenceInMinutes(now, date);

    if (minutesAgo < 1) return 'Just now';
    if (minutesAgo < 60) return `${minutesAgo}m ago`;
    if (isToday(date)) return format(date, 'HH:mm');
    if (isThisWeek(date)) return format(date, 'EEE HH:mm');
    return format(date, 'MMM dd HH:mm');
  };

  const AlertItem = ({ alert }) => (
    <ListItem
      sx={{
        bgcolor: !alert.read ? 'action.hover' : 'transparent',
        borderRadius: 1,
        mb: 0.5,
        border: alert.priority === 'critical' ? '1px solid' : 'none',
        borderColor: 'error.main',
        '&:hover': { bgcolor: 'action.selected' }
      }}
    >
      <ListItemIcon sx={{ minWidth: 36 }}>
        <Box position="relative">
          {getAlertIcon(alert)}
          {!alert.read && (
            <Circle 
              sx={{ 
                position: 'absolute', 
                top: -2, 
                right: -2, 
                fontSize: 8, 
                color: 'primary.main' 
              }} 
            />
          )}
        </Box>
      </ListItemIcon>
      
      <ListItemText
        primary={
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: !alert.read ? 'bold' : 'normal',
                color: !alert.read ? 'text.primary' : 'text.secondary'
              }}
            >
              {alert.message}
            </Typography>
            <Box display="flex" gap={0.5} alignItems="center">
              <Chip
                label={alert.type || 'info'}
                size="small"
                variant="outlined"
                sx={{ 
                  fontSize: '0.7rem',
                  height: 20,
                  color: getAlertColor(alert),
                  borderColor: getAlertColor(alert)
                }}
              />
              <Typography variant="caption" color="textSecondary">
                {formatTimestamp(alert.timestamp)}
              </Typography>
            </Box>
          </Box>
        }
        secondary={
          alert.priority === 'critical' && (
            <Typography variant="caption" color="error.main" fontWeight="bold">
              CRITICAL: Immediate attention required
            </Typography>
          )
        }
      />
      
      <Box>
        <Tooltip title={alert.read ? "Mark as unread" : "Mark as read"}>
          <IconButton 
            size="small"
            onClick={() => markAlertRead(alert.id)}
          >
            <Clear fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </ListItem>
  );

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Badge badgeContent={alertStats.unread} color="error">
              <Notifications />
            </Badge>
            <Typography variant="h6" fontWeight="bold">
              Alerts
            </Typography>
          </Box>
          
          <Box display="flex" gap={0.5} alignItems="center">
            <Tooltip title={soundEnabled ? "Disable sound" : "Enable sound"}>
              <IconButton 
                size="small"
                onClick={() => setSoundEnabled(!soundEnabled)}
              >
                {soundEnabled ? <VolumeUp fontSize="small" /> : <VolumeOff fontSize="small" />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Clear all alerts">
              <IconButton 
                size="small"
                onClick={clearAllAlerts}
                disabled={alerts.length === 0}
              >
                <DeleteSweep fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title={expanded ? "Collapse" : "Expand"}>
              <IconButton size="small" onClick={() => setExpanded(!expanded)}>
                {expanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Alert Statistics */}
        <Box display="flex" gap={1} mb={2} flexWrap="wrap">
          <Chip
            label={`Total: ${alertStats.total}`}
            size="small"
            onClick={() => setFilter('all')}
            color={filter === 'all' ? 'primary' : 'default'}
          />
          <Chip
            label={`Unread: ${alertStats.unread}`}
            size="small"
            onClick={() => setFilter('unread')}
            color={filter === 'unread' ? 'primary' : 'default'}
          />
          <Chip
            label={`Critical: ${alertStats.critical}`}
            size="small"
            onClick={() => setFilter('critical')}
            color={filter === 'critical' ? 'error' : 'default'}
          />
          <Chip
            label={`Signals: ${alertStats.signals}`}
            size="small"
            onClick={() => setFilter('signals')}
            color={filter === 'signals' ? 'primary' : 'default'}
          />
          <Chip
            label={`Today: ${alertStats.today}`}
            size="small"
            onClick={() => setFilter('today')}
            color={filter === 'today' ? 'primary' : 'default'}
          />
        </Box>

        <Collapse in={expanded}>
          {/* Controls */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <FormControlLabel
              control={
                <Switch 
                  size="small"
                  checked={groupedView}
                  onChange={(e) => setGroupedView(e.target.checked)}
                />
              }
              label={<Typography variant="caption">Group by type</Typography>}
            />
            
            <FormControlLabel
              control={
                <Switch 
                  size="small"
                  checked={soundEnabled}
                  onChange={(e) => setSoundEnabled(e.target.checked)}
                />
              }
              label={<Typography variant="caption">Sound alerts</Typography>}
            />
          </Box>

          <Divider sx={{ mb: 2 }} />

          {/* Alert List */}
          <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
            {alerts.length === 0 ? (
              <Alert severity="info">
                No alerts yet. System alerts and trading signals will appear here.
              </Alert>
            ) : groupedView ? (
              Object.entries(processedAlerts).map(([type, typeAlerts]) => (
                <Box key={type} mb={2}>
                  <Typography variant="subtitle2" color="textSecondary" mb={1}>
                    {type.charAt(0).toUpperCase() + type.slice(1)} ({typeAlerts.length})
                  </Typography>
                  <List dense>
                    {typeAlerts.slice(0, 5).map((alert) => (
                      <AlertItem key={alert.id} alert={alert} />
                    ))}
                  </List>
                </Box>
              ))
            ) : (
              <List dense>
                {processedAlerts.map((alert) => (
                  <AlertItem key={alert.id} alert={alert} />
                ))}
              </List>
            )}
          </Box>

          {/* Quick Actions */}
          {alertStats.unread > 0 && (
            <Box mt={2} display="flex" gap={1} justifyContent="center">
              <Button 
                size="small" 
                variant="outlined"
                onClick={() => {
                  alerts.filter(a => !a.read).forEach(a => markAlertRead(a.id));
                }}
              >
                Mark All Read
              </Button>
              <Button 
                size="small" 
                variant="outlined"
                color="error"
                onClick={clearAllAlerts}
              >
                Clear All
              </Button>
            </Box>
          )}

          {/* Alert Settings */}
          <Box mt={2} p={1} bgcolor="action.hover" borderRadius={1}>
            <Typography variant="caption" color="textSecondary" display="block" mb={1}>
              Alert Settings
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="caption">
                Auto-clear after: 24h
              </Typography>
              <Typography variant="caption">
                Max alerts: 100
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default AlertsPanel;