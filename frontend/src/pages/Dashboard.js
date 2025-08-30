import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Speed,
  Timeline,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { botAPI } from '../api/botAPI';
import { useBotStatus } from '../hooks/useBotStatus';

const MetricCard = ({ title, value, change, icon: Icon, color = 'primary' }) => (
  <Paper sx={{ p: 3, height: '100%', bgcolor: '#1e2329' }}>
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
      <Typography variant="h6" sx={{ color: '#848e9c', fontSize: '0.9rem' }}>
        {title}
      </Typography>
      <Icon sx={{ color: color === 'success' ? '#00d4aa' : color === 'error' ? '#f6465d' : '#f0b90b' }} />
    </Box>
    <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
      {value}
    </Typography>
    {change && (
      <Chip
        label={`${change > 0 ? '+' : ''}${change.toFixed(2)}%`}
        size="small"
        color={change > 0 ? 'success' : 'error'}
        sx={{ fontWeight: 600 }}
      />
    )}
  </Paper>
);

const Dashboard = () => {
  const { botStatus } = useBotStatus();
  const [positions, setPositions] = useState([]);
  const [performance, setPerformance] = useState({ data: [], totalReturn: 0, winRate: 0, sharpeRatio: 0 });
  const [marketData, setMarketData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [positionsData, performanceData, marketDataResponse] = await Promise.all([
          botAPI.getPositions(),
          botAPI.getPerformance('24h'),
          botAPI.getMarketData(['ETHUSDT', 'SOLUSDT', 'LINKUSDT', 'BTCUSDT']),
        ]);

        setPositions(positionsData);
        setPerformance(performanceData);
        setMarketData(marketDataResponse);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Trading Dashboard
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Balance"
            value={`$${botStatus.balance?.toLocaleString() || '0'}`}
            icon={AccountBalance}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total P&L"
            value={`$${botStatus.pnl?.toFixed(2) || '0.00'}`}
            change={performance.totalReturn}
            icon={performance.totalReturn > 0 ? TrendingUp : TrendingDown}
            color={performance.totalReturn > 0 ? 'success' : 'error'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Win Rate"
            value={`${performance.winRate?.toFixed(1) || '0.0'}%`}
            icon={Speed}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Positions"
            value={positions.length}
            icon={Timeline}
            color="primary"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Performance Chart */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Performance (24h)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performance.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2b3139" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  stroke="#848e9c"
                />
                <YAxis stroke="#848e9c" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e2329',
                    border: '1px solid #2b3139',
                    borderRadius: '4px',
                  }}
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                />
                <Line
                  type="monotone"
                  dataKey="balance"
                  stroke="#f0b90b"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Market Overview */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Market Overview
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {marketData.slice(0, 4).map((market, index) => (
                <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {market.symbol}
                  </Typography>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      ${market.price?.toFixed(2)}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{ color: market.change24h > 0 ? '#00d4aa' : '#f6465d' }}
                    >
                      {market.change24h > 0 ? '+' : ''}{market.change24h?.toFixed(2)}%
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Active Positions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Active Positions
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell align="right">Size</TableCell>
                    <TableCell align="right">Entry Price</TableCell>
                    <TableCell align="right">Mark Price</TableCell>
                    <TableCell align="right">P&L</TableCell>
                    <TableCell align="right">P&L %</TableCell>
                    <TableCell align="right">Leverage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {positions.length > 0 ? (
                    positions.map((position, index) => (
                      <TableRow key={index}>
                        <TableCell sx={{ fontWeight: 600 }}>{position.symbol}</TableCell>
                        <TableCell>
                          <Chip
                            label={position.side.toUpperCase()}
                            size="small"
                            color={position.side === 'long' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell align="right">{position.size}</TableCell>
                        <TableCell align="right">${position.entryPrice?.toFixed(2)}</TableCell>
                        <TableCell align="right">${position.markPrice?.toFixed(2)}</TableCell>
                        <TableCell
                          align="right"
                          sx={{ color: position.pnl > 0 ? '#00d4aa' : '#f6465d' }}
                        >
                          ${position.pnl?.toFixed(2)}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{ color: position.pnlPercent > 0 ? '#00d4aa' : '#f6465d' }}
                        >
                          {position.pnlPercent > 0 ? '+' : ''}{position.pnlPercent?.toFixed(2)}%
                        </TableCell>
                        <TableCell align="right">{position.leverage}x</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 4, color: '#848e9c' }}>
                        No active positions
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;