#!/usr/bin/env python3
"""
Railway Deployment Script for Scalping Bot
Optimized for Railway cloud deployment with proper environment handling
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger_config import setup_logger
from launch_scalping_bot import check_environment, validate_scalping_config

logger = setup_logger("RailwayDeploy", level=logging.INFO)

def setup_railway_environment():
    """Setup Railway-specific environment configuration"""
    logger.info("🚂 Setting up Railway environment...")
    
    # Railway provides PORT environment variable
    port = os.getenv('PORT', '8080')
    os.environ['FLASK_PORT'] = port
    
    # Set Railway-specific logging
    os.environ['PYTHONUNBUFFERED'] = '1'  # Ensure logs appear in Railway
    
    # Enable uvloop for better async performance on Railway
    try:
        import uvloop
        uvloop.install()
        logger.info("✅ uvloop installed for better performance")
    except ImportError:
        logger.info("ℹ️ uvloop not available, using default event loop")
    
    # Set Railway-specific configurations
    railway_configs = {
        'ENVIRONMENT': 'production',
        'DEBUG': 'false',
        'LOG_LEVEL': 'INFO',
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379'),
    }
    
    for key, value in railway_configs.items():
        if not os.getenv(key):
            os.environ[key] = value
    
    logger.info("✅ Railway environment configured")

def validate_railway_deployment():
    """Validate Railway deployment requirements"""
    logger.info("🔍 Validating Railway deployment...")
    
    required_railway_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY',
        'RAILWAY_DEPLOYMENT_ID'  # Set by Railway automatically
    ]
    
    missing_vars = []
    for var in required_railway_vars[:-1]:  # Skip RAILWAY_DEPLOYMENT_ID check for local testing
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required Railway variables: {missing_vars}")
        logger.error("Please set these in your Railway project environment variables")
        return False
    
    # Check Railway-specific settings
    deployment_id = os.getenv('RAILWAY_DEPLOYMENT_ID')
    if deployment_id:
        logger.info(f"✅ Railway deployment detected: {deployment_id[:8]}...")
    else:
        logger.warning("⚠️ RAILWAY_DEPLOYMENT_ID not found - might be local testing")
    
    # Validate memory limits for Railway
    railway_memory_limit = os.getenv('RAILWAY_MEMORY_LIMIT')
    if railway_memory_limit:
        memory_mb = int(railway_memory_limit)
        if memory_mb < 512:
            logger.warning(f"⚠️ Low memory allocation: {memory_mb}MB - consider upgrading")
        else:
            logger.info(f"✅ Memory allocation: {memory_mb}MB")
    
    logger.info("✅ Railway validation completed")
    return True

async def start_railway_scalping_bot():
    """Start the scalping bot optimized for Railway"""
    try:
        logger.info("🚀 Starting Scalping Bot on Railway...")
        
        # Import the scalping bot
        from scalping_main import ScalpingTradingBot
        
        # Create bot instance
        bot = ScalpingTradingBot()
        
        # Start the bot
        await bot.start()
        
    except Exception as e:
        logger.error(f"💥 Error starting Railway scalping bot: {e}", exc_info=True)
        # Don't re-raise to prevent Railway restart loops
        await asyncio.sleep(60)  # Wait before exit to prevent rapid restarts

def setup_railway_health_check():
    """Setup health check endpoint for Railway"""
    try:
        from flask import Flask, jsonify
        from datetime import datetime
        import threading
        import time
        
        app = Flask(__name__)
        
        # Global health status
        health_status = {
            'status': 'starting',
            'start_time': datetime.utcnow().isoformat(),
            'last_heartbeat': datetime.utcnow().isoformat(),
            'bot_running': False
        }
        
        @app.route('/health')
        def health_check():
            """Health check endpoint for Railway"""
            health_status['last_heartbeat'] = datetime.utcnow().isoformat()
            
            return jsonify({
                'status': health_status['status'],
                'start_time': health_status['start_time'],
                'last_heartbeat': health_status['last_heartbeat'],
                'bot_running': health_status['bot_running'],
                'uptime_seconds': (datetime.utcnow() - datetime.fromisoformat(health_status['start_time'])).total_seconds()
            })
        
        @app.route('/')
        def root():
            """Root endpoint"""
            return jsonify({
                'service': 'Quantum Trading Bot - Scalping Mode',
                'status': 'running',
                'timestamp': datetime.utcnow().isoformat(),
                'deployment': 'railway'
            })
        
        def run_flask():
            """Run Flask health check server"""
            port = int(os.getenv('PORT', 8080))
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        
        # Start Flask server in background thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        logger.info(f"✅ Health check server started on port {os.getenv('PORT', 8080)}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Failed to setup health check: {e}")
        return None

async def main():
    """Main Railway deployment function"""
    logger.info("🚂 Railway Scalping Bot Deployment Starting...")
    
    try:
        # Step 1: Setup Railway environment
        setup_railway_environment()
        
        # Step 2: Validate deployment
        if not validate_railway_deployment():
            logger.error("❌ Railway deployment validation failed")
            sys.exit(1)
        
        # Step 3: Validate environment and configuration
        if not check_environment():
            logger.error("❌ Environment check failed")
            sys.exit(1)
        
        if not validate_scalping_config():
            logger.error("❌ Configuration validation failed")
            sys.exit(1)
        
        # Step 4: Setup health check for Railway
        health_status = setup_railway_health_check()
        if health_status:
            health_status['status'] = 'healthy'
            health_status['bot_running'] = True
        
        # Step 5: Start the scalping bot
        logger.info("✅ All checks passed - starting scalping bot...")
        await start_railway_scalping_bot()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"💥 Railway deployment failed: {e}", exc_info=True)
        
        # For Railway, we want to exit with error code but not crash immediately
        await asyncio.sleep(30)  # Give time for logs to be collected
        sys.exit(1)
    
    finally:
        logger.info("🏁 Railway deployment ended")

if __name__ == "__main__":
    # For Railway deployment, we need to handle the event loop properly
    try:
        # Check if we're in Railway environment
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'):
            logger.info("🚂 Detected Railway environment")
            
            # Set Railway-specific asyncio policy for better performance
            if sys.platform != 'win32':
                try:
                    import uvloop
                    uvloop.install()
                except ImportError:
                    pass
            
            # Run the main deployment
            asyncio.run(main())
        else:
            # Local development mode
            logger.info("🏠 Running in local development mode")
            logger.info("Use 'python launch_scalping_bot.py' for local deployment")
            logger.info("This script is optimized for Railway cloud deployment")
            
    except KeyboardInterrupt:
        print("\n🛑 Deployment cancelled")
    except Exception as e:
        print(f"💥 Fatal deployment error: {e}")
        sys.exit(1)