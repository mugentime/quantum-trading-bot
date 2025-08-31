#!/usr/bin/env python3
"""
Quantum Trading Dashboard Startup Script
Production-ready launcher with health checks and monitoring
"""

import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def setup_logging():
    """Setup logging configuration"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "dashboard_startup.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    logger = logging.getLogger(__name__)
    
    try:
        import flask
        import flask_cors
        import flask_socketio
        import ccxt
        import pandas
        import numpy
        logger.info("All Python dependencies available ✓")
    except ImportError as e:
        logger.error(f"Missing Python dependency: {e}")
        logger.error("Run: pip install -r dashboard/requirements.txt")
        return False
    
    return True

def check_environment():
    """Check environment configuration"""
    logger = logging.getLogger(__name__)
    
    required_vars = ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Dashboard will run with mock data")
        return False
    
    logger.info("Environment configuration ✓")
    return True

def start_dashboard():
    """Start the dashboard server"""
    logger = logging.getLogger(__name__)
    
    # Change to project directory
    os.chdir(project_root)
    
    # Set Python path
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # Dashboard server path
    dashboard_script = project_root / "dashboard" / "backend" / "dashboard_server.py"
    
    if not dashboard_script.exists():
        logger.error(f"Dashboard server not found: {dashboard_script}")
        return None
    
    logger.info("Starting Quantum Trading Dashboard...")
    logger.info(f"Server script: {dashboard_script}")
    logger.info(f"Port: {os.getenv('PORT', '5000')}")
    logger.info(f"Mode: {'Production' if not os.getenv('DEBUG') else 'Development'}")
    
    try:
        # Start the dashboard server
        process = subprocess.Popen([
            sys.executable, str(dashboard_script)
        ], env=env)
        
        logger.info(f"Dashboard started with PID: {process.pid}")
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info("Dashboard server started successfully ✓")
            logger.info(f"Access dashboard at: http://localhost:{os.getenv('PORT', '5000')}")
            return process
        else:
            logger.error("Dashboard server failed to start")
            return None
            
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        return None

def health_check():
    """Perform health check on the dashboard"""
    logger = logging.getLogger(__name__)
    
    try:
        import requests
        
        port = os.getenv('PORT', '5000')
        health_url = f"http://localhost:{port}/health"
        
        logger.info("Performing health check...")
        
        # Wait for server to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info("Health check passed ✓")
                    logger.info(f"Status: {health_data.get('status', 'unknown')}")
                    logger.info(f"Version: {health_data.get('version', 'unknown')}")
                    return True
            except requests.RequestException:
                if attempt < max_attempts - 1:
                    logger.info(f"Health check attempt {attempt + 1}/{max_attempts} - waiting...")
                    time.sleep(2)
                else:
                    logger.warning("Health check failed - server may not be ready")
                    return False
                    
    except ImportError:
        logger.warning("Requests library not available - skipping health check")
        return True
        
    return False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum} - shutting down...")
    sys.exit(0)

def main():
    """Main function"""
    logger = setup_logging()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("QUANTUM TRADING DASHBOARD STARTUP")
    logger.info("=" * 50)
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Project Root: {project_root}")
    
    # Pre-flight checks
    logger.info("\nPerforming pre-flight checks...")
    
    if not check_dependencies():
        logger.error("Dependency check failed")
        sys.exit(1)
    
    check_environment()  # Warning only, don't exit
    
    # Start dashboard
    logger.info("\nStarting dashboard server...")
    process = start_dashboard()
    
    if not process:
        logger.error("Failed to start dashboard server")
        sys.exit(1)
    
    # Health check
    if health_check():
        logger.info("\n" + "=" * 50)
        logger.info("DASHBOARD STARTED SUCCESSFULLY!")
        logger.info("=" * 50)
        logger.info(f"🚀 Dashboard URL: http://localhost:{os.getenv('PORT', '5000')}")
        logger.info("📊 Features Available:")
        logger.info("   • Live Trading Panel")
        logger.info("   • Volatility Heat Map")
        logger.info("   • Performance Metrics")
        logger.info("   • Risk Monitor")
        logger.info("   • Signal Analysis")
        logger.info("   • Historical Charts")
        logger.info("   • Alert System")
        logger.info("📱 Mobile-responsive design with dark mode")
        logger.info("🔔 Telegram notifications (if configured)")
        logger.info("\n⚠️  Trading Risk Disclaimer:")
        logger.info("   This software is for educational purposes only.")
        logger.info("   Trading involves substantial risk of loss.")
        logger.info("   Only trade with funds you can afford to lose.")
        logger.info("=" * 50)
    else:
        logger.warning("Health check failed - dashboard may have issues")
    
    try:
        # Keep the main process running
        logger.info("\nDashboard is running. Press Ctrl+C to stop.")
        process.wait()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if process and process.poll() is None:
            logger.info("Terminating dashboard process...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Force killing dashboard process...")
                process.kill()
        
        logger.info("Dashboard shutdown complete")

if __name__ == "__main__":
    main()