"""
Enhanced Leverage Configuration System
Dynamic leverage scaling based on performance, volatility, and market conditions
"""
import os
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass

@dataclass
class LeverageProfile:
    """Individual trading pair leverage configuration"""
    symbol: str
    base_leverage: int
    max_leverage: int
    min_leverage: int
    volatility_adjustment: float
    performance_multiplier: float
    risk_tier: str
    
class EnhancedLeverageConfig:
    """Advanced leverage configuration with dynamic scaling"""
    
    def __init__(self):
        self.pair_profiles = self._initialize_pair_profiles()
        self.market_condition_multipliers = self._initialize_market_conditions()
        self.performance_thresholds = self._initialize_performance_thresholds()
        
    def _initialize_pair_profiles(self) -> Dict[str, LeverageProfile]:
        """Initialize leverage profiles based on backtest performance"""
        return {
            # TIER 1: HIGHEST PERFORMING PAIRS
            'ETHUSDT': LeverageProfile(
                symbol='ETHUSDT',
                base_leverage=20,
                max_leverage=35,  # Can go up to 35x for exceptional setups
                min_leverage=10,
                volatility_adjustment=0.85,  # Slightly conservative due to ETH volatility
                performance_multiplier=1.15,  # 25.22% return, 62.9% win rate
                risk_tier='aggressive'
            ),
            
            'SOLUSDT': LeverageProfile(
                symbol='SOLUSDT',
                base_leverage=25,
                max_leverage=45,  # Highest performer gets highest leverage potential
                min_leverage=12,
                volatility_adjustment=0.80,  # More volatile, needs adjustment
                performance_multiplier=1.20,  # 20.42% return, 58.2% win rate + momentum
                risk_tier='aggressive'
            ),
            
            # TIER 2: STABLE PERFORMERS
            'ADAUSDT': LeverageProfile(
                symbol='ADAUSDT',
                base_leverage=18,
                max_leverage=30,
                min_leverage=8,
                volatility_adjustment=0.90,  # Generally more stable
                performance_multiplier=1.10,  # Based on mentioned +1.29% optimization
                risk_tier='moderate'
            ),
            
            'AVAXUSDT': LeverageProfile(
                symbol='AVAXUSDT',
                base_leverage=18,
                max_leverage=30,
                min_leverage=8,
                volatility_adjustment=0.88,
                performance_multiplier=1.10,  # +1.29% optimization result
                risk_tier='moderate'
            ),
            
            # TIER 3: CONSERVATIVE APPROACH
            'BTCUSDT': LeverageProfile(
                symbol='BTCUSDT',
                base_leverage=15,
                max_leverage=25,  # Conservative due to -0.16% performance
                min_leverage=5,
                volatility_adjustment=0.95,  # Most stable, least adjustment needed
                performance_multiplier=0.90,  # Reduce due to challenging performance
                risk_tier='conservative'
            ),
            
            # TIER 4: EXPERIMENTAL PAIRS (Lower leverage until proven)
            'BNBUSDT': LeverageProfile(
                symbol='BNBUSDT',
                base_leverage=12,
                max_leverage=22,
                min_leverage=5,
                volatility_adjustment=0.92,
                performance_multiplier=1.0,
                risk_tier='conservative'
            ),
            
            'XRPUSDT': LeverageProfile(
                symbol='XRPUSDT',
                base_leverage=12,
                max_leverage=22,
                min_leverage=5,
                volatility_adjustment=0.90,
                performance_multiplier=1.0,
                risk_tier='conservative'
            ),
            
            'DOGEUSDT': LeverageProfile(
                symbol='DOGEUSDT',
                base_leverage=10,
                max_leverage=20,
                min_leverage=5,
                volatility_adjustment=0.85,  # High volatility memecoin
                performance_multiplier=0.95,
                risk_tier='conservative'
            )
        }
    
    def _initialize_market_conditions(self) -> Dict[str, float]:
        """Market condition leverage multipliers"""
        return {
            'bull_market': 1.2,      # Increase leverage in bull markets
            'bear_market': 0.7,      # Reduce leverage in bear markets
            'sideways': 1.0,         # Standard leverage in ranging markets
            'high_volatility': 0.8,  # Reduce during high vol periods
            'low_volatility': 1.1,   # Slightly increase during low vol
            'weekend': 0.9,          # Conservative on weekends
            'asian_session': 1.05,   # Slightly higher during Asian hours
            'us_session': 0.95,      # Conservative during US hours
            'london_session': 1.0    # Standard during London hours
        }
    
    def _initialize_performance_thresholds(self) -> Dict[str, Dict]:
        """Performance-based leverage adjustment thresholds"""
        return {
            'excellent': {
                'win_rate_threshold': 0.70,
                'return_threshold': 0.15,
                'leverage_multiplier': 1.25,
                'max_position_risk': 0.04
            },
            'good': {
                'win_rate_threshold': 0.60,
                'return_threshold': 0.10,
                'leverage_multiplier': 1.15,
                'max_position_risk': 0.035
            },
            'average': {
                'win_rate_threshold': 0.50,
                'return_threshold': 0.05,
                'leverage_multiplier': 1.0,
                'max_position_risk': 0.03
            },
            'poor': {
                'win_rate_threshold': 0.40,
                'return_threshold': 0.0,
                'leverage_multiplier': 0.85,
                'max_position_risk': 0.02
            },
            'terrible': {
                'win_rate_threshold': 0.30,
                'return_threshold': -0.05,
                'leverage_multiplier': 0.7,
                'max_position_risk': 0.015
            }
        }
    
    def get_pair_profile(self, symbol: str) -> LeverageProfile:
        """Get leverage profile for a specific trading pair"""
        return self.pair_profiles.get(symbol, self._get_default_profile(symbol))
    
    def _get_default_profile(self, symbol: str) -> LeverageProfile:
        """Default conservative profile for unknown pairs"""
        return LeverageProfile(
            symbol=symbol,
            base_leverage=10,
            max_leverage=20,
            min_leverage=5,
            volatility_adjustment=0.90,
            performance_multiplier=0.95,
            risk_tier='conservative'
        )
    
    def calculate_dynamic_leverage(self, symbol: str, signal_strength: float,
                                 recent_performance: Dict, market_conditions: List[str],
                                 account_balance: float) -> Tuple[int, Dict]:
        """
        Calculate optimal leverage with dynamic adjustments
        
        Args:
            symbol: Trading pair
            signal_strength: Signal deviation/correlation strength (0-1)
            recent_performance: {'win_rate': 0.6, 'return': 0.15, 'trades': 20}
            market_conditions: List of current market conditions
            account_balance: Current account balance
            
        Returns:
            Tuple of (leverage, adjustment_details)
        """
        profile = self.get_pair_profile(symbol)
        
        # Start with base leverage
        current_leverage = profile.base_leverage
        adjustments = {'base': profile.base_leverage}
        
        # Signal strength adjustment (most important factor)
        signal_multiplier = 1 + (signal_strength - 0.15) * 1.5  # Scale from 0.15 baseline
        signal_multiplier = max(0.7, min(1.4, signal_multiplier))
        current_leverage *= signal_multiplier
        adjustments['signal_strength'] = signal_multiplier
        
        # Performance-based adjustment
        performance_category = self._categorize_performance(recent_performance)
        perf_multiplier = self.performance_thresholds[performance_category]['leverage_multiplier']
        current_leverage *= perf_multiplier
        adjustments['performance'] = perf_multiplier
        
        # Market condition adjustments
        market_multiplier = 1.0
        for condition in market_conditions:
            if condition in self.market_condition_multipliers:
                market_multiplier *= self.market_condition_multipliers[condition]
        current_leverage *= market_multiplier
        adjustments['market_conditions'] = market_multiplier
        
        # Volatility adjustment
        current_leverage *= profile.volatility_adjustment
        adjustments['volatility'] = profile.volatility_adjustment
        
        # Account size adjustment (larger accounts can handle more leverage)
        size_multiplier = min(1.15, 1 + (account_balance - 10000) / 50000)
        if account_balance > 10000:
            current_leverage *= size_multiplier
            adjustments['account_size'] = size_multiplier
        
        # Apply bounds
        final_leverage = max(profile.min_leverage, 
                           min(profile.max_leverage, int(current_leverage)))
        
        # Emergency conditions override
        if recent_performance.get('win_rate', 0.5) < 0.25:  # Very poor performance
            final_leverage = min(final_leverage, profile.min_leverage + 2)
            adjustments['emergency_override'] = True
        
        return final_leverage, adjustments
    
    def _categorize_performance(self, performance: Dict) -> str:
        """Categorize recent performance into tiers"""
        win_rate = performance.get('win_rate', 0.5)
        return_rate = performance.get('return', 0.0)
        
        if win_rate >= 0.70 and return_rate >= 0.15:
            return 'excellent'
        elif win_rate >= 0.60 and return_rate >= 0.10:
            return 'good'
        elif win_rate >= 0.50 and return_rate >= 0.05:
            return 'average'
        elif win_rate >= 0.40:
            return 'poor'
        else:
            return 'terrible'
    
    def get_position_size_adjustment(self, leverage: int, signal_strength: float,
                                   account_balance: float) -> float:
        """
        Calculate position size adjustment based on leverage and signal
        Higher leverage = smaller position size for same risk
        """
        # Base position size (2% of account)
        base_position = 0.02
        
        # Signal strength multiplier (stronger signals get larger positions)
        signal_multiplier = min(1.5, 0.8 + signal_strength)
        
        # Leverage adjustment (inverse relationship)
        leverage_adjustment = min(1.2, 15.0 / leverage)
        
        # Account size adjustment
        size_adjustment = min(1.1, 1 + (account_balance - 15000) / 100000) if account_balance > 15000 else 1.0
        
        position_size = base_position * signal_multiplier * leverage_adjustment * size_adjustment
        
        # Maximum position limits based on leverage
        if leverage > 40:
            max_position = 0.015  # 1.5% max for extreme leverage
        elif leverage > 30:
            max_position = 0.025  # 2.5% max for high leverage
        elif leverage > 20:
            max_position = 0.035  # 3.5% max for medium leverage
        else:
            max_position = 0.05   # 5% max for low leverage
        
        return min(position_size, max_position)
    
    def should_enter_high_leverage_trade(self, symbol: str, leverage: int, 
                                       current_positions: int, recent_performance: Dict) -> bool:
        """Determine if high leverage trade should be entered based on risk conditions"""
        
        # Never enter high leverage if performance is poor
        if recent_performance.get('win_rate', 0.5) < 0.4:
            return False
        
        # Limit high leverage trades based on current exposure
        if leverage > 25 and current_positions >= 2:
            return False
        
        if leverage > 35 and current_positions >= 1:
            return False
        
        # Only allow extreme leverage (>40x) for tier 1 pairs with excellent performance
        profile = self.get_pair_profile(symbol)
        if leverage > 40:
            return (profile.risk_tier == 'aggressive' and 
                   recent_performance.get('win_rate', 0) > 0.65 and
                   current_positions == 0)
        
        return True
    
    def get_emergency_leverage_reduction(self, current_leverage: int, 
                                       drawdown_pct: float) -> int:
        """Calculate emergency leverage reduction based on drawdown"""
        if drawdown_pct > 0.15:  # 15% drawdown
            return max(5, int(current_leverage * 0.5))  # Cut leverage in half
        elif drawdown_pct > 0.10:  # 10% drawdown
            return max(8, int(current_leverage * 0.7))  # Reduce by 30%
        elif drawdown_pct > 0.05:  # 5% drawdown
            return max(10, int(current_leverage * 0.85))  # Reduce by 15%
        
        return current_leverage

# Global instance
enhanced_leverage_config = EnhancedLeverageConfig()