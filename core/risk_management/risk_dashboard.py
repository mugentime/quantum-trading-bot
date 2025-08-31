"""
Real-time Risk Monitoring Dashboard for Scalping Operations

Provides live visualization and monitoring of risk metrics
with immediate alerts for critical situations.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from dataclasses import asdict
import logging
from collections import deque

class RiskDashboard:
    """Real-time risk monitoring and alerting system"""
    
    def __init__(self, risk_manager, telegram_bot=None):
        self.risk_manager = risk_manager
        self.telegram_bot = telegram_bot
        self.logger = logging.getLogger(__name__)
        
        # Historical data storage
        self.risk_history = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.pnl_history = deque(maxlen=1440)
        self.position_history = deque(maxlen=288)  # 24 hours at 5-minute intervals
        
        # Alert tracking
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 minutes between same type alerts
        
        # Performance metrics
        self.metrics = {
            'trades_per_hour': 0,
            'avg_hold_time': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'sharpe_ratio': 0,
            'max_drawdown_today': 0,
            'risk_adjusted_return': 0
        }
    
    async def start_monitoring(self, update_interval: int = 60):
        """Start real-time monitoring and alerting"""
        self.logger.info("Starting risk dashboard monitoring")
        
        while True:
            try:
                # Collect current risk data
                risk_data = await self._collect_risk_data()
                
                # Store historical data
                self._store_historical_data(risk_data)
                
                # Update performance metrics
                await self._update_performance_metrics()
                
                # Check for alerts
                await self._check_alerts(risk_data)
                
                # Log dashboard status
                await self._log_dashboard_status(risk_data)
                
                await asyncio.sleep(update_interval)
                
            except Exception as e:
                self.logger.error(f"Dashboard monitoring error: {e}")
                await asyncio.sleep(update_interval * 2)
    
    async def _collect_risk_data(self) -> Dict:
        """Collect comprehensive risk data"""
        try:
            # Get risk summary from manager
            risk_summary = self.risk_manager.get_risk_summary()
            
            # Add timestamp and additional calculations
            risk_data = {
                'timestamp': datetime.now(),
                'account_risk': risk_summary['account_risk'],
                'daily_stats': risk_summary['daily_stats'],
                'positions': risk_summary['positions'],
                'risk_parameters': risk_summary['risk_parameters'],
                'next_funding_time': risk_summary.get('next_funding_time'),
                
                # Additional calculated metrics
                'portfolio_heat': self._calculate_portfolio_heat(risk_summary),
                'risk_score': self._calculate_risk_score(risk_summary),
                'velocity_metrics': await self._calculate_velocity_metrics(),
                'exposure_metrics': self._calculate_exposure_metrics(risk_summary)
            }
            
            return risk_data
            
        except Exception as e:
            self.logger.error(f"Risk data collection error: {e}")
            return {}
    
    def _calculate_portfolio_heat(self, risk_summary: Dict) -> float:
        """Calculate overall portfolio heat (0-100)"""
        try:
            heat_factors = []
            
            # Position count heat (0-30)
            position_count = risk_summary['positions']['count']
            max_positions = risk_summary['risk_parameters']['max_concurrent_positions']
            position_heat = (position_count / max_positions) * 30
            heat_factors.append(position_heat)
            
            # Daily PnL heat (0-40)
            daily_pnl_pct = abs(risk_summary['account_risk']['daily_pnl_pct'])
            daily_limit = risk_summary['risk_parameters']['daily_loss_limit_pct']
            pnl_heat = min(40, (daily_pnl_pct / daily_limit) * 40)
            heat_factors.append(pnl_heat)
            
            # Consecutive losses heat (0-20)
            consecutive_losses = risk_summary['account_risk']['consecutive_losses']
            max_losses = risk_summary['risk_parameters']['max_consecutive_losses']
            loss_heat = (consecutive_losses / max_losses) * 20
            heat_factors.append(loss_heat)
            
            # Circuit breaker/emergency (0-10 or 100 if active)
            if risk_summary['account_risk']['circuit_breaker'] or risk_summary['account_risk']['emergency_stop']:
                heat_factors.append(100)
            else:
                heat_factors.append(0)
            
            return min(100, sum(heat_factors))
            
        except Exception as e:
            self.logger.error(f"Portfolio heat calculation error: {e}")
            return 0
    
    def _calculate_risk_score(self, risk_summary: Dict) -> float:
        """Calculate composite risk score (0-10)"""
        try:
            # Risk level mapping
            risk_level_scores = {
                'low': 2,
                'moderate': 4,
                'high': 7,
                'critical': 9,
                'emergency': 10
            }
            
            base_score = risk_level_scores.get(risk_summary['account_risk']['risk_level'], 5)
            
            # Adjustments
            if risk_summary['positions']['count'] == 0:
                base_score *= 0.5  # Lower risk with no positions
            
            if risk_summary['account_risk']['daily_pnl_pct'] > 0:
                base_score *= 0.8  # Lower risk when profitable
            
            return min(10, base_score)
            
        except Exception as e:
            self.logger.error(f"Risk score calculation error: {e}")
            return 5
    
    async def _calculate_velocity_metrics(self) -> Dict:
        """Calculate trading velocity and frequency metrics"""
        try:
            current_hour = datetime.now().hour
            
            # Get recent trade data
            if len(self.risk_manager.trade_history) > 0:
                recent_trades = [
                    t for t in self.risk_manager.trade_history 
                    if datetime.fromisoformat(t['timestamp']).hour == current_hour
                ]
                
                trades_this_hour = len(recent_trades)
                
                # Calculate average time between trades
                if len(recent_trades) > 1:
                    timestamps = [datetime.fromisoformat(t['timestamp']) for t in recent_trades]
                    timestamps.sort()
                    intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() 
                               for i in range(1, len(timestamps))]
                    avg_interval = sum(intervals) / len(intervals) if intervals else 0
                else:
                    avg_interval = 0
                
                return {
                    'trades_this_hour': trades_this_hour,
                    'avg_trade_interval_seconds': avg_interval,
                    'trading_frequency': trades_this_hour / max(1, (datetime.now().minute + 1) / 60),
                    'velocity_status': 'high' if trades_this_hour > 10 else 'normal' if trades_this_hour > 5 else 'low'
                }
            
            return {
                'trades_this_hour': 0,
                'avg_trade_interval_seconds': 0,
                'trading_frequency': 0,
                'velocity_status': 'idle'
            }
            
        except Exception as e:
            self.logger.error(f"Velocity metrics calculation error: {e}")
            return {}
    
    def _calculate_exposure_metrics(self, risk_summary: Dict) -> Dict:
        """Calculate position exposure metrics"""
        try:
            positions = risk_summary['positions']['details']
            
            if not positions:
                return {
                    'total_exposure': 0,
                    'long_exposure': 0,
                    'short_exposure': 0,
                    'net_exposure': 0,
                    'exposure_balance': 1.0
                }
            
            long_exposure = sum(pos['unrealized_pnl'] for pos in positions if pos['side'] == 'BUY')
            short_exposure = sum(pos['unrealized_pnl'] for pos in positions if pos['side'] == 'SELL')
            total_exposure = abs(long_exposure) + abs(short_exposure)
            net_exposure = long_exposure + short_exposure
            
            # Calculate exposure balance (how balanced long/short positions are)
            if total_exposure > 0:
                exposure_balance = 1 - abs(net_exposure) / total_exposure
            else:
                exposure_balance = 1.0
            
            return {
                'total_exposure': total_exposure,
                'long_exposure': long_exposure,
                'short_exposure': short_exposure,
                'net_exposure': net_exposure,
                'exposure_balance': exposure_balance
            }
            
        except Exception as e:
            self.logger.error(f"Exposure metrics calculation error: {e}")
            return {}
    
    def _store_historical_data(self, risk_data: Dict):
        """Store data for historical analysis"""
        try:
            # Store risk history
            self.risk_history.append({
                'timestamp': risk_data['timestamp'],
                'risk_score': risk_data['risk_score'],
                'portfolio_heat': risk_data['portfolio_heat'],
                'daily_pnl_pct': risk_data['account_risk']['daily_pnl_pct'],
                'position_count': risk_data['positions']['count']
            })
            
            # Store PnL history
            self.pnl_history.append({
                'timestamp': risk_data['timestamp'],
                'daily_pnl': risk_data['account_risk']['daily_pnl'],
                'total_balance': risk_data['account_risk']['total_balance'],
                'unrealized_pnl': sum(pos['unrealized_pnl'] for pos in risk_data['positions']['details'])
            })
            
            # Store position history (every 5 minutes)
            if datetime.now().minute % 5 == 0:
                self.position_history.append({
                    'timestamp': risk_data['timestamp'],
                    'positions': risk_data['positions']['details'].copy(),
                    'exposure_metrics': risk_data['exposure_metrics']
                })
            
        except Exception as e:
            self.logger.error(f"Historical data storage error: {e}")
    
    async def _update_performance_metrics(self):
        """Update performance metrics from historical data"""
        try:
            if len(self.pnl_history) < 2:
                return
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(list(self.pnl_history))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Trades per hour (estimate from PnL changes)
            pnl_changes = df['daily_pnl'].diff().abs()
            significant_changes = pnl_changes[pnl_changes > 1.0]  # $1+ changes
            hours_covered = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds() / 3600
            self.metrics['trades_per_hour'] = len(significant_changes) / max(1, hours_covered)
            
            # Win rate from daily stats
            daily_stats = self.risk_manager.daily_stats
            total_trades = daily_stats['wins'] + daily_stats['losses']
            self.metrics['win_rate'] = daily_stats['wins'] / max(1, total_trades)
            
            # Profit factor
            if daily_stats['losses'] > 0 and daily_stats['wins'] > 0:
                # Simplified calculation - would need individual trade data for accuracy
                avg_win = daily_stats['total_pnl'] / max(1, daily_stats['wins']) if daily_stats['total_pnl'] > 0 else 0
                avg_loss = abs(daily_stats['total_pnl']) / max(1, daily_stats['losses']) if daily_stats['total_pnl'] < 0 else 0
                self.metrics['profit_factor'] = avg_win / max(0.01, avg_loss)
            
            # Max drawdown today
            self.metrics['max_drawdown_today'] = daily_stats['max_drawdown']
            
            # Sharpe ratio (simplified daily calculation)
            if len(df) > 10:
                returns = df['daily_pnl'].pct_change().dropna()
                if len(returns) > 1 and returns.std() > 0:
                    self.metrics['sharpe_ratio'] = returns.mean() / returns.std() * np.sqrt(252)  # Annualized
            
            # Risk-adjusted return
            if self.metrics['max_drawdown_today'] < 0:
                self.metrics['risk_adjusted_return'] = daily_stats['total_pnl'] / abs(self.metrics['max_drawdown_today'])
            
        except Exception as e:
            self.logger.error(f"Performance metrics update error: {e}")
    
    async def _check_alerts(self, risk_data: Dict):
        """Check for alert conditions and send notifications"""
        try:
            alerts = []
            
            # Critical risk level
            if risk_data['account_risk']['risk_level'] in ['critical', 'emergency']:
                alerts.append({
                    'level': 'CRITICAL',
                    'type': 'risk_level',
                    'message': f"Risk level: {risk_data['account_risk']['risk_level'].upper()}",
                    'data': risk_data['account_risk']
                })
            
            # High portfolio heat
            if risk_data['portfolio_heat'] > 80:
                alerts.append({
                    'level': 'HIGH',
                    'type': 'portfolio_heat',
                    'message': f"Portfolio heat: {risk_data['portfolio_heat']:.1f}%",
                    'data': {'heat': risk_data['portfolio_heat']}
                })
            
            # Daily loss approaching limit
            daily_loss_pct = abs(risk_data['account_risk']['daily_pnl_pct'])
            loss_limit = risk_data['risk_parameters']['daily_loss_limit_pct']
            if daily_loss_pct > loss_limit * 0.8:  # 80% of limit
                alerts.append({
                    'level': 'HIGH',
                    'type': 'daily_loss',
                    'message': f"Daily loss: {daily_loss_pct:.2f}% (limit: {loss_limit:.2f}%)",
                    'data': {'loss_pct': daily_loss_pct, 'limit': loss_limit}
                })
            
            # High consecutive losses
            consecutive = risk_data['account_risk']['consecutive_losses']
            max_consecutive = risk_data['risk_parameters']['max_consecutive_losses']
            if consecutive > max_consecutive * 0.6:  # 60% of limit
                alerts.append({
                    'level': 'MEDIUM',
                    'type': 'consecutive_losses',
                    'message': f"Consecutive losses: {consecutive}/{max_consecutive}",
                    'data': {'consecutive': consecutive, 'max': max_consecutive}
                })
            
            # High trading velocity
            velocity = risk_data.get('velocity_metrics', {})
            if velocity.get('trades_this_hour', 0) > 20:  # Very high frequency
                alerts.append({
                    'level': 'MEDIUM',
                    'type': 'high_velocity',
                    'message': f"High trading velocity: {velocity['trades_this_hour']} trades this hour",
                    'data': velocity
                })
            
            # Funding time approaching with high exposure
            if risk_data.get('next_funding_time'):
                funding_time = datetime.fromisoformat(risk_data['next_funding_time'])
                time_to_funding = (funding_time - datetime.now()).total_seconds()
                if time_to_funding < 300 and risk_data['positions']['count'] > 0:  # 5 minutes
                    alerts.append({
                        'level': 'LOW',
                        'type': 'funding_approaching',
                        'message': f"Funding in {time_to_funding/60:.1f} minutes with {risk_data['positions']['count']} positions",
                        'data': {'time_to_funding': time_to_funding, 'positions': risk_data['positions']['count']}
                    })
            
            # Send alerts
            for alert in alerts:
                await self._send_alert(alert)
            
        except Exception as e:
            self.logger.error(f"Alert checking error: {e}")
    
    async def _send_alert(self, alert: Dict):
        """Send alert notification"""
        try:
            alert_key = f"{alert['type']}_{alert['level']}"
            current_time = time.time()
            
            # Check cooldown
            if alert_key in self.last_alerts:
                if current_time - self.last_alerts[alert_key] < self.alert_cooldown:
                    return
            
            # Log alert
            log_method = {
                'CRITICAL': self.logger.critical,
                'HIGH': self.logger.error,
                'MEDIUM': self.logger.warning,
                'LOW': self.logger.info
            }.get(alert['level'], self.logger.info)
            
            log_method(f"RISK ALERT [{alert['level']}] {alert['message']}")
            
            # Send Telegram notification if available
            if self.telegram_bot and alert['level'] in ['CRITICAL', 'HIGH']:
                await self.telegram_bot.send_risk_alert(alert)
            
            # Update cooldown
            self.last_alerts[alert_key] = current_time
            
        except Exception as e:
            self.logger.error(f"Alert sending error: {e}")
    
    async def _log_dashboard_status(self, risk_data: Dict):
        """Log comprehensive dashboard status"""
        try:
            # Log every 5 minutes
            if datetime.now().minute % 5 != 0:
                return
            
            status_msg = (
                f"=== RISK DASHBOARD STATUS ===\n"
                f"Time: {risk_data['timestamp'].strftime('%H:%M:%S')}\n"
                f"Risk Score: {risk_data['risk_score']:.1f}/10\n"
                f"Portfolio Heat: {risk_data['portfolio_heat']:.1f}%\n"
                f"Daily P&L: ${risk_data['account_risk']['daily_pnl']:.2f} "
                f"({risk_data['account_risk']['daily_pnl_pct']:.2f}%)\n"
                f"Active Positions: {risk_data['positions']['count']}\n"
                f"Trades Today: {risk_data['daily_stats']['trades']}\n"
                f"Win Rate: {self.metrics['win_rate']*100:.1f}%\n"
                f"Consecutive Losses: {risk_data['account_risk']['consecutive_losses']}\n"
                f"Circuit Breaker: {'ACTIVE' if risk_data['account_risk']['circuit_breaker'] else 'OFF'}\n"
                f"Emergency Stop: {'ACTIVE' if risk_data['account_risk']['emergency_stop'] else 'OFF'}\n"
                f"=========================="
            )
            
            self.logger.info(status_msg)
            
        except Exception as e:
            self.logger.error(f"Status logging error: {e}")
    
    def get_dashboard_data(self) -> Dict:
        """Get complete dashboard data for API/UI"""
        try:
            latest_risk = list(self.risk_history)[-1] if self.risk_history else {}
            latest_pnl = list(self.pnl_history)[-1] if self.pnl_history else {}
            
            return {
                'current_status': {
                    'timestamp': datetime.now().isoformat(),
                    'risk_score': latest_risk.get('risk_score', 0),
                    'portfolio_heat': latest_risk.get('portfolio_heat', 0),
                    'daily_pnl': latest_pnl.get('daily_pnl', 0),
                    'position_count': latest_risk.get('position_count', 0),
                },
                'performance_metrics': self.metrics,
                'historical_data': {
                    'risk_history': list(self.risk_history)[-60:],  # Last hour
                    'pnl_history': list(self.pnl_history)[-60:],   # Last hour
                    'position_history': list(self.position_history)[-12:]  # Last hour
                },
                'alerts': {
                    'recent_alerts': self.last_alerts,
                    'cooldown_seconds': self.alert_cooldown
                }
            }
            
        except Exception as e:
            self.logger.error(f"Dashboard data error: {e}")
            return {'error': str(e)}
    
    def export_risk_report(self, filename: str = None) -> str:
        """Export comprehensive risk report"""
        try:
            if not filename:
                filename = f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report_data = {
                'report_timestamp': datetime.now().isoformat(),
                'risk_manager_summary': self.risk_manager.get_risk_summary(),
                'performance_metrics': self.metrics,
                'historical_data': {
                    'risk_history': [
                        {**item, 'timestamp': item['timestamp'].isoformat()} 
                        for item in list(self.risk_history)
                    ],
                    'pnl_history': [
                        {**item, 'timestamp': item['timestamp'].isoformat()} 
                        for item in list(self.pnl_history)
                    ],
                    'position_history': [
                        {**item, 'timestamp': item['timestamp'].isoformat()} 
                        for item in list(self.position_history)
                    ]
                },
                'trade_history': self.risk_manager.trade_history,
                'alert_history': self.last_alerts
            }
            
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.logger.info(f"Risk report exported to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Risk report export error: {e}")
            return f"Export failed: {str(e)}"