"""
Multi-Timeframe Analysis System
Provides correlation analysis across multiple timeframes for enhanced signal quality
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .config.settings import config

logger = logging.getLogger(__name__)

class MultiTimeframeAnalyzer:
    """Analyzes correlations across multiple timeframes for signal confluence"""
    
    def __init__(self):
        self.timeframes = {
            '1h': {'minutes': 60, 'periods': 50, 'weight': 0.2},
            '4h': {'minutes': 240, 'periods': 30, 'weight': 0.3},
            '1d': {'minutes': 1440, 'periods': 20, 'weight': 0.5}
        }
        self.correlation_cache = {}
        self.signal_history = []
        
    async def analyze_multi_timeframe_correlation(self, symbol: str, vs_symbol: str = 'BTCUSDT', 
                                                exchange = None) -> Dict:
        """
        Analyze correlation across multiple timeframes
        
        Args:
            symbol: Target symbol (e.g., 'ETHUSDT', 'SOLUSDT')
            vs_symbol: Reference symbol for correlation
            exchange: Exchange interface for data fetching
            
        Returns:
            Multi-timeframe correlation analysis results
        """
        try:
            if not exchange:
                logger.error("Exchange interface required for multi-timeframe analysis")
                return {}
            
            tf_correlations = {}
            tf_deviations = {}
            tf_strengths = {}
            
            # Analyze each timeframe
            for tf_name, tf_config in self.timeframes.items():
                try:
                    # Fetch data for this timeframe
                    correlation_data = await self._get_timeframe_correlation(
                        symbol, vs_symbol, tf_name, tf_config, exchange
                    )
                    
                    if correlation_data:
                        tf_correlations[tf_name] = correlation_data['correlation']
                        tf_deviations[tf_name] = correlation_data['deviation']
                        tf_strengths[tf_name] = correlation_data['strength']
                        
                except Exception as e:
                    logger.warning(f"Error analyzing {tf_name} timeframe: {e}")
                    continue
            
            if not tf_correlations:
                logger.warning("No timeframe correlations calculated")
                return {}
            
            # Calculate weighted signals
            weighted_analysis = self._calculate_weighted_signals(
                tf_correlations, tf_deviations, tf_strengths
            )
            
            # Determine signal confluence
            confluence_score = self._calculate_confluence_score(tf_correlations)
            
            # Generate enhanced signal
            enhanced_signal = self._generate_enhanced_signal(
                weighted_analysis, confluence_score, tf_correlations
            )
            
            result = {
                'symbol': symbol,
                'vs_symbol': vs_symbol,
                'timestamp': datetime.now(),
                'timeframe_data': {
                    'correlations': tf_correlations,
                    'deviations': tf_deviations,
                    'strengths': tf_strengths
                },
                'weighted_correlation': weighted_analysis['weighted_correlation'],
                'weighted_deviation': weighted_analysis['weighted_deviation'],
                'confluence_score': confluence_score,
                'enhanced_signal': enhanced_signal,
                'signal_strength': self._calculate_signal_strength(
                    weighted_analysis, confluence_score
                )
            }
            
            # Cache result
            cache_key = f"{symbol}_{vs_symbol}_{datetime.now().strftime('%Y%m%d_%H')}"
            self.correlation_cache[cache_key] = result
            
            logger.info(f"Multi-timeframe analysis complete for {symbol}: "
                       f"confluence={confluence_score:.3f}, "
                       f"strength={result['signal_strength']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe correlation analysis: {e}")
            return {}
    
    async def _get_timeframe_correlation(self, symbol: str, vs_symbol: str, 
                                       tf_name: str, tf_config: Dict, 
                                       exchange) -> Optional[Dict]:
        """Get correlation data for specific timeframe"""
        try:
            # Calculate timeframe parameters
            periods = tf_config['periods']
            minutes_per_candle = tf_config['minutes']
            
            # Fetch historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes_per_candle * periods)
            
            # Get price data (simplified - in real implementation would use exchange)
            symbol_prices = await self._fetch_timeframe_data(
                symbol, tf_name, start_time, end_time, exchange
            )
            vs_prices = await self._fetch_timeframe_data(
                vs_symbol, tf_name, start_time, end_time, exchange
            )
            
            if len(symbol_prices) < periods or len(vs_prices) < periods:
                logger.warning(f"Insufficient data for {tf_name} analysis")
                return None
            
            # Calculate correlation
            correlation = np.corrcoef(symbol_prices[-periods:], vs_prices[-periods:])[0, 1]
            
            # Calculate deviation from expected correlation
            expected_correlation = self._get_expected_correlation(symbol, vs_symbol)
            deviation = abs(correlation - expected_correlation)
            
            # Calculate signal strength
            strength = min(1.0, deviation / 0.3)  # Normalize deviation to strength
            
            return {
                'correlation': correlation,
                'deviation': deviation,
                'strength': strength,
                'periods_analyzed': periods,
                'timeframe': tf_name
            }
            
        except Exception as e:
            logger.error(f"Error getting {tf_name} correlation: {e}")
            return None
    
    async def _fetch_timeframe_data(self, symbol: str, timeframe: str, 
                                  start_time: datetime, end_time: datetime,
                                  exchange) -> List[float]:
        """Fetch price data for specific timeframe"""
        try:
            # This would integrate with your existing data collection
            # For now, return mock data structure
            from .data_collector import data_collector
            
            # Get cached data or fetch new
            data = await data_collector.get_historical_data(
                symbol, timeframe, start_time, end_time
            )
            
            if data and len(data) > 0:
                return [float(candle['close']) for candle in data]
            else:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching {timeframe} data for {symbol}: {e}")
            return []
    
    def _calculate_weighted_signals(self, correlations: Dict, deviations: Dict, 
                                  strengths: Dict) -> Dict:
        """Calculate weighted correlation and deviation signals"""
        try:
            weighted_correlation = 0.0
            weighted_deviation = 0.0
            total_weight = 0.0
            
            for tf_name in correlations:
                if tf_name in self.timeframes:
                    weight = self.timeframes[tf_name]['weight']
                    strength = strengths.get(tf_name, 0.5)
                    
                    # Weight by both timeframe importance and signal strength
                    effective_weight = weight * (0.5 + 0.5 * strength)
                    
                    weighted_correlation += correlations[tf_name] * effective_weight
                    weighted_deviation += deviations[tf_name] * effective_weight
                    total_weight += effective_weight
            
            if total_weight > 0:
                weighted_correlation /= total_weight
                weighted_deviation /= total_weight
            
            return {
                'weighted_correlation': weighted_correlation,
                'weighted_deviation': weighted_deviation,
                'total_weight': total_weight
            }
            
        except Exception as e:
            logger.error(f"Error calculating weighted signals: {e}")
            return {'weighted_correlation': 0.0, 'weighted_deviation': 0.0, 'total_weight': 0.0}
    
    def _calculate_confluence_score(self, correlations: Dict) -> float:
        """Calculate how well timeframes agree on correlation direction"""
        try:
            if len(correlations) < 2:
                return 0.5  # Neutral if insufficient data
            
            correlation_values = list(correlations.values())
            
            # Check for consistent direction across timeframes
            positive_count = sum(1 for corr in correlation_values if corr > 0)
            negative_count = sum(1 for corr in correlation_values if corr < 0)
            
            # Calculate agreement ratio
            total_timeframes = len(correlation_values)
            max_agreement = max(positive_count, negative_count)
            agreement_ratio = max_agreement / total_timeframes
            
            # Calculate correlation consistency (low variance = high confluence)
            correlation_std = np.std(correlation_values)
            consistency_score = max(0.0, 1.0 - correlation_std)
            
            # Combine agreement and consistency
            confluence_score = 0.6 * agreement_ratio + 0.4 * consistency_score
            
            return min(1.0, max(0.0, confluence_score))
            
        except Exception as e:
            logger.error(f"Error calculating confluence score: {e}")
            return 0.5
    
    def _generate_enhanced_signal(self, weighted_analysis: Dict, confluence_score: float,
                                correlations: Dict) -> Dict:
        """Generate enhanced trading signal from multi-timeframe analysis"""
        try:
            weighted_correlation = weighted_analysis['weighted_correlation']
            weighted_deviation = weighted_analysis['weighted_deviation']
            
            # Determine signal direction
            signal_direction = 'long' if weighted_correlation > 0 else 'short'
            
            # Calculate signal confidence
            base_confidence = min(1.0, weighted_deviation / 0.2)
            confluence_boost = confluence_score * 0.3
            signal_confidence = min(1.0, base_confidence + confluence_boost)
            
            # Determine if signal meets minimum thresholds
            min_deviation_threshold = 0.15
            min_confluence_threshold = 0.6
            
            signal_valid = (
                weighted_deviation >= min_deviation_threshold and
                confluence_score >= min_confluence_threshold
            )
            
            return {
                'action': signal_direction,
                'confidence': signal_confidence,
                'valid': signal_valid,
                'correlation': weighted_correlation,
                'deviation': weighted_deviation,
                'confluence': confluence_score,
                'reasoning': f"Multi-timeframe analysis: {len(correlations)} timeframes, "
                           f"deviation={weighted_deviation:.3f}, confluence={confluence_score:.3f}"
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced signal: {e}")
            return {
                'action': 'hold',
                'confidence': 0.0,
                'valid': False,
                'correlation': 0.0,
                'deviation': 0.0,
                'confluence': 0.0,
                'reasoning': f"Error in signal generation: {e}"
            }
    
    def _calculate_signal_strength(self, weighted_analysis: Dict, confluence_score: float) -> float:
        """Calculate overall signal strength score"""
        try:
            deviation_strength = min(1.0, weighted_analysis['weighted_deviation'] / 0.3)
            confluence_strength = confluence_score
            
            # Weight deviation more heavily, but confluence provides boost
            signal_strength = 0.7 * deviation_strength + 0.3 * confluence_strength
            
            return min(1.0, max(0.0, signal_strength))
            
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return 0.0
    
    def _get_expected_correlation(self, symbol: str, vs_symbol: str) -> float:
        """Get expected correlation between symbol pairs"""
        # Default expected correlations for major crypto pairs
        expected_correlations = {
            ('ETHUSDT', 'BTCUSDT'): 0.75,
            ('SOLUSDT', 'BTCUSDT'): 0.65,
            ('BNBUSDT', 'BTCUSDT'): 0.70,
            ('ADAUSDT', 'BTCUSDT'): 0.60,
            ('DOTUSDT', 'BTCUSDT'): 0.65
        }
        
        pair_key = (symbol, vs_symbol)
        reverse_key = (vs_symbol, symbol)
        
        return expected_correlations.get(pair_key, 
               expected_correlations.get(reverse_key, 0.65))  # Default 0.65
    
    def get_timeframe_weights(self) -> Dict:
        """Get current timeframe weight configuration"""
        return {tf: config['weight'] for tf, config in self.timeframes.items()}
    
    def update_timeframe_weights(self, new_weights: Dict):
        """Update timeframe weights for different market conditions"""
        try:
            for tf_name, weight in new_weights.items():
                if tf_name in self.timeframes:
                    self.timeframes[tf_name]['weight'] = max(0.0, min(1.0, weight))
            
            # Normalize weights to sum to 1.0
            total_weight = sum(config['weight'] for config in self.timeframes.values())
            if total_weight > 0:
                for tf_config in self.timeframes.values():
                    tf_config['weight'] /= total_weight
                    
            logger.info(f"Updated timeframe weights: {self.get_timeframe_weights()}")
            
        except Exception as e:
            logger.error(f"Error updating timeframe weights: {e}")
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict]:
        """Get recent multi-timeframe analysis results"""
        return self.signal_history[-limit:] if self.signal_history else []
    
    def clear_cache(self):
        """Clear correlation cache (useful for memory management)"""
        self.correlation_cache.clear()
        logger.info("Multi-timeframe correlation cache cleared")

# Global instance
multi_timeframe_analyzer = MultiTimeframeAnalyzer()