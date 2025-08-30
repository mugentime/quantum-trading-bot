"""
Advanced Risk Management System
Implements trailing stops, dynamic position sizing, and portfolio heat mapping
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .config.settings import config

logger = logging.getLogger(__name__)

class AdvancedRiskManager:
    """Advanced risk management with adaptive controls and trailing stops"""
    
    def __init__(self):
        # Risk thresholds
        self.max_portfolio_heat = 0.15  # 15% max portfolio heat
        self.max_symbol_exposure = 0.08  # 8% max exposure per symbol
        self.max_correlation_exposure = 0.20  # 20% max for correlated positions
        
        # Trailing stop parameters
        self.trailing_stop_atr_multiplier = 2.0
        self.min_trailing_profit = 0.005  # 0.5% minimum profit before trailing
        self.trailing_step_pct = 0.002    # 0.2% trailing step size
        
        # Performance tracking
        self.recent_performance = []
        self.position_tracking = {}
        self.heat_map = {}
        self.stop_adjustments = {}
        
    async def validate_advanced_trade_risk(self, signal: Dict, account_balance: float,
                                         proposed_leverage: int, proposed_position_size: float,
                                         current_positions: Dict = None, exchange = None) -> Dict:
        """
        Advanced trade risk validation with multiple risk factors
        
        Args:
            signal: Trading signal data
            account_balance: Current balance
            proposed_leverage: Proposed leverage multiplier
            proposed_position_size: Proposed position size (as percentage)
            current_positions: Currently open positions
            exchange: Exchange interface
            
        Returns:
            Comprehensive risk validation result
        """
        try:
            current_positions = current_positions or {}
            
            # Basic risk validation
            basic_validation = await self._basic_risk_validation(
                signal, account_balance, proposed_leverage, proposed_position_size
            )
            
            if not basic_validation['approved']:
                return basic_validation
            
            # Portfolio heat analysis
            heat_analysis = await self._analyze_portfolio_heat(
                signal, proposed_position_size, proposed_leverage, 
                current_positions, account_balance, exchange
            )
            
            # Correlation exposure analysis
            correlation_analysis = await self._analyze_correlation_exposure(
                signal, proposed_position_size, current_positions
            )
            
            # Performance-based adjustments
            performance_adjustment = self._analyze_performance_based_risk()
            
            # Market regime risk adjustment
            regime_adjustment = await self._analyze_regime_risk(exchange)
            
            # Combine all risk factors
            combined_assessment = self._combine_risk_assessments(
                basic_validation, heat_analysis, correlation_analysis,
                performance_adjustment, regime_adjustment
            )
            
            # Generate final recommendation
            final_recommendation = self._generate_final_risk_recommendation(
                combined_assessment, signal, account_balance
            )
            
            logger.info(f"Advanced risk validation for {signal.get('symbol', 'UNKNOWN')}: "
                       f"approved={final_recommendation['approved']}, "
                       f"risk_score={final_recommendation['risk_score']:.2f}")
            
            return final_recommendation
            
        except Exception as e:
            logger.error(f"Error in advanced risk validation: {e}")
            return {
                'approved': False,
                'risk_score': 1.0,
                'warnings': [f"Risk validation error: {e}"],
                'adjustments': {},
                'reasoning': "Error in risk analysis - trade rejected for safety"
            }
    
    async def _basic_risk_validation(self, signal: Dict, account_balance: float,
                                   leverage: int, position_size: float) -> Dict:
        """Basic risk validation checks"""
        try:
            warnings = []
            adjustments = {}
            
            # Check leverage bounds
            if leverage > config.MAX_LEVERAGE:
                warnings.append(f"Leverage {leverage}x exceeds maximum {config.MAX_LEVERAGE}x")
                adjustments['leverage'] = config.MAX_LEVERAGE
                leverage = config.MAX_LEVERAGE
            
            # Check position size bounds
            max_position = config.MAX_POSITION_RISK / leverage
            if position_size > max_position:
                warnings.append(f"Position size {position_size:.1%} too large for leverage {leverage}x")
                adjustments['position_size'] = max_position
                position_size = max_position
            
            # Check minimum signal strength
            deviation = signal.get('deviation', 0.0)
            if deviation < 0.10:
                warnings.append(f"Signal strength too weak: {deviation:.3f}")
                return {
                    'approved': False,
                    'risk_score': 0.8,
                    'warnings': warnings,
                    'adjustments': adjustments,
                    'reasoning': "Signal strength below minimum threshold"
                }
            
            return {
                'approved': True,
                'risk_score': 0.2,
                'warnings': warnings,
                'adjustments': adjustments,
                'reasoning': "Basic risk checks passed"
            }
            
        except Exception as e:
            logger.error(f"Error in basic risk validation: {e}")
            return {'approved': False, 'risk_score': 1.0, 'warnings': [str(e)], 
                   'adjustments': {}, 'reasoning': "Basic validation error"}
    
    async def _analyze_portfolio_heat(self, signal: Dict, position_size: float,
                                    leverage: int, current_positions: Dict,
                                    account_balance: float, exchange) -> Dict:
        """Analyze portfolio heat and exposure concentration"""
        try:
            symbol = signal.get('symbol', 'UNKNOWN')
            
            # Calculate current portfolio heat
            current_heat = 0.0
            symbol_exposure = {}
            
            for pos_symbol, position in current_positions.items():
                position_value = position.get('quantity', 0) * position.get('entry_price', 0)
                position_risk = position_value / account_balance
                current_heat += position_risk
                
                if pos_symbol in symbol_exposure:
                    symbol_exposure[pos_symbol] += position_risk
                else:
                    symbol_exposure[pos_symbol] = position_risk
            
            # Calculate new position heat
            new_position_value = account_balance * position_size * leverage
            new_position_heat = new_position_value / account_balance
            
            # Check portfolio heat limit
            projected_heat = current_heat + new_position_heat
            
            warnings = []
            adjustments = {}
            risk_score = 0.0
            
            if projected_heat > self.max_portfolio_heat:
                warnings.append(f"Portfolio heat would exceed {self.max_portfolio_heat:.1%}")
                max_allowed_size = (self.max_portfolio_heat - current_heat) / leverage
                adjustments['position_size'] = max(0.005, max_allowed_size)  # Min 0.5%
                risk_score += 0.3
            
            # Check symbol concentration
            current_symbol_exposure = symbol_exposure.get(symbol, 0.0)
            projected_symbol_exposure = current_symbol_exposure + new_position_heat
            
            if projected_symbol_exposure > self.max_symbol_exposure:
                warnings.append(f"Symbol exposure would exceed {self.max_symbol_exposure:.1%}")
                max_symbol_size = (self.max_symbol_exposure - current_symbol_exposure) / leverage
                if 'position_size' in adjustments:
                    adjustments['position_size'] = min(adjustments['position_size'], max_symbol_size)
                else:
                    adjustments['position_size'] = max(0.005, max_symbol_size)
                risk_score += 0.2
            
            self.heat_map[symbol] = {
                'current_heat': current_heat,
                'projected_heat': projected_heat,
                'symbol_exposure': projected_symbol_exposure,
                'timestamp': datetime.now()
            }
            
            return {
                'approved': projected_heat <= self.max_portfolio_heat and 
                          projected_symbol_exposure <= self.max_symbol_exposure,
                'risk_score': min(1.0, risk_score),
                'warnings': warnings,
                'adjustments': adjustments,
                'heat_data': {
                    'current_portfolio_heat': current_heat,
                    'projected_portfolio_heat': projected_heat,
                    'symbol_exposure': projected_symbol_exposure
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio heat: {e}")
            return {'approved': True, 'risk_score': 0.1, 'warnings': [str(e)], 
                   'adjustments': {}, 'heat_data': {}}
    
    async def _analyze_correlation_exposure(self, signal: Dict, position_size: float,
                                          current_positions: Dict) -> Dict:
        """Analyze correlation exposure risk"""
        try:
            symbol = signal.get('symbol', 'UNKNOWN')
            
            # Define correlation groups
            correlation_groups = {
                'major_alts': ['ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT'],
                'defi_tokens': ['SOLUSDT', 'AVAXUSDT', 'MATICUSDT'],
                'layer1s': ['ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 'DOTUSDT']
            }
            
            # Find which group this symbol belongs to
            symbol_groups = []
            for group_name, symbols in correlation_groups.items():
                if symbol in symbols:
                    symbol_groups.append(group_name)
            
            if not symbol_groups:
                return {'approved': True, 'risk_score': 0.0, 'warnings': [], 'adjustments': {}}
            
            # Calculate current exposure in each group
            group_exposures = {group: 0.0 for group in correlation_groups.keys()}
            
            for pos_symbol, position in current_positions.items():
                position_exposure = position.get('quantity', 0) * position.get('entry_price', 0)
                
                for group_name, symbols in correlation_groups.items():
                    if pos_symbol in symbols:
                        group_exposures[group_name] += position_exposure
            
            # Check correlation exposure limits
            warnings = []
            adjustments = {}
            risk_score = 0.0
            
            for group_name in symbol_groups:
                current_group_exposure = group_exposures[group_name]
                # Assuming account balance for calculation
                current_group_pct = current_group_exposure / 10000  # Placeholder
                
                if current_group_pct > self.max_correlation_exposure:
                    warnings.append(f"High correlation exposure in {group_name}: {current_group_pct:.1%}")
                    risk_score += 0.2
            
            return {
                'approved': risk_score < 0.5,
                'risk_score': min(1.0, risk_score),
                'warnings': warnings,
                'adjustments': adjustments,
                'correlation_data': {
                    'symbol_groups': symbol_groups,
                    'group_exposures': group_exposures
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlation exposure: {e}")
            return {'approved': True, 'risk_score': 0.0, 'warnings': [str(e)], 'adjustments': {}}
    
    def _analyze_performance_based_risk(self) -> Dict:
        """Adjust risk based on recent performance"""
        try:
            if len(self.recent_performance) < 5:
                return {'approved': True, 'risk_score': 0.0, 'warnings': [], 'adjustments': {}}
            
            # Calculate recent win rate
            recent_wins = sum(1 for perf in self.recent_performance[-10:] if perf.get('pnl', 0) > 0)
            recent_trades = len(self.recent_performance[-10:])
            win_rate = recent_wins / recent_trades if recent_trades > 0 else 0.5
            
            # Calculate recent PnL
            recent_pnl = sum(perf.get('pnl', 0) for perf in self.recent_performance[-5:])
            
            warnings = []
            adjustments = {}
            risk_score = 0.0
            
            # Reduce risk after poor performance
            if win_rate < 0.3:
                warnings.append(f"Low recent win rate: {win_rate:.1%}")
                adjustments['position_size_multiplier'] = 0.7
                risk_score += 0.3
            
            if recent_pnl < -0.05:  # More than 5% loss recently
                warnings.append(f"Recent losses detected: {recent_pnl:.1%}")
                adjustments['leverage_multiplier'] = 0.8
                risk_score += 0.2
            
            # Increase risk after good performance (but cap it)
            if win_rate > 0.7 and recent_pnl > 0.03:
                adjustments['position_size_multiplier'] = min(1.2, 
                    adjustments.get('position_size_multiplier', 1.0) * 1.1)
            
            return {
                'approved': True,
                'risk_score': min(1.0, risk_score),
                'warnings': warnings,
                'adjustments': adjustments,
                'performance_data': {
                    'recent_win_rate': win_rate,
                    'recent_pnl': recent_pnl,
                    'trades_analyzed': recent_trades
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance-based risk: {e}")
            return {'approved': True, 'risk_score': 0.0, 'warnings': [str(e)], 'adjustments': {}}
    
    async def _analyze_regime_risk(self, exchange) -> Dict:
        """Analyze risk based on current market regime"""
        try:
            if not exchange:
                return {'approved': True, 'risk_score': 0.0, 'warnings': [], 'adjustments': {}}
            
            # Import regime detector
            from .market_regime_detector import market_regime_detector
            
            # Get current regime (simplified - would use cached data in real implementation)
            current_regime = market_regime_detector.get_current_regime()
            
            if not current_regime:
                return {'approved': True, 'risk_score': 0.0, 'warnings': [], 'adjustments': {}}
            
            volatility_regime = current_regime.get('volatility_regime', 'normal')
            trend_regime = current_regime.get('trend_regime', 'sideways')
            
            warnings = []
            adjustments = {}
            risk_score = 0.0
            
            # High volatility regime adjustments
            if volatility_regime in ['high', 'extreme']:
                warnings.append(f"High volatility regime detected: {volatility_regime}")
                adjustments['leverage_multiplier'] = 0.8
                adjustments['position_size_multiplier'] = 0.9
                risk_score += 0.1
            
            # Sideways market with high volatility is risky
            if trend_regime == 'sideways' and volatility_regime in ['high', 'extreme']:
                warnings.append("Dangerous combination: sideways market with high volatility")
                adjustments['leverage_multiplier'] = adjustments.get('leverage_multiplier', 1.0) * 0.7
                risk_score += 0.2
            
            return {
                'approved': True,
                'risk_score': min(1.0, risk_score),
                'warnings': warnings,
                'adjustments': adjustments,
                'regime_data': {
                    'trend_regime': trend_regime,
                    'volatility_regime': volatility_regime
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing regime risk: {e}")
            return {'approved': True, 'risk_score': 0.0, 'warnings': [str(e)], 'adjustments': {}}
    
    def _combine_risk_assessments(self, *assessments) -> Dict:
        """Combine multiple risk assessment results"""
        try:
            combined_warnings = []
            combined_adjustments = {}
            total_risk_score = 0.0
            approved_count = 0
            
            for assessment in assessments:
                if not assessment.get('approved', False):
                    return {
                        'approved': False,
                        'risk_score': 1.0,
                        'warnings': assessment.get('warnings', []),
                        'adjustments': assessment.get('adjustments', {}),
                        'reasoning': assessment.get('reasoning', 'Risk assessment failed')
                    }
                
                approved_count += 1
                combined_warnings.extend(assessment.get('warnings', []))
                total_risk_score += assessment.get('risk_score', 0.0)
                
                # Combine adjustments (multiply multipliers, take minimum for sizes)
                for key, value in assessment.get('adjustments', {}).items():
                    if key.endswith('_multiplier'):
                        combined_adjustments[key] = combined_adjustments.get(key, 1.0) * value
                    else:
                        if key in combined_adjustments:
                            combined_adjustments[key] = min(combined_adjustments[key], value)
                        else:
                            combined_adjustments[key] = value
            
            avg_risk_score = total_risk_score / len(assessments) if assessments else 0.0
            
            return {
                'approved': True,
                'risk_score': min(1.0, avg_risk_score),
                'warnings': combined_warnings,
                'adjustments': combined_adjustments,
                'assessments_passed': approved_count
            }
            
        except Exception as e:
            logger.error(f"Error combining risk assessments: {e}")
            return {'approved': False, 'risk_score': 1.0, 'warnings': [str(e)], 
                   'adjustments': {}, 'reasoning': "Error combining assessments"}
    
    def _generate_final_risk_recommendation(self, combined_assessment: Dict,
                                          signal: Dict, account_balance: float) -> Dict:
        """Generate final risk recommendation with adjusted parameters"""
        try:
            if not combined_assessment.get('approved', False):
                return combined_assessment
            
            # Apply adjustments to original signal
            adjustments = combined_assessment.get('adjustments', {})
            
            # Calculate final leverage
            original_leverage = signal.get('suggested_leverage', config.DEFAULT_LEVERAGE)
            leverage_multiplier = adjustments.get('leverage_multiplier', 1.0)
            final_leverage = int(original_leverage * leverage_multiplier)
            final_leverage = max(config.MIN_LEVERAGE, min(config.MAX_LEVERAGE, final_leverage))
            
            # Calculate final position size
            original_position_size = signal.get('suggested_position_size', config.RISK_PER_TRADE)
            position_size_multiplier = adjustments.get('position_size_multiplier', 1.0)
            
            if 'position_size' in adjustments:
                final_position_size = adjustments['position_size']
            else:
                final_position_size = original_position_size * position_size_multiplier
            
            final_position_size = max(0.005, min(0.05, final_position_size))  # 0.5% to 5%
            
            # Calculate risk metrics
            position_value = account_balance * final_position_size * final_leverage
            risk_amount = position_value * 0.02  # Assume 2% stop loss
            
            return {
                'approved': True,
                'risk_score': combined_assessment.get('risk_score', 0.0),
                'warnings': combined_assessment.get('warnings', []),
                'adjustments': {
                    'leverage': final_leverage,
                    'position_size': final_position_size,
                    'position_value': position_value,
                    'risk_amount': risk_amount,
                    'adjustments_applied': adjustments
                },
                'reasoning': f"Risk validated with {len(combined_assessment.get('warnings', []))} warnings",
                'final_parameters': {
                    'leverage': final_leverage,
                    'position_size_pct': final_position_size * 100,
                    'risk_amount_usd': risk_amount
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating final recommendation: {e}")
            return {'approved': False, 'risk_score': 1.0, 'warnings': [str(e)], 
                   'adjustments': {}, 'reasoning': "Error in final recommendation"}
    
    async def setup_trailing_stop(self, position: Dict, current_price: float,
                                 exchange = None) -> Dict:
        """Setup trailing stop for a position"""
        try:
            if not exchange:
                logger.error("Exchange interface required for trailing stop")
                return {}
            
            symbol = position.get('symbol', 'UNKNOWN')
            side = position.get('side', 'BUY')
            entry_price = position.get('entry_price', current_price)
            
            # Calculate ATR for trailing distance
            from .dynamic_exit_manager import dynamic_exit_manager
            atr_data = await dynamic_exit_manager._calculate_atr(symbol, exchange)
            
            if not atr_data:
                logger.warning(f"No ATR data for trailing stop on {symbol}")
                return {}
            
            current_atr = atr_data['current_atr']
            trailing_distance = current_atr * self.trailing_stop_atr_multiplier
            
            # Calculate initial trailing stop
            if side == 'BUY':
                current_profit_pct = (current_price - entry_price) / entry_price
                initial_stop = current_price - trailing_distance
            else:  # SELL
                current_profit_pct = (entry_price - current_price) / entry_price
                initial_stop = current_price + trailing_distance
            
            # Only setup trailing if minimum profit reached
            if current_profit_pct < self.min_trailing_profit:
                return {
                    'trailing_active': False,
                    'reason': f"Insufficient profit for trailing: {current_profit_pct:.2%}",
                    'min_profit_required': self.min_trailing_profit
                }
            
            trailing_data = {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'current_price': current_price,
                'trailing_distance': trailing_distance,
                'current_stop': initial_stop,
                'highest_price': current_price if side == 'BUY' else None,
                'lowest_price': current_price if side == 'SELL' else None,
                'trailing_active': True,
                'setup_time': datetime.now(),
                'last_updated': datetime.now()
            }
            
            # Store trailing stop data
            position_key = f"{symbol}_{position.get('order_id', 'unknown')}"
            self.stop_adjustments[position_key] = trailing_data
            
            logger.info(f"Trailing stop setup for {symbol}: distance={trailing_distance:.4f}, "
                       f"initial_stop={initial_stop:.4f}")
            
            return trailing_data
            
        except Exception as e:
            logger.error(f"Error setting up trailing stop: {e}")
            return {}
    
    async def update_trailing_stop(self, position_key: str, current_price: float) -> Dict:
        """Update trailing stop based on current price"""
        try:
            if position_key not in self.stop_adjustments:
                return {'updated': False, 'reason': 'No trailing stop data found'}
            
            trailing_data = self.stop_adjustments[position_key]
            side = trailing_data['side']
            current_stop = trailing_data['current_stop']
            trailing_distance = trailing_data['trailing_distance']
            
            updated = False
            new_stop = current_stop
            
            if side == 'BUY':
                # Update highest price
                if current_price > trailing_data.get('highest_price', 0):
                    trailing_data['highest_price'] = current_price
                    new_stop = current_price - trailing_distance
                    
                    # Only update if new stop is higher (trailing up)
                    if new_stop > current_stop:
                        trailing_data['current_stop'] = new_stop
                        updated = True
            
            else:  # SELL
                # Update lowest price
                if current_price < trailing_data.get('lowest_price', float('inf')):
                    trailing_data['lowest_price'] = current_price
                    new_stop = current_price + trailing_distance
                    
                    # Only update if new stop is lower (trailing down)
                    if new_stop < current_stop:
                        trailing_data['current_stop'] = new_stop
                        updated = True
            
            if updated:
                trailing_data['last_updated'] = datetime.now()
                trailing_data['current_price'] = current_price
                
                logger.info(f"Trailing stop updated for {trailing_data['symbol']}: "
                           f"new_stop={new_stop:.4f}, current_price={current_price:.4f}")
            
            return {
                'updated': updated,
                'current_stop': trailing_data['current_stop'],
                'current_price': current_price,
                'trailing_data': trailing_data
            }
            
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}")
            return {'updated': False, 'reason': str(e)}
    
    def add_performance_record(self, trade_result: Dict):
        """Add trade result to performance tracking"""
        try:
            self.recent_performance.append({
                'timestamp': datetime.now(),
                'symbol': trade_result.get('symbol'),
                'pnl': trade_result.get('pnl_usd', 0) / 10000,  # Normalize to portfolio percentage
                'pnl_pct': trade_result.get('pnl_pct', 0),
                'exit_reason': trade_result.get('exit_reason'),
                'duration_minutes': trade_result.get('duration_minutes', 0)
            })
            
            # Keep only recent records
            if len(self.recent_performance) > 50:
                self.recent_performance = self.recent_performance[-50:]
                
        except Exception as e:
            logger.error(f"Error adding performance record: {e}")
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk management metrics"""
        try:
            return {
                'portfolio_heat_limit': self.max_portfolio_heat,
                'symbol_exposure_limit': self.max_symbol_exposure,
                'correlation_exposure_limit': self.max_correlation_exposure,
                'active_trailing_stops': len(self.stop_adjustments),
                'recent_performance_records': len(self.recent_performance),
                'heat_map_entries': len(self.heat_map),
                'trailing_parameters': {
                    'atr_multiplier': self.trailing_stop_atr_multiplier,
                    'min_profit_required': self.min_trailing_profit,
                    'trailing_step': self.trailing_step_pct
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {}

# Global instance
advanced_risk_manager = AdvancedRiskManager()