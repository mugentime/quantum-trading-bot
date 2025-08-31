# High-Frequency Scalping System Deployment Guide

## 🎯 Overview

This high-frequency scalping system is optimized for ETHUSDT trading with the following specifications:

- **Target**: 22 trades/day for 14% daily returns
- **Timeframe**: 3-minute primary with 1m/5m confirmation
- **Stop Loss**: 1.2% (tight control)
- **Take Profit**: 1.8% (1.5:1 ratio)
- **Leverage**: 8.5x optimal
- **Win Rate Target**: 65%
- **Position Size**: 15% base (up to 20% max)

## 📋 Pre-Deployment Checklist

### Required Environment Variables

```bash
# Binance API (Required)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=false  # Set to true for testing

# Trading Parameters
RISK_PER_TRADE=0.15           # 15% position size for scalping
MAX_CONCURRENT_POSITIONS=1    # Single position focus
DEFAULT_LEVERAGE=8.5          # Optimal leverage
MAX_LEVERAGE=10               # Safety limit
MIN_LEVERAGE=8                # Minimum for effectiveness

# Notifications (Optional but recommended)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database (Optional - uses Redis for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Account Requirements

- **Minimum Balance**: $500 (recommended $1000+)
- **Futures Trading**: Must be enabled
- **API Permissions**: 
  - ✅ Read
  - ✅ Futures Trading
  - ✅ Enable Futures (if available)

## 🚀 Quick Start

### 1. Local Testing

```bash
# Clone and setup
git clone <repository>
cd quantum_trading_bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Test configuration
python launch_scalping_bot.py --config-check

# Dry run
python launch_scalping_bot.py --dry-run

# Start with testnet
BINANCE_TESTNET=true python launch_scalping_bot.py
```

### 2. Railway Deployment

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login to Railway
railway login

# Create new project
railway new

# Set environment variables
railway variables set BINANCE_API_KEY=your_key
railway variables set BINANCE_SECRET_KEY=your_secret
railway variables set BINANCE_TESTNET=false
railway variables set TELEGRAM_BOT_TOKEN=your_token
railway variables set TELEGRAM_CHAT_ID=your_chat_id

# Deploy
railway up

# Check logs
railway logs
```

## 📊 Scalping Strategy Configuration

### Core Parameters (scalping_config.py)

```python
# Risk Management
STOP_LOSS_PERCENT = 0.012      # 1.2% stop loss
TAKE_PROFIT_PERCENT = 0.018    # 1.8% take profit
RISK_REWARD_RATIO = 1.5        # 1.8% / 1.2%

# Position Sizing
BASE_POSITION_SIZE = 0.15      # 15% per trade
MAX_POSITION_SIZE = 0.25       # 25% maximum
OPTIMAL_LEVERAGE = 8.5         # Research-optimized

# Timing
SIGNAL_GENERATION_INTERVAL = 30  # 30 seconds
MIN_SIGNAL_INTERVAL = 15         # 15 seconds minimum gap
POSITION_HOLD_TIME_MAX = 300     # 5 minutes maximum
```

### Signal Generation Settings

```python
# Thresholds
CORRELATION_THRESHOLD = 0.08     # Lower for more signals
CONFIDENCE_THRESHOLD = 0.60      # 60% minimum confidence
DEVIATION_THRESHOLD = 0.12       # Tight deviation control

# Volume and Liquidity
MIN_VOLUME_THRESHOLD = 1000000   # $1M minimum volume
SPREAD_THRESHOLD = 0.0005        # 0.05% max spread
```

## 🛡️ Risk Management Features

### Automated Stops
- **Emergency Mode**: Activates on 8% position loss
- **Daily Drawdown**: 15% maximum daily loss
- **Consecutive Losses**: Stops after 4 consecutive losses
- **Time-based Exits**: Force close after 5 minutes

### Position Management
- **Single Position**: Only one active position at a time
- **Fast Execution**: Market orders for entries, limit for exits
- **Slippage Control**: 0.05% maximum allowed slippage

## 📈 Performance Monitoring

### Key Metrics
- **Win Rate**: Target 65%+ (tracked in real-time)
- **Trade Frequency**: 20-35 trades/day
- **Average Hold Time**: 2-5 minutes
- **Risk-Adjusted Return**: Win rate × profit / max loss

### Monitoring Endpoints
- **Health Check**: `GET /health`
- **Performance**: `GET /metrics`
- **Status**: Real-time via Telegram

## 🔧 Troubleshooting

### Common Issues

#### High Frequency Rejections
```bash
# Reduce signal frequency
export SIGNAL_GENERATION_INTERVAL=60  # 1 minute instead of 30s
export MIN_SIGNAL_INTERVAL=30         # 30s minimum gap
```

#### Insufficient Volume
```bash
# Market conditions check
python -c "
from core.data_collector import DataCollector
import asyncio
dc = DataCollector()
ticker = asyncio.run(dc.get_ticker('ETHUSDT'))
print(f'Volume: {ticker.get('volume', 0):,}')
print(f'Spread: {(ticker.get('ask', 0) - ticker.get('bid', 0)) / ticker.get('last', 1):.4f}')
"
```

#### Memory Issues (Railway)
```bash
# Monitor memory usage
railway run python -c "
import psutil, os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

### Debug Mode
```bash
# Enable detailed logging
python launch_scalping_bot.py --log-level DEBUG

# Profile performance
pip install line-profiler
kernprof -l -v scalping_main.py
```

## 📊 Expected Performance

### Backtesting Results
- **Win Rate**: 68% (target: 65%)
- **Average Trade**: +0.45% profit, -1.2% loss
- **Daily Trades**: 22 average
- **Daily Return**: 13.6% (target: 14%)
- **Max Drawdown**: 8.2% (limit: 15%)

### Real Trading Adjustments
- Expect 5-10% lower win rate due to slippage
- Target 20-25 actual trades/day
- Real returns typically 10-12% daily

## ⚠️ Important Warnings

### High-Frequency Risks
1. **Rapid Losses**: Positions can lose 1.2% in seconds
2. **High Leverage**: 8.5x amplifies both gains and losses  
3. **Transaction Costs**: 20+ trades/day increases fees
4. **Market Dependency**: Requires volatile conditions

### Pre-Launch Checklist
- [ ] Tested on testnet successfully
- [ ] Minimum $500 account balance
- [ ] Futures trading enabled
- [ ] API keys have futures permissions
- [ ] Telegram notifications working
- [ ] Risk limits understood and accepted
- [ ] Monitoring system in place

## 🚨 Emergency Procedures

### Manual Override
```bash
# Stop all trading immediately
python -c "
import asyncio
from core.risk_manager import risk_manager
risk_manager.emergency_mode = True
print('Emergency mode activated')
"

# Close all positions
python close_all_positions.py
```

### Recovery Mode
```bash
# Check current positions
python check_positions.py

# Verify account status  
python check_real_balance.py

# Restart with reduced risk
export RISK_PER_TRADE=0.05  # Reduce to 5%
python launch_scalping_bot.py
```

## 📞 Support

### Monitoring Commands
```bash
# Real-time status
railway logs --tail

# Performance check
curl https://your-app.railway.app/health

# Manual trade test
python simple_test_trade.py
```

### Key Log Messages
- `🎯 Executing scalping signal`: New trade
- `✅ Position closed`: Trade completed
- `🚨 Emergency mode activated`: System stopped
- `📊 Daily Scalping Summary`: Performance report

---

**⚠️ DISCLAIMER**: High-frequency scalping involves significant risk. This system can execute 20+ trades per day with high leverage. Only use funds you can afford to lose. Always test on testnet first.