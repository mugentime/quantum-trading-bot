"""
Advanced Volatility Manager for Dynamic Leverage Adjustment
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VolatilityManager:
    """Manages volatility-based leverage adjustments"""
    
    def __init__(self):
        self.volatility_cache = {}
        self.cache_expiry = 300  # 5 minutes
        
    async def calculate_volatility_adjusted_leverage(self, base_leverage: int, 
                                                   symbol: str, exchange: Any) -> int:
        """Calculate leverage adjusted for volatility"""
        try:
            # Get volatility metrics
            volatility_metrics = await self._get_volatility_metrics(symbol, exchange)
            adjustment_factor = self._calculate_adjustment_factor(volatility_metrics)
            adjusted_leverage = int(base_leverage * adjustment_factor)
            
            # Ensure bounds
            min_leverage = max(5, int(base_leverage * 0.5))
            max_leverage = min(50, int(base_leverage * 1.3))
            final_leverage = max(min_leverage, min(max_leverage, adjusted_leverage))
            
            return final_leverage
            
        except Exception as e:
            logger.error(f"Error in volatility adjustment: {e}")
            return int(base_leverage * 0.9)
    
    async def _get_volatility_metrics(self, symbol: str, exchange: Any) -> Dict:
        """Get volatility metrics for symbol"""
        try:
            # Check cache
            cache_key = f"{symbol}_volatility"
            if cache_key in self.volatility_cache:
                cached_data, timestamp = self.volatility_cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_expiry):
                    return cached_data
            
            # Fetch data
            ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=24)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['returns'] = df['close'].pct_change()
            
            # Calculate metrics
            realized_vol = df['returns'].std() * np.sqrt(24 * 365)
            df['range'] = (df['high'] - df['low']) / df['close']
            intraday_range = df['range'].mean()
            
            metrics = {
                'realized_volatility_24h': realized_vol,
                'intraday_range': intraday_range,
                'volatility_regime': self._detect_regime(df['returns']),
                'correlation_breakdown': False  # Simplified
            }
            
            # Cache results
            self.volatility_cache[cache_key] = (metrics, datetime.now())
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting volatility metrics: {e}")
            return self._get_fallback_metrics()
    
    def _detect_regime(self, returns: pd.Series) -> str:
        """Detect volatility regime"""
        try:
            if len(returns) < 20:
                return 'normal'
            
            current_vol = returns.tail(10).std()
            historical_vol = returns.std()
            vol_ratio = current_vol / historical_vol
            
            if vol_ratio > 1.5:
                return 'high_vol'
            elif vol_ratio < 0.7:
                return 'low_vol'
            else:
                return 'normal'
        except Exception:
            return 'normal'
    
    def _calculate_adjustment_factor(self, metrics: Dict) -> float:
        """Calculate volatility adjustment factor"""
        try:
            factors = []
            
            # Volatility factor
            vol_24h = metrics['realized_volatility_24h']
            if vol_24h > 2.0:
                vol_factor = 0.6
            elif vol_24h > 1.0:
                vol_factor = 0.8
            elif vol_24h < 0.3:
                vol_factor = 1.2
            else:
                vol_factor = 1.0
            factors.append(vol_factor)
            
            # Regime factor
            regime = metrics['volatility_regime']
            if regime == 'high_vol':
                regime_factor = 0.7
            elif regime == 'low_vol':
                regime_factor = 1.15
            else:
                regime_factor = 1.0
            factors.append(regime_factor)
            
            # Average factors
            final_factor = np.mean(factors)
            return max(0.5, min(1.3, final_factor))
            
        except Exception:
            return 0.9
    
    def _get_fallback_metrics(self) -> Dict:
        """Fallback volatility metrics"""
        return {
            'realized_volatility_24h': 0.8,
            'intraday_range': 0.05,
            'volatility_regime': 'normal',
            'correlation_breakdown': False
        }

# Global instance
volatility_manager = VolatilityManager()