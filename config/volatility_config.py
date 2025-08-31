#!/usr/bin/env python3
"""
HIGH VOLATILITY TRADING CONFIGURATION
Comprehensive configuration management for high volatility pairs trading strategy
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import json
import os

class ExchangeType(Enum):
    BINANCE = "binance"
    OKX = "okx"
    BYBIT = "bybit"

class TradingMode(Enum):
    TESTNET = "testnet"
    MAINNET = "mainnet"

@dataclass
class PairConfig:
    """Individual pair configuration"""
    symbol: str
    min_volatility_threshold: float
    max_position_size_pct: float
    base_leverage: int
    max_leverage: int
    stop_loss_range: tuple  # (min, max) percentage
    liquidity_requirement: float  # Minimum daily volume in USDT
    correlation_limit: float
    priority: int  # 1 = highest priority

@dataclass
class VolatilityThresholds:
    """Volatility detection thresholds"""
    # Minimum thresholds to trigger trading
    hourly_min: float = 0.05  # 5%
    daily_min: float = 0.15   # 15%
    
    # Percentile thresholds
    high_volatility_percentile: float = 95.0
    extreme_volatility_percentile: float = 99.0
    low_volatility_filter: float = 25.0
    
    # Breakout requirements
    volatility_breakout_multiplier: float = 2.0  # 2x average volatility
    
    # ATR scaling factors
    atr_stop_loss_multiplier: float = 1.5
    atr_take_profit_multiplier: float = 3.0

@dataclass
class RiskManagement:
    """Risk management parameters"""
    # Position sizing
    max_risk_per_trade: float = 0.02        # 2% max risk per trade
    max_portfolio_risk: float = 0.08        # 8% max total portfolio risk
    max_position_size: float = 0.05         # 5% max position size
    
    # Stop losses
    min_stop_loss: float = 0.008           # 0.8% minimum stop
    max_stop_loss: float = 0.015           # 1.5% maximum stop
    
    # Daily limits
    max_daily_loss: float = 0.03           # 3% max daily loss
    max_daily_trades: int = 10             # Max trades per day
    
    # Leverage limits
    min_leverage: int = 3
    max_leverage: int = 10
    
    # Correlation limits
    max_correlation_exposure: float = 0.7   # Max exposure to correlated pairs
    
    # Emergency stops
    portfolio_drawdown_limit: float = 0.15  # 15% portfolio drawdown limit
    consecutive_loss_limit: int = 5         # Max consecutive losses

@dataclass
class SignalConfig:
    """Signal generation configuration"""
    # Confidence thresholds
    min_confidence: float = 0.6
    high_confidence: float = 0.8
    
    # Technical indicators
    rsi_oversold: float = 30
    rsi_overbought: float = 70
    rsi_period: int = 14
    
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    
    # Volume analysis
    volume_spike_multiplier: float = 2.0
    volume_lookback: int = 50
    
    # Multi-timeframe alignment
    timeframes: List[str] = None
    alignment_requirement: float = 0.7  # 70% of timeframes must agree
    
    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = ['1m', '5m', '15m', '1h']

@dataclass
class ExecutionConfig:
    """Order execution configuration"""
    # Order types
    entry_order_type: str = "market"
    stop_loss_order_type: str = "stop_market"
    take_profit_order_type: str = "limit"
    
    # Slippage protection
    max_slippage: float = 0.001  # 0.1% max slippage
    
    # Timing
    order_timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    
    # Rate limiting
    orders_per_second: float = 2.0
    requests_per_minute: int = 1200

@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    # Performance tracking
    track_sharpe_ratio: bool = True
    track_sortino_ratio: bool = True
    track_max_drawdown: bool = True
    
    # Alert thresholds
    drawdown_alert_threshold: float = 0.05  # 5%
    consecutive_loss_alert: int = 3
    
    # Logging
    log_level: str = "INFO"
    log_trades: bool = True
    log_signals: bool = True
    log_performance: bool = True
    
    # Data retention
    trade_history_days: int = 90
    signal_history_days: int = 30

class HighVolatilityConfig:
    """Main configuration class for high volatility trading strategy"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Core configuration
        self.trading_mode = TradingMode.TESTNET
        self.exchange = ExchangeType.BINANCE
        
        # Strategy components
        self.volatility_thresholds = VolatilityThresholds()
        self.risk_management = RiskManagement()
        self.signal_config = SignalConfig()
        self.execution_config = ExecutionConfig()
        self.monitoring_config = MonitoringConfig()
        
        # Pair configurations
        self.pair_configs = self._create_default_pair_configs()
        
        # Operational settings
        self.scan_interval = 30  # seconds
        self.max_concurrent_positions = 5
        self.enable_paper_trading = False
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def _create_default_pair_configs(self) -> Dict[str, PairConfig]:
        """Create default configuration for target pairs"""
        
        # Primary pairs (highest priority, most liquid)
        primary_configs = {
            'BTC/USDT': PairConfig(
                symbol='BTC/USDT',
                min_volatility_threshold=0.04,  # 4% for BTC (less volatile)
                max_position_size_pct=0.06,     # 6% max position
                base_leverage=5,
                max_leverage=8,
                stop_loss_range=(0.008, 0.012), # 0.8-1.2%
                liquidity_requirement=1000000000, # 1B USDT daily volume
                correlation_limit=0.8,
                priority=1
            ),
            'ETH/USDT': PairConfig(
                symbol='ETH/USDT',
                min_volatility_threshold=0.05,  # 5% for ETH
                max_position_size_pct=0.05,     # 5% max position
                base_leverage=6,
                max_leverage=10,
                stop_loss_range=(0.008, 0.015), # 0.8-1.5%
                liquidity_requirement=500000000,  # 500M USDT daily volume
                correlation_limit=0.75,
                priority=1
            ),
            'SOL/USDT': PairConfig(
                symbol='SOL/USDT',
                min_volatility_threshold=0.06,  # 6% for SOL (more volatile)
                max_position_size_pct=0.04,     # 4% max position (higher risk)
                base_leverage=4,
                max_leverage=8,
                stop_loss_range=(0.010, 0.020), # 1.0-2.0% (wider for volatility)
                liquidity_requirement=200000000,  # 200M USDT daily volume
                correlation_limit=0.7,
                priority=1
            ),
            'BNB/USDT': PairConfig(
                symbol='BNB/USDT',
                min_volatility_threshold=0.05,  # 5% for BNB
                max_position_size_pct=0.045,    # 4.5% max position
                base_leverage=5,
                max_leverage=9,
                stop_loss_range=(0.009, 0.016), # 0.9-1.6%
                liquidity_requirement=150000000,  # 150M USDT daily volume
                correlation_limit=0.75,
                priority=1
            )
        }
        
        # Secondary pairs (lower priority, higher risk)
        secondary_configs = {
            'AXS/USDT': PairConfig(
                symbol='AXS/USDT',
                min_volatility_threshold=0.08,  # 8% for gaming tokens
                max_position_size_pct=0.03,     # 3% max (higher risk)
                base_leverage=3,
                max_leverage=6,
                stop_loss_range=(0.012, 0.025), # 1.2-2.5%
                liquidity_requirement=50000000,   # 50M USDT daily volume
                correlation_limit=0.6,
                priority=2
            ),
            'ADA/USDT': PairConfig(
                symbol='ADA/USDT',
                min_volatility_threshold=0.06,  # 6% for ADA
                max_position_size_pct=0.035,    # 3.5% max
                base_leverage=4,
                max_leverage=7,
                stop_loss_range=(0.010, 0.018), # 1.0-1.8%
                liquidity_requirement=100000000,  # 100M USDT daily volume
                correlation_limit=0.65,
                priority=2
            ),
            'XRP/USDT': PairConfig(
                symbol='XRP/USDT',
                min_volatility_threshold=0.07,  # 7% for XRP
                max_position_size_pct=0.035,    # 3.5% max
                base_leverage=4,
                max_leverage=7,
                stop_loss_range=(0.010, 0.020), # 1.0-2.0%
                liquidity_requirement=120000000,  # 120M USDT daily volume
                correlation_limit=0.65,
                priority=2
            ),
            'DOGE/USDT': PairConfig(
                symbol='DOGE/USDT',
                min_volatility_threshold=0.10,  # 10% for meme coins
                max_position_size_pct=0.025,    # 2.5% max (highest risk)
                base_leverage=3,
                max_leverage=5,
                stop_loss_range=(0.015, 0.030), # 1.5-3.0% (widest stops)
                liquidity_requirement=80000000,   # 80M USDT daily volume
                correlation_limit=0.5,
                priority=3
            )
        }
        
        # Combine all configurations
        all_configs = {**primary_configs, **secondary_configs}
        return all_configs
    
    def get_pair_config(self, symbol: str) -> Optional[PairConfig]:
        """Get configuration for a specific trading pair"""
        return self.pair_configs.get(symbol)
    
    def get_primary_pairs(self) -> List[str]:
        """Get list of primary trading pairs"""
        return [symbol for symbol, config in self.pair_configs.items() 
                if config.priority == 1]
    
    def get_secondary_pairs(self) -> List[str]:
        """Get list of secondary trading pairs"""
        return [symbol for symbol, config in self.pair_configs.items() 
                if config.priority >= 2]
    
    def get_all_pairs(self) -> List[str]:
        """Get all configured trading pairs"""
        return list(self.pair_configs.keys())
    
    def update_pair_config(self, symbol: str, updates: Dict):
        """Update configuration for a specific pair"""
        if symbol in self.pair_configs:
            config = self.pair_configs[symbol]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    def set_trading_mode(self, mode: TradingMode):
        """Set trading mode (testnet/mainnet)"""
        self.trading_mode = mode
        
        # Adjust risk parameters for mainnet
        if mode == TradingMode.MAINNET:
            # More conservative settings for real money
            self.risk_management.max_risk_per_trade = 0.01  # 1%
            self.risk_management.max_daily_loss = 0.02      # 2%
            self.signal_config.min_confidence = 0.7        # Higher confidence
    
    def set_exchange(self, exchange: ExchangeType):
        """Set target exchange"""
        self.exchange = exchange
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of warnings/errors"""
        warnings = []
        
        # Check risk management
        if self.risk_management.max_risk_per_trade > 0.05:
            warnings.append("Risk per trade > 5% may be too aggressive")
        
        if self.risk_management.max_leverage > 15:
            warnings.append("Maximum leverage > 15x may be dangerous")
        
        # Check pair configurations
        total_max_exposure = sum(
            config.max_position_size_pct for config in self.pair_configs.values()
        )
        if total_max_exposure > 0.5:
            warnings.append(f"Total maximum exposure {total_max_exposure:.1%} may be too high")
        
        # Check signal requirements
        if self.signal_config.min_confidence < 0.5:
            warnings.append("Minimum confidence < 50% may generate too many false signals")
        
        # Check volatility thresholds
        if self.volatility_thresholds.hourly_min > 0.1:
            warnings.append("Hourly volatility threshold > 10% may miss opportunities")
        
        return warnings
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            'trading_mode': self.trading_mode.value,
            'exchange': self.exchange.value,
            'scan_interval': self.scan_interval,
            'max_concurrent_positions': self.max_concurrent_positions,
            'volatility_thresholds': {
                'hourly_min': self.volatility_thresholds.hourly_min,
                'daily_min': self.volatility_thresholds.daily_min,
                'high_volatility_percentile': self.volatility_thresholds.high_volatility_percentile,
                'extreme_volatility_percentile': self.volatility_thresholds.extreme_volatility_percentile,
            },
            'risk_management': {
                'max_risk_per_trade': self.risk_management.max_risk_per_trade,
                'max_portfolio_risk': self.risk_management.max_portfolio_risk,
                'max_position_size': self.risk_management.max_position_size,
                'max_daily_loss': self.risk_management.max_daily_loss,
                'max_leverage': self.risk_management.max_leverage,
            },
            'pair_configs': {
                symbol: {
                    'min_volatility_threshold': config.min_volatility_threshold,
                    'max_position_size_pct': config.max_position_size_pct,
                    'base_leverage': config.base_leverage,
                    'max_leverage': config.max_leverage,
                    'priority': config.priority
                } for symbol, config in self.pair_configs.items()
            }
        }
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Update configuration from loaded data
        self.trading_mode = TradingMode(data.get('trading_mode', 'testnet'))
        self.exchange = ExchangeType(data.get('exchange', 'binance'))
        self.scan_interval = data.get('scan_interval', 30)
        self.max_concurrent_positions = data.get('max_concurrent_positions', 5)
        
        # Update thresholds if provided
        if 'volatility_thresholds' in data:
            vt_data = data['volatility_thresholds']
            self.volatility_thresholds.hourly_min = vt_data.get('hourly_min', 0.05)
            self.volatility_thresholds.daily_min = vt_data.get('daily_min', 0.15)
            self.volatility_thresholds.high_volatility_percentile = vt_data.get('high_volatility_percentile', 95.0)
        
        # Update risk management if provided
        if 'risk_management' in data:
            rm_data = data['risk_management']
            self.risk_management.max_risk_per_trade = rm_data.get('max_risk_per_trade', 0.02)
            self.risk_management.max_portfolio_risk = rm_data.get('max_portfolio_risk', 0.08)
            self.risk_management.max_daily_loss = rm_data.get('max_daily_loss', 0.03)

# Create default configuration instance
DEFAULT_HIGH_VOLATILITY_CONFIG = HighVolatilityConfig()

# Configuration presets for different risk levels
CONSERVATIVE_CONFIG = HighVolatilityConfig()
CONSERVATIVE_CONFIG.risk_management.max_risk_per_trade = 0.01  # 1%
CONSERVATIVE_CONFIG.risk_management.max_leverage = 5
CONSERVATIVE_CONFIG.signal_config.min_confidence = 0.75
CONSERVATIVE_CONFIG.volatility_thresholds.high_volatility_percentile = 97

AGGRESSIVE_CONFIG = HighVolatilityConfig()
AGGRESSIVE_CONFIG.risk_management.max_risk_per_trade = 0.03  # 3%
AGGRESSIVE_CONFIG.risk_management.max_leverage = 15
AGGRESSIVE_CONFIG.signal_config.min_confidence = 0.55
AGGRESSIVE_CONFIG.volatility_thresholds.high_volatility_percentile = 90

# Trading session configurations
ASIAN_SESSION_CONFIG = HighVolatilityConfig()
ASIAN_SESSION_CONFIG.scan_interval = 15  # More frequent scanning
ASIAN_SESSION_CONFIG.volatility_thresholds.hourly_min = 0.03  # Lower threshold

EUROPEAN_SESSION_CONFIG = HighVolatilityConfig()
EUROPEAN_SESSION_CONFIG.scan_interval = 30
EUROPEAN_SESSION_CONFIG.volatility_thresholds.hourly_min = 0.05

US_SESSION_CONFIG = HighVolatilityConfig()
US_SESSION_CONFIG.scan_interval = 20  # More active during US hours
US_SESSION_CONFIG.volatility_thresholds.hourly_min = 0.06  # Higher threshold