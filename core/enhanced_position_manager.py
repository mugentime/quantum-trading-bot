"""
Enhanced Position Manager with Intelligent Leverage Utilization
Handles position sizing, leverage amplification, and risk scaling
"""
import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from .enhanced_leverage_config import enhanced_leverage_config
from .leverage_manager import leverage_manager
import ccxt

logger = logging.getLogger(__name__)

class EnhancedPositionManager:
    """Advanced position management with intelligent leverage scaling"""
    
    def __init__(self):
        self.active_positions = {}
        self.position_history = []
        self.daily_leverage_usage = {}
        self.risk_budget_remaining = 1.0  # 100% of daily risk budget
        self.leverage_heat_map = {}  # Track leverage usage by pair
        
    async def calculate_optimal_position_parameters(self, signal: Dict, 
                                                  account_balance: float,
                                                  exchange: Any,
                                                  market_data: Dict) -> Dict:
        """
        Calculate optimal position parameters including leverage and size
        
        Args:
            signal: Trading signal with correlation/deviation data
            account_balance: Current account balance
            exchange: Exchange instance for market data
            market_data: Current market conditions
            
        Returns:
            Dict with position parameters: leverage, size, stop_loss, take_profit
        """
        try:
            symbol = signal.get('symbol', 'BTCUSDT')
            signal_strength = signal.get('deviation', 0.15)
            correlation = signal.get('correlation', 0.5)
            
            # Get recent performance for the pair
            recent_performance = await self._get_recent_performance(symbol)
            
            # Determine market conditions
            market_conditions = await self._assess_market_conditions(symbol, exchange, market_data)
            
            # Calculate optimal leverage using enhanced configuration
            optimal_leverage, leverage_adjustments = enhanced_leverage_config.calculate_dynamic_leverage(
                symbol=symbol,
                signal_strength=signal_strength,
                recent_performance=recent_performance,
                market_conditions=market_conditions,
                account_balance=account_balance
            )
            
            # Check if high leverage trade should be entered
            if not enhanced_leverage_config.should_enter_high_leverage_trade(
                symbol, optimal_leverage, len(self.active_positions), recent_performance
            ):
                # Fallback to conservative leverage
                optimal_leverage = max(10, int(optimal_leverage * 0.7))
                logger.warning(f"Reducing leverage for {symbol} due to risk conditions: {optimal_leverage}x")
            
            # Calculate position size
            position_size = enhanced_leverage_config.get_position_size_adjustment(
                optimal_leverage, signal_strength, account_balance
            )
            
            # Adjust for remaining risk budget
            position_size *= self.risk_budget_remaining
            
            # Calculate stop loss and take profit based on leverage
            stop_loss_pct, take_profit_pct = self._calculate_stop_take_levels(
                optimal_leverage, signal_strength, symbol
            )
            
            # Get liquidation-safe parameters
            safe_params = await self._ensure_liquidation_safety(
                symbol, optimal_leverage, position_size, account_balance, exchange
            )
            
            position_params = {
                'leverage': safe_params['leverage'],
                'position_size_pct': safe_params['position_size'],
                'position_value': account_balance * safe_params['position_size'],
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': take_profit_pct,
                'max_loss_usd': account_balance * safe_params['position_size'] * stop_loss_pct,
                'expected_profit_usd': account_balance * safe_params['position_size'] * take_profit_pct,
                'leverage_adjustments': leverage_adjustments,
                'risk_reward_ratio': take_profit_pct / stop_loss_pct,
                'liquidation_price': safe_params.get('liquidation_price', 0),
                'margin_required': safe_params.get('margin_required', 0),
                'confidence_score': self._calculate_confidence_score(signal, recent_performance)
            }
            
            logger.info(f"Position parameters for {symbol}: "
                       f"Leverage={optimal_leverage}x, Size={position_size:.3f}%, "
                       f"Stop={stop_loss_pct:.2f}%, Take={take_profit_pct:.2f}%")
            
            return position_params
            
        except Exception as e:
            logger.error(f"Error calculating position parameters: {e}")
            return self._get_fallback_parameters(signal, account_balance)
    
    async def _get_recent_performance(self, symbol: str, lookback_days: int = 7) -> Dict:
        """Get recent trading performance for the symbol"""
        try:
            # Filter position history for the symbol
            recent_trades = [
                trade for trade in self.position_history[-50:]  # Last 50 trades
                if trade.get('symbol') == symbol and 
                trade.get('exit_time', datetime.now()) > datetime.now() - timedelta(days=lookback_days)
            ]
            
            if not recent_trades:
                return {'win_rate': 0.5, 'return': 0.0, 'trades': 0, 'avg_hold_time': 4}
            
            wins = sum(1 for trade in recent_trades if trade.get('pnl_usd', 0) > 0)
            total_return = sum(trade.get('pnl_pct', 0) for trade in recent_trades) / 100
            avg_hold_time = np.mean([trade.get('hold_time_hours', 4) for trade in recent_trades])
            
            return {
                'win_rate': wins / len(recent_trades),
                'return': total_return,
                'trades': len(recent_trades),
                'avg_hold_time': avg_hold_time
            }
            
        except Exception as e:
            logger.error(f"Error getting recent performance: {e}")
            return {'win_rate': 0.5, 'return': 0.0, 'trades': 0, 'avg_hold_time': 4}
    
    async def _assess_market_conditions(self, symbol: str, exchange: Any, 
                                      market_data: Dict) -> List[str]:
        """Assess current market conditions for leverage adjustment"""
        try:
            conditions = []
            
            # Time-based conditions
            current_hour = datetime.now().hour
            
            if 0 <= current_hour <= 8:  # Asian session
                conditions.append('asian_session')
            elif 8 <= current_hour <= 16:  # London session
                conditions.append('london_session')
            else:  # US session
                conditions.append('us_session')
            
            # Weekend condition
            if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
                conditions.append('weekend')
            
            # Volatility assessment
            if exchange:
                try:
                    # Get recent 24h ticker data
                    ticker = await exchange.fetch_ticker(symbol)
                    daily_change = abs(ticker.get('percentage', 0))
                    
                    if daily_change > 8:  # High volatility threshold
                        conditions.append('high_volatility')
                    elif daily_change < 2:  # Low volatility threshold
                        conditions.append('low_volatility')
                        
                except Exception as e:
                    logger.debug(f"Could not assess volatility for {symbol}: {e}")
            
            # Market trend assessment (simplified)
            btc_change = market_data.get('btc_24h_change', 0)
            if btc_change > 5:
                conditions.append('bull_market')
            elif btc_change < -5:
                conditions.append('bear_market')
            else:
                conditions.append('sideways')
            
            logger.debug(f"Market conditions for {symbol}: {conditions}")
            return conditions
            
        except Exception as e:
            logger.error(f"Error assessing market conditions: {e}")
            return ['sideways']  # Default to neutral condition
    
    def _calculate_stop_take_levels(self, leverage: int, signal_strength: float, 
                                  symbol: str) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels based on leverage and signal"""
        try:
            # Base levels
            base_stop = 0.02  # 2% stop loss
            base_take = 0.04  # 4% take profit (2:1 ratio)
            
            # Adjust for leverage (higher leverage = tighter stops)
            leverage_adjustment = min(1.0, 20.0 / leverage)
            adjusted_stop = base_stop * leverage_adjustment
            
            # Adjust for signal strength (stronger signals = wider targets)
            signal_adjustment = 0.8 + (signal_strength * 0.8)  # 0.8x to 1.6x multiplier
            adjusted_take = base_take * signal_adjustment
            
            # Pair-specific adjustments
            pair_multiplier = self._get_pair_volatility_multiplier(symbol)
            adjusted_stop *= pair_multiplier
            adjusted_take *= pair_multiplier
            
            # Ensure minimum risk-reward ratio of 1.5:1
            min_take = adjusted_stop * 1.5
            adjusted_take = max(adjusted_take, min_take)
            
            # Apply bounds
            adjusted_stop = max(0.005, min(0.04, adjusted_stop))  # 0.5% to 4%
            adjusted_take = max(0.01, min(0.08, adjusted_take))   # 1% to 8%
            
            logger.debug(f"Stop/Take for {symbol} at {leverage}x: "
                        f"Stop={adjusted_stop:.3f}%, Take={adjusted_take:.3f}%")
            
            return adjusted_stop, adjusted_take
            
        except Exception as e:
            logger.error(f"Error calculating stop/take levels: {e}")
            return 0.02, 0.04  # Fallback levels
    
    def _get_pair_volatility_multiplier(self, symbol: str) -> float:
        """Get volatility-based multiplier for stop/take levels"""
        volatility_multipliers = {
            'BTCUSDT': 0.9,   # Lower volatility
            'ETHUSDT': 1.0,   # Standard
            'SOLUSDT': 1.2,   # Higher volatility
            'ADAUSDT': 1.1,
            'AVAXUSDT': 1.15,
            'BNBUSDT': 1.0,
            'XRPUSDT': 1.1,
            'DOGEUSDT': 1.3   # Highest volatility
        }
        return volatility_multipliers.get(symbol, 1.0)
    
    async def _ensure_liquidation_safety(self, symbol: str, leverage: int, 
                                       position_size: float, account_balance: float,
                                       exchange: Any) -> Dict:
        """Ensure position parameters won't lead to liquidation"""
        try:
            if not exchange:
                return {'leverage': leverage, 'position_size': position_size}
            
            # Get current price
            ticker = await exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Calculate position value and margin required
            position_value = account_balance * position_size
            margin_required = position_value / leverage
            
            # Calculate liquidation price (simplified)
            # For long: liquidation_price = entry_price * (1 - margin_ratio)
            # For short: liquidation_price = entry_price * (1 + margin_ratio)
            margin_ratio = 1 / leverage
            safe_margin_buffer = 0.02  # 2% additional safety buffer
            
            # Ensure liquidation price is at least 25% away from current price
            min_liquidation_distance = 0.25
            max_safe_leverage = int(1 / (min_liquidation_distance + safe_margin_buffer))
            
            if leverage > max_safe_leverage:
                logger.warning(f"Reducing leverage for {symbol} from {leverage}x to {max_safe_leverage}x for safety")
                leverage = max_safe_leverage
                margin_required = position_value / leverage
            
            # Ensure margin requirement doesn't exceed account balance
            if margin_required > account_balance * 0.8:  # Max 80% of balance as margin
                max_safe_position = (account_balance * 0.8) * leverage / account_balance
                logger.warning(f"Reducing position size for {symbol} from {position_size:.3f}% to {max_safe_position:.3f}%")
                position_size = max_safe_position
                position_value = account_balance * position_size
                margin_required = position_value / leverage
            
            liquidation_price_long = current_price * (1 - (margin_ratio + safe_margin_buffer))
            liquidation_price_short = current_price * (1 + (margin_ratio + safe_margin_buffer))
            
            return {
                'leverage': leverage,
                'position_size': position_size,
                'liquidation_price': liquidation_price_long,  # Assuming long for example
                'margin_required': margin_required,
                'margin_ratio': margin_ratio,
                'safety_buffer': safe_margin_buffer
            }
            
        except Exception as e:
            logger.error(f"Error ensuring liquidation safety: {e}")
            return {'leverage': min(leverage, 20), 'position_size': min(position_size, 0.03)}
    
    def _calculate_confidence_score(self, signal: Dict, recent_performance: Dict) -> float:
        """Calculate overall confidence score for the trade"""
        try:
            # Signal strength component (0-40 points)
            signal_score = min(40, signal.get('deviation', 0.15) * 100)
            
            # Correlation component (0-20 points)
            correlation_score = min(20, abs(signal.get('correlation', 0.5)) * 20)
            
            # Recent performance component (0-40 points)
            win_rate = recent_performance.get('win_rate', 0.5)
            return_rate = recent_performance.get('return', 0.0)
            performance_score = min(40, (win_rate * 20) + (max(0, return_rate) * 100))
            
            # Total confidence (0-100)
            total_confidence = signal_score + correlation_score + performance_score
            
            return min(100, total_confidence) / 100  # Normalize to 0-1
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _get_fallback_parameters(self, signal: Dict, account_balance: float) -> Dict:
        """Get conservative fallback parameters in case of errors"""
        return {
            'leverage': 10,
            'position_size_pct': 0.015,  # 1.5%
            'position_value': account_balance * 0.015,
            'stop_loss_pct': 0.025,
            'take_profit_pct': 0.05,
            'max_loss_usd': account_balance * 0.015 * 0.025,
            'expected_profit_usd': account_balance * 0.015 * 0.05,
            'risk_reward_ratio': 2.0,
            'liquidation_price': 0,
            'margin_required': account_balance * 0.0015,
            'confidence_score': 0.5
        }
    
    async def monitor_position_risk(self, position: Dict, current_price: float,
                                  account_balance: float) -> Dict:
        """Monitor existing position and suggest adjustments"""
        try:
            entry_price = position.get('entry_price', current_price)
            leverage = position.get('leverage', 10)
            position_size = position.get('position_size', 0.02)
            side = position.get('side', 'BUY')
            
            # Calculate current P&L
            if side == 'BUY':
                unrealized_pnl_pct = (current_price - entry_price) / entry_price
            else:
                unrealized_pnl_pct = (entry_price - current_price) / entry_price
            
            # Apply leverage
            leveraged_pnl_pct = unrealized_pnl_pct * leverage
            unrealized_pnl_usd = account_balance * position_size * leveraged_pnl_pct
            
            # Calculate distance to liquidation
            margin_ratio = 1 / leverage
            if side == 'BUY':
                liquidation_price = entry_price * (1 - margin_ratio + 0.02)
                liquidation_distance = (current_price - liquidation_price) / current_price
            else:
                liquidation_price = entry_price * (1 + margin_ratio - 0.02)
                liquidation_distance = (liquidation_price - current_price) / current_price
            
            # Risk assessment
            risk_status = 'LOW'
            if liquidation_distance < 0.1:  # Within 10% of liquidation
                risk_status = 'CRITICAL'
            elif liquidation_distance < 0.2:  # Within 20% of liquidation
                risk_status = 'HIGH'
            elif liquidation_distance < 0.4:  # Within 40% of liquidation
                risk_status = 'MEDIUM'
            
            # Suggest actions
            actions = []
            if risk_status == 'CRITICAL':
                actions.append('CLOSE_POSITION')
                actions.append('REDUCE_LEVERAGE_IMMEDIATELY')
            elif risk_status == 'HIGH':
                actions.append('ADD_MARGIN')
                actions.append('REDUCE_LEVERAGE')
            elif leveraged_pnl_pct > 0.5:  # 50% profit
                actions.append('TAKE_PARTIAL_PROFIT')
            
            return {
                'unrealized_pnl_pct': leveraged_pnl_pct,
                'unrealized_pnl_usd': unrealized_pnl_usd,
                'liquidation_price': liquidation_price,
                'liquidation_distance': liquidation_distance,
                'risk_status': risk_status,
                'suggested_actions': actions
            }
            
        except Exception as e:
            logger.error(f"Error monitoring position risk: {e}")
            return {'risk_status': 'UNKNOWN', 'suggested_actions': ['MONITOR_MANUALLY']}
    
    def update_risk_budget(self, trade_result: Dict):
        """Update remaining risk budget after trade completion"""
        try:
            pnl_pct = trade_result.get('pnl_pct', 0) / 100
            
            # If losing trade, reduce risk budget
            if pnl_pct < 0:
                risk_used = abs(pnl_pct) / 0.10  # Normalize by 10% max daily loss
                self.risk_budget_remaining = max(0.2, self.risk_budget_remaining - risk_used)
            else:
                # If winning trade, slightly increase risk budget
                risk_gained = min(0.2, pnl_pct / 0.05)  # Normalize by 5% gain
                self.risk_budget_remaining = min(1.0, self.risk_budget_remaining + risk_gained * 0.5)
            
            logger.info(f"Updated risk budget: {self.risk_budget_remaining:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating risk budget: {e}")
    
    def reset_daily_limits(self):
        """Reset daily risk limits (call at start of each day)"""
        self.risk_budget_remaining = 1.0
        self.daily_leverage_usage = {}
        logger.info("Daily risk limits reset")
    
    def get_portfolio_leverage_exposure(self) -> Dict:
        """Get current portfolio leverage exposure"""
        try:
            total_leverage_exposure = 0
            position_exposures = {}
            
            for symbol, position in self.active_positions.items():
                leverage = position.get('leverage', 1)
                position_size = position.get('position_size', 0)
                exposure = leverage * position_size
                
                total_leverage_exposure += exposure
                position_exposures[symbol] = {
                    'leverage': leverage,
                    'position_size': position_size,
                    'leverage_exposure': exposure
                }
            
            return {
                'total_leverage_exposure': total_leverage_exposure,
                'position_exposures': position_exposures,
                'risk_budget_used': 1.0 - self.risk_budget_remaining,
                'max_additional_exposure': max(0, 2.0 - total_leverage_exposure)  # Max 200% leverage exposure
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio exposure: {e}")
            return {'total_leverage_exposure': 0, 'position_exposures': {}}

# Global instance
enhanced_position_manager = EnhancedPositionManager()