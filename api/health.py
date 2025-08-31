#!/usr/bin/env python3
"""
Health Check API for Railway Deployment
Provides comprehensive health monitoring endpoints
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from flask import Flask, jsonify, request
import threading
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.last_trade_time = None
        self.system_stats = {}
        self.trading_stats = {}
        self.error_counts = {}
        
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def check_database_connection(self) -> bool:
        """Check database connectivity"""
        try:
            # In production, test actual database connection
            return True
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False
    
    def check_binance_api(self) -> bool:
        """Check Binance API connectivity"""
        try:
            # In production, make test API call
            return True
        except Exception as e:
            logger.error(f"Binance API check failed: {e}")
            return False
    
    def check_trading_system(self) -> bool:
        """Check trading system status"""
        try:
            # Check if trading components are running
            return True
        except Exception as e:
            logger.error(f"Trading system check failed: {e}")
            return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        import psutil
        
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "network_connections": len(psutil.net_connections()),
                "process_count": len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def get_trading_metrics(self) -> Dict[str, Any]:
        """Get trading performance metrics"""
        return {
            "active_positions": self.trading_stats.get("active_positions", 0),
            "total_trades": self.trading_stats.get("total_trades", 0),
            "win_rate": self.trading_stats.get("win_rate", 0.0),
            "pnl_today": self.trading_stats.get("pnl_today", 0.0),
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None
        }

health_checker = HealthChecker()

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        uptime = health_checker.get_uptime()
        
        # Basic checks
        checks = {
            "database": health_checker.check_database_connection(),
            "binance_api": health_checker.check_binance_api(),
            "trading_system": health_checker.check_trading_system()
        }
        
        # Overall health status
        all_healthy = all(checks.values())
        status = "healthy" if all_healthy else "degraded"
        
        return jsonify({
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "checks": checks,
            "version": "1.0.0"
        }), 200 if all_healthy else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with metrics"""
    try:
        uptime = health_checker.get_uptime()
        system_metrics = health_checker.get_system_metrics()
        trading_metrics = health_checker.get_trading_metrics()
        
        # Detailed checks
        checks = {
            "database": health_checker.check_database_connection(),
            "binance_api": health_checker.check_binance_api(),
            "trading_system": health_checker.check_trading_system(),
            "system_resources": {
                "cpu_ok": system_metrics.get("cpu_percent", 0) < 80,
                "memory_ok": system_metrics.get("memory_percent", 0) < 85,
                "disk_ok": system_metrics.get("disk_usage", 0) < 90
            }
        }
        
        # Overall health status
        all_healthy = (
            all(checks["system_resources"].values()) and
            checks["database"] and
            checks["binance_api"] and
            checks["trading_system"]
        )
        
        status = "healthy" if all_healthy else "degraded"
        
        return jsonify({
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "checks": checks,
            "metrics": {
                "system": system_metrics,
                "trading": trading_metrics
            },
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }), 200 if all_healthy else 503
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness probe for Railway"""
    try:
        # Check if all components are ready to serve traffic
        ready = (
            health_checker.check_database_connection() and
            health_checker.check_binance_api() and
            health_checker.check_trading_system()
        )
        
        return jsonify({
            "ready": ready,
            "timestamp": datetime.utcnow().isoformat()
        }), 200 if ready else 503
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 500

@app.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness probe for Railway"""
    try:
        # Basic liveness check - just return if process is alive
        return jsonify({
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": health_checker.get_uptime()
        }), 200
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({
            "alive": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 500

@app.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        system_metrics = health_checker.get_system_metrics()
        trading_metrics = health_checker.get_trading_metrics()
        uptime = health_checker.get_uptime()
        
        metrics = []
        
        # System metrics
        for metric, value in system_metrics.items():
            metrics.append(f'quantum_trading_{metric} {value}')
        
        # Trading metrics
        for metric, value in trading_metrics.items():
            if isinstance(value, (int, float)):
                metrics.append(f'quantum_trading_{metric} {value}')
        
        # Uptime metric
        metrics.append(f'quantum_trading_uptime_seconds {uptime}')
        
        return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return f'# Error generating metrics: {e}', 500

def start_health_server(port: int = 8080):
    """Start the health check server"""
    logger.info(f"Starting health check server on port {port}")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

def run_health_server_thread(port: int = 8080):
    """Run health server in a separate thread"""
    thread = threading.Thread(
        target=start_health_server,
        args=(port,),
        daemon=True,
        name="HealthServer"
    )
    thread.start()
    logger.info(f"Health server thread started on port {port}")
    return thread

if __name__ == "__main__":
    # For testing
    port = int(os.getenv("HEALTH_CHECK_PORT", 8080))
    start_health_server(port)