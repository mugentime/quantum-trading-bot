import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  IconButton,
  Tooltip,
  Button,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Grid,
  LinearProgress
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Close,
  MoreVert,
  ShowChart,
  Info,
  Warning
} from '@mui/icons-material';
import { format } from 'date-fns';
import { usePositions, useTotalPnL, useDashboardStore } from '../../stores/dashboardStore';

const LiveTradingPanel = () => {
  const positions = usePositions();
  const totalPnL = useTotalPnL();
  const { performance, priceData } = useDashboardStore();
  
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Calculate aggregated metrics
  const metrics = useMemo(() => {
    const longPositions = positions.filter(p => p.side === 'long');
    const shortPositions = positions.filter(p => p.side === 'short');
    const profitablePositions = positions.filter(p => p.pnl > 0);
    
    return {
      total: positions.length,
      long: longPositions.length,
      short: shortPositions.length,
      profitable: profitablePositions.length,
      totalMargin: positions.reduce((sum, p) => sum + (p.margin_used || 0), 0),
      totalPnL: positions.reduce((sum, p) => sum + (p.pnl || 0), 0),
      avgPnL: positions.length > 0 ? totalPnL / positions.length : 0,
    };
  }, [positions, totalPnL]);

  const handleMenuClick = (event, position) => {
    setAnchorEl(event.currentTarget);
    setSelectedPosition(position);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedPosition(null);
  };

  const handleShowDetails = () => {
    setDetailsOpen(true);
    handleMenuClose();
  };

  const handleClosePosition = () => {
    // Implement position closing logic
    console.log('Closing position:', selectedPosition);
    handleMenuClose();
  };

  const formatPnL = (pnl) => {
    const formatted = Math.abs(pnl).toFixed(2);
    return pnl >= 0 ? `+$${formatted}` : `-$${formatted}`;
  };

  const formatPercent = (percent) => {
    const formatted = Math.abs(percent).toFixed(2);
    return percent >= 0 ? `+${formatted}%` : `-${formatted}%`;
  };

  const getPnLColor = (pnl) => {
    return pnl >= 0 ? 'success.main' : 'error.main';
  };

  const getSideColor = (side) => {
    return side === 'long' ? 'success.main' : 'error.main';
  };

  const getRiskLevel = (position) => {
    const leverage = position.leverage || 1;
    const pnlPercent = Math.abs(position.pnl_percent || 0);
    
    if (leverage > 30 || pnlPercent > 20) return 'high';
    if (leverage > 15 || pnlPercent > 10) return 'medium';
    return 'low';
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return 'error.main';
      case 'medium': return 'warning.main';
      default: return 'success.main';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            Live Positions
          </Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="body2" color="textSecondary">
              Total P&L:
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ color: getPnLColor(totalPnL), fontWeight: 'bold' }}
            >
              {formatPnL(totalPnL)}
            </Typography>
          </Box>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h4" fontWeight="bold">
                {metrics.total}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Total Positions
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" sx={{ color: 'success.main' }}>
                {metrics.long}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Long
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" sx={{ color: 'error.main' }}>
                {metrics.short}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Short
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box textAlign="center" p={1} bgcolor="action.hover" borderRadius={1}>
              <Typography variant="h6" sx={{ color: 'info.main' }}>
                {metrics.profitable}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Profitable
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {positions.length === 0 ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            No active positions. Monitor the signal analysis panel for entry opportunities.
          </Alert>
        ) : (
          <TableContainer sx={{ maxHeight: 400 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Side</TableCell>
                  <TableCell align="right">Size</TableCell>
                  <TableCell align="right">Entry</TableCell>
                  <TableCell align="right">Mark</TableCell>
                  <TableCell align="right">P&L</TableCell>
                  <TableCell align="right">Lev</TableCell>
                  <TableCell align="right">Risk</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {positions.map((position) => {
                  const riskLevel = getRiskLevel(position);
                  const currentPrice = priceData[position.symbol]?.last || position.mark_price;
                  
                  return (
                    <TableRow key={position.id} hover>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontWeight="bold">
                            {position.symbol}
                          </Typography>
                          {riskLevel === 'high' && (
                            <Warning fontSize="small" color="error" />
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Chip 
                          label={position.side.toUpperCase()}
                          size="small"
                          sx={{ 
                            bgcolor: getSideColor(position.side),
                            color: 'white',
                            fontWeight: 'bold'
                          }}
                        />
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2">
                          {position.size?.toFixed(3)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2">
                          ${position.entry_price?.toFixed(2)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Box display="flex" flexDirection="column" alignItems="end">
                          <Typography variant="body2">
                            ${currentPrice?.toFixed(2)}
                          </Typography>
                          {position.side === 'long' && currentPrice > position.entry_price && (
                            <TrendingUp fontSize="small" color="success" />
                          )}
                          {position.side === 'long' && currentPrice < position.entry_price && (
                            <TrendingDown fontSize="small" color="error" />
                          )}
                          {position.side === 'short' && currentPrice < position.entry_price && (
                            <TrendingUp fontSize="small" color="success" />
                          )}
                          {position.side === 'short' && currentPrice > position.entry_price && (
                            <TrendingDown fontSize="small" color="error" />
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Box display="flex" flexDirection="column" alignItems="end">
                          <Typography 
                            variant="body2" 
                            sx={{ color: getPnLColor(position.pnl), fontWeight: 'bold' }}
                          >
                            {formatPnL(position.pnl)}
                          </Typography>
                          <Typography 
                            variant="caption" 
                            sx={{ color: getPnLColor(position.pnl_percent) }}
                          >
                            {formatPercent(position.pnl_percent)}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="bold">
                          {position.leverage}x
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Chip 
                          label={riskLevel.toUpperCase()}
                          size="small"
                          sx={{ 
                            bgcolor: getRiskColor(riskLevel),
                            color: 'white',
                            fontSize: '0.7rem',
                            height: 20
                          }}
                        />
                      </TableCell>
                      
                      <TableCell align="center">
                        <IconButton 
                          size="small"
                          onClick={(e) => handleMenuClick(e, position)}
                        >
                          <MoreVert fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Margin Usage Bar */}
        <Box mt={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" color="textSecondary">
              Margin Usage
            </Typography>
            <Typography variant="body2">
              ${metrics.totalMargin.toFixed(2)} / ${performance.balance?.toFixed(2)}
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={(metrics.totalMargin / performance.balance) * 100}
            sx={{
              height: 8,
              borderRadius: 1,
              bgcolor: 'action.hover',
              '& .MuiLinearProgress-bar': {
                bgcolor: (metrics.totalMargin / performance.balance) > 0.8 ? 'error.main' : 
                        (metrics.totalMargin / performance.balance) > 0.6 ? 'warning.main' : 'success.main'
              }
            }}
          />
        </Box>

        {/* Position Actions Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleShowDetails}>
            <Info fontSize="small" sx={{ mr: 1 }} />
            View Details
          </MenuItem>
          <MenuItem onClick={() => console.log('Show chart')}>
            <ShowChart fontSize="small" sx={{ mr: 1 }} />
            Show Chart
          </MenuItem>
          <MenuItem onClick={handleClosePosition} sx={{ color: 'error.main' }}>
            <Close fontSize="small" sx={{ mr: 1 }} />
            Close Position
          </MenuItem>
        </Menu>

        {/* Position Details Dialog */}
        <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md">
          <DialogTitle>Position Details</DialogTitle>
          <DialogContent>
            {selectedPosition && (
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Symbol</Typography>
                  <Typography variant="h6">{selectedPosition.symbol}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Side</Typography>
                  <Typography variant="h6" sx={{ color: getSideColor(selectedPosition.side) }}>
                    {selectedPosition.side.toUpperCase()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Entry Price</Typography>
                  <Typography variant="h6">${selectedPosition.entry_price?.toFixed(2)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Mark Price</Typography>
                  <Typography variant="h6">${selectedPosition.mark_price?.toFixed(2)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Position Size</Typography>
                  <Typography variant="h6">{selectedPosition.size?.toFixed(3)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Leverage</Typography>
                  <Typography variant="h6">{selectedPosition.leverage}x</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Unrealized P&L</Typography>
                  <Typography variant="h6" sx={{ color: getPnLColor(selectedPosition.pnl) }}>
                    {formatPnL(selectedPosition.pnl)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">P&L Percentage</Typography>
                  <Typography variant="h6" sx={{ color: getPnLColor(selectedPosition.pnl_percent) }}>
                    {formatPercent(selectedPosition.pnl_percent)}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary">Open Time</Typography>
                  <Typography variant="body1">
                    {selectedPosition.timestamp ? format(new Date(selectedPosition.timestamp), 'PPpp') : 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default LiveTradingPanel;