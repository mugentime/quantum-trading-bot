#!/usr/bin/env python3
"""
Railway Performance Tracker
Historical performance logging and analysis for Railway trading bot
"""
import asyncio
import aiohttp
import json
import csv
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import os
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger_config import setup_logger
from utils.telegram_notifier import TelegramNotifier

# Set up logging
logger = setup_logger("PerformanceTracker", level=logging.INFO)

class PerformanceTracker:
    """Historical performance tracking and analysis for Railway bot"""
    
    def __init__(self, railway_url: str = "https://railway-up-production-f151.up.railway.app"):
        """Initialize the performance tracker"""
        self.railway_url = railway_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.telegram = TelegramNotifier()
        
        # Tracking state
        self.tracking = False
        self.tracking_interval = 60  # Track every minute
        
        # Data storage setup
        self.data_dir = project_root / "monitoring" / "performance_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database setup
        self.db_path = self.data_dir / "performance_history.db"
        self._init_database()
        
        # CSV files setup
        self.trading_csv = self.data_dir / "trading_performance.csv"
        self.system_csv = self.data_dir / "system_performance.csv"
        self.alerts_csv = self.data_dir / "performance_alerts.csv"
        
        self._init_csv_files()
        
        # Performance targets for 620% monthly target
        self.targets = {
            'daily_target_percent': 14.0,  # 14% daily
            'monthly_target_percent': 620.0,  # 620% monthly
            'min_win_rate': 60.0,  # Minimum 60% win rate
            'max_drawdown': 15.0,  # Maximum 15% drawdown
            'target_trades_per_day': 50,  # High frequency target
            'max_position_hold_time': 300,  # 5 minutes max hold
        }
        
        logger.info(f"Performance Tracker initialized for: {self.railway_url}")
        logger.info(f"Target: {self.targets['monthly_target_percent']}% monthly return")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=50, limit_per_host=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _init_database(self):
        """Initialize SQLite database for performance tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Trading performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_trades INTEGER,
                    successful_trades INTEGER,
                    total_pnl REAL,
                    daily_pnl REAL,
                    win_rate REAL,
                    avg_trade_duration REAL,
                    max_drawdown REAL,
                    active_positions INTEGER,
                    daily_target_progress REAL,
                    monthly_target_progress REAL
                )
            ''')
            
            # System performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    memory_usage_percent REAL,
                    cpu_usage_percent REAL,
                    response_time_ms REAL,
                    request_count INTEGER,
                    error_rate REAL,
                    uptime_hours REAL,
                    restart_count INTEGER,
                    health_status TEXT
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    metric_value REAL,
                    threshold REAL,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Daily summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    total_trades INTEGER,
                    successful_trades INTEGER,
                    daily_pnl REAL,
                    win_rate REAL,
                    max_drawdown REAL,
                    avg_response_time REAL,
                    uptime_percent REAL,
                    target_achieved BOOLEAN
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Performance tracking database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
    
    def _init_csv_files(self):
        """Initialize CSV files for performance tracking"""
        try:
            # Trading performance CSV
            if not self.trading_csv.exists():
                with open(self.trading_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'total_trades', 'successful_trades', 'total_pnl',
                        'daily_pnl', 'win_rate', 'avg_trade_duration', 'max_drawdown',
                        'active_positions', 'daily_target_progress', 'monthly_target_progress'
                    ])
            
            # System performance CSV
            if not self.system_csv.exists():
                with open(self.system_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'memory_usage_percent', 'cpu_usage_percent',
                        'response_time_ms', 'request_count', 'error_rate',
                        'uptime_hours', 'restart_count', 'health_status'
                    ])
            
            # Alerts CSV
            if not self.alerts_csv.exists():
                with open(self.alerts_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'alert_type', 'severity', 'message',
                        'metric_value', 'threshold', 'resolved'
                    ])
            
            logger.info("CSV files initialized for performance tracking")
            
        except Exception as e:
            logger.error(f"Error initializing CSV files: {e}")
    
    async def start_tracking(self):
        """Start performance tracking"""
        logger.info("🚀 Starting Railway bot performance tracking...")
        self.tracking = True
        
        # Send startup notification
        await self.telegram.send_message(
            "📊 **Performance Tracker Started**\n"
            f"Target: {self.railway_url}\n"
            f"Tracking interval: {self.tracking_interval}s\n"
            f"Monthly target: {self.targets['monthly_target_percent']}%\n"
            f"Daily target: {self.targets['daily_target_percent']}%"
        )
        
        try:
            # Create tracking tasks
            tasks = [
                asyncio.create_task(self._performance_tracking_loop(), name="performance_tracker"),
                asyncio.create_task(self._hourly_analysis_loop(), name="hourly_analyzer"),
                asyncio.create_task(self._daily_summary_loop(), name="daily_summarizer")
            ]
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            logger.info("Performance tracking stopped by user")
        except Exception as e:
            logger.error(f"Error in performance tracking: {e}", exc_info=True)
        finally:
            self.tracking = False
            await self.telegram.send_message("🛑 **Performance Tracker Stopped**")
    
    async def _performance_tracking_loop(self):
        """Main performance tracking loop"""
        logger.info("Starting performance data collection...")
        
        while self.tracking:
            try:
                # Collect all performance data
                trading_data = await self._collect_trading_performance()
                system_data = await self._collect_system_performance()
                
                # Store data
                if trading_data:
                    await self._store_trading_performance(trading_data)
                    await self._check_trading_alerts(trading_data)
                
                if system_data:
                    await self._store_system_performance(system_data)
                    await self._check_system_alerts(system_data)
                
                # Log progress every 10 intervals
                current_minute = datetime.now().minute
                if current_minute % 10 == 0:
                    await self._log_tracking_progress(trading_data, system_data)
                
            except Exception as e:
                logger.error(f"Error in performance tracking loop: {e}")
            
            await asyncio.sleep(self.tracking_interval)
    
    async def _hourly_analysis_loop(self):
        """Hourly performance analysis loop"""
        while self.tracking:
            try:
                # Wait for next hour
                await asyncio.sleep(3600)  # 1 hour
                
                # Generate hourly analysis
                await self._generate_hourly_analysis()
                
            except Exception as e:
                logger.error(f"Error in hourly analysis: {e}")
    
    async def _daily_summary_loop(self):
        """Daily summary generation loop"""
        while self.tracking:
            try:
                # Check if it's a new day
                now = datetime.now()
                if now.hour == 0 and now.minute == 0:
                    await self._generate_daily_summary()
                    await asyncio.sleep(3600)  # Skip rest of hour
                else:
                    await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in daily summary loop: {e}")
    
    async def _collect_trading_performance(self) -> Optional[Dict]:
        """Collect trading performance metrics"""
        try:
            url = f"{self.railway_url}/metrics"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Calculate derived metrics
                    return self._calculate_trading_metrics(data)
                    
                return None
                
        except Exception as e:
            logger.debug(f"Error collecting trading performance: {e}")
            return None
    
    async def _collect_system_performance(self) -> Optional[Dict]:
        """Collect system performance metrics"""
        try:
            url = f"{self.railway_url}/health/detailed"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
                
        except Exception as e:
            logger.debug(f"Error collecting system performance: {e}")
            return None
    
    def _calculate_trading_metrics(self, data: Dict) -> Dict:
        """Calculate enhanced trading performance metrics"""
        try:
            # Extract basic metrics
            total_trades = data.get('total_trades', 0)
            successful_trades = data.get('successful_trades', 0)
            total_pnl = data.get('total_pnl', 0.0)
            daily_pnl = data.get('daily_pnl', 0.0)
            active_positions = data.get('active_positions', 0)
            
            # Calculate derived metrics
            win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate progress toward targets
            daily_target_progress = (daily_pnl / self.targets['daily_target_percent']) * 100
            monthly_target_progress = (total_pnl / self.targets['monthly_target_percent']) * 100
            
            # Get trade history for advanced metrics
            trades = data.get('trades', [])
            avg_trade_duration = 0
            max_drawdown = 0
            
            if trades:
                durations = [trade.get('duration_seconds', 0) for trade in trades]
                avg_trade_duration = statistics.mean(durations) if durations else 0
                
                # Calculate max drawdown
                pnls = [trade.get('pnl_percent', 0) for trade in trades]
                if pnls:
                    cumulative_pnl = 0
                    peak = 0
                    max_drawdown = 0
                    
                    for pnl in pnls:
                        cumulative_pnl += pnl
                        if cumulative_pnl > peak:
                            peak = cumulative_pnl
                        drawdown = (peak - cumulative_pnl) / peak * 100 if peak > 0 else 0
                        max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'total_pnl': total_pnl,
                'daily_pnl': daily_pnl,
                'win_rate': win_rate,
                'avg_trade_duration': avg_trade_duration,
                'max_drawdown': max_drawdown,
                'active_positions': active_positions,
                'daily_target_progress': daily_target_progress,
                'monthly_target_progress': monthly_target_progress
            }
            
        except Exception as e:
            logger.error(f"Error calculating trading metrics: {e}")
            return {}
    
    async def _store_trading_performance(self, data: Dict):
        """Store trading performance data"""
        try:
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_performance 
                (total_trades, successful_trades, total_pnl, daily_pnl, win_rate,
                 avg_trade_duration, max_drawdown, active_positions, 
                 daily_target_progress, monthly_target_progress)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['total_trades'], data['successful_trades'], data['total_pnl'],
                data['daily_pnl'], data['win_rate'], data['avg_trade_duration'],
                data['max_drawdown'], data['active_positions'],
                data['daily_target_progress'], data['monthly_target_progress']
            ))
            
            conn.commit()
            conn.close()
            
            # Append to CSV
            with open(self.trading_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['timestamp'], data['total_trades'], data['successful_trades'],
                    data['total_pnl'], data['daily_pnl'], data['win_rate'],
                    data['avg_trade_duration'], data['max_drawdown'], data['active_positions'],
                    data['daily_target_progress'], data['monthly_target_progress']
                ])
            
        except Exception as e:
            logger.error(f"Error storing trading performance: {e}")
    
    async def _store_system_performance(self, data: Dict):
        """Store system performance data"""
        try:
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_performance 
                (memory_usage_percent, cpu_usage_percent, response_time_ms,
                 request_count, error_rate, uptime_hours, restart_count, health_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('memory_usage_percent', 0),
                data.get('cpu_usage_percent', 0),
                data.get('average_response_time', 0),
                data.get('total_requests', 0),
                data.get('error_rate', 0),
                data.get('uptime_hours', 0),
                data.get('restart_count', 0),
                'healthy' if data.get('healthy', True) else 'unhealthy'
            ))
            
            conn.commit()
            conn.close()
            
            # Append to CSV
            with open(self.system_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    data.get('memory_usage_percent', 0),
                    data.get('cpu_usage_percent', 0),
                    data.get('average_response_time', 0),
                    data.get('total_requests', 0),
                    data.get('error_rate', 0),
                    data.get('uptime_hours', 0),
                    data.get('restart_count', 0),
                    'healthy' if data.get('healthy', True) else 'unhealthy'
                ])
            
        except Exception as e:
            logger.error(f"Error storing system performance: {e}")
    
    async def _check_trading_alerts(self, data: Dict):
        """Check for trading performance alerts"""
        alerts = []
        
        # Check win rate
        win_rate = data.get('win_rate', 0)
        if win_rate < self.targets['min_win_rate']:
            alerts.append({
                'type': 'win_rate',
                'severity': 'high',
                'message': f"Win rate below target: {win_rate:.1f}% < {self.targets['min_win_rate']}%",
                'value': win_rate,
                'threshold': self.targets['min_win_rate']
            })
        
        # Check daily target progress
        daily_progress = data.get('daily_target_progress', 0)
        if daily_progress < 50 and datetime.now().hour > 12:  # After noon
            alerts.append({
                'type': 'daily_target',
                'severity': 'medium',
                'message': f"Daily target progress low: {daily_progress:.1f}%",
                'value': daily_progress,
                'threshold': 50
            })
        
        # Check drawdown
        drawdown = data.get('max_drawdown', 0)
        if drawdown > self.targets['max_drawdown']:
            alerts.append({
                'type': 'drawdown',
                'severity': 'high',
                'message': f"Maximum drawdown exceeded: {drawdown:.1f}% > {self.targets['max_drawdown']}%",
                'value': drawdown,
                'threshold': self.targets['max_drawdown']
            })
        
        # Store and send alerts
        for alert in alerts:
            await self._store_alert(alert)
            await self._send_alert(alert)
    
    async def _check_system_alerts(self, data: Dict):
        """Check for system performance alerts"""
        alerts = []
        
        # Check memory usage
        memory_usage = data.get('memory_usage_percent', 0)
        if memory_usage > 90:
            alerts.append({
                'type': 'memory',
                'severity': 'high',
                'message': f"High memory usage: {memory_usage:.1f}%",
                'value': memory_usage,
                'threshold': 90
            })
        
        # Check response time
        response_time = data.get('average_response_time', 0)
        if response_time > 5000:  # 5 seconds
            alerts.append({
                'type': 'response_time',
                'severity': 'medium',
                'message': f"High response time: {response_time:.0f}ms",
                'value': response_time,
                'threshold': 5000
            })
        
        # Check error rate
        error_rate = data.get('error_rate', 0)
        if error_rate > 5:  # 5% error rate
            alerts.append({
                'type': 'error_rate',
                'severity': 'medium',
                'message': f"High error rate: {error_rate:.1f}%",
                'value': error_rate,
                'threshold': 5
            })
        
        # Store and send alerts
        for alert in alerts:
            await self._store_alert(alert)
            await self._send_alert(alert)
    
    async def _store_alert(self, alert: Dict):
        """Store alert in database and CSV"""
        try:
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_alerts 
                (alert_type, severity, message, metric_value, threshold)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                alert['type'], alert['severity'], alert['message'],
                alert['value'], alert['threshold']
            ))
            
            conn.commit()
            conn.close()
            
            # Append to CSV
            with open(self.alerts_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    alert['type'], alert['severity'], alert['message'],
                    alert['value'], alert['threshold'], False
                ])
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def _send_alert(self, alert: Dict):
        """Send alert notification"""
        try:
            severity_icons = {
                'high': '🚨',
                'medium': '⚠️',
                'low': 'ℹ️'
            }
            
            icon = severity_icons.get(alert['severity'], 'ℹ️')
            message = (
                f"{icon} **Performance Alert**\n"
                f"Type: {alert['type'].replace('_', ' ').title()}\n"
                f"Severity: {alert['severity'].title()}\n"
                f"Message: {alert['message']}"
            )
            
            await self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def _log_tracking_progress(self, trading_data: Optional[Dict], system_data: Optional[Dict]):
        """Log tracking progress"""
        try:
            if trading_data and system_data:
                logger.info(
                    f"Tracking: Trades={trading_data.get('total_trades', 0)}, "
                    f"Win Rate={trading_data.get('win_rate', 0):.1f}%, "
                    f"Daily Progress={trading_data.get('daily_target_progress', 0):.1f}%, "
                    f"Memory={system_data.get('memory_usage_percent', 0):.1f}%"
                )
        except Exception as e:
            logger.error(f"Error logging progress: {e}")
    
    async def _generate_hourly_analysis(self):
        """Generate hourly performance analysis"""
        try:
            # Get last hour's data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Trading performance for last hour
            cursor.execute('''
                SELECT * FROM trading_performance 
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp
            ''')
            trading_records = cursor.fetchall()
            
            # System performance for last hour
            cursor.execute('''
                SELECT * FROM system_performance 
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp
            ''')
            system_records = cursor.fetchall()
            
            conn.close()
            
            if trading_records and system_records:
                await self._send_hourly_summary(trading_records, system_records)
                
        except Exception as e:
            logger.error(f"Error generating hourly analysis: {e}")
    
    async def _send_hourly_summary(self, trading_records: List, system_records: List):
        """Send hourly performance summary"""
        try:
            # Calculate hourly metrics
            latest_trading = trading_records[-1] if trading_records else None
            latest_system = system_records[-1] if system_records else None
            
            if latest_trading and latest_system:
                message = (
                    f"📊 **Hourly Performance Summary**\n"
                    f"Total Trades: {latest_trading[2]}\n"
                    f"Win Rate: {latest_trading[5]:.1f}%\n"
                    f"Daily Progress: {latest_trading[10]:.1f}%\n"
                    f"Monthly Progress: {latest_trading[11]:.1f}%\n"
                    f"Memory Usage: {latest_system[2]:.1f}%\n"
                    f"Avg Response: {latest_system[4]:.0f}ms"
                )
                
                await self.telegram.send_message(message)
                
        except Exception as e:
            logger.error(f"Error sending hourly summary: {e}")
    
    async def _generate_daily_summary(self):
        """Generate daily performance summary"""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).date()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get yesterday's final metrics
            cursor.execute('''
                SELECT * FROM trading_performance 
                WHERE date(timestamp) = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (yesterday,))
            trading_record = cursor.fetchone()
            
            cursor.execute('''
                SELECT AVG(memory_usage_percent), AVG(response_time_ms), 
                       COUNT(*) as uptime_records
                FROM system_performance 
                WHERE date(timestamp) = ?
            ''', (yesterday,))
            system_stats = cursor.fetchone()
            
            if trading_record:
                # Calculate if daily target was achieved
                daily_pnl = trading_record[4]  # daily_pnl
                target_achieved = daily_pnl >= self.targets['daily_target_percent']
                
                # Store daily summary
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_summaries 
                    (date, total_trades, successful_trades, daily_pnl, win_rate,
                     max_drawdown, avg_response_time, uptime_percent, target_achieved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    yesterday,
                    trading_record[2],  # total_trades
                    trading_record[3],  # successful_trades
                    daily_pnl,
                    trading_record[5],  # win_rate
                    trading_record[7],  # max_drawdown
                    system_stats[1] if system_stats else 0,  # avg_response_time
                    (system_stats[2] / 1440 * 100) if system_stats else 0,  # uptime %
                    target_achieved
                ))
                
                conn.commit()
                
                # Send daily summary
                status_icon = "✅" if target_achieved else "❌"
                message = (
                    f"📈 **Daily Summary - {yesterday}** {status_icon}\n"
                    f"Daily P&L: {daily_pnl:.2f}% (Target: {self.targets['daily_target_percent']}%)\n"
                    f"Total Trades: {trading_record[2]}\n"
                    f"Win Rate: {trading_record[5]:.1f}%\n"
                    f"Max Drawdown: {trading_record[7]:.1f}%\n"
                    f"Target Achieved: {'Yes' if target_achieved else 'No'}"
                )
                
                await self.telegram.send_message(message)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
    
    def get_performance_summary(self) -> Dict:
        """Get current performance summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest metrics
            cursor.execute('SELECT * FROM trading_performance ORDER BY timestamp DESC LIMIT 1')
            latest_trading = cursor.fetchone()
            
            cursor.execute('SELECT * FROM system_performance ORDER BY timestamp DESC LIMIT 1')
            latest_system = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM performance_alerts WHERE resolved = FALSE')
            active_alerts = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'tracking_active': self.tracking,
                'latest_trading_metrics': dict(zip([
                    'id', 'timestamp', 'total_trades', 'successful_trades', 'total_pnl',
                    'daily_pnl', 'win_rate', 'avg_trade_duration', 'max_drawdown',
                    'active_positions', 'daily_target_progress', 'monthly_target_progress'
                ], latest_trading)) if latest_trading else None,
                'latest_system_metrics': dict(zip([
                    'id', 'timestamp', 'memory_usage_percent', 'cpu_usage_percent',
                    'response_time_ms', 'request_count', 'error_rate', 'uptime_hours',
                    'restart_count', 'health_status'
                ], latest_system)) if latest_system else None,
                'active_alerts_count': active_alerts,
                'targets': self.targets
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

async def main():
    """Main entry point for performance tracker"""
    # Get Railway URL from environment or use default
    railway_url = os.getenv('RAILWAY_BOT_URL', 'https://railway-up-production-f151.up.railway.app')
    
    logger.info("🚀 Starting Railway Bot Performance Tracker...")
    logger.info(f"Target: {railway_url}")
    
    try:
        async with PerformanceTracker(railway_url) as tracker:
            await tracker.start_tracking()
            
    except KeyboardInterrupt:
        logger.info("Performance tracker stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in tracker: {e}", exc_info=True)
    finally:
        logger.info("Performance tracker terminated")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTracker stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)