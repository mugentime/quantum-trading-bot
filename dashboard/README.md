# Quantum Trading Dashboard

A comprehensive real-time performance monitoring dashboard for the high-volatility quantum trading system.

## Features

### Real-Time Monitoring
- **Live Trading Panel**: Real-time display of active positions across all 6 pairs with P&L tracking
- **Volatility Heat Map**: Visual representation of current volatility levels across all monitored pairs
- **Performance Metrics Panel**: Live calculation of win rate, profit factor, Sharpe ratio, drawdown
- **Risk Monitor**: Real-time tracking of portfolio heat, correlation exposure, margin usage

### Advanced Analytics
- **Signal Analysis Dashboard**: Display of current signals, confidence levels, entry/exit points
- **Historical Performance Charts**: Interactive charts showing daily/weekly/monthly performance
- **Alert System**: Visual and audio alerts for critical events and opportunities
- **Export Functionality**: Performance reports and data export capabilities

### Professional Features
- **WebSocket Real-Time Updates**: Sub-second data streaming
- **Mobile-Responsive Design**: Optimized for trading on-the-go
- **Dark Mode**: Professional trading environment
- **Customizable Layouts**: Drag-and-drop dashboard components
- **Telegram Integration**: Push notifications for critical alerts
- **Railway Deployment Ready**: Production-grade deployment configuration

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend development)
- Binance API keys
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd quantum_trading_bot/dashboard
   ```

2. **Automated Setup**
   ```bash
   python scripts/setup.py
   ```

3. **Manual Setup**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run Dashboard**
   ```bash
   python backend/dashboard_server.py
   ```

6. **Access Dashboard**
   Open http://localhost:5000

## Configuration

### Environment Variables

```bash
# Trading Configuration
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
BINANCE_TESTNET=true  # Set to false for live trading

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_NOTIFICATIONS=true

# Dashboard Settings
PORT=5000
DEBUG=false
```

### Trading Pairs
Default monitored pairs:
- ETH/USDT
- LINK/USDT
- SOL/USDT
- AVAX/USDT
- INJ/USDT
- WLD/USDT

## Architecture

### Backend (Python/Flask)
- **Flask API Server**: RESTful endpoints for dashboard data
- **WebSocket Server**: Real-time data streaming using Flask-SocketIO
- **Data Collection**: Real-time market data from Binance
- **Performance Engine**: Live calculation of trading metrics
- **Risk Management**: Real-time risk monitoring and alerts

### Frontend (React)
- **Material-UI Components**: Professional trading interface
- **Real-Time Updates**: WebSocket client with automatic reconnection
- **Responsive Grid**: Customizable dashboard layout
- **Chart Visualizations**: Interactive performance charts
- **State Management**: Zustand for efficient state handling

### Key Components

#### Live Trading Panel
- Active position tracking
- Real-time P&L calculation
- Position risk assessment
- Margin usage monitoring

#### Volatility Heat Map
- Visual volatility representation
- Opportunity scoring
- 24h price change tracking
- Volume analysis

#### Performance Metrics
- Win rate calculation
- Profit factor analysis
- Sharpe ratio computation
- Drawdown tracking
- ROI calculation

#### Risk Monitor
- Margin level alerts
- Position concentration analysis
- Leverage risk assessment
- Diversification scoring

#### Signal Analysis
- Real-time signal display
- Confidence level filtering
- Signal strength calculation
- Entry/exit point visualization

## Deployment

### Docker Deployment
```bash
# Build and run
docker build -f docker/Dockerfile -t quantum-dashboard .
docker run -p 5000:5000 --env-file .env quantum-dashboard

# Using Docker Compose
docker-compose up -d
```

### Railway Deployment
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically with each push

### Manual Production Deployment
```bash
# Install production dependencies
pip install -r requirements.txt

# Build frontend
cd frontend && npm run build && cd ..

# Run with Gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 backend.dashboard_server:app
```

## API Documentation

### REST Endpoints

#### System Status
- `GET /api/status` - System status and health
- `GET /health` - Health check endpoint

#### Trading Data
- `GET /api/positions` - Current positions
- `GET /api/performance` - Performance metrics
- `GET /api/trades?limit=100` - Trade history
- `GET /api/signals` - Current trading signals
- `GET /api/volatility` - Volatility data

#### Alerts
- `GET /api/alerts` - Recent alerts
- `POST /api/alerts/<id>/read` - Mark alert as read

#### Control
- `POST /api/start` - Start trading
- `POST /api/stop` - Stop trading
- `GET /api/export/<data_type>` - Export data as CSV

### WebSocket Events

#### Client → Server
- `subscribe` - Subscribe to data streams
- `command` - Send commands to server

#### Server → Client
- `dashboard_update` - Complete dashboard data update
- `alert` - New alert notification
- `position_update` - Position change notification
- `trade_executed` - Trade execution notification

## Monitoring

### Health Checks
The dashboard includes comprehensive health monitoring:
- API endpoint availability
- WebSocket connection status
- Exchange connectivity
- System resource usage

### Logging
Structured logging with multiple levels:
- ERROR: Critical issues requiring immediate attention
- WARNING: Important events that may need investigation
- INFO: General operational information
- DEBUG: Detailed debugging information

### Metrics
Performance metrics tracked:
- Request response times
- WebSocket connection count
- Memory usage
- CPU utilization
- Error rates

## Security

### API Security
- Rate limiting on all endpoints
- Input validation and sanitization
- CORS configuration
- Environment variable protection

### Trading Security
- API key encryption at rest
- Secure WebSocket connections
- Position size validation
- Risk limit enforcement

## Development

### Frontend Development
```bash
cd frontend
npm start  # Development server on port 3000
```

### Backend Development
```bash
export FLASK_ENV=development
python backend/dashboard_server.py
```

### Testing
```bash
# Backend tests
python -m pytest tests/

# Frontend tests
cd frontend && npm test
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check API keys in .env
   - Verify network connectivity
   - Check Binance API status

2. **WebSocket Disconnections**
   - Check firewall settings
   - Verify port 5000 accessibility
   - Monitor network stability

3. **Performance Issues**
   - Increase system resources
   - Reduce update frequency
   - Check Redis availability

4. **Permission Errors**
   - Check file permissions
   - Verify write access to logs/data directories
   - Run with appropriate user privileges

### Logs Location
- Application logs: `logs/dashboard.log`
- Error logs: `logs/error.log`
- Access logs: `logs/access.log`

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review error logs for debugging

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**⚠️ Trading Risk Disclaimer**: This software is for educational and informational purposes only. Cryptocurrency trading involves substantial risk of loss and is not suitable for every investor. Past performance does not guarantee future results. Only trade with funds you can afford to lose.