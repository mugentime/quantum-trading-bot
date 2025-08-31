"""
High-Frequency Scalping Configuration
Optimized parameters for 20-50 trades per day targeting 14% daily returns
"""
import os
from dataclasses import dataclass
from typing import Dict, List
from datetime import time


@dataclass
class ScalpingParameters:
    """Scalping-specific trading parameters"""
    
    # Core Scalping Settings
    PRIMARY_SYMBOL: str = 'ETHUSDT'
    TARGET_TRADES_PER_DAY: int = 22  # Research-optimized for 14% target
    MIN_TRADES_PER_DAY: int = 15
    MAX_TRADES_PER_DAY: int = 35
    
    # Timeframe Configuration
    MAIN_TIMEFRAME: str = '3m'  # Primary 3-minute timeframe
    CONFIRMATION_TIMEFRAMES: List[str] = ['1m', '5m']  # Supporting timeframes
    
    # Risk Parameters (Research-Optimized)
    STOP_LOSS_PERCENT: float = 0.012  # 1.2% stop loss
    TAKE_PROFIT_PERCENT: float = 0.018  # 1.8% take profit
    RISK_REWARD_RATIO: float = 1.5  # 1.8% / 1.2% = 1.5
    WIN_RATE_TARGET: float = 0.65  # 65% win rate required
    
    # Position Sizing
    BASE_POSITION_SIZE: float = 0.15  # 15% of balance per trade
    MAX_POSITION_SIZE: float = 0.25  # Maximum position size
    MIN_POSITION_SIZE: float = 0.05  # Minimum position size
    
    # Leverage Settings
    OPTIMAL_LEVERAGE: float = 8.5  # Research-optimized leverage
    MAX_LEVERAGE: float = 10.0
    MIN_LEVERAGE: float = 6.0
    
    # Signal Generation
    CORRELATION_THRESHOLD: float = 0.08  # Lower threshold for more signals
    DEVIATION_THRESHOLD: float = 0.12  # Tighter deviation threshold
    CONFIDENCE_THRESHOLD: float = 0.60  # Lower confidence for more trades
    
    # Timing Controls
    SIGNAL_COOLDOWN_SECONDS: int = 15  # Minimum time between signals
    ORDER_EXECUTION_TIMEOUT: int = 5  # 5-second order timeout
    POSITION_HOLD_TIME_MAX: int = 300  # Maximum 5 minutes per position
    
    # Market Hours (UTC) - Optimized for high liquidity
    ACTIVE_HOURS_START: time = time(6, 0)  # 06:00 UTC
    ACTIVE_HOURS_END: time = time(22, 0)  # 22:00 UTC
    HIGH_ACTIVITY_HOURS: List[tuple] = [
        (time(8, 0), time(12, 0)),   # European session
        (time(13, 0), time(17, 0)),  # US overlap
        (time(20, 0), time(24, 0))   # Asian session start
    ]
    
    # Volume and Liquidity
    MIN_VOLUME_THRESHOLD: float = 1000000  # Minimum volume for trades
    SPREAD_THRESHOLD: float = 0.0005  # Maximum allowed spread
    
    # Technical Indicators
    RSI_OVERSOLD: float = 25
    RSI_OVERBOUGHT: float = 75
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STDDEV: float = 1.5
    
    # Performance Targets
    DAILY_TARGET_PERCENT: float = 0.14  # 14% daily target
    DRAWDOWN_LIMIT_PERCENT: float = 0.08  # 8% maximum drawdown
    CONSECUTIVE_LOSSES_LIMIT: int = 4  # Stop after 4 consecutive losses


@dataclass
class ScalpingFilters:
    """Signal filtering parameters for high-frequency trading"""
    
    # Signal Quality Filters
    MIN_CORRELATION_STRENGTH: float = 0.3
    MIN_STATISTICAL_SIGNIFICANCE: float = 0.85
    MIN_VOLATILITY: float = 0.005  # Minimum 0.5% volatility
    MAX_VOLATILITY: float = 0.08   # Maximum 8% volatility
    
    # Market Condition Filters
    AVOID_NEWS_MINUTES_BEFORE: int = 5
    AVOID_NEWS_MINUTES_AFTER: int = 10
    MIN_LIQUIDITY_RATIO: float = 0.8
    
    # Time-Based Filters
    AVOID_MARKET_OPEN_MINUTES: int = 15  # Avoid first 15 minutes
    AVOID_MARKET_CLOSE_MINUTES: int = 30  # Avoid last 30 minutes
    
    # Technical Filters
    TREND_ALIGNMENT_REQUIRED: bool = True
    VOLUME_CONFIRMATION_REQUIRED: bool = True
    MOMENTUM_THRESHOLD: float = 0.02


@dataclass
class ScalpingExecution:
    """Execution parameters optimized for scalping"""
    
    # Order Types
    ENTRY_ORDER_TYPE: str = 'MARKET'  # Fast market entry
    EXIT_ORDER_TYPE: str = 'LIMIT'    # Limit exit for better fills
    
    # Execution Timing
    MAX_EXECUTION_DELAY_MS: int = 500  # Maximum 500ms delay
    ORDER_RETRY_ATTEMPTS: int = 3
    ORDER_RETRY_DELAY_MS: int = 100
    
    # Slippage Management
    MAX_SLIPPAGE_PERCENT: float = 0.0005  # 0.05% maximum slippage
    SLIPPAGE_BUFFER: float = 0.0002  # Buffer for slippage
    
    # Position Management
    USE_STOP_LOSS_ORDERS: bool = True
    USE_TAKE_PROFIT_ORDERS: bool = True
    TRAILING_STOP_ENABLED: bool = False  # Disabled for scalping
    
    # Emergency Controls
    MAX_DAILY_LOSSES: int = 6  # Stop after 6 losses
    EMERGENCY_STOP_LOSS_PERCENT: float = 0.05  # 5% emergency stop
    FORCE_EXIT_AFTER_MINUTES: int = 8  # Force exit after 8 minutes


class ScalpingConfig:
    """Main scalping configuration class"""
    
    def __init__(self):
        self.parameters = ScalpingParameters()
        self.filters = ScalpingFilters()
        self.execution = ScalpingExecution()
        
    def get_dynamic_parameters(self, current_performance: Dict) -> Dict:
        """Get dynamic parameters based on current performance"""
        params = {}
        
        # Adjust position sizing based on win rate
        current_win_rate = current_performance.get('win_rate', 0.5)
        if current_win_rate > 0.7:
            params['position_size_multiplier'] = 1.2
        elif current_win_rate < 0.5:
            params['position_size_multiplier'] = 0.8
        else:
            params['position_size_multiplier'] = 1.0
            
        # Adjust thresholds based on recent performance
        recent_pnl = current_performance.get('recent_pnl', 0.0)
        if recent_pnl < -0.05:  # If losing 5%
            params['confidence_threshold'] = 0.75  # Higher threshold
            params['correlation_threshold'] = 0.12  # Stricter correlation
        elif recent_pnl > 0.03:  # If winning 3%
            params['confidence_threshold'] = 0.55  # Lower threshold for more trades
            params['correlation_threshold'] = 0.06  # Looser correlation
        
        # Adjust leverage based on volatility
        market_volatility = current_performance.get('market_volatility', 0.02)
        if market_volatility > 0.05:
            params['leverage_multiplier'] = 0.8  # Reduce leverage in high volatility
        else:
            params['leverage_multiplier'] = 1.0
            
        return params
    
    def get_time_based_adjustments(self) -> Dict:
        """Get time-based parameter adjustments"""
        from datetime import datetime
        
        current_time = datetime.utcnow().time()
        adjustments = {}
        
        # More aggressive during high-activity hours
        for start, end in self.parameters.HIGH_ACTIVITY_HOURS:
            if start <= current_time <= end:
                adjustments['activity_multiplier'] = 1.3
                adjustments['signal_frequency_boost'] = True
                break
        else:
            adjustments['activity_multiplier'] = 0.8
            adjustments['signal_frequency_boost'] = False
            
        # Avoid trading during low liquidity hours
        if time(0, 0) <= current_time <= time(4, 0):  # UTC midnight to 4 AM
            adjustments['trading_suspended'] = True
        else:
            adjustments['trading_suspended'] = False
            
        return adjustments
    
    def validate_config(self) -> Dict:
        """Validate configuration parameters"""
        validation_results = {'valid': True, 'warnings': [], 'errors': []}
        
        # Check risk parameters
        if self.parameters.STOP_LOSS_PERCENT >= self.parameters.TAKE_PROFIT_PERCENT:
            validation_results['errors'].append(
                "Stop loss should be smaller than take profit"
            )
            validation_results['valid'] = False
            
        # Check position sizing
        if self.parameters.BASE_POSITION_SIZE > 0.25:
            validation_results['warnings'].append(
                "Base position size above 25% is risky for scalping"
            )
            
        # Check leverage settings
        if self.parameters.OPTIMAL_LEVERAGE > 10:
            validation_results['warnings'].append(
                "Leverage above 10x increases liquidation risk"
            )
            
        # Check trading frequency
        if self.parameters.TARGET_TRADES_PER_DAY > 40:
            validation_results['warnings'].append(
                "High trade frequency may increase transaction costs"
            )
            
        return validation_results


# Global instance
scalping_config = ScalpingConfig()

# Validation on import
validation = scalping_config.validate_config()
if not validation['valid']:
    raise ValueError(f"Invalid scalping configuration: {validation['errors']}")