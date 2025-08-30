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
    
    # Trading Parameters - EXPANDED PAIR SET
    SYMBOLS = [
        'BTCUSDT', 'ETHUSDT', 'SOLUSDT',  # Core crypto trio
        'BNBUSDT', 'XRPUSDT',             # Exchange/utility tokens
        'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', # Layer-1 & meme leader
        'DOTUSDT', 'LINKUSDT'             # Infrastructure tokens (MATIC->DOT for testnet)
    ]
    TIMEFRAMES = ['1m', '5m', '15m', '1h']
    CORRELATION_PERIOD = 50
    DEVIATION_THRESHOLD = 0.15
    
    # Risk Management
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 0.02))  # Increased from 0.01
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', 5))
    DEFAULT_LEVERAGE = int(os.getenv('DEFAULT_LEVERAGE', 15))  # Increased from 10
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', 30))  # New parameter
    MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', 10))  # New parameter
    STOP_LOSS_PERCENT = 0.02
    TAKE_PROFIT_RATIO = 2.0
    
    # Advanced Leverage Parameters
    MAX_DAILY_DRAWDOWN = 0.10  # 10% daily loss limit
    MAX_POSITION_RISK = 0.03   # 3% per position with leverage
    MAX_CORRELATION_EXPOSURE = 0.15  # Max 15% in correlated trades
    LEVERAGE_REDUCTION_TRIGGER = 0.05  # Reduce leverage after 5% drawdown
    MAX_MARGIN_USAGE = 0.60    # Never exceed 60% margin utilization
    
    # Leverage Tiers based on signal strength
    LEVERAGE_TIERS = {
        'base': 15,               # Default for all trades
        'medium_confidence': 20,  # Deviation 0.15-0.30
        'high_confidence': 25,    # Deviation 0.30-0.50
        'extreme_confidence': 30  # Deviation > 0.50
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
