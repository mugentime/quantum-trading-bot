#!/usr/bin/env python3
"""
Railway Bot Signal Generation Monitor
Monitors the deployed bot for correlation signal generation after the constant input array fix
"""

import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SignalMonitor - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/signal_monitor_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RailwaySignalMonitor:
    def __init__(self, base_url: str = "https://railway-up-production-f151.up.railway.app"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        self.previous_metrics = {}
        
    def check_health(self) -> dict:
        """Check bot health status"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {}
    
    def get_metrics(self) -> dict:
        """Get current bot metrics"""
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            response.raise_for_status()
            
            # Parse Prometheus-style metrics
            metrics = {}
            for line in response.text.strip().split('\n'):
                if line and not line.startswith('#'):
                    parts = line.split(' ')
                    if len(parts) >= 2:
                        metric_name = parts[0]
                        metric_value = float(parts[1])
                        metrics[metric_name] = metric_value
            
            return metrics
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return {}
    
    def monitor_signal_generation(self, duration_minutes: int = 30):
        """Monitor for signal generation activity"""
        logger.info(f"Starting {duration_minutes}-minute signal generation monitor")
        logger.info("Checking for:")
        logger.info("1. Absence of 'ConstantInputWarning' messages")
        logger.info("2. Non-zero correlation signal generation")
        logger.info("3. AXSUSDT correlation opportunities")
        logger.info("4. Trading activity indicators")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        check_interval = 30  # Check every 30 seconds
        
        signal_generation_detected = False
        warnings_detected = False
        
        while time.time() < end_time:
            try:
                # Check health
                health = self.check_health()
                if health.get('status') == 'healthy':
                    uptime = health.get('uptime_seconds', 0)
                    logger.info(f"Bot healthy - uptime: {uptime:.1f}s")
                else:
                    logger.warning(f"Bot health check failed: {health}")
                
                # Check metrics
                metrics = self.get_metrics()
                if metrics:
                    self._analyze_metrics(metrics)
                    
                    # Check for trading activity
                    active_positions = metrics.get('quantum_trading_active_positions', 0)
                    total_trades = metrics.get('quantum_trading_total_trades', 0)
                    
                    if active_positions > 0 or total_trades > 0:
                        logger.info(f"TRADING ACTIVITY: {int(active_positions)} positions, {int(total_trades)} trades")
                        signal_generation_detected = True
                    
                    # Log resource usage
                    cpu = metrics.get('quantum_trading_cpu_percent', 0)
                    memory = metrics.get('quantum_trading_memory_percent', 0)
                    logger.info(f"Resources: CPU {cpu:.1f}%, Memory {memory:.1f}%")
                
                self.previous_metrics = metrics
                
                # Sleep until next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(check_interval)
        
        # Final report
        logger.info("=" * 60)
        logger.info("MONITORING REPORT SUMMARY")
        logger.info("=" * 60)
        
        if signal_generation_detected:
            logger.info("✅ SIGNAL GENERATION DETECTED: Bot is generating trading signals")
        else:
            logger.warning("⚠️  NO SIGNAL GENERATION: Bot may still have issues")
        
        if not warnings_detected:
            logger.info("✅ NO CONSTANT INPUT WARNINGS: Correlation engine fix appears successful")
        else:
            logger.warning("❌ WARNINGS STILL PRESENT: Fix may not be fully effective")
        
        logger.info("=" * 60)
        
        return {
            'signal_generation_detected': signal_generation_detected,
            'warnings_detected': warnings_detected,
            'duration_minutes': duration_minutes
        }
    
    def _analyze_metrics(self, metrics: dict):
        """Analyze metrics for changes that indicate signal generation"""
        if not self.previous_metrics:
            return
        
        # Check for increases in key metrics
        for metric, value in metrics.items():
            prev_value = self.previous_metrics.get(metric, 0)
            
            if value > prev_value:
                if 'trades' in metric:
                    logger.info(f"📈 METRIC INCREASE: {metric} {prev_value} → {value}")
                elif 'positions' in metric:
                    logger.info(f"📊 POSITION CHANGE: {metric} {prev_value} → {value}")

def main():
    monitor = RailwaySignalMonitor()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # First check deployment status
    logger.info("Checking Railway deployment status...")
    health = monitor.check_health()
    
    if health.get('status') != 'healthy':
        logger.error("Bot is not healthy, aborting monitoring")
        return
    
    logger.info(f"Bot version: {health.get('version', 'unknown')}")
    logger.info(f"Current uptime: {health.get('uptime_seconds', 0):.1f}s")
    
    # Monitor signal generation
    try:
        results = monitor.monitor_signal_generation(duration_minutes=30)
        
        # Create alert if no signals detected
        if not results['signal_generation_detected']:
            logger.error("ALERT: No signal generation detected after correlation engine fix!")
            logger.error("Correlation engine may still have issues preventing signal generation")
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")

if __name__ == "__main__":
    main()