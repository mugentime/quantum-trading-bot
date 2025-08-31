"""
Ultra-High Frequency Trading Module for AXSUSDT
Specialized for 1-5 minute holds with 620% monthly target potential
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .config.settings import config

logger = logging.getLogger(__name__)

class UltraHighFrequencyTrader:
    """
    Ultra-high frequency trading system optimized for AXSUSDT
    Target: 620% monthly returns through rapid scalping
    """
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / 'config' / 'axsusdt_config.json'
        self.axs_config = self._load_axs_config()
        
        # Ultra-high frequency state tracking
        self.last_signal_time = None
        self.active_positions = {}
        self.volatility_history = []
        self.momentum_tracker = {}
        self.frequency_metrics = {
            'trades_per_hour': 0,
            'average_hold_time': 0,
            'success_rate': 0,
            'volatility_correlation': 0
        }
        
        # Circuit breaker for ultra-high frequency
        self.consecutive_losses = 0
        self.circuit_breaker_active = False
        self.cooldown_end_time = None
        
        logger.info("UltraHighFrequencyTrader initialized for AXSUSDT")
        logger.info(f"Target: {self.axs_config['target_performance']['monthly_target']}x monthly returns")
    
    def _load_axs_config(self) -> Dict:
        """Load AXSUSDT-specific configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("AXSUSDT config file not found - using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading AXSUSDT config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Default AXSUSDT configuration"""
        return {
            "symbol": "AXSUSDT",
            "target_performance": {"monthly_target": 6.2},
            "risk_parameters": {
                "max_position_size": 0.02,
                "leverage": 8.5,
                "stop_loss_percent": 0.015,
                "take_profit_percent": 0.04
            },
            "ultra_high_frequency": {
                "signal_refresh_seconds": 30,
                "min_signal_interval": 15,
                "max_trades_per_hour": 20
            }
        }
    
    async def analyze_ultra_high_frequency_opportunity(self, market_data: Dict, 
                                                     correlation_data: Dict) -> Dict:
        """
        Analyze ultra-high frequency trading opportunity for AXSUSDT
        Focus on 1-5 minute scalping opportunities
        """
        analysis = {
            'signal': None,
            'confidence': 0.0,
            'hold_time_estimate': 0,
            'volatility_score': 0.0,
            'momentum_direction': None,
            'risk_score': 0.0
        }
        
        try:
            # Check if AXSUSDT data is available
            if 'AXSUSDT' not in market_data:
                logger.debug("AXSUSDT data not available")
                return analysis
            
            axs_data = market_data['AXSUSDT']
            if not axs_data or 'last' not in axs_data:
                return analysis
            
            # Check circuit breaker
            if self._is_circuit_breaker_active():
                logger.debug("Circuit breaker active - skipping opportunity analysis")
                return analysis
            
            # Check signal frequency limits
            if not self._can_generate_signal():
                logger.debug("Signal frequency limit reached")
                return analysis
            
            # Calculate real-time volatility
            volatility_score = await self._calculate_real_time_volatility(axs_data)
            analysis['volatility_score'] = volatility_score
            
            # Minimum volatility threshold for ultra-high frequency
            if volatility_score < self.axs_config['volatility_detection']['volatility_threshold']:
                logger.debug(f"Insufficient volatility for UHF: {volatility_score}")
                return analysis
            
            # Analyze momentum for rapid entry/exit
            momentum_analysis = await self._analyze_ultra_momentum(axs_data, market_data)
            analysis['momentum_direction'] = momentum_analysis['direction']
            
            # Check correlation divergence opportunities
            correlation_opportunity = await self._check_correlation_divergence(
                'AXSUSDT', correlation_data
            )
            
            # Generate ultra-high frequency signal
            if (momentum_analysis['strength'] > 0.7 and 
                volatility_score > 0.05 and
                correlation_opportunity['strength'] > 0.6):
                
                signal = await self._generate_uhf_signal(
                    axs_data, momentum_analysis, correlation_opportunity, volatility_score
                )
                
                if signal:
                    analysis['signal'] = signal
                    analysis['confidence'] = self._calculate_signal_confidence(
                        momentum_analysis, volatility_score, correlation_opportunity
                    )
                    analysis['hold_time_estimate'] = self._estimate_hold_time(
                        volatility_score, momentum_analysis['strength']
                    )
                    analysis['risk_score'] = self._calculate_risk_score(
                        signal, volatility_score
                    )
                    
                    logger.info(f"UHF Signal Generated - AXSUSDT {signal['side']} "
                              f"Confidence: {analysis['confidence']:.2f} "
                              f"Hold Time: {analysis['hold_time_estimate']}s")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in ultra-high frequency analysis: {e}", exc_info=True)
            return analysis
    
    async def _calculate_real_time_volatility(self, axs_data: Dict) -> float:
        """Calculate real-time volatility for AXSUSDT"""
        try:
            current_price = float(axs_data['last'])
            
            # Store price in volatility history
            self.volatility_history.append({
                'price': current_price,
                'timestamp': datetime.now()
            })
            
            # Keep only last 15 minutes for ultra-high frequency
            cutoff_time = datetime.now() - timedelta(
                minutes=self.axs_config['volatility_detection']['volatility_lookback_minutes']
            )
            self.volatility_history = [
                h for h in self.volatility_history 
                if h['timestamp'] > cutoff_time
            ]
            
            if len(self.volatility_history) < 5:
                return 0.0
            
            # Calculate volatility as standard deviation of returns
            prices = [h['price'] for h in self.volatility_history]
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) if len(returns) > 1 else 0.0
            
            # Normalize volatility for scoring (0-1 scale)
            volatility_score = min(volatility / 0.05, 1.0)  # Cap at 5% volatility
            
            return float(volatility_score)
            
        except Exception as e:
            logger.error(f"Error calculating real-time volatility: {e}")
            return 0.0
    
    async def _analyze_ultra_momentum(self, axs_data: Dict, market_data: Dict) -> Dict:
        """Analyze ultra-short-term momentum for AXSUSDT"""
        try:
            current_price = float(axs_data['last'])
            symbol = 'AXSUSDT'
            
            # Initialize momentum tracker if needed
            if symbol not in self.momentum_tracker:
                self.momentum_tracker[symbol] = {
                    'prices': [],
                    'timestamps': [],
                    'ema_short': current_price,
                    'ema_long': current_price
                }
            
            tracker = self.momentum_tracker[symbol]
            
            # Add current price
            tracker['prices'].append(current_price)
            tracker['timestamps'].append(datetime.now())
            
            # Keep only last 5 minutes of data
            cutoff_time = datetime.now() - timedelta(minutes=5)
            while (tracker['timestamps'] and 
                   tracker['timestamps'][0] < cutoff_time):
                tracker['prices'].pop(0)
                tracker['timestamps'].pop(0)
            
            if len(tracker['prices']) < 3:
                return {'direction': None, 'strength': 0.0}
            
            # Calculate ultra-short EMAs (2 and 5 periods)
            alpha_short = 2.0 / (2 + 1)  # 2-period EMA
            alpha_long = 2.0 / (5 + 1)   # 5-period EMA
            
            tracker['ema_short'] = (alpha_short * current_price + 
                                  (1 - alpha_short) * tracker['ema_short'])
            tracker['ema_long'] = (alpha_long * current_price + 
                                 (1 - alpha_long) * tracker['ema_long'])
            
            # Determine momentum direction
            direction = None
            if tracker['ema_short'] > tracker['ema_long'] * 1.001:  # 0.1% threshold
                direction = 'bullish'
            elif tracker['ema_short'] < tracker['ema_long'] * 0.999:  # 0.1% threshold
                direction = 'bearish'
            
            # Calculate momentum strength
            price_change = (tracker['prices'][-1] - tracker['prices'][0]) / tracker['prices'][0]
            strength = min(abs(price_change) / 0.02, 1.0)  # Normalize to 2% max change
            
            return {
                'direction': direction,
                'strength': float(strength),
                'ema_cross': tracker['ema_short'] > tracker['ema_long'],
                'price_change': float(price_change)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing ultra momentum: {e}")
            return {'direction': None, 'strength': 0.0}
    
    async def _check_correlation_divergence(self, symbol: str, 
                                          correlation_data: Dict) -> Dict:
        """Check for correlation divergence opportunities"""
        try:
            if not correlation_data or 'opportunities' not in correlation_data:
                return {'strength': 0.0, 'type': None}
            
            opportunities = correlation_data['opportunities']
            
            # Look for AXSUSDT opportunities
            axs_opportunities = [
                opp for opp in opportunities 
                if symbol in opp.get('symbols', [])
            ]
            
            if not axs_opportunities:
                return {'strength': 0.0, 'type': None}
            
            # Get strongest opportunity
            best_opp = max(axs_opportunities, key=lambda x: x.get('confidence', 0))
            
            return {
                'strength': float(best_opp.get('confidence', 0)),
                'type': best_opp.get('type', None),
                'correlation': float(best_opp.get('correlation', 0)),
                'paired_with': [s for s in best_opp.get('symbols', []) if s != symbol]
            }
            
        except Exception as e:
            logger.error(f"Error checking correlation divergence: {e}")
            return {'strength': 0.0, 'type': None}
    
    async def _generate_uhf_signal(self, axs_data: Dict, momentum_analysis: Dict,
                                 correlation_opportunity: Dict, volatility_score: float) -> Optional[Dict]:
        """Generate ultra-high frequency trading signal"""
        try:
            current_price = float(axs_data['last'])
            
            # Determine signal direction
            signal_direction = None
            signal_strength = 0.0
            
            # Primary: Momentum direction
            if momentum_analysis['direction'] == 'bullish':
                signal_direction = 'buy'
                signal_strength += momentum_analysis['strength'] * 0.4
            elif momentum_analysis['direction'] == 'bearish':
                signal_direction = 'sell'
                signal_strength += momentum_analysis['strength'] * 0.4
            
            # Secondary: Correlation divergence
            if correlation_opportunity['type'] == 'high_correlation':
                # Trade in same direction as correlation
                corr_strength = correlation_opportunity['strength'] * 0.3
                signal_strength += corr_strength
            elif correlation_opportunity['type'] == 'negative_correlation':
                # Trade opposite to correlation
                corr_strength = correlation_opportunity['strength'] * 0.2
                signal_strength += corr_strength
            
            # Volatility boost
            signal_strength += min(volatility_score * 0.3, 0.3)
            
            if signal_direction and signal_strength > 0.6:
                # Calculate position parameters
                position_size = self._calculate_uhf_position_size(
                    signal_strength, volatility_score
                )
                leverage = self.axs_config['risk_parameters']['leverage']
                
                # Calculate stop loss and take profit
                if signal_direction == 'buy':
                    stop_loss = current_price * (1 - self.axs_config['risk_parameters']['stop_loss_percent'])
                    take_profit = current_price * (1 + self.axs_config['risk_parameters']['take_profit_percent'])
                else:
                    stop_loss = current_price * (1 + self.axs_config['risk_parameters']['stop_loss_percent'])
                    take_profit = current_price * (1 - self.axs_config['risk_parameters']['take_profit_percent'])
                
                signal = {
                    'symbol': 'AXSUSDT',
                    'side': signal_direction,
                    'entry_price': current_price,
                    'position_size': position_size,
                    'leverage': leverage,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'signal_strength': signal_strength,
                    'volatility_score': volatility_score,
                    'momentum_direction': momentum_analysis['direction'],
                    'correlation_type': correlation_opportunity.get('type'),
                    'timestamp': datetime.now().isoformat(),
                    'trading_mode': 'ultra_high_frequency',
                    'expected_hold_time': self._estimate_hold_time(volatility_score, signal_strength)
                }
                
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating UHF signal: {e}")
            return None
    
    def _calculate_uhf_position_size(self, signal_strength: float, 
                                   volatility_score: float) -> float:
        """Calculate position size for ultra-high frequency trade"""
        try:
            base_position_size = self.axs_config['risk_parameters']['max_position_size']
            
            # Adjust for signal strength (0.5x to 1.0x)
            strength_multiplier = 0.5 + (signal_strength * 0.5)
            
            # Adjust for volatility (reduce size for high volatility)
            volatility_adjustment = max(0.5, 1.0 - volatility_score * 0.3)
            
            position_size = base_position_size * strength_multiplier * volatility_adjustment
            
            # Ensure within bounds
            return max(0.005, min(position_size, base_position_size))
            
        except Exception as e:
            logger.error(f"Error calculating UHF position size: {e}")
            return 0.01  # Safe default
    
    def _calculate_signal_confidence(self, momentum_analysis: Dict, 
                                   volatility_score: float,
                                   correlation_opportunity: Dict) -> float:
        """Calculate overall signal confidence"""
        try:
            confidence = 0.0
            
            # Momentum confidence (0-0.4)
            momentum_strength = momentum_analysis.get('strength', 0)
            confidence += momentum_strength * 0.4
            
            # Volatility confidence (0-0.3)
            vol_confidence = min(volatility_score / 0.1, 1.0)  # Normalize to 10% vol
            confidence += vol_confidence * 0.3
            
            # Correlation confidence (0-0.3)
            corr_strength = correlation_opportunity.get('strength', 0)
            confidence += corr_strength * 0.3
            
            return min(confidence, 0.95)  # Cap at 95%
            
        except Exception as e:
            logger.error(f"Error calculating signal confidence: {e}")
            return 0.5  # Default moderate confidence
    
    def _estimate_hold_time(self, volatility_score: float, signal_strength: float) -> int:
        """Estimate hold time in seconds for ultra-high frequency trade"""
        try:
            # Base hold time from config
            base_time = self.axs_config['target_performance']['hold_time_range']['target_average']
            
            # Adjust for volatility (higher volatility = shorter hold time)
            volatility_adjustment = max(0.5, 1.0 - volatility_score * 0.4)
            
            # Adjust for signal strength (stronger signal = longer hold time)
            strength_adjustment = 0.8 + (signal_strength * 0.4)
            
            estimated_time = int(base_time * volatility_adjustment * strength_adjustment)
            
            # Ensure within ultra-high frequency bounds
            min_time = self.axs_config['target_performance']['hold_time_range']['min_seconds']
            max_time = self.axs_config['target_performance']['hold_time_range']['max_seconds']
            
            return max(min_time, min(estimated_time, max_time))
            
        except Exception as e:
            logger.error(f"Error estimating hold time: {e}")
            return 180  # 3 minutes default
    
    def _calculate_risk_score(self, signal: Dict, volatility_score: float) -> float:
        """Calculate risk score for ultra-high frequency trade"""
        try:
            risk_score = 0.0
            
            # Base risk from position size
            position_size = signal.get('position_size', 0)
            max_size = self.axs_config['risk_parameters']['max_position_size']
            size_risk = position_size / max_size * 0.3
            risk_score += size_risk
            
            # Volatility risk
            vol_risk = min(volatility_score * 0.4, 0.4)
            risk_score += vol_risk
            
            # Leverage risk
            leverage = signal.get('leverage', 1)
            leverage_risk = max(0, (leverage - 5) / 10) * 0.2  # Risk above 5x leverage
            risk_score += leverage_risk
            
            # Time-of-day risk
            current_hour = datetime.now().hour
            if current_hour in self.axs_config['market_conditions']['avoid_hours']:
                risk_score += 0.1
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.5  # Moderate risk default
    
    def _can_generate_signal(self) -> bool:
        """Check if new signal can be generated based on frequency limits"""
        try:
            if not self.last_signal_time:
                return True
            
            min_interval = self.axs_config['ultra_high_frequency']['min_signal_interval']
            time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
            
            return time_since_last >= min_interval
            
        except Exception as e:
            logger.error(f"Error checking signal generation: {e}")
            return True
    
    def _is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is active"""
        try:
            if not self.circuit_breaker_active:
                return False
            
            if self.cooldown_end_time and datetime.now() > self.cooldown_end_time:
                # Reset circuit breaker
                self.circuit_breaker_active = False
                self.consecutive_losses = 0
                self.cooldown_end_time = None
                logger.info("Circuit breaker reset - UHF trading resumed")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return False
    
    def update_trade_result(self, trade_result: Dict):
        """Update ultra-high frequency performance metrics"""
        try:
            symbol = trade_result.get('symbol', '')
            if symbol != 'AXSUSDT':
                return
            
            # Update consecutive losses for circuit breaker
            if trade_result.get('pnl_pct', 0) < 0:
                self.consecutive_losses += 1
                
                # Trigger circuit breaker if needed
                max_losses = self.axs_config.get('safety_mechanisms', {}).get(
                    'circuit_breaker', {}
                ).get('max_consecutive_losses', 3)
                
                if self.consecutive_losses >= max_losses:
                    self._trigger_circuit_breaker()
            else:
                self.consecutive_losses = 0
            
            # Update frequency metrics
            self._update_frequency_metrics(trade_result)
            
            logger.info(f"UHF Trade Result: {symbol} PnL: {trade_result.get('pnl_pct', 0):.2%}")
            
        except Exception as e:
            logger.error(f"Error updating trade result: {e}")
    
    def _trigger_circuit_breaker(self):
        """Trigger circuit breaker to pause ultra-high frequency trading"""
        try:
            self.circuit_breaker_active = True
            cooldown_minutes = self.axs_config.get('safety_mechanisms', {}).get(
                'circuit_breaker', {}
            ).get('cooldown_minutes', 30)
            
            self.cooldown_end_time = datetime.now() + timedelta(minutes=cooldown_minutes)
            
            logger.warning(f"Circuit breaker triggered for UHF trading - "
                         f"Cooldown until {self.cooldown_end_time}")
            
        except Exception as e:
            logger.error(f"Error triggering circuit breaker: {e}")
    
    def _update_frequency_metrics(self, trade_result: Dict):
        """Update ultra-high frequency performance metrics"""
        try:
            # This would integrate with the performance tracker
            # For now, just log the key metrics
            hold_time = trade_result.get('hold_time_seconds', 0)
            pnl_pct = trade_result.get('pnl_pct', 0)
            
            logger.info(f"UHF Metrics Update - Hold Time: {hold_time}s, "
                       f"PnL: {pnl_pct:.2%}, Consecutive Losses: {self.consecutive_losses}")
            
        except Exception as e:
            logger.error(f"Error updating frequency metrics: {e}")
    
    def get_uhf_status(self) -> Dict:
        """Get ultra-high frequency trading status"""
        try:
            return {
                'active': not self.circuit_breaker_active,
                'consecutive_losses': self.consecutive_losses,
                'circuit_breaker_active': self.circuit_breaker_active,
                'cooldown_end_time': self.cooldown_end_time.isoformat() if self.cooldown_end_time else None,
                'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
                'active_positions': len(self.active_positions),
                'volatility_readings': len(self.volatility_history),
                'target_monthly_return': self.axs_config['target_performance']['monthly_target']
            }
            
        except Exception as e:
            logger.error(f"Error getting UHF status: {e}")
            return {'active': False, 'error': str(e)}
    
    def update_signal_time(self):
        """Update last signal generation time"""
        self.last_signal_time = datetime.now()

# Global instance
ultra_high_frequency_trader = UltraHighFrequencyTrader()