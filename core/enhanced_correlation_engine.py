"""Enhanced Multi-Pair Correlation Engine for 10 Trading Pairs"""
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from itertools import combinations
import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)

@dataclass
class CorrelationMatrix:
    """Advanced correlation matrix with cluster analysis"""
    pairs: List[str]
    correlation_data: np.ndarray
    timestamp: datetime
    cluster_groups: Dict[str, List[str]]
    strength_scores: Dict[str, float]
    divergence_opportunities: List[Dict]

@dataclass 
class EnhancedCorrelationSignal:
    """Enhanced signal with multi-pair correlation analysis"""
    primary_pair: str
    reference_pair: str
    signal_type: str
    correlation_strength: float
    cluster_alignment: float
    market_regime_factor: float
    confidence_score: float
    expected_move: float
    risk_factor: float
    supporting_pairs: List[str]
    timestamp: datetime

class EnhancedCorrelationEngine:
    """Advanced correlation engine for 10-pair trading system"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.pairs = [
            'BTCUSDT', 'ETHUSDT', 'AXSUSDT', 'SOLUSDT',    # Core crypto with AXSUSDT
            'BNBUSDT', 'XRPUSDT',                          # Exchange/utility tokens  
            'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT',             # Layer-1 & meme leader
            'DOTUSDT', 'LINKUSDT'                          # Infrastructure tokens
        ]
        
        # Define correlation clusters based on token categories
        self.clusters = {
            'layer1_core': ['BTCUSDT', 'ETHUSDT'],
            'gaming_high_vol': ['AXSUSDT'],  # AXSUSDT for ultra-high frequency trading
            'layer1_alt': ['SOLUSDT', 'ADAUSDT', 'AVAXUSDT'],
            'exchange_util': ['BNBUSDT', 'XRPUSDT'],
            'infrastructure': ['DOTUSDT', 'LINKUSDT'],
            'meme_momentum': ['DOGEUSDT']
        }
        
        self.correlation_history = []
        self.lookback_period = 100  # Increased for 10 pairs
        
    async def build_correlation_matrix(self, timeframe: str = '15m') -> CorrelationMatrix:
        """Build comprehensive correlation matrix for all 10 pairs"""
        try:
            # Fetch price data for all pairs
            price_data = {}
            for pair in self.pairs:
                ohlcv = await self.exchange.fetch_ohlcv(
                    pair, timeframe, limit=self.lookback_period
                )
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                price_data[pair] = df['close'].pct_change().dropna()
            
            # Create correlation matrix
            combined_df = pd.DataFrame(price_data)
            correlation_matrix = combined_df.corr().values
            
            # Analyze cluster correlations
            cluster_groups = await self._analyze_cluster_correlations(combined_df)
            
            # Calculate strength scores for each pair
            strength_scores = await self._calculate_strength_scores(combined_df, correlation_matrix)
            
            # Identify divergence opportunities
            divergence_ops = await self._find_divergence_opportunities(
                combined_df, correlation_matrix
            )
            
            return CorrelationMatrix(
                pairs=self.pairs,
                correlation_data=correlation_matrix,
                timestamp=datetime.now(),
                cluster_groups=cluster_groups,
                strength_scores=strength_scores,
                divergence_opportunities=divergence_ops
            )
            
        except Exception as e:
            logger.error(f"Error building correlation matrix: {e}")
            return None
    
    async def _analyze_cluster_correlations(self, price_df: pd.DataFrame) -> Dict[str, List[str]]:
        """Analyze correlations within defined clusters"""
        cluster_analysis = {}
        
        for cluster_name, cluster_pairs in self.clusters.items():
            available_pairs = [p for p in cluster_pairs if p in price_df.columns]
            if len(available_pairs) > 1:
                cluster_corr = price_df[available_pairs].corr()
                avg_correlation = cluster_corr.values[np.triu_indices_from(cluster_corr.values, k=1)].mean()
                
                cluster_analysis[cluster_name] = {
                    'pairs': available_pairs,
                    'avg_correlation': avg_correlation,
                    'strength': 'strong' if avg_correlation > 0.6 else 'moderate' if avg_correlation > 0.3 else 'weak'
                }
        
        return cluster_analysis
    
    async def _calculate_strength_scores(self, price_df: pd.DataFrame, corr_matrix: np.ndarray) -> Dict[str, float]:
        """Calculate relative strength scores for each pair"""
        strength_scores = {}
        
        # Calculate momentum and volatility metrics
        for i, pair in enumerate(self.pairs):
            if pair in price_df.columns:
                returns = price_df[pair]
                
                # Momentum score (recent vs historical performance)
                recent_momentum = returns.tail(10).mean()
                historical_momentum = returns.head(50).mean()
                momentum_score = recent_momentum - historical_momentum
                
                # Volatility score
                volatility_score = returns.tail(20).std()
                
                # Correlation stability (how consistent correlations are)
                pair_correlations = np.abs(corr_matrix[i, :])
                correlation_stability = 1 / (np.std(pair_correlations) + 0.001)  # Avoid division by zero
                
                # Combined strength score
                strength_scores[pair] = {
                    'momentum': momentum_score,
                    'volatility': volatility_score, 
                    'correlation_stability': correlation_stability,
                    'composite_score': momentum_score * 0.4 + volatility_score * 0.3 + correlation_stability * 0.3
                }
        
        return strength_scores
    
    async def _find_divergence_opportunities(self, price_df: pd.DataFrame, corr_matrix: np.ndarray) -> List[Dict]:
        """Identify pairs showing correlation divergence (trading opportunities)"""
        opportunities = []
        
        for i, pair_a in enumerate(self.pairs):
            for j, pair_b in enumerate(self.pairs[i+1:], i+1):
                if pair_a in price_df.columns and pair_b in price_df.columns:
                    # Historical correlation
                    historical_corr = corr_matrix[i, j]
                    
                    # Recent correlation (last 20 periods)
                    recent_data_a = price_df[pair_a].tail(20)
                    recent_data_b = price_df[pair_b].tail(20)
                    recent_corr = recent_data_a.corr(recent_data_b)
                    
                    # Correlation divergence
                    divergence = abs(historical_corr - recent_corr)
                    
                    if divergence > 0.3:  # Significant divergence threshold
                        # Determine expected reversion direction
                        direction = 'converge' if abs(recent_corr) < abs(historical_corr) else 'diverge'
                        
                        opportunities.append({
                            'pair_a': pair_a,
                            'pair_b': pair_b,
                            'historical_corr': historical_corr,
                            'recent_corr': recent_corr,
                            'divergence_magnitude': divergence,
                            'expected_direction': direction,
                            'confidence': min(divergence * 2, 1.0),  # Normalize to 0-1
                            'cluster_match': self._pairs_in_same_cluster(pair_a, pair_b)
                        })
        
        # Sort by divergence magnitude
        return sorted(opportunities, key=lambda x: x['divergence_magnitude'], reverse=True)[:10]
    
    def _pairs_in_same_cluster(self, pair_a: str, pair_b: str) -> bool:
        """Check if two pairs belong to the same cluster"""
        for cluster_pairs in self.clusters.values():
            if pair_a in cluster_pairs and pair_b in cluster_pairs:
                return True
        return False
    
    async def generate_enhanced_signals(self, correlation_matrix: CorrelationMatrix) -> List[EnhancedCorrelationSignal]:
        """Generate trading signals using enhanced correlation analysis"""
        signals = []
        
        try:
            # Process top divergence opportunities
            for opp in correlation_matrix.divergence_opportunities[:5]:  # Top 5 opportunities
                primary_pair = opp['pair_a']
                reference_pair = opp['pair_b']
                
                # Determine signal type based on divergence pattern
                if opp['expected_direction'] == 'converge':
                    if opp['recent_corr'] > opp['historical_corr']:
                        signal_type = 'mean_reversion'
                    else:
                        signal_type = 'trend_continuation'
                else:
                    signal_type = 'breakout_divergence'
                
                # Calculate market regime factor
                regime_factor = await self._calculate_market_regime_factor(primary_pair, correlation_matrix)
                
                # Find supporting pairs (correlated pairs showing similar patterns)
                supporting_pairs = await self._find_supporting_pairs(
                    primary_pair, correlation_matrix
                )
                
                # Calculate confidence score
                confidence = self._calculate_enhanced_confidence(
                    opp, regime_factor, len(supporting_pairs)
                )
                
                signal = EnhancedCorrelationSignal(
                    primary_pair=primary_pair,
                    reference_pair=reference_pair,
                    signal_type=signal_type,
                    correlation_strength=abs(opp['historical_corr']),
                    cluster_alignment=1.0 if opp['cluster_match'] else 0.5,
                    market_regime_factor=regime_factor,
                    confidence_score=confidence,
                    expected_move=opp['divergence_magnitude'] * 0.02,  # Estimated price move
                    risk_factor=1 - confidence,
                    supporting_pairs=supporting_pairs,
                    timestamp=datetime.now()
                )
                
                signals.append(signal)
            
            # Sort by confidence score
            return sorted(signals, key=lambda x: x.confidence_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error generating enhanced signals: {e}")
            return []
    
    async def _calculate_market_regime_factor(self, pair: str, correlation_matrix: CorrelationMatrix) -> float:
        """Calculate market regime factor for better signal timing"""
        try:
            # Get recent price action for the pair
            ohlcv = await self.exchange.fetch_ohlcv(pair, '1h', limit=24)
            closes = [candle[4] for candle in ohlcv]
            
            # Calculate trend strength
            sma_fast = np.mean(closes[-5:])  # 5-hour average
            sma_slow = np.mean(closes[-20:])  # 20-hour average
            
            trend_factor = (sma_fast - sma_slow) / sma_slow
            
            # Calculate volatility regime
            returns = np.diff(closes) / closes[:-1]
            current_volatility = np.std(returns[-10:])  # Recent volatility
            average_volatility = np.std(returns)  # Overall volatility
            
            volatility_factor = current_volatility / average_volatility
            
            # Combine factors (trend-following in low volatility, mean-reversion in high volatility)
            regime_factor = abs(trend_factor) * (1 / volatility_factor)
            
            return min(regime_factor, 2.0)  # Cap at 2.0
            
        except Exception as e:
            logger.warning(f"Error calculating market regime factor: {e}")
            return 0.5  # Neutral factor
    
    async def _find_supporting_pairs(self, primary_pair: str, correlation_matrix: CorrelationMatrix) -> List[str]:
        """Find pairs that support the signal (highly correlated pairs moving similarly)"""
        supporting_pairs = []
        
        try:
            primary_idx = correlation_matrix.pairs.index(primary_pair)
            correlations = correlation_matrix.correlation_data[primary_idx, :]
            
            # Find highly correlated pairs (> 0.6 correlation)
            for i, corr in enumerate(correlations):
                if abs(corr) > 0.6 and i != primary_idx:
                    supporting_pairs.append(correlation_matrix.pairs[i])
            
            return supporting_pairs[:3]  # Return top 3 supporting pairs
            
        except Exception as e:
            logger.warning(f"Error finding supporting pairs: {e}")
            return []
    
    def _calculate_enhanced_confidence(self, opportunity: Dict, regime_factor: float, supporting_count: int) -> float:
        """Calculate enhanced confidence score"""
        base_confidence = opportunity['confidence']
        
        # Boost confidence with supporting factors
        regime_boost = min(regime_factor * 0.1, 0.2)
        support_boost = min(supporting_count * 0.05, 0.15)
        cluster_boost = 0.1 if opportunity['cluster_match'] else 0
        
        final_confidence = min(base_confidence + regime_boost + support_boost + cluster_boost, 0.95)
        
        return final_confidence
    
    async def get_correlation_summary(self) -> Dict:
        """Get summary of current correlation state"""
        correlation_matrix = await self.build_correlation_matrix()
        
        if not correlation_matrix:
            return {"error": "Failed to build correlation matrix"}
        
        return {
            "timestamp": correlation_matrix.timestamp.isoformat(),
            "total_pairs": len(correlation_matrix.pairs),
            "clusters_analyzed": len(correlation_matrix.cluster_groups),
            "divergence_opportunities": len(correlation_matrix.divergence_opportunities),
            "top_opportunities": correlation_matrix.divergence_opportunities[:3],
            "strongest_correlations": self._get_strongest_correlations(correlation_matrix),
            "market_regime": "enhanced_multi_pair_analysis"
        }
    
    def _get_strongest_correlations(self, correlation_matrix: CorrelationMatrix) -> List[Dict]:
        """Get the strongest correlation pairs"""
        strong_correlations = []
        
        corr_data = correlation_matrix.correlation_data
        pairs = correlation_matrix.pairs
        
        for i in range(len(pairs)):
            for j in range(i+1, len(pairs)):
                correlation = corr_data[i, j]
                if abs(correlation) > 0.7:  # Strong correlation threshold
                    strong_correlations.append({
                        'pair_a': pairs[i],
                        'pair_b': pairs[j],
                        'correlation': correlation,
                        'strength': 'very_strong' if abs(correlation) > 0.8 else 'strong'
                    })
        
        return sorted(strong_correlations, key=lambda x: abs(x['correlation']), reverse=True)[:5]

# Create global instance
enhanced_correlation_engine = None

async def get_enhanced_correlation_engine(exchange):
    """Get or create enhanced correlation engine instance"""
    global enhanced_correlation_engine
    if enhanced_correlation_engine is None:
        enhanced_correlation_engine = EnhancedCorrelationEngine(exchange)
    return enhanced_correlation_engine