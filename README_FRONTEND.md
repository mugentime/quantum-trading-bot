# 🖥️ Quantum Trading Bot Frontend Dashboard

A modern, responsive web dashboard for monitoring and controlling your quantum trading bot. Built with React and Material-UI, featuring real-time updates and a Binance-inspired interface.

## 🚀 Features

### 📊 **Main Dashboard**
- Real-time P&L tracking and balance monitoring
- Performance charts with 24h data visualization
- Active positions overview with live updates
- Market overview with price changes and correlations
- Key trading metrics (Win rate, Sharpe ratio, Max drawdown)

### 📈 **Trading Analysis**
- Advanced correlation matrix for all trading pairs
- Real-time price action charts and market data
- Trading statistics and performance analytics
- Recent trades history with detailed information
- Correlation strength indicators and breakout signals

### 💼 **Position Management**
- Complete portfolio overview with position distribution
- Individual position management (stop-loss, take-profit)
- Real-time P&L calculations per position
- Position closing and modification capabilities
- Risk analytics and position sizing insights

### ⚙️ **Settings & Risk Management**
- Comprehensive risk management controls
- Trading pair selection and management
- Leverage and position size configuration
- Stop-loss and take-profit parameter tuning
- Notification preferences (Telegram integration)
- Advanced strategy parameters

### 🔄 **Real-time Features**
- WebSocket integration for live data updates
- Real-time bot status monitoring and control
- Live trade notifications and alerts
- Auto-refreshing charts and metrics
- Connection status indicators

## 🛠️ Technology Stack

- **Frontend**: React 18, Material-UI 5, Recharts
- **Real-time**: Socket.IO for WebSocket connections
- **Backend**: Flask with Flask-SocketIO
- **Styling**: Emotion, styled-components
- **Charts**: Recharts for data visualization
- **State Management**: React hooks and context

## 📦 Installation & Setup

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+ with pip
- Your quantum trading bot backend

### Quick Start

1. **Start the backend API server:**
   ```bash
   # Run the batch file (Windows)
   start_backend.bat
   
   # Or manually:
   pip install flask flask-cors flask-socketio python-socketio eventlet
   python backend_api_server.py
   ```

2. **Start the frontend dashboard:**
   ```bash
   # Run the batch file (Windows)
   start_frontend.bat
   
   # Or manually:
   cd frontend
   npm install
   npm start
   ```

3. **Access the dashboard:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🎯 Dashboard Overview

### Navigation
- **Dashboard**: Main overview with key metrics and charts
- **Trading**: Detailed trading analysis and correlation data
- **Positions**: Portfolio management and position controls
- **Settings**: Bot configuration and risk management

### Key Components

#### Bot Status Bar
- Real-time bot status (Running/Stopped)
- Current balance and P&L display
- Start/Stop bot controls
- Connection status indicator

#### Performance Charts
- 24-hour balance evolution
- P&L trends and drawdown analysis
- Market correlation visualizations
- Trade frequency and success rates

#### Position Cards
- Individual position details
- Real-time profit/loss calculations
- Risk metrics per position
- Quick action buttons

#### Settings Panel
- Risk per trade slider (0.5% - 10%)
- Max concurrent positions
- Leverage controls (1x - 50x)
- Trading pair selection
- Stop-loss/Take-profit settings

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=http://localhost:8000
```

### Backend Integration
The frontend connects to your existing bot through the `backend_api_server.py` which:
- Provides REST API endpoints for data
- Maintains WebSocket connections for real-time updates
- Interfaces with your trading orchestrator
- Handles bot start/stop commands

## 📱 Responsive Design

The dashboard is fully responsive and works on:
- **Desktop**: Full feature set with multi-column layouts
- **Tablet**: Optimized layouts for touch interaction
- **Mobile**: Condensed views with essential information

## 🎨 Design Features

### Binance-Inspired Theme
- Dark theme optimized for trading
- Professional color scheme (Gold #f0b90b, Green #00d4aa, Red #f6465d)
- Clean typography and intuitive layouts
- Smooth animations and transitions

### User Experience
- Instant feedback for all actions
- Toast notifications for important events
- Loading states and error handling
- Keyboard shortcuts for power users

## 🔐 Security Features

- CORS protection for API endpoints
- Input validation on all forms
- Secure WebSocket connections
- Error boundary components
- Safe bot control mechanisms

## 📊 Data Flow

1. **Real-time Updates**: WebSocket connection provides live data
2. **API Calls**: REST endpoints for configuration and historical data
3. **State Management**: React hooks manage local component state
4. **Error Handling**: Graceful degradation with mock data fallback

## 🚦 API Endpoints

### Bot Control
- `GET /api/bot/status` - Current bot status
- `POST /api/bot/start` - Start trading bot
- `POST /api/bot/stop` - Stop trading bot

### Trading Data
- `GET /api/positions` - Current positions
- `GET /api/trades` - Trade history
- `GET /api/market/data` - Market data for symbols
- `GET /api/performance` - Performance metrics

### Configuration
- `GET /api/settings` - Bot settings
- `PUT /api/settings` - Update settings

## 🎯 Key Metrics Displayed

### Performance Metrics
- **Total Return**: Overall profit/loss percentage
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Largest peak-to-trough loss
- **Profit Factor**: Ratio of gross profit to gross loss

### Risk Metrics
- **Position Size**: Current exposure per trade
- **Leverage Usage**: Current and maximum leverage
- **Correlation Risk**: Inter-pair correlation exposure
- **Portfolio Heat**: Overall portfolio risk level

## 🔄 Real-time Updates

The dashboard receives live updates for:
- Bot status changes
- New trade executions
- Position updates
- P&L changes
- Market price movements
- System alerts and errors

## 🎛️ Control Features

### Bot Controls
- **Start/Stop**: Control bot execution
- **Emergency Stop**: Immediate halt with position closing
- **Pause Trading**: Temporary suspension

### Position Controls
- **Manual Close**: Close individual positions
- **Modify Orders**: Update stop-loss and take-profit
- **Position Sizing**: Adjust exposure levels

### Risk Controls
- **Risk Limits**: Set maximum loss per trade
- **Position Limits**: Control maximum concurrent positions
- **Leverage Limits**: Set maximum leverage usage

## 📋 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure backend server is running on port 8000
   - Check firewall settings
   - Verify CORS configuration

2. **Data Not Loading**
   - Check API endpoints are accessible
   - Verify bot configuration
   - Check browser console for errors

3. **WebSocket Disconnections**
   - Backend server may be restarting
   - Network connectivity issues
   - Check socket.io configuration

### Debug Mode
Enable debug mode by setting:
```javascript
localStorage.setItem('debug', 'true');
```

## 🎯 Future Enhancements

- Advanced charting with TradingView integration
- Multiple timeframe analysis
- Strategy backtesting interface
- Portfolio optimization tools
- Mobile app version
- Multi-bot management
- Advanced order types
- Risk simulation tools

## 📞 Support

For issues or questions:
1. Check the browser console for errors
2. Verify backend API is running
3. Check WebSocket connection status
4. Review bot logs for errors

The dashboard provides comprehensive monitoring and control capabilities for your quantum trading bot, offering professional-grade tools in an intuitive interface.