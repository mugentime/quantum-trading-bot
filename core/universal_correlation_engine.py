#!/usr/bin/env python3
"""
Universal Correlation Engine for High-Volatility Trading
Supports multi-pair correlation analysis across different volatility profiles
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VolatilityTier(Enum):
    ULTRA_HIGH = "ultra_high"    # 15%+ daily volatility
    HIGH = "high"                # 8-15% daily volatility  
    MEDIUM = "medium"            # 5-8% daily volatility
    STANDARD = "standard"        # 3-5% daily volatility

class CorrelationType(Enum):
    POSITIVE = "positive"        # Move in same direction
    NEGATIVE = "negative"        # Move in opposite direction
    DIVERGENCE = "divergence"    # Correlation breakdown

@dataclass
class CorrelationSignal:
    primary_pair: str
    reference_pair: str
    correlation_strength: float
    signal_type: CorrelationType
    confidence_score: float
    volatility_tier: VolatilityTier
    supporting_pairs: List[str]
    timeframe: str
    expected_direction: str
    risk_score: float
    timestamp: datetime

@dataclass
class CorrelationMatrix:
    pairs: List[str]
    correlation_data: Dict[Tuple[str, str], float]
    volatility_data: Dict[str, float]
    divergence_opportunities: List[CorrelationSignal]
    cluster_groups: Dict[str, List[str]]
    market_regime: str
    timestamp: datetime

class UniversalCorrelationEngine:
    """
    Advanced correlation engine supporting multiple volatility tiers
    and dynamic correlation analysis for high-frequency trading
    """
    
    def __init__(self):
        self.high_volatility_pairs = [
            'AXSUSDT', 'GALAUSDT', 'SUSHIUSDT', 'SANDUSDT', 'OPUSDT',
            'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'ATOMUSDT', 'NEARUSDT'
        ]
        
        self.volatility_tiers = {
            VolatilityTier.ULTRA_HIGH: ['AXSUSDT'],
            VolatilityTier.HIGH: ['GALAUSDT', 'SUSHIUSDT', 'SANDUSDT', 'OPUSDT'],
            VolatilityTier.MEDIUM: ['AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'ATOMUSDT'],
            VolatilityTier.STANDARD: ['NEARUSDT']
        }
        
        # Sector clustering for correlation analysis
        self.sector_clusters = {
            'gaming_metaverse': ['AXSUSDT', 'SANDUSDT', 'GALAUSDT'],
            'defi_infrastructure': ['SUSHIUSDT', 'LINKUSDT'],
            'layer1_protocols': ['AVAXUSDT', 'DOTUSDT', 'ATOMUSDT', 'NEARUSDT'],
            'optimism_ecosystem': ['OPUSDT']
        }
        
        # Correlation scoring weights
        self.correlation_weights = {
            'price_momentum': 0.25,
            'volume_correlation': 0.20,
            'volatility_sync': 0.15,
            'divergence_strength': 0.20,
            'recovery_patterns': 0.10,
            'market_regime': 0.10
        }
        
        # Dynamic thresholds by volatility tier
        self.signal_thresholds = {
            VolatilityTier.ULTRA_HIGH: {
                'entry_threshold': 0.12,
                'confidence_threshold': 0.75,
                'divergence_threshold': 0.15
            },
            VolatilityTier.HIGH: {
                'entry_threshold': 0.08,
                'confidence_threshold': 0.65,
                'divergence_threshold': 0.12
            },
            VolatilityTier.MEDIUM: {
                'entry_threshold': 0.06,
                'confidence_threshold': 0.55,
                'divergence_threshold': 0.10
            },
            VolatilityTier.STANDARD: {
                'entry_threshold': 0.04,
                'confidence_threshold': 0.50,
                'divergence_threshold': 0.08
            }
        }
        
        self.correlation_cache = {}
        self.last_update = None
        
    async def build_correlation_matrix(self, market_data: Dict) -> CorrelationMatrix:
        """
        Build comprehensive correlation matrix for all high-volatility pairs
        """
        try:
            timestamp = datetime.now()
            
            # Calculate individual pair volatilities
            volatility_data = {}
            for pair in self.high_volatility_pairs:
                if pair in market_data:
                    volatility = await self._calculate_pair_volatility(pair, market_data[pair])
                    volatility_data[pair] = volatility
            
            # Calculate pairwise correlations
            correlation_data = {}
            for i, pair1 in enumerate(self.high_volatility_pairs):
                for j, pair2 in enumerate(self.high_volatility_pairs[i+1:], i+1):
                    if pair1 in market_data and pair2 in market_data:
                        correlation = await self._calculate_pair_correlation(
                            pair1, pair2, market_data
                        )
                        correlation_data[(pair1, pair2)] = correlation
                        correlation_data[(pair2, pair1)] = correlation
            
            # Identify divergence opportunities
            divergence_opportunities = await self._identify_divergence_opportunities(
                correlation_data, volatility_data, market_data
            )
            
            # Group pairs into correlation clusters
            cluster_groups = await self._identify_correlation_clusters(correlation_data)
            
            # Determine current market regime
            market_regime = await self._determine_market_regime(market_data)
            
            matrix = CorrelationMatrix(
                pairs=self.high_volatility_pairs,
                correlation_data=correlation_data,
                volatility_data=volatility_data,
                divergence_opportunities=divergence_opportunities,
                cluster_groups=cluster_groups,
                market_regime=market_regime,
                timestamp=timestamp
            )
            
            self.correlation_cache = matrix
            self.last_update = timestamp
            
            logger.info(f"Built correlation matrix with {len(self.high_volatility_pairs)} pairs")
            logger.info(f"Found {len(divergence_opportunities)} divergence opportunities")
            
            return matrix
            
        except Exception as e:
            logger.error(f"Error building correlation matrix: {e}")
            raise
    
    async def _calculate_pair_volatility(self, pair: str, price_data: Dict) -> float:
        """Calculate rolling volatility for a trading pair"""
        try:
            if 'ohlcv' not in price_data or not price_data['ohlcv']:
                return 0.0
            
            # Get last 20 periods for volatility calculation
            ohlcv = price_data['ohlcv'][-20:]
            closes = [float(candle[4]) for candle in ohlcv]  # Close prices
            
            if len(closes) < 2:
                return 0.0
            
            # Calculate returns
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            
            # Calculate volatility as standard deviation of returns
            volatility = np.std(returns) if returns else 0.0
            
            return volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {pair}: {e}")
            return 0.0
    
    async def _calculate_pair_correlation(self, pair1: str, pair2: str, market_data: Dict) -> float:
        """Calculate correlation between two trading pairs"""
        try:
            data1 = market_data.get(pair1, {})
            data2 = market_data.get(pair2, {})
            
            if 'ohlcv' not in data1 or 'ohlcv' not in data2:
                return 0.0
            
            ohlcv1 = data1['ohlcv'][-20:]  # Last 20 periods
            ohlcv2 = data2['ohlcv'][-20:]  # Last 20 periods
            
            if len(ohlcv1) < 10 or len(ohlcv2) < 10:
                return 0.0
            
            # Align periods (use minimum length)
            min_length = min(len(ohlcv1), len(ohlcv2))
            ohlcv1 = ohlcv1[-min_length:]
            ohlcv2 = ohlcv2[-min_length:]
            
            # Extract close prices and calculate returns
            closes1 = [float(candle[4]) for candle in ohlcv1]
            closes2 = [float(candle[4]) for candle in ohlcv2]
            
            returns1 = [(closes1[i] - closes1[i-1]) / closes1[i-1] for i in range(1, len(closes1))]
            returns2 = [(closes2[i] - closes2[i-1]) / closes2[i-1] for i in range(1, len(closes2))]
            
            if len(returns1) < 5 or len(returns2) < 5:
                return 0.0
            
            # Calculate correlation coefficient
            correlation = np.corrcoef(returns1, returns2)[0, 1]
            
            # Handle NaN values
            if np.isnan(correlation):
                return 0.0
                
            return float(correlation)
            
        except Exception as e:
            logger.error(f"Error calculating correlation between {pair1} and {pair2}: {e}")
            return 0.0
    
    async def _identify_divergence_opportunities(
        self, 
        correlation_data: Dict, 
        volatility_data: Dict, 
        market_data: Dict
    ) -> List[CorrelationSignal]:
        """Identify correlation divergence opportunities for trading"""
        
        opportunities = []
        
        try:
            for (pair1, pair2), correlation in correlation_data.items():
                if pair1 >= pair2:  # Avoid duplicates
                    continue
                
                # Get volatility tiers
                tier1 = self._get_volatility_tier(pair1)
                tier2 = self._get_volatility_tier(pair2)
                
                # Use higher volatility tier for thresholds
                primary_tier = tier1 if tier1.value == 'ultra_high' or tier1.value == 'high' else tier2
                
                # Check for strong positive correlation (move together opportunities)
                if correlation > 0.7:
                    # Look for temporary divergence in recent price action
                    divergence_strength = await self._calculate_recent_divergence(
                        pair1, pair2, market_data
                    )
                    
                    if divergence_strength > self.signal_thresholds[primary_tier]['divergence_threshold']:
                        # Determine which pair should catch up
                        primary_pair, reference_pair = await self._determine_catch_up_pair(
                            pair1, pair2, market_data
                        )
                        
                        signal = CorrelationSignal(
                            primary_pair=primary_pair,
                            reference_pair=reference_pair,
                            correlation_strength=abs(correlation),
                            signal_type=CorrelationType.POSITIVE,
                            confidence_score=min(abs(correlation) * divergence_strength * 2, 1.0),
                            volatility_tier=primary_tier,
                            supporting_pairs=await self._find_supporting_pairs(primary_pair, correlation_data),
                            timeframe=self._get_optimal_timeframe(primary_tier),
                            expected_direction='convergence',
                            risk_score=self._calculate_risk_score(primary_pair, volatility_data),
                            timestamp=datetime.now()
                        )
                        
                        opportunities.append(signal)
                
                # Check for strong negative correlation (divergence opportunities)
                elif correlation < -0.5:
                    # Look for synchronized movement (divergence breakdown)
                    sync_strength = await self._calculate_recent_synchronization(
                        pair1, pair2, market_data
                    )
                    
                    if sync_strength > self.signal_thresholds[primary_tier]['divergence_threshold']:
                        signal = CorrelationSignal(
                            primary_pair=pair1,
                            reference_pair=pair2,
                            correlation_strength=abs(correlation),
                            signal_type=CorrelationType.NEGATIVE,
                            confidence_score=min(abs(correlation) * sync_strength * 1.5, 1.0),
                            volatility_tier=primary_tier,
                            supporting_pairs=await self._find_supporting_pairs(pair1, correlation_data),
                            timeframe=self._get_optimal_timeframe(primary_tier),
                            expected_direction='divergence_restoration',
                            risk_score=self._calculate_risk_score(pair1, volatility_data),
                            timestamp=datetime.now()
                        )
                        
                        opportunities.append(signal)
            
            # Sort by confidence score
            opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            logger.error(f"Error identifying divergence opportunities: {e}")
            return []
    
    async def _calculate_recent_divergence(self, pair1: str, pair2: str, market_data: Dict) -> float:
        """Calculate recent price divergence between correlated pairs"""
        try:
            data1 = market_data.get(pair1, {})
            data2 = market_data.get(pair2, {})
            
            if 'ohlcv' not in data1 or 'ohlcv' not in data2:
                return 0.0
            
            # Get recent 5 periods
            recent1 = data1['ohlcv'][-5:]
            recent2 = data2['ohlcv'][-5:]
            
            if len(recent1) < 5 or len(recent2) < 5:
                return 0.0
            
            # Calculate recent returns
            closes1 = [float(candle[4]) for candle in recent1]
            closes2 = [float(candle[4]) for candle in recent2]
            
            recent_return1 = (closes1[-1] - closes1[0]) / closes1[0]
            recent_return2 = (closes2[-1] - closes2[0]) / closes2[0]
            
            # Divergence is the absolute difference in returns
            divergence = abs(recent_return1 - recent_return2)
            
            return divergence
            
        except Exception as e:
            logger.error(f"Error calculating recent divergence: {e}")
            return 0.0
    
    async def _calculate_recent_synchronization(self, pair1: str, pair2: str, market_data: Dict) -> float:
        """Calculate recent synchronization between typically divergent pairs"""
        try:
            data1 = market_data.get(pair1, {})
            data2 = market_data.get(pair2, {})
            
            if 'ohlcv' not in data1 or 'ohlcv' not in data2:
                return 0.0
            
            # Get recent 5 periods
            recent1 = data1['ohlcv'][-5:]
            recent2 = data2['ohlcv'][-5:]
            
            if len(recent1) < 5 or len(recent2) < 5:
                return 0.0
            
            # Calculate period-by-period correlation
            closes1 = [float(candle[4]) for candle in recent1]
            closes2 = [float(candle[4]) for candle in recent2]
            
            returns1 = [(closes1[i] - closes1[i-1]) / closes1[i-1] for i in range(1, len(closes1))]
            returns2 = [(closes2[i] - closes2[i-1]) / closes2[i-1] for i in range(1, len(closes2))]
            
            # Calculate recent correlation
            if len(returns1) >= 3 and len(returns2) >= 3:
                recent_corr = np.corrcoef(returns1, returns2)[0, 1]
                if not np.isnan(recent_corr):
                    # Synchronization strength is positive correlation for typically negative pairs
                    return max(recent_corr, 0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating recent synchronization: {e}")
            return 0.0
    
    async def _determine_catch_up_pair(self, pair1: str, pair2: str, market_data: Dict) -> Tuple[str, str]:
        """Determine which pair should catch up in a divergence scenario"""
        try:
            data1 = market_data.get(pair1, {})
            data2 = market_data.get(pair2, {})
            
            # Get recent performance
            recent_return1 = 0
            recent_return2 = 0
            
            if 'change_percent' in data1:
                recent_return1 = float(data1['change_percent']) / 100
            
            if 'change_percent' in data2:
                recent_return2 = float(data2['change_percent']) / 100
            
            # The underperforming pair should catch up
            if recent_return1 < recent_return2:
                return pair1, pair2  # pair1 should catch up to pair2
            else:
                return pair2, pair1  # pair2 should catch up to pair1
                
        except Exception as e:
            logger.error(f"Error determining catch-up pair: {e}")
            return pair1, pair2
    
    async def _find_supporting_pairs(self, primary_pair: str, correlation_data: Dict) -> List[str]:
        """Find pairs that support the primary pair's signal"""
        supporting = []
        
        for (pair1, pair2), correlation in correlation_data.items():
            if pair1 == primary_pair and abs(correlation) > 0.6:
                supporting.append(pair2)
            elif pair2 == primary_pair and abs(correlation) > 0.6:
                supporting.append(pair1)
        
        return supporting[:3]  # Return top 3 supporting pairs
    
    def _get_volatility_tier(self, pair: str) -> VolatilityTier:
        """Get volatility tier for a trading pair"""
        for tier, pairs in self.volatility_tiers.items():
            if pair in pairs:
                return tier
        return VolatilityTier.STANDARD
    
    def _get_optimal_timeframe(self, volatility_tier: VolatilityTier) -> str:
        """Get optimal timeframe for volatility tier"""
        timeframe_map = {
            VolatilityTier.ULTRA_HIGH: '5m',
            VolatilityTier.HIGH: '15m',
            VolatilityTier.MEDIUM: '1h',
            VolatilityTier.STANDARD: '4h'
        }
        return timeframe_map.get(volatility_tier, '1h')
    
    def _calculate_risk_score(self, pair: str, volatility_data: Dict) -> float:
        """Calculate risk score for a pair based on volatility"""
        volatility = volatility_data.get(pair, 0.05)
        
        # Risk score from 0.1 (low risk) to 1.0 (high risk)
        risk_score = min(volatility * 10, 1.0)
        return max(risk_score, 0.1)
    
    async def _identify_correlation_clusters(self, correlation_data: Dict) -> Dict[str, List[str]]:
        """Identify groups of highly correlated pairs"""
        clusters = {}
        
        try:
            # Create correlation matrix
            pairs = list(set([pair for pair_tuple in correlation_data.keys() for pair in pair_tuple]))
            
            high_corr_pairs = []
            for (pair1, pair2), correlation in correlation_data.items():
                if abs(correlation) > 0.7:  # High correlation threshold
                    high_corr_pairs.append((pair1, pair2, correlation))
            
            # Group into clusters
            cluster_id = 0
            used_pairs = set()
            
            for pair1, pair2, corr in high_corr_pairs:
                if pair1 not in used_pairs and pair2 not in used_pairs:
                    cluster_name = f"cluster_{cluster_id}"
                    clusters[cluster_name] = [pair1, pair2]
                    used_pairs.add(pair1)
                    used_pairs.add(pair2)
                    cluster_id += 1
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error identifying correlation clusters: {e}")
            return {}
    
    async def _determine_market_regime(self, market_data: Dict) -> str:
        """Determine current market regime (bull, bear, sideways)"""
        try:
            positive_moves = 0
            total_moves = 0
            
            for pair, data in market_data.items():
                if 'change_percent' in data:
                    change = float(data['change_percent'])
                    total_moves += 1
                    if change > 0:
                        positive_moves += 1
            
            if total_moves == 0:
                return 'unknown'
            
            bullish_ratio = positive_moves / total_moves
            
            if bullish_ratio > 0.7:
                return 'bull'
            elif bullish_ratio < 0.3:
                return 'bear'
            else:
                return 'sideways'
                
        except Exception as e:
            logger.error(f"Error determining market regime: {e}")
            return 'unknown'
    
    async def generate_enhanced_signals(self, correlation_matrix: CorrelationMatrix) -> List[CorrelationSignal]:
        """Generate enhanced trading signals based on correlation analysis"""
        try:
            signals = []
            
            # Filter high-confidence opportunities
            for opportunity in correlation_matrix.divergence_opportunities:
                tier = opportunity.volatility_tier
                threshold = self.signal_thresholds[tier]['confidence_threshold']
                
                if opportunity.confidence_score >= threshold:
                    signals.append(opportunity)
            
            logger.info(f"Generated {len(signals)} enhanced correlation signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating enhanced signals: {e}")
            return []
    
    async def get_correlation_summary(self) -> Dict:
        """Get summary of current correlation analysis"""
        try:
            if not self.correlation_cache:
                return {'error': 'No correlation data available'}
            
            matrix = self.correlation_cache
            
            # Find strongest correlations
            strongest_correlations = []
            for (pair1, pair2), correlation in matrix.correlation_data.items():
                if pair1 < pair2:  # Avoid duplicates
                    strength = 'very_strong' if abs(correlation) > 0.8 else 'strong' if abs(correlation) > 0.6 else 'moderate'
                    strongest_correlations.append({
                        'pair_a': pair1,
                        'pair_b': pair2,
                        'correlation': correlation,
                        'strength': strength
                    })
            
            strongest_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            # Top opportunities
            top_opportunities = []
            for opp in matrix.divergence_opportunities[:5]:
                top_opportunities.append({
                    'pair_a': opp.primary_pair,
                    'pair_b': opp.reference_pair,
                    'divergence_magnitude': opp.correlation_strength,
                    'expected_direction': opp.expected_direction,
                    'confidence': opp.confidence_score
                })
            
            summary = {
                'total_pairs': len(matrix.pairs),
                'clusters_analyzed': len(matrix.cluster_groups),
                'divergence_opportunities': len(matrix.divergence_opportunities),
                'market_regime': matrix.market_regime,
                'strongest_correlations': strongest_correlations[:10],
                'top_opportunities': top_opportunities,
                'last_updated': matrix.timestamp.isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating correlation summary: {e}")
            return {'error': str(e)}