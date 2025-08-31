"""Advanced trading signal generation based on correlation analysis"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from .config.settings import config

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Signal types based on correlation analysis"""
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    MEAN_REVERSION = "mean_reversion" 
    MOMENTUM_CONTINUATION = "momentum_continuation"
    REGIME_CHANGE = "regime_change"

class SignalAction(Enum):
    """Trading actions"""
    LONG = "long"
    SHORT = "short"
    CLOSE = "close"

@dataclass
class TradingSignal:
    """Structured trading signal with comprehensive metadata"""
    id: str
    timestamp: datetime
    symbol: str
    action: SignalAction
    signal_type: SignalType
    entry_price: float
    confidence: float
    correlation_data: Dict
    stop_loss: float
    take_profit: float
    position_size: float
    reasoning: str
    statistical_significance: float
    market_regime: str
    risk_reward_ratio: float
    expected_duration: str
    supporting_signals: List[str]

class SignalGenerator:
    def __init__(self, 
                 confidence_threshold: float = 0.60,  # OPTIMIZED FOR HIGH-FREQUENCY SCALPING
                 min_statistical_significance: float = 0.85):  # ADJUSTED FOR MORE SIGNALS
        """Initialize advanced SignalGenerator optimized for high-frequency scalping"""
        self.confidence_threshold = confidence_threshold
        self.min_statistical_significance = min_statistical_significance
        self.active_signals = {}
        self.signal_history = []
        self.signal_count = 0
        
        # Signal filtering parameters - HIGH-FREQUENCY SCALPING OPTIMIZED
        self.min_correlation_change = 0.08  # Much lower threshold for frequent signals
        self.regime_change_threshold = 0.15  # More sensitive for scalping
        self.false_positive_filters = True
        # High-frequency scalping focus
        self.primary_symbols = ['ETHUSDT']  # Primary scalping symbol
        self.signal_generation_frequency = 30  # Generate signals every 30 seconds
        self.last_signal_time = None
        self.min_signal_interval = 15  # Minimum 15 seconds between signals
        
        logger.info("SignalGenerator initialized for high-frequency scalping with enhanced signal detection")
        
    def generate(self, correlation_results: Dict, market_data: Dict) -> List[Dict]:
        """Generate advanced trading signals from correlation analysis"""
        signals = []
        
        try:
            if not correlation_results or not market_data:
                return signals
            
            # Extract correlation data
            opportunities = correlation_results.get('opportunities', [])
            breakdowns = correlation_results.get('breakdowns', [])
            regime = correlation_results.get('regime', 'neutral')
            statistics = correlation_results.get('statistics', {})
            
            # Generate opportunity-based signals
            for opportunity in opportunities:
                signal = self._analyze_correlation_opportunity(opportunity, market_data, regime)
                if signal:
                    signals.append(signal)
            
            # Generate breakdown-based signals  
            for breakdown in breakdowns:
                signal = self._analyze_correlation_breakdown(breakdown, market_data, regime)
                if signal:
                    signals.append(signal)
            
            # Generate regime change signals
            if self._is_regime_change(regime):
                regime_signals = self._generate_regime_change_signals(correlation_results, market_data)
                signals.extend(regime_signals)
            
            # Apply false positive filtering
            if self.false_positive_filters:
                signals = self._filter_false_positives(signals, correlation_results)
            
            # Log generated signals
            for signal in signals:
                self.signal_count += 1
                logger.info(f"SIGNAL #{self.signal_count}: {signal['action']} {signal['symbol']} "
                          f"(confidence={signal['confidence']:.3f}, type={signal['signal_type']})")
            
            # Store signal history
            self.signal_history.extend(signals)
            if len(self.signal_history) > 1000:  # Keep last 1000 signals
                self.signal_history = self.signal_history[-1000:]
                
        except Exception as e:
            logger.error(f"Error generating signals: {e}", exc_info=True)
            
        return signals
    
    def _analyze_correlation_opportunity(self, opportunity: Dict, market_data: Dict, regime: str) -> Optional[Dict]:
        """Analyze correlation opportunity and generate high-confidence signal"""
        try:
            symbols = opportunity.get('symbols', [])
            correlation = opportunity.get('correlation', 0)
            p_value = opportunity.get('p_value', 1.0)
            confidence = opportunity.get('confidence', 0)
            
            if len(symbols) < 2 or confidence < self.confidence_threshold:
                return None
            
            # PRIORITIZE ETHUSDT FOR HIGH-FREQUENCY SCALPING
            if 'ETHUSDT' in symbols:
                symbol = 'ETHUSDT'  # Always prefer ETHUSDT for scalping
            else:
                symbol = symbols[0]
            
            # Symbol already selected above with ETHUSDT priority
            
            if symbol not in market_data:
                return None
            
            price_data = market_data[symbol]
            entry_price = price_data.get('last')
            
            if not entry_price:
                return None
            
            # Determine signal direction based on correlation type and market conditions
            signal_type = SignalType.CORRELATION_BREAKDOWN if correlation < 0 else SignalType.MEAN_REVERSION
            action = self._determine_signal_direction(opportunity, market_data, regime)
            
            # Calculate statistical significance
            statistical_significance = 1 - p_value
            
            if statistical_significance < (self.min_statistical_significance / 100):
                return None
            
            # Calculate position sizing - SCALPING OPTIMIZED
            position_size = self._calculate_position_size(confidence, symbol, market_data)
            # Scalping-specific position sizing for ETHUSDT
            if symbol == 'ETHUSDT':
                position_size = min(position_size * 1.1, 0.20)  # Cap at 20% for scalping
            
            # Set stop loss and take profit based on statistical analysis
            stop_loss, take_profit = self._calculate_risk_levels(
                entry_price, action, confidence, symbol, market_data
            )
            
            # Build reasoning
            reasoning = self._build_signal_reasoning(opportunity, regime, statistical_significance)
            
            # Calculate risk/reward ratio
            risk_reward_ratio = self._calculate_risk_reward_ratio(
                entry_price, stop_loss, take_profit, action
            )
            
            signal_id = f"COR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(symbols)}"
            
            return {
                'id': signal_id,
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action.value,
                'signal_type': signal_type.value,
                'entry_price': float(entry_price),
                'confidence': float(confidence),
                'correlation_data': {
                    'correlation': float(correlation),
                    'symbols': symbols,
                    'p_value': float(p_value)
                },
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'position_size': float(position_size),
                'reasoning': reasoning,
                'statistical_significance': float(statistical_significance),
                'market_regime': regime,
                'risk_reward_ratio': float(risk_reward_ratio),
                'expected_duration': self._estimate_signal_duration(signal_type, regime),
                'supporting_signals': self._get_supporting_signals(opportunity, market_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlation opportunity: {e}")
            return None
    
    def _analyze_correlation_breakdown(self, breakdown: Dict, market_data: Dict, regime: str) -> Optional[Dict]:
        """Analyze correlation breakdown for trading signal"""
        try:
            pair = breakdown.get('pair', '').split('-')
            if len(pair) != 2:
                return None
            
            abs_change = breakdown.get('abs_change', 0)
            breakdown_type = breakdown.get('type', 'unknown')
            severity = breakdown.get('severity', 'low')
            
            if abs_change < self.min_correlation_change:
                return None
            
            # Select symbol with better liquidity/volume
            symbol = self._select_optimal_symbol(pair, market_data)
            
            if symbol not in market_data:
                return None
            
            price_data = market_data[symbol]
            entry_price = price_data.get('last')
            
            if not entry_price:
                return None
            
            # Determine action based on breakdown type and market regime
            if breakdown_type == 'weakening':
                action = SignalAction.LONG if regime == 'low_correlation' else SignalAction.SHORT
            else:  # strengthening
                action = SignalAction.SHORT if regime == 'high_correlation' else SignalAction.LONG
            
            # Calculate confidence based on breakdown magnitude and regime consistency
            confidence = min(abs_change * 2, 0.95)  # Scale breakdown change to confidence
            if regime in ['high_correlation', 'low_correlation']:
                confidence *= 1.2  # Boost confidence in clear regime
            confidence = min(confidence, 0.95)
            
            if confidence < self.confidence_threshold:
                return None
            
            position_size = self._calculate_position_size(confidence, symbol, market_data)
            stop_loss, take_profit = self._calculate_risk_levels(
                entry_price, action, confidence, symbol, market_data
            )
            
            reasoning = f"Correlation {breakdown_type} detected in {pair[0]}-{pair[1]} pair. " \
                       f"Change: {abs_change:.3f}, Severity: {severity}, Regime: {regime}"
            
            risk_reward_ratio = self._calculate_risk_reward_ratio(
                entry_price, stop_loss, take_profit, action
            )
            
            signal_id = f"BRK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{severity}"
            
            return {
                'id': signal_id,
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action.value,
                'signal_type': SignalType.CORRELATION_BREAKDOWN.value,
                'entry_price': float(entry_price),
                'confidence': float(confidence),
                'correlation_data': {
                    'pair': breakdown.get('pair', ''),
                    'previous_corr': breakdown.get('previous_corr', 0),
                    'current_corr': breakdown.get('current_corr', 0),
                    'change': breakdown.get('change', 0),
                    'abs_change': abs_change,
                    'type': breakdown_type,
                    'severity': severity
                },
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'position_size': float(position_size),
                'reasoning': reasoning,
                'statistical_significance': 0.90,  # Breakdown signals have inherent significance
                'market_regime': regime,
                'risk_reward_ratio': float(risk_reward_ratio),
                'expected_duration': self._estimate_signal_duration(SignalType.CORRELATION_BREAKDOWN, regime),
                'supporting_signals': []
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlation breakdown: {e}")
            return None
    
    def _determine_signal_direction(self, opportunity: Dict, market_data: Dict, regime: str) -> SignalAction:
        """Determine signal direction using multiple factors"""
        correlation = opportunity.get('correlation', 0)
        confidence = opportunity.get('confidence', 0)
        
        # Mean reversion logic for high correlation pairs
        if abs(correlation) > 0.8:
            # In high correlation regime, look for mean reversion opportunities
            if regime == 'high_correlation':
                return SignalAction.LONG if confidence > 0.8 else SignalAction.SHORT
        
        # Momentum logic for moderate correlations
        return SignalAction.LONG if correlation > 0 else SignalAction.SHORT
    
    def _calculate_position_size(self, confidence: float, symbol: str, market_data: Dict) -> float:
        """Calculate position size optimized for high-frequency scalping"""
        base_position_size = config.RISK_PER_TRADE  # 0.15 for scalping strategy
        
        # ETHUSDT gets optimized sizing for scalping
        if symbol == 'ETHUSDT':
            confidence_multiplier = min(confidence * 1.2, 1.4)  # Moderate multiplier for scalping
        else:
            confidence_multiplier = min(confidence * 1.0, 1.2)
        
        # Get volume data for liquidity adjustment (more conservative for scalping)
        volume_data = market_data.get(symbol, {}).get('volume', 1000000)
        liquidity_factor = min(volume_data / 1000000, 1.5)  # More conservative cap
        
        position_size = base_position_size * confidence_multiplier * liquidity_factor
        # Scalping position limits
        max_position = 0.20 if symbol == 'ETHUSDT' else 0.10
        return min(position_size, max_position)
    
    def _calculate_risk_levels(self, entry_price: float, action: SignalAction, 
                              confidence: float, symbol: str, market_data: Dict) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels optimized for high-frequency scalping"""
        # SCALPING-OPTIMIZED RISK LEVELS
        if symbol == 'ETHUSDT':
            base_stop_loss_pct = 0.012  # 1.2% stop loss for scalping
            base_take_profit_ratio = 1.5   # 1.5:1 ratio (1.8% take profit)
        else:
            base_stop_loss_pct = config.STOP_LOSS_PERCENT
            base_take_profit_ratio = config.TAKE_PROFIT_RATIO
        
        # Scalping-specific adjustments based on confidence
        stop_loss_pct = base_stop_loss_pct * (1.1 - confidence * 0.15)  # Slight tightening
        take_profit_ratio = base_take_profit_ratio * (1 + confidence * 0.2)   # Moderate improvement
        
        if action == SignalAction.LONG:
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + stop_loss_pct * take_profit_ratio)
        else:  # SHORT
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - stop_loss_pct * take_profit_ratio)
        
        return stop_loss, take_profit
    
    def _calculate_risk_reward_ratio(self, entry_price: float, stop_loss: float, 
                                   take_profit: float, action: SignalAction) -> float:
        """Calculate risk/reward ratio"""
        try:
            if action == SignalAction.LONG:
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:  # SHORT
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
            
            return abs(reward / risk) if risk != 0 else 0.0
        except:
            return 1.0
    
    def _build_signal_reasoning(self, opportunity: Dict, regime: str, significance: float) -> str:
        """Build human-readable reasoning for the signal"""
        symbols = opportunity.get('symbols', [])
        correlation = opportunity.get('correlation', 0)
        confidence = opportunity.get('confidence', 0)
        
        reasoning = f"High correlation ({correlation:.3f}) detected between {'-'.join(symbols)} "
        reasoning += f"with {confidence:.1%} confidence and {significance:.1%} statistical significance. "
        reasoning += f"Market regime: {regime}. "
        
        if abs(correlation) > 0.8:
            reasoning += "Strong correlation suggests mean reversion opportunity."
        elif regime == 'high_correlation':
            reasoning += "High correlation regime supports directional trade."
        else:
            reasoning += "Mixed regime requires careful position sizing."
        
        return reasoning
    
    def _estimate_signal_duration(self, signal_type: SignalType, regime: str) -> str:
        """Estimate expected signal duration"""
        if signal_type == SignalType.CORRELATION_BREAKDOWN:
            return "short-term" if regime == 'mixed_correlation' else "medium-term"
        elif signal_type == SignalType.MEAN_REVERSION:
            return "short-term"
        elif signal_type == SignalType.MOMENTUM_CONTINUATION:
            return "medium-term"
        elif signal_type == SignalType.REGIME_CHANGE:
            return "long-term"
        return "unknown"
    
    def _get_supporting_signals(self, opportunity: Dict, market_data: Dict) -> List[str]:
        """Identify supporting signals/confirmations"""
        supporting = []
        
        confidence = opportunity.get('confidence', 0)
        if confidence > 0.85:
            supporting.append("high_confidence")
        
        p_value = opportunity.get('p_value', 1.0)
        if p_value < 0.01:
            supporting.append("highly_significant")
        elif p_value < 0.05:
            supporting.append("statistically_significant")
        
        symbols = opportunity.get('symbols', [])
        if len(symbols) == 2:
            supporting.append("pair_trade")
        elif len(symbols) > 2:
            supporting.append("multi_symbol_confirmation")
        
        return supporting
    
    def _select_optimal_symbol(self, symbols: List[str], market_data: Dict) -> str:
        """Select the best symbol for trading based on volume/liquidity"""
        best_symbol = symbols[0]
        best_volume = 0
        
        for symbol in symbols:
            if symbol in market_data:
                volume = market_data[symbol].get('volume', 0)
                if volume > best_volume:
                    best_volume = volume
                    best_symbol = symbol
        
        return best_symbol
    
    def _is_regime_change(self, regime: str) -> bool:
        """Detect if we're in a regime change period"""
        # This could be enhanced with historical regime tracking
        return regime == 'mixed_correlation'
    
    def _generate_regime_change_signals(self, correlation_results: Dict, market_data: Dict) -> List[Dict]:
        """Generate signals based on market regime changes"""
        signals = []
        # Placeholder for regime change signal logic
        # Could analyze transition from high->low correlation or vice versa
        return signals
    
    def _filter_false_positives(self, signals: List[Dict], correlation_results: Dict) -> List[Dict]:
        """Apply false positive filtering to signals"""
        if not signals:
            return signals
        
        filtered_signals = []
        
        for signal in signals:
            # Filter by minimum confidence threshold
            if signal['confidence'] < self.confidence_threshold:
                continue
            
            # Filter by minimum statistical significance
            if signal['statistical_significance'] < (self.min_statistical_significance / 100):
                continue
            
            # Filter by minimum risk/reward ratio - SCALPING OPTIMIZED
            if signal['risk_reward_ratio'] < 1.2:  # Lower threshold for scalping frequency
                continue
            
            # Check for signal conflicts (opposite signals on same symbol)
            has_conflict = False
            for existing in filtered_signals:
                if (existing['symbol'] == signal['symbol'] and 
                    existing['action'] != signal['action']):
                    # Keep higher confidence signal
                    if signal['confidence'] > existing['confidence']:
                        filtered_signals.remove(existing)
                    else:
                        has_conflict = True
                    break
            
            if not has_conflict:
                filtered_signals.append(signal)
        
        return filtered_signals
    
    def can_generate_signal(self) -> bool:
        """Check if enough time has passed since last signal generation"""
        if self.last_signal_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.min_signal_interval
    
    def generate_scalping_signals(self, market_data: Dict, correlation_results: Dict) -> List[Dict]:
        """Generate high-frequency scalping signals optimized for 3-minute timeframe"""
        signals = []
        
        try:
            # Check if we can generate signals
            if not self.can_generate_signal():
                return signals
            
            # Focus on ETHUSDT for scalping
            symbol = 'ETHUSDT'
            if symbol not in market_data:
                return signals
            
            # Get current price and volume data
            price_data = market_data[symbol]
            current_price = price_data.get('last')
            volume = price_data.get('volume', 0)
            
            if not current_price or volume < 1000000:  # Minimum volume requirement
                return signals
            
            # Check for micro-movements and correlation deviations
            correlation_data = correlation_results.get('statistics', {})
            current_correlation = correlation_data.get('mean_correlation', 0)
            correlation_std = correlation_data.get('correlation_std', 0)
            
            # Generate scalping signal based on tight thresholds
            if correlation_std > 0.05:  # Volatility threshold for scalping
                confidence = min(correlation_std * 10, 0.95)  # Scale volatility to confidence
                
                if confidence > self.confidence_threshold:
                    # Determine signal direction based on price momentum
                    price_change = price_data.get('change_percent', 0)
                    action = SignalAction.LONG if price_change > 0 else SignalAction.SHORT
                    
                    # Calculate scalping-specific risk levels
                    stop_loss_pct = 0.012  # 1.2%
                    take_profit_pct = 0.018  # 1.8%
                    
                    if action == SignalAction.LONG:
                        stop_loss = current_price * (1 - stop_loss_pct)
                        take_profit = current_price * (1 + take_profit_pct)
                    else:
                        stop_loss = current_price * (1 + stop_loss_pct)
                        take_profit = current_price * (1 - take_profit_pct)
                    
                    # Calculate position size for scalping (smaller positions)
                    position_size = config.RISK_PER_TRADE * 0.8  # Reduced size for scalping
                    
                    signal_id = f"SCALP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    signal = {
                        'id': signal_id,
                        'timestamp': datetime.now().isoformat(),
                        'symbol': symbol,
                        'action': action.value,
                        'signal_type': 'scalping_opportunity',
                        'entry_price': float(current_price),
                        'confidence': float(confidence),
                        'correlation_data': {
                            'current_correlation': float(current_correlation),
                            'volatility': float(correlation_std),
                            'volume': float(volume)
                        },
                        'stop_loss': float(stop_loss),
                        'take_profit': float(take_profit),
                        'position_size': float(position_size),
                        'reasoning': f"Scalping opportunity detected: {correlation_std:.3f} volatility, "
                                   f"{confidence:.1%} confidence, volume: {volume:,.0f}",
                        'statistical_significance': 0.90,
                        'market_regime': 'scalping',
                        'risk_reward_ratio': 1.5,
                        'expected_duration': 'ultra-short-term',
                        'supporting_signals': ['high_volume', 'volatility_spike']
                    }
                    
                    signals.append(signal)
                    self.last_signal_time = datetime.now()
                    
                    logger.info(f"SCALPING SIGNAL: {action.value} {symbol} @ {current_price} "
                              f"(confidence={confidence:.3f}, vol={correlation_std:.3f})")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating scalping signals: {e}", exc_info=True)
            return signals
    
    def get_signal_performance_stats(self) -> Dict:
        """Get performance statistics of generated signals"""
        if not self.signal_history:
            return {}
        
        total_signals = len(self.signal_history)
        signal_types = {}
        avg_confidence = 0
        
        for signal in self.signal_history:
            signal_type = signal.get('signal_type', 'unknown')
            signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            avg_confidence += signal.get('confidence', 0)
        
        return {
            'total_signals': total_signals,
            'signal_types': signal_types,
            'average_confidence': avg_confidence / total_signals,
            'confidence_threshold': self.confidence_threshold,
            'min_statistical_significance': self.min_statistical_significance,
            'scalping_mode': True,
            'min_signal_interval': self.min_signal_interval
        }
