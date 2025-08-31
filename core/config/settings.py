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
    
    # Trading Parameters - HIGH-FREQUENCY SCALPING OPTIMIZED
    SYMBOLS = ['ETHUSDT']  # Primary focus for high-frequency scalping
    TIMEFRAMES = ['1m', '3m', '5m']  # Optimized for 3-minute scalping
    CORRELATION_PERIOD = 30  # Shorter period for faster signal detection
    DEVIATION_THRESHOLD = 0.08  # Lower threshold for more frequent signals
    
    # Risk Management - HIGH-FREQUENCY SCALPING OPTIMIZED
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 0.15))  # Lower risk per trade for high frequency
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', 1))  # Single position focus
    DEFAULT_LEVERAGE = int(os.getenv('DEFAULT_LEVERAGE', 8.5))  # Optimal leverage
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', 10))  # Safety limit
    MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', 8))  # Minimum for target achievement
    STOP_LOSS_PERCENT = 0.012  # 1.2% stop loss for tight control
    TAKE_PROFIT_RATIO = 1.5  # 1.8% take profit (1.2% * 1.5)
    
    # Advanced Leverage Parameters - SCALPING OPTIMIZED
    MAX_DAILY_DRAWDOWN = 0.15  # 15% daily loss limit for scalping
    MAX_POSITION_RISK = 0.08   # 8% per position with leverage for tighter control
    MAX_CORRELATION_EXPOSURE = 0.30  # Lower correlation exposure for scalping
    LEVERAGE_REDUCTION_TRIGGER = 0.10  # Reduce leverage after 10% drawdown
    MAX_MARGIN_USAGE = 0.70    # Conservative margin usage for scalping
    
    # Leverage Tiers based on signal strength - SCALPING OPTIMIZED
    LEVERAGE_TIERS = {
        'base': 8,                # Conservative base for scalping
        'medium_confidence': 8.5, # Slight increase for medium confidence
        'high_confidence': 9,     # Moderate increase for high confidence
        'extreme_confidence': 10  # Maximum for extreme confidence
    }
    
    # Execution - HIGH-FREQUENCY OPTIMIZED
    SLIPPAGE_TOLERANCE = 0.0005  # Tighter slippage tolerance for scalping
    MAX_ORDER_RETRIES = 5  # More retries for high-frequency trading
    ORDER_TIMEOUT = 5  # Shorter timeout for faster execution
    SIGNAL_GENERATION_INTERVAL = 30  # Generate signals every 30 seconds
    MIN_SIGNAL_INTERVAL = 15  # Minimum 15 seconds between signals
    
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
