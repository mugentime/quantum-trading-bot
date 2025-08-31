import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Chip,
  Divider,
  IconButton,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  ShowChart,
  Timeline,
  Info,
  Refresh
} from '@mui/icons-material';
import { usePerformance, useDashboardStore } from '../../stores/dashboardStore';

const PerformanceMetrics = () => {
  const performance = usePerformance();
  const { equityCurve, lastUpdate } = useDashboardStore();
  const [timeframe, setTimeframe] = useState('today');
  const [view, setView] = useState('overview');

  // Calculate performance metrics based on timeframe
  const metrics = useMemo(() => {
    const pnl = performance.total_pnl || 0;
    const dailyPnl = performance.daily_pnl || 0;
    const weeklyPnl = performance.weekly_pnl || 0;
    const monthlyPnl = performance.monthly_pnl || 0;
    const balance = performance.balance || 10000;
    
    return {
      currentPnL: timeframe === 'today' ? dailyPnl :
                  timeframe === 'week' ? weeklyPnl :
                  timeframe === 'month' ? monthlyPnl : pnl,
      
      roi: ((balance - 10000) / 10000) * 100,
      winRate: performance.win_rate || 0,
      profitFactor: performance.profit_factor || 0,
      sharpeRatio: performance.sharpe_ratio || 0,
      maxDrawdown: performance.max_drawdown || 0,
      currentDrawdown: performance.current_drawdown || 0,
      totalTrades: performance.total_trades || 0,
      winningTrades: performance.winning_trades || 0,
      losingTrades: performance.losing_trades || 0,
      avgWin: performance.avg_win || 0,
      avgLoss: performance.avg_loss || 0,
      bestTrade: performance.best_trade || 0,
      worstTrade: performance.worst_trade || 0,
    };
  }, [performance, timeframe]);

  const getPerformanceColor = (value, isPercentage = false) => {
    if (value > (isPercentage ? 0 : 0)) return 'success.main';
    if (value < (isPercentage ? 0 : 0)) return 'error.main';
    return 'text.primary';
  };

  const getDrawdownColor = (drawdown) => {
    if (drawdown > 15) return 'error.main';
    if (drawdown > 10) return 'warning.main';
    return 'success.main';
  };

  const getRiskLevel = () => {
    const marginLevel = performance.margin_level || 100;
    const drawdown = metrics.currentDrawdown;
    
    if (marginLevel < 150 || drawdown > 15) return { level: 'High', color: 'error.main' };
    if (marginLevel < 300 || drawdown > 10) return { level: 'Medium', color: 'warning.main' };
    return { level: 'Low', color: 'success.main' };
  };

  const getGrade = () => {
    const score = (metrics.winRate * 0.3) + 
                  (Math.min(metrics.profitFactor * 20, 100) * 0.3) + 
                  (Math.max(0, 100 - metrics.maxDrawdown * 5) * 0.2) +
                  (Math.min(metrics.sharpeRatio * 50, 100) * 0.2);
    
    if (score >= 80) return { grade: 'A+', color: 'success.main' };
    if (score >= 70) return { grade: 'A', color: 'success.main' };
    if (score >= 60) return { grade: 'B', color: 'info.main' };
    if (score >= 50) return { grade: 'C', color: 'warning.main' };
    return { grade: 'D', color: 'error.main' };
  };

  const formatCurrency = (value) => {
    return `$${Math.abs(value).toFixed(2)}`;
  };

  const formatPercent = (value) => {
    return `${value.toFixed(2)}%`;
  };

  const MetricCard = ({ title, value, subtitle, icon, color, format = 'currency' }) => (
    <Box 
      sx={{ 
        p: 2, 
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
        height: '100%'
      }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="caption" color="textSecondary">
          {title}
        </Typography>
        {icon}
      </Box>
      <Typography 
        variant="h6" 
        fontWeight="bold"
        sx={{ color: color || 'text.primary' }}
      >
        {format === 'currency' ? formatCurrency(value) : 
         format === 'percent' ? formatPercent(value) :
         format === 'number' ? value.toFixed(format === 'integer' ? 0 : 2) : value}
      </Typography>
      {subtitle && (
        <Typography variant="caption" color="textSecondary">
          {subtitle}
        </Typography>
      )}
    </Box>
  );

  const risk = getRiskLevel();
  const grade = getGrade();

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            Performance Metrics
          </Typography>
          <Box display="flex" gap={1} alignItems="center">
            <Tooltip title="Last Updated">
              <Typography variant="caption" color="textSecondary">
                {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : 'Never'}
              </Typography>
            </Tooltip>
            <IconButton size="small" onClick={() => window.location.reload()}>
              <Refresh fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {/* Timeframe Selector */}
        <Box display="flex" justifyContent="center" mb={2}>
          <ToggleButtonGroup
            value={timeframe}
            exclusive
            onChange={(e, value) => value && setTimeframe(value)}
            size="small"
          >
            <ToggleButton value="today">Today</ToggleButton>
            <ToggleButton value="week">Week</ToggleButton>
            <ToggleButton value="month">Month</ToggleButton>
            <ToggleButton value="all">All Time</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Key Performance Indicators */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6}>
            <MetricCard
              title="Total P&L"
              value={metrics.currentPnL}
              subtitle={`${metrics.currentPnL >= 0 ? '+' : ''}${formatPercent(metrics.roi)}`}
              icon={metrics.currentPnL >= 0 ? 
                <TrendingUp color="success" /> : 
                <TrendingDown color="error" />
              }
              color={getPerformanceColor(metrics.currentPnL)}
              format="currency"
            />
          </Grid>
          <Grid item xs={6}>
            <MetricCard
              title="Balance"
              value={performance.balance || 10000}
              subtitle={`Equity: ${formatCurrency(performance.equity || 10000)}`}
              icon={<Assessment color="primary" />}
              format="currency"
            />
          </Grid>
        </Grid>

        {/* Win Rate Progress */}
        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" fontWeight="bold">
              Win Rate
            </Typography>
            <Typography variant="body2" fontWeight="bold" color="primary.main">
              {formatPercent(metrics.winRate)}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={metrics.winRate}
            sx={{
              height: 8,
              borderRadius: 1,
              bgcolor: 'action.hover',
              '& .MuiLinearProgress-bar': {
                bgcolor: metrics.winRate > 60 ? 'success.main' : 
                        metrics.winRate > 40 ? 'warning.main' : 'error.main'
              }
            }}
          />
          <Box display="flex" justifyContent="space-between" mt={1}>
            <Typography variant="caption" color="textSecondary">
              {metrics.winningTrades} wins
            </Typography>
            <Typography variant="caption" color="textSecondary">
              {metrics.losingTrades} losses
            </Typography>
          </Box>
        </Box>

        {/* Detailed Metrics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6}>
            <MetricCard
              title="Profit Factor"
              value={metrics.profitFactor}
              subtitle={metrics.profitFactor > 1 ? 'Profitable' : 'Unprofitable'}
              color={metrics.profitFactor > 1 ? 'success.main' : 'error.main'}
              format="number"
            />
          </Grid>
          <Grid item xs={6}>
            <MetricCard
              title="Sharpe Ratio"
              value={metrics.sharpeRatio}
              subtitle={metrics.sharpeRatio > 1 ? 'Good' : 'Poor'}
              color={metrics.sharpeRatio > 1 ? 'success.main' : 'warning.main'}
              format="number"
            />
          </Grid>
        </Grid>

        {/* Drawdown Analysis */}
        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" fontWeight="bold">
              Current Drawdown
            </Typography>
            <Typography 
              variant="body2" 
              fontWeight="bold" 
              color={getDrawdownColor(metrics.currentDrawdown)}
            >
              {formatPercent(metrics.currentDrawdown)}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={(metrics.currentDrawdown / 25) * 100} // Max 25% shown as 100%
            sx={{
              height: 6,
              borderRadius: 1,
              bgcolor: 'action.hover',
              '& .MuiLinearProgress-bar': {
                bgcolor: getDrawdownColor(metrics.currentDrawdown)
              }
            }}
          />
          <Typography variant="caption" color="textSecondary" display="block" mt={1}>
            Max Drawdown: {formatPercent(metrics.maxDrawdown)}
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Risk Assessment */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="body2" color="textSecondary">
              Risk Level
            </Typography>
            <Chip 
              label={risk.level}
              size="small"
              sx={{ 
                bgcolor: risk.color,
                color: 'white',
                fontWeight: 'bold'
              }}
            />
          </Box>
          <Box textAlign="right">
            <Typography variant="body2" color="textSecondary">
              Performance Grade
            </Typography>
            <Chip 
              label={grade.grade}
              size="small"
              sx={{ 
                bgcolor: grade.color,
                color: 'white',
                fontWeight: 'bold',
                fontSize: '1rem'
              }}
            />
          </Box>
        </Box>

        {/* Trading Statistics */}
        <Box>
          <Typography variant="body2" fontWeight="bold" mb={1}>
            Trading Statistics
          </Typography>
          <Grid container spacing={1} sx={{ fontSize: '0.8rem' }}>
            <Grid item xs={6}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="caption" color="textSecondary">
                  Total Trades:
                </Typography>
                <Typography variant="caption">
                  {metrics.totalTrades}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="caption" color="textSecondary">
                  Avg Win:
                </Typography>
                <Typography variant="caption" color="success.main">
                  {formatCurrency(metrics.avgWin)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="caption" color="textSecondary">
                  Best Trade:
                </Typography>
                <Typography variant="caption" color="success.main">
                  {formatCurrency(metrics.bestTrade)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="caption" color="textSecondary">
                  Avg Loss:
                </Typography>
                <Typography variant="caption" color="error.main">
                  {formatCurrency(metrics.avgLoss)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="caption" color="textSecondary">
                  Worst Trade:
                </Typography>
                <Typography variant="caption" color="error.main">
                  {formatCurrency(metrics.worstTrade)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="caption" color="textSecondary">
                  ROI:
                </Typography>
                <Typography 
                  variant="caption" 
                  color={getPerformanceColor(metrics.roi, true)}
                >
                  {formatPercent(metrics.roi)}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PerformanceMetrics;