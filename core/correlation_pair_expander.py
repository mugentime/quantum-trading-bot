"""
Correlation Pair Expansion System
Implements multi-asset correlation analysis and cross-pair arbitrage detection
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from itertools import combinations
from .config.settings import config

logger = logging.getLogger(__name__)

class CorrelationPairExpander:
    """Expands correlation analysis to multiple asset pairs and cross-correlations"""
    
    def __init__(self):
        # Define asset groups and their expected correlations
        self.asset_groups = {
            'major_cryptos': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            'defi_tokens': ['ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 'MATICUSDT'],
            'layer1s': ['ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 'DOTUSDT', 'ADAUSDT'],
            'top_alts': ['ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT']
        }
        
        # Expected correlation ranges for different pairs
        self.correlation_expectations = {
            ('ETHUSDT', 'BTCUSDT'): {'mean': 0.75, 'std': 0.15},
            ('SOLUSDT', 'BTCUSDT'): {'mean': 0.65, 'std': 0.20},
            ('ETHUSDT', 'SOLUSDT'): {'mean': 0.70, 'std': 0.18},
            ('BNBUSDT', 'BTCUSDT'): {'mean': 0.68, 'std': 0.18},
            ('AVAXUSDT', 'SOLUSDT'): {'mean': 0.72, 'std': 0.16},
            ('MATICUSDT', 'ETHUSDT'): {'mean': 0.64, 'std': 0.22}
        }
        
        # Correlation analysis parameters
        self.analysis_periods = [24, 48, 72]  # Hours for different timeframe analysis
        self.min_correlation_strength = 0.3
        self.correlation_breakdown_threshold = 0.25
        
        # Cross-pair arbitrage parameters
        self.arbitrage_threshold = 0.015  # 1.5% minimum arbitrage opportunity
        self.max_arbitrage_pairs = 3      # Maximum simultaneous arbitrage positions
        
        # Data storage
        self.correlation_matrix = {}
        self.arbitrage_opportunities = []
        self.cross_pair_signals = []
        
    async def analyze_multi_pair_correlations(self, symbols: List[str], 
                                            exchange = None) -> Dict:
        """
        Analyze correlations across multiple asset pairs
        
        Args:
            symbols: List of symbols to analyze
            exchange: Exchange interface for data fetching
            
        Returns:
            Comprehensive multi-pair correlation analysis
        """
        try:
            if not exchange:
                logger.error("Exchange interface required for multi-pair analysis")
                return {}
            
            if len(symbols) < 2:
                logger.warning("Need at least 2 symbols for correlation analysis")
                return {}
            
            # Calculate pairwise correlations for different timeframes
            timeframe_correlations = {}
            
            for period_hours in self.analysis_periods:
                period_correlations = await self._calculate_period_correlations(
                    symbols, period_hours, exchange
                )
                if period_correlations:
                    timeframe_correlations[f"{period_hours}h"] = period_correlations
            
            if not timeframe_correlations:
                logger.warning("No correlation data calculated")
                return {}
            
            # Identify correlation breakdowns
            breakdown_signals = self._identify_correlation_breakdowns(timeframe_correlations)
            
            # Find cross-pair arbitrage opportunities
            arbitrage_opportunities = await self._detect_cross_pair_arbitrage(
                symbols, timeframe_correlations, exchange
            )
            
            # Calculate correlation stability scores
            stability_scores = self._calculate_correlation_stability(timeframe_correlations)
            
            # Generate trading signals from correlation analysis
            correlation_signals = self._generate_correlation_signals(
                breakdown_signals, stability_scores, timeframe_correlations
            )
            
            # Identify strongest opportunities
            ranked_opportunities = self._rank_trading_opportunities(
                correlation_signals, arbitrage_opportunities
            )
            
            result = {
                'timestamp': datetime.now(),
                'symbols_analyzed': symbols,
                'timeframe_correlations': timeframe_correlations,
                'breakdown_signals': breakdown_signals,
                'arbitrage_opportunities': arbitrage_opportunities,
                'stability_scores': stability_scores,
                'correlation_signals': correlation_signals,
                'ranked_opportunities': ranked_opportunities,
                'market_structure': self._analyze_market_structure(timeframe_correlations)
            }
            
            # Update stored data
            self.correlation_matrix = timeframe_correlations
            self.arbitrage_opportunities = arbitrage_opportunities
            self.cross_pair_signals = correlation_signals
            
            logger.info(f"Multi-pair correlation analysis complete: {len(breakdown_signals)} "
                       f"breakdown signals, {len(arbitrage_opportunities)} arbitrage opportunities")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-pair correlation analysis: {e}")
            return {}
    
    async def _calculate_period_correlations(self, symbols: List[str], period_hours: int,
                                           exchange) -> Dict:
        """Calculate correlations for specific time period"""
        try:
            from .data_collector import data_collector
            
            # Fetch historical data for all symbols
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=period_hours + 24)  # Extra buffer
            
            symbol_data = {}
            for symbol in symbols:
                candles = await data_collector.get_historical_data(
                    symbol, '1h', start_time, end_time
                )
                if candles and len(candles) >= period_hours:
                    prices = [candle['close'] for candle in candles[-period_hours:]]
                    returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                              for i in range(1, len(prices))]
                    symbol_data[symbol] = {
                        'prices': prices,
                        'returns': returns,
                        'current_price': prices[-1]
                    }
            
            if len(symbol_data) < 2:
                return {}
            
            # Calculate pairwise correlations
            correlations = {}
            for symbol1, symbol2 in combinations(symbol_data.keys(), 2):
                if len(symbol_data[symbol1]['returns']) == len(symbol_data[symbol2]['returns']):
                    correlation = np.corrcoef(
                        symbol_data[symbol1]['returns'],
                        symbol_data[symbol2]['returns']
                    )[0, 1]
                    
                    # Calculate additional metrics
                    price_ratio = (symbol_data[symbol1]['current_price'] / 
                                 symbol_data[symbol2]['current_price'])
                    
                    pair_key = tuple(sorted([symbol1, symbol2]))
                    correlations[pair_key] = {
                        'correlation': correlation,
                        'price_ratio': price_ratio,
                        'symbol1_price': symbol_data[symbol1]['current_price'],
                        'symbol2_price': symbol_data[symbol2]['current_price'],
                        'data_points': len(symbol_data[symbol1]['returns'])
                    }
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error calculating period correlations: {e}")
            return {}
    
    def _identify_correlation_breakdowns(self, timeframe_correlations: Dict) -> List[Dict]:
        """Identify significant correlation breakdowns across timeframes"""
        try:
            breakdown_signals = []
            
            # Compare correlations across timeframes
            all_pairs = set()
            for tf_data in timeframe_correlations.values():
                all_pairs.update(tf_data.keys())
            
            for pair in all_pairs:
                pair_analysis = []
                expected_corr = self._get_expected_correlation(pair)
                
                for timeframe, correlations in timeframe_correlations.items():
                    if pair in correlations:
                        corr_data = correlations[pair]
                        correlation = corr_data['correlation']
                        
                        # Calculate deviation from expected
                        deviation = abs(correlation - expected_corr['mean'])
                        normalized_deviation = deviation / expected_corr['std']
                        
                        pair_analysis.append({
                            'timeframe': timeframe,
                            'correlation': correlation,
                            'deviation': deviation,
                            'normalized_deviation': normalized_deviation,
                            'price_ratio': corr_data['price_ratio']
                        })
                
                # Check for breakdown signals
                if len(pair_analysis) >= 2:
                    # Look for correlation breakdown (strong deviation)
                    max_deviation = max(analysis['normalized_deviation'] for analysis in pair_analysis)
                    
                    if max_deviation > 2.0:  # 2 standard deviations
                        # Determine signal direction
                        current_correlation = pair_analysis[-1]['correlation']  # Most recent timeframe
                        expected_correlation = expected_corr['mean']
                        
                        signal_direction = 'long' if current_correlation < expected_correlation else 'short'
                        
                        breakdown_signal = {
                            'pair': pair,
                            'signal_type': 'correlation_breakdown',
                            'direction': signal_direction,
                            'strength': min(1.0, max_deviation / 3.0),  # Cap at 1.0
                            'current_correlation': current_correlation,
                            'expected_correlation': expected_correlation,
                            'max_deviation': max_deviation,
                            'timeframe_analysis': pair_analysis,
                            'timestamp': datetime.now()
                        }
                        
                        breakdown_signals.append(breakdown_signal)
            
            # Sort by signal strength
            breakdown_signals.sort(key=lambda x: x['strength'], reverse=True)
            
            return breakdown_signals
            
        except Exception as e:
            logger.error(f"Error identifying correlation breakdowns: {e}")
            return []
    
    async def _detect_cross_pair_arbitrage(self, symbols: List[str], 
                                         timeframe_correlations: Dict,
                                         exchange) -> List[Dict]:
        """Detect cross-pair arbitrage opportunities"""
        try:
            arbitrage_ops = []
            
            # Look for triangular arbitrage opportunities
            if 'BTCUSDT' in symbols:
                base_symbol = 'BTCUSDT'
                other_symbols = [s for s in symbols if s != base_symbol]
                
                for symbol1, symbol2 in combinations(other_symbols, 2):
                    # Check if we have correlation data for these pairs
                    pair1_btc = tuple(sorted([symbol1, base_symbol]))
                    pair2_btc = tuple(sorted([symbol2, base_symbol]))
                    pair1_pair2 = tuple(sorted([symbol1, symbol2]))
                    
                    # Get recent correlations
                    recent_tf = list(timeframe_correlations.keys())[-1]  # Most recent timeframe
                    correlations = timeframe_correlations.get(recent_tf, {})
                    
                    if all(pair in correlations for pair in [pair1_btc, pair2_btc, pair1_pair2]):
                        corr1 = correlations[pair1_btc]['correlation']
                        corr2 = correlations[pair2_btc]['correlation']
                        corr12 = correlations[pair1_pair2]['correlation']
                        
                        # Calculate expected vs actual correlation
                        # If symbol1 and symbol2 both correlate with BTC, they should correlate with each other
                        expected_cross_corr = corr1 * corr2
                        actual_cross_corr = corr12
                        
                        arbitrage_score = abs(expected_cross_corr - actual_cross_corr)
                        
                        if arbitrage_score > self.arbitrage_threshold:
                            arbitrage_op = {
                                'type': 'triangular_arbitrage',
                                'symbols': [symbol1, symbol2, base_symbol],
                                'primary_pair': pair1_pair2,
                                'arbitrage_score': arbitrage_score,
                                'expected_correlation': expected_cross_corr,
                                'actual_correlation': actual_cross_corr,
                                'direction': 'convergence' if actual_cross_corr < expected_cross_corr else 'divergence',
                                'confidence': min(1.0, arbitrage_score / 0.05),
                                'timestamp': datetime.now()
                            }
                            
                            arbitrage_ops.append(arbitrage_op)
            
            # Sort by arbitrage score
            arbitrage_ops.sort(key=lambda x: x['arbitrage_score'], reverse=True)
            
            # Limit to max arbitrage pairs
            return arbitrage_ops[:self.max_arbitrage_pairs]
            
        except Exception as e:
            logger.error(f"Error detecting cross-pair arbitrage: {e}")
            return []
    
    def _calculate_correlation_stability(self, timeframe_correlations: Dict) -> Dict:
        """Calculate stability scores for correlations across timeframes"""
        try:
            stability_scores = {}
            
            # Get all unique pairs
            all_pairs = set()
            for correlations in timeframe_correlations.values():
                all_pairs.update(correlations.keys())
            
            for pair in all_pairs:
                correlations_list = []
                
                for correlations in timeframe_correlations.values():
                    if pair in correlations:
                        correlations_list.append(correlations[pair]['correlation'])
                
                if len(correlations_list) >= 2:
                    # Calculate stability metrics
                    correlation_std = np.std(correlations_list)
                    correlation_mean = np.mean(correlations_list)
                    
                    # Stability score (lower std = higher stability)
                    stability_score = max(0.0, 1.0 - correlation_std * 2)  # Scale factor
                    
                    # Trend consistency
                    if len(correlations_list) >= 3:
                        trend_direction = np.sign(correlations_list[-1] - correlations_list[0])
                        consistent_trend = all(np.sign(correlations_list[i] - correlations_list[i-1]) == trend_direction 
                                             for i in range(1, len(correlations_list)))
                    else:
                        consistent_trend = True
                    
                    stability_scores[pair] = {
                        'stability_score': stability_score,
                        'correlation_std': correlation_std,
                        'correlation_mean': correlation_mean,
                        'consistent_trend': consistent_trend,
                        'timeframes_analyzed': len(correlations_list)
                    }
            
            return stability_scores
            
        except Exception as e:
            logger.error(f"Error calculating correlation stability: {e}")
            return {}
    
    def _generate_correlation_signals(self, breakdown_signals: List[Dict],
                                    stability_scores: Dict,
                                    timeframe_correlations: Dict) -> List[Dict]:
        """Generate trading signals from correlation analysis"""
        try:
            correlation_signals = []
            
            for breakdown in breakdown_signals:
                pair = breakdown['pair']
                stability = stability_scores.get(pair, {})
                
                # Enhanced signal with stability information
                signal = {
                    'signal_id': f"corr_{pair[0]}_{pair[1]}_{int(datetime.now().timestamp())}",
                    'type': 'correlation_breakdown',
                    'primary_symbol': pair[0],
                    'reference_symbol': pair[1],
                    'action': 'long' if breakdown['direction'] == 'long' else 'short',
                    'strength': breakdown['strength'],
                    'confidence': breakdown['strength'] * stability.get('stability_score', 0.5),
                    'correlation_data': breakdown,
                    'stability_data': stability,
                    'suggested_leverage': self._calculate_signal_leverage(breakdown, stability),
                    'suggested_position_size': self._calculate_signal_position_size(breakdown, stability),
                    'exit_conditions': self._generate_exit_conditions(breakdown),
                    'timestamp': datetime.now()
                }
                
                # Only include high-confidence signals
                if signal['confidence'] > 0.6:
                    correlation_signals.append(signal)
            
            return correlation_signals
            
        except Exception as e:
            logger.error(f"Error generating correlation signals: {e}")
            return []
    
    def _calculate_signal_leverage(self, breakdown: Dict, stability: Dict) -> int:
        """Calculate suggested leverage for correlation signal"""
        try:
            base_leverage = config.DEFAULT_LEVERAGE
            
            # Adjust based on signal strength
            strength_multiplier = 0.8 + (breakdown['strength'] * 0.4)  # 0.8 to 1.2
            
            # Adjust based on stability
            stability_multiplier = 0.9 + (stability.get('stability_score', 0.5) * 0.2)  # 0.9 to 1.1
            
            suggested_leverage = int(base_leverage * strength_multiplier * stability_multiplier)
            
            return max(config.MIN_LEVERAGE, min(config.MAX_LEVERAGE, suggested_leverage))
            
        except Exception as e:
            logger.error(f"Error calculating signal leverage: {e}")
            return config.DEFAULT_LEVERAGE
    
    def _calculate_signal_position_size(self, breakdown: Dict, stability: Dict) -> float:
        """Calculate suggested position size for correlation signal"""
        try:
            base_position_size = config.RISK_PER_TRADE
            
            # Adjust based on signal strength and stability
            strength_factor = breakdown['strength']
            stability_factor = stability.get('stability_score', 0.5)
            
            size_multiplier = 0.7 + (strength_factor * stability_factor * 0.6)  # 0.7 to 1.3
            
            suggested_size = base_position_size * size_multiplier
            
            return max(0.005, min(0.05, suggested_size))  # 0.5% to 5%
            
        except Exception as e:
            logger.error(f"Error calculating signal position size: {e}")
            return config.RISK_PER_TRADE
    
    def _generate_exit_conditions(self, breakdown: Dict) -> Dict:
        """Generate exit conditions for correlation signals"""
        try:
            # Target correlation reversion
            current_corr = breakdown['current_correlation']
            expected_corr = breakdown['expected_correlation']
            
            # Exit when correlation moves halfway back to expected
            target_correlation = current_corr + ((expected_corr - current_corr) * 0.6)
            
            return {
                'target_correlation': target_correlation,
                'max_hold_hours': 48,  # Maximum hold time
                'stop_loss_deviation': breakdown['max_deviation'] * 1.5,  # Stop if deviation increases
                'take_profit_reversion': abs(expected_corr - current_corr) * 0.6
            }
            
        except Exception as e:
            logger.error(f"Error generating exit conditions: {e}")
            return {
                'target_correlation': 0.7,
                'max_hold_hours': 48,
                'stop_loss_deviation': 0.3,
                'take_profit_reversion': 0.1
            }
    
    def _rank_trading_opportunities(self, correlation_signals: List[Dict],
                                  arbitrage_opportunities: List[Dict]) -> List[Dict]:
        """Rank and combine all trading opportunities"""
        try:
            all_opportunities = []
            
            # Add correlation signals
            for signal in correlation_signals:
                opportunity = {
                    'type': 'correlation_breakdown',
                    'rank_score': signal['confidence'] * signal['strength'],
                    'signal': signal,
                    'expected_return': self._estimate_signal_return(signal),
                    'risk_score': 1.0 - signal['confidence']
                }
                all_opportunities.append(opportunity)
            
            # Add arbitrage opportunities
            for arbitrage in arbitrage_opportunities:
                opportunity = {
                    'type': 'cross_pair_arbitrage',
                    'rank_score': arbitrage['confidence'] * arbitrage['arbitrage_score'],
                    'signal': arbitrage,
                    'expected_return': arbitrage['arbitrage_score'],
                    'risk_score': 1.0 - arbitrage['confidence']
                }
                all_opportunities.append(opportunity)
            
            # Sort by rank score
            all_opportunities.sort(key=lambda x: x['rank_score'], reverse=True)
            
            return all_opportunities[:10]  # Top 10 opportunities
            
        except Exception as e:
            logger.error(f"Error ranking trading opportunities: {e}")
            return []
    
    def _analyze_market_structure(self, timeframe_correlations: Dict) -> Dict:
        """Analyze overall market structure from correlations"""
        try:
            # Get most recent timeframe
            recent_tf = list(timeframe_correlations.keys())[-1]
            recent_correlations = timeframe_correlations[recent_tf]
            
            # Calculate average correlation
            all_correlations = [data['correlation'] for data in recent_correlations.values()]
            avg_correlation = np.mean(all_correlations) if all_correlations else 0.0
            correlation_std = np.std(all_correlations) if all_correlations else 0.0
            
            # Determine market structure
            if avg_correlation > 0.7:
                structure = 'high_correlation'  # Risk-on environment
            elif avg_correlation < 0.3:
                structure = 'low_correlation'   # Divergent market
            else:
                structure = 'normal_correlation'
            
            # Calculate market cohesion
            cohesion_score = max(0.0, avg_correlation - correlation_std)
            
            return {
                'structure_type': structure,
                'average_correlation': avg_correlation,
                'correlation_std': correlation_std,
                'cohesion_score': cohesion_score,
                'total_pairs_analyzed': len(recent_correlations),
                'analysis_timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market structure: {e}")
            return {'structure_type': 'unknown', 'average_correlation': 0.0}
    
    def _get_expected_correlation(self, pair: Tuple[str, str]) -> Dict:
        """Get expected correlation parameters for a pair"""
        # Check both orientations of the pair
        if pair in self.correlation_expectations:
            return self.correlation_expectations[pair]
        
        reversed_pair = (pair[1], pair[0])
        if reversed_pair in self.correlation_expectations:
            return self.correlation_expectations[reversed_pair]
        
        # Default expectations
        return {'mean': 0.65, 'std': 0.20}
    
    def _estimate_signal_return(self, signal: Dict) -> float:
        """Estimate expected return from correlation signal"""
        try:
            strength = signal['strength']
            confidence = signal['confidence']
            
            # Simple estimation based on historical correlation reversion
            base_return = strength * 0.03  # 3% max expected return
            confidence_adjusted = base_return * confidence
            
            return min(0.05, max(0.01, confidence_adjusted))  # 1% to 5% range
            
        except Exception as e:
            logger.error(f"Error estimating signal return: {e}")
            return 0.02  # Default 2%
    
    def get_correlation_matrix(self) -> Dict:
        """Get current correlation matrix"""
        return self.correlation_matrix
    
    def get_active_arbitrage_opportunities(self) -> List[Dict]:
        """Get current arbitrage opportunities"""
        return self.arbitrage_opportunities
    
    def get_cross_pair_signals(self) -> List[Dict]:
        """Get current cross-pair signals"""
        return self.cross_pair_signals

# Global instance
correlation_pair_expander = CorrelationPairExpander()