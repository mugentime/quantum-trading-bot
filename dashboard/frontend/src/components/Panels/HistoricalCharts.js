import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  ToggleButtonGroup,
  ToggleButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Tooltip,
  IconButton,
  Paper
} from '@mui/material';
import {
  ShowChart,
  TrendingUp,
  Assessment,
  Timeline,
  Fullscreen,
  ZoomIn,
  ZoomOut
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Bar,
  ReferenceLine
} from 'recharts';
import { format, subDays, subHours, subMinutes } from 'date-fns';
import { usePerformance, useDashboardStore } from '../../stores/dashboardStore';

const HistoricalCharts = () => {
  const performance = usePerformance();
  const { equityCurve, selectedTimeframe, setSelectedTimeframe } = useDashboardStore();
  const [chartType, setChartType] = useState('equity');
  const [period, setPeriod] = useState('24h');

  // Generate historical data
  const chartData = useMemo(() => {
    const now = new Date();
    const dataPoints = [];
    
    // Determine time range and interval
    const { startTime, interval } = (() => {
      switch (period) {
        case '1h':
          return { startTime: subHours(now, 1), interval: 60000 }; // 1 minute
        case '4h':
          return { startTime: subHours(now, 4), interval: 240000 }; // 4 minutes
        case '24h':
          return { startTime: subHours(now, 24), interval: 900000 }; // 15 minutes
        case '7d':
          return { startTime: subDays(now, 7), interval: 3600000 }; // 1 hour
        case '30d':
          return { startTime: subDays(now, 30), interval: 14400000 }; // 4 hours
        default:
          return { startTime: subHours(now, 24), interval: 900000 };
      }
    })();

    const startBalance = 10000;
    let currentTime = startTime;
    let currentBalance = startBalance;
    let currentDrawdown = 0;
    let maxBalance = startBalance;
    let totalPnL = 0;

    while (currentTime < now) {
      // Simulate realistic trading data
      const randomChange = (Math.random() - 0.5) * 2; // -1% to +1%
      const pnlChange = currentBalance * (randomChange / 100);
      
      currentBalance += pnlChange;
      totalPnL += pnlChange;
      
      if (currentBalance > maxBalance) {
        maxBalance = currentBalance;
        currentDrawdown = 0;
      } else {
        currentDrawdown = ((maxBalance - currentBalance) / maxBalance) * 100;
      }

      dataPoints.push({
        timestamp: currentTime.getTime(),
        time: format(currentTime, period === '1h' || period === '4h' ? 'HH:mm' : 
                     period === '24h' ? 'HH:mm' : 'MMM dd'),
        equity: currentBalance,
        balance: startBalance,
        pnl: totalPnL,
        drawdown: currentDrawdown,
        returns: ((currentBalance - startBalance) / startBalance) * 100,
        volume: Math.random() * 1000000, // Random volume
        trades: Math.floor(Math.random() * 10), // Random trade count
      });

      currentTime = new Date(currentTime.getTime() + interval);
    }

    return dataPoints;
  }, [period]);

  const chartStats = useMemo(() => {
    if (chartData.length === 0) return {};

    const latest = chartData[chartData.length - 1];
    const first = chartData[0];
    
    return {
      totalReturn: ((latest.equity - first.equity) / first.equity) * 100,
      maxDrawdown: Math.max(...chartData.map(d => d.drawdown)),
      totalTrades: chartData.reduce((sum, d) => sum + d.trades, 0),
      winRate: 65.5, // Mock win rate
      sharpeRatio: 1.2, // Mock Sharpe ratio
      maxEquity: Math.max(...chartData.map(d => d.equity)),
      minEquity: Math.min(...chartData.map(d => d.equity))
    };
  }, [chartData]);

  const formatTooltipValue = (value, name) => {
    if (name === 'equity' || name === 'balance' || name === 'pnl') {
      return [`$${value.toFixed(2)}`, name.charAt(0).toUpperCase() + name.slice(1)];
    }
    if (name === 'drawdown' || name === 'returns') {
      return [`${value.toFixed(2)}%`, name.charAt(0).toUpperCase() + name.slice(1)];
    }
    return [value, name];
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Paper elevation={3} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle2" mb={1}>
            {label}
          </Typography>
          {payload.map((entry, index) => (
            <Typography 
              key={index}
              variant="body2" 
              sx={{ color: entry.color }}
            >
              {entry.name}: {formatTooltipValue(entry.value, entry.dataKey)[0]}
            </Typography>
          ))}
        </Paper>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      width: '100%',
      height: 300,
      data: chartData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    switch (chartType) {
      case 'equity':
        return (
          <ResponsiveContainer {...commonProps}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00e676" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00e676" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="#666" fontSize={12} />
              <YAxis stroke="#666" fontSize={12} />
              <RechartsTooltip content={<CustomTooltip />} />
              <ReferenceLine y={chartStats.minEquity} stroke="#ff1744" strokeDasharray="2 2" />
              <ReferenceLine y={chartStats.maxEquity} stroke="#00e676" strokeDasharray="2 2" />
              <Area 
                type="monotone" 
                dataKey="equity" 
                stroke="#00e676" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#equityGradient)" 
              />
              <Line 
                type="monotone" 
                dataKey="balance" 
                stroke="#1976d2" 
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pnl':
        return (
          <ResponsiveContainer {...commonProps}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="#666" fontSize={12} />
              <YAxis stroke="#666" fontSize={12} />
              <RechartsTooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="#666" />
              <Bar 
                dataKey="pnl" 
                fill={(entry) => entry.pnl >= 0 ? '#00e676' : '#ff1744'}
                opacity={0.7}
              />
              <Line 
                type="monotone" 
                dataKey="pnl" 
                stroke="#ffb300" 
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        );

      case 'drawdown':
        return (
          <ResponsiveContainer {...commonProps}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff1744" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ff1744" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="#666" fontSize={12} />
              <YAxis stroke="#666" fontSize={12} />
              <RechartsTooltip content={<CustomTooltip />} />
              <ReferenceLine y={15} stroke="#ff8800" strokeDasharray="2 2" />
              <Area 
                type="monotone" 
                dataKey="drawdown" 
                stroke="#ff1744" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#drawdownGradient)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'returns':
        return (
          <ResponsiveContainer {...commonProps}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="#666" fontSize={12} />
              <YAxis stroke="#666" fontSize={12} />
              <RechartsTooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="#666" />
              <Line 
                type="monotone" 
                dataKey="returns" 
                stroke="#1976d2" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            Historical Performance
          </Typography>
          <Box display="flex" gap={1} alignItems="center">
            <IconButton size="small">
              <ZoomIn fontSize="small" />
            </IconButton>
            <IconButton size="small">
              <Fullscreen fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {/* Controls */}
        <Grid container spacing={2} mb={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <ToggleButtonGroup
              value={chartType}
              exclusive
              onChange={(e, value) => value && setChartType(value)}
              size="small"
            >
              <ToggleButton value="equity">
                <ShowChart fontSize="small" sx={{ mr: 0.5 }} />
                Equity
              </ToggleButton>
              <ToggleButton value="pnl">
                <Assessment fontSize="small" sx={{ mr: 0.5 }} />
                P&L
              </ToggleButton>
              <ToggleButton value="drawdown">
                <TrendingUp fontSize="small" sx={{ mr: 0.5 }} />
                Drawdown
              </ToggleButton>
              <ToggleButton value="returns">
                <Timeline fontSize="small" sx={{ mr: 0.5 }} />
                Returns
              </ToggleButton>
            </ToggleButtonGroup>
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <FormControl size="small" fullWidth>
              <InputLabel>Period</InputLabel>
              <Select
                value={period}
                label="Period"
                onChange={(e) => setPeriod(e.target.value)}
              >
                <MenuItem value="1h">1 Hour</MenuItem>
                <MenuItem value="4h">4 Hours</MenuItem>
                <MenuItem value="24h">24 Hours</MenuItem>
                <MenuItem value="7d">7 Days</MenuItem>
                <MenuItem value="30d">30 Days</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Performance Statistics */}
        <Grid container spacing={2} mb={2}>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color={chartStats.totalReturn >= 0 ? 'success.main' : 'error.main'}>
                {chartStats.totalReturn >= 0 ? '+' : ''}{chartStats.totalReturn?.toFixed(2)}%
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Total Return
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color="error.main">
                {chartStats.maxDrawdown?.toFixed(2)}%
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Max Drawdown
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color="info.main">
                {chartStats.sharpeRatio?.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Sharpe Ratio
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" color="primary.main">
                {chartStats.winRate?.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Win Rate
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Chart */}
        <Box sx={{ height: 350, width: '100%' }}>
          {renderChart()}
        </Box>

        {/* Chart Legend */}
        <Box display="flex" justifyContent="center" gap={3} mt={2} flexWrap="wrap">
          {chartType === 'equity' && (
            <>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Box sx={{ width: 16, height: 2, bgcolor: '#00e676' }} />
                <Typography variant="caption">Equity Curve</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Box sx={{ width: 16, height: 2, bgcolor: '#1976d2', borderStyle: 'dashed' }} />
                <Typography variant="caption">Starting Balance</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Box sx={{ width: 16, height: 2, bgcolor: '#00e676', borderStyle: 'dashed' }} />
                <Typography variant="caption">All-Time High</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Box sx={{ width: 16, height: 2, bgcolor: '#ff1744', borderStyle: 'dashed' }} />
                <Typography variant="caption">All-Time Low</Typography>
              </Box>
            </>
          )}
          
          {chartType === 'drawdown' && (
            <>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Box sx={{ width: 16, height: 2, bgcolor: '#ff1744' }} />
                <Typography variant="caption">Drawdown</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Box sx={{ width: 16, height: 2, bgcolor: '#ff8800', borderStyle: 'dashed' }} />
                <Typography variant="caption">15% Risk Level</Typography>
              </Box>
            </>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default HistoricalCharts;