import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Card,
  CardContent,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Timeline,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { botAPI } from '../api/botAPI';

const CorrelationCard = ({ pair, correlation, change }) => (
  <Card sx={{ bgcolor: '#1e2329', height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          {pair}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {change > 0 ? <TrendingUp sx={{ color: '#00d4aa' }} /> : <TrendingDown sx={{ color: '#f6465d' }} />}
          <Typography
            variant="body2"
            sx={{ color: change > 0 ? '#00d4aa' : '#f6465d', fontWeight: 600 }}
          >
            {change > 0 ? '+' : ''}{change.toFixed(2)}%
          </Typography>
        </Box>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          {correlation.toFixed(3)}
        </Typography>
        <Chip
          label={Math.abs(correlation) > 0.7 ? 'Strong' : Math.abs(correlation) > 0.3 ? 'Moderate' : 'Weak'}
          size="small"
          color={Math.abs(correlation) > 0.7 ? 'success' : Math.abs(correlation) > 0.3 ? 'warning' : 'error'}
        />
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.abs(correlation) * 100}
        sx={{
          mt: 2,
          bgcolor: '#2b3139',
          '& .MuiLinearProgress-bar': {
            bgcolor: correlation > 0 ? '#00d4aa' : '#f6465d',
          },
        }}
      />
    </CardContent>
  </Card>
);

const TradingView = () => {
  const [trades, setTrades] = useState([]);
  const [marketData, setMarketData] = useState([]);
  const [correlationData, setCorrelationData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tradesData, marketDataResponse] = await Promise.all([
          botAPI.getTrades(50),
          botAPI.getMarketData(['ETHUSDT', 'SOLUSDT', 'LINKUSDT', 'BTCUSDT', 'BNBUSDT', 'ADAUSDT']),
        ]);

        setTrades(tradesData);
        setMarketData(marketDataResponse);
        
        // Generate correlation data
        const correlationMockData = marketDataResponse.map(market => ({
          symbol: market.symbol,
          correlation: Math.random() * 2 - 1, // -1 to 1
          change: (Math.random() - 0.5) * 10,
        }));
        setCorrelationData(correlationMockData);
      } catch (error) {
        console.error('Failed to fetch trading data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 15000);
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
        Trading Analysis
      </Typography>

      {/* Correlation Matrix */}
      <Paper sx={{ p: 3, mb: 4, bgcolor: '#1e2329' }}>
        <Typography variant="h6" sx={{ mb: 3 }}>
          Correlation Analysis
        </Typography>
        <Grid container spacing={3}>
          {correlationData.slice(0, 6).map((item, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <CorrelationCard
                pair={item.symbol}
                correlation={item.correlation}
                change={item.change}
              />
            </Grid>
          ))}
        </Grid>
      </Paper>

      <Grid container spacing={3}>
        {/* Market Data Chart */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Price Action
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={marketData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2b3139" />
                <XAxis dataKey="symbol" stroke="#848e9c" />
                <YAxis stroke="#848e9c" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e2329',
                    border: '1px solid #2b3139',
                    borderRadius: '4px',
                  }}
                />
                <Bar
                  dataKey="change24h"
                  fill={(entry) => entry.change24h > 0 ? '#00d4aa' : '#f6465d'}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Trading Stats
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>
                  Total Trades Today
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  {trades.filter(trade => {
                    const today = new Date();
                    const tradeDate = new Date(trade.timestamp);
                    return tradeDate.toDateString() === today.toDateString();
                  }).length}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>
                  Average Hold Time
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  2.4h
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>
                  Best Performing Pair
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 600, color: '#00d4aa' }}>
                  ETHUSDT
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>
                  Risk Level
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={65}
                    sx={{
                      flex: 1,
                      bgcolor: '#2b3139',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: '#f0b90b',
                      },
                    }}
                  />
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    65%
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Trades */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Recent Trades
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell align="right">Size</TableCell>
                    <TableCell align="right">Entry Price</TableCell>
                    <TableCell align="right">Exit Price</TableCell>
                    <TableCell align="right">P&L</TableCell>
                    <TableCell align="right">P&L %</TableCell>
                    <TableCell align="right">Duration</TableCell>
                    <TableCell align="right">Time</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trades.slice(0, 10).map((trade, index) => (
                    <TableRow key={index}>
                      <TableCell sx={{ fontWeight: 600 }}>{trade.symbol}</TableCell>
                      <TableCell>
                        <Chip
                          label={trade.side.toUpperCase()}
                          size="small"
                          color={trade.side === 'long' ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell align="right">{trade.size}</TableCell>
                      <TableCell align="right">${trade.entryPrice?.toFixed(2)}</TableCell>
                      <TableCell align="right">${trade.exitPrice?.toFixed(2)}</TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: trade.pnl > 0 ? '#00d4aa' : '#f6465d' }}
                      >
                        ${trade.pnl?.toFixed(2)}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: trade.pnlPercent > 0 ? '#00d4aa' : '#f6465d' }}
                      >
                        {trade.pnlPercent > 0 ? '+' : ''}{trade.pnlPercent?.toFixed(2)}%
                      </TableCell>
                      <TableCell align="right">{trade.duration}</TableCell>
                      <TableCell align="right">
                        {new Date(trade.timestamp).toLocaleTimeString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TradingView;