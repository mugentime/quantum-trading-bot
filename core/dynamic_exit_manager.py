"""
Dynamic Exit Strategy Manager
Implements volatility-based dynamic exits and trending market detection
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from .config.settings import config

logger = logging.getLogger(__name__)

class DynamicExitManager:
    """Manages dynamic exit strategies based on market conditions"""
    
    def __init__(self):
        self.atr_period = 14
        self.trend_period = 20
        self.volatility_thresholds = {
            'very_low': 0.01,   # <1% ATR
            'low': 0.02,        # 1-2% ATR  
            'normal': 0.04,     # 2-4% ATR
            'high': 0.06,       # 4-6% ATR
            'extreme': 0.08     # >6% ATR
        }
        self.exit_timing_rules = {
            'very_low': {'min_minutes': 180, 'max_minutes': 240},  # 3-4 hours
            'low': {'min_minutes': 120, 'max_minutes': 180},       # 2-3 hours
            'normal': {'min_minutes': 90, 'max_minutes': 120},     # 1.5-2 hours
            'high': {'min_minutes': 45, 'max_minutes': 90},        # 45min-1.5h
            'extreme': {'min_minutes': 30, 'max_minutes': 60}      # 30min-1h
        }
        self.position_timings = {}
        
    async def calculate_dynamic_exit_timing(self, symbol: str, entry_price: float,
                                          entry_time: datetime, side: str,
                                          exchange = None) -> Dict:
        """
        Calculate optimal exit timing based on current market volatility
        
        Args:
            symbol: Trading symbol
            entry_price: Position entry price
            entry_time: Position entry time
            side: 'BUY' or 'SELL'
            exchange: Exchange interface for data
            
        Returns:
            Dynamic exit timing recommendation
        """
        try:
            if not exchange:
                logger.error("Exchange interface required for dynamic exit calculation")
                return self._get_default_exit_timing()
            
            # Calculate current ATR
            atr_data = await self._calculate_atr(symbol, exchange)
            if not atr_data:
                return self._get_default_exit_timing()
            
            current_atr = atr_data['current_atr']
            atr_percentage = atr_data['atr_percentage']
            
            # Determine volatility regime
            volatility_regime = self._classify_volatility_regime(atr_percentage)
            
            # Check for trending conditions
            trend_data = await self._detect_trend_strength(symbol, exchange)
            
            # Calculate base timing from volatility
            base_timing = self._get_base_timing_from_volatility(volatility_regime)
            
            # Adjust timing based on trend strength
            adjusted_timing = self._adjust_timing_for_trend(
                base_timing, trend_data, volatility_regime
            )
            
            # Calculate specific exit conditions
            exit_conditions = self._calculate_exit_conditions(
                entry_price, current_atr, atr_percentage, side, trend_data
            )
            
            # Determine recommended exit time
            current_time = datetime.now()
            position_age = (current_time - entry_time).total_seconds() / 60  # minutes
            
            exit_recommendation = self._generate_exit_recommendation(
                adjusted_timing, position_age, exit_conditions, trend_data
            )
            
            result = {
                'symbol': symbol,
                'volatility_regime': volatility_regime,
                'atr_percentage': atr_percentage,
                'trend_data': trend_data,
                'base_timing_minutes': base_timing,
                'adjusted_timing_minutes': adjusted_timing,
                'exit_conditions': exit_conditions,
                'exit_recommendation': exit_recommendation,
                'position_age_minutes': position_age,
                'calculated_at': current_time
            }
            
            # Store timing for this position
            position_key = f"{symbol}_{entry_time.strftime('%Y%m%d_%H%M%S')}"
            self.position_timings[position_key] = result
            
            logger.info(f"Dynamic exit timing calculated for {symbol}: "
                       f"regime={volatility_regime}, timing={adjusted_timing}min, "
                       f"recommendation={exit_recommendation['action']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating dynamic exit timing: {e}")
            return self._get_default_exit_timing()
    
    async def _calculate_atr(self, symbol: str, exchange, periods: Optional[int] = None) -> Optional[Dict]:
        """Calculate Average True Range for volatility measurement"""
        try:
            periods = periods or self.atr_period
            
            # Get recent price data
            from .data_collector import data_collector
            
            # Fetch recent hourly data for ATR calculation
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=periods + 5)  # Extra buffer
            
            candles = await data_collector.get_historical_data(
                symbol, '1h', start_time, end_time
            )
            
            if not candles or len(candles) < periods:
                logger.warning(f"Insufficient data for ATR calculation: {len(candles) if candles else 0}")
                return None
            
            # Calculate True Range for each period
            true_ranges = []
            for i in range(1, len(candles)):
                current = candles[i]
                previous = candles[i-1]
                
                high_low = current['high'] - current['low']
                high_close_prev = abs(current['high'] - previous['close'])
                low_close_prev = abs(current['low'] - previous['close'])
                
                true_range = max(high_low, high_close_prev, low_close_prev)
                true_ranges.append(true_range)
            
            if len(true_ranges) < periods:
                return None
            
            # Calculate ATR (Simple Moving Average of True Range)
            atr = np.mean(true_ranges[-periods:])
            current_price = candles[-1]['close']
            atr_percentage = (atr / current_price) * 100
            
            return {
                'current_atr': atr,
                'atr_percentage': atr_percentage,
                'current_price': current_price,
                'periods_used': periods
            }
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return None
    
    def _classify_volatility_regime(self, atr_percentage: float) -> str:
        """Classify current volatility regime based on ATR percentage"""
        atr_pct = atr_percentage / 100  # Convert to decimal
        
        if atr_pct < self.volatility_thresholds['very_low']:
            return 'very_low'
        elif atr_pct < self.volatility_thresholds['low']:
            return 'low'
        elif atr_pct < self.volatility_thresholds['normal']:
            return 'normal'
        elif atr_pct < self.volatility_thresholds['high']:
            return 'high'
        else:
            return 'extreme'
    
    async def _detect_trend_strength(self, symbol: str, exchange) -> Dict:
        """Detect trend strength and direction"""
        try:
            from .data_collector import data_collector
            
            # Get trend analysis data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=self.trend_period + 5)
            
            candles = await data_collector.get_historical_data(
                symbol, '1h', start_time, end_time
            )
            
            if not candles or len(candles) < self.trend_period:
                return {'strength': 0.0, 'direction': 'sideways', 'confidence': 0.0}
            
            # Calculate price momentum
            recent_candles = candles[-self.trend_period:]
            prices = [candle['close'] for candle in recent_candles]
            
            # Linear regression for trend direction
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices, 1)
            
            # Calculate trend strength (R-squared)
            y_pred = slope * x + intercept
            ss_res = np.sum((prices - y_pred) ** 2)
            ss_tot = np.sum((prices - np.mean(prices)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Determine trend direction
            price_change_pct = (prices[-1] - prices[0]) / prices[0] * 100
            
            if abs(price_change_pct) < 2:  # Less than 2% change
                direction = 'sideways'
            elif price_change_pct > 0:
                direction = 'uptrend'
            else:
                direction = 'downtrend'
            
            # Calculate confidence (combination of R-squared and price change magnitude)
            confidence = min(1.0, r_squared * (abs(price_change_pct) / 10))
            
            return {
                'strength': abs(slope) / prices[-1] * 100,  # Normalized strength
                'direction': direction,
                'confidence': confidence,
                'price_change_pct': price_change_pct,
                'r_squared': r_squared
            }
            
        except Exception as e:
            logger.error(f"Error detecting trend strength: {e}")
            return {'strength': 0.0, 'direction': 'sideways', 'confidence': 0.0}
    
    def _get_base_timing_from_volatility(self, volatility_regime: str) -> int:
        """Get base exit timing based on volatility regime"""
        timing_rules = self.exit_timing_rules.get(volatility_regime, 
                                                 self.exit_timing_rules['normal'])
        
        # Return average of min and max
        return (timing_rules['min_minutes'] + timing_rules['max_minutes']) // 2
    
    def _adjust_timing_for_trend(self, base_timing: int, trend_data: Dict, 
                               volatility_regime: str) -> int:
        """Adjust timing based on trend strength and direction"""
        try:
            trend_strength = trend_data.get('strength', 0.0)
            trend_confidence = trend_data.get('confidence', 0.0)
            trend_direction = trend_data.get('direction', 'sideways')
            
            # Base adjustment factor
            adjustment_factor = 1.0
            
            # Strong trending markets can hold positions longer
            if trend_direction in ['uptrend', 'downtrend'] and trend_confidence > 0.7:
                if trend_strength > 5:  # Strong trend (>5% slope)
                    adjustment_factor = 1.5  # Hold 50% longer
                elif trend_strength > 3:  # Medium trend
                    adjustment_factor = 1.25  # Hold 25% longer
            
            # High volatility + strong trend = shorter holds for risk management
            if volatility_regime in ['high', 'extreme'] and trend_strength > 5:
                adjustment_factor = min(adjustment_factor, 1.2)  # Cap extension
            
            # Sideways markets = shorter holds
            if trend_direction == 'sideways':
                adjustment_factor = 0.8  # Reduce timing by 20%
            
            adjusted_timing = int(base_timing * adjustment_factor)
            
            # Apply bounds from volatility regime
            timing_rules = self.exit_timing_rules[volatility_regime]
            adjusted_timing = max(timing_rules['min_minutes'], 
                                min(timing_rules['max_minutes'], adjusted_timing))
            
            return adjusted_timing
            
        except Exception as e:
            logger.error(f"Error adjusting timing for trend: {e}")
            return base_timing
    
    def _calculate_exit_conditions(self, entry_price: float, atr: float, 
                                 atr_percentage: float, side: str, 
                                 trend_data: Dict) -> Dict:
        """Calculate specific exit conditions based on market analysis"""
        try:
            # Dynamic stop loss based on ATR
            atr_multiplier = 2.0  # Standard ATR stop distance
            
            if side == 'BUY':
                dynamic_stop = entry_price - (atr * atr_multiplier)
                dynamic_target = entry_price + (atr * atr_multiplier * 1.5)  # 1.5:1 reward/risk
            else:  # SELL
                dynamic_stop = entry_price + (atr * atr_multiplier)
                dynamic_target = entry_price - (atr * atr_multiplier * 1.5)
            
            # Adjust based on trend
            trend_direction = trend_data.get('direction', 'sideways')
            trend_strength = trend_data.get('strength', 0.0)
            
            if trend_direction == 'uptrend' and side == 'BUY':
                # More aggressive target in trending direction
                dynamic_target = entry_price + (atr * atr_multiplier * 2.0)
            elif trend_direction == 'downtrend' and side == 'SELL':
                # More aggressive target in trending direction
                dynamic_target = entry_price - (atr * atr_multiplier * 2.0)
            
            # Calculate profit/loss percentages
            if side == 'BUY':
                stop_loss_pct = ((entry_price - dynamic_stop) / entry_price) * 100
                take_profit_pct = ((dynamic_target - entry_price) / entry_price) * 100
            else:
                stop_loss_pct = ((dynamic_stop - entry_price) / entry_price) * 100
                take_profit_pct = ((entry_price - dynamic_target) / entry_price) * 100
            
            return {
                'dynamic_stop_loss': dynamic_stop,
                'dynamic_take_profit': dynamic_target,
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': take_profit_pct,
                'atr_multiplier': atr_multiplier,
                'risk_reward_ratio': take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 1.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating exit conditions: {e}")
            return {
                'dynamic_stop_loss': entry_price * 0.98,  # 2% stop loss fallback
                'dynamic_take_profit': entry_price * 1.03,  # 3% take profit fallback
                'stop_loss_pct': 2.0,
                'take_profit_pct': 3.0,
                'atr_multiplier': 2.0,
                'risk_reward_ratio': 1.5
            }
    
    def _generate_exit_recommendation(self, adjusted_timing: int, position_age: float,
                                    exit_conditions: Dict, trend_data: Dict) -> Dict:
        """Generate specific exit recommendation"""
        try:
            # Check if minimum time has passed
            min_hold_time = 30  # Minimum 30 minutes
            
            if position_age < min_hold_time:
                return {
                    'action': 'hold',
                    'reason': f'Position too young ({position_age:.1f}min < {min_hold_time}min)',
                    'recommended_exit_time': min_hold_time - position_age,
                    'urgency': 'low'
                }
            
            # Check if target timing reached
            if position_age >= adjusted_timing:
                urgency = 'high' if position_age > adjusted_timing * 1.5 else 'medium'
                return {
                    'action': 'exit_now',
                    'reason': f'Target exit time reached ({position_age:.1f}min >= {adjusted_timing}min)',
                    'recommended_exit_time': 0,
                    'urgency': urgency
                }
            
            # Check trend continuation
            trend_direction = trend_data.get('direction', 'sideways')
            trend_confidence = trend_data.get('confidence', 0.0)
            
            # If strong trend continues, consider holding longer
            if trend_confidence > 0.8 and trend_direction in ['uptrend', 'downtrend']:
                remaining_time = adjusted_timing - position_age
                return {
                    'action': 'hold_trending',
                    'reason': f'Strong {trend_direction} continues (conf={trend_confidence:.2f})',
                    'recommended_exit_time': remaining_time,
                    'urgency': 'low'
                }
            
            # Normal holding period
            remaining_time = adjusted_timing - position_age
            return {
                'action': 'hold',
                'reason': f'Normal holding period ({position_age:.1f}/{adjusted_timing}min)',
                'recommended_exit_time': remaining_time,
                'urgency': 'low'
            }
            
        except Exception as e:
            logger.error(f"Error generating exit recommendation: {e}")
            return {
                'action': 'hold',
                'reason': f'Error in recommendation: {e}',
                'recommended_exit_time': 60,  # Default 1 hour
                'urgency': 'low'
            }
    
    def _get_default_exit_timing(self) -> Dict:
        """Get default exit timing when dynamic calculation fails"""
        return {
            'symbol': 'UNKNOWN',
            'volatility_regime': 'normal',
            'atr_percentage': 3.0,
            'trend_data': {'strength': 0.0, 'direction': 'sideways', 'confidence': 0.0},
            'base_timing_minutes': 120,  # 2 hours default
            'adjusted_timing_minutes': 120,
            'exit_conditions': {
                'dynamic_stop_loss': 0.0,
                'dynamic_take_profit': 0.0,
                'stop_loss_pct': 2.0,
                'take_profit_pct': 3.0,
                'risk_reward_ratio': 1.5
            },
            'exit_recommendation': {
                'action': 'hold',
                'reason': 'Using default timing due to calculation error',
                'recommended_exit_time': 120,
                'urgency': 'low'
            },
            'position_age_minutes': 0,
            'calculated_at': datetime.now()
        }
    
    def should_exit_position(self, position_key: str) -> Dict:
        """Check if a position should be exited based on dynamic conditions"""
        try:
            if position_key not in self.position_timings:
                return {'should_exit': False, 'reason': 'No timing data available'}
            
            timing_data = self.position_timings[position_key]
            recommendation = timing_data['exit_recommendation']
            
            should_exit = recommendation['action'] in ['exit_now', 'exit_target']
            urgency = recommendation.get('urgency', 'low')
            
            return {
                'should_exit': should_exit,
                'reason': recommendation['reason'],
                'urgency': urgency,
                'timing_data': timing_data
            }
            
        except Exception as e:
            logger.error(f"Error checking exit condition: {e}")
            return {'should_exit': False, 'reason': f'Error: {e}'}
    
    def cleanup_old_timings(self, hours_old: int = 24):
        """Clean up old position timing data"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            
            keys_to_remove = []
            for key, data in self.position_timings.items():
                if data['calculated_at'] < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.position_timings[key]
            
            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} old position timings")
                
        except Exception as e:
            logger.error(f"Error cleaning up old timings: {e}")

# Global instance
dynamic_exit_manager = DynamicExitManager()