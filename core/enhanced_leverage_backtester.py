"""
Enhanced Leverage Backtester
Tests leverage strategies against historical data with advanced risk metrics
"""
import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import json
from .enhanced_leverage_config import enhanced_leverage_config
from .enhanced_position_manager import enhanced_position_manager
from .enhanced_risk_manager import enhanced_risk_manager

logger = logging.getLogger(__name__)

class EnhancedLeverageBacktester:
    """Advanced backtesting for leverage optimization strategies"""
    
    def __init__(self):
        self.results = {}
        self.equity_curve = []
        self.max_leverage_used = {}
        self.liquidation_events = []
        
    async def run_leverage_optimization_backtest(self, symbols: List[str], 
                                               historical_data: Dict,
                                               initial_balance: float = 10000,
                                               test_period_days: int = 30) -> Dict:
        """
        Run comprehensive leverage optimization backtest
        
        Args:
            symbols: List of trading pairs to test
            historical_data: Historical OHLCV data for each symbol
            initial_balance: Starting balance for backtest
            test_period_days: Period to test over
            
        Returns:
            Comprehensive backtest results with leverage analysis
        """
        try:
            logger.info(f"Starting leverage optimization backtest for {len(symbols)} pairs")
            
            # Initialize backtest state
            current_balance = initial_balance
            positions = {}
            trade_history = []
            daily_pnl = []
            leverage_usage_history = []
            risk_violations = []
            
            # Get date range
            start_date = datetime.now() - timedelta(days=test_period_days)
            end_date = datetime.now()
            
            # Main backtest loop
            current_date = start_date
            while current_date <= end_date:
                try:
                    daily_trades = 0
                    daily_start_balance = current_balance
                    
                    # Process each symbol
                    for symbol in symbols:
                        if symbol not in historical_data:
                            continue
                            
                        # Get market data for current date
                        market_data = self._get_market_data_for_date(
                            historical_data[symbol], current_date
                        )
                        
                        if not market_data:
                            continue
                        
                        # Generate signals (simplified for backtest)
                        signals = self._generate_backtest_signals(symbol, market_data)
                        
                        for signal in signals:
                            # Calculate optimal position parameters using enhanced system
                            position_params = await self._calculate_enhanced_position_params(
                                signal, current_balance, positions, market_data
                            )
                            
                            # Risk validation
                            risk_validation = await enhanced_risk_manager.validate_trade_entry(
                                signal, position_params, current_balance, positions, None
                            )
                            
                            if not risk_validation['approved']:
                                risk_violations.append({
                                    'date': current_date,
                                    'symbol': symbol,
                                    'reason': risk_validation['blocking_issues']
                                })
                                continue
                            
                            # Execute trade
                            trade_result = await self._execute_backtest_trade(
                                signal, risk_validation['adjusted_params'], 
                                current_balance, market_data
                            )
                            
                            if trade_result:
                                trade_history.append(trade_result)
                                current_balance += trade_result['pnl_usd']
                                daily_trades += 1
                                
                                # Track leverage usage
                                leverage_usage_history.append({
                                    'date': current_date,
                                    'symbol': symbol,
                                    'leverage': trade_result['leverage'],
                                    'position_size': trade_result['position_size'],
                                    'pnl_pct': trade_result['pnl_pct']
                                })
                                
                                # Update risk manager
                                enhanced_risk_manager.update_daily_pnl(trade_result['pnl_usd'])
                    
                    # Record daily performance
                    daily_pnl.append({
                        'date': current_date,
                        'balance': current_balance,
                        'daily_return': (current_balance - daily_start_balance) / daily_start_balance,
                        'trades': daily_trades
                    })
                    
                    # Check for liquidation events
                    if current_balance < initial_balance * 0.2:  # 80% drawdown = liquidation
                        self.liquidation_events.append({
                            'date': current_date,
                            'remaining_balance': current_balance,
                            'drawdown': (initial_balance - current_balance) / initial_balance
                        })
                        logger.warning(f"Liquidation event detected on {current_date}: {current_balance:.2f}")
                        break
                    
                    current_date += timedelta(days=1)
                    
                except Exception as e:
                    logger.error(f"Error processing date {current_date}: {e}")
                    current_date += timedelta(days=1)
                    continue
            
            # Calculate comprehensive results
            results = await self._calculate_enhanced_backtest_results(
                trade_history, daily_pnl, leverage_usage_history, 
                risk_violations, initial_balance, current_balance
            )
            
            logger.info(f"Backtest completed: {results['total_return_pct']:.2f}% return, "
                       f"{results['max_leverage_used']:.1f}x max leverage")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in leverage optimization backtest: {e}")
            return self._get_fallback_results(initial_balance)
    
    async def _calculate_enhanced_position_params(self, signal: Dict, balance: float,
                                                positions: Dict, market_data: Dict) -> Dict:
        """Calculate position parameters using enhanced leverage system"""
        try:
            symbol = signal['symbol']
            
            # Get recent performance (simplified for backtest)
            recent_performance = {
                'win_rate': 0.6,  # Assume 60% win rate
                'return': 0.05,   # Assume 5% average return
                'trades': 10
            }
            
            # Market conditions (simplified)
            market_conditions = ['normal', 'asian_session']  # Default conditions
            
            # Calculate optimal leverage
            optimal_leverage, adjustments = enhanced_leverage_config.calculate_dynamic_leverage(
                symbol=symbol,
                signal_strength=signal.get('deviation', 0.20),
                recent_performance=recent_performance,
                market_conditions=market_conditions,
                account_balance=balance
            )
            
            # Calculate position size
            position_size = enhanced_leverage_config.get_position_size_adjustment(
                optimal_leverage, signal.get('deviation', 0.20), balance
            )
            
            # Calculate stops and targets
            base_stop = 0.02
            base_target = 0.04
            
            # Adjust for leverage
            adjusted_stop = base_stop * min(1.0, 20.0 / optimal_leverage)
            adjusted_target = base_target * (1 + signal.get('deviation', 0.20))
            
            return {
                'leverage': optimal_leverage,
                'position_size_pct': position_size,
                'position_value': balance * position_size,
                'stop_loss_pct': adjusted_stop,
                'take_profit_pct': adjusted_target,
                'leverage_adjustments': adjustments
            }
            
        except Exception as e:
            logger.error(f"Error calculating enhanced position params: {e}")
            return {
                'leverage': 15,
                'position_size_pct': 0.02,
                'position_value': balance * 0.02,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'leverage_adjustments': {}
            }
    
    def _generate_backtest_signals(self, symbol: str, market_data: Dict) -> List[Dict]:
        """Generate trading signals for backtest (simplified)"""
        try:
            signals = []
            
            # Simulate correlation-based signals
            if np.random.random() < 0.3:  # 30% chance of signal
                deviation = np.random.uniform(0.10, 0.50)  # Random deviation
                correlation = np.random.uniform(0.3, 0.9)   # Random correlation
                
                signals.append({
                    'symbol': symbol,
                    'side': np.random.choice(['BUY', 'SELL']),
                    'deviation': deviation,
                    'correlation': correlation,
                    'confidence': min(1.0, deviation * 2),
                    'entry_price': market_data.get('close', 100)
                })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating backtest signals: {e}")
            return []
    
    def _get_market_data_for_date(self, historical_data: List, date: datetime) -> Dict:
        """Extract market data for specific date"""
        try:
            # Find closest data point to the date
            target_timestamp = date.timestamp() * 1000  # Convert to milliseconds
            
            closest_data = None
            min_diff = float('inf')
            
            for data_point in historical_data:
                timestamp = data_point[0]  # Assuming [timestamp, open, high, low, close, volume]
                diff = abs(timestamp - target_timestamp)
                
                if diff < min_diff:
                    min_diff = diff
                    closest_data = data_point
            
            if closest_data:
                return {
                    'timestamp': closest_data[0],
                    'open': closest_data[1],
                    'high': closest_data[2],
                    'low': closest_data[3],
                    'close': closest_data[4],
                    'volume': closest_data[5]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting market data for date: {e}")
            return None
    
    async def _execute_backtest_trade(self, signal: Dict, position_params: Dict,
                                    balance: float, market_data: Dict) -> Optional[Dict]:
        """Execute a trade in the backtest"""
        try:
            symbol = signal['symbol']
            side = signal['side']
            leverage = position_params['leverage']
            position_size = position_params['position_size_pct']
            stop_loss = position_params['stop_loss_pct']
            take_profit = position_params['take_profit_pct']
            
            entry_price = market_data['close']
            position_value = balance * position_size
            
            # Simulate trade outcome based on random price movement
            # In real backtest, this would use actual historical price data
            price_move_pct = np.random.normal(0, 0.03)  # 3% daily volatility
            
            # Apply directional bias based on signal
            if side == 'BUY':
                exit_price = entry_price * (1 + price_move_pct)
                price_change_pct = (exit_price - entry_price) / entry_price
            else:
                exit_price = entry_price * (1 + price_move_pct)
                price_change_pct = (entry_price - exit_price) / entry_price
            
            # Check if stop loss or take profit hit
            exit_reason = 'TIME_EXIT'
            if abs(price_change_pct) >= stop_loss:
                if price_change_pct < 0:
                    price_change_pct = -stop_loss
                    exit_reason = 'STOP_LOSS'
                elif price_change_pct >= take_profit:
                    price_change_pct = take_profit
                    exit_reason = 'TAKE_PROFIT'
            
            # Apply leverage
            leveraged_pnl_pct = price_change_pct * leverage
            pnl_usd = position_value * leveraged_pnl_pct
            
            # Check for liquidation
            if leveraged_pnl_pct <= -0.9:  # 90% loss = liquidation
                leveraged_pnl_pct = -0.9
                pnl_usd = position_value * -0.9
                exit_reason = 'LIQUIDATION'
                
                self.liquidation_events.append({
                    'symbol': symbol,
                    'leverage': leverage,
                    'loss_pct': 90,
                    'timestamp': market_data['timestamp']
                })
            
            return {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'leverage': leverage,
                'position_size': position_size,
                'position_value': position_value,
                'pnl_pct': leveraged_pnl_pct * 100,  # Convert to percentage
                'pnl_usd': pnl_usd,
                'exit_reason': exit_reason,
                'timestamp': market_data['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error executing backtest trade: {e}")
            return None
    
    async def _calculate_enhanced_backtest_results(self, trade_history: List, 
                                                 daily_pnl: List, leverage_history: List,
                                                 risk_violations: List, initial_balance: float,
                                                 final_balance: float) -> Dict:
        """Calculate comprehensive backtest results"""
        try:
            if not trade_history:
                return self._get_fallback_results(initial_balance)
            
            # Basic performance metrics
            total_return_pct = ((final_balance - initial_balance) / initial_balance) * 100
            total_trades = len(trade_history)
            winning_trades = sum(1 for trade in trade_history if trade['pnl_usd'] > 0)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # P&L statistics
            pnl_values = [trade['pnl_usd'] for trade in trade_history]
            avg_trade_pnl = np.mean(pnl_values)
            best_trade = max(pnl_values)
            worst_trade = min(pnl_values)
            
            # Leverage statistics
            leverages = [trade['leverage'] for trade in trade_history]
            avg_leverage = np.mean(leverages)
            max_leverage_used = max(leverages)
            leverage_distribution = {
                'low_leverage_trades': sum(1 for lev in leverages if lev <= 15),
                'medium_leverage_trades': sum(1 for lev in leverages if 15 < lev <= 25),
                'high_leverage_trades': sum(1 for lev in leverages if 25 < lev <= 35),
                'extreme_leverage_trades': sum(1 for lev in leverages if lev > 35)
            }
            
            # Risk metrics
            daily_returns = [day['daily_return'] for day in daily_pnl if day['daily_return'] != 0]
            if daily_returns:
                volatility = np.std(daily_returns) * np.sqrt(365)  # Annualized
                sharpe_ratio = (np.mean(daily_returns) * 365) / volatility if volatility > 0 else 0
                
                # Maximum drawdown
                peak_balance = initial_balance
                max_drawdown = 0
                for day in daily_pnl:
                    if day['balance'] > peak_balance:
                        peak_balance = day['balance']
                    drawdown = (peak_balance - day['balance']) / peak_balance
                    max_drawdown = max(max_drawdown, drawdown)
            else:
                volatility = 0
                sharpe_ratio = 0
                max_drawdown = 0
            
            # Liquidation analysis
            liquidation_count = len(self.liquidation_events)
            liquidation_rate = liquidation_count / total_trades if total_trades > 0 else 0
            
            # Risk-adjusted returns by leverage tier
            leverage_performance = {}
            for tier, trades in leverage_distribution.items():
                if trades > 0:
                    tier_trades = [t for t in trade_history if self._get_leverage_tier(t['leverage']) == tier]
                    if tier_trades:
                        tier_return = sum(t['pnl_pct'] for t in tier_trades) / len(tier_trades)
                        tier_win_rate = sum(1 for t in tier_trades if t['pnl_usd'] > 0) / len(tier_trades)
                        leverage_performance[tier] = {
                            'avg_return_pct': tier_return,
                            'win_rate': tier_win_rate,
                            'trade_count': len(tier_trades)
                        }
            
            # Risk violation analysis
            violation_analysis = {
                'total_violations': len(risk_violations),
                'violation_rate': len(risk_violations) / (total_trades + len(risk_violations)) if (total_trades + len(risk_violations)) > 0 else 0,
                'common_violations': self._analyze_common_violations(risk_violations)
            }
            
            return {
                # Basic Performance
                'initial_balance': initial_balance,
                'final_balance': final_balance,
                'total_return_pct': total_return_pct,
                'total_return_usd': final_balance - initial_balance,
                
                # Trade Statistics
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': win_rate,
                'avg_trade_pnl': avg_trade_pnl,
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                
                # Risk Metrics
                'max_drawdown_pct': max_drawdown * 100,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'liquidation_count': liquidation_count,
                'liquidation_rate': liquidation_rate,
                
                # Leverage Analysis
                'avg_leverage_used': avg_leverage,
                'max_leverage_used': max_leverage_used,
                'leverage_distribution': leverage_distribution,
                'leverage_performance_by_tier': leverage_performance,
                
                # Risk Analysis
                'risk_violations': violation_analysis,
                'emergency_stops': sum(1 for event in self.liquidation_events if event.get('loss_pct', 0) >= 80),
                
                # Advanced Metrics
                'profit_factor': abs(sum(p for p in pnl_values if p > 0) / sum(p for p in pnl_values if p < 0)) if any(p < 0 for p in pnl_values) else float('inf'),
                'max_consecutive_losses': self._calculate_max_consecutive_losses(trade_history),
                'risk_adjusted_return': total_return_pct / max(max_drawdown * 100, 1),  # Return/MaxDD ratio
                
                # Detailed Data
                'daily_pnl': daily_pnl,
                'trade_history': trade_history[-50:],  # Last 50 trades
                'leverage_usage_history': leverage_history[-100:],  # Last 100 leverage events
            }
            
        except Exception as e:
            logger.error(f"Error calculating enhanced backtest results: {e}")
            return self._get_fallback_results(initial_balance)
    
    def _get_leverage_tier(self, leverage: int) -> str:
        """Categorize leverage into tiers"""
        if leverage <= 15:
            return 'low_leverage_trades'
        elif leverage <= 25:
            return 'medium_leverage_trades'
        elif leverage <= 35:
            return 'high_leverage_trades'
        else:
            return 'extreme_leverage_trades'
    
    def _analyze_common_violations(self, violations: List) -> Dict:
        """Analyze common risk violations"""
        try:
            violation_reasons = {}
            for violation in violations:
                for reason in violation.get('reason', []):
                    violation_reasons[reason] = violation_reasons.get(reason, 0) + 1
            
            # Sort by frequency
            return dict(sorted(violation_reasons.items(), key=lambda x: x[1], reverse=True))
            
        except Exception:
            return {}
    
    def _calculate_max_consecutive_losses(self, trades: List) -> int:
        """Calculate maximum consecutive losing trades"""
        try:
            max_consecutive = 0
            current_consecutive = 0
            
            for trade in trades:
                if trade['pnl_usd'] < 0:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
            
            return max_consecutive
            
        except Exception:
            return 0
    
    def _get_fallback_results(self, initial_balance: float) -> Dict:
        """Fallback results in case of error"""
        return {
            'initial_balance': initial_balance,
            'final_balance': initial_balance,
            'total_return_pct': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'max_leverage_used': 0,
            'error': 'Backtest calculation failed'
        }
    
    async def compare_leverage_strategies(self, symbols: List[str], 
                                        historical_data: Dict) -> Dict:
        """Compare different leverage strategies"""
        try:
            strategies = {
                'conservative': {'max_leverage': 15, 'risk_multiplier': 0.8},
                'moderate': {'max_leverage': 25, 'risk_multiplier': 1.0},
                'aggressive': {'max_leverage': 40, 'risk_multiplier': 1.2},
                'enhanced_dynamic': {'max_leverage': 50, 'risk_multiplier': 1.0}  # Our enhanced system
            }
            
            comparison_results = {}
            
            for strategy_name, params in strategies.items():
                logger.info(f"Testing {strategy_name} leverage strategy...")
                
                # Temporarily adjust config for this strategy
                original_config = enhanced_leverage_config.pair_profiles.copy()
                
                if strategy_name != 'enhanced_dynamic':
                    # Apply strategy limits
                    for symbol, profile in enhanced_leverage_config.pair_profiles.items():
                        profile.max_leverage = min(profile.max_leverage, params['max_leverage'])
                        profile.performance_multiplier *= params['risk_multiplier']
                
                # Run backtest
                results = await self.run_leverage_optimization_backtest(
                    symbols, historical_data, initial_balance=10000
                )
                
                comparison_results[strategy_name] = {
                    'total_return_pct': results.get('total_return_pct', 0),
                    'sharpe_ratio': results.get('sharpe_ratio', 0),
                    'max_drawdown_pct': results.get('max_drawdown_pct', 0),
                    'win_rate': results.get('win_rate', 0),
                    'avg_leverage': results.get('avg_leverage_used', 0),
                    'max_leverage': results.get('max_leverage_used', 0),
                    'liquidation_rate': results.get('liquidation_rate', 0),
                    'risk_adjusted_return': results.get('risk_adjusted_return', 0)
                }
                
                # Restore original config
                enhanced_leverage_config.pair_profiles = original_config
            
            # Determine best strategy
            best_strategy = max(comparison_results.items(), 
                              key=lambda x: x[1]['risk_adjusted_return'])
            
            return {
                'strategy_comparison': comparison_results,
                'best_strategy': {
                    'name': best_strategy[0],
                    'metrics': best_strategy[1]
                },
                'summary': self._generate_strategy_summary(comparison_results)
            }
            
        except Exception as e:
            logger.error(f"Error comparing leverage strategies: {e}")
            return {'error': 'Strategy comparison failed'}
    
    def _generate_strategy_summary(self, results: Dict) -> str:
        """Generate summary of strategy comparison"""
        try:
            summary_lines = []
            
            for strategy, metrics in results.items():
                risk_return = metrics.get('risk_adjusted_return', 0)
                summary_lines.append(
                    f"{strategy.title()}: {metrics.get('total_return_pct', 0):.1f}% return, "
                    f"{metrics.get('max_drawdown_pct', 0):.1f}% max DD, "
                    f"RR: {risk_return:.2f}"
                )
            
            return "\n".join(summary_lines)
            
        except Exception:
            return "Summary generation failed"

# Global instance
enhanced_leverage_backtester = EnhancedLeverageBacktester()