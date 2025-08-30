"""
Market Regime Detection System
Identifies bull/bear markets and volatility regimes for adaptive trading
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .config.settings import config

logger = logging.getLogger(__name__)

class MarketRegimeDetector:
    """Detects and classifies market regimes for adaptive strategy adjustment"""
    
    def __init__(self):
        self.regime_lookback_days = 30
        self.volatility_lookback_days = 14
        self.trend_lookback_days = 20
        
        # Regime classification thresholds
        self.bull_threshold = 0.05      # 5% upward movement
        self.bear_threshold = -0.05     # 5% downward movement
        self.volatility_bands = {
            'very_low': 0.015,    # <1.5% daily volatility
            'low': 0.025,         # 1.5-2.5%
            'normal': 0.035,      # 2.5-3.5%
            'high': 0.055,        # 3.5-5.5%
            'extreme': 0.100      # >5.5%
        }
        
        # Historical regime data
        self.regime_history = []
        self.current_regime = None
        self.regime_confidence = 0.0
        
    async def detect_market_regime(self, symbols: List[str], exchange = None) -> Dict:
        """
        Detect current market regime across multiple symbols
        
        Args:
            symbols: List of symbols to analyze
            exchange: Exchange interface for data
            
        Returns:
            Comprehensive market regime analysis
        """
        try:
            if not exchange:
                logger.error("Exchange interface required for regime detection")
                return self._get_default_regime()
            
            # Analyze each symbol
            symbol_regimes = {}
            for symbol in symbols:
                regime_data = await self._analyze_symbol_regime(symbol, exchange)
                if regime_data:
                    symbol_regimes[symbol] = regime_data
            
            if not symbol_regimes:
                logger.warning("No symbol regime data available")
                return self._get_default_regime()
            
            # Aggregate regime analysis
            overall_regime = self._aggregate_regime_analysis(symbol_regimes)
            
            # Detect volatility regime
            volatility_regime = await self._detect_volatility_regime(symbols, exchange)
            
            # Combine trend and volatility analysis
            combined_regime = self._combine_regime_factors(overall_regime, volatility_regime)
            
            # Calculate regime confidence
            confidence = self._calculate_regime_confidence(symbol_regimes, volatility_regime)
            
            # Generate trading recommendations
            recommendations = self._generate_regime_recommendations(combined_regime)
            
            result = {
                'timestamp': datetime.now(),
                'overall_regime': combined_regime,
                'confidence': confidence,
                'symbol_analysis': symbol_regimes,
                'volatility_regime': volatility_regime,
                'recommendations': recommendations,
                'regime_strength': self._calculate_regime_strength(overall_regime),
                'expected_duration_days': self._estimate_regime_duration(combined_regime)
            }
            
            # Update current regime
            self.current_regime = combined_regime
            self.regime_confidence = confidence
            self.regime_history.append(result)
            
            # Keep only recent history
            if len(self.regime_history) > 100:
                self.regime_history = self.regime_history[-100:]
            
            logger.info(f"Market regime detected: {combined_regime['trend_regime']} + "
                       f"{combined_regime['volatility_regime']} (confidence: {confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return self._get_default_regime()
    
    async def _analyze_symbol_regime(self, symbol: str, exchange) -> Optional[Dict]:
        """Analyze regime for individual symbol"""
        try:
            from .data_collector import data_collector
            
            # Fetch historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.regime_lookback_days + 5)
            
            candles = await data_collector.get_historical_data(
                symbol, '1d', start_time, end_time
            )
            
            if not candles or len(candles) < self.regime_lookback_days:
                logger.warning(f"Insufficient data for {symbol} regime analysis")
                return None
            
            # Extract price data
            recent_candles = candles[-self.regime_lookback_days:]
            closes = [candle['close'] for candle in recent_candles]
            highs = [candle['high'] for candle in recent_candles]
            lows = [candle['low'] for candle in recent_candles]
            
            # Calculate price movement
            start_price = closes[0]
            end_price = closes[-1]
            total_return = (end_price - start_price) / start_price
            
            # Calculate volatility
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            volatility = np.std(returns) * np.sqrt(365)  # Annualized volatility
            
            # Trend analysis
            trend_strength = self._calculate_trend_strength(closes)
            trend_consistency = self._calculate_trend_consistency(closes)
            
            # Support/Resistance levels
            support_resistance = self._identify_support_resistance(highs, lows, closes)
            
            # Momentum indicators
            momentum = self._calculate_momentum_indicators(closes)
            
            # Classify trend regime
            if total_return > self.bull_threshold and trend_consistency > 0.6:
                trend_regime = 'bull'
            elif total_return < self.bear_threshold and trend_consistency > 0.6:
                trend_regime = 'bear'
            else:
                trend_regime = 'sideways'
            
            return {
                'symbol': symbol,
                'trend_regime': trend_regime,
                'total_return': total_return,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'trend_consistency': trend_consistency,
                'support_resistance': support_resistance,
                'momentum': momentum,
                'confidence': min(1.0, trend_consistency + abs(total_return) * 10)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing regime for {symbol}: {e}")
            return None
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """Calculate trend strength using linear regression"""
        try:
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices, 1)
            
            # Normalize slope by average price
            avg_price = np.mean(prices)
            normalized_slope = abs(slope) / avg_price
            
            return min(1.0, normalized_slope * 100)  # Scale to 0-1
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.0
    
    def _calculate_trend_consistency(self, prices: List[float]) -> float:
        """Calculate how consistent the trend direction is"""
        try:
            if len(prices) < 3:
                return 0.0
            
            # Calculate daily changes
            changes = [(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            
            # Count direction consistency
            positive_changes = sum(1 for change in changes if change > 0)
            negative_changes = sum(1 for change in changes if change < 0)
            
            # Calculate consistency ratio
            total_changes = len(changes)
            max_direction = max(positive_changes, negative_changes)
            consistency = max_direction / total_changes if total_changes > 0 else 0.0
            
            return consistency
            
        except Exception as e:
            logger.error(f"Error calculating trend consistency: {e}")
            return 0.0
    
    def _identify_support_resistance(self, highs: List[float], lows: List[float], 
                                   closes: List[float]) -> Dict:
        """Identify key support and resistance levels"""
        try:
            current_price = closes[-1]
            
            # Simple support/resistance identification
            recent_highs = highs[-10:]  # Last 10 periods
            recent_lows = lows[-10:]
            
            resistance_level = max(recent_highs)
            support_level = min(recent_lows)
            
            # Distance to levels
            resistance_distance = (resistance_level - current_price) / current_price
            support_distance = (current_price - support_level) / current_price
            
            return {
                'resistance_level': resistance_level,
                'support_level': support_level,
                'resistance_distance_pct': resistance_distance * 100,
                'support_distance_pct': support_distance * 100,
                'in_range': support_level <= current_price <= resistance_level
            }
            
        except Exception as e:
            logger.error(f"Error identifying support/resistance: {e}")
            return {
                'resistance_level': 0.0,
                'support_level': 0.0,
                'resistance_distance_pct': 0.0,
                'support_distance_pct': 0.0,
                'in_range': False
            }
    
    def _calculate_momentum_indicators(self, prices: List[float]) -> Dict:
        """Calculate momentum indicators"""
        try:
            if len(prices) < 14:
                return {'rsi': 50.0, 'momentum': 0.0, 'rate_of_change': 0.0}
            
            # Simple RSI calculation
            changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [max(0, change) for change in changes]
            losses = [max(0, -change) for change in changes]
            
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            # Momentum (price change over 10 periods)
            momentum = (prices[-1] - prices[-10]) / prices[-10] * 100 if len(prices) >= 10 else 0.0
            
            # Rate of change (5 period)
            roc = (prices[-1] - prices[-5]) / prices[-5] * 100 if len(prices) >= 5 else 0.0
            
            return {
                'rsi': rsi,
                'momentum': momentum,
                'rate_of_change': roc
            }
            
        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {e}")
            return {'rsi': 50.0, 'momentum': 0.0, 'rate_of_change': 0.0}
    
    def _aggregate_regime_analysis(self, symbol_regimes: Dict) -> Dict:
        """Aggregate regime analysis across all symbols"""
        try:
            trend_votes = {'bull': 0, 'bear': 0, 'sideways': 0}
            total_confidence = 0.0
            total_volatility = 0.0
            total_symbols = len(symbol_regimes)
            
            # Aggregate votes and metrics
            for symbol_data in symbol_regimes.values():
                trend_regime = symbol_data['trend_regime']
                confidence = symbol_data['confidence']
                
                trend_votes[trend_regime] += confidence  # Weight votes by confidence
                total_confidence += confidence
                total_volatility += symbol_data['volatility']
            
            # Determine overall trend
            max_vote = max(trend_votes.values())
            overall_trend = next(trend for trend, votes in trend_votes.items() 
                               if votes == max_vote)
            
            # Calculate averages
            avg_confidence = total_confidence / total_symbols if total_symbols > 0 else 0.0
            avg_volatility = total_volatility / total_symbols if total_symbols > 0 else 0.0
            
            return {
                'trend_regime': overall_trend,
                'trend_votes': trend_votes,
                'average_confidence': avg_confidence,
                'average_volatility': avg_volatility,
                'consensus_strength': max_vote / total_confidence if total_confidence > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error aggregating regime analysis: {e}")
            return {
                'trend_regime': 'sideways',
                'trend_votes': {'bull': 0, 'bear': 0, 'sideways': 1},
                'average_confidence': 0.0,
                'average_volatility': 0.03,
                'consensus_strength': 0.0
            }
    
    async def _detect_volatility_regime(self, symbols: List[str], exchange) -> Dict:
        """Detect current volatility regime"""
        try:
            volatilities = []
            
            for symbol in symbols:
                from .data_collector import data_collector
                
                end_time = datetime.now()
                start_time = end_time - timedelta(days=self.volatility_lookback_days + 5)
                
                candles = await data_collector.get_historical_data(
                    symbol, '1d', start_time, end_time
                )
                
                if candles and len(candles) >= self.volatility_lookback_days:
                    closes = [candle['close'] for candle in candles[-self.volatility_lookback_days:]]
                    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                    volatility = np.std(returns) * np.sqrt(365)  # Annualized
                    volatilities.append(volatility)
            
            if not volatilities:
                return {'regime': 'normal', 'value': 0.03, 'percentile': 50}
            
            avg_volatility = np.mean(volatilities)
            
            # Classify volatility regime
            if avg_volatility < self.volatility_bands['very_low']:
                vol_regime = 'very_low'
            elif avg_volatility < self.volatility_bands['low']:
                vol_regime = 'low'
            elif avg_volatility < self.volatility_bands['normal']:
                vol_regime = 'normal'
            elif avg_volatility < self.volatility_bands['high']:
                vol_regime = 'high'
            else:
                vol_regime = 'extreme'
            
            # Calculate volatility percentile (simplified)
            percentile = min(99, (avg_volatility / 0.10) * 100)  # Assume 10% is 99th percentile
            
            return {
                'regime': vol_regime,
                'value': avg_volatility,
                'percentile': percentile,
                'symbol_count': len(volatilities)
            }
            
        except Exception as e:
            logger.error(f"Error detecting volatility regime: {e}")
            return {'regime': 'normal', 'value': 0.03, 'percentile': 50}
    
    def _combine_regime_factors(self, trend_regime: Dict, volatility_regime: Dict) -> Dict:
        """Combine trend and volatility analysis into unified regime"""
        return {
            'trend_regime': trend_regime['trend_regime'],
            'volatility_regime': volatility_regime['regime'],
            'combined_regime': f"{trend_regime['trend_regime']}_{volatility_regime['regime']}",
            'trend_strength': trend_regime['consensus_strength'],
            'volatility_value': volatility_regime['value'],
            'regime_quality': 'high' if (trend_regime['consensus_strength'] > 0.7 and 
                                       trend_regime['average_confidence'] > 0.6) else 'medium'
        }
    
    def _calculate_regime_confidence(self, symbol_regimes: Dict, volatility_regime: Dict) -> float:
        """Calculate overall confidence in regime detection"""
        try:
            # Average symbol confidence
            symbol_confidences = [data['confidence'] for data in symbol_regimes.values()]
            avg_symbol_confidence = np.mean(symbol_confidences) if symbol_confidences else 0.0
            
            # Volatility consistency (higher volatility percentiles = more confident)
            vol_confidence = min(1.0, volatility_regime['percentile'] / 80)  # 80th percentile = full confidence
            
            # Combine factors
            overall_confidence = 0.7 * avg_symbol_confidence + 0.3 * vol_confidence
            
            return min(1.0, max(0.0, overall_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating regime confidence: {e}")
            return 0.5
    
    def _generate_regime_recommendations(self, regime: Dict) -> Dict:
        """Generate trading recommendations based on detected regime"""
        try:
            trend = regime['trend_regime']
            volatility = regime['volatility_regime']
            combined = regime['combined_regime']
            
            recommendations = {
                'leverage_adjustment': 1.0,
                'position_size_adjustment': 1.0,
                'preferred_timeframes': ['4h'],
                'risk_adjustment': 1.0,
                'strategy_focus': 'balanced'
            }
            
            # Trend-based adjustments
            if trend == 'bull':
                recommendations['leverage_adjustment'] = 1.1
                recommendations['position_size_adjustment'] = 1.1
                recommendations['strategy_focus'] = 'long_bias'
            elif trend == 'bear':
                recommendations['leverage_adjustment'] = 1.1
                recommendations['position_size_adjustment'] = 1.1
                recommendations['strategy_focus'] = 'short_bias'
            else:  # sideways
                recommendations['leverage_adjustment'] = 0.9
                recommendations['position_size_adjustment'] = 0.9
                recommendations['strategy_focus'] = 'range_bound'
            
            # Volatility-based adjustments
            if volatility in ['high', 'extreme']:
                recommendations['leverage_adjustment'] *= 0.8
                recommendations['risk_adjustment'] = 0.8
                recommendations['preferred_timeframes'] = ['1h', '2h']
            elif volatility == 'very_low':
                recommendations['leverage_adjustment'] *= 1.2
                recommendations['preferred_timeframes'] = ['4h', '1d']
            
            # Combined regime adjustments
            if combined in ['bull_low', 'bear_low']:
                recommendations['leverage_adjustment'] *= 1.15  # Low vol trending = opportunity
            elif combined in ['sideways_high', 'sideways_extreme']:
                recommendations['leverage_adjustment'] *= 0.7   # High vol sideways = dangerous
            
            # Ensure reasonable bounds
            recommendations['leverage_adjustment'] = max(0.5, min(1.5, recommendations['leverage_adjustment']))
            recommendations['position_size_adjustment'] = max(0.5, min(1.5, recommendations['position_size_adjustment']))
            recommendations['risk_adjustment'] = max(0.5, min(1.5, recommendations['risk_adjustment']))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating regime recommendations: {e}")
            return {
                'leverage_adjustment': 1.0,
                'position_size_adjustment': 1.0,
                'preferred_timeframes': ['4h'],
                'risk_adjustment': 1.0,
                'strategy_focus': 'balanced'
            }
    
    def _calculate_regime_strength(self, regime: Dict) -> float:
        """Calculate strength of the current regime"""
        try:
            trend_strength = regime.get('trend_strength', 0.0)
            volatility_percentile = regime.get('volatility_value', 0.03) * 100  # Convert to percentage
            
            # Combine trend strength with volatility clarity
            regime_strength = 0.6 * trend_strength + 0.4 * min(1.0, volatility_percentile / 5)
            
            return min(1.0, max(0.0, regime_strength))
            
        except Exception as e:
            logger.error(f"Error calculating regime strength: {e}")
            return 0.5
    
    def _estimate_regime_duration(self, regime: Dict) -> int:
        """Estimate how long current regime might last (in days)"""
        try:
            # Simple heuristic based on regime type and strength
            base_duration = {
                'bull': 45,      # Bull markets tend to last longer
                'bear': 30,      # Bear markets are often shorter but intense
                'sideways': 20   # Sideways markets are transitional
            }
            
            trend = regime.get('trend_regime', 'sideways')
            strength = regime.get('trend_strength', 0.5)
            volatility = regime.get('volatility_regime', 'normal')
            
            base_days = base_duration.get(trend, 20)
            
            # Adjust for strength
            strength_multiplier = 0.5 + strength  # 0.5 to 1.5 multiplier
            
            # Adjust for volatility
            vol_multiplier = {'very_low': 1.3, 'low': 1.1, 'normal': 1.0, 
                             'high': 0.8, 'extreme': 0.6}
            
            estimated_days = int(base_days * strength_multiplier * vol_multiplier.get(volatility, 1.0))
            
            return max(5, min(90, estimated_days))  # Bound between 5-90 days
            
        except Exception as e:
            logger.error(f"Error estimating regime duration: {e}")
            return 21  # Default 3 weeks
    
    def _get_default_regime(self) -> Dict:
        """Get default regime when detection fails"""
        return {
            'timestamp': datetime.now(),
            'overall_regime': {
                'trend_regime': 'sideways',
                'volatility_regime': 'normal',
                'combined_regime': 'sideways_normal',
                'trend_strength': 0.3,
                'volatility_value': 0.03,
                'regime_quality': 'medium'
            },
            'confidence': 0.5,
            'symbol_analysis': {},
            'volatility_regime': {'regime': 'normal', 'value': 0.03, 'percentile': 50},
            'recommendations': {
                'leverage_adjustment': 1.0,
                'position_size_adjustment': 1.0,
                'preferred_timeframes': ['4h'],
                'risk_adjustment': 1.0,
                'strategy_focus': 'balanced'
            },
            'regime_strength': 0.3,
            'expected_duration_days': 21
        }
    
    def get_current_regime(self) -> Optional[Dict]:
        """Get the current market regime"""
        return self.current_regime
    
    def get_regime_history(self, limit: int = 10) -> List[Dict]:
        """Get recent regime history"""
        return self.regime_history[-limit:] if self.regime_history else []
    
    def get_expected_correlation(self, pair: Tuple[str, str]) -> Dict:
        """Get expected correlation parameters for a pair (public method)"""
        return self._get_expected_correlation(pair)

# Global instance
market_regime_detector = MarketRegimeDetector()