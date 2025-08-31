# Railway Bot Monitoring System

Comprehensive monitoring suite for Railway-deployed trading bot with real-time health checking, performance tracking, and interactive dashboard.

## 🚀 Quick Start

### Check Bot Health (One-time)
```bash
python monitoring/start_monitoring.py --check
```

### Start Full Monitoring Suite
```bash
python monitoring/start_monitoring.py --all
```

### Start Interactive Dashboard
```bash
python monitoring/start_monitoring.py --dashboard
```

## 📊 Monitoring Components

### 1. Railway Monitor (`railway_monitor.py`)
**Real-time comprehensive monitoring**
- Health endpoint monitoring (every 30s)
- Trading activity tracking (every 10s)
- Performance metrics collection (every 60s)
- Automated alerts and notifications
- Historical data logging

**Key Features:**
- Monitors `/health`, `/health/detailed`, `/ready`, `/live`, `/metrics` endpoints
- Tracks AXSUSDT and ETHUSDT trading performance
- Telegram notifications for critical events
- JSON data export for analysis

### 2. Interactive Dashboard (`railway_dashboard.py`)
**Real-time visual monitoring dashboard**
- Live system status display
- Trading metrics visualization
- Performance graphs and statistics
- Health status indicators
- Rich terminal UI (when available)

**Key Features:**
- Updates every 5 seconds
- Color-coded status indicators
- Trading performance metrics
- System resource monitoring
- Fallback to simple text mode

### 3. Performance Tracker (`performance_tracker.py`)
**Historical performance analysis**
- SQLite database for long-term storage
- CSV export for external analysis
- 620% monthly target tracking
- Automated performance alerts
- Daily/hourly reporting

**Key Features:**
- Tracks toward 14% daily target
- Win rate and drawdown monitoring
- Response time analysis
- Uptime calculation
- Performance trend analysis

### 4. Health Checker (`health_checker.py`)
**Endpoint health monitoring**
- Comprehensive endpoint testing
- Response time tracking
- Uptime calculation
- Alert threshold management
- Health history analysis

**Key Features:**
- Parallel endpoint checking
- Configurable timeout settings
- Critical vs non-critical endpoints
- Alert cooldown periods
- Detailed health reports

## 🛠️ Installation & Setup

### Prerequisites
```bash
pip install aiohttp rich
```

### Optional Dependencies
```bash
pip install rich  # For enhanced dashboard UI
```

### Environment Variables
```bash
RAILWAY_BOT_URL=https://railway-up-production-f151.up.railway.app
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 📋 Usage Examples

### Monitor Specific URL
```bash
python monitoring/start_monitoring.py --all --url https://your-railway-app.railway.app
```

### Performance Tracking Only
```bash
python monitoring/start_monitoring.py --performance
```

### Health Monitoring Only
```bash
python monitoring/start_monitoring.py --health
```

### Basic Monitoring (Health + Main)
```bash
python monitoring/start_monitoring.py --basic
```

### Verbose Logging
```bash
python monitoring/start_monitoring.py --all --verbose
```

## 📈 Monitoring Targets

### Trading Performance Targets
- **Daily Target:** 14% return
- **Monthly Target:** 620% return
- **Minimum Win Rate:** 60%
- **Maximum Drawdown:** 15%
- **Target Trades/Day:** 50 (high frequency)
- **Max Position Hold:** 5 minutes

### System Performance Thresholds
- **Memory Usage:** < 90%
- **Response Time:** < 10 seconds
- **Error Rate:** < 5%
- **Uptime Requirement:** > 99%

## 📊 Data Storage

### Performance Database (`performance_history.db`)
- **trading_performance:** Trade metrics and P&L
- **system_performance:** System resource usage
- **performance_alerts:** Alert history
- **daily_summaries:** Daily performance summaries

### CSV Files
- `trading_performance.csv` - Trading metrics export
- `system_performance.csv` - System metrics export
- `performance_alerts.csv` - Alert history export

### JSON Logs
- `monitoring/data/health_YYYYMMDD_HHMMSS.json`
- `monitoring/data/trading_YYYYMMDD_HHMMSS.json`
- `monitoring/data/performance_YYYYMMDD_HHMMSS.json`

## 🚨 Alert Configuration

### Health Alerts
- Endpoint failures (3 consecutive)
- High response times (> 10 seconds)
- System unhealthy status
- Low uptime (< 99%)

### Trading Alerts
- Win rate below 60%
- Daily target progress < 50% (after noon)
- Drawdown exceeding 15%
- Extended periods without trades

### System Alerts
- Memory usage > 90%
- High response times > 5 seconds
- Error rate > 5%
- Multiple system restarts

## 📱 Telegram Notifications

The monitoring system sends automated Telegram notifications for:
- **Startup/Shutdown:** Monitor status changes
- **Health Alerts:** Critical system issues
- **Trading Updates:** Significant trading activity
- **Performance Alerts:** Performance threshold breaches
- **Daily Summaries:** End-of-day performance reports
- **Hourly Reports:** Regular status updates

## 🔧 Configuration

### Monitoring Intervals
```python
health_check_interval = 30      # seconds
trading_check_interval = 10     # seconds  
metrics_check_interval = 60     # seconds
```

### Alert Thresholds
```python
max_response_time = 10000       # milliseconds
max_consecutive_failures = 3    # count
min_uptime_percent = 99.0       # percentage
alert_cooldown = 300           # seconds
```

### Data Retention
```python
health_history_limit = 1000     # entries
trading_history_limit = 2000    # entries
performance_history_limit = 500 # entries
```

## 📊 Dashboard Features

### Real-time Panels
1. **Health Status Panel**
   - Overall health indicator
   - Individual endpoint status
   - Response time metrics

2. **Trading Activity Panel**
   - Total trades executed
   - Active positions
   - Success rate and P&L
   - Daily/monthly target progress

3. **Performance Metrics Panel**
   - Memory and CPU usage
   - Response time statistics
   - Request count and error rate
   - System uptime

4. **System Status Panel**
   - Bot process status
   - Database connectivity
   - Exchange API connection
   - Risk manager status

## 🔍 Troubleshooting

### Common Issues

#### Dashboard not displaying properly
```bash
pip install rich
# Or run with simple mode:
export RICH_AVAILABLE=false
```

#### Connection timeouts
```bash
# Check Railway app is running
curl https://railway-up-production-f151.up.railway.app/health

# Increase timeout in monitoring scripts
timeout = aiohttp.ClientTimeout(total=30)
```

#### Missing dependencies
```bash
pip install aiohttp rich
```

#### Telegram notifications not working
```bash
# Verify environment variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Test telegram bot
python -c "from utils.telegram_notifier import TelegramNotifier; import asyncio; asyncio.run(TelegramNotifier().send_message('Test'))"
```

### Log Locations
- Main logs: `logs/monitoring_YYYYMMDD.log`
- Performance data: `monitoring/performance_data/`
- Health check data: `monitoring/data/`

## 🚀 Production Deployment

### Systemd Service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/railway-monitor.service

[Unit]
Description=Railway Bot Monitor
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/quantum_trading_bot
ExecStart=/usr/bin/python3 monitoring/start_monitoring.py --all
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable railway-monitor
sudo systemctl start railway-monitor
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "monitoring/start_monitoring.py", "--all"]
```

### Cron Job for Health Checks
```bash
# Add to crontab
*/5 * * * * cd /path/to/quantum_trading_bot && python monitoring/start_monitoring.py --check >> /tmp/health_check.log 2>&1
```

## 📚 API Integration

### Health Check Endpoints Expected by Monitor

#### `/health` - Basic Health Check
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "bot_running": true
}
```

#### `/health/detailed` - Detailed Metrics
```json
{
  "status": "healthy",
  "memory_usage_percent": 65.2,
  "cpu_usage_percent": 23.1,
  "average_response_time": 150,
  "total_requests": 1500,
  "error_rate": 1.2,
  "uptime_hours": 48.5,
  "bot_running": true,
  "exchange_connected": true,
  "db_connected": true
}
```

#### `/metrics` - Trading Metrics
```json
{
  "total_trades": 145,
  "successful_trades": 98,
  "total_pnl": 12.5,
  "daily_pnl": 2.8,
  "active_positions": 1,
  "win_rate": 0.676,
  "daily_target_progress": 0.2
}
```

#### `/ready` - Readiness Check
```json
{
  "ready": true,
  "dependencies": {
    "database": "connected",
    "exchange": "connected",
    "telegram": "active"
  }
}
```

#### `/live` - Liveness Check
```json
{
  "alive": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔒 Security Considerations

- Monitor logs may contain sensitive information
- Ensure proper file permissions on data directories
- Use environment variables for API keys
- Implement log rotation for long-running deployments
- Consider rate limiting for monitoring requests

## 📞 Support

For monitoring system issues:
1. Check logs in `logs/` directory
2. Verify Railway app is accessible
3. Check network connectivity
4. Validate environment variables
5. Test individual components with `--check` mode

---

**Railway Bot Monitoring System v1.0**  
*Comprehensive monitoring for high-frequency trading operations*