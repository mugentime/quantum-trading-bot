"""
Advanced Performance Monitoring and Metrics System
Tracks leverage efficiency, risk metrics, and trading performance in real-time
"""
import logging
import json
import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from .config.settings import config
from .leverage_manager import leverage_manager
from .risk_manager import risk_manager
from .volatility_manager import volatility_manager
from ..utils.telegram_notifier import telegram_notifier

logger = logging.getLogger(__name__)

@dataclass
class PerformanceSnapshot:
    """Single point-in-time performance snapshot"""
    timestamp: datetime
    account_balance: float
    daily_pnl: float
    daily_pnl_pct: float
    active_positions: int
    avg_leverage_used: float
    win_rate: float
    total_trades: int
    margin_utilization: float
    risk_status: str
    volatility_regime: str

class PerformanceMonitor:
    """Comprehensive performance tracking and analysis system"""
    
    def __init__(self):
        self.performance_history: List[PerformanceSnapshot] = []
        self.leverage_metrics = {}
        self.alert_thresholds = {
            'daily_loss_warning': 0.05,      # 5% daily loss
            'daily_loss_critical': 0.08,     # 8% daily loss
            'margin_warning': 0.70,          # 70% margin usage
            'margin_critical': 0.85,         # 85% margin usage
            'leverage_efficiency_low': 0.60, # < 60% efficiency
            'win_rate_warning': 0.40         # < 40% win rate
        }
        self.last_report_time = datetime.now()
        
    async def capture_performance_snapshot(self, executor) -> PerformanceSnapshot:
        """Capture comprehensive performance metrics at current moment"""
        try:
            # Get account balance
            try:
                balance = await executor.exchange.fetch_balance()
                account_balance = balance.get('USDT', {}).get('total', 0)
                free_balance = balance.get('USDT', {}).get('free', 0)
                used_balance = balance.get('USDT', {}).get('used', 0)
                margin_utilization = used_balance / account_balance if account_balance > 0 else 0
            except Exception as e:
                logger.error(f"Error fetching balance: {e}")
                account_balance = 0
                margin_utilization = 0
            
            # Get positions and leverage metrics
            positions = await executor.get_open_positions()
            active_positions = len(positions)
            
            # Calculate average leverage used
            avg_leverage = self._calculate_average_leverage(positions)
            
            # Get performance metrics from components
            leverage_metrics = leverage_manager.get_leverage_metrics()
            risk_metrics = risk_manager.get_risk_metrics()
            
            # Calculate win rate and trade count
            win_rate = leverage_metrics.get('recent_win_rate', 0.5)
            total_trades = leverage_metrics.get('total_recent_trades', 0)
            
            # Get volatility status
            volatility_regime = 'normal'  # Default
            try:
                # Get overall market volatility regime
                symbols = config.SYMBOLS
                vol_summary = await volatility_manager.get_market_volatility_summary(
                    symbols, executor.exchange
                )
                volatility_regime = vol_summary.get('overall_regime', 'normal')
            except Exception as e:
                logger.error(f"Error getting volatility regime: {e}")
            
            # Create snapshot
            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                account_balance=account_balance,
                daily_pnl=leverage_manager.daily_pnl,
                daily_pnl_pct=(leverage_manager.daily_pnl / account_balance * 100) if account_balance > 0 else 0,
                active_positions=active_positions,
                avg_leverage_used=avg_leverage,
                win_rate=win_rate,
                total_trades=total_trades,
                margin_utilization=margin_utilization,
                risk_status=risk_metrics.get('risk_status', 'UNKNOWN'),
                volatility_regime=volatility_regime
            )
            
            # Store snapshot
            self.performance_history.append(snapshot)
            
            # Keep only last 24 hours of snapshots (assuming 1 snapshot per hour)
            if len(self.performance_history) > 24:
                self.performance_history = self.performance_history[-24:]
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error capturing performance snapshot: {e}")
            # Return minimal snapshot
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                account_balance=0,
                daily_pnl=0,
                daily_pnl_pct=0,
                active_positions=0,
                avg_leverage_used=0,
                win_rate=0.5,
                total_trades=0,
                margin_utilization=0,
                risk_status='ERROR',
                volatility_regime='unknown'
            )
    
    def _calculate_average_leverage(self, positions: List[Dict]) -> float:
        """Calculate weighted average leverage across positions"""
        try:
            if not positions:
                return 0.0
            
            total_value = 0
            weighted_leverage = 0
            
            for position in positions:
                # Estimate position value (simplified)
                quantity = position.get('quantity', 0)
                entry_price = position.get('entry_price', 0)
                position_value = quantity * entry_price
                
                # Assume standard leverage tiers based on position
                # In a real implementation, you'd track actual leverage per position
                estimated_leverage = config.DEFAULT_LEVERAGE
                
                weighted_leverage += estimated_leverage * position_value
                total_value += position_value
            
            return weighted_leverage / total_value if total_value > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating average leverage: {e}")
            return config.DEFAULT_LEVERAGE
    
    async def analyze_leverage_efficiency(self) -> Dict:
        """Analyze how efficiently leverage is being used"""
        try:
            if len(self.performance_history) < 2:
                return {'efficiency_score': 0.5, 'analysis': 'Insufficient data'}
            
            # Get recent snapshots
            recent_snapshots = self.performance_history[-6:]  # Last 6 hours
            
            # Calculate metrics
            avg_leverage_used = np.mean([s.avg_leverage_used for s in recent_snapshots])
            avg_margin_usage = np.mean([s.margin_utilization for s in recent_snapshots])
            avg_daily_return = np.mean([s.daily_pnl_pct for s in recent_snapshots])
            
            # Leverage efficiency score
            # Higher leverage with positive returns = more efficient
            # Lower leverage with negative returns = more efficient
            base_efficiency = 0.5
            
            if avg_daily_return > 0:
                # Positive returns: higher leverage is more efficient
                leverage_factor = min(avg_leverage_used / config.DEFAULT_LEVERAGE, 2.0)
                efficiency_score = base_efficiency + (leverage_factor - 1) * 0.3
            else:
                # Negative returns: lower leverage is more efficient
                leverage_factor = avg_leverage_used / config.DEFAULT_LEVERAGE
                efficiency_score = base_efficiency + (1 - leverage_factor) * 0.3
            
            # Adjust for margin usage
            if avg_margin_usage > 0.8:
                efficiency_score -= 0.2  # Penalty for overuse
            elif avg_margin_usage < 0.3:
                efficiency_score -= 0.1  # Penalty for underuse
            
            efficiency_score = max(0, min(1, efficiency_score))
            
            analysis = {
                'efficiency_score': efficiency_score,
                'avg_leverage_used': avg_leverage_used,
                'avg_margin_usage': avg_margin_usage,
                'avg_daily_return': avg_daily_return,
                'analysis': self._get_efficiency_analysis(efficiency_score),
                'recommendations': self._get_efficiency_recommendations(
                    efficiency_score, avg_leverage_used, avg_margin_usage
                )
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing leverage efficiency: {e}")
            return {'efficiency_score': 0.5, 'analysis': f'Analysis failed: {str(e)}'}
    
    def _get_efficiency_analysis(self, score: float) -> str:
        """Get text analysis of efficiency score"""
        if score >= 0.8:
            return "Excellent leverage efficiency - optimal risk/reward balance"
        elif score >= 0.7:
            return "Good leverage efficiency - minor optimization opportunities"
        elif score >= 0.6:
            return "Fair leverage efficiency - consider adjustments"
        elif score >= 0.4:
            return "Poor leverage efficiency - significant optimization needed"
        else:
            return "Very poor efficiency - review leverage strategy immediately"
    
    def _get_efficiency_recommendations(self, score: float, avg_leverage: float, 
                                      avg_margin: float) -> List[str]:
        """Get specific recommendations for improving efficiency"""
        recommendations = []
        
        if score < 0.6:
            if avg_leverage < config.DEFAULT_LEVERAGE * 0.8:
                recommendations.append("Consider increasing leverage for stronger signals")
            elif avg_leverage > config.DEFAULT_LEVERAGE * 1.5:
                recommendations.append("Consider reducing leverage to improve risk management")
        
        if avg_margin > 0.8:
            recommendations.append("Reduce margin usage to avoid liquidation risk")
        elif avg_margin < 0.3:
            recommendations.append("Consider increasing position sizes to utilize available margin")
        
        if not recommendations:
            recommendations.append("Continue with current leverage strategy")
        
        return recommendations
    
    async def check_alert_conditions(self, snapshot: PerformanceSnapshot) -> List[Dict]:
        """Check for alert conditions and return list of alerts"""
        alerts = []
        
        try:
            # Daily loss alerts
            daily_loss_pct = abs(snapshot.daily_pnl_pct) if snapshot.daily_pnl < 0 else 0
            
            if daily_loss_pct >= self.alert_thresholds['daily_loss_critical']:
                alerts.append({
                    'type': 'CRITICAL',
                    'category': 'DAILY_LOSS',
                    'message': f'Critical daily loss: {daily_loss_pct:.1f}%',
                    'value': daily_loss_pct,
                    'threshold': self.alert_thresholds['daily_loss_critical']
                })
            elif daily_loss_pct >= self.alert_thresholds['daily_loss_warning']:
                alerts.append({
                    'type': 'WARNING',
                    'category': 'DAILY_LOSS',
                    'message': f'Daily loss warning: {daily_loss_pct:.1f}%',
                    'value': daily_loss_pct,
                    'threshold': self.alert_thresholds['daily_loss_warning']
                })
            
            # Margin usage alerts
            if snapshot.margin_utilization >= self.alert_thresholds['margin_critical']:
                alerts.append({
                    'type': 'CRITICAL',
                    'category': 'MARGIN',
                    'message': f'Critical margin usage: {snapshot.margin_utilization:.1%}',
                    'value': snapshot.margin_utilization,
                    'threshold': self.alert_thresholds['margin_critical']
                })
            elif snapshot.margin_utilization >= self.alert_thresholds['margin_warning']:
                alerts.append({
                    'type': 'WARNING',
                    'category': 'MARGIN',
                    'message': f'High margin usage: {snapshot.margin_utilization:.1%}',
                    'value': snapshot.margin_utilization,
                    'threshold': self.alert_thresholds['margin_warning']
                })
            
            # Win rate alerts
            if snapshot.win_rate <= self.alert_thresholds['win_rate_warning']:
                alerts.append({
                    'type': 'WARNING',
                    'category': 'PERFORMANCE',
                    'message': f'Low win rate: {snapshot.win_rate:.1%}',
                    'value': snapshot.win_rate,
                    'threshold': self.alert_thresholds['win_rate_warning']
                })
            
            # Risk status alerts
            if snapshot.risk_status in ['HIGH', 'EMERGENCY']:
                alerts.append({
                    'type': 'CRITICAL' if snapshot.risk_status == 'EMERGENCY' else 'WARNING',
                    'category': 'RISK',
                    'message': f'Risk status: {snapshot.risk_status}',
                    'value': snapshot.risk_status,
                    'threshold': 'LOW'
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
            return []
    
    async def send_performance_alerts(self, alerts: List[Dict]):
        """Send performance alerts via Telegram"""
        try:
            if not alerts:
                return
            
            # Group alerts by severity
            critical_alerts = [a for a in alerts if a['type'] == 'CRITICAL']
            warning_alerts = [a for a in alerts if a['type'] == 'WARNING']
            
            # Send critical alerts immediately
            if critical_alerts:
                message = "🚨 CRITICAL PERFORMANCE ALERTS 🚨\n\n"
                for alert in critical_alerts:
                    message += f"• {alert['message']}\n"
                
                await telegram_notifier.send_message(message)
            
            # Send warning alerts (less frequent)
            if warning_alerts:
                message = "⚠️ Performance Warnings ⚠️\n\n"
                for alert in warning_alerts:
                    message += f"• {alert['message']}\n"
                
                await telegram_notifier.send_message(message)
                
        except Exception as e:
            logger.error(f"Error sending performance alerts: {e}")
    
    async def generate_performance_report(self, executor) -> Dict:
        """Generate comprehensive performance report"""
        try:
            # Capture current snapshot
            current_snapshot = await self.capture_performance_snapshot(executor)
            
            # Analyze efficiency
            efficiency_analysis = await self.analyze_leverage_efficiency()
            
            # Check for alerts
            alerts = await self.check_alert_conditions(current_snapshot)
            
            # Calculate trends
            trends = self._calculate_trends()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'current_snapshot': asdict(current_snapshot),
                'efficiency_analysis': efficiency_analysis,
                'alerts': alerts,
                'trends': trends,
                'leverage_metrics': leverage_manager.get_leverage_metrics(),
                'risk_metrics': risk_manager.get_risk_metrics(),
                'summary': self._generate_summary(current_snapshot, efficiency_analysis, alerts)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _calculate_trends(self) -> Dict:
        """Calculate performance trends from historical data"""
        try:
            if len(self.performance_history) < 3:
                return {'insufficient_data': True}
            
            recent = self.performance_history[-6:]  # Last 6 snapshots
            
            # Calculate trends
            balance_trend = (recent[-1].account_balance - recent[0].account_balance) / recent[0].account_balance if recent[0].account_balance > 0 else 0
            pnl_trend = recent[-1].daily_pnl - recent[0].daily_pnl
            leverage_trend = recent[-1].avg_leverage_used - recent[0].avg_leverage_used
            
            return {
                'balance_trend_pct': balance_trend * 100,
                'pnl_trend': pnl_trend,
                'leverage_trend': leverage_trend,
                'direction': 'improving' if balance_trend > 0 else 'declining'
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {'error': str(e)}
    
    def _generate_summary(self, snapshot: PerformanceSnapshot, 
                         efficiency: Dict, alerts: List[Dict]) -> str:
        """Generate human-readable summary"""
        try:
            summary_parts = []
            
            # Account status
            if snapshot.daily_pnl >= 0:
                summary_parts.append(f"✅ Profitable day: +{snapshot.daily_pnl_pct:.2f}%")
            else:
                summary_parts.append(f"📉 Daily loss: {snapshot.daily_pnl_pct:.2f}%")
            
            # Efficiency status
            eff_score = efficiency.get('efficiency_score', 0.5)
            if eff_score >= 0.7:
                summary_parts.append(f"⚡ High leverage efficiency: {eff_score:.1%}")
            else:
                summary_parts.append(f"🔧 Leverage efficiency needs improvement: {eff_score:.1%}")
            
            # Alert status
            critical_count = len([a for a in alerts if a['type'] == 'CRITICAL'])
            warning_count = len([a for a in alerts if a['type'] == 'WARNING'])
            
            if critical_count > 0:
                summary_parts.append(f"🚨 {critical_count} critical alerts")
            elif warning_count > 0:
                summary_parts.append(f"⚠️ {warning_count} warnings")
            else:
                summary_parts.append("✅ No active alerts")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            return f"Summary generation failed: {str(e)}"
    
    async def run_periodic_monitoring(self, executor, interval_minutes: int = 60):
        """Run continuous performance monitoring"""
        try:
            while True:
                # Generate performance report
                report = await self.generate_performance_report(executor)
                
                # Check and send alerts
                alerts = report.get('alerts', [])
                await self.send_performance_alerts(alerts)
                
                # Log performance summary
                summary = report.get('summary', 'No summary available')
                logger.info(f"Performance Monitor: {summary}")
                
                # Send periodic reports (every 4 hours)
                if datetime.now() - self.last_report_time > timedelta(hours=4):
                    await self._send_periodic_report(report)
                    self.last_report_time = datetime.now()
                
                # Wait for next interval
                await asyncio.sleep(interval_minutes * 60)
                
        except Exception as e:
            logger.error(f"Error in periodic monitoring: {e}")
    
    async def _send_periodic_report(self, report: Dict):
        """Send periodic performance report via Telegram"""
        try:
            snapshot = report.get('current_snapshot', {})
            efficiency = report.get('efficiency_analysis', {})
            
            message = f"""
📊 QUANTUM BOT PERFORMANCE REPORT
⏰ {snapshot.get('timestamp', 'Unknown time')}

💰 Account: ${snapshot.get('account_balance', 0):.2f}
📈 Daily P&L: {snapshot.get('daily_pnl_pct', 0):+.2f}%
🎯 Win Rate: {snapshot.get('win_rate', 0):.1%}
⚡ Leverage Efficiency: {efficiency.get('efficiency_score', 0):.1%}
🔄 Active Positions: {snapshot.get('active_positions', 0)}
📊 Margin Usage: {snapshot.get('margin_utilization', 0):.1%}
🌡️ Market Volatility: {snapshot.get('volatility_regime', 'unknown').title()}

{report.get('summary', 'No summary available')}
            """
            
            await telegram_notifier.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending periodic report: {e}")

# Global instance
performance_monitor = PerformanceMonitor()