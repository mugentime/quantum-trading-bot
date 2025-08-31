#!/usr/bin/env python3
"""
HIGH VOLATILITY TRADING MONITOR
Real-time monitoring, alerting, and performance tracking system
for high volatility pairs trading strategy.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import numpy as np
from pathlib import Path
import aiohttp
import websockets
from telegram import Bot
from telegram.ext import Application
import psutil
import traceback

# Strategy imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.high_volatility_strategy import VolatilityLevel, MarketRegime
from config.volatility_config import HighVolatilityConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Real-time performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    monthly_pnl: float = 0.0
    roi: float = 0.0
    active_positions: int = 0
    last_updated: datetime = None

@dataclass
class RiskMetrics:
    """Risk monitoring metrics"""
    portfolio_risk: float = 0.0
    concentration_risk: float = 0.0
    correlation_risk: float = 0.0
    leverage_utilization: float = 0.0
    margin_ratio: float = 0.0
    var_1d: float = 0.0  # 1-day Value at Risk
    var_1w: float = 0.0  # 1-week Value at Risk
    daily_loss_limit_used: float = 0.0
    consecutive_losses: int = 0
    risk_score: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL

@dataclass
class SystemHealth:
    """System health metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_latency: float = 0.0
    api_response_time: float = 0.0
    websocket_connections: int = 0
    error_count: int = 0
    uptime_hours: float = 0.0
    last_trade_time: Optional[datetime] = None
    status: str = "HEALTHY"  # HEALTHY, WARNING, ERROR, CRITICAL

@dataclass
class AlertConfig:
    """Alert configuration"""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_enabled: bool = False
    webhook_url: str = ""
    
    # Alert thresholds
    max_drawdown_alert: float = 0.05  # 5%
    daily_loss_alert: float = 0.03    # 3%
    consecutive_loss_alert: int = 3
    high_risk_alert: bool = True
    system_error_alert: bool = True
    position_size_alert: float = 0.06  # 6%
    
    # Alert frequencies
    performance_report_hours: int = 6
    health_check_minutes: int = 15
    risk_check_minutes: int = 5

class VolatilityMonitor:
    """Comprehensive monitoring system for high volatility strategy"""
    
    def __init__(self, config: HighVolatilityConfig, alert_config: AlertConfig):
        self.config = config
        self.alert_config = alert_config
        
        # Monitoring state
        self.performance_metrics = PerformanceMetrics(last_updated=datetime.now())
        self.risk_metrics = RiskMetrics()
        self.system_health = SystemHealth()
        
        # Data storage
        self.trade_history: List[Dict] = []
        self.daily_metrics: Dict[str, Dict] = {}
        self.alert_history: List[Dict] = []
        self.price_data: Dict[str, List] = {}
        
        # Monitoring settings
        self.monitoring_active = False
        self.start_time = datetime.now()
        self.last_alert_times: Dict[str, datetime] = {}
        self.error_count = 0
        
        # Initialize Telegram bot
        if self.alert_config.telegram_bot_token:
            self.telegram_bot = Bot(token=self.alert_config.telegram_bot_token)
        else:
            self.telegram_bot = None
        
        # Create monitoring directories
        self.log_dir = Path("monitoring_logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.report_dir = Path("monitoring_reports")
        self.report_dir.mkdir(exist_ok=True)
    
    async def start_monitoring(self):
        """Start comprehensive monitoring system"""
        self.monitoring_active = True
        logger.info("🔍 STARTING HIGH VOLATILITY TRADING MONITOR")
        logger.info("=" * 50)
        
        # Send startup notification
        await self.send_alert(
            "🚀 High Volatility Trading Monitor Started",
            f"Monitor active for {len(self.config.get_all_pairs())} pairs\n"
            f"Initial capital tracking enabled\n"
            f"Real-time alerts configured",
            "INFO"
        )
        
        # Start monitoring tasks
        tasks = [
            self.monitor_performance(),
            self.monitor_risk(),
            self.monitor_system_health(),
            self.generate_periodic_reports(),
            self.cleanup_old_data()
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring system error: {e}")
            await self.send_alert(
                "❌ Monitor System Error",
                f"Critical error in monitoring system: {str(e)}",
                "CRITICAL"
            )
    
    async def monitor_performance(self):
        """Monitor trading performance in real-time"""
        logger.info("📊 Performance monitoring started")
        
        while self.monitoring_active:
            try:
                await self.update_performance_metrics()
                await self.check_performance_alerts()
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                self.error_count += 1
                await asyncio.sleep(60)
    
    async def monitor_risk(self):
        """Monitor risk metrics in real-time"""
        logger.info("⚠️ Risk monitoring started")
        
        while self.monitoring_active:
            try:
                await self.update_risk_metrics()
                await self.check_risk_alerts()
                await asyncio.sleep(self.alert_config.risk_check_minutes * 60)
                
            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
                self.error_count += 1
                await asyncio.sleep(60)
    
    async def monitor_system_health(self):
        """Monitor system health and performance"""
        logger.info("🏥 System health monitoring started")
        
        while self.monitoring_active:
            try:
                await self.update_system_health()
                await self.check_system_alerts()
                await asyncio.sleep(self.alert_config.health_check_minutes * 60)
                
            except Exception as e:
                logger.error(f"System health monitoring error: {e}")
                self.error_count += 1
                await asyncio.sleep(60)
    
    async def update_performance_metrics(self):
        """Update real-time performance metrics"""
        try:
            current_time = datetime.now()
            
            # Calculate time-based PnL from trade history
            today = current_time.date()
            week_start = today - timedelta(days=7)
            month_start = today - timedelta(days=30)
            
            daily_trades = [t for t in self.trade_history 
                          if datetime.fromisoformat(t['exit_time']).date() == today]
            weekly_trades = [t for t in self.trade_history 
                           if datetime.fromisoformat(t['exit_time']).date() >= week_start]
            monthly_trades = [t for t in self.trade_history 
                            if datetime.fromisoformat(t['exit_time']).date() >= month_start]
            
            # Update metrics
            total_pnl = sum(t['pnl'] for t in self.trade_history)
            winning_trades = len([t for t in self.trade_history if t['pnl'] > 0])
            losing_trades = len([t for t in self.trade_history if t['pnl'] <= 0])
            
            self.performance_metrics.total_trades = len(self.trade_history)
            self.performance_metrics.winning_trades = winning_trades
            self.performance_metrics.losing_trades = losing_trades
            self.performance_metrics.total_pnl = total_pnl
            self.performance_metrics.win_rate = (winning_trades / len(self.trade_history) 
                                               if self.trade_history else 0)
            
            # Calculate profit factor
            gross_profit = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0)
            gross_loss = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0))
            self.performance_metrics.profit_factor = (gross_profit / gross_loss 
                                                    if gross_loss > 0 else float('inf'))
            
            # Time-based PnL
            self.performance_metrics.daily_pnl = sum(t['pnl'] for t in daily_trades)
            self.performance_metrics.weekly_pnl = sum(t['pnl'] for t in weekly_trades)
            self.performance_metrics.monthly_pnl = sum(t['pnl'] for t in monthly_trades)
            
            # Calculate Sharpe ratio (simplified)
            if len(self.trade_history) > 1:
                returns = [t['pnl_pct'] for t in self.trade_history]
                self.performance_metrics.sharpe_ratio = (
                    np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
                )
            
            # Calculate drawdown
            if self.trade_history:
                cumulative_returns = np.cumsum([t['pnl'] for t in self.trade_history])
                peak = np.maximum.accumulate(cumulative_returns)
                drawdown = (peak - cumulative_returns) / np.maximum(peak, 1)
                self.performance_metrics.max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
                self.performance_metrics.current_drawdown = drawdown[-1] if len(drawdown) > 0 else 0
            
            self.performance_metrics.last_updated = current_time
            
            # Log performance update
            if len(self.trade_history) > 0:
                logger.info(f"📊 Performance: {self.performance_metrics.total_trades} trades, "
                          f"{self.performance_metrics.win_rate:.1%} win rate, "
                          f"${self.performance_metrics.total_pnl:.2f} PnL")
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def update_risk_metrics(self):
        """Update risk monitoring metrics"""
        try:
            # Calculate portfolio risk based on active positions
            # This would normally connect to actual position data
            
            # Simulated risk calculations for demo
            self.risk_metrics.portfolio_risk = min(0.08, len(self.trade_history) * 0.01)
            self.risk_metrics.leverage_utilization = 0.6  # 60% of max leverage used
            
            # Daily loss tracking
            today = datetime.now().date()
            daily_losses = [abs(t['pnl']) for t in self.trade_history 
                          if datetime.fromisoformat(t['exit_time']).date() == today and t['pnl'] < 0]
            total_daily_loss = sum(daily_losses)
            max_daily_loss = 10000 * self.config.risk_management.max_daily_loss  # Assume $10k capital
            self.risk_metrics.daily_loss_limit_used = total_daily_loss / max_daily_loss
            
            # Consecutive losses
            recent_trades = sorted(self.trade_history, 
                                 key=lambda x: datetime.fromisoformat(x['exit_time']), 
                                 reverse=True)[:10]
            consecutive_losses = 0
            for trade in recent_trades:
                if trade['pnl'] < 0:
                    consecutive_losses += 1
                else:
                    break
            self.risk_metrics.consecutive_losses = consecutive_losses
            
            # Risk score calculation
            risk_factors = [
                self.risk_metrics.portfolio_risk > 0.06,  # >6% portfolio risk
                self.risk_metrics.daily_loss_limit_used > 0.7,  # >70% daily loss limit
                self.risk_metrics.consecutive_losses >= 3,  # 3+ consecutive losses
                self.performance_metrics.current_drawdown > 0.05,  # >5% drawdown
            ]
            
            risk_count = sum(risk_factors)
            if risk_count >= 3:
                self.risk_metrics.risk_score = "CRITICAL"
            elif risk_count >= 2:
                self.risk_metrics.risk_score = "HIGH"
            elif risk_count >= 1:
                self.risk_metrics.risk_score = "MEDIUM"
            else:
                self.risk_metrics.risk_score = "LOW"
            
            logger.debug(f"⚠️ Risk Score: {self.risk_metrics.risk_score}, "
                        f"Portfolio Risk: {self.risk_metrics.portfolio_risk:.2%}")
            
        except Exception as e:
            logger.error(f"Error updating risk metrics: {e}")
    
    async def update_system_health(self):
        """Update system health metrics"""
        try:
            # CPU and memory usage
            self.system_health.cpu_usage = psutil.cpu_percent(interval=1)
            self.system_health.memory_usage = psutil.virtual_memory().percent
            
            # Uptime calculation
            uptime = datetime.now() - self.start_time
            self.system_health.uptime_hours = uptime.total_seconds() / 3600
            
            # Error count and status
            self.system_health.error_count = self.error_count
            
            # Determine system status
            if self.error_count > 10:
                self.system_health.status = "CRITICAL"
            elif self.system_health.cpu_usage > 80 or self.system_health.memory_usage > 85:
                self.system_health.status = "WARNING"
            elif self.error_count > 5:
                self.system_health.status = "ERROR"
            else:
                self.system_health.status = "HEALTHY"
            
            # Last trade time
            if self.trade_history:
                last_trade = max(self.trade_history, key=lambda x: datetime.fromisoformat(x['exit_time']))
                self.system_health.last_trade_time = datetime.fromisoformat(last_trade['exit_time'])
            
            logger.debug(f"🏥 System Health: {self.system_health.status}, "
                        f"CPU: {self.system_health.cpu_usage:.1f}%, "
                        f"Memory: {self.system_health.memory_usage:.1f}%")
            
        except Exception as e:
            logger.error(f"Error updating system health: {e}")
    
    async def check_performance_alerts(self):
        """Check for performance-based alerts"""
        try:
            current_time = datetime.now()
            
            # Maximum drawdown alert
            if (self.performance_metrics.current_drawdown > self.alert_config.max_drawdown_alert
                and self.should_send_alert("max_drawdown", hours=1)):
                
                await self.send_alert(
                    "📉 High Drawdown Alert",
                    f"Current drawdown: {self.performance_metrics.current_drawdown:.2%}\n"
                    f"Max drawdown: {self.performance_metrics.max_drawdown:.2%}\n"
                    f"Alert threshold: {self.alert_config.max_drawdown_alert:.2%}",
                    "WARNING"
                )
            
            # Daily loss alert
            if (abs(self.performance_metrics.daily_pnl) > 
                10000 * self.alert_config.daily_loss_alert  # Assume $10k capital
                and self.performance_metrics.daily_pnl < 0
                and self.should_send_alert("daily_loss", hours=2)):
                
                await self.send_alert(
                    "💸 Daily Loss Alert",
                    f"Daily P&L: ${self.performance_metrics.daily_pnl:.2f}\n"
                    f"Daily loss limit: ${10000 * self.alert_config.daily_loss_alert:.2f}",
                    "WARNING"
                )
            
            # Consecutive losses alert
            if (self.risk_metrics.consecutive_losses >= self.alert_config.consecutive_loss_alert
                and self.should_send_alert("consecutive_losses", hours=1)):
                
                await self.send_alert(
                    "🔴 Consecutive Losses Alert",
                    f"Consecutive losses: {self.risk_metrics.consecutive_losses}\n"
                    f"Consider reviewing strategy or reducing position sizes",
                    "WARNING"
                )
            
            # Excellent performance alert
            if (self.performance_metrics.daily_pnl > 500  # $500 daily profit
                and self.should_send_alert("excellent_performance", hours=6)):
                
                await self.send_alert(
                    "🎉 Excellent Performance",
                    f"Daily P&L: ${self.performance_metrics.daily_pnl:.2f}\n"
                    f"Win Rate: {self.performance_metrics.win_rate:.1%}\n"
                    f"Total Trades: {self.performance_metrics.total_trades}",
                    "INFO"
                )
            
        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")
    
    async def check_risk_alerts(self):
        """Check for risk-based alerts"""
        try:
            # High risk score alert
            if (self.risk_metrics.risk_score in ["HIGH", "CRITICAL"]
                and self.should_send_alert("high_risk", minutes=30)):
                
                severity = "CRITICAL" if self.risk_metrics.risk_score == "CRITICAL" else "WARNING"
                await self.send_alert(
                    f"⚠️ Risk Level: {self.risk_metrics.risk_score}",
                    f"Portfolio Risk: {self.risk_metrics.portfolio_risk:.2%}\n"
                    f"Daily Loss Used: {self.risk_metrics.daily_loss_limit_used:.1%}\n"
                    f"Consecutive Losses: {self.risk_metrics.consecutive_losses}\n"
                    f"Current Drawdown: {self.performance_metrics.current_drawdown:.2%}",
                    severity
                )
            
            # Position size alert
            if (self.risk_metrics.portfolio_risk > self.alert_config.position_size_alert
                and self.should_send_alert("position_size", hours=1)):
                
                await self.send_alert(
                    "📊 High Position Size Alert",
                    f"Current portfolio risk: {self.risk_metrics.portfolio_risk:.2%}\n"
                    f"Threshold: {self.alert_config.position_size_alert:.2%}\n"
                    f"Consider reducing position sizes",
                    "WARNING"
                )
            
        except Exception as e:
            logger.error(f"Error checking risk alerts: {e}")
    
    async def check_system_alerts(self):
        """Check for system health alerts"""
        try:
            # System status alert
            if (self.system_health.status in ["ERROR", "CRITICAL"]
                and self.should_send_alert("system_status", minutes=15)):
                
                severity = "CRITICAL" if self.system_health.status == "CRITICAL" else "WARNING"
                await self.send_alert(
                    f"🏥 System Status: {self.system_health.status}",
                    f"CPU Usage: {self.system_health.cpu_usage:.1f}%\n"
                    f"Memory Usage: {self.system_health.memory_usage:.1f}%\n"
                    f"Error Count: {self.system_health.error_count}\n"
                    f"Uptime: {self.system_health.uptime_hours:.1f} hours",
                    severity
                )
            
            # No trading activity alert
            if (self.system_health.last_trade_time and
                datetime.now() - self.system_health.last_trade_time > timedelta(hours=6)
                and self.should_send_alert("no_trading", hours=6)):
                
                await self.send_alert(
                    "😴 No Trading Activity",
                    f"Last trade: {self.system_health.last_trade_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Time since last trade: {datetime.now() - self.system_health.last_trade_time}\n"
                    f"Check if market conditions are suitable for strategy",
                    "INFO"
                )
            
        except Exception as e:
            logger.error(f"Error checking system alerts: {e}")
    
    def should_send_alert(self, alert_type: str, minutes: int = 60, hours: int = 0) -> bool:
        """Check if enough time has passed since last alert of this type"""
        total_minutes = minutes + (hours * 60)
        last_alert = self.last_alert_times.get(alert_type)
        
        if last_alert is None:
            return True
        
        time_since_last = datetime.now() - last_alert
        return time_since_last > timedelta(minutes=total_minutes)
    
    async def send_alert(self, title: str, message: str, severity: str = "INFO"):
        """Send alert via configured channels"""
        try:
            alert_data = {
                'timestamp': datetime.now().isoformat(),
                'title': title,
                'message': message,
                'severity': severity,
                'performance': asdict(self.performance_metrics),
                'risk': asdict(self.risk_metrics),
                'system': asdict(self.system_health)
            }
            
            # Store alert in history
            self.alert_history.append(alert_data)
            
            # Format message with emojis based on severity
            emoji_map = {
                'INFO': '💡',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }
            
            emoji = emoji_map.get(severity, '📢')
            formatted_message = f"{emoji} {title}\n\n{message}"
            
            # Send via Telegram
            if self.telegram_bot and self.alert_config.telegram_chat_id:
                try:
                    await self.telegram_bot.send_message(
                        chat_id=self.alert_config.telegram_chat_id,
                        text=formatted_message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"📱 Telegram alert sent: {title}")
                except Exception as e:
                    logger.error(f"Failed to send Telegram alert: {e}")
            
            # Send via webhook (if configured)
            if self.alert_config.webhook_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            self.alert_config.webhook_url,
                            json=alert_data,
                            timeout=10
                        )
                    logger.info(f"🌐 Webhook alert sent: {title}")
                except Exception as e:
                    logger.error(f"Failed to send webhook alert: {e}")
            
            # Log alert locally
            logger.info(f"🚨 ALERT [{severity}]: {title}")
            
            # Update last alert time
            alert_type = title.lower().replace(' ', '_')
            self.last_alert_times[alert_type] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def generate_periodic_reports(self):
        """Generate periodic performance reports"""
        logger.info("📋 Periodic reporting started")
        
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.alert_config.performance_report_hours * 3600)
                await self.generate_performance_report()
                
            except Exception as e:
                logger.error(f"Error generating periodic reports: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def generate_performance_report(self):
        """Generate comprehensive performance report"""
        try:
            current_time = datetime.now()
            
            # Create report
            report = {
                'timestamp': current_time.isoformat(),
                'period': f'{self.alert_config.performance_report_hours}h Report',
                'performance': asdict(self.performance_metrics),
                'risk': asdict(self.risk_metrics),
                'system_health': asdict(self.system_health),
                'recent_trades': self.trade_history[-10:] if self.trade_history else [],
                'recent_alerts': self.alert_history[-5:] if self.alert_history else []
            }
            
            # Save report to file
            timestamp_str = current_time.strftime("%Y%m%d_%H%M%S")
            report_file = self.report_dir / f"performance_report_{timestamp_str}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Generate summary message
            summary = (
                f"📊 {self.alert_config.performance_report_hours}h Performance Report\n\n"
                f"💰 P&L: ${self.performance_metrics.total_pnl:.2f} "
                f"(${self.performance_metrics.daily_pnl:.2f} today)\n"
                f"📈 Trades: {self.performance_metrics.total_trades} "
                f"({self.performance_metrics.win_rate:.1%} win rate)\n"
                f"⚠️ Risk Score: {self.risk_metrics.risk_score}\n"
                f"🏥 System: {self.system_health.status}\n"
                f"📋 Report saved: {report_file.name}"
            )
            
            await self.send_alert("Performance Report", summary, "INFO")
            
            logger.info(f"📋 Performance report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
    
    async def cleanup_old_data(self):
        """Clean up old monitoring data"""
        logger.info("🧹 Data cleanup task started")
        
        while self.monitoring_active:
            try:
                # Clean up every 24 hours
                await asyncio.sleep(24 * 3600)
                
                current_time = datetime.now()
                cutoff_date = current_time - timedelta(days=30)
                
                # Clean old alerts (keep 30 days)
                self.alert_history = [
                    alert for alert in self.alert_history
                    if datetime.fromisoformat(alert['timestamp']) > cutoff_date
                ]
                
                # Clean old trade history (keep 30 days)
                self.trade_history = [
                    trade for trade in self.trade_history
                    if datetime.fromisoformat(trade['exit_time']) > cutoff_date
                ]
                
                # Clean old report files (keep 7 days)
                report_cutoff = current_time - timedelta(days=7)
                for report_file in self.report_dir.glob("performance_report_*.json"):
                    try:
                        file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                        if file_time < report_cutoff:
                            report_file.unlink()
                    except Exception as e:
                        logger.error(f"Error deleting old report {report_file}: {e}")
                
                logger.info("🧹 Data cleanup completed")
                
            except Exception as e:
                logger.error(f"Error in data cleanup: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    def record_trade(self, trade_data: Dict):
        """Record a completed trade for monitoring"""
        try:
            # Add timestamp if not present
            if 'exit_time' not in trade_data:
                trade_data['exit_time'] = datetime.now().isoformat()
            
            # Store trade
            self.trade_history.append(trade_data)
            
            # Trigger immediate performance update
            asyncio.create_task(self.update_performance_metrics())
            
            logger.info(f"📝 Trade recorded: {trade_data['symbol']} "
                       f"${trade_data['pnl']:.2f}")
            
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
    
    def get_current_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'performance': asdict(self.performance_metrics),
            'risk': asdict(self.risk_metrics),
            'system_health': asdict(self.system_health),
            'monitoring_active': self.monitoring_active,
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
        }
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        
        # Send shutdown notification
        await self.send_alert(
            "🔚 Monitor Shutdown",
            f"High Volatility Trading Monitor stopped\n"
            f"Total uptime: {self.system_health.uptime_hours:.1f} hours\n"
            f"Final P&L: ${self.performance_metrics.total_pnl:.2f}",
            "INFO"
        )
        
        logger.info("🔍 High Volatility Trading Monitor stopped")

# Configuration and startup
def create_default_alert_config() -> AlertConfig:
    """Create default alert configuration"""
    return AlertConfig(
        telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
        webhook_url=os.getenv('MONITOR_WEBHOOK_URL', ''),
        
        max_drawdown_alert=0.05,
        daily_loss_alert=0.03,
        consecutive_loss_alert=3,
        position_size_alert=0.06,
        
        performance_report_hours=6,
        health_check_minutes=15,
        risk_check_minutes=5
    )

async def main():
    """Main monitoring execution"""
    # Create configurations
    config = HighVolatilityConfig()
    alert_config = create_default_alert_config()
    
    # Create monitor
    monitor = VolatilityMonitor(config, alert_config)
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    print("HIGH VOLATILITY TRADING MONITOR")
    print("=" * 50)
    print("🔍 Real-time performance tracking")
    print("⚠️ Risk monitoring and alerts") 
    print("🏥 System health monitoring")
    print("📱 Telegram notifications")
    print("📊 Periodic performance reports")
    print("=" * 50)
    
    asyncio.run(main())