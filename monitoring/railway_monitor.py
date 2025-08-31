#!/usr/bin/env python3
"""
Railway Trading Bot Monitor
Real-time monitoring system for Railway-deployed trading bot
"""
import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger_config import setup_logger
from utils.telegram_notifier import TelegramNotifier

# Set up logging
logger = setup_logger("RailwayMonitor", level=logging.INFO)

class RailwayBotMonitor:
    """Comprehensive monitoring system for Railway trading bot"""
    
    def __init__(self, railway_url: str = "https://railway-up-production-f151.up.railway.app"):
        """Initialize the Railway bot monitor"""
        self.railway_url = railway_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.telegram = TelegramNotifier()
        
        # Monitoring state
        self.monitoring = False
        self.last_successful_health_check = None
        self.consecutive_failures = 0
        self.alert_sent = False
        
        # Performance tracking
        self.performance_history = []
        self.trading_history = []
        self.health_history = []
        
        # Monitoring intervals (seconds)
        self.health_check_interval = 30
        self.trading_check_interval = 10
        self.metrics_check_interval = 60
        self.alert_threshold = 3  # consecutive failures before alert
        
        # Initialize data storage directory
        self.data_dir = project_root / "monitoring" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Railway Monitor initialized for: {self.railway_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def start_monitoring(self):
        """Start comprehensive monitoring of Railway bot"""
        logger.info("🔍 Starting Railway bot monitoring...")
        self.monitoring = True
        
        # Send startup notification
        await self.telegram.send_message(
            "🔍 **Railway Monitor Started**\n"
            f"Target: {self.railway_url}\n"
            f"Health checks: Every {self.health_check_interval}s\n"
            f"Trading checks: Every {self.trading_check_interval}s\n"
            f"Metrics checks: Every {self.metrics_check_interval}s"
        )
        
        try:
            # Create monitoring tasks
            tasks = [
                asyncio.create_task(self._health_monitor(), name="health_monitor"),
                asyncio.create_task(self._trading_monitor(), name="trading_monitor"),
                asyncio.create_task(self._performance_monitor(), name="performance_monitor"),
                asyncio.create_task(self._log_collector(), name="log_collector")
            ]
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring: {e}", exc_info=True)
        finally:
            self.monitoring = False
            await self.telegram.send_message("🛑 **Railway Monitor Stopped**")
    
    async def _health_monitor(self):
        """Monitor health endpoints continuously"""
        logger.info("Starting health monitoring...")
        
        while self.monitoring:
            try:
                # Check multiple health endpoints
                health_data = await self._check_all_health_endpoints()
                
                if health_data['overall_healthy']:
                    self.consecutive_failures = 0
                    if self.alert_sent:
                        await self.telegram.send_message("✅ **Railway Bot Recovered**\nAll health checks passing")
                        self.alert_sent = False
                    
                    self.last_successful_health_check = datetime.now()
                else:
                    self.consecutive_failures += 1
                    logger.warning(f"Health check failed ({self.consecutive_failures}/{self.alert_threshold})")
                    
                    if self.consecutive_failures >= self.alert_threshold and not self.alert_sent:
                        await self._send_health_alert(health_data)
                        self.alert_sent = True
                
                # Store health data
                self.health_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'data': health_data
                })
                
                # Keep only last 1000 entries
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]
                
                # Log status every 10 checks
                if len(self.health_history) % 10 == 0:
                    status = "✅ HEALTHY" if health_data['overall_healthy'] else "❌ UNHEALTHY"
                    logger.info(f"Health status: {status} (Checks: {len(self.health_history)})")
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                self.consecutive_failures += 1
            
            await asyncio.sleep(self.health_check_interval)
    
    async def _trading_monitor(self):
        """Monitor trading activity and performance"""
        logger.info("Starting trading activity monitoring...")
        
        last_trade_count = 0
        
        while self.monitoring:
            try:
                # Get trading metrics
                trading_data = await self._get_trading_metrics()
                
                if trading_data:
                    current_trade_count = trading_data.get('total_trades', 0)
                    
                    # Check for new trades
                    if current_trade_count > last_trade_count:
                        new_trades = current_trade_count - last_trade_count
                        logger.info(f"📈 {new_trades} new trades detected (Total: {current_trade_count})")
                        
                        # Send trading update if significant activity
                        if new_trades >= 5:  # 5 or more trades in interval
                            await self._send_trading_update(trading_data, new_trades)
                    
                    last_trade_count = current_trade_count
                    
                    # Store trading data
                    self.trading_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'data': trading_data
                    })
                    
                    # Keep only last 2000 entries
                    if len(self.trading_history) > 2000:
                        self.trading_history = self.trading_history[-2000:]
                
            except Exception as e:
                logger.error(f"Error in trading monitoring: {e}")
            
            await asyncio.sleep(self.trading_check_interval)
    
    async def _performance_monitor(self):
        """Monitor performance metrics and system resources"""
        logger.info("Starting performance monitoring...")
        
        while self.monitoring:
            try:
                # Get performance metrics
                metrics_data = await self._get_detailed_metrics()
                
                if metrics_data:
                    # Store performance data
                    self.performance_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'data': metrics_data
                    })
                    
                    # Check for performance issues
                    await self._check_performance_alerts(metrics_data)
                    
                    # Keep only last 500 entries (covers ~8 hours at 1min intervals)
                    if len(self.performance_history) > 500:
                        self.performance_history = self.performance_history[-500:]
                    
                    # Log performance summary every 15 minutes
                    if len(self.performance_history) % 15 == 0:
                        await self._log_performance_summary(metrics_data)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
            
            await asyncio.sleep(self.metrics_check_interval)
    
    async def _log_collector(self):
        """Collect and store monitoring logs"""
        logger.info("Starting log collection...")
        
        while self.monitoring:
            try:
                # Save monitoring data to files every 5 minutes
                await asyncio.sleep(300)  # 5 minutes
                await self._save_monitoring_data()
                
            except Exception as e:
                logger.error(f"Error in log collection: {e}")
    
    async def _check_all_health_endpoints(self) -> Dict:
        """Check all health endpoints and return comprehensive status"""
        endpoints = {
            'health': '/health',
            'health_detailed': '/health/detailed',
            'ready': '/ready',
            'live': '/live',
            'metrics': '/metrics'
        }
        
        results = {}
        overall_healthy = True
        
        for name, endpoint in endpoints.items():
            try:
                url = f"{self.railway_url}{endpoint}"
                async with self.session.get(url) as response:
                    success = response.status == 200
                    results[name] = {
                        'status_code': response.status,
                        'success': success,
                        'response_time': response.headers.get('X-Response-Time', 'N/A'),
                        'data': await response.json() if success else None
                    }
                    
                    if not success:
                        overall_healthy = False
                        
            except Exception as e:
                results[name] = {
                    'status_code': None,
                    'success': False,
                    'error': str(e),
                    'data': None
                }
                overall_healthy = False
        
        return {
            'overall_healthy': overall_healthy,
            'endpoints': results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _get_trading_metrics(self) -> Optional[Dict]:
        """Get trading activity metrics"""
        try:
            url = f"{self.railway_url}/metrics"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.debug(f"Error getting trading metrics: {e}")
            return None
    
    async def _get_detailed_metrics(self) -> Optional[Dict]:
        """Get detailed performance metrics"""
        try:
            url = f"{self.railway_url}/health/detailed"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.debug(f"Error getting detailed metrics: {e}")
            return None
    
    async def _send_health_alert(self, health_data: Dict):
        """Send health alert notification"""
        failed_endpoints = [
            name for name, data in health_data['endpoints'].items() 
            if not data['success']
        ]
        
        alert_message = (
            f"🚨 **Railway Bot Health Alert**\n"
            f"Consecutive failures: {self.consecutive_failures}\n"
            f"Failed endpoints: {', '.join(failed_endpoints)}\n"
            f"Last success: {self.last_successful_health_check}\n"
            f"URL: {self.railway_url}"
        )
        
        await self.telegram.send_message(alert_message)
        logger.error(f"Health alert sent: {len(failed_endpoints)} endpoints failing")
    
    async def _send_trading_update(self, trading_data: Dict, new_trades: int):
        """Send trading activity update"""
        message = (
            f"📊 **Trading Activity Update**\n"
            f"New trades: {new_trades}\n"
            f"Total trades: {trading_data.get('total_trades', 'N/A')}\n"
            f"Success rate: {trading_data.get('success_rate', 'N/A'):.1%}\n"
            f"P&L: {trading_data.get('total_pnl', 'N/A'):.2%}\n"
            f"Active positions: {trading_data.get('active_positions', 'N/A')}"
        )
        
        await self.telegram.send_message(message)
    
    async def _check_performance_alerts(self, metrics_data: Dict):
        """Check for performance issues and send alerts"""
        alerts = []
        
        # Check memory usage
        memory_usage = metrics_data.get('memory_usage_percent', 0)
        if memory_usage > 90:
            alerts.append(f"High memory usage: {memory_usage:.1f}%")
        
        # Check response times
        avg_response_time = metrics_data.get('average_response_time', 0)
        if avg_response_time > 5000:  # 5 seconds
            alerts.append(f"High response time: {avg_response_time:.0f}ms")
        
        # Check error rate
        error_rate = metrics_data.get('error_rate', 0)
        if error_rate > 10:  # 10% error rate
            alerts.append(f"High error rate: {error_rate:.1f}%")
        
        # Check trading performance
        win_rate = metrics_data.get('win_rate', 100)
        if win_rate < 30:  # Less than 30% win rate
            alerts.append(f"Low win rate: {win_rate:.1f}%")
        
        if alerts:
            alert_message = (
                f"⚠️ **Performance Alerts**\n" +
                "\n".join(f"• {alert}" for alert in alerts)
            )
            await self.telegram.send_message(alert_message)
    
    async def _log_performance_summary(self, metrics_data: Dict):
        """Log performance summary"""
        summary = (
            f"Performance Summary - "
            f"Memory: {metrics_data.get('memory_usage_percent', 0):.1f}%, "
            f"Response: {metrics_data.get('average_response_time', 0):.0f}ms, "
            f"Trades: {metrics_data.get('total_trades', 0)}, "
            f"Win Rate: {metrics_data.get('win_rate', 0):.1f}%"
        )
        logger.info(summary)
    
    async def _save_monitoring_data(self):
        """Save monitoring data to files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save health data
            health_file = self.data_dir / f"health_{timestamp}.json"
            with open(health_file, 'w') as f:
                json.dump(self.health_history[-50:], f, indent=2)  # Last 50 entries
            
            # Save trading data
            trading_file = self.data_dir / f"trading_{timestamp}.json"
            with open(trading_file, 'w') as f:
                json.dump(self.trading_history[-100:], f, indent=2)  # Last 100 entries
            
            # Save performance data
            performance_file = self.data_dir / f"performance_{timestamp}.json"
            with open(performance_file, 'w') as f:
                json.dump(self.performance_history[-50:], f, indent=2)  # Last 50 entries
            
            logger.debug(f"Monitoring data saved at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error saving monitoring data: {e}")
    
    def get_status_summary(self) -> Dict:
        """Get current monitoring status summary"""
        return {
            'monitoring_active': self.monitoring,
            'last_successful_health_check': self.last_successful_health_check.isoformat() if self.last_successful_health_check else None,
            'consecutive_failures': self.consecutive_failures,
            'alert_sent': self.alert_sent,
            'total_health_checks': len(self.health_history),
            'total_trading_records': len(self.trading_history),
            'total_performance_records': len(self.performance_history)
        }

async def main():
    """Main entry point for Railway monitor"""
    logger.info("🚀 Starting Railway Bot Monitor...")
    
    # Get Railway URL from environment or use default
    railway_url = os.getenv('RAILWAY_BOT_URL', 'https://railway-up-production-f151.up.railway.app')
    
    try:
        async with RailwayBotMonitor(railway_url) as monitor:
            await monitor.start_monitoring()
            
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in monitor: {e}", exc_info=True)
    finally:
        logger.info("Railway monitor terminated")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)