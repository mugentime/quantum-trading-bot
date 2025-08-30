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

# Simplified imports for startup
print("Starting Quantum Trading Bot...")
print("Loading configuration...")

try:
    from core.config.settings import config
    from core.data_collector import DataCollector
    from core.correlation_engine import CorrelationEngine
    from core.signal_generator import SignalGenerator
    from core.executor import Executor
    from core.risk_manager import RiskManager
    from analytics.performance import PerformanceTracker
    from analytics.failure_analyzer import FailureAnalyzer
    from utils.logger import setup_logger
    from core.environment_manager import environment_manager, Environment
    from core.data_authenticity_validator import authenticity_validator
except ImportError as e:
    print(f"[ERROR] Error importing modules: {e}")
    print("Please install dependencies with: pip install -r requirements.txt")
    sys.exit(1)

# Setup logging
logger = setup_logger('main')

class TradingBot:
    def __init__(self):
        logger.info("Initializing Quantum Trading Bot...")
        
        # SECURITY: Initialize environment manager first
        env_type = Environment.TESTNET if config.BINANCE_TESTNET else Environment.PRODUCTION
        if not environment_manager.initialize_environment(env_type):
            raise Exception("Failed to initialize trading environment")
        
        # Configure authenticity validator with Telegram alerts
        authenticity_validator.set_alert_callback(self._handle_security_alert)
        
        logger.info(f"Environment initialized: {env_type.value}")
        logger.info(f"Data authenticity validation: {'ENABLED' if authenticity_validator.validation_enabled else 'DISABLED'}")
        
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
                
                # Risk checks
                approved_signals = self.risk_manager.filter_signals(signals)
                
                # Execute trades
                for signal in approved_signals:
                    execution_result = await self.executor.execute(signal)
                    
                    # Track performance
                    self.performance_tracker.record_trade(execution_result)
                    
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
    """Handle shutdown signals"""
    logger.info(f"Signal received {signum}")
    sys.exit(0)

async def main():
    global bot
    
    # Create bot instance
    bot = TradingBot()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot
    await bot.start()

if __name__ == "__main__":
    print("=" * 50)
    print("QUANTUM TRADING BOT v1.0")
    print("=" * 50)
    print(f"Mode: {'TESTNET' if config.BINANCE_TESTNET else 'PRODUCTION'}")
    print(f"Symbols: {', '.join(config.SYMBOLS)}")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] Bot stopped by user")
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        sys.exit(1)
