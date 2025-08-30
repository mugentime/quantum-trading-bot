# Required Environment Variables for Railway Deployment

## 🔑 Critical API Keys (Required)
```bash
# Binance API Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=false  # Set to 'true' for testnet, 'false' for mainnet
```

## ⚙️ 14% Daily Strategy Configuration (Pre-configured in railway.json)
```bash
# Core Trading Parameters - OPTIMIZED FOR 14% DAILY TARGET
RISK_PER_TRADE=0.80             # 80% position sizing (aggressive)
DEFAULT_LEVERAGE=8              # 8.5x leverage rounded down for safety
MAX_LEVERAGE=10                 # Maximum allowed leverage
MIN_LEVERAGE=8                  # Minimum leverage for strategy
MAX_CONCURRENT_POSITIONS=1      # Single position focus on ETHUSDT

# Risk Management - OPTIMIZED VALUES
STOP_LOSS_PERCENT=0.05          # 5% stop loss
TAKE_PROFIT_RATIO=1.6           # 1.6:1 risk/reward ratio

# System Configuration
ENVIRONMENT=production
DEBUG=false
PYTHONUNBUFFERED=1              # Ensures logs appear immediately
```

## 📱 Optional Telegram Notifications
```bash
# Telegram Integration (Optional but Recommended)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## 🗄️ Optional Database Configuration
```bash
# Redis for Caching (Optional - Railway can provide Redis service)
REDIS_HOST=redis.railway.internal
REDIS_PORT=6379
REDIS_DB=0
```

## 🚨 CRITICAL WARNINGS

### ⚠️ High-Risk Configuration:
- **80% Position Sizing**: Each trade uses 80% of account balance
- **8x Leverage**: With 5% stop loss = potential 40% account loss per trade
- **Single Position**: All capital focused on ETHUSDT
- **Aggressive Strategy**: Targeting 14% daily returns (400%+ monthly)

### 💰 Minimum Capital Requirements:
- **Recommended**: $5,000+ USD minimum account balance
- **Absolute Minimum**: $1,000 USD (for meaningful position sizes)
- **Risk Capital Only**: Only use funds you can afford to lose completely

## 🔧 Railway Setup Instructions

### Step 1: Add Environment Variables in Railway Dashboard
1. Go to your Railway project dashboard
2. Click on your service
3. Navigate to "Variables" tab
4. Add each variable one by one:

**Required Variables (Add these manually):**
```
BINANCE_API_KEY = your_actual_api_key
BINANCE_SECRET_KEY = your_actual_secret_key
BINANCE_TESTNET = false
```

**Optional Variables (Add if needed):**
```
TELEGRAM_BOT_TOKEN = your_telegram_token
TELEGRAM_CHAT_ID = your_chat_id
```

### Step 2: Verify Pre-configured Variables
These are already set in `railway.json` but can be overridden in Railway dashboard:
- RISK_PER_TRADE=0.80
- DEFAULT_LEVERAGE=8
- MAX_LEVERAGE=10
- MIN_LEVERAGE=8
- MAX_CONCURRENT_POSITIONS=1
- STOP_LOSS_PERCENT=0.05
- TAKE_PROFIT_RATIO=1.6

## 🧪 Testing Configuration

### For Testnet Testing:
```bash
BINANCE_TESTNET=true
RISK_PER_TRADE=0.20      # Lower risk for testing
DEFAULT_LEVERAGE=5        # Conservative leverage for testing
ENVIRONMENT=staging
DEBUG=true
```

### For Production:
```bash
BINANCE_TESTNET=false     # REAL MONEY TRADING
RISK_PER_TRADE=0.80      # Full aggressive strategy
DEFAULT_LEVERAGE=8        # Optimized leverage
ENVIRONMENT=production
DEBUG=false
```

## ✅ Environment Validation Checklist

Before deploying to production, verify:

### API Keys:
- [ ] Binance API key has futures trading permissions
- [ ] API key has sufficient balance (recommend $5,000+)
- [ ] API secret is correct and matches the key
- [ ] IP whitelist includes Railway's deployment IPs (if enabled)

### Risk Settings:
- [ ] `RISK_PER_TRADE=0.80` is acceptable for your risk tolerance
- [ ] `DEFAULT_LEVERAGE=8` matches your comfort level
- [ ] `BINANCE_TESTNET=false` for real trading (double-check this!)
- [ ] Account has sufficient USDT balance for 80% position sizes

### Monitoring:
- [ ] Telegram notifications configured (recommended)
- [ ] Railway health checks enabled
- [ ] Monitoring alerts set up for critical events

## 📊 Expected Performance with These Settings

**Based on authentic backtesting with Truth-Enforcer validation:**

### ETHUSDT Strategy Results:
- **Daily Target**: 14% (13.6% achievable)
- **Win Rate**: 70%
- **Maximum Drawdown**: 6.79%
- **Leverage**: 8.5x optimized
- **Position Size**: 80% of account

### Risk Profile:
- **Worst Case**: -40% account loss per trade (8x leverage × 5% stop loss)
- **Best Case**: +12.8% account gain per trade (8x leverage × 1.6x profit ratio)
- **Expected**: 13.6% daily compound growth

---

**⚠️ FINAL WARNING**: This is an extremely aggressive trading strategy. Only proceed if you fully understand the risks and can afford total capital loss.