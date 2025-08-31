#!/usr/bin/env python3
"""
Volatility-Adjusted Signal Generator
Generates optimized trading signals based on volatility tiers and correlation analysis
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from .universal_correlation_engine import (
    UniversalCorrelationEngine, 
    CorrelationSignal, 
    CorrelationMatrix,
    VolatilityTier,
    CorrelationType
)

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    WEAK = "weak"
    MODERATE = "moderate" 
    STRONG = "strong"
    ULTRA_STRONG = "ultra_strong"

class SignalDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"

@dataclass
class TradingSignal:
    symbol: str
    direction: SignalDirection
    strength: SignalStrength
    confidence: float
    volatility_tier: VolatilityTier
    correlation_basis: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float]
    position_size_pct: float
    timeframe: str
    max_hold_time_minutes: int
    supporting_indicators: List[str]
    risk_reward_ratio: float
    correlation_signals: List[CorrelationSignal]
    timestamp: datetime

class VolatilitySignalGenerator:
    """
    Advanced signal generator optimized for high-volatility trading
    with correlation-based enhancement
    """
    
    def __init__(self):
        self.correlation_engine = UniversalCorrelationEngine()
        
        # Volatility-specific parameters
        self.volatility_params = {
            VolatilityTier.ULTRA_HIGH: {
                'entry_threshold': 0.12,
                'confidence_threshold': 0.75,
                'stop_loss_pct': 0.015,  # 1.5%
                'take_profit_1_pct': 0.04,  # 4%
                'take_profit_2_pct': 0.08,  # 8%
                'max_position_pct': 0.02,  # 2% of account
                'max_hold_minutes': 15,
                'timeframes': ['1m', '3m', '5m'],
                'required_confirmations': 3
            },
            VolatilityTier.HIGH: {
                'entry_threshold': 0.08,
                'confidence_threshold': 0.65,
                'stop_loss_pct': 0.02,  # 2%
                'take_profit_1_pct': 0.05,  # 5%
                'take_profit_2_pct': 0.10,  # 10%
                'max_position_pct': 0.03,  # 3% of account
                'max_hold_minutes': 60,
                'timeframes': ['5m', '15m', '30m'],
                'required_confirmations': 2
            },
            VolatilityTier.MEDIUM: {
                'entry_threshold': 0.06,
                'confidence_threshold': 0.55,
                'stop_loss_pct': 0.025,  # 2.5%
                'take_profit_1_pct': 0.06,  # 6%
                'take_profit_2_pct': 0.12,  # 12%
                'max_position_pct': 0.04,  # 4% of account
                'max_hold_minutes': 240,
                'timeframes': ['15m', '1h', '4h'],
                'required_confirmations': 2
            },
            VolatilityTier.STANDARD: {
                'entry_threshold': 0.04,
                'confidence_threshold': 0.50,
                'stop_loss_pct': 0.03,  # 3%
                'take_profit_1_pct': 0.07,  # 7%
                'take_profit_2_pct': 0.15,  # 15%
                'max_position_pct': 0.05,  # 5% of account
                'max_hold_minutes': 480,
                'timeframes': ['1h', '4h', '1d'],
                'required_confirmations': 1
            }
        }
        
        # Technical indicators for signal confirmation
        self.technical_indicators = {
            'momentum': ['RSI', 'MACD', 'Stochastic'],
            'trend': ['EMA_cross', 'Bollinger_bands', 'ADX'],
            'volume': ['Volume_surge', 'OBV', 'VWAP'],
            'volatility': ['ATR', 'Bollinger_width', 'Volatility_ratio']
        }
        
        self.signal_cache = []
        self.last_signal_time = {}
        
    async def generate_volatility_signals(
        self, 
        market_data: Dict, 
        account_balance: float = 10000
    ) -> List[TradingSignal]:
        """
        Generate volatility-adjusted trading signals with correlation enhancement
        """
        try:
            signals = []
            
            # Build correlation matrix
            correlation_matrix = await self.correlation_engine.build_correlation_matrix(market_data)
            
            # Generate correlation-based signals
            correlation_signals = await self.correlation_engine.generate_enhanced_signals(correlation_matrix)
            
            # Process each correlation signal into trading signals
            for corr_signal in correlation_signals:
                trading_signals = await self._process_correlation_signal(
                    corr_signal, market_data, account_balance
                )
                signals.extend(trading_signals)
            
            # Add momentum-based signals for high-volatility pairs
            momentum_signals = await self._generate_momentum_signals(
                market_data, correlation_matrix, account_balance
            )
            signals.extend(momentum_signals)
            
            # Filter and rank signals
            filtered_signals = await self._filter_and_rank_signals(signals, market_data)
            
            logger.info(f"Generated {len(filtered_signals)} volatility-adjusted signals")
            
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Error generating volatility signals: {e}")
            return []
    
    async def _process_correlation_signal(
        self, 
        corr_signal: CorrelationSignal, 
        market_data: Dict, 
        account_balance: float
    ) -> List[TradingSignal]:
        """Process a correlation signal into trading signals"""
        
        signals = []
        
        try:
            primary_pair = corr_signal.primary_pair
            primary_data = market_data.get(primary_pair)
            
            if not primary_data:
                return signals
            
            # Get volatility parameters
            tier = corr_signal.volatility_tier
            params = self.volatility_params[tier]
            
            # Check signal strength
            if corr_signal.confidence_score < params['confidence_threshold']:
                return signals
            
            # Determine direction based on correlation type and recent price action
            direction = await self._determine_signal_direction(
                corr_signal, market_data
            )
            
            if direction == SignalDirection.NEUTRAL:
                return signals
            
            # Calculate entry price and levels
            current_price = float(primary_data.get('last', 0))
            if current_price <= 0:
                return signals
            
            # Calculate stop loss and take profit levels
            stop_loss_pct = params['stop_loss_pct']
            tp1_pct = params['take_profit_1_pct']
            tp2_pct = params['take_profit_2_pct']
            
            if direction == SignalDirection.LONG:
                stop_loss = current_price * (1 - stop_loss_pct)
                take_profit_1 = current_price * (1 + tp1_pct)
                take_profit_2 = current_price * (1 + tp2_pct)
            else:  # SHORT
                stop_loss = current_price * (1 + stop_loss_pct)
                take_profit_1 = current_price * (1 - tp1_pct)
                take_profit_2 = current_price * (1 - tp2_pct)
            
            # Calculate position size
            position_size_pct = self._calculate_position_size(
                tier, corr_signal.confidence_score, account_balance, current_price, stop_loss
            )
            
            # Determine signal strength
            signal_strength = self._determine_signal_strength(
                corr_signal.confidence_score, tier
            )
            
            # Calculate risk-reward ratio
            risk = abs(current_price - stop_loss) / current_price
            reward = abs(take_profit_1 - current_price) / current_price
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Get supporting indicators
            supporting_indicators = await self._get_supporting_indicators(
                primary_pair, market_data, direction
            )
            
            # Create trading signal
            trading_signal = TradingSignal(
                symbol=primary_pair,
                direction=direction,
                strength=signal_strength,
                confidence=corr_signal.confidence_score,
                volatility_tier=tier,
                correlation_basis=f"{corr_signal.signal_type.value} with {corr_signal.reference_pair}",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                position_size_pct=position_size_pct,
                timeframe=corr_signal.timeframe,
                max_hold_time_minutes=params['max_hold_minutes'],
                supporting_indicators=supporting_indicators,
                risk_reward_ratio=risk_reward_ratio,
                correlation_signals=[corr_signal],
                timestamp=datetime.now()
            )
            
            signals.append(trading_signal)
            
        except Exception as e:
            logger.error(f"Error processing correlation signal: {e}")
        
        return signals
    
    async def _determine_signal_direction(
        self, 
        corr_signal: CorrelationSignal, 
        market_data: Dict
    ) -> SignalDirection:
        """Determine trading direction based on correlation signal"""
        
        try:
            primary_data = market_data.get(corr_signal.primary_pair, {})
            reference_data = market_data.get(corr_signal.reference_pair, {})
            
            if not primary_data or not reference_data:
                return SignalDirection.NEUTRAL
            
            primary_change = float(primary_data.get('change_percent', 0))
            reference_change = float(reference_data.get('change_percent', 0))
            
            if corr_signal.signal_type == CorrelationType.POSITIVE:
                # For positive correlation, trade in direction of reference pair
                if corr_signal.expected_direction == 'convergence':
                    # Primary should catch up to reference
                    if reference_change > primary_change:
                        return SignalDirection.LONG  # Primary should go up
                    elif reference_change < primary_change:
                        return SignalDirection.SHORT  # Primary should go down
            
            elif corr_signal.signal_type == CorrelationType.NEGATIVE:
                # For negative correlation, trade opposite to reference
                if corr_signal.expected_direction == 'divergence_restoration':
                    if reference_change > 0:
                        return SignalDirection.SHORT  # Primary should go opposite
                    elif reference_change < 0:
                        return SignalDirection.LONG  # Primary should go opposite
            
            return SignalDirection.NEUTRAL
            
        except Exception as e:
            logger.error(f"Error determining signal direction: {e}")
            return SignalDirection.NEUTRAL
    
    def _calculate_position_size(
        self, 
        tier: VolatilityTier, 
        confidence: float, 
        account_balance: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate optimal position size based on volatility and risk"""
        
        try:
            params = self.volatility_params[tier]
            base_size = params['max_position_pct']
            
            # Adjust for confidence
            confidence_multiplier = min(confidence * 1.5, 1.0)
            
            # Adjust for risk (distance to stop loss)
            risk_distance = abs(entry_price - stop_loss) / entry_price
            risk_multiplier = max(0.5, 1.0 - (risk_distance * 10))  # Reduce size for wider stops
            
            # Calculate final position size
            position_size_pct = base_size * confidence_multiplier * risk_multiplier
            
            # Ensure minimum and maximum bounds
            position_size_pct = max(0.005, min(position_size_pct, params['max_position_pct']))
            
            return position_size_pct
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01  # Default 1%
    
    def _determine_signal_strength(self, confidence: float, tier: VolatilityTier) -> SignalStrength:
        """Determine signal strength based on confidence and volatility tier"""
        
        # Adjust thresholds based on volatility tier
        if tier == VolatilityTier.ULTRA_HIGH:
            if confidence >= 0.90:
                return SignalStrength.ULTRA_STRONG
            elif confidence >= 0.80:
                return SignalStrength.STRONG
            elif confidence >= 0.70:
                return SignalStrength.MODERATE
            else:
                return SignalStrength.WEAK
        
        elif tier == VolatilityTier.HIGH:
            if confidence >= 0.85:
                return SignalStrength.ULTRA_STRONG
            elif confidence >= 0.75:
                return SignalStrength.STRONG
            elif confidence >= 0.65:
                return SignalStrength.MODERATE
            else:
                return SignalStrength.WEAK
        
        else:  # MEDIUM or STANDARD
            if confidence >= 0.80:
                return SignalStrength.ULTRA_STRONG
            elif confidence >= 0.70:
                return SignalStrength.STRONG
            elif confidence >= 0.60:
                return SignalStrength.MODERATE
            else:
                return SignalStrength.WEAK
    
    async def _get_supporting_indicators(
        self, 
        symbol: str, 
        market_data: Dict, 
        direction: SignalDirection
    ) -> List[str]:
        """Get supporting technical indicators for the signal"""
        
        supporting = []
        
        try:
            pair_data = market_data.get(symbol, {})
            
            # Volume analysis
            current_volume = float(pair_data.get('volume', 0))
            if current_volume > 0:
                # Simplified volume analysis - would need historical data for proper analysis
                supporting.append('Volume_confirmation')
            
            # Price momentum
            price_change = float(pair_data.get('change_percent', 0))
            if direction == SignalDirection.LONG and price_change > 0:
                supporting.append('Momentum_alignment')
            elif direction == SignalDirection.SHORT and price_change < 0:
                supporting.append('Momentum_alignment')
            
            # Volatility check
            if 'ohlcv' in pair_data:
                ohlcv = pair_data['ohlcv'][-5:] if pair_data['ohlcv'] else []
                if len(ohlcv) >= 5:
                    # Calculate recent volatility
                    closes = [float(candle[4]) for candle in ohlcv]
                    volatility = np.std([closes[i]/closes[i-1] - 1 for i in range(1, len(closes))])
                    
                    if volatility > 0.02:  # 2% volatility
                        supporting.append('High_volatility')
            
            # Spread analysis
            if 'bid' in pair_data and 'ask' in pair_data:
                bid = float(pair_data['bid'])
                ask = float(pair_data['ask'])
                last = float(pair_data.get('last', 0))
                
                if last > 0:
                    spread_pct = (ask - bid) / last
                    if spread_pct < 0.001:  # Less than 0.1% spread
                        supporting.append('Tight_spread')
            
        except Exception as e:
            logger.error(f"Error getting supporting indicators: {e}")
        
        return supporting
    
    async def _generate_momentum_signals(
        self, 
        market_data: Dict, 
        correlation_matrix: CorrelationMatrix,
        account_balance: float
    ) -> List[TradingSignal]:
        """Generate momentum-based signals for high-volatility opportunities"""
        
        signals = []
        
        try:
            for pair in correlation_matrix.pairs:
                # Skip if we already have correlation signals for this pair
                has_correlation_signal = any(
                    opp.primary_pair == pair for opp in correlation_matrix.divergence_opportunities
                )
                
                if has_correlation_signal:
                    continue
                
                pair_data = market_data.get(pair)
                if not pair_data:
                    continue
                
                # Check for strong momentum
                momentum_score = await self._calculate_momentum_score(pair, pair_data)
                
                if momentum_score > 0.7:  # Strong momentum threshold
                    tier = self.correlation_engine._get_volatility_tier(pair)
                    params = self.volatility_params[tier]
                    
                    current_price = float(pair_data.get('last', 0))
                    if current_price <= 0:
                        continue
                    
                    # Determine direction based on momentum
                    price_change = float(pair_data.get('change_percent', 0))
                    direction = SignalDirection.LONG if price_change > 0 else SignalDirection.SHORT
                    
                    # Calculate levels
                    stop_loss_pct = params['stop_loss_pct']
                    tp1_pct = params['take_profit_1_pct']
                    
                    if direction == SignalDirection.LONG:
                        stop_loss = current_price * (1 - stop_loss_pct)
                        take_profit_1 = current_price * (1 + tp1_pct)
                        take_profit_2 = current_price * (1 + tp1_pct * 2)
                    else:
                        stop_loss = current_price * (1 + stop_loss_pct)
                        take_profit_1 = current_price * (1 - tp1_pct)
                        take_profit_2 = current_price * (1 - tp1_pct * 2)
                    
                    # Calculate position size
                    position_size_pct = self._calculate_position_size(
                        tier, momentum_score, account_balance, current_price, stop_loss
                    )
                    
                    # Create momentum signal
                    signal = TradingSignal(
                        symbol=pair,
                        direction=direction,
                        strength=self._determine_signal_strength(momentum_score, tier),
                        confidence=momentum_score,
                        volatility_tier=tier,
                        correlation_basis='momentum_breakout',
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        take_profit_1=take_profit_1,
                        take_profit_2=take_profit_2,
                        position_size_pct=position_size_pct,
                        timeframe=params['timeframes'][0],
                        max_hold_time_minutes=params['max_hold_minutes'],
                        supporting_indicators=await self._get_supporting_indicators(pair, market_data, direction),
                        risk_reward_ratio=abs(take_profit_1 - current_price) / abs(current_price - stop_loss),
                        correlation_signals=[],
                        timestamp=datetime.now()
                    )
                    
                    signals.append(signal)
        
        except Exception as e:
            logger.error(f"Error generating momentum signals: {e}")
        
        return signals
    
    async def _calculate_momentum_score(self, pair: str, pair_data: Dict) -> float:
        """Calculate momentum score for a trading pair"""
        
        try:
            momentum_factors = []
            
            # Price change momentum
            price_change = float(pair_data.get('change_percent', 0))
            momentum_factors.append(min(abs(price_change) / 10, 1.0))  # Normalize to 0-1
            
            # Volume momentum
            current_volume = float(pair_data.get('volume', 0))
            if current_volume > 0:
                # Simplified volume momentum - would need historical average for comparison
                momentum_factors.append(0.7)  # Placeholder
            
            # OHLC momentum
            if 'ohlcv' in pair_data and len(pair_data['ohlcv']) >= 5:
                ohlcv = pair_data['ohlcv'][-5:]
                closes = [float(candle[4]) for candle in ohlcv]
                
                # Calculate trend strength
                if len(closes) >= 3:
                    recent_trend = (closes[-1] - closes[0]) / closes[0]
                    momentum_factors.append(min(abs(recent_trend) * 5, 1.0))
            
            # Calculate weighted average
            if momentum_factors:
                return sum(momentum_factors) / len(momentum_factors)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating momentum score for {pair}: {e}")
            return 0.0
    
    async def _filter_and_rank_signals(
        self, 
        signals: List[TradingSignal], 
        market_data: Dict
    ) -> List[TradingSignal]:
        """Filter and rank signals by quality and avoid conflicts"""
        
        try:
            if not signals:
                return []
            
            # Filter out signals that are too close in time for same pair
            filtered_signals = []
            
            for signal in signals:
                last_signal_time = self.last_signal_time.get(signal.symbol, datetime.min)
                time_since_last = (datetime.now() - last_signal_time).total_seconds()
                
                # Minimum time between signals based on volatility tier
                min_interval = {
                    VolatilityTier.ULTRA_HIGH: 300,  # 5 minutes
                    VolatilityTier.HIGH: 900,        # 15 minutes
                    VolatilityTier.MEDIUM: 1800,     # 30 minutes
                    VolatilityTier.STANDARD: 3600   # 1 hour
                }
                
                required_interval = min_interval.get(signal.volatility_tier, 1800)
                
                if time_since_last >= required_interval:
                    filtered_signals.append(signal)
                    self.last_signal_time[signal.symbol] = datetime.now()
            
            # Rank by composite score (confidence * risk_reward_ratio * strength_multiplier)
            strength_multipliers = {
                SignalStrength.WEAK: 0.5,
                SignalStrength.MODERATE: 0.75,
                SignalStrength.STRONG: 1.0,
                SignalStrength.ULTRA_STRONG: 1.25
            }
            
            for signal in filtered_signals:
                strength_mult = strength_multipliers.get(signal.strength, 1.0)
                signal.composite_score = (
                    signal.confidence * 
                    min(signal.risk_reward_ratio, 5.0) * 
                    strength_mult
                )
            
            # Sort by composite score
            filtered_signals.sort(key=lambda x: getattr(x, 'composite_score', 0), reverse=True)
            
            # Return top 10 signals
            return filtered_signals[:10]
            
        except Exception as e:
            logger.error(f"Error filtering and ranking signals: {e}")
            return signals[:5]  # Return first 5 as fallback
    
    async def get_signal_summary(self) -> Dict:
        """Get summary of current signals and system status"""
        try:
            return {
                'total_signals_generated': len(self.signal_cache),
                'volatility_tiers_active': list(self.volatility_params.keys()),
                'correlation_engine_status': 'active',
                'last_update': datetime.now().isoformat(),
                'supported_pairs': self.correlation_engine.high_volatility_pairs
            }
        except Exception as e:
            logger.error(f"Error generating signal summary: {e}")
            return {'error': str(e)}