#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Quantum Trading Bot
"""

import asyncio
import signal
import sys
from datetime import datetime
import logging
import os

# Add current directory to Python path to fix import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize production logging first
try:
    from utils.production_logger import setup_production_logging, get_trading_logger
    setup_production_logging()
    startup_logger = get_trading_logger('main')
    startup_logger.info("Starting Quantum Trading Bot", 
                       environment=os.getenv('ENVIRONMENT', 'development'),
                       version="1.0.0")
except ImportError:
    # Fallback to basic logging if production logger not available
    logging.basicConfig(level=logging.INFO)
    startup_logger = logging.getLogger('main')
    startup_logger.info("Starting Quantum Trading Bot (fallback logging)")

startup_logger.info("Loading configuration...")

try:
    from core.config.settings import config
    from core.data_collector import DataCollector
    from core.correlation_engine import CorrelationEngine
    from core.signal_generator import SignalGenerator
    from core.ultra_high_frequency_trader import ultra_high_frequency_trader
    from core.executor import Executor
    from core.risk_manager import RiskManager
    from analytics.performance import PerformanceTracker
    from analytics.failure_analyzer import FailureAnalyzer
    from core.environment_manager import environment_manager, Environment
    from core.data_authenticity_validator import authenticity_validator
    from api.health import run_health_server_thread
    
    startup_logger.info("Core modules imported successfully")
except ImportError as e:
    startup_logger.critical(f"Error importing modules: {e}")
    startup_logger.critical("Please install dependencies with: pip install -r requirements.txt")
    sys.exit(1)

# Use production logger if available, fallback otherwise
try:
    logger = get_trading_logger('main')
except NameError:
    logger = logging.getLogger('main')

class TradingBot:
    def __init__(self):
        logger.info("Initializing Quantum Trading Bot...")
        
        # Set trading context for structured logging
        if hasattr(logger, 'set_trading_context'):
            logger.set_trading_context({
                "bot_version": "1.0.0",
                "target_return": "14%_daily",
                "primary_symbol": "ETHUSDT",
                "strategy": "ultra_high_frequency_scalping"
            })
        
        # SECURITY: Initialize environment manager first
        env_type = Environment.TESTNET if config.BINANCE_TESTNET else Environment.PRODUCTION
        if not environment_manager.initialize_environment(env_type):
            raise Exception("Failed to initialize trading environment")
        
        # Configure authenticity validator with Telegram alerts
        authenticity_validator.set_alert_callback(self._handle_security_alert)
        
        logger.info(f"Environment initialized: {env_type.value}")
        logger.info(f"Data authenticity validation: {'ENABLED' if authenticity_validator.validation_enabled else 'DISABLED'}")
        
        # Log critical production settings
        if env_type == Environment.PRODUCTION:
            logger.info("Production settings active",
                       leverage=config.DEFAULT_LEVERAGE,
                       risk_per_trade=config.RISK_PER_TRADE,
                       stop_loss=config.STOP_LOSS_PERCENT,
                       symbols=config.SYMBOLS)
        
        # Initialize components
        self.data_collector = DataCollector(config.SYMBOLS)
        self.correlation_engine = CorrelationEngine()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.executor = Executor()
        self.performance_tracker = PerformanceTracker()
        self.failure_analyzer = FailureAnalyzer()
        
        self.running = False
        
    async def start(self):
        """Start the trading bot"""
        self.running = True
        logger.info(f"Trading bot started at {datetime.now()}")
        
        # Start data collection
        await self.data_collector.start()
        
        # Main trading loop
        while self.running:
            try:
                # Collect latest data
                market_data = await self.data_collector.get_latest_data()
                
                # Calculate correlations
                correlations = self.correlation_engine.calculate(market_data)
                
                # Generate signals
                signals = self.signal_generator.generate(correlations, market_data)
                
                # Generate AXSUSDT ultra-high frequency signals
                if 'AXSUSDT' in market_data:
                    uhf_analysis = await ultra_high_frequency_trader.analyze_ultra_high_frequency_opportunity(
                        market_data, correlations
                    )
                    if uhf_analysis['signal']:
                        uhf_signal = uhf_analysis['signal']
                        uhf_signal['uhf_confidence'] = uhf_analysis['confidence']
                        uhf_signal['volatility_score'] = uhf_analysis['volatility_score']
                        signals.append(uhf_signal)
                        logger.info(f"UHF Signal added: AXSUSDT {uhf_signal['side']} "
                                  f"(confidence={uhf_analysis['confidence']:.2f})")
                        ultra_high_frequency_trader.update_signal_time()
                
                # Risk checks
                approved_signals = self.risk_manager.filter_signals(signals)
                
                # Execute trades
                for signal in approved_signals:
                    execution_result = await self.executor.execute(signal)
                    
                    # Track performance
                    self.performance_tracker.record_trade(execution_result)
                    
                    # Update ultra-high frequency trader metrics if AXSUSDT
                    if signal.get('symbol') == 'AXSUSDT' and hasattr(signal, 'trading_mode'):
                        if signal.get('trading_mode') == 'ultra_high_frequency':
                            ultra_high_frequency_trader.update_trade_result(execution_result)
                    
                    # Analyze if failed
                    if execution_result.status not in ['FILLED', 'SUCCESS']:
                        failure_analysis = self.failure_analyzer.analyze(
                            signal, execution_result, market_data
                        )
                        logger.warning(f"Trade failed: {failure_analysis}")
                
                # Log status
                logger.info(f"Signals: {len(signals)}, Approved: {len(approved_signals)}")
                
                await asyncio.sleep(1)  # Main loop frequency
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def stop(self):
        """Gracefully stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.running = False
        
        # Close all positions
        await self.executor.close_all_positions()
        
        # Stop data collection
        await self.data_collector.stop()
        
        # Save performance data
        self.performance_tracker.save_report()
        
        logger.info("Trading bot stopped correctly")
    
    async def _handle_security_alert(self, message: str):
        """Handle security alerts from authenticity validator"""
        logger.critical(f"SECURITY ALERT: {message}")
        try:
            # Import here to avoid circular imports
            from utils.telegram_notifier import telegram_notifier
            await telegram_notifier.send_error_alert(
                "CRITICAL SECURITY ALERT",
                f"Data authenticity violation detected:\n{message}",
                "SYSTEM"
            )
        except Exception as e:
            logger.error(f"Failed to send security alert: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Shutdown signal received: {signum}")
    
    # Attempt graceful shutdown
    if 'bot' in globals() and hasattr(bot, 'stop'):
        try:
            asyncio.create_task(bot.stop())
            logger.info("Graceful shutdown initiated")
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
    
    logger.info("Process terminating")
    sys.exit(0)

async def main():
    global bot
    
    try:
        # Start health check server for Railway
        health_port = int(os.getenv("HEALTH_CHECK_PORT", 8080))
        logger.info(f"Starting health check server on port {health_port}")
        run_health_server_thread(health_port)
        
        # Create bot instance
        logger.info("Creating bot instance...")
        bot = TradingBot()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Log final startup information
        startup_info = {
            "mode": "PRODUCTION" if not config.BINANCE_TESTNET else "TESTNET",
            "symbols": config.SYMBOLS,
            "leverage": config.DEFAULT_LEVERAGE,
            "risk_per_trade": config.RISK_PER_TRADE,
            "health_port": health_port,
            "deployment_id": os.getenv('RAILWAY_DEPLOYMENT_ID', 'local')
        }
        
        logger.info("Bot initialization complete", **startup_info)
        
        # Start bot with error handling
        await bot.start()
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Production-ready startup banner
    environment = "PRODUCTION" if not config.BINANCE_TESTNET else "TESTNET"
    deployment_id = os.getenv('RAILWAY_DEPLOYMENT_ID', 'local')
    
    print("=" * 60)
    print("🤖 QUANTUM TRADING BOT v1.0 - RAILWAY DEPLOYMENT")
    print("=" * 60)
    print(f"🌍 Environment: {environment}")
    print(f"📈 Symbols: {', '.join(config.SYMBOLS)}")
    print(f"⚡ Leverage: {config.DEFAULT_LEVERAGE}x")
    print(f"💰 Risk per Trade: {config.RISK_PER_TRADE*100:.1f}%")
    print(f"🆔 Deployment: {deployment_id}")
    print(f"🕒 Started: {datetime.now().isoformat()}")
    print("=" * 60)
    
    try:
        # Log startup to structured logging
        logger.info("Bot startup initiated",
                   environment=environment,
                   deployment_id=deployment_id,
                   startup_time=datetime.now().isoformat())
                   
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt)")
        print("\n[STOPPED] Bot stopped by user")
        
    except Exception as e:
        logger.critical(f"Fatal error during execution: {e}", exc_info=True)
        print(f"[ERROR] Fatal error: {e}")
        sys.exit(1)
        
    finally:
        logger.info("Bot process terminated")
        print("Bot process terminated")
