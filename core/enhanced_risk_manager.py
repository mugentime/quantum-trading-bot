"""
Enhanced Risk Manager for High-Leverage Trading
Provides advanced risk controls, circuit breakers, and emergency protocols
"""
import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from .enhanced_leverage_config import enhanced_leverage_config
from .volatility_manager import volatility_manager
import ccxt

logger = logging.getLogger(__name__)

class EnhancedRiskManager:
    """Advanced risk management for high-leverage trading"""
    
    def __init__(self):
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_start = datetime.now().date()
        self.circuit_breakers = {}
        self.emergency_mode = False
        self.leverage_heat_score = 0.0
        self.risk_violations = []
        
        # Risk thresholds
        self.MAX_DAILY_LOSS = 0.15  # 15% max daily loss
        self.MAX_DRAWDOWN = 0.25   # 25% max total drawdown
        self.MAX_CONCURRENT_HIGH_LEVERAGE = 2  # Max 2 positions >30x
        self.MAX_PORTFOLIO_LEVERAGE = 3.0  # Max 300% leverage exposure
        self.EMERGENCY_STOP_LOSS = 0.20  # Emergency stop at 20% account loss
        
    async def validate_trade_entry(self, signal: Dict, position_params: Dict,
                                 account_balance: float, active_positions: Dict,
                                 exchange: Any) -> Dict:
        """
        Comprehensive pre-trade risk validation
        
        Args:
            signal: Trading signal data
            position_params: Calculated position parameters
            account_balance: Current account balance
            active_positions: Current open positions
            exchange: Exchange instance
            
        Returns:
            Validation result with approval status and adjustments
        """
        try:
            validation_result = {
                'approved': False,
                'adjusted_params': position_params.copy(),
                'risk_score': 0.0,
                'warnings': [],
                'blocking_issues': []
            }
            
            symbol = signal.get('symbol', 'BTCUSDT')
            leverage = position_params.get('leverage', 10)
            position_size = position_params.get('position_size_pct', 0.02)
            
            # Check emergency mode
            if self.emergency_mode:
                validation_result['blocking_issues'].append("Emergency mode active - no new trades")
                return validation_result
            
            # Daily loss limit check
            daily_loss_check = await self._check_daily_loss_limit(account_balance)
            if not daily_loss_check['passed']:
                validation_result['blocking_issues'].append(daily_loss_check['message'])
                return validation_result
            
            # Portfolio leverage exposure check
            leverage_check = self._check_portfolio_leverage(leverage, position_size, active_positions)
            if not leverage_check['passed']:
                if leverage_check['severity'] == 'blocking':
                    validation_result['blocking_issues'].append(leverage_check['message'])
                    return validation_result
                else:
                    validation_result['warnings'].append(leverage_check['message'])
                    # Adjust leverage if possible
                    validation_result['adjusted_params']['leverage'] = leverage_check.get('suggested_leverage', leverage)
            
            # High leverage position limit check
            high_lev_check = self._check_high_leverage_limits(leverage, active_positions)
            if not high_lev_check['passed']:
                validation_result['blocking_issues'].append(high_lev_check['message'])
                return validation_result
            
            # Correlation exposure check
            correlation_check = await self._check_correlation_exposure(symbol, position_size, active_positions, exchange)
            if not correlation_check['passed']:
                validation_result['warnings'].append(correlation_check['message'])
                # Reduce position size if needed
                validation_result['adjusted_params']['position_size_pct'] *= 0.8
            
            # Volatility risk assessment
            volatility_check = await self._assess_volatility_risk(symbol, leverage, exchange)
            validation_result['risk_score'] += volatility_check['risk_contribution']
            if volatility_check['warnings']:
                validation_result['warnings'].extend(volatility_check['warnings'])
            
            # Margin requirement check
            margin_check = self._check_margin_requirements(position_params, account_balance, active_positions)
            if not margin_check['passed']:
                validation_result['blocking_issues'].append(margin_check['message'])
                return validation_result
            
            # Time-based restrictions
            time_check = self._check_time_restrictions(leverage)
            if not time_check['passed']:
                validation_result['warnings'].append(time_check['message'])
                validation_result['adjusted_params']['leverage'] = min(leverage, 20)  # Reduce for off-hours
            
            # Calculate overall risk score (0-100)
            risk_components = [
                leverage / 50 * 30,  # Leverage component (30 points max)
                position_size / 0.05 * 20,  # Position size component (20 points max)  
                len(active_positions) / 5 * 15,  # Exposure component (15 points max)
                volatility_check['risk_contribution']  # Volatility component (35 points max)
            ]
            validation_result['risk_score'] = min(100, sum(risk_components))
            
            # Final approval decision
            if not validation_result['blocking_issues']:
                if validation_result['risk_score'] <= 75:  # Accept reasonable risk
                    validation_result['approved'] = True
                    logger.info(f"Trade approved for {symbol} with risk score: {validation_result['risk_score']:.1f}")
                else:
                    validation_result['blocking_issues'].append(f"Risk score too high: {validation_result['risk_score']:.1f}/100")
                    logger.warning(f"Trade rejected for {symbol} - high risk score: {validation_result['risk_score']:.1f}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in trade validation: {e}")
            return {
                'approved': False,
                'adjusted_params': position_params,
                'risk_score': 100.0,
                'warnings': [],
                'blocking_issues': ['Risk validation system error']
            }
    
    async def _check_daily_loss_limit(self, account_balance: float) -> Dict:
        """Check if daily loss limit would be exceeded"""
        try:
            current_date = datetime.now().date()
            
            # Reset daily tracking if new day
            if current_date != self.daily_start:
                self.daily_pnl = 0.0
                self.daily_trades = 0
                self.daily_start = current_date
            
            daily_loss_pct = abs(min(0, self.daily_pnl)) / account_balance
            
            if daily_loss_pct >= self.MAX_DAILY_LOSS:
                return {
                    'passed': False,
                    'message': f"Daily loss limit reached: {daily_loss_pct:.1%} of {self.MAX_DAILY_LOSS:.1%}"
                }
            elif daily_loss_pct >= self.MAX_DAILY_LOSS * 0.8:  # 80% of limit
                return {
                    'passed': True,
                    'message': f"Warning: Close to daily loss limit ({daily_loss_pct:.1%})"
                }
            
            return {'passed': True, 'message': 'Daily loss check passed'}
            
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return {'passed': False, 'message': 'Daily loss check failed'}
    
    def _check_portfolio_leverage(self, leverage: int, position_size: float, 
                                active_positions: Dict) -> Dict:
        """Check overall portfolio leverage exposure"""
        try:
            # Calculate current leverage exposure
            current_exposure = sum(
                pos.get('leverage', 1) * pos.get('position_size', 0.01) 
                for pos in active_positions.values()
            )
            
            # Add proposed position exposure
            new_exposure = current_exposure + (leverage * position_size)
            
            if new_exposure > self.MAX_PORTFOLIO_LEVERAGE:
                # Try to suggest a reduction
                max_additional = self.MAX_PORTFOLIO_LEVERAGE - current_exposure
                suggested_leverage = max(10, int(max_additional / position_size))
                
                if suggested_leverage >= 10:
                    return {
                        'passed': False,
                        'severity': 'warning',
                        'message': f"Portfolio leverage too high ({new_exposure:.1f}x), reducing to {suggested_leverage}x",
                        'suggested_leverage': suggested_leverage
                    }
                else:
                    return {
                        'passed': False,
                        'severity': 'blocking',
                        'message': f"Cannot add position - portfolio leverage limit exceeded ({new_exposure:.1f}x > {self.MAX_PORTFOLIO_LEVERAGE:.1f}x)"
                    }
            
            return {'passed': True, 'message': f'Portfolio leverage OK ({new_exposure:.1f}x)'}
            
        except Exception as e:
            logger.error(f"Error checking portfolio leverage: {e}")
            return {'passed': False, 'severity': 'blocking', 'message': 'Portfolio leverage check failed'}
    
    def _check_high_leverage_limits(self, leverage: int, active_positions: Dict) -> Dict:
        """Check limits on high leverage positions"""
        try:
            high_leverage_count = sum(
                1 for pos in active_positions.values() 
                if pos.get('leverage', 1) > 30
            )
            
            if leverage > 30 and high_leverage_count >= self.MAX_CONCURRENT_HIGH_LEVERAGE:
                return {
                    'passed': False,
                    'message': f"Too many high leverage positions ({high_leverage_count}/{self.MAX_CONCURRENT_HIGH_LEVERAGE})"
                }
            
            return {'passed': True, 'message': 'High leverage check passed'}
            
        except Exception as e:
            logger.error(f"Error checking high leverage limits: {e}")
            return {'passed': False, 'message': 'High leverage check failed'}
    
    async def _check_correlation_exposure(self, symbol: str, position_size: float,
                                        active_positions: Dict, exchange: Any) -> Dict:
        """Check for excessive correlation exposure"""
        try:
            if not active_positions:
                return {'passed': True, 'message': 'No correlation risk with empty portfolio'}
            
            # Simplified correlation check - group by major categories
            correlation_groups = {
                'major_crypto': ['BTCUSDT', 'ETHUSDT'],
                'layer1': ['SOLUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT'],
                'defi_ecosystem': ['LINKUSDT', 'AVAXUSDT'],
                'exchange_tokens': ['BNBUSDT'],
                'meme_coins': ['DOGEUSDT']
            }
            
            # Find which group the new symbol belongs to
            new_symbol_group = None
            for group, symbols in correlation_groups.items():
                if symbol in symbols:
                    new_symbol_group = group
                    break
            
            if not new_symbol_group:
                return {'passed': True, 'message': 'Symbol not in correlation groups'}
            
            # Calculate exposure to the same group
            group_exposure = sum(
                pos.get('position_size', 0.01) 
                for sym, pos in active_positions.items()
                if any(sym in symbols for group, symbols in correlation_groups.items() if group == new_symbol_group)
            )
            
            new_group_exposure = group_exposure + position_size
            
            if new_group_exposure > 0.10:  # 10% max exposure to correlated assets
                return {
                    'passed': False,
                    'message': f"High correlation exposure to {new_symbol_group}: {new_group_exposure:.1%}"
                }
            
            return {'passed': True, 'message': 'Correlation exposure acceptable'}
            
        except Exception as e:
            logger.error(f"Error checking correlation exposure: {e}")
            return {'passed': True, 'message': 'Correlation check skipped due to error'}
    
    async def _assess_volatility_risk(self, symbol: str, leverage: int, exchange: Any) -> Dict:
        """Assess volatility-based risk contribution"""
        try:
            if not exchange:
                return {'risk_contribution': 15, 'warnings': ['Cannot assess volatility - no exchange']}
            
            # Get volatility summary
            vol_summary = volatility_manager.get_volatility_summary(symbol)
            
            risk_contribution = 10  # Base risk
            warnings = []
            
            if vol_summary.get('status') == 'active':
                vol_status = vol_summary.get('overall_volatility', 'NORMAL')
                
                if vol_status == 'HIGH':
                    risk_contribution = 35
                    warnings.append(f"High volatility detected for {symbol}")
                elif vol_status == 'ELEVATED':
                    risk_contribution = 25
                    warnings.append(f"Elevated volatility for {symbol}")
                elif vol_status == 'LOW':
                    risk_contribution = 5
                    
                # Additional penalty for high leverage + high volatility
                if leverage > 25 and vol_status in ['HIGH', 'ELEVATED']:
                    risk_contribution += 10
                    warnings.append(f"High leverage ({leverage}x) + elevated volatility combination")
            
            return {
                'risk_contribution': risk_contribution,
                'warnings': warnings,
                'volatility_status': vol_summary.get('overall_volatility', 'UNKNOWN')
            }
            
        except Exception as e:
            logger.error(f"Error assessing volatility risk: {e}")
            return {'risk_contribution': 20, 'warnings': ['Volatility assessment failed']}
    
    def _check_margin_requirements(self, position_params: Dict, account_balance: float,
                                 active_positions: Dict) -> Dict:
        """Check if there's sufficient margin for the position"""
        try:
            leverage = position_params.get('leverage', 10)
            position_value = position_params.get('position_value', 0)
            margin_required = position_value / leverage
            
            # Calculate total margin currently used
            used_margin = sum(
                pos.get('position_value', 0) / pos.get('leverage', 1)
                for pos in active_positions.values()
            )
            
            total_margin_needed = used_margin + margin_required
            available_margin = account_balance * 0.8  # Use max 80% of balance as margin
            
            if total_margin_needed > available_margin:
                return {
                    'passed': False,
                    'message': f"Insufficient margin: need ${total_margin_needed:.0f}, have ${available_margin:.0f}"
                }
            elif total_margin_needed > available_margin * 0.9:  # 90% of available
                return {
                    'passed': True,
                    'message': f"Warning: High margin usage ({total_margin_needed/available_margin:.1%})"
                }
            
            return {'passed': True, 'message': 'Margin requirements OK'}
            
        except Exception as e:
            logger.error(f"Error checking margin requirements: {e}")
            return {'passed': False, 'message': 'Margin check failed'}
    
    def _check_time_restrictions(self, leverage: int) -> Dict:
        """Check time-based leverage restrictions"""
        try:
            current_hour = datetime.now().hour
            current_weekday = datetime.now().weekday()
            
            # Weekend restrictions
            if current_weekday >= 5:  # Saturday = 5, Sunday = 6
                if leverage > 25:
                    return {
                        'passed': False,
                        'message': "High leverage restricted on weekends"
                    }
            
            # Late night/early morning restrictions (11 PM - 6 AM)
            if current_hour >= 23 or current_hour <= 6:
                if leverage > 30:
                    return {
                        'passed': False,
                        'message': "Very high leverage restricted during off-hours"
                    }
            
            return {'passed': True, 'message': 'Time restrictions OK'}
            
        except Exception as e:
            logger.error(f"Error checking time restrictions: {e}")
            return {'passed': True, 'message': 'Time check skipped due to error'}
    
    async def monitor_position_risk(self, positions: Dict, account_balance: float,
                                  exchange: Any) -> Dict:
        """Monitor existing positions for risk violations"""
        try:
            risk_alerts = []
            emergency_actions = []
            total_unrealized_pnl = 0
            
            for symbol, position in positions.items():
                try:
                    # Get current price
                    ticker = await exchange.fetch_ticker(symbol)
                    current_price = ticker['last']
                    
                    # Calculate unrealized P&L
                    entry_price = position.get('entry_price', current_price)
                    leverage = position.get('leverage', 1)
                    position_size = position.get('position_size', 0.01)
                    side = position.get('side', 'BUY')
                    
                    if side == 'BUY':
                        price_change_pct = (current_price - entry_price) / entry_price
                    else:
                        price_change_pct = (entry_price - current_price) / entry_price
                    
                    leveraged_pnl_pct = price_change_pct * leverage
                    unrealized_pnl_usd = account_balance * position_size * leveraged_pnl_pct
                    total_unrealized_pnl += unrealized_pnl_usd
                    
                    # Check for liquidation risk
                    margin_ratio = 1 / leverage
                    if side == 'BUY':
                        liquidation_price = entry_price * (1 - margin_ratio + 0.01)  # 1% buffer
                        distance_to_liquidation = (current_price - liquidation_price) / current_price
                    else:
                        liquidation_price = entry_price * (1 + margin_ratio - 0.01)
                        distance_to_liquidation = (liquidation_price - current_price) / current_price
                    
                    # Risk level assessment
                    if distance_to_liquidation < 0.05:  # Within 5% of liquidation
                        emergency_actions.append({
                            'symbol': symbol,
                            'action': 'EMERGENCY_CLOSE',
                            'reason': f'Within {distance_to_liquidation:.1%} of liquidation',
                            'priority': 'CRITICAL'
                        })
                    elif distance_to_liquidation < 0.15:  # Within 15% of liquidation
                        risk_alerts.append({
                            'symbol': symbol,
                            'level': 'HIGH',
                            'message': f'Close to liquidation ({distance_to_liquidation:.1%} away)',
                            'suggested_action': 'ADD_MARGIN_OR_CLOSE'
                        })
                    elif leveraged_pnl_pct < -0.50:  # 50% loss
                        risk_alerts.append({
                            'symbol': symbol,
                            'level': 'MEDIUM',
                            'message': f'Large unrealized loss ({leveraged_pnl_pct:.1%})',
                            'suggested_action': 'CONSIDER_CLOSING'
                        })
                    
                except Exception as e:
                    logger.error(f"Error monitoring position {symbol}: {e}")
                    continue
            
            # Check total portfolio risk
            total_pnl_pct = total_unrealized_pnl / account_balance
            
            if total_pnl_pct < -self.EMERGENCY_STOP_LOSS:
                emergency_actions.append({
                    'symbol': 'PORTFOLIO',
                    'action': 'EMERGENCY_STOP_ALL',
                    'reason': f'Portfolio loss exceeds emergency threshold ({total_pnl_pct:.1%})',
                    'priority': 'CRITICAL'
                })
                self.emergency_mode = True
            elif total_pnl_pct < -0.10:  # 10% portfolio loss
                risk_alerts.append({
                    'symbol': 'PORTFOLIO',
                    'level': 'HIGH',
                    'message': f'Portfolio down {total_pnl_pct:.1%}',
                    'suggested_action': 'REDUCE_RISK'
                })
            
            return {
                'risk_alerts': risk_alerts,
                'emergency_actions': emergency_actions,
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_pnl_pct': total_pnl_pct,
                'emergency_mode': self.emergency_mode
            }
            
        except Exception as e:
            logger.error(f"Error monitoring position risk: {e}")
            return {
                'risk_alerts': [{'level': 'ERROR', 'message': 'Risk monitoring system error'}],
                'emergency_actions': [],
                'total_unrealized_pnl': 0,
                'total_pnl_pct': 0,
                'emergency_mode': False
            }
    
    def update_daily_pnl(self, trade_pnl: float):
        """Update daily P&L tracking"""
        try:
            current_date = datetime.now().date()
            
            # Reset daily tracking if new day
            if current_date != self.daily_start:
                self.daily_pnl = 0.0
                self.daily_trades = 0
                self.daily_start = current_date
                self.emergency_mode = False  # Reset emergency mode daily
            
            self.daily_pnl += trade_pnl
            self.daily_trades += 1
            
            logger.info(f"Daily P&L updated: ${self.daily_pnl:.2f} ({self.daily_trades} trades)")
            
        except Exception as e:
            logger.error(f"Error updating daily PnL: {e}")
    
    def get_risk_summary(self) -> Dict:
        """Get current risk status summary"""
        try:
            current_date = datetime.now().date()
            
            # Reset if new day
            if current_date != self.daily_start:
                self.daily_pnl = 0.0
                self.daily_trades = 0
                self.daily_start = current_date
            
            return {
                'emergency_mode': self.emergency_mode,
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades,
                'daily_loss_limit': self.MAX_DAILY_LOSS,
                'daily_loss_used': abs(min(0, self.daily_pnl)) / 10000,  # Assume 10k balance for percentage
                'max_portfolio_leverage': self.MAX_PORTFOLIO_LEVERAGE,
                'max_high_leverage_positions': self.MAX_CONCURRENT_HIGH_LEVERAGE,
                'circuit_breakers_active': len(self.circuit_breakers),
                'risk_violations': len(self.risk_violations)
            }
            
        except Exception as e:
            logger.error(f"Error getting risk summary: {e}")
            return {'error': 'Risk summary unavailable'}

# Global instance
enhanced_risk_manager = EnhancedRiskManager()