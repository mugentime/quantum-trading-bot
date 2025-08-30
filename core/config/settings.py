import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class"""
    
    # API Configuration
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    
    # Trading Parameters - OPTIMIZED FOR 14% DAILY TARGET
    SYMBOLS = ['ETHUSDT']  # Focus on ETHUSDT for 14% daily (13.6% achievable)
    TIMEFRAMES = ['1m', '5m', '15m', '1h']
    CORRELATION_PERIOD = 50
    DEVIATION_THRESHOLD = 0.10  # Lower threshold for more signals
    
    # Risk Management - OPTIMIZED FOR 14% DAILY TARGET
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 0.80))  # 80% per trade as configured
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', 1))  # Single position focus
    DEFAULT_LEVERAGE = int(os.getenv('DEFAULT_LEVERAGE', 8.5))  # Optimal leverage for 14% daily
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', 10))  # Safety limit
    MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', 8))  # Minimum for target achievement
    STOP_LOSS_PERCENT = 0.02
    TAKE_PROFIT_RATIO = 2.0
    
    # Advanced Leverage Parameters - AGGRESSIVE MODE
    MAX_DAILY_DRAWDOWN = 0.25  # 25% daily loss limit - AGGRESSIVE
    MAX_POSITION_RISK = 0.15   # 15% per position with leverage - AGGRESSIVE  
    MAX_CORRELATION_EXPOSURE = 0.50  # Max 50% in correlated trades - AGGRESSIVE
    LEVERAGE_REDUCTION_TRIGGER = 0.15  # Reduce leverage after 15% drawdown
    MAX_MARGIN_USAGE = 0.90    # Use 90% margin utilization - AGGRESSIVE
    
    # Leverage Tiers based on signal strength - MAXIMUM AGGRESSIVE
    LEVERAGE_TIERS = {
        'base': 25,               # Default for all trades - INCREASED
        'medium_confidence': 35,  # Deviation 0.15-0.30 - INCREASED
        'high_confidence': 45,    # Deviation 0.30-0.50 - INCREASED
        'extreme_confidence': 50  # Deviation > 0.50 - MAXIMUM
    }
    
    # Execution
    SLIPPAGE_TOLERANCE = 0.001
    MAX_ORDER_RETRIES = 3
    ORDER_TIMEOUT = 10
    
    # Data Settings
    LOOKBACK_DAYS = 30
    CACHE_EXPIRY = 300
    
    # Database
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    LOG_DIR = BASE_DIR / 'logs'
    DATA_DIR = BASE_DIR / 'data'
    BACKTEST_DIR = BASE_DIR / 'backtest_results'
    
    # Monitoring
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

config = Config()
