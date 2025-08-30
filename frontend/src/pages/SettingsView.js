import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  Divider,
  Slider,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  Save as SaveIcon,
  Security as SecurityIcon,
  TrendingUp as TradingIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { botAPI } from '../api/botAPI';
import { toast } from 'react-toastify';

const SettingsView = () => {
  const [settings, setSettings] = useState({
    riskPerTrade: 0.02,
    maxPositions: 5,
    defaultLeverage: 15,
    maxLeverage: 30,
    stopLoss: 0.03,
    takeProfit: 0.05,
    enabledPairs: ['ETHUSDT', 'LINKUSDT', 'SOLUSDT'],
    telegramNotifications: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [originalSettings, setOriginalSettings] = useState({});

  const availablePairs = [
    'ETHUSDT', 'BTCUSDT', 'LINKUSDT', 'SOLUSDT', 'BNBUSDT',
    'ADAUSDT', 'DOGEUSDT', 'XRPUSDT', 'DOTUSDT', 'AVAXUSDT'
  ];

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await botAPI.getSettings();
        setSettings(data);
        setOriginalSettings(data);
      } catch (error) {
        console.error('Failed to fetch settings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleInputChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handlePairToggle = (pair) => {
    setSettings(prev => ({
      ...prev,
      enabledPairs: prev.enabledPairs.includes(pair)
        ? prev.enabledPairs.filter(p => p !== pair)
        : [...prev.enabledPairs, pair]
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await botAPI.updateSettings(settings);
      setOriginalSettings(settings);
      toast.success('Settings saved successfully');
    } catch (error) {
      toast.error('Failed to save settings');
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setSettings(originalSettings);
  };

  const hasChanges = JSON.stringify(settings) !== JSON.stringify(originalSettings);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Bot Settings
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={handleReset}
            disabled={!hasChanges || saving}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={!hasChanges || saving}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      {hasChanges && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You have unsaved changes. Click "Save Changes" to apply them.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Risk Management */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: '#1e2329' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <SecurityIcon sx={{ color: '#f0b90b', mr: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Risk Management
                </Typography>
              </Box>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" sx={{ color: '#848e9c', mb: 2 }}>
                    Risk Per Trade: {(settings.riskPerTrade * 100).toFixed(1)}%
                  </Typography>
                  <Slider
                    value={settings.riskPerTrade * 100}
                    onChange={(_, value) => handleInputChange('riskPerTrade', value / 100)}
                    min={0.5}
                    max={10}
                    step={0.1}
                    marks={[
                      { value: 1, label: '1%' },
                      { value: 2, label: '2%' },
                      { value: 5, label: '5%' },
                      { value: 10, label: '10%' },
                    ]}
                    sx={{
                      '& .MuiSlider-thumb': {
                        backgroundColor: '#f0b90b',
                      },
                      '& .MuiSlider-track': {
                        backgroundColor: '#f0b90b',
                      },
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Max Concurrent Positions"
                    type="number"
                    value={settings.maxPositions}
                    onChange={(e) => handleInputChange('maxPositions', parseInt(e.target.value))}
                    fullWidth
                    inputProps={{ min: 1, max: 20 }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" sx={{ color: '#848e9c', mb: 2 }}>
                    Default Leverage: {settings.defaultLeverage}x
                  </Typography>
                  <Slider
                    value={settings.defaultLeverage}
                    onChange={(_, value) => handleInputChange('defaultLeverage', value)}
                    min={1}
                    max={50}
                    step={1}
                    marks={[
                      { value: 1, label: '1x' },
                      { value: 10, label: '10x' },
                      { value: 25, label: '25x' },
                      { value: 50, label: '50x' },
                    ]}
                    sx={{
                      '& .MuiSlider-thumb': {
                        backgroundColor: '#f0b90b',
                      },
                      '& .MuiSlider-track': {
                        backgroundColor: '#f0b90b',
                      },
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Max Leverage"
                    type="number"
                    value={settings.maxLeverage}
                    onChange={(e) => handleInputChange('maxLeverage', parseInt(e.target.value))}
                    fullWidth
                    inputProps={{ min: 1, max: 100 }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Stop Loss (%)"
                    type="number"
                    value={(settings.stopLoss * 100).toFixed(1)}
                    onChange={(e) => handleInputChange('stopLoss', parseFloat(e.target.value) / 100)}
                    fullWidth
                    inputProps={{ min: 0.1, max: 50, step: 0.1 }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Take Profit (%)"
                    type="number"
                    value={(settings.takeProfit * 100).toFixed(1)}
                    onChange={(e) => handleInputChange('takeProfit', parseFloat(e.target.value) / 100)}
                    fullWidth
                    inputProps={{ min: 0.1, max: 100, step: 0.1 }}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Trading Pairs */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: '#1e2329' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <TradingIcon sx={{ color: '#00d4aa', mr: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Trading Pairs
                </Typography>
              </Box>
              
              <Typography variant="body2" sx={{ color: '#848e9c', mb: 3 }}>
                Select which trading pairs the bot should monitor and trade
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {availablePairs.map((pair) => (
                  <Chip
                    key={pair}
                    label={pair}
                    clickable
                    color={settings.enabledPairs.includes(pair) ? 'primary' : 'default'}
                    onClick={() => handlePairToggle(pair)}
                    sx={{
                      bgcolor: settings.enabledPairs.includes(pair) ? '#f0b90b' : '#2b3139',
                      color: settings.enabledPairs.includes(pair) ? '#000' : '#fff',
                      '&:hover': {
                        bgcolor: settings.enabledPairs.includes(pair) ? '#f0b90b' : '#474d57',
                      },
                    }}
                  />
                ))}
              </Box>
              
              <Typography variant="body2" sx={{ color: '#848e9c', mt: 2 }}>
                Selected: {settings.enabledPairs.length} pairs
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: '#1e2329' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <NotificationsIcon sx={{ color: '#2196f3', mr: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Notifications
                </Typography>
              </Box>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.telegramNotifications}
                    onChange={(e) => handleInputChange('telegramNotifications', e.target.checked)}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': {
                        color: '#f0b90b',
                      },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                        backgroundColor: '#f0b90b',
                      },
                    }}
                  />
                }
                label="Enable Telegram Notifications"
              />
              
              <Typography variant="body2" sx={{ color: '#848e9c', mt: 1 }}>
                Receive notifications for trade executions, errors, and important events
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Advanced Settings */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: '#1e2329' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Advanced Settings
              </Typography>
              
              <Alert severity="warning" sx={{ mb: 3 }}>
                These settings are for advanced users only. Changing them may affect bot performance.
              </Alert>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Trading Mode</InputLabel>
                    <Select
                      value="correlation"
                      label="Trading Mode"
                    >
                      <MenuItem value="correlation">Correlation Strategy</MenuItem>
                      <MenuItem value="momentum" disabled>Momentum Strategy (Coming Soon)</MenuItem>
                      <MenuItem value="arbitrage" disabled>Arbitrage Strategy (Coming Soon)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Correlation Threshold"
                    type="number"
                    value={0.7}
                    fullWidth
                    inputProps={{ min: 0.1, max: 1.0, step: 0.1 }}
                    helperText="Minimum correlation strength to trigger trades"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SettingsView;