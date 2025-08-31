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
    
    # Trading Parameters - HIGH-VOLATILITY MULTI-PAIR OPTIMIZED
    SYMBOLS = ['AXSUSDT', 'GALAUSDT', 'SUSHIUSDT', 'SANDUSDT', 'AVAXUSDT', 'ETHUSDT']  # High-volatility pairs for 300%+ monthly target
    TIMEFRAMES = ['1m', '3m', '5m']  # Optimized for ultra-high frequency scalping
    CORRELATION_PERIOD = 30  # Shorter period for faster signal detection
    DEVIATION_THRESHOLD = 0.08  # Lower threshold for more frequent signals
    
    # Risk Management - HIGH-VOLATILITY MULTI-PAIR OPTIMIZED
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 0.08))  # Reduced risk for volatile multi-pair trading
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', 5))  # Multi-pair portfolio focus
    DEFAULT_LEVERAGE = int(os.getenv('DEFAULT_LEVERAGE', 8.5))  # Optimal leverage
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', 10))  # Safety limit
    MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', 8))  # Minimum for target achievement
    STOP_LOSS_PERCENT = 0.018  # 1.8% stop loss for volatile pairs
    TAKE_PROFIT_RATIO = 2.5  # 4.5% take profit (1.8% * 2.5) for volatility capture
    
    # Advanced Leverage Parameters - HIGH-VOLATILITY OPTIMIZED
    MAX_DAILY_DRAWDOWN = 0.12  # 12% daily loss limit for volatile pairs
    MAX_POSITION_RISK = 0.06   # 6% per position with leverage for volatile pairs
    MAX_CORRELATION_EXPOSURE = 0.50  # Higher correlation tolerance for multi-pair
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
    SIGNAL_GENERATION_INTERVAL = 45  # Generate signals every 45 seconds for volatile pairs
    MIN_SIGNAL_INTERVAL = 30  # Minimum 30 seconds between signals for processing
    
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
