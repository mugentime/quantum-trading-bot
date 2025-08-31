#!/usr/bin/env python3
"""
High Volatility Trading Configuration
Optimized parameters for extreme volatility pairs trading
"""

from enum import Enum

class VolatilityTier(Enum):
    ULTRA_HIGH = "ultra_high"
    HIGH = "high"  
    MEDIUM = "medium"
    STANDARD = "standard"

# High-volatility pairs configuration
HIGH_VOLATILITY_PAIRS = {
    # TIER 1: ULTRA-HIGH VOLATILITY (300%+ monthly potential)
    'AXSUSDT': {
        'tier': VolatilityTier.ULTRA_HIGH,
        'priority': 1,
        'avg_daily_volatility': 0.152,  # 15.2%
        'max_position_pct': 0.02,       # 2% max position
        'stop_loss_pct': 0.015,         # 1.5% stop loss
        'take_profit_pct': 0.04,        # 4% take profit
        'timeframes': ['1m', '3m', '5m'],
        'max_hold_minutes': 15,
        'correlation_threshold': 0.12,
        'sector': 'gaming'
    },
    
    # TIER 2: HIGH VOLATILITY (200%+ monthly potential)
    'GALAUSDT': {
        'tier': VolatilityTier.HIGH,
        'priority': 2,
        'avg_daily_volatility': 0.087,  # 8.7%
        'max_position_pct': 0.03,       # 3% max position
        'stop_loss_pct': 0.02,          # 2% stop loss
        'take_profit_pct': 0.05,        # 5% take profit
        'timeframes': ['5m', '15m', '30m'],
        'max_hold_minutes': 60,
        'correlation_threshold': 0.08,
        'sector': 'gaming'
    },
    
    'SUSHIUSDT': {
        'tier': VolatilityTier.HIGH,
        'priority': 3,
        'avg_daily_volatility': 0.079,  # 7.9%
        'max_position_pct': 0.03,       # 3% max position
        'stop_loss_pct': 0.02,          # 2% stop loss
        'take_profit_pct': 0.05,        # 5% take profit
        'timeframes': ['5m', '15m', '30m'],
        'max_hold_minutes': 60,
        'correlation_threshold': 0.08,
        'sector': 'defi'
    },
    
    'SANDUSDT': {
        'tier': VolatilityTier.HIGH,
        'priority': 4,
        'avg_daily_volatility': 0.068,  # 6.8%
        'max_position_pct': 0.035,      # 3.5% max position
        'stop_loss_pct': 0.022,         # 2.2% stop loss
        'take_profit_pct': 0.055,       # 5.5% take profit
        'timeframes': ['15m', '30m', '1h'],
        'max_hold_minutes': 120,
        'correlation_threshold': 0.07,
        'sector': 'gaming'
    },
    
    # TIER 3: MEDIUM VOLATILITY (150%+ monthly potential)
    'AVAXUSDT': {
        'tier': VolatilityTier.MEDIUM,
        'priority': 5,
        'avg_daily_volatility': 0.058,  # 5.8%
        'max_position_pct': 0.04,       # 4% max position
        'stop_loss_pct': 0.025,         # 2.5% stop loss
        'take_profit_pct': 0.06,        # 6% take profit
        'timeframes': ['15m', '1h', '4h'],
        'max_hold_minutes': 240,
        'correlation_threshold': 0.06,
        'sector': 'layer1'
    },
    
    # ETHUSDT maintained as reference/baseline
    'ETHUSDT': {
        'tier': VolatilityTier.STANDARD,
        'priority': 6,
        'avg_daily_volatility': 0.035,  # 3.5%
        'max_position_pct': 0.05,       # 5% max position
        'stop_loss_pct': 0.03,          # 3% stop loss
        'take_profit_pct': 0.07,        # 7% take profit
        'timeframes': ['1h', '4h', '1d'],
        'max_hold_minutes': 480,
        'correlation_threshold': 0.04,
        'sector': 'layer1'
    }
}

# Portfolio risk management
PORTFOLIO_RISK_CONFIG = {
    'max_total_exposure': 0.08,         # 8% max total portfolio exposure
    'max_correlation_exposure': 0.50,   # 50% max correlated exposure
    'max_daily_drawdown': 0.12,         # 12% max daily loss
    'max_positions_per_sector': 3,      # Max 3 positions per sector
    'correlation_exit_threshold': 0.9,  # Exit all if correlation >90%
    'volatility_reduction_trigger': 0.15  # Reduce sizes if market vol >15%
}

# Sector correlations for risk management
SECTOR_CORRELATIONS = {
    'gaming': ['AXSUSDT', 'GALAUSDT', 'SANDUSDT'],
    'defi': ['SUSHIUSDT'],
    'layer1': ['AVAXUSDT', 'ETHUSDT']
}

# Signal generation parameters by tier
SIGNAL_PARAMETERS = {
    VolatilityTier.ULTRA_HIGH: {
        'confidence_threshold': 0.75,
        'entry_threshold': 0.12,
        'volume_threshold': 2.0,        # 2x average volume
        'momentum_threshold': 0.08,     # 8% momentum
        'signal_interval_seconds': 30   # 30 second intervals
    },
    VolatilityTier.HIGH: {
        'confidence_threshold': 0.65,
        'entry_threshold': 0.08,
        'volume_threshold': 1.5,        # 1.5x average volume
        'momentum_threshold': 0.05,     # 5% momentum
        'signal_interval_seconds': 45   # 45 second intervals
    },
    VolatilityTier.MEDIUM: {
        'confidence_threshold': 0.55,
        'entry_threshold': 0.06,
        'volume_threshold': 1.3,        # 1.3x average volume
        'momentum_threshold': 0.03,     # 3% momentum
        'signal_interval_seconds': 60   # 60 second intervals
    },
    VolatilityTier.STANDARD: {
        'confidence_threshold': 0.50,
        'entry_threshold': 0.04,
        'volume_threshold': 1.2,        # 1.2x average volume
        'momentum_threshold': 0.02,     # 2% momentum
        'signal_interval_seconds': 90   # 90 second intervals
    }
}

# Expected performance targets
PERFORMANCE_TARGETS = {
    'monthly_return_target': 3.0,       # 300% monthly target
    'monthly_return_minimum': 1.5,      # 150% monthly minimum
    'max_drawdown_limit': 0.25,         # 25% max drawdown
    'win_rate_target': 0.65,            # 65% win rate target
    'sharpe_ratio_target': 2.5,         # 2.5 Sharpe ratio target
    'profit_factor_target': 2.0         # 2.0 profit factor target
}