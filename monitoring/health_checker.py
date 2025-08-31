#!/usr/bin/env python3
"""
Railway Health Checker
Comprehensive health monitoring system for Railway trading bot endpoints
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import os
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger_config import setup_logger
from utils.telegram_notifier import TelegramNotifier

# Set up logging
logger = setup_logger("HealthChecker", level=logging.INFO)

class HealthChecker:
    """Comprehensive health monitoring for Railway bot endpoints"""
    
    def __init__(self, railway_url: str = "https://railway-up-production-f151.up.railway.app"):
        """Initialize the health checker"""
        self.railway_url = railway_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.telegram = TelegramNotifier()
        
        # Health check configuration
        self.endpoints = {
            'root': {'path': '/', 'critical': True, 'timeout': 5},
            'health': {'path': '/health', 'critical': True, 'timeout': 5},
            'health_detailed': {'path': '/health/detailed', 'critical': True, 'timeout': 10},
            'ready': {'path': '/ready', 'critical': True, 'timeout': 5},
            'live': {'path': '/live', 'critical': True, 'timeout': 5},
            'metrics': {'path': '/metrics', 'critical': False, 'timeout': 15}
        }
        
        # Monitoring state
        self.monitoring = False
        self.check_interval = 30  # Check every 30 seconds
        self.alert_cooldown = 300  # 5 minutes between same alerts
        
        # Health history
        self.health_history = {}
        self.downtime_periods = []
        self.last_alerts = {}
        
        # Health thresholds
        self.thresholds = {
            'max_response_time': 10000,  # 10 seconds
            'max_consecutive_failures': 3,
            'min_uptime_percent': 99.0,  # 99% uptime requirement
            'critical_failure_threshold': 2,  # Critical endpoints failing
        }
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'uptime_start': datetime.now(),
            'total_downtime_seconds': 0,
            'longest_outage_seconds': 0,
            'avg_response_time': 0
        }
        
        logger.info(f"Health Checker initialized for: {self.railway_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=20, limit_per_host=5)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def start_health_monitoring(self):
        """Start comprehensive health monitoring"""
        logger.info("🏥 Starting Railway bot health monitoring...")
        self.monitoring = True
        
        # Initialize health history
        for endpoint in self.endpoints:
            self.health_history[endpoint] = {
                'consecutive_failures': 0,
                'total_checks': 0,
                'successful_checks': 0,
                'response_times': [],
                'last_success': None,
                'last_failure': None
            }
        
        # Send startup notification
        await self.telegram.send_message(
            "🏥 **Health Monitor Started**\n"
            f"Target: {self.railway_url}\n"
            f"Endpoints: {len(self.endpoints)}\n"
            f"Check interval: {self.check_interval}s\n"
            f"Uptime requirement: {self.thresholds['min_uptime_percent']}%"
        )
        
        try:
            # Create monitoring tasks
            tasks = [
                asyncio.create_task(self._health_check_loop(), name="health_checker"),
                asyncio.create_task(self._uptime_calculator(), name="uptime_calculator"),
                asyncio.create_task(self._periodic_reporter(), name="periodic_reporter")
            ]
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            logger.info("Health monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in health monitoring: {e}", exc_info=True)
        finally:
            self.monitoring = False
            await self.telegram.send_message("🛑 **Health Monitor Stopped**")
    
    async def _health_check_loop(self):
        """Main health checking loop"""
        logger.info("Starting health check loop...")
        
        while self.monitoring:
            try:
                check_start_time = time.time()
                
                # Perform health checks on all endpoints
                results = await self._check_all_endpoints()
                
                # Update statistics
                self.stats['total_checks'] += 1
                check_duration = time.time() - check_start_time
                
                # Analyze results
                overall_health = await self._analyze_health_results(results)
                
                # Update health history
                await self._update_health_history(results, overall_health)
                
                # Check for alerts
                await self._check_health_alerts(results, overall_health)
                
                # Log status periodically
                if self.stats['total_checks'] % 10 == 0:
                    await self._log_health_status(overall_health)
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                self.stats['failed_checks'] += 1
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_all_endpoints(self) -> Dict:
        """Check all configured endpoints"""
        results = {}
        
        # Create tasks for parallel checking
        tasks = []
        for endpoint_name, config in self.endpoints.items():
            task = asyncio.create_task(
                self._check_single_endpoint(endpoint_name, config),
                name=f"check_{endpoint_name}"
            )
            tasks.append((endpoint_name, task))
        
        # Wait for all checks to complete
        for endpoint_name, task in tasks:
            try:
                result = await task
                results[endpoint_name] = result
            except Exception as e:
                results[endpoint_name] = {
                    'success': False,
                    'status_code': None,
                    'response_time': None,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return results
    
    async def _check_single_endpoint(self, endpoint_name: str, config: Dict) -> Dict:
        """Check a single endpoint"""
        url = f"{self.railway_url}{config['path']}"
        start_time = time.time()
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=config['timeout'])) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Get response data if possible
                response_data = None
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        response_data = await response.json()
                    else:
                        response_text = await response.text()
                        response_data = {'content': response_text[:200]}  # First 200 chars
                except:
                    pass
                
                return {
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'response_data': response_data,
                    'headers': dict(response.headers),
                    'error': None if response.status == 200 else f"HTTP {response.status}",
                    'timestamp': datetime.now().isoformat()
                }
                
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return {
                'success': False,
                'status_code': None,
                'response_time': response_time,
                'response_data': None,
                'headers': {},
                'error': f"Timeout after {config['timeout']}s",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'success': False,
                'status_code': None,
                'response_time': response_time,
                'response_data': None,
                'headers': {},
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _analyze_health_results(self, results: Dict) -> Dict:
        """Analyze health check results"""
        total_endpoints = len(results)
        successful_endpoints = sum(1 for r in results.values() if r['success'])
        critical_endpoints = len([name for name in results if self.endpoints[name]['critical']])
        successful_critical = sum(1 for name, result in results.items() 
                                if self.endpoints[name]['critical'] and result['success'])
        
        # Calculate overall health
        overall_healthy = successful_critical == critical_endpoints
        health_percentage = (successful_endpoints / total_endpoints) * 100 if total_endpoints > 0 else 0
        
        # Calculate average response time
        response_times = [r['response_time'] for r in results.values() if r['response_time'] is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Identify failing endpoints
        failing_endpoints = [name for name, result in results.items() if not result['success']]
        critical_failures = [name for name in failing_endpoints if self.endpoints[name]['critical']]
        
        return {
            'overall_healthy': overall_healthy,
            'health_percentage': health_percentage,
            'total_endpoints': total_endpoints,
            'successful_endpoints': successful_endpoints,
            'critical_endpoints': critical_endpoints,
            'successful_critical': successful_critical,
            'avg_response_time': avg_response_time,
            'failing_endpoints': failing_endpoints,
            'critical_failures': critical_failures,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _update_health_history(self, results: Dict, overall_health: Dict):
        """Update health history and statistics"""
        # Update per-endpoint history
        for endpoint_name, result in results.items():
            history = self.health_history[endpoint_name]
            history['total_checks'] += 1
            
            if result['success']:
                history['successful_checks'] += 1
                history['consecutive_failures'] = 0
                history['last_success'] = datetime.now()
                
                # Update response time history (keep last 100)
                if result['response_time'] is not None:
                    history['response_times'].append(result['response_time'])
                    if len(history['response_times']) > 100:
                        history['response_times'] = history['response_times'][-100:]
            else:
                history['consecutive_failures'] += 1
                history['last_failure'] = datetime.now()
        
        # Update overall statistics
        if overall_health['overall_healthy']:
            self.stats['successful_checks'] += 1
        else:
            self.stats['failed_checks'] += 1
        
        # Update average response time
        if overall_health['avg_response_time'] > 0:
            total_avg = self.stats['avg_response_time'] * (self.stats['total_checks'] - 1)
            self.stats['avg_response_time'] = (total_avg + overall_health['avg_response_time']) / self.stats['total_checks']
    
    async def _check_health_alerts(self, results: Dict, overall_health: Dict):
        """Check for health alerts and send notifications"""
        alerts = []
        current_time = datetime.now()
        
        # Check overall health
        if not overall_health['overall_healthy']:
            alert_key = 'overall_health'
            if self._should_send_alert(alert_key):
                alerts.append({
                    'type': 'overall_health',
                    'severity': 'critical',
                    'message': f"System unhealthy: {len(overall_health['critical_failures'])} critical endpoints failing",
                    'details': overall_health['critical_failures']
                })
                self.last_alerts[alert_key] = current_time
        
        # Check individual endpoints
        for endpoint_name, result in results.items():
            history = self.health_history[endpoint_name]
            config = self.endpoints[endpoint_name]
            
            # Check consecutive failures
            if history['consecutive_failures'] >= self.thresholds['max_consecutive_failures']:
                alert_key = f'consecutive_failures_{endpoint_name}'
                if self._should_send_alert(alert_key):
                    severity = 'critical' if config['critical'] else 'warning'
                    alerts.append({
                        'type': 'consecutive_failures',
                        'severity': severity,
                        'message': f"Endpoint {endpoint_name} has {history['consecutive_failures']} consecutive failures",
                        'details': {'endpoint': endpoint_name, 'error': result.get('error')}
                    })
                    self.last_alerts[alert_key] = current_time
            
            # Check response time
            if result['success'] and result['response_time'] and result['response_time'] > self.thresholds['max_response_time']:
                alert_key = f'slow_response_{endpoint_name}'
                if self._should_send_alert(alert_key):
                    alerts.append({
                        'type': 'slow_response',
                        'severity': 'warning',
                        'message': f"Endpoint {endpoint_name} slow response: {result['response_time']:.0f}ms",
                        'details': {'endpoint': endpoint_name, 'response_time': result['response_time']}
                    })
                    self.last_alerts[alert_key] = current_time
        
        # Send alerts
        for alert in alerts:
            await self._send_health_alert(alert)
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if enough time has passed to send the same alert again"""
        last_alert_time = self.last_alerts.get(alert_key)
        if last_alert_time is None:
            return True
        
        time_since_last = (datetime.now() - last_alert_time).total_seconds()
        return time_since_last >= self.alert_cooldown
    
    async def _send_health_alert(self, alert: Dict):
        """Send health alert notification"""
        try:
            severity_icons = {
                'critical': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️'
            }
            
            icon = severity_icons.get(alert['severity'], 'ℹ️')
            message = (
                f"{icon} **Health Alert**\n"
                f"Type: {alert['type'].replace('_', ' ').title()}\n"
                f"Severity: {alert['severity'].title()}\n"
                f"Message: {alert['message']}"
            )
            
            if alert.get('details'):
                if isinstance(alert['details'], list):
                    message += f"\nAffected: {', '.join(alert['details'])}"
                elif isinstance(alert['details'], dict):
                    for key, value in alert['details'].items():
                        message += f"\n{key.title()}: {value}"
            
            await self.telegram.send_message(message)
            logger.warning(f"Health alert sent: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error sending health alert: {e}")
    
    async def _log_health_status(self, overall_health: Dict):
        """Log current health status"""
        status = "✅ HEALTHY" if overall_health['overall_healthy'] else "❌ UNHEALTHY"
        uptime_pct = (self.stats['successful_checks'] / self.stats['total_checks'] * 100) if self.stats['total_checks'] > 0 else 0
        
        logger.info(
            f"Health Status: {status} | "
            f"Uptime: {uptime_pct:.2f}% | "
            f"Avg Response: {self.stats['avg_response_time']:.0f}ms | "
            f"Checks: {self.stats['total_checks']}"
        )
    
    async def _uptime_calculator(self):
        """Calculate and track uptime statistics"""
        while self.monitoring:
            try:
                # Calculate current uptime
                total_runtime = (datetime.now() - self.stats['uptime_start']).total_seconds()
                successful_runtime = total_runtime - self.stats['total_downtime_seconds']
                uptime_percentage = (successful_runtime / total_runtime * 100) if total_runtime > 0 else 0
                
                # Check uptime threshold
                if uptime_percentage < self.thresholds['min_uptime_percent']:
                    alert_key = 'low_uptime'
                    if self._should_send_alert(alert_key):
                        await self._send_health_alert({
                            'type': 'low_uptime',
                            'severity': 'warning',
                            'message': f"Uptime below threshold: {uptime_percentage:.2f}% < {self.thresholds['min_uptime_percent']}%",
                            'details': {'uptime_percentage': uptime_percentage}
                        })
                        self.last_alerts[alert_key] = datetime.now()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in uptime calculator: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_reporter(self):
        """Send periodic health reports"""
        while self.monitoring:
            try:
                # Wait for next report time (every 4 hours)
                await asyncio.sleep(14400)  # 4 hours
                
                # Generate and send report
                await self._send_periodic_report()
                
            except Exception as e:
                logger.error(f"Error in periodic reporter: {e}")
    
    async def _send_periodic_report(self):
        """Send periodic health report"""
        try:
            runtime = datetime.now() - self.stats['uptime_start']
            uptime_pct = (self.stats['successful_checks'] / self.stats['total_checks'] * 100) if self.stats['total_checks'] > 0 else 0
            
            # Calculate endpoint statistics
            endpoint_stats = []
            for endpoint_name, history in self.health_history.items():
                if history['total_checks'] > 0:
                    success_pct = (history['successful_checks'] / history['total_checks'] * 100)
                    avg_response = sum(history['response_times']) / len(history['response_times']) if history['response_times'] else 0
                    endpoint_stats.append(f"• {endpoint_name}: {success_pct:.1f}% ({avg_response:.0f}ms avg)")
            
            message = (
                f"📊 **Health Report - {runtime.days}d {runtime.seconds//3600}h**\n"
                f"Overall Uptime: {uptime_pct:.2f}%\n"
                f"Total Checks: {self.stats['total_checks']}\n"
                f"Avg Response: {self.stats['avg_response_time']:.0f}ms\n"
                f"Endpoint Status:\n" + "\n".join(endpoint_stats[:5])  # Top 5 endpoints
            )
            
            if len(endpoint_stats) > 5:
                message += f"\n...and {len(endpoint_stats) - 5} more endpoints"
            
            await self.telegram.send_message(message)
            logger.info("Periodic health report sent")
            
        except Exception as e:
            logger.error(f"Error sending periodic report: {e}")
    
    def get_health_summary(self) -> Dict:
        """Get current health monitoring summary"""
        runtime = datetime.now() - self.stats['uptime_start']
        uptime_pct = (self.stats['successful_checks'] / self.stats['total_checks'] * 100) if self.stats['total_checks'] > 0 else 0
        
        endpoint_summaries = {}
        for endpoint_name, history in self.health_history.items():
            if history['total_checks'] > 0:
                endpoint_summaries[endpoint_name] = {
                    'success_rate': (history['successful_checks'] / history['total_checks'] * 100),
                    'consecutive_failures': history['consecutive_failures'],
                    'avg_response_time': sum(history['response_times']) / len(history['response_times']) if history['response_times'] else 0,
                    'last_success': history['last_success'].isoformat() if history['last_success'] else None,
                    'last_failure': history['last_failure'].isoformat() if history['last_failure'] else None
                }
        
        return {
            'monitoring_active': self.monitoring,
            'runtime_hours': runtime.total_seconds() / 3600,
            'overall_uptime_percent': uptime_pct,
            'total_checks': self.stats['total_checks'],
            'successful_checks': self.stats['successful_checks'],
            'failed_checks': self.stats['failed_checks'],
            'avg_response_time_ms': self.stats['avg_response_time'],
            'endpoint_summaries': endpoint_summaries,
            'active_alerts': len(self.last_alerts),
            'thresholds': self.thresholds
        }

async def main():
    """Main entry point for health checker"""
    # Get Railway URL from environment or use default
    railway_url = os.getenv('RAILWAY_BOT_URL', 'https://railway-up-production-f151.up.railway.app')
    
    logger.info("🚀 Starting Railway Bot Health Checker...")
    logger.info(f"Target: {railway_url}")
    
    try:
        async with HealthChecker(railway_url) as checker:
            await checker.start_health_monitoring()
            
    except KeyboardInterrupt:
        logger.info("Health checker stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in health checker: {e}", exc_info=True)
    finally:
        logger.info("Health checker terminated")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nHealth checker stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)