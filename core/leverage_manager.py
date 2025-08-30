"""
Advanced Leverage Management System
Handles dynamic leverage calculation, risk management, and optimization
"""
import logging
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from .config.settings import config

logger = logging.getLogger(__name__)

class LeverageManager:
    """Manages dynamic leverage optimization and risk controls"""
    
    def __init__(self):
        self.daily_pnl = 0.0
        self.daily_start = datetime.now().date()
        self.recent_trades = []
        self.current_margin_usage = 0.0
        self.volatility_cache = {}
        
    async def calculate_optimal_leverage(self, signal: Dict, account_balance: float, 
                                       recent_performance: Optional[float] = None,
                                       exchange = None) -> int:
        """
        Calculate optimal leverage based on signal strength, market conditions, and risk parameters
        
        Args:
            signal: Trading signal with correlation and deviation data
            account_balance: Current account balance
            recent_performance: Recent win rate (0-1)
            
        Returns:
            Optimal leverage multiplier (10-30x)
        """
        try:
            # Extract signal parameters
            deviation = signal.get('deviation', 0.15)
            correlation = signal.get('correlation', 0.5)
            symbol = signal.get('symbol', 'BTCUSDT')
            
            # Start with base leverage from signal strength
            base_leverage = self._get_leverage_from_signal_strength(deviation)
            
            # Apply performance multiplier
            performance_adjusted = self._apply_performance_adjustment(
                base_leverage, recent_performance or self._calculate_recent_win_rate()
            )
            
            # Apply volatility adjustment
            volatility_adjusted = await self._apply_volatility_adjustment(
                performance_adjusted, symbol, exchange
            )
            
            # Apply risk constraints
            final_leverage = self._apply_risk_constraints(
                volatility_adjusted, account_balance
            )
            
            # Ensure within bounds
            final_leverage = max(config.MIN_LEVERAGE, 
                               min(config.MAX_LEVERAGE, final_leverage))
            
            logger.info(f"Leverage calculation for {symbol}: "
                       f"base={base_leverage}, performance_adj={performance_adjusted}, "
                       f"volatility_adj={volatility_adjusted}, final={final_leverage}")
            
            return int(final_leverage)
            
        except Exception as e:
            logger.error(f"Error calculating optimal leverage: {e}")
            return config.DEFAULT_LEVERAGE
    
    def _get_leverage_from_signal_strength(self, deviation: float) -> int:
        """Determine base leverage from correlation deviation strength"""
        if deviation > 0.50:
            return config.LEVERAGE_TIERS['extreme_confidence']
        elif deviation > 0.30:
            return config.LEVERAGE_TIERS['high_confidence']
        elif deviation > 0.20:
            return config.LEVERAGE_TIERS['medium_confidence']
        else:
            return config.LEVERAGE_TIERS['base']
    
    def _apply_performance_adjustment(self, base_leverage: int, 
                                    recent_win_rate: float) -> int:
        """Adjust leverage based on recent trading performance"""
        try:
            # Performance multiplier based on recent success
            if recent_win_rate > 0.70:  # Very successful
                multiplier = 1.15
            elif recent_win_rate > 0.60:  # Good performance
                multiplier = 1.10
            elif recent_win_rate > 0.50:  # Above average
                multiplier = 1.05
            elif recent_win_rate > 0.40:  # Below average
                multiplier = 0.95
            else:  # Poor performance
                multiplier = 0.85
            
            adjusted_leverage = base_leverage * multiplier
            return int(adjusted_leverage)
            
        except Exception as e:
            logger.error(f"Error in performance adjustment: {e}")
            return base_leverage
    
    async def _apply_volatility_adjustment(self, base_leverage: int, symbol: str, 
                                         exchange = None) -> int:
        """Adjust leverage based on current market volatility using advanced volatility analysis"""
        try:
            if not exchange:
                logger.warning("No exchange provided for volatility adjustment")
                return base_leverage
            
            # Import here to avoid circular imports
            from .volatility_manager import volatility_manager
            
            # Get volatility-adjusted leverage
            volatility_adjusted = await volatility_manager.calculate_volatility_adjusted_leverage(
                base_leverage, symbol, exchange
            )
            
            return volatility_adjusted
            
        except Exception as e:
            logger.error(f"Error in volatility adjustment: {e}")
            # Fallback: simple conservative adjustment
            return int(base_leverage * 0.95)
    
    def _apply_risk_constraints(self, base_leverage: int, account_balance: float) -> int:
        """Apply risk management constraints"""
        try:
            # Check daily drawdown
            if self._check_daily_drawdown_exceeded():
                logger.warning("Daily drawdown limit reached, reducing leverage")
                return max(config.MIN_LEVERAGE, int(base_leverage * 0.7))
            
            # Check margin usage
            if self.current_margin_usage > config.MAX_MARGIN_USAGE:
                logger.warning("High margin usage, reducing leverage")
                return max(config.MIN_LEVERAGE, int(base_leverage * 0.8))
            
            # Account size adjustment (larger accounts can handle slightly more leverage)
            if account_balance > 10000:
                size_multiplier = min(1.1, 1 + (account_balance - 10000) / 100000)
                base_leverage = int(base_leverage * size_multiplier)
            
            return base_leverage
            
        except Exception as e:
            logger.error(f"Error in risk constraints: {e}")
            return base_leverage
    
    def calculate_optimal_position_size(self, signal: Dict, account_balance: float,
                                      leverage: int) -> float:
        """
        Calculate optimal position size based on Kelly criterion and risk parameters
        
        Args:
            signal: Trading signal data
            account_balance: Current balance
            leverage: Selected leverage multiplier
            
        Returns:
            Position size as percentage of balance (0.01 = 1%)
        """
        try:
            deviation = signal.get('deviation', 0.15)
            
            # Base position size
            base_position = config.RISK_PER_TRADE
            
            # Signal strength multiplier (stronger signals get larger positions)
            signal_multiplier = min(2.0, 1 + (deviation - 0.15) * 2)
            
            # Risk adjustment for leverage
            leverage_adjustment = min(1.2, 15 / leverage)  # Reduce size for higher leverage
            
            # Calculate final position size
            position_size = base_position * signal_multiplier * leverage_adjustment
            
            # Apply maximum limits
            max_position = min(config.MAX_POSITION_RISK / leverage, 0.05)  # Never more than 5%
            position_size = min(position_size, max_position)
            
            # Minimum position size
            position_size = max(position_size, 0.005)  # At least 0.5%
            
            logger.debug(f"Position size calculation: base={base_position}, "
                        f"signal_mult={signal_multiplier}, lev_adj={leverage_adjustment}, "
                        f"final={position_size}")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return config.RISK_PER_TRADE
    
    def calculate_safe_leverage(self, account_balance: float, symbol: str,
                              max_drawdown: float = 0.20) -> int:
        """Calculate safe leverage to prevent liquidation"""
        try:
            # Estimate volatility (simplified)
            daily_volatility = 0.05  # 5% daily volatility assumption for crypto
            
            # Account size factor
            size_factor = min(1.5, account_balance / 5000)
            
            # Base safe leverage calculation
            # Ensure liquidation price is at least max_drawdown away
            max_safe_leverage = 1 / (max_drawdown + 0.02)  # 2% buffer
            
            # Apply volatility adjustment
            volatility_adjusted = max_safe_leverage * (0.02 / daily_volatility)
            
            # Apply size factor
            final_safe_leverage = volatility_adjusted * size_factor
            
            # Ensure within reasonable bounds
            safe_leverage = max(config.MIN_LEVERAGE, 
                              min(config.MAX_LEVERAGE, int(final_safe_leverage)))
            
            return safe_leverage
            
        except Exception as e:
            logger.error(f"Error calculating safe leverage: {e}")
            return config.MIN_LEVERAGE
    
    def update_daily_pnl(self, trade_pnl: float):
        """Update daily P&L tracking"""
        try:
            current_date = datetime.now().date()
            
            # Reset daily tracking if new day
            if current_date != self.daily_start:
                self.daily_pnl = 0.0
                self.daily_start = current_date
            
            self.daily_pnl += trade_pnl
            
        except Exception as e:
            logger.error(f"Error updating daily PnL: {e}")
    
    def _check_daily_drawdown_exceeded(self) -> bool:
        """Check if daily drawdown limit has been exceeded"""
        try:
            return self.daily_pnl < -config.MAX_DAILY_DRAWDOWN
        except Exception as e:
            logger.error(f"Error checking daily drawdown: {e}")
            return False
    
    def add_trade_result(self, trade_result: Dict):
        """Add completed trade to recent performance tracking"""
        try:
            # Keep only last 20 trades for performance calculation
            self.recent_trades.append({
                'pnl': trade_result.get('pnl_usd', 0),
                'timestamp': datetime.now(),
                'success': trade_result.get('pnl_usd', 0) > 0
            })
            
            # Keep only recent trades (last 20)
            if len(self.recent_trades) > 20:
                self.recent_trades = self.recent_trades[-20:]
                
        except Exception as e:
            logger.error(f"Error adding trade result: {e}")
    
    def _calculate_recent_win_rate(self) -> float:
        """Calculate win rate from recent trades"""
        try:
            if not self.recent_trades:
                return 0.5  # Default to 50% if no data
            
            wins = sum(1 for trade in self.recent_trades if trade['success'])
            return wins / len(self.recent_trades)
            
        except Exception as e:
            logger.error(f"Error calculating win rate: {e}")
            return 0.5
    
    def get_leverage_metrics(self) -> Dict:
        """Get current leverage utilization metrics"""
        try:
            return {
                'daily_pnl': self.daily_pnl,
                'daily_drawdown_limit': config.MAX_DAILY_DRAWDOWN,
                'current_margin_usage': self.current_margin_usage,
                'max_margin_usage': config.MAX_MARGIN_USAGE,
                'recent_win_rate': self._calculate_recent_win_rate(),
                'total_recent_trades': len(self.recent_trades),
                'risk_status': 'normal' if not self._check_daily_drawdown_exceeded() else 'reduced'
            }
            
        except Exception as e:
            logger.error(f"Error getting leverage metrics: {e}")
            return {}
    
    def should_reduce_leverage(self) -> bool:
        """Determine if leverage should be reduced due to risk conditions"""
        return (self._check_daily_drawdown_exceeded() or 
                self.current_margin_usage > config.MAX_MARGIN_USAGE or
                self._calculate_recent_win_rate() < 0.3)
    
    def calculate_optimal_leverage_sync(self, signal: Dict, account_balance: float, 
                                      recent_performance: Optional[float] = None) -> int:
        """Synchronous version for testing (without volatility adjustment)"""
        try:
            deviation = signal.get('deviation', 0.15)
            
            # Start with base leverage from signal strength
            base_leverage = self._get_leverage_from_signal_strength(deviation)
            
            # Apply performance multiplier
            performance_adjusted = self._apply_performance_adjustment(
                base_leverage, recent_performance or self._calculate_recent_win_rate()
            )
            
            # Apply risk constraints (skip volatility for sync version)
            final_leverage = self._apply_risk_constraints(
                performance_adjusted, account_balance
            )
            
            # Ensure within bounds
            final_leverage = max(config.MIN_LEVERAGE, 
                               min(config.MAX_LEVERAGE, final_leverage))
            
            return int(final_leverage)
            
        except Exception as e:
            logger.error(f"Error calculating optimal leverage (sync): {e}")
            return config.DEFAULT_LEVERAGE

# Global instance
leverage_manager = LeverageManager()