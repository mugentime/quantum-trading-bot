import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Remove,
  Whatshot,
  Snow,
  LocalFireDepartment,
  Warning
} from '@mui/icons-material';
import { useVolatilityData, usePriceData, useDashboardStore } from '../../stores/dashboardStore';

const VolatilityHeatMap = () => {
  const volatilityData = useVolatilityData();
  const priceData = usePriceData();
  const { selectedTimeframe, setSelectedTimeframe } = useDashboardStore();
  const [sortBy, setSortBy] = useState('volatility');
  const [viewMode, setViewMode] = useState('grid');

  const symbols = ['ETH/USDT', 'LINK/USDT', 'SOL/USDT', 'AVAX/USDT', 'INJ/USDT', 'WLD/USDT'];

  // Process and sort data
  const heatMapData = useMemo(() => {
    const data = symbols.map(symbol => {
      const symbolKey = symbol.replace('/', '');
      const volatility = volatilityData[symbolKey] || { value: 0, level: 'Low', color: '#00ff00' };
      const price = priceData[symbolKey] || { last: 0, change_24h: 0, volume_24h: 0 };
      
      return {
        symbol,
        symbolKey,
        volatility: volatility.value,
        volatilityLevel: volatility.level,
        volatilityColor: volatility.color,
        price: price.last,
        change24h: price.change_24h || 0,
        volume24h: price.volume_24h || 0,
        high24h: price.high_24h || 0,
        low24h: price.low_24h || 0,
        // Calculate additional metrics
        priceRange: price.high_24h && price.low_24h ? 
          ((price.high_24h - price.low_24h) / price.low_24h * 100) : 0,
        opportunity: volatility.value * Math.abs(price.change_24h || 0)
      };
    });

    // Sort data based on selected criteria
    return data.sort((a, b) => {
      switch (sortBy) {
        case 'volatility':
          return b.volatility - a.volatility;
        case 'change':
          return Math.abs(b.change24h) - Math.abs(a.change24h);
        case 'volume':
          return b.volume24h - a.volume24h;
        case 'opportunity':
          return b.opportunity - a.opportunity;
        default:
          return 0;
      }
    });
  }, [volatilityData, priceData, sortBy]);

  const getVolatilityIcon = (level) => {
    switch (level) {
      case 'Extreme':
        return <LocalFireDepartment sx={{ color: '#ff0000' }} />;
      case 'High':
        return <Whatshot sx={{ color: '#ff8800' }} />;
      case 'Medium':
        return <Warning sx={{ color: '#ffff00' }} />;
      default:
        return <Snow sx={{ color: '#00ff00' }} />;
    }
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <TrendingUp color="success" />;
    if (change < 0) return <TrendingDown color="error" />;
    return <Remove color="disabled" />;
  };

  const getOpportunityLevel = (opportunity) => {
    if (opportunity > 50) return 'Excellent';
    if (opportunity > 25) return 'Good';
    if (opportunity > 10) return 'Moderate';
    return 'Low';
  };

  const getOpportunityColor = (opportunity) => {
    if (opportunity > 50) return 'success.main';
    if (opportunity > 25) return 'info.main';
    if (opportunity > 10) return 'warning.main';
    return 'text.secondary';
  };

  const formatVolume = (volume) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`;
    return volume.toFixed(0);
  };

  const HeatMapTile = ({ item }) => (
    <Tooltip 
      title={
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
            {item.symbol}
          </Typography>
          <Typography variant="body2">Volatility: {item.volatility.toFixed(2)}%</Typography>
          <Typography variant="body2">24h Change: {item.change24h.toFixed(2)}%</Typography>
          <Typography variant="body2">Price Range: {item.priceRange.toFixed(2)}%</Typography>
          <Typography variant="body2">Volume: {formatVolume(item.volume24h)}</Typography>
          <Typography variant="body2">Opportunity Score: {item.opportunity.toFixed(1)}</Typography>
        </Box>
      }
      arrow
      placement="top"
    >
      <Paper
        elevation={2}
        sx={{
          p: 2,
          height: 120,
          cursor: 'pointer',
          background: `linear-gradient(135deg, ${item.volatilityColor}15, ${item.volatilityColor}05)`,
          border: `2px solid ${item.volatilityColor}`,
          borderRadius: 2,
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'scale(1.05)',
            boxShadow: 4,
            border: `2px solid ${item.volatilityColor}`,
          }
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="h6" fontWeight="bold">
            {item.symbol.replace('/USDT', '')}
          </Typography>
          {getVolatilityIcon(item.volatilityLevel)}
        </Box>
        
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Typography variant="h6" fontWeight="bold">
            ${item.price.toFixed(2)}
          </Typography>
          {getChangeIcon(item.change24h)}
        </Box>
        
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Chip 
            label={`${item.volatility.toFixed(1)}%`}
            size="small"
            sx={{ 
              bgcolor: item.volatilityColor,
              color: 'white',
              fontWeight: 'bold'
            }}
          />
          <Typography 
            variant="caption"
            sx={{ color: item.change24h >= 0 ? 'success.main' : 'error.main' }}
            fontWeight="bold"
          >
            {item.change24h >= 0 ? '+' : ''}{item.change24h.toFixed(2)}%
          </Typography>
        </Box>
        
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="textSecondary">
            Vol: {formatVolume(item.volume24h)}
          </Typography>
          <Chip 
            label={getOpportunityLevel(item.opportunity)}
            size="small"
            variant="outlined"
            sx={{ 
              color: getOpportunityColor(item.opportunity),
              borderColor: getOpportunityColor(item.opportunity),
              fontSize: '0.65rem'
            }}
          />
        </Box>
      </Paper>
    </Tooltip>
  );

  const HeatMapList = ({ item }) => (
    <Paper 
      elevation={1}
      sx={{ 
        p: 2, 
        mb: 1,
        borderLeft: `4px solid ${item.volatilityColor}`,
        '&:hover': { bgcolor: 'action.hover' }
      }}
    >
      <Grid container alignItems="center" spacing={2}>
        <Grid item xs={3}>
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="h6" fontWeight="bold">
              {item.symbol.replace('/USDT', '')}
            </Typography>
            {getVolatilityIcon(item.volatilityLevel)}
          </Box>
        </Grid>
        
        <Grid item xs={2}>
          <Typography variant="body2" fontWeight="bold">
            ${item.price.toFixed(2)}
          </Typography>
          <Box display="flex" alignItems="center">
            {getChangeIcon(item.change24h)}
            <Typography 
              variant="caption"
              sx={{ color: item.change24h >= 0 ? 'success.main' : 'error.main' }}
            >
              {item.change24h >= 0 ? '+' : ''}{item.change24h.toFixed(2)}%
            </Typography>
          </Box>
        </Grid>
        
        <Grid item xs={2}>
          <Chip 
            label={`${item.volatility.toFixed(1)}%`}
            size="small"
            sx={{ 
              bgcolor: item.volatilityColor,
              color: 'white',
              fontWeight: 'bold'
            }}
          />
          <Typography variant="caption" color="textSecondary" display="block">
            {item.volatilityLevel}
          </Typography>
        </Grid>
        
        <Grid item xs={2}>
          <Typography variant="body2">
            {formatVolume(item.volume24h)}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Volume 24h
          </Typography>
        </Grid>
        
        <Grid item xs={2}>
          <Typography variant="body2">
            {item.priceRange.toFixed(2)}%
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Range 24h
          </Typography>
        </Grid>
        
        <Grid item xs={1}>
          <Chip 
            label={getOpportunityLevel(item.opportunity)}
            size="small"
            variant="outlined"
            sx={{ 
              color: getOpportunityColor(item.opportunity),
              borderColor: getOpportunityColor(item.opportunity)
            }}
          />
        </Grid>
      </Grid>
    </Paper>
  );

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            Volatility Heat Map
          </Typography>
          
          <Box display="flex" gap={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                label="Sort By"
                onChange={(e) => setSortBy(e.target.value)}
              >
                <MenuItem value="volatility">Volatility</MenuItem>
                <MenuItem value="change">24h Change</MenuItem>
                <MenuItem value="volume">Volume</MenuItem>
                <MenuItem value="opportunity">Opportunity</MenuItem>
              </Select>
            </FormControl>
            
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(e, value) => value && setViewMode(value)}
              size="small"
            >
              <ToggleButton value="grid">Grid</ToggleButton>
              <ToggleButton value="list">List</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Box>

        {/* Legend */}
        <Box display="flex" justifyContent="center" gap={2} mb={2} flexWrap="wrap">
          <Box display="flex" alignItems="center" gap={0.5}>
            <Box 
              sx={{ 
                width: 12, 
                height: 12, 
                bgcolor: '#00ff00', 
                borderRadius: 1 
              }} 
            />
            <Typography variant="caption">Low (0-2%)</Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={0.5}>
            <Box 
              sx={{ 
                width: 12, 
                height: 12, 
                bgcolor: '#ffff00', 
                borderRadius: 1 
              }} 
            />
            <Typography variant="caption">Medium (2-5%)</Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={0.5}>
            <Box 
              sx={{ 
                width: 12, 
                height: 12, 
                bgcolor: '#ff8800', 
                borderRadius: 1 
              }} 
            />
            <Typography variant="caption">High (5-10%)</Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={0.5}>
            <Box 
              sx={{ 
                width: 12, 
                height: 12, 
                bgcolor: '#ff0000', 
                borderRadius: 1 
              }} 
            />
            <Typography variant="caption">Extreme (10%+)</Typography>
          </Box>
        </Box>

        {/* Heat Map Display */}
        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          {viewMode === 'grid' ? (
            <Grid container spacing={2}>
              {heatMapData.map((item) => (
                <Grid item xs={12} sm={6} md={4} key={item.symbol}>
                  <HeatMapTile item={item} />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box>
              {heatMapData.map((item) => (
                <HeatMapList key={item.symbol} item={item} />
              ))}
            </Box>
          )}
        </Box>

        {/* Summary Stats */}
        <Box mt={2} p={1} bgcolor="action.hover" borderRadius={1}>
          <Grid container spacing={2} textAlign="center">
            <Grid item xs={3}>
              <Typography variant="h6" color="error.main">
                {heatMapData.filter(item => item.volatilityLevel === 'Extreme').length}
              </Typography>
              <Typography variant="caption">Extreme</Typography>
            </Grid>
            <Grid item xs={3}>
              <Typography variant="h6" color="warning.main">
                {heatMapData.filter(item => item.volatilityLevel === 'High').length}
              </Typography>
              <Typography variant="caption">High</Typography>
            </Grid>
            <Grid item xs={3}>
              <Typography variant="h6" color="info.main">
                {heatMapData.filter(item => item.volatilityLevel === 'Medium').length}
              </Typography>
              <Typography variant="caption">Medium</Typography>
            </Grid>
            <Grid item xs={3}>
              <Typography variant="h6" color="success.main">
                {heatMapData.filter(item => item.volatilityLevel === 'Low').length}
              </Typography>
              <Typography variant="caption">Low</Typography>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default VolatilityHeatMap;