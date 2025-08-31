import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
  Alert
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Remove,
  PlayArrow,
  Pause,
  Refresh,
  FilterList,
  TrendingFlat,
  Timeline
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useSignals, usePriceData, useDashboardStore } from '../../stores/dashboardStore';

const SignalAnalysis = () => {
  const signals = useSignals();
  const priceData = usePriceData();
  const { isConnected } = useDashboardStore();
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('confidence');

  // Process and filter signals
  const processedSignals = useMemo(() => {
    let filtered = signals;
    
    // Apply filters
    if (filter === 'buy') {
      filtered = filtered.filter(signal => signal.action === 'buy');
    } else if (filter === 'sell') {
      filtered = filtered.filter(signal => signal.action === 'sell');
    } else if (filter === 'high-confidence') {
      filtered = filtered.filter(signal => signal.confidence > 0.7);
    }
    
    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'confidence':
          return b.confidence - a.confidence;
        case 'volatility':
          return b.volatility - a.volatility;
        case 'correlation':
          return Math.abs(b.correlation) - Math.abs(a.correlation);
        case 'expected_move':
          return Math.abs(b.expected_move) - Math.abs(a.expected_move);
        case 'timestamp':
          return new Date(b.timestamp) - new Date(a.timestamp);
        default:
          return 0;
      }
    });
    
    return filtered;
  }, [signals, filter, sortBy]);

  // Calculate summary statistics
  const signalStats = useMemo(() => {
    const buySignals = signals.filter(s => s.action === 'buy');
    const sellSignals = signals.filter(s => s.action === 'sell');
    const highConfidence = signals.filter(s => s.confidence > 0.7);
    const avgConfidence = signals.length > 0 ? 
      signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length : 0;
    const avgVolatility = signals.length > 0 ?
      signals.reduce((sum, s) => sum + s.volatility, 0) / signals.length : 0;
    
    return {
      total: signals.length,
      buy: buySignals.length,
      sell: sellSignals.length,
      highConfidence: highConfidence.length,
      avgConfidence: avgConfidence * 100,
      avgVolatility,
      strongSignals: signals.filter(s => s.confidence > 0.8 && Math.abs(s.correlation) > 0.6).length
    };
  }, [signals]);

  const getActionIcon = (action) => {
    switch (action) {
      case 'buy':
        return <TrendingUp color="success" />;
      case 'sell':
        return <TrendingDown color="error" />;
      default:
        return <TrendingFlat color="disabled" />;
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'buy':
        return 'success.main';
      case 'sell':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return 'success.main';
    if (confidence > 0.6) return 'info.main';
    if (confidence > 0.4) return 'warning.main';
    return 'text.secondary';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence > 0.8) return 'Very High';
    if (confidence > 0.6) return 'High';
    if (confidence > 0.4) return 'Medium';
    if (confidence > 0.2) return 'Low';
    return 'Very Low';
  };

  const formatPercent = (value) => `${(value * 100).toFixed(1)}%`;

  const SignalStrengthMeter = ({ confidence, volatility, correlation }) => {
    const strength = confidence * (volatility / 100) * Math.abs(correlation);
    const normalizedStrength = Math.min(strength * 10, 1); // Normalize to 0-1
    
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
          <Typography variant="caption" color="textSecondary">
            Signal Strength
          </Typography>
          <Typography variant="caption">
            {(normalizedStrength * 100).toFixed(0)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={normalizedStrength * 100}
          sx={{
            height: 4,
            borderRadius: 1,
            bgcolor: 'action.hover',
            '& .MuiLinearProgress-bar': {
              bgcolor: normalizedStrength > 0.7 ? 'success.main' :
                      normalizedStrength > 0.4 ? 'warning.main' : 'error.main'
            }
          }}
        />
      </Box>
    );
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            Signal Analysis
          </Typography>
          <Box display="flex" gap={1} alignItems="center">
            <Tooltip title="Connection Status">
              <Chip 
                label={isConnected ? 'Live' : 'Offline'}
                size="small"
                color={isConnected ? 'success' : 'error'}
                variant="outlined"
              />
            </Tooltip>
            <IconButton size="small" onClick={() => window.location.reload()}>
              <Refresh fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {/* Signal Statistics */}
        <Grid container spacing={1} sx={{ mb: 2 }}>
          <Grid item xs={6}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color="success.main" fontWeight="bold">
                {signalStats.buy}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Buy Signals
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color="error.main" fontWeight="bold">
                {signalStats.sell}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Sell Signals
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color="primary.main" fontWeight="bold">
                {signalStats.highConfidence}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                High Confidence
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color="info.main" fontWeight="bold">
                {signalStats.avgConfidence.toFixed(0)}%
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Avg Confidence
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Filters */}
        <Box display="flex" gap={1} alignItems="center" mb={2} flexWrap="wrap">
          <ToggleButtonGroup
            value={filter}
            exclusive
            onChange={(e, value) => value && setFilter(value)}
            size="small"
          >
            <ToggleButton value="all">All</ToggleButton>
            <ToggleButton value="buy">Buy</ToggleButton>
            <ToggleButton value="sell">Sell</ToggleButton>
            <ToggleButton value="high-confidence">High Conf.</ToggleButton>
          </ToggleButtonGroup>

          <ToggleButtonGroup
            value={sortBy}
            exclusive
            onChange={(e, value) => value && setSortBy(value)}
            size="small"
          >
            <ToggleButton value="confidence">Confidence</ToggleButton>
            <ToggleButton value="volatility">Volatility</ToggleButton>
            <ToggleButton value="timestamp">Time</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {processedSignals.length === 0 ? (
          <Alert severity="info">
            No signals available. Check connection status and trading pairs configuration.
          </Alert>
        ) : (
          <TableContainer sx={{ maxHeight: 400 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell align="center">Confidence</TableCell>
                  <TableCell align="right">Entry</TableCell>
                  <TableCell align="right">Target</TableCell>
                  <TableCell align="right">Stop</TableCell>
                  <TableCell align="center">Strength</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {processedSignals.slice(0, 10).map((signal, index) => {
                  const currentPrice = priceData[signal.symbol]?.last || signal.entry_price;
                  const potentialReturn = signal.action === 'buy' 
                    ? ((signal.take_profit - signal.entry_price) / signal.entry_price) * 100
                    : ((signal.entry_price - signal.take_profit) / signal.entry_price) * 100;
                  const riskReturn = signal.action === 'buy'
                    ? ((signal.entry_price - signal.stop_loss) / signal.entry_price) * 100
                    : ((signal.stop_loss - signal.entry_price) / signal.entry_price) * 100;
                  
                  return (
                    <TableRow 
                      key={`${signal.symbol}-${index}`} 
                      hover
                      sx={{ 
                        bgcolor: signal.confidence > 0.7 ? 
                          (theme) => theme.palette.action.selected : 'inherit'
                      }}
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontWeight="bold">
                            {signal.symbol}
                          </Typography>
                          {signal.confidence > 0.8 && (
                            <Timeline fontSize="small" color="primary" />
                          )}
                        </Box>
                        <Typography variant="caption" color="textSecondary">
                          {format(new Date(signal.timestamp), 'HH:mm')}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getActionIcon(signal.action)}
                          <Chip
                            label={signal.action.toUpperCase()}
                            size="small"
                            sx={{ 
                              bgcolor: getActionColor(signal.action),
                              color: 'white',
                              fontWeight: 'bold',
                              minWidth: 50
                            }}
                          />
                        </Box>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Box>
                          <Chip
                            label={getConfidenceLabel(signal.confidence)}
                            size="small"
                            variant="outlined"
                            sx={{ 
                              color: getConfidenceColor(signal.confidence),
                              borderColor: getConfidenceColor(signal.confidence),
                              fontSize: '0.7rem'
                            }}
                          />
                          <Typography variant="caption" display="block" mt={0.5}>
                            {formatPercent(signal.confidence)}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="bold">
                          ${signal.entry_price.toFixed(2)}
                        </Typography>
                        <Typography 
                          variant="caption" 
                          color={currentPrice > signal.entry_price ? 'success.main' : 'error.main'}
                        >
                          Now: ${currentPrice.toFixed(2)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2" color="success.main">
                          ${signal.take_profit.toFixed(2)}
                        </Typography>
                        <Typography variant="caption" color="success.main">
                          +{potentialReturn.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2" color="error.main">
                          ${signal.stop_loss.toFixed(2)}
                        </Typography>
                        <Typography variant="caption" color="error.main">
                          -{Math.abs(riskReturn).toFixed(1)}%
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Box width={80}>
                          <SignalStrengthMeter 
                            confidence={signal.confidence}
                            volatility={signal.volatility}
                            correlation={signal.correlation}
                          />
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Signal Quality Summary */}
        <Box mt={2} p={1} bgcolor="action.hover" borderRadius={1}>
          <Typography variant="caption" color="textSecondary" display="block" mb={1}>
            Signal Quality Summary
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={4}>
              <Typography variant="caption">
                Strong: {signalStats.strongSignals}
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption">
                Avg Vol: {signalStats.avgVolatility.toFixed(1)}%
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption">
                Active: {processedSignals.length}
              </Typography>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SignalAnalysis;