"""
High-Frequency Signal Generation Framework
Specialized for scalping with 14% daily target
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum
from collections import deque
import uuid

from .micro_timeframe_correlation_engine import MicroTimeframeSignal, MicroTimeframeCorrelationEngine

logger = logging.getLogger(__name__)

class ScalpingSignalType(Enum):
    """High-frequency scalping signal types"""
    MICRO_CORRELATION_BREAKDOWN = "micro_correlation_breakdown"
    VOLUME_MOMENTUM_SPIKE = "volume_momentum_spike"
    QUICK_MEAN_REVERSION = "quick_mean_reversion"
    MOMENTUM_CONTINUATION = "momentum_continuation"
    LIQUIDITY_GRAB = "liquidity_grab"

class SignalPriority(Enum):
    """Signal priority levels"""
    CRITICAL = "critical"  # > 90% confidence, immediate execution
    HIGH = "high"          # 80-90% confidence
    MEDIUM = "medium"      # 70-80% confidence
    LOW = "low"            # 60-70% confidence

@dataclass
class HighFrequencySignal:
    """Optimized signal structure for scalping"""
    id: str
    timestamp: datetime
    symbol: str
    signal_type: ScalpingSignalType
    priority: SignalPriority
    timeframe: str
    
    # Entry parameters
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size_pct: float
    
    # Signal quality metrics
    confidence: float
    correlation_strength: float
    volume_confirmation: bool
    momentum_score: float
    liquidity_score: float
    
    # Execution parameters
    max_slippage_pct: float
    max_hold_minutes: int
    risk_reward_ratio: float
    expected_move_pct: float
    
    # Meta data
    source_engine: str
    reasoning: str
    supporting_indicators: List[str]
    
    # Status tracking
    status: str = "pending"  # pending, active, filled, cancelled, expired
    fill_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl_pct: Optional[float] = None

class HighFrequencySignalGenerator:
    """Advanced signal generator for high-frequency scalping"""
    
    def __init__(self, micro_engine: MicroTimeframeCorrelationEngine):
        self.micro_engine = micro_engine
        self.active_signals = {}
        self.signal_history = deque(maxlen=1000)
        self.performance_stats = {
            'total_generated': 0,
            'total_filled': 0,
            'win_rate': 0.0,
            'avg_pnl_pct': 0.0,
            'avg_hold_time_minutes': 0.0
        }
        
        # High-frequency parameters optimized for 14% daily target
        self.config = {
            'min_confidence': 0.65,        # Lower threshold for more signals
            'min_risk_reward': 1.4,        # Minimum 1.4:1 R/R ratio
            'max_concurrent_signals': 3,   # Limit concurrent positions
            'max_daily_signals': 80,       # Prevent overtrading
            'confidence_decay_minutes': 5, # Signal confidence decay
            'priority_boost_threshold': 0.85,  # Boost to HIGH priority
            'critical_threshold': 0.92     # Critical priority threshold
        }
        
        # Signal filtering and enhancement
        self.signal_filters = {
            'volume_spike_multiplier': 1.3,
            'momentum_threshold': 0.002,
            'correlation_stability': 0.15,
            'market_hours_only': True,
            'avoid_news_events': True
        }
        
        # Performance tracking
        self.daily_stats = {}
        self.reset_daily_stats()
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        today = datetime.now().date()
        self.daily_stats[today] = {
            'signals_generated': 0,
            'signals_filled': 0,
            'total_pnl_pct': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_hold_time': 0.0,
            'target_progress': 0.0  # Progress toward 14% daily target
        }
    
    async def generate_signals(self) -> List[HighFrequencySignal]:
        """Generate high-frequency scalping signals"""
        signals = []
        
        try:
            # Check if we've hit daily limits
            today = datetime.now().date()
            if today not in self.daily_stats:
                self.reset_daily_stats()
            
            daily_signals = self.daily_stats[today]['signals_generated']
            if daily_signals >= self.config['max_daily_signals']:
                logger.warning(f"Daily signal limit reached: {daily_signals}")
                return signals
            
            # Generate micro-timeframe signals
            for timeframe in ['1m', '3m', '5m']:
                micro_signals = await self.micro_engine.generate_scalping_signals(timeframe)
                
                for micro_signal in micro_signals:
                    hf_signal = await self._convert_to_hf_signal(micro_signal)
                    
                    if hf_signal and await self._validate_signal(hf_signal):
                        signals.append(hf_signal)
            
            # Sort by priority and confidence
            signals = self._prioritize_signals(signals)
            
            # Limit concurrent signals
            max_new_signals = max(0, self.config['max_concurrent_signals'] - len(self.active_signals))
            signals = signals[:max_new_signals]
            
            # Update statistics
            self.daily_stats[today]['signals_generated'] += len(signals)
            self.performance_stats['total_generated'] += len(signals)
            
            logger.info(f"Generated {len(signals)} high-frequency signals")
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
        
        return signals
    
    async def _convert_to_hf_signal(self, micro_signal: MicroTimeframeSignal) -> Optional[HighFrequencySignal]:
        """Convert micro-timeframe signal to high-frequency signal"""
        try:
            # Determine signal type based on characteristics
            signal_type = self._classify_signal_type(micro_signal)
            
            # Calculate priority
            priority = self._calculate_priority(micro_signal.confidence, micro_signal.momentum_score)
            
            # Enhance position sizing based on confidence and timeframe
            position_size = self._calculate_position_size(micro_signal)
            
            # Calculate liquidity score
            liquidity_score = await self._calculate_liquidity_score(micro_signal.symbol, micro_signal.timeframe)
            
            # Determine max slippage
            max_slippage = self._calculate_max_slippage(micro_signal.timeframe, liquidity_score)
            
            # Calculate expected move
            expected_move = abs(micro_signal.take_profit - micro_signal.entry_price) / micro_signal.entry_price
            
            hf_signal = HighFrequencySignal(
                id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                symbol=micro_signal.symbol,
                signal_type=signal_type,
                priority=priority,
                timeframe=micro_signal.timeframe,
                
                # Entry parameters
                entry_price=micro_signal.entry_price,
                stop_loss=micro_signal.stop_loss,
                take_profit=micro_signal.take_profit,
                position_size_pct=position_size,
                
                # Signal quality metrics
                confidence=micro_signal.confidence,
                correlation_strength=micro_signal.correlation_strength,
                volume_confirmation=micro_signal.volume_confirmation,
                momentum_score=micro_signal.momentum_score,
                liquidity_score=liquidity_score,
                
                # Execution parameters
                max_slippage_pct=max_slippage,
                max_hold_minutes=micro_signal.expected_duration_minutes,
                risk_reward_ratio=micro_signal.risk_reward_ratio,
                expected_move_pct=expected_move * 100,
                
                # Meta data
                source_engine="MicroTimeframeCorrelationEngine",
                reasoning=f"Correlation breakdown signal with {micro_signal.momentum_score:.1f} momentum score",
                supporting_indicators=[
                    f"correlation_strength_{micro_signal.correlation_strength:.2f}",
                    f"volume_confirmed_{micro_signal.volume_confirmation}",
                    f"timeframe_{micro_signal.timeframe}"
                ]
            )
            
            return hf_signal
            
        except Exception as e:
            logger.error(f"Error converting micro signal: {e}")
            return None
    
    def _classify_signal_type(self, micro_signal: MicroTimeframeSignal) -> ScalpingSignalType:
        """Classify the type of scalping signal"""
        if micro_signal.correlation_strength > 0.75:
            return ScalpingSignalType.MICRO_CORRELATION_BREAKDOWN
        elif micro_signal.volume_confirmation and micro_signal.momentum_score > 0.5:
            return ScalpingSignalType.VOLUME_MOMENTUM_SPIKE
        elif micro_signal.momentum_score > 0.3:
            return ScalpingSignalType.MOMENTUM_CONTINUATION
        else:
            return ScalpingSignalType.QUICK_MEAN_REVERSION
    
    def _calculate_priority(self, confidence: float, momentum_score: float) -> SignalPriority:
        """Calculate signal priority based on quality metrics"""
        combined_score = (confidence + momentum_score / 100) / 2
        
        if combined_score >= self.config['critical_threshold']:
            return SignalPriority.CRITICAL
        elif combined_score >= self.config['priority_boost_threshold']:
            return SignalPriority.HIGH
        elif combined_score >= 0.75:
            return SignalPriority.MEDIUM
        else:
            return SignalPriority.LOW
    
    def _calculate_position_size(self, micro_signal: MicroTimeframeSignal) -> float:
        """Calculate optimal position size based on signal characteristics"""
        base_size = 0.02  # 2% base position
        
        # Adjust based on timeframe
        tf_multiplier = {
            '1m': 0.7,   # Smaller positions for higher frequency
            '3m': 1.0,   # Base size
            '5m': 1.2    # Slightly larger for lower frequency
        }.get(micro_signal.timeframe, 1.0)
        
        # Adjust based on confidence
        confidence_multiplier = 0.5 + (micro_signal.confidence * 0.5)
        
        # Adjust based on risk-reward ratio
        rr_multiplier = min(1.5, micro_signal.risk_reward_ratio / 2.0)
        
        position_size = base_size * tf_multiplier * confidence_multiplier * rr_multiplier
        
        # Cap at maximum
        return min(0.035, position_size)  # Maximum 3.5% position
    
    async def _calculate_liquidity_score(self, symbol: str, timeframe: str) -> float:
        """Calculate liquidity score for the symbol"""
        # For now, return estimated scores based on symbol
        # In production, this would analyze actual order book depth
        
        liquidity_scores = {
            'ETHUSDT': 0.95,
            'BTCUSDT': 0.98,
            'SOLUSDT': 0.85,
            'LINKUSDT': 0.80
        }
        
        base_score = liquidity_scores.get(symbol, 0.70)
        
        # Adjust for timeframe (lower timeframes may have less liquidity)
        tf_adjustment = {
            '1m': 0.9,
            '3m': 0.95,
            '5m': 1.0
        }.get(timeframe, 1.0)
        
        return base_score * tf_adjustment
    
    def _calculate_max_slippage(self, timeframe: str, liquidity_score: float) -> float:
        """Calculate maximum acceptable slippage"""
        base_slippage = {
            '1m': 0.008,  # 0.8% for 1min trades
            '3m': 0.006,  # 0.6% for 3min trades
            '5m': 0.004   # 0.4% for 5min trades
        }.get(timeframe, 0.005)
        
        # Adjust based on liquidity
        liquidity_adjustment = 2.0 - liquidity_score  # Lower liquidity = higher slippage
        
        return base_slippage * liquidity_adjustment
    
    async def _validate_signal(self, signal: HighFrequencySignal) -> bool:
        """Validate signal quality and execution feasibility"""
        try:
            # Check minimum confidence
            if signal.confidence < self.config['min_confidence']:
                return False
            
            # Check minimum risk-reward ratio
            if signal.risk_reward_ratio < self.config['min_risk_reward']:
                return False
            
            # Check if symbol already has active signal
            active_symbols = [s.symbol for s in self.active_signals.values()]
            if signal.symbol in active_symbols and signal.priority != SignalPriority.CRITICAL:
                return False
            
            # Check market hours (if enabled)
            if self.signal_filters['market_hours_only']:
                current_hour = datetime.now().hour
                if current_hour < 6 or current_hour > 22:  # Avoid low liquidity hours
                    return False
            
            # Validate liquidity score
            if signal.liquidity_score < 0.6:
                return False
            
            # Check expected move reasonableness
            if signal.expected_move_pct > 3.0:  # Cap at 3% expected move
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False
    
    def _prioritize_signals(self, signals: List[HighFrequencySignal]) -> List[HighFrequencySignal]:
        """Sort and prioritize signals for execution"""
        
        def signal_score(signal):
            priority_scores = {
                SignalPriority.CRITICAL: 1000,
                SignalPriority.HIGH: 100,
                SignalPriority.MEDIUM: 10,
                SignalPriority.LOW: 1
            }
            
            base_score = priority_scores[signal.priority]
            confidence_score = signal.confidence * 10
            rr_score = signal.risk_reward_ratio * 5
            liquidity_score = signal.liquidity_score * 5
            
            return base_score + confidence_score + rr_score + liquidity_score
        
        return sorted(signals, key=signal_score, reverse=True)
    
    async def track_signal_performance(self, signal_id: str, fill_price: float = None, 
                                     exit_price: float = None, status: str = None):
        """Track performance of executed signals"""
        try:
            if signal_id not in self.active_signals:
                return
            
            signal = self.active_signals[signal_id]
            
            if fill_price:
                signal.fill_price = fill_price
                signal.status = "active"
                
            if exit_price:
                signal.exit_price = exit_price
                signal.status = "closed"
                
                # Calculate PnL
                if signal.signal_type.value in ["long", "momentum_continuation"]:
                    signal.pnl_pct = (exit_price - signal.fill_price) / signal.fill_price * 100
                else:
                    signal.pnl_pct = (signal.fill_price - exit_price) / signal.fill_price * 100
                
                # Update statistics
                await self._update_performance_stats(signal)
                
                # Move to history
                self.signal_history.append(signal)
                del self.active_signals[signal_id]
            
            if status:
                signal.status = status
                
        except Exception as e:
            logger.error(f"Error tracking signal performance: {e}")
    
    async def _update_performance_stats(self, signal: HighFrequencySignal):
        """Update performance statistics"""
        try:
            today = datetime.now().date()
            if today not in self.daily_stats:
                self.reset_daily_stats()
            
            # Update daily stats
            self.daily_stats[today]['signals_filled'] += 1
            self.daily_stats[today]['total_pnl_pct'] += signal.pnl_pct or 0.0
            
            if signal.pnl_pct and signal.pnl_pct > 0:
                self.daily_stats[today]['winning_trades'] += 1
            else:
                self.daily_stats[today]['losing_trades'] += 1
            
            # Calculate hold time
            if signal.fill_price and signal.exit_price:
                hold_time = (datetime.now() - signal.timestamp).total_seconds() / 60
                self.daily_stats[today]['avg_hold_time'] = (
                    self.daily_stats[today]['avg_hold_time'] + hold_time
                ) / 2
            
            # Update overall stats
            self.performance_stats['total_filled'] += 1
            
            filled_signals = [s for s in self.signal_history if s.pnl_pct is not None]
            if filled_signals:
                winning_trades = len([s for s in filled_signals if s.pnl_pct > 0])
                self.performance_stats['win_rate'] = winning_trades / len(filled_signals)
                self.performance_stats['avg_pnl_pct'] = np.mean([s.pnl_pct for s in filled_signals])
            
            # Update daily target progress
            daily_pnl = self.daily_stats[today]['total_pnl_pct']
            self.daily_stats[today]['target_progress'] = min(100, (daily_pnl / 14.0) * 100)
            
        except Exception as e:
            logger.error(f"Error updating performance stats: {e}")
    
    def get_daily_progress(self) -> Dict:
        """Get progress toward daily 14% target"""
        today = datetime.now().date()
        if today not in self.daily_stats:
            self.reset_daily_stats()
        
        stats = self.daily_stats[today].copy()
        
        # Calculate additional metrics
        if stats['signals_filled'] > 0:
            stats['win_rate'] = stats['winning_trades'] / stats['signals_filled'] * 100
            stats['avg_pnl_per_trade'] = stats['total_pnl_pct'] / stats['signals_filled']
        else:
            stats['win_rate'] = 0
            stats['avg_pnl_per_trade'] = 0
        
        stats['remaining_target'] = max(0, 14.0 - stats['total_pnl_pct'])
        
        return stats
    
    def get_active_signals(self) -> List[HighFrequencySignal]:
        """Get currently active signals"""
        return list(self.active_signals.values())
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        return {
            'overall_stats': self.performance_stats,
            'daily_progress': self.get_daily_progress(),
            'active_signals_count': len(self.active_signals),
            'config': self.config,
            'recent_signals': list(self.signal_history)[-10:] if self.signal_history else []
        }

# Utility functions
def create_hf_signal_generator(exchange) -> HighFrequencySignalGenerator:
    """Factory function to create high-frequency signal generator"""
    micro_engine = MicroTimeframeCorrelationEngine(exchange)
    return HighFrequencySignalGenerator(micro_engine)

async def test_hf_signal_generation(exchange):
    """Test function for high-frequency signal generation"""
    generator = create_hf_signal_generator(exchange)
    
    # Initialize micro engine
    await generator.micro_engine.initialize_buffers()
    
    # Generate test signals
    signals = await generator.generate_signals()
    
    print(f"Generated {len(signals)} high-frequency signals:")
    for signal in signals:
        print(f"  {signal.id}: {signal.symbol} {signal.signal_type.value} "
              f"@ {signal.entry_price:.4f} (conf: {signal.confidence:.2f}, "
              f"priority: {signal.priority.value})")

if __name__ == "__main__":
    import ccxt.async_support as ccxt
    
    async def main():
        exchange = ccxt.binance()
        await test_hf_signal_generation(exchange)
        await exchange.close()
    
    asyncio.run(main())