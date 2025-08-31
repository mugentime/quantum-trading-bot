"""
Enhanced Risk Management System
Implements advanced risk controls, position limits, and emergency safeguards
"""
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .config.settings import config
from .leverage_manager import leverage_manager

logger = logging.getLogger(__name__)

class RiskManager:
    """Advanced risk management with real-time monitoring and controls"""
    
    def __init__(self):
        self.emergency_mode = False
        self.daily_trades_count = 0
        self.daily_start = datetime.now().date()
        self.active_correlations = {}
        self.margin_usage_history = []
        self.risk_violations = []
        
    async def validate_trade_risk(self, signal: Dict, account_balance: float,
                                proposed_leverage: int, position_size: float) -> Dict:
        """
        Comprehensive trade risk validation
        
        Returns:
            Dict with 'approved', 'warnings', 'adjustments', 'reason'
        """
        validation_result = {
            'approved': True,
            'warnings': [],
            'adjustments': {},
            'reason': 'Trade approved',
            'risk_score': 0.0
        }
        
        try:
            # Check emergency mode
            if self.emergency_mode:
                validation_result.update({
                    'approved': False,
                    'reason': 'Emergency mode active - trading suspended'
                })
                return validation_result
            
            # Check daily loss limits - SCALPING OPTIMIZED
            if leverage_manager.daily_pnl < -config.MAX_DAILY_DRAWDOWN * account_balance:
                validation_result['warnings'].append('Daily drawdown limit approached')
                validation_result['adjustments']['reduce_position_size'] = 0.5  # More conservative for scalping
                validation_result['risk_score'] += 0.3
            
            # Check position concentration
            symbol = signal.get('symbol', '')
            correlation_risk = await self._check_correlation_risk(symbol, position_size)
            if correlation_risk['high_risk']:
                validation_result['warnings'].append(f'High correlation exposure: {correlation_risk["exposure"]:.1%}')
                validation_result['adjustments']['max_position_size'] = correlation_risk['max_allowed']
                validation_result['risk_score'] += 0.2
            
            # Check margin requirements - OPTIMIZED FOR 8.5X LEVERAGE
            estimated_margin = self._calculate_margin_requirement(
                account_balance, position_size, proposed_leverage
            )
            
            if estimated_margin > config.MAX_MARGIN_USAGE * account_balance:
                validation_result['warnings'].append('High margin usage detected')
                validation_result['adjustments']['reduce_leverage'] = max(8, int(proposed_leverage * 0.9))  # Adjusted for 8.5x base
                validation_result['risk_score'] += 0.2
            
            # Check leverage safety - FOCUSED ON 8.5X ETHUSDT + AXSUSDT
            safe_leverage = leverage_manager.calculate_safe_leverage(account_balance, symbol)
            # Allow leverage optimization for specific pairs
            if symbol == 'ETHUSDT':
                leverage_multiplier = 1.3  # Higher for proven ETHUSDT performance
            elif symbol == 'AXSUSDT':
                leverage_multiplier = 1.2  # Moderate for AXSUSDT high volatility potential
            else:
                leverage_multiplier = 1.1
            if proposed_leverage > safe_leverage * leverage_multiplier:
                validation_result['warnings'].append(f'Leverage exceeds safe limit: {safe_leverage}x')
                validation_result['adjustments']['max_leverage'] = int(safe_leverage * leverage_multiplier)
                validation_result['risk_score'] += 0.15
            
            # Check signal quality
            signal_risk = self._assess_signal_risk(signal)
            validation_result['risk_score'] += signal_risk
            
            if signal_risk > 0.3:
                validation_result['warnings'].append('Low confidence signal detected')
            
            # Check trading frequency - SCALPING FREQUENCY MANAGEMENT
            if self._check_overtrading():
                validation_result['warnings'].append('High trading frequency detected')
                validation_result['adjustments']['delay_seconds'] = 30  # 30-second delay for scalping
                validation_result['risk_score'] += 0.15
            
            # Final risk assessment - SCALPING RISK MANAGEMENT
            if validation_result['risk_score'] > 0.65:  # Lower threshold for scalping safety
                validation_result.update({
                    'approved': False,
                    'reason': f'Risk score too high for scalping: {validation_result["risk_score"]:.2f}'
                })
            elif validation_result['risk_score'] > 0.45:  # Lower warning threshold for scalping
                validation_result['warnings'].append('Moderate risk scalping trade - enhanced monitoring active')
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in trade risk validation: {e}")
            return {
                'approved': False,
                'warnings': ['Risk validation failed'],
                'adjustments': {},
                'reason': f'Risk validation error: {str(e)}',
                'risk_score': 1.0
            }
    
    async def _check_correlation_risk(self, symbol: str, position_size: float) -> Dict:
        """Check if new position would create excessive correlation exposure"""
        try:
            # Group symbols by correlation - INCLUDING AXSUSDT
            correlation_groups = {
                'crypto_majors': ['BTCUSDT', 'ETHUSDT'],
                'high_volatility': ['AXSUSDT', 'SOLUSDT'],  # AXSUSDT in high volatility group
                'altcoins': ['BNBUSDT', 'XRPUSDT']
            }
            
            current_group = None
            for group, symbols in correlation_groups.items():
                if symbol in symbols:
                    current_group = group
                    break
            
            if not current_group:
                return {'high_risk': False, 'exposure': 0.0, 'max_allowed': position_size}
            
            # Calculate current exposure in this correlation group
            current_exposure = sum(
                pos.get('position_size', 0) 
                for pos_symbol, pos in self.active_correlations.items()
                if pos_symbol in correlation_groups[current_group]
            )
            
            total_exposure = current_exposure + position_size
            max_allowed_exposure = config.MAX_CORRELATION_EXPOSURE
            
            if total_exposure > max_allowed_exposure:
                max_allowed_position = max(0, max_allowed_exposure - current_exposure)
                return {
                    'high_risk': True,
                    'exposure': total_exposure,
                    'max_allowed': max_allowed_position
                }
            
            return {
                'high_risk': False,
                'exposure': total_exposure,
                'max_allowed': position_size
            }
            
        except Exception as e:
            logger.error(f"Error checking correlation risk: {e}")
            return {'high_risk': False, 'exposure': 0.0, 'max_allowed': position_size}
    
    def _calculate_margin_requirement(self, balance: float, position_size: float, 
                                    leverage: int) -> float:
        """Calculate required margin for position"""
        try:
            position_value = balance * position_size
            margin_required = position_value / leverage
            return margin_required
        except Exception as e:
            logger.error(f"Error calculating margin requirement: {e}")
            return balance * position_size  # Conservative fallback
    
    def _assess_signal_risk(self, signal: Dict) -> float:
        """Assess risk level of trading signal"""
        try:
            risk_score = 0.0
            
            # Check correlation strength
            correlation = abs(signal.get('correlation', 0.5))
            if correlation < 0.3:
                risk_score += 0.2  # Very weak correlation
            elif correlation < 0.5:
                risk_score += 0.1  # Weak correlation
            
            # Check deviation magnitude
            deviation = signal.get('deviation', 0.15)
            if deviation < 0.12:
                risk_score += 0.15  # Weak signal
            elif deviation > 2.0:
                risk_score += 0.1   # Extreme deviation might be noise
            
            # Check time of day (avoid low liquidity periods)
            current_hour = datetime.now().hour
            if current_hour in [0, 1, 2, 3, 4, 5]:  # Low liquidity hours
                risk_score += 0.1
            
            return min(risk_score, 0.5)  # Cap at 0.5
            
        except Exception as e:
            logger.error(f"Error assessing signal risk: {e}")
            return 0.3  # Default moderate risk
    
    def _check_overtrading(self) -> bool:
        """Check if trading frequency is excessive"""
        try:
            current_date = datetime.now().date()
            
            # Reset daily counter if new day
            if current_date != self.daily_start:
                self.daily_trades_count = 0
                self.daily_start = current_date
            
            # Check if approaching daily trade limit for scalping
            max_daily_trades = 35  # Higher limit for scalping strategy
            return self.daily_trades_count >= max_daily_trades
            
        except Exception as e:
            logger.error(f"Error checking overtrading: {e}")
            return False
    
    async def monitor_positions(self, executor) -> Dict:
        """Monitor open positions for risk violations"""
        try:
            monitoring_result = {
                'violations': [],
                'warnings': [],
                'actions_required': [],
                'emergency_triggered': False
            }
            
            # Get current positions
            positions = await executor.get_open_positions()
            
            # Check individual position risks
            for position in positions:
                position_risk = await self._check_position_risk(position, executor)
                
                if position_risk['emergency']:
                    monitoring_result['violations'].append(
                        f"Emergency: {position['symbol']} - {position_risk['reason']}"
                    )
                    monitoring_result['actions_required'].append(
                        f"CLOSE {position['symbol']} immediately"
                    )
                
                if position_risk['warning']:
                    monitoring_result['warnings'].append(
                        f"Warning: {position['symbol']} - {position_risk['reason']}"
                    )
            
            # Check portfolio-level risks
            portfolio_risk = self._assess_portfolio_risk(positions)
            
            if portfolio_risk['critical']:
                monitoring_result['emergency_triggered'] = True
                monitoring_result['actions_required'].append("EMERGENCY: Close all positions")
                await self._trigger_emergency_mode()
            
            return monitoring_result
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
            return {'violations': [], 'warnings': [], 'actions_required': [], 'emergency_triggered': False}
    
    async def _check_position_risk(self, position: Dict, executor) -> Dict:
        """Check individual position for risk violations"""
        try:
            symbol = position.get('symbol', '')
            entry_price = position.get('entry_price', 0)
            
            # Get current market price
            try:
                ticker = await executor.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
            except:
                return {'emergency': False, 'warning': False, 'reason': 'Cannot get current price'}
            
            # Calculate unrealized P&L
            side = position.get('side', 'buy').lower()
            quantity = position.get('quantity', 0)
            
            if side in ['long', 'buy']:
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price
            
            # Check for emergency conditions - SCALPING THRESHOLDS
            if pnl_pct < -0.08:  # 8% loss triggers emergency for scalping
                return {
                    'emergency': True,
                    'warning': False,
                    'reason': f'Excessive loss for scalping: {pnl_pct:.1%}'
                }
            
            # Check for warning conditions - SCALPING THRESHOLDS
            if pnl_pct < -0.04:  # 4% loss triggers warning for scalping
                return {
                    'emergency': False,
                    'warning': True,
                    'reason': f'Significant loss for scalping: {pnl_pct:.1%}'
                }
            
            return {'emergency': False, 'warning': False, 'reason': 'Position normal'}
            
        except Exception as e:
            logger.error(f"Error checking position risk: {e}")
            return {'emergency': False, 'warning': True, 'reason': f'Risk check failed: {str(e)}'}
    
    def _assess_portfolio_risk(self, positions: List[Dict]) -> Dict:
        """Assess overall portfolio risk"""
        try:
            if not positions:
                return {'critical': False, 'moderate': False, 'reason': 'No positions'}
            
            # Check for excessive position count
            if len(positions) > config.MAX_CONCURRENT_POSITIONS * 1.5:
                return {
                    'critical': True,
                    'moderate': False,
                    'reason': f'Too many positions: {len(positions)}'
                }
            
            # Check daily P&L
            if leverage_manager.daily_pnl < -config.MAX_DAILY_DRAWDOWN * 0.8:
                return {
                    'critical': True,
                    'moderate': False,
                    'reason': f'Approaching daily loss limit: {leverage_manager.daily_pnl}'
                }
            
            return {'critical': False, 'moderate': False, 'reason': 'Portfolio normal'}
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return {'critical': False, 'moderate': True, 'reason': f'Assessment failed: {str(e)}'}
    
    async def _trigger_emergency_mode(self):
        """Trigger emergency trading halt"""
        try:
            self.emergency_mode = True
            self.risk_violations.append({
                'timestamp': datetime.now(),
                'type': 'EMERGENCY',
                'reason': 'Portfolio risk exceeded critical threshold',
                'action': 'Trading suspended'
            })
            
            logger.critical("EMERGENCY MODE ACTIVATED - Trading suspended")
            
            # Here you could add additional emergency actions:
            # - Send urgent notifications
            # - Close all positions
            # - Reduce leverage across all symbols
            
        except Exception as e:
            logger.error(f"Error triggering emergency mode: {e}")
    
    def update_position_tracking(self, symbol: str, position_data: Dict):
        """Update position tracking for correlation monitoring"""
        try:
            self.active_correlations[symbol] = {
                'position_size': position_data.get('position_size', 0),
                'entry_time': datetime.now(),
                'side': position_data.get('side', 'buy')
            }
        except Exception as e:
            logger.error(f"Error updating position tracking: {e}")
    
    def remove_position_tracking(self, symbol: str):
        """Remove position from correlation tracking"""
        try:
            if symbol in self.active_correlations:
                del self.active_correlations[symbol]
        except Exception as e:
            logger.error(f"Error removing position tracking: {e}")
    
    def get_risk_metrics(self) -> Dict:
        """Get comprehensive risk metrics"""
        try:
            return {
                'emergency_mode': self.emergency_mode,
                'daily_trades': self.daily_trades_count,
                'daily_pnl': leverage_manager.daily_pnl,
                'daily_drawdown_limit': config.MAX_DAILY_DRAWDOWN,
                'active_positions': len(self.active_correlations),
                'max_positions': config.MAX_CONCURRENT_POSITIONS,
                'recent_violations': len([v for v in self.risk_violations 
                                        if v['timestamp'] > datetime.now() - timedelta(hours=24)]),
                'risk_status': self._get_overall_risk_status()
            }
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {}
    
    def _get_overall_risk_status(self) -> str:
        """Get overall risk status assessment"""
        try:
            if self.emergency_mode:
                return 'EMERGENCY'
            
            risk_factors = 0
            
            # Check various risk factors
            if leverage_manager.daily_pnl < -config.MAX_DAILY_DRAWDOWN * 0.5:
                risk_factors += 1
            
            if len(self.active_correlations) > config.MAX_CONCURRENT_POSITIONS * 0.8:
                risk_factors += 1
            
            if leverage_manager._calculate_recent_win_rate() < 0.4:
                risk_factors += 1
            
            if risk_factors >= 2:
                return 'HIGH'
            elif risk_factors == 1:
                return 'MODERATE'
            else:
                return 'LOW'
                
        except Exception as e:
            logger.error(f"Error assessing overall risk status: {e}")
            return 'UNKNOWN'
    
    def validate_scalping_trade(self, signal: Dict, account_balance: float) -> Dict:
        """Validate scalping trade with specific scalping risk parameters"""
        validation_result = {
            'approved': True,
            'warnings': [],
            'adjustments': {},
            'reason': 'Scalping trade approved',
            'risk_score': 0.0
        }
        
        try:
            # Scalping-specific checks
            symbol = signal.get('symbol', '')
            confidence = signal.get('confidence', 0)
            
            # Check signal freshness (scalping requires fresh signals)
            signal_time = datetime.fromisoformat(signal.get('timestamp', datetime.now().isoformat()))
            signal_age = (datetime.now() - signal_time).total_seconds()
            
            if signal_age > 60:  # Signal older than 1 minute
                validation_result['warnings'].append('Signal age exceeds scalping threshold')
                validation_result['risk_score'] += 0.2
            
            # Check market volatility for scalping
            volatility = signal.get('correlation_data', {}).get('volatility', 0)
            if volatility < 0.01:  # Too low volatility for scalping
                validation_result.update({
                    'approved': False,
                    'reason': 'Insufficient market volatility for scalping'
                })
                return validation_result
            
            # Check trading session activity
            current_hour = datetime.now().hour
            if current_hour in [0, 1, 2, 3, 4, 5]:  # Low activity hours
                validation_result['warnings'].append('Trading during low activity hours')
                validation_result['adjustments']['reduce_position_size'] = 0.7
                validation_result['risk_score'] += 0.25
            
            # Check for rapid consecutive trades (scalping frequency control)
            if hasattr(self, 'last_trade_time') and self.last_trade_time:
                time_since_last_trade = (datetime.now() - self.last_trade_time).total_seconds()
                if time_since_last_trade < 30:  # Less than 30 seconds
                    validation_result['warnings'].append('Rapid consecutive trading detected')
                    validation_result['adjustments']['delay_seconds'] = 30 - time_since_last_trade
                    validation_result['risk_score'] += 0.15
            
            # Scalping position size limits
            max_scalping_position = account_balance * 0.15  # 15% max for scalping
            if signal.get('position_size', 0) > max_scalping_position:
                validation_result['adjustments']['max_position_size'] = max_scalping_position
                validation_result['warnings'].append('Position size reduced for scalping safety')
            
            # Final scalping risk assessment
            if validation_result['risk_score'] > 0.5:
                validation_result.update({
                    'approved': False,
                    'reason': f'Scalping risk score too high: {validation_result["risk_score"]:.2f}'
                })
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in scalping trade validation: {e}")
            return {
                'approved': False,
                'warnings': ['Scalping validation failed'],
                'adjustments': {},
                'reason': f'Scalping validation error: {str(e)}',
                'risk_score': 1.0
            }
    
    def update_scalping_metrics(self, trade_result: Dict):
        """Update scalping-specific performance metrics"""
        try:
            if not hasattr(self, 'scalping_metrics'):
                self.scalping_metrics = {
                    'total_scalping_trades': 0,
                    'successful_scalps': 0,
                    'failed_scalps': 0,
                    'average_hold_time': 0,
                    'best_scalp_pnl': 0,
                    'worst_scalp_pnl': 0,
                    'scalping_win_rate': 0
                }
            
            # Update metrics
            self.scalping_metrics['total_scalping_trades'] += 1
            pnl = trade_result.get('pnl_pct', 0)
            
            if pnl > 0:
                self.scalping_metrics['successful_scalps'] += 1
            else:
                self.scalping_metrics['failed_scalps'] += 1
            
            # Update best/worst
            if pnl > self.scalping_metrics['best_scalp_pnl']:
                self.scalping_metrics['best_scalp_pnl'] = pnl
            if pnl < self.scalping_metrics['worst_scalp_pnl']:
                self.scalping_metrics['worst_scalp_pnl'] = pnl
            
            # Update win rate
            total = self.scalping_metrics['total_scalping_trades']
            successful = self.scalping_metrics['successful_scalps']
            self.scalping_metrics['scalping_win_rate'] = successful / total if total > 0 else 0
            
            # Update hold time
            hold_time = trade_result.get('hold_time_seconds', 0)
            current_avg = self.scalping_metrics['average_hold_time']
            self.scalping_metrics['average_hold_time'] = (current_avg * (total - 1) + hold_time) / total
            
            # Update last trade time for frequency control
            self.last_trade_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating scalping metrics: {e}")
    
    def get_scalping_performance(self) -> Dict:
        """Get scalping performance statistics"""
        try:
            if not hasattr(self, 'scalping_metrics'):
                return {}
            
            metrics = self.scalping_metrics.copy()
            
            # Add derived metrics
            metrics['trades_per_hour'] = self._calculate_trades_per_hour()
            metrics['risk_adjusted_return'] = self._calculate_risk_adjusted_scalping_return()
            metrics['frequency_score'] = self._calculate_frequency_score()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting scalping performance: {e}")
            return {}
    
    def _calculate_trades_per_hour(self) -> float:
        """Calculate average trades per hour for scalping"""
        try:
            if not hasattr(self, 'scalping_metrics'):
                return 0.0
            
            total_trades = self.scalping_metrics.get('total_scalping_trades', 0)
            if total_trades == 0:
                return 0.0
            
            # Estimate based on average hold time and trading hours
            avg_hold_time = self.scalping_metrics.get('average_hold_time', 300)  # 5 minutes default
            trades_per_hour = 3600 / max(avg_hold_time, 60)  # At least 1 minute per trade
            
            return min(trades_per_hour, 20)  # Cap at 20 trades per hour
            
        except Exception as e:
            logger.error(f"Error calculating trades per hour: {e}")
            return 0.0
    
    def _calculate_risk_adjusted_scalping_return(self) -> float:
        """Calculate risk-adjusted return for scalping"""
        try:
            if not hasattr(self, 'scalping_metrics'):
                return 0.0
            
            win_rate = self.scalping_metrics.get('scalping_win_rate', 0)
            best_pnl = self.scalping_metrics.get('best_scalp_pnl', 0)
            worst_pnl = abs(self.scalping_metrics.get('worst_scalp_pnl', 0))
            
            # Simple risk-adjusted calculation
            if worst_pnl == 0:
                return win_rate * best_pnl
            
            return (win_rate * best_pnl) / worst_pnl
            
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted return: {e}")
            return 0.0
    
    def _calculate_frequency_score(self) -> float:
        """Calculate trading frequency score for scalping efficiency"""
        try:
            total_trades = self.scalping_metrics.get('total_scalping_trades', 0)
            win_rate = self.scalping_metrics.get('scalping_win_rate', 0)
            
            # Target: 20-35 trades per day with >65% win rate
            target_trades = 25
            target_win_rate = 0.65
            
            frequency_score = (total_trades / target_trades) * (win_rate / target_win_rate)
            return min(frequency_score, 2.0)  # Cap at 2.0
            
        except Exception as e:
            logger.error(f"Error calculating frequency score: {e}")
            return 0.0
    
    def reset_emergency_mode(self):
        """Reset emergency mode (manual intervention required)"""
        try:
            self.emergency_mode = False
            logger.info("Emergency mode reset - Trading resumed")
        except Exception as e:
            logger.error(f"Error resetting emergency mode: {e}")
    
    def filter_signals(self, signals: List[Dict]) -> List[Dict]:
        """
        Filter trading signals based on risk management rules
        Compatible with ultra-high frequency trading system
        """
        if not signals:
            return []
        
        try:
            filtered_signals = []
            
            for signal in signals:
                # Skip if emergency mode active
                if self.emergency_mode:
                    logger.warning("Emergency mode active - filtering out all signals")
                    continue
                
                # Basic signal validation
                if not isinstance(signal, dict):
                    logger.warning("Invalid signal format - skipping")
                    continue
                
                # Check required signal fields
                required_fields = ['symbol', 'action', 'confidence', 'price']
                if not all(field in signal for field in required_fields):
                    logger.warning(f"Signal missing required fields: {signal}")
                    continue
                
                # Skip low confidence signals
                if signal.get('confidence', 0) < 0.3:
                    logger.debug(f"Filtering low confidence signal: {signal['confidence']}")
                    continue
                
                # Check trading frequency limits
                if self._check_overtrading():
                    logger.warning("Trading frequency limit reached - filtering signals")
                    continue
                
                # Check daily loss limits
                account_balance = signal.get('account_balance', 10000)  # Default fallback
                if leverage_manager.daily_pnl < -config.MAX_DAILY_DRAWDOWN * account_balance:
                    logger.warning("Daily loss limit reached - filtering signals")
                    continue
                
                # Signal passed all filters
                filtered_signals.append(signal)
                logger.debug(f"Signal approved for {signal['symbol']}: confidence {signal['confidence']}")
            
            logger.info(f"Filtered {len(signals)} signals down to {len(filtered_signals)} approved signals")
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Error filtering signals: {e}")
            return []  # Fail safe - return empty list if error

# Global instance
risk_manager = RiskManager()