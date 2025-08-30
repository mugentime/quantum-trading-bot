"""
Advanced Volatility Analysis and Leverage Scaling
Provides real-time volatility assessment and dynamic leverage adjustments
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
from .config.settings import config

logger = logging.getLogger(__name__)

class VolatilityManager:
    """Manages volatility analysis and leverage scaling based on market conditions"""
    
    def __init__(self):
        self.volatility_cache = {}
        self.atr_cache = {}
        self.volatility_regimes = {
            'very_low': (0, 0.01),      # < 1% daily vol
            'low': (0.01, 0.025),       # 1-2.5% daily vol
            'normal': (0.025, 0.05),    # 2.5-5% daily vol  
            'high': (0.05, 0.08),       # 5-8% daily vol
            'extreme': (0.08, float('inf'))  # > 8% daily vol
        }
        
        self.leverage_multipliers = {
            'very_low': 1.3,    # Increase leverage in stable conditions
            'low': 1.2,         # Slightly increase leverage
            'normal': 1.0,      # Standard leverage
            'high': 0.8,        # Reduce leverage in volatile conditions
            'extreme': 0.6      # Significantly reduce leverage
        }
    
    async def calculate_volatility_adjusted_leverage(self, base_leverage: int, 
                                                   symbol: str, exchange) -> int:
        """
        Calculate leverage adjusted for current market volatility
        
        Args:
            base_leverage: Base leverage from signal strength
            symbol: Trading symbol
            exchange: Exchange connection
            
        Returns:
            Volatility-adjusted leverage
        """
        try:
            # Get current volatility metrics
            current_vol = await self.get_current_volatility(symbol, exchange)
            historical_vol = await self.get_historical_volatility(symbol, exchange)
            
            # Determine volatility regime
            regime = self._classify_volatility_regime(current_vol)
            
            # Get leverage multiplier for current regime
            multiplier = self.leverage_multipliers.get(regime, 1.0)
            
            # Apply relative volatility adjustment
            if historical_vol > 0:
                relative_vol = current_vol / historical_vol
                # Additional adjustment based on relative volatility
                if relative_vol > 1.5:      # Much higher than normal
                    multiplier *= 0.9
                elif relative_vol < 0.7:    # Much lower than normal
                    multiplier *= 1.1
            
            # Calculate adjusted leverage
            adjusted_leverage = int(base_leverage * multiplier)
            
            # Ensure within bounds
            adjusted_leverage = max(config.MIN_LEVERAGE, 
                                  min(config.MAX_LEVERAGE, adjusted_leverage))
            
            logger.info(f"Volatility adjustment for {symbol}: "
                       f"regime={regime}, current_vol={current_vol:.3f}, "
                       f"multiplier={multiplier:.2f}, "
                       f"base={base_leverage} -> adjusted={adjusted_leverage}")
            
            # Cache the result
            self.volatility_cache[symbol] = {
                'regime': regime,
                'current_vol': current_vol,
                'historical_vol': historical_vol,
                'multiplier': multiplier,
                'timestamp': datetime.now()
            }
            
            return adjusted_leverage
            
        except Exception as e:
            logger.error(f"Error calculating volatility-adjusted leverage: {e}")
            return base_leverage
    
    async def get_current_volatility(self, symbol: str, exchange) -> float:
        """Calculate current volatility using recent price data"""
        try:
            # Fetch recent hourly candles (last 24 hours)
            ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=24)
            
            if len(ohlcv) < 10:
                logger.warning(f"Insufficient data for volatility calculation: {len(ohlcv)} candles")
                return 0.03  # Default 3% volatility
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate hourly returns
            df['returns'] = df['close'].pct_change()
            
            # Calculate volatility (standard deviation of returns)
            hourly_vol = df['returns'].std()
            
            # Annualize to daily volatility (assuming 24 hours in a day for crypto)
            daily_vol = hourly_vol * np.sqrt(24)
            
            return float(daily_vol) if not np.isnan(daily_vol) else 0.03
            
        except Exception as e:
            logger.error(f"Error calculating current volatility for {symbol}: {e}")
            return 0.03  # Default volatility
    
    async def get_historical_volatility(self, symbol: str, exchange) -> float:
        """Calculate historical average volatility (30-day lookback)"""
        try:
            # Check cache first (refresh every 6 hours)
            cache_key = f"{symbol}_historical_vol"
            if cache_key in self.volatility_cache:
                cached_data = self.volatility_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < timedelta(hours=6):
                    return cached_data['value']
            
            # Fetch daily candles for the last 30 days
            ohlcv = await exchange.fetch_ohlcv(symbol, '1d', limit=30)
            
            if len(ohlcv) < 15:
                logger.warning(f"Insufficient historical data for {symbol}: {len(ohlcv)} days")
                return 0.035  # Default historical volatility
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate daily returns
            df['returns'] = df['close'].pct_change()
            
            # Calculate average historical volatility
            historical_vol = df['returns'].std()
            
            # Cache the result
            self.volatility_cache[cache_key] = {
                'value': float(historical_vol) if not np.isnan(historical_vol) else 0.035,
                'timestamp': datetime.now()
            }
            
            return self.volatility_cache[cache_key]['value']
            
        except Exception as e:
            logger.error(f"Error calculating historical volatility for {symbol}: {e}")
            return 0.035  # Default historical volatility
    
    def _classify_volatility_regime(self, volatility: float) -> str:
        """Classify current volatility into regime categories"""
        for regime, (low, high) in self.volatility_regimes.items():
            if low <= volatility < high:
                return regime
        return 'extreme'  # Fallback for very high volatility
    
    async def get_atr(self, symbol: str, exchange, period: int = 14) -> float:
        """Calculate Average True Range for additional volatility context"""
        try:
            # Check cache first
            cache_key = f"{symbol}_atr_{period}"
            if cache_key in self.atr_cache:
                cached_data = self.atr_cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < timedelta(minutes=30):
                    return cached_data['value']
            
            # Fetch enough data for ATR calculation
            ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=period + 10)
            
            if len(ohlcv) < period:
                logger.warning(f"Insufficient data for ATR calculation: {len(ohlcv)} candles")
                return 0.02  # Default ATR
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate True Range
            df['prev_close'] = df['close'].shift(1)
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = np.abs(df['high'] - df['prev_close'])
            df['tr3'] = np.abs(df['low'] - df['prev_close'])
            df['true_range'] = np.maximum(df['tr1'], np.maximum(df['tr2'], df['tr3']))
            
            # Calculate ATR (Simple Moving Average of True Range)
            atr = df['true_range'].rolling(window=period).mean().iloc[-1]
            
            # Normalize by current price
            current_price = df['close'].iloc[-1]
            atr_normalized = atr / current_price if current_price > 0 else 0.02
            
            # Cache the result
            self.atr_cache[cache_key] = {
                'value': float(atr_normalized) if not np.isnan(atr_normalized) else 0.02,
                'timestamp': datetime.now()
            }
            
            return self.atr_cache[cache_key]['value']
            
        except Exception as e:
            logger.error(f"Error calculating ATR for {symbol}: {e}")
            return 0.02  # Default ATR
    
    async def get_market_volatility_summary(self, symbols: List[str], exchange) -> Dict:
        """Get comprehensive volatility summary for multiple symbols"""
        try:
            summary = {
                'overall_regime': 'normal',
                'symbols': {},
                'market_stress_level': 0.0,
                'recommended_leverage_adjustment': 1.0
            }
            
            volatilities = []
            regimes = []
            
            for symbol in symbols:
                try:
                    current_vol = await self.get_current_volatility(symbol, exchange)
                    regime = self._classify_volatility_regime(current_vol)
                    
                    summary['symbols'][symbol] = {
                        'volatility': current_vol,
                        'regime': regime,
                        'leverage_multiplier': self.leverage_multipliers.get(regime, 1.0)
                    }
                    
                    volatilities.append(current_vol)
                    regimes.append(regime)
                    
                except Exception as e:
                    logger.error(f"Error processing volatility for {symbol}: {e}")
                    continue
            
            if volatilities:
                # Calculate overall market metrics
                avg_volatility = np.mean(volatilities)
                summary['overall_regime'] = self._classify_volatility_regime(avg_volatility)
                summary['market_stress_level'] = min(1.0, avg_volatility / 0.05)  # Normalize to 0-1
                summary['recommended_leverage_adjustment'] = self.leverage_multipliers.get(
                    summary['overall_regime'], 1.0
                )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating volatility summary: {e}")
            return {'overall_regime': 'normal', 'symbols': {}, 'market_stress_level': 0.5, 
                   'recommended_leverage_adjustment': 1.0}
    
    def get_volatility_metrics(self, symbol: str) -> Dict:
        """Get cached volatility metrics for a symbol"""
        try:
            if symbol in self.volatility_cache:
                return self.volatility_cache[symbol]
            else:
                return {
                    'regime': 'normal',
                    'current_vol': 0.03,
                    'historical_vol': 0.035,
                    'multiplier': 1.0,
                    'timestamp': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error getting volatility metrics: {e}")
            return {}
    
    def is_high_volatility_period(self, symbol: str = None) -> bool:
        """Check if currently in a high volatility period"""
        try:
            if symbol and symbol in self.volatility_cache:
                regime = self.volatility_cache[symbol].get('regime', 'normal')
                return regime in ['high', 'extreme']
            
            # Check overall market if no specific symbol
            high_vol_count = sum(
                1 for data in self.volatility_cache.values()
                if isinstance(data, dict) and data.get('regime') in ['high', 'extreme']
            )
            
            total_symbols = len([
                data for data in self.volatility_cache.values()
                if isinstance(data, dict) and 'regime' in data
            ])
            
            if total_symbols == 0:
                return False
            
            return (high_vol_count / total_symbols) > 0.5
            
        except Exception as e:
            logger.error(f"Error checking volatility period: {e}")
            return False
    
    def clear_cache(self):
        """Clear volatility cache (useful for testing or reset)"""
        self.volatility_cache.clear()
        self.atr_cache.clear()
        logger.info("Volatility cache cleared")

# Global instance
volatility_manager = VolatilityManager()