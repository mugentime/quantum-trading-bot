import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Warning,
  Error,
  CheckCircle,
  ExpandMore,
  ExpandLess,
  TrendingDown,
  AccountBalance,
  Psychology,
  Speed,
  Timeline
} from '@mui/icons-material';
import { usePerformance, usePositions, usePortfolioHeat, useRiskLevel } from '../../stores/dashboardStore';

const RiskMonitor = () => {
  const performance = usePerformance();
  const positions = usePositions();
  const portfolioHeat = usePortfolioHeat();
  const riskLevel = useRiskLevel();
  const [expanded, setExpanded] = useState(true);

  // Calculate comprehensive risk metrics
  const riskMetrics = useMemo(() => {
    const marginLevel = performance.margin_level || 100;
    const currentDrawdown = performance.current_drawdown || 0;
    const totalPositions = positions.length;
    const totalMarginUsed = performance.margin_used || 0;
    const balance = performance.balance || 10000;
    const equity = performance.equity || balance;
    
    // Position concentration risk
    const positionSizes = positions.map(pos => pos.margin_used || 0);
    const maxPosition = Math.max(...positionSizes, 0);
    const concentrationRisk = totalMarginUsed > 0 ? (maxPosition / totalMarginUsed) * 100 : 0;
    
    // Leverage analysis
    const leverages = positions.map(pos => pos.leverage || 1);
    const avgLeverage = leverages.length > 0 ? 
      leverages.reduce((sum, lev) => sum + lev, 0) / leverages.length : 0;
    const maxLeverage = Math.max(...leverages, 0);
    
    // Correlation risk (simplified)
    const symbols = [...new Set(positions.map(pos => pos.symbol))];
    const diversificationScore = Math.min((symbols.length / 6) * 100, 100);
    
    // Heat calculation
    const heat = (totalMarginUsed / balance) * 100;
    
    // Risk scores (0-100, higher is riskier)
    const marginRisk = Math.max(0, 100 - ((marginLevel - 100) / 5));
    const drawdownRisk = currentDrawdown * 10;
    const concentrationRiskScore = concentrationRisk;
    const leverageRisk = avgLeverage > 20 ? 100 : (avgLeverage / 20) * 100;
    const heatRisk = heat > 80 ? 100 : (heat / 80) * 100;
    const diversificationRisk = 100 - diversificationScore;
    
    // Overall risk score
    const overallRisk = (
      marginRisk * 0.25 +
      drawdownRisk * 0.2 +
      concentrationRiskScore * 0.2 +
      leverageRisk * 0.15 +
      heatRisk * 0.1 +
      diversificationRisk * 0.1
    );
    
    return {
      marginLevel,
      currentDrawdown,
      concentrationRisk,
      avgLeverage,
      maxLeverage,
      diversificationScore,
      heat,
      overallRisk,
      marginRisk,
      drawdownRisk,
      leverageRisk,
      heatRisk,
      totalPositions,
      symbols: symbols.length
    };
  }, [performance, positions]);

  const getRiskColor = (risk) => {
    if (risk > 70) return 'error.main';
    if (risk > 40) return 'warning.main';
    return 'success.main';
  };

  const getRiskIcon = (risk) => {
    if (risk > 70) return <Error color="error" />;
    if (risk > 40) return <Warning color="warning" />;
    return <CheckCircle color="success" />;
  };

  const getRiskLevel = (risk) => {
    if (risk > 70) return 'High Risk';
    if (risk > 40) return 'Medium Risk';
    return 'Low Risk';
  };

  const formatPercent = (value) => `${value.toFixed(1)}%`;

  const RiskIndicator = ({ title, value, risk, icon, subtitle }) => (
    <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Box display="flex" alignItems="center" gap={1}>
          {icon}
          <Typography variant="body2" fontWeight="bold">
            {title}
          </Typography>
        </Box>
        <Chip 
          label={getRiskLevel(risk)}
          size="small"
          sx={{ 
            bgcolor: getRiskColor(risk),
            color: 'white',
            fontWeight: 'bold'
          }}
        />
      </Box>
      <Typography variant="h6" sx={{ color: getRiskColor(risk), fontWeight: 'bold' }}>
        {value}
      </Typography>
      {subtitle && (
        <Typography variant="caption" color="textSecondary">
          {subtitle}
        </Typography>
      )}
      <LinearProgress 
        variant="determinate"
        value={Math.min(risk, 100)}
        sx={{
          mt: 1,
          height: 4,
          borderRadius: 1,
          bgcolor: 'action.hover',
          '& .MuiLinearProgress-bar': {
            bgcolor: getRiskColor(risk)
          }
        }}
      />
    </Box>
  );

  // Risk alerts based on current conditions
  const riskAlerts = useMemo(() => {
    const alerts = [];
    
    if (riskMetrics.marginLevel < 150) {
      alerts.push({
        severity: 'error',
        message: `Critical: Margin level at ${riskMetrics.marginLevel.toFixed(1)}% - Risk of liquidation`,
        action: 'Close positions or add margin immediately'
      });
    } else if (riskMetrics.marginLevel < 200) {
      alerts.push({
        severity: 'warning',
        message: `Low margin level: ${riskMetrics.marginLevel.toFixed(1)}%`,
        action: 'Consider reducing position sizes'
      });
    }
    
    if (riskMetrics.currentDrawdown > 15) {
      alerts.push({
        severity: 'error',
        message: `High drawdown: ${formatPercent(riskMetrics.currentDrawdown)}`,
        action: 'Review trading strategy and risk management'
      });
    } else if (riskMetrics.currentDrawdown > 10) {
      alerts.push({
        severity: 'warning',
        message: `Moderate drawdown: ${formatPercent(riskMetrics.currentDrawdown)}`,
        action: 'Monitor positions closely'
      });
    }
    
    if (riskMetrics.concentrationRisk > 40) {
      alerts.push({
        severity: 'warning',
        message: `High position concentration: ${formatPercent(riskMetrics.concentrationRisk)}`,
        action: 'Diversify position sizes'
      });
    }
    
    if (riskMetrics.avgLeverage > 30) {
      alerts.push({
        severity: 'warning',
        message: `High average leverage: ${riskMetrics.avgLeverage.toFixed(1)}x`,
        action: 'Consider reducing leverage'
      });
    }
    
    if (riskMetrics.symbols < 3) {
      alerts.push({
        severity: 'info',
        message: `Low diversification: Only ${riskMetrics.symbols} symbols`,
        action: 'Consider trading more symbols'
      });
    }
    
    if (riskMetrics.heat > 80) {
      alerts.push({
        severity: 'error',
        message: `Excessive portfolio heat: ${formatPercent(riskMetrics.heat)}`,
        action: 'Reduce overall position sizes immediately'
      });
    }
    
    return alerts;
  }, [riskMetrics]);

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            Risk Monitor
          </Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <Chip 
              label={getRiskLevel(riskMetrics.overallRisk)}
              size="small"
              icon={getRiskIcon(riskMetrics.overallRisk)}
              sx={{ 
                bgcolor: getRiskColor(riskMetrics.overallRisk),
                color: 'white',
                fontWeight: 'bold'
              }}
            />
            <Tooltip title={expanded ? "Collapse details" : "Expand details"}>
              <IconButton size="small" onClick={() => setExpanded(!expanded)}>
                {expanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Overall Risk Score */}
        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" fontWeight="bold">
              Overall Risk Score
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {riskMetrics.overallRisk.toFixed(1)}/100
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.min(riskMetrics.overallRisk, 100)}
            sx={{
              height: 12,
              borderRadius: 2,
              bgcolor: 'action.hover',
              '& .MuiLinearProgress-bar': {
                bgcolor: getRiskColor(riskMetrics.overallRisk),
                borderRadius: 2
              }
            }}
          />
        </Box>

        {/* Risk Alerts */}
        {riskAlerts.length > 0 && (
          <Box mb={3}>
            <Typography variant="body2" fontWeight="bold" mb={1}>
              Active Alerts ({riskAlerts.length})
            </Typography>
            <List dense sx={{ maxHeight: 150, overflow: 'auto' }}>
              {riskAlerts.map((alert, index) => (
                <ListItem key={index} sx={{ px: 0 }}>
                  <Alert 
                    severity={alert.severity} 
                    size="small"
                    sx={{ width: '100%', fontSize: '0.75rem' }}
                  >
                    <Typography variant="caption" fontWeight="bold">
                      {alert.message}
                    </Typography>
                    <Typography variant="caption" display="block">
                      {alert.action}
                    </Typography>
                  </Alert>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Collapse in={expanded}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <RiskIndicator
                title="Margin Level"
                value={`${riskMetrics.marginLevel.toFixed(1)}%`}
                risk={riskMetrics.marginRisk}
                icon={<AccountBalance fontSize="small" />}
                subtitle="Min: 150% recommended"
              />
            </Grid>
            
            <Grid item xs={6}>
              <RiskIndicator
                title="Drawdown"
                value={formatPercent(riskMetrics.currentDrawdown)}
                risk={riskMetrics.drawdownRisk}
                icon={<TrendingDown fontSize="small" />}
                subtitle="Max: 15% acceptable"
              />
            </Grid>
            
            <Grid item xs={6}>
              <RiskIndicator
                title="Portfolio Heat"
                value={formatPercent(riskMetrics.heat)}
                risk={riskMetrics.heatRisk}
                icon={<Speed fontSize="small" />}
                subtitle={`${riskMetrics.totalPositions} positions`}
              />
            </Grid>
            
            <Grid item xs={6}>
              <RiskIndicator
                title="Concentration"
                value={formatPercent(riskMetrics.concentrationRisk)}
                risk={riskMetrics.concentrationRisk}
                icon={<Psychology fontSize="small" />}
                subtitle="Max position size"
              />
            </Grid>
            
            <Grid item xs={6}>
              <RiskIndicator
                title="Avg Leverage"
                value={`${riskMetrics.avgLeverage.toFixed(1)}x`}
                risk={riskMetrics.leverageRisk}
                icon={<Timeline fontSize="small" />}
                subtitle={`Max: ${riskMetrics.maxLeverage}x`}
              />
            </Grid>
            
            <Grid item xs={6}>
              <RiskIndicator
                title="Diversification"
                value={formatPercent(riskMetrics.diversificationScore)}
                risk={100 - riskMetrics.diversificationScore}
                icon={<CheckCircle fontSize="small" />}
                subtitle={`${riskMetrics.symbols} symbols`}
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />

          {/* Risk Management Guidelines */}
          <Box>
            <Typography variant="body2" fontWeight="bold" mb={1}>
              Risk Management Guidelines
            </Typography>
            <List dense>
              <ListItem sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Maintain margin level above 200%"
                  primaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Keep maximum drawdown under 15%"
                  primaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Limit single position to 30% of portfolio"
                  primaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Use average leverage below 25x"
                  primaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
            </List>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default RiskMonitor;