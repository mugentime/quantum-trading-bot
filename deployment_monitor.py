#!/usr/bin/env python3
"""
Real-time Railway Deployment Monitor for Quantum Trading Bot
Usage: python deployment_monitor.py https://your-app.railway.app
"""

import requests
import time
import json
import sys
from datetime import datetime
from typing import Dict, Any
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RailwayDeploymentMonitor:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.start_time = datetime.now()
        self.health_history = []
        self.error_count = 0
        self.success_count = 0
        
    def check_health(self) -> Dict[str, Any]:
        """Check all health endpoints"""
        endpoints = {
            'health': '/health',
            'ready': '/health/ready', 
            'live': '/health/live',
            'detailed': '/health/detailed'
        }
        
        results = {}
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    timeout=10
                )
                results[name] = {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'data': response.json() if response.content else None,
                    'success': response.status_code == 200
                }
                if response.status_code == 200:
                    self.success_count += 1
                else:
                    self.error_count += 1
                    
            except Exception as e:
                results[name] = {
                    'status_code': 0,
                    'response_time': 0,
                    'data': None,
                    'error': str(e),
                    'success': False
                }
                self.error_count += 1
                
        return results
    
    def check_metrics(self) -> Dict[str, Any]:
        """Check Prometheus metrics endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/metrics",
                timeout=10
            )
            if response.status_code == 200:
                return {
                    'success': True,
                    'metrics': response.text,
                    'response_time': response.elapsed.total_seconds()
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Unknown error'}
    
    def display_status(self, health_results: Dict[str, Any]):
        """Display current status"""
        print("\n" + "="*80)
        print(f"🚀 RAILWAY DEPLOYMENT MONITOR - {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
        
        # Overall status
        all_healthy = all(result.get('success', False) for result in health_results.values())
        status_icon = "✅" if all_healthy else "❌"
        print(f"Overall Status: {status_icon} {'HEALTHY' if all_healthy else 'ISSUES DETECTED'}")
        print(f"Uptime: {datetime.now() - self.start_time}")
        print(f"Success Rate: {self.success_count}/{self.success_count + self.error_count}")
        
        print("\n📊 HEALTH ENDPOINTS:")
        for endpoint, result in health_results.items():
            icon = "✅" if result.get('success') else "❌"
            status = result.get('status_code', 'N/A')
            time_ms = int(result.get('response_time', 0) * 1000)
            print(f"  {icon} {endpoint:10} | Status: {status:3} | Time: {time_ms:4}ms")
            
            if result.get('data'):
                data = result['data']
                if endpoint == 'health' and isinstance(data, dict):
                    print(f"      Status: {data.get('status', 'unknown')}")
                    if 'checks' in data:
                        for check, status in data['checks'].items():
                            check_icon = "✅" if status else "❌"
                            print(f"      {check_icon} {check}")
                            
            if result.get('error'):
                print(f"      Error: {result['error']}")
        
        print("\n" + "="*80)
    
    def check_trading_bot_status(self, health_data: Dict) -> Dict[str, Any]:
        """Extract trading bot specific status"""
        if not health_data or 'detailed' not in health_data:
            return {}
            
        detailed = health_data['detailed'].get('data', {})
        if not detailed:
            return {}
            
        return {
            'trading_active': detailed.get('trading_active', False),
            'api_connection': detailed.get('api_connection', 'unknown'),
            'components': detailed.get('components', {}),
            'uptime': detailed.get('uptime_seconds', 0),
            'environment': detailed.get('environment', 'unknown')
        }
    
    async def continuous_monitor(self, interval: int = 30):
        """Continuously monitor the deployment"""
        print(f"🔍 Starting continuous monitoring of {self.base_url}")
        print(f"⏱️  Check interval: {interval} seconds")
        
        while True:
            try:
                # Check health endpoints
                health_results = self.check_health()
                self.health_history.append(health_results)
                
                # Keep only last 20 checks
                if len(self.health_history) > 20:
                    self.health_history.pop(0)
                
                # Display status
                self.display_status(health_results)
                
                # Check for critical issues
                critical_issues = []
                for endpoint, result in health_results.items():
                    if not result.get('success') and endpoint in ['health', 'live']:
                        critical_issues.append(f"{endpoint} endpoint failed")
                
                if critical_issues:
                    print(f"\n🚨 CRITICAL ALERTS:")
                    for issue in critical_issues:
                        print(f"  ⚠️  {issue}")
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)

def main():
    if len(sys.argv) != 2:
        print("Usage: python deployment_monitor.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    print(f"🎯 Railway Deployment Monitor")
    print(f"Target: {base_url}")
    print(f"Started: {datetime.now()}")
    
    monitor = RailwayDeploymentMonitor(base_url)
    
    try:
        # Initial check
        print("\n🔍 Initial health check...")
        initial_results = monitor.check_health()
        monitor.display_status(initial_results)
        
        # Start continuous monitoring
        asyncio.run(monitor.continuous_monitor())
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()