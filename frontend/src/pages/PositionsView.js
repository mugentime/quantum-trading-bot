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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { botAPI } from '../api/botAPI';
import { toast } from 'react-toastify';

const COLORS = ['#00d4aa', '#f6465d', '#f0b90b', '#848e9c'];

const PositionDialog = ({ open, onClose, position, onUpdate }) => {
  const [stopLoss, setStopLoss] = useState(position?.stopLoss || '');
  const [takeProfit, setTakeProfit] = useState(position?.takeProfit || '');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (position) {
      setStopLoss(position.stopLoss || '');
      setTakeProfit(position.takeProfit || '');
    }
  }, [position]);

  const handleUpdate = async () => {
    setLoading(true);
    try {
      await botAPI.updatePosition(position.id, {
        stopLoss: parseFloat(stopLoss),
        takeProfit: parseFloat(takeProfit),
      });
      toast.success('Position updated successfully');
      onUpdate();
      onClose();
    } catch (error) {
      toast.error('Failed to update position');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = async () => {
    setLoading(true);
    try {
      await botAPI.closePosition(position.id);
      toast.success('Position closed successfully');
      onUpdate();
      onClose();
    } catch (error) {
      toast.error('Failed to close position');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Manage Position - {position?.symbol}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Box>
            <Typography variant="body2" sx={{ color: '#848e9c', mb: 1 }}>
              Position Details
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>Side</Typography>
                <Chip
                  label={position?.side?.toUpperCase()}
                  size="small"
                  color={position?.side === 'long' ? 'success' : 'error'}
                />
              </Box>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>Size</Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {position?.size}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>Entry Price</Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  ${position?.entryPrice?.toFixed(2)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ color: '#848e9c' }}>Mark Price</Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  ${position?.markPrice?.toFixed(2)}
                </Typography>
              </Box>
            </Box>
          </Box>

          <TextField
            label="Stop Loss"
            type="number"
            value={stopLoss}
            onChange={(e) => setStopLoss(e.target.value)}
            fullWidth
            variant="outlined"
            helperText="Set stop loss price to limit losses"
          />

          <TextField
            label="Take Profit"
            type="number"
            value={takeProfit}
            onChange={(e) => setTakeProfit(e.target.value)}
            fullWidth
            variant="outlined"
            helperText="Set take profit price to secure gains"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleClose}
          color="error"
          disabled={loading}
          startIcon={<CloseIcon />}
        >
          Close Position
        </Button>
        <Button
          onClick={handleUpdate}
          variant="contained"
          disabled={loading}
          startIcon={<EditIcon />}
        >
          Update Position
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const PositionsView = () => {
  const [positions, setPositions] = useState([]);
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [positionStats, setPositionStats] = useState({
    totalValue: 0,
    totalPnl: 0,
    longPositions: 0,
    shortPositions: 0,
  });

  const fetchPositions = async () => {
    try {
      const data = await botAPI.getPositions();
      setPositions(data);
      
      // Calculate stats
      const stats = data.reduce(
        (acc, position) => ({
          totalValue: acc.totalValue + (position.size * position.markPrice),
          totalPnl: acc.totalPnl + position.pnl,
          longPositions: acc.longPositions + (position.side === 'long' ? 1 : 0),
          shortPositions: acc.shortPositions + (position.side === 'short' ? 1 : 0),
        }),
        { totalValue: 0, totalPnl: 0, longPositions: 0, shortPositions: 0 }
      );
      setPositionStats(stats);
    } catch (error) {
      console.error('Failed to fetch positions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPositions();
    const interval = setInterval(fetchPositions, 10000);
    return () => clearInterval(interval);
  }, []);

  const handlePositionClick = (position) => {
    setSelectedPosition(position);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedPosition(null);
  };

  // Data for charts
  const pieData = [
    { name: 'Long', value: positionStats.longPositions, fill: '#00d4aa' },
    { name: 'Short', value: positionStats.shortPositions, fill: '#f6465d' },
  ];

  const symbolData = positions.reduce((acc, position) => {
    const existing = acc.find(item => item.symbol === position.symbol);
    if (existing) {
      existing.value += Math.abs(position.pnl);
      existing.count += 1;
    } else {
      acc.push({
        symbol: position.symbol,
        value: Math.abs(position.pnl),
        count: 1,
      });
    }
    return acc;
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Positions Management
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchPositions}
        >
          Refresh
        </Button>
      </Box>

      {/* Position Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="body2" sx={{ color: '#848e9c', mb: 1 }}>
              Total Positions
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {positions.length}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="body2" sx={{ color: '#848e9c', mb: 1 }}>
              Total Value
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              ${positionStats.totalValue.toLocaleString()}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="body2" sx={{ color: '#848e9c', mb: 1 }}>
              Total P&L
            </Typography>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: positionStats.totalPnl > 0 ? '#00d4aa' : '#f6465d',
              }}
            >
              ${positionStats.totalPnl.toFixed(2)}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="body2" sx={{ color: '#848e9c', mb: 1 }}>
              Long/Short Ratio
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {positionStats.shortPositions > 0
                ? (positionStats.longPositions / positionStats.shortPositions).toFixed(2)
                : positionStats.longPositions
              }
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Position Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Position Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* P&L by Symbol */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              P&L by Symbol
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={symbolData}>
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
                <Bar dataKey="value" fill="#f0b90b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Positions Table */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: '#1e2329' }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              Active Positions
            </Typography>
            {positions.length > 0 ? (
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
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {positions.map((position, index) => (
                      <TableRow key={index} sx={{ cursor: 'pointer' }} onClick={() => handlePositionClick(position)}>
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
                        <TableCell align="right">
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePositionClick(position);
                            }}
                          >
                            Manage
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="info" sx={{ bgcolor: 'rgba(33, 150, 243, 0.1)', color: '#2196f3' }}>
                No active positions found. Start trading to see positions here.
              </Alert>
            )}
          </Paper>
        </Grid>
      </Grid>

      <PositionDialog
        open={dialogOpen}
        onClose={handleDialogClose}
        position={selectedPosition}
        onUpdate={fetchPositions}
      />
    </Container>
  );
};

export default PositionsView;