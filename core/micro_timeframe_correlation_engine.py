"""
Micro-Timeframe Correlation Engine
Specialized for 1m/3m/5m high-frequency scalping analysis
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from collections import deque
import ccxt.async_support as ccxt
from .enhanced_correlation_engine import CorrelationMatrix, EnhancedCorrelationSignal

logger = logging.getLogger(__name__)

@dataclass
class MicroTimeframeSignal:
    """High-frequency scalping signal with micro-timeframe analysis"""
    symbol: str
    timeframe: str
    signal_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    correlation_strength: float
    volume_confirmation: bool
    momentum_score: float
    expected_duration_minutes: int
    risk_reward_ratio: float
    timestamp: datetime

@dataclass
class VolumeProfile:
    """Volume analysis for liquidity validation"""
    symbol: str
    avg_volume_1m: float
    volume_spike_threshold: float
    bid_ask_spread: float
    market_depth_score: float
    slippage_estimate: float

class MicroTimeframeCorrelationEngine:
    """High-frequency correlation engine optimized for scalping"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.primary_scalping_pairs = ['ETHUSDT']  # Focus on best performer
        self.reference_pairs = ['BTCUSDT', 'SOLUSDT', 'LINKUSDT']  # For correlation
        self.timeframes = ['1m', '3m', '5m']
        
        # High-frequency parameters
        self.micro_lookback = 20  # Much shorter lookback for responsiveness
        self.correlation_threshold = 0.60  # Lower threshold for more signals
        self.volume_spike_threshold = 1.5  # 50% above average
        
        # Real-time data buffers
        self.price_buffers = {tf: {} for tf in self.timeframes}
        self.volume_buffers = {tf: {} for tf in self.timeframes}
        self.correlation_buffers = {tf: deque(maxlen=50) for tf in self.timeframes}
        
        # Performance tracking
        self.signal_performance = {}
        self.last_update = {}
        
    async def initialize_buffers(self):
        """Initialize real-time data buffers for all timeframes"""
        try:
            for timeframe in self.timeframes:
                self.price_buffers[timeframe] = {}
                self.volume_buffers[timeframe] = {}
                
                all_pairs = self.primary_scalping_pairs + self.reference_pairs
                
                for pair in all_pairs:
                    # Initialize with recent data
                    ohlcv = await self.exchange.fetch_ohlcv(
                        pair, timeframe, limit=self.micro_lookback * 2
                    )
                    
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    self.price_buffers[timeframe][pair] = deque(
                        df['close'].values, maxlen=self.micro_lookback
                    )
                    self.volume_buffers[timeframe][pair] = deque(
                        df['volume'].values, maxlen=self.micro_lookback
                    )
                
                logger.info(f"Initialized buffers for {timeframe} timeframe")
                
        except Exception as e:
            logger.error(f"Error initializing buffers: {e}")
    
    async def update_real_time_data(self, timeframe: str):
        """Update real-time price and volume data"""
        try:
            all_pairs = self.primary_scalping_pairs + self.reference_pairs
            
            for pair in all_pairs:
                # Get latest candle
                ohlcv = await self.exchange.fetch_ohlcv(pair, timeframe, limit=2)
                
                if len(ohlcv) >= 2:
                    latest_candle = ohlcv[-1]  # Most recent complete candle
                    close_price = latest_candle[4]
                    volume = latest_candle[5]
                    
                    # Update buffers
                    self.price_buffers[timeframe][pair].append(close_price)
                    self.volume_buffers[timeframe][pair].append(volume)
            
            self.last_update[timeframe] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating real-time data for {timeframe}: {e}")
    
    async def calculate_micro_correlation(self, timeframe: str) -> Dict:
        """Calculate real-time correlation for micro timeframe"""
        try:
            correlations = {}
            
            # Calculate correlations between primary and reference pairs
            for primary_pair in self.primary_scalping_pairs:
                primary_prices = list(self.price_buffers[timeframe][primary_pair])
                
                if len(primary_prices) < self.micro_lookback:
                    continue
                
                primary_returns = pd.Series(primary_prices).pct_change().dropna()
                
                pair_correlations = {}
                
                for ref_pair in self.reference_pairs:
                    ref_prices = list(self.price_buffers[timeframe][ref_pair])
                    
                    if len(ref_prices) < self.micro_lookback:
                        continue
                    
                    ref_returns = pd.Series(ref_prices).pct_change().dropna()
                    
                    # Calculate correlation
                    if len(primary_returns) == len(ref_returns) and len(primary_returns) > 5:
                        correlation = primary_returns.corr(ref_returns)
                        pair_correlations[ref_pair] = correlation if not pd.isna(correlation) else 0.0
                
                correlations[primary_pair] = pair_correlations
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error calculating micro correlation for {timeframe}: {e}")
            return {}
    
    async def analyze_volume_profile(self, symbol: str, timeframe: str) -> VolumeProfile:
        """Analyze volume profile for liquidity validation"""
        try:
            volumes = list(self.volume_buffers[timeframe][symbol])
            
            if len(volumes) < 10:
                return VolumeProfile(
                    symbol=symbol,
                    avg_volume_1m=0,
                    volume_spike_threshold=0,
                    bid_ask_spread=0.01,  # Default estimate
                    market_depth_score=0.5,
                    slippage_estimate=0.05
                )
            
            avg_volume = np.mean(volumes)
            current_volume = volumes[-1]
            volume_spike_threshold = avg_volume * self.volume_spike_threshold
            
            # Get order book for spread analysis
            try:
                order_book = await self.exchange.fetch_order_book(symbol, limit=10)
                best_bid = order_book['bids'][0][0] if order_book['bids'] else 0
                best_ask = order_book['asks'][0][0] if order_book['asks'] else 0
                
                bid_ask_spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0.001
                
                # Calculate market depth score
                bid_depth = sum([order[1] for order in order_book['bids'][:5]])
                ask_depth = sum([order[1] for order in order_book['asks'][:5]])
                depth_score = min(1.0, (bid_depth + ask_depth) / 1000000)  # Normalize to 1M
                
            except:
                bid_ask_spread = 0.001
                depth_score = 0.7  # Default for ETHUSDT
            
            # Estimate slippage based on volume and spread
            slippage_estimate = bid_ask_spread + (0.001 if current_volume > volume_spike_threshold else 0.002)
            
            return VolumeProfile(
                symbol=symbol,
                avg_volume_1m=avg_volume,
                volume_spike_threshold=volume_spike_threshold,
                bid_ask_spread=bid_ask_spread,
                market_depth_score=depth_score,
                slippage_estimate=slippage_estimate
            )
            
        except Exception as e:
            logger.error(f"Error analyzing volume profile for {symbol}: {e}")
            return VolumeProfile(symbol, 0, 0, 0.001, 0.5, 0.05)
    
    async def detect_micro_breakdowns(self, correlations: Dict, timeframe: str) -> List[Dict]:
        """Detect correlation breakdowns suitable for scalping"""
        breakdowns = []
        
        try:
            for primary_pair, corr_data in correlations.items():
                prices = list(self.price_buffers[timeframe][primary_pair])
                
                if len(prices) < 10:
                    continue
                
                # Calculate recent momentum
                short_momentum = (prices[-1] - prices[-3]) / prices[-3] if len(prices) >= 3 else 0
                medium_momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
                
                for ref_pair, correlation in corr_data.items():
                    # Check for correlation breakdown
                    if abs(correlation) > self.correlation_threshold:
                        ref_prices = list(self.price_buffers[timeframe][ref_pair])
                        ref_momentum = (ref_prices[-1] - ref_prices[-3]) / ref_prices[-3] if len(ref_prices) >= 3 else 0
                        
                        # Look for momentum divergence
                        momentum_divergence = abs(short_momentum - ref_momentum)
                        
                        if momentum_divergence > 0.002:  # 0.2% divergence threshold
                            volume_profile = await self.analyze_volume_profile(primary_pair, timeframe)
                            
                            breakdown = {
                                'primary_pair': primary_pair,
                                'reference_pair': ref_pair,
                                'correlation': correlation,
                                'momentum_divergence': momentum_divergence,
                                'primary_momentum': short_momentum,
                                'reference_momentum': ref_momentum,
                                'volume_confirmation': volume_profile.avg_volume_1m > volume_profile.volume_spike_threshold * 0.8,
                                'timeframe': timeframe,
                                'confidence': min(0.95, abs(correlation) + momentum_divergence * 100),
                                'timestamp': datetime.now()
                            }
                            
                            breakdowns.append(breakdown)
            
        except Exception as e:
            logger.error(f"Error detecting micro breakdowns: {e}")
        
        return breakdowns
    
    async def generate_scalping_signals(self, timeframe: str) -> List[MicroTimeframeSignal]:
        """Generate high-frequency scalping signals"""
        signals = []
        
        try:
            # Update real-time data
            await self.update_real_time_data(timeframe)
            
            # Calculate correlations
            correlations = await self.calculate_micro_correlation(timeframe)
            
            if not correlations:
                return signals
            
            # Detect breakdown opportunities
            breakdowns = await self.detect_micro_breakdowns(correlations, timeframe)
            
            for breakdown in breakdowns:
                symbol = breakdown['primary_pair']
                current_price = list(self.price_buffers[timeframe][symbol])[-1]
                
                # Determine signal direction
                momentum = breakdown['primary_momentum']
                signal_type = 'long' if momentum > 0 else 'short'
                
                # Calculate scalping parameters based on timeframe
                if timeframe == '1m':
                    sl_pct, tp_pct = 0.008, 0.012  # 0.8% SL, 1.2% TP
                    max_duration = 15
                elif timeframe == '3m':
                    sl_pct, tp_pct = 0.012, 0.018  # 1.2% SL, 1.8% TP
                    max_duration = 30
                else:  # 5m
                    sl_pct, tp_pct = 0.015, 0.022  # 1.5% SL, 2.2% TP
                    max_duration = 60
                
                # Calculate entry, SL, TP
                if signal_type == 'long':
                    stop_loss = current_price * (1 - sl_pct)
                    take_profit = current_price * (1 + tp_pct)
                else:
                    stop_loss = current_price * (1 + sl_pct)
                    take_profit = current_price * (1 - tp_pct)
                
                risk_reward = tp_pct / sl_pct
                
                # Volume confirmation
                volume_profile = await self.analyze_volume_profile(symbol, timeframe)
                
                signal = MicroTimeframeSignal(
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_type=signal_type,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=breakdown['confidence'],
                    correlation_strength=abs(breakdown['correlation']),
                    volume_confirmation=breakdown['volume_confirmation'],
                    momentum_score=abs(momentum) * 100,
                    expected_duration_minutes=max_duration,
                    risk_reward_ratio=risk_reward,
                    timestamp=datetime.now()
                )
                
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error generating scalping signals for {timeframe}: {e}")
        
        return signals
    
    async def run_continuous_analysis(self, update_interval: int = 60):
        """Run continuous micro-timeframe analysis"""
        logger.info("Starting continuous micro-timeframe analysis")
        
        # Initialize buffers
        await self.initialize_buffers()
        
        while True:
            try:
                all_signals = []
                
                # Generate signals for all timeframes
                for timeframe in self.timeframes:
                    signals = await self.generate_scalping_signals(timeframe)
                    all_signals.extend(signals)
                
                if all_signals:
                    # Sort by confidence and return top signals
                    all_signals.sort(key=lambda x: x.confidence, reverse=True)
                    
                    logger.info(f"Generated {len(all_signals)} scalping signals")
                    
                    # Log top signal for monitoring
                    if all_signals:
                        top_signal = all_signals[0]
                        logger.info(f"Top signal: {top_signal.symbol} {top_signal.signal_type} "
                                   f"@ {top_signal.entry_price:.4f} "
                                   f"(conf: {top_signal.confidence:.2f}, tf: {top_signal.timeframe})")
                
                # Wait before next analysis
                await asyncio.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
                await asyncio.sleep(update_interval)
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics for the micro-timeframe engine"""
        stats = {
            'total_signals_generated': len(self.signal_performance),
            'timeframe_distribution': {},
            'avg_confidence_by_timeframe': {},
            'buffer_health': {}
        }
        
        # Calculate timeframe distribution
        for tf in self.timeframes:
            tf_signals = [s for s in self.signal_performance.values() if s.get('timeframe') == tf]
            stats['timeframe_distribution'][tf] = len(tf_signals)
            
            if tf_signals:
                avg_conf = np.mean([s.get('confidence', 0) for s in tf_signals])
                stats['avg_confidence_by_timeframe'][tf] = avg_conf
        
        # Check buffer health
        for tf in self.timeframes:
            buffer_sizes = {pair: len(buffer) for pair, buffer in self.price_buffers[tf].items()}
            stats['buffer_health'][tf] = buffer_sizes
        
        return stats

# Utility functions
async def test_micro_engine(exchange):
    """Test function for micro-timeframe engine"""
    engine = MicroTimeframeCorrelationEngine(exchange)
    
    # Initialize and run test
    await engine.initialize_buffers()
    
    # Generate test signals
    for timeframe in ['1m', '3m', '5m']:
        signals = await engine.generate_scalping_signals(timeframe)
        print(f"{timeframe}: {len(signals)} signals generated")
        
        for signal in signals[:2]:  # Print top 2 signals
            print(f"  {signal.symbol} {signal.signal_type} @ {signal.entry_price:.4f} "
                  f"(SL: {signal.stop_loss:.4f}, TP: {signal.take_profit:.4f})")

if __name__ == "__main__":
    # Example usage
    import ccxt.async_support as ccxt
    
    async def main():
        exchange = ccxt.binance()
        await test_micro_engine(exchange)
        await exchange.close()
    
    asyncio.run(main())