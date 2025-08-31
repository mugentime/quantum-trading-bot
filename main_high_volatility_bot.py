#!/usr/bin/env python3
"""
HIGH VOLATILITY QUANTUM TRADING BOT - MAIN EXECUTION
Complete high volatility pairs trading system with comprehensive monitoring,
risk management, and performance tracking.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import strategy components
from strategies.high_volatility_strategy import (
    HighVolatilityStrategy, HIGH_VOLATILITY_CONFIG
)
from config.volatility_config import (
    HighVolatilityConfig, TradingMode, ExchangeType,
    CONSERVATIVE_CONFIG, AGGRESSIVE_CONFIG
)
from monitoring.volatility_monitor import (
    VolatilityMonitor, create_default_alert_config
)
from backtesting.volatility_backtester import (
    VolatilityBacktester
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('high_volatility_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HighVolatilityTradingBot:
    """Main high volatility trading bot orchestrator"""
    
    def __init__(self, config_file: Optional[str] = None, trading_mode: str = "testnet"):
        # Load configuration
        if config_file and os.path.exists(config_file):
            self.config = HighVolatilityConfig(config_file)
        else:
            self.config = HighVolatilityConfig()
        
        # Set trading mode
        if trading_mode.lower() == "mainnet":
            self.config.set_trading_mode(TradingMode.MAINNET)
            logger.warning("🚨 MAINNET MODE: REAL MONEY TRADING ENABLED")
        else:
            self.config.set_trading_mode(TradingMode.TESTNET)
            logger.info("🧪 TESTNET MODE: Paper trading enabled")
        
        # Initialize components
        self.strategy = HighVolatilityStrategy(self.config.to_dict())
        self.monitor = VolatilityMonitor(self.config, create_default_alert_config())
        self.backtester = None
        
        # Bot state
        self.running = False
        self.start_time = None
        self.session_stats = {
            'total_trades': 0,
            'total_pnl': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'session_start': None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop_trading())
    
    async def initialize(self) -> bool:
        """Initialize the trading bot"""
        try:
            logger.info("🚀 INITIALIZING HIGH VOLATILITY QUANTUM TRADING BOT")
            logger.info("=" * 70)
            
            # Validate configuration
            warnings = self.config.validate_config()
            if warnings:
                logger.warning("Configuration warnings:")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
            
            # Display configuration summary
            await self._log_configuration_summary()
            
            # Validate API credentials
            if not await self._validate_credentials():
                logger.error("❌ API credential validation failed")
                return False
            
            # Initialize strategy
            await self.strategy.initialize_exchange()
            
            # Test connectivity
            try:
                balance = await self.strategy.get_account_balance()
                logger.info(f"💰 Account Balance: ${balance:.2f} USDT")
            except Exception as e:
                logger.error(f"❌ Failed to fetch account balance: {e}")
                return False
            
            # Initialize monitoring
            logger.info("🔍 Initializing monitoring system...")
            
            self.session_stats['session_start'] = datetime.now()
            
            logger.info("✅ Initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def _validate_credentials(self) -> bool:
        """Validate API credentials"""
        try:
            api_key = os.getenv('BINANCE_API_KEY')
            secret_key = os.getenv('BINANCE_SECRET_KEY')
            
            if not api_key or not secret_key:
                logger.error("❌ Missing Binance API credentials")
                logger.error("Please set BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables")
                return False
            
            # Mask keys in logs for security
            masked_key = f"{api_key[:8]}...{api_key[-8:]}"
            logger.info(f"🔑 API Key: {masked_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating credentials: {e}")
            return False
    
    async def _log_configuration_summary(self):
        """Log comprehensive configuration summary"""
        logger.info(f"📊 CONFIGURATION SUMMARY:")
        logger.info(f"  Trading Mode: {self.config.trading_mode.value.upper()}")
        logger.info(f"  Exchange: {self.config.exchange.value.upper()}")
        logger.info(f"  Max Risk Per Trade: {self.config.risk_management.max_risk_per_trade:.2%}")
        logger.info(f"  Max Leverage: {self.config.risk_management.max_leverage}x")
        logger.info(f"  Max Daily Loss: {self.config.risk_management.max_daily_loss:.2%}")
        logger.info(f"  Scan Interval: {self.config.scan_interval}s")
        
        primary_pairs = self.config.get_primary_pairs()
        secondary_pairs = self.config.get_secondary_pairs()
        
        logger.info(f"  Primary Pairs ({len(primary_pairs)}): {', '.join(primary_pairs)}")
        logger.info(f"  Secondary Pairs ({len(secondary_pairs)}): {', '.join(secondary_pairs)}")
        
        logger.info(f"  Volatility Thresholds:")
        logger.info(f"    - Hourly: >{self.config.volatility_thresholds.hourly_min:.1%}")
        logger.info(f"    - Daily: >{self.config.volatility_thresholds.daily_min:.1%}")
        logger.info(f"    - High Vol Percentile: >{self.config.volatility_thresholds.high_volatility_percentile}th")
    
    async def run_backtest(self, days: int = 30) -> Dict:
        """Run strategy backtest before live trading"""
        logger.info("🔄 RUNNING STRATEGY BACKTEST")
        logger.info("=" * 50)
        
        try:
            from datetime import timedelta
            
            # Create backtester
            self.backtester = VolatilityBacktester(self.config, initial_capital=10000)
            
            # Define backtest period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Backtesting period: {start_date.date()} to {end_date.date()}")
            logger.info(f"Initial capital: ${self.backtester.initial_capital:.2f}")
            
            # Run backtest
            results = await self.backtester.run_comprehensive_backtest(start_date, end_date)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"backtest_results/high_volatility_backtest_{timestamp}.json"
            
            os.makedirs("backtest_results", exist_ok=True)
            self.backtester.save_results(results, results_file)
            
            # Calculate overall performance
            total_trades = sum(r.total_trades for r in results.values())
            avg_return = sum(r.total_return for r in results.values()) / len(results) if results else 0
            profitable_pairs = len([r for r in results.values() if r.total_return > 0])
            
            logger.info("🎯 BACKTEST RESULTS SUMMARY:")
            logger.info(f"  Total Pairs Tested: {len(results)}")
            logger.info(f"  Profitable Pairs: {profitable_pairs}/{len(results)} ({profitable_pairs/len(results):.1%})")
            logger.info(f"  Total Trades: {total_trades}")
            logger.info(f"  Average Return: {avg_return:.2%}")
            logger.info(f"  Results saved to: {results_file}")
            
            # Show top performers
            sorted_results = sorted(results.items(), key=lambda x: x[1].total_return, reverse=True)
            logger.info("  Top 3 Performers:")
            for i, (symbol, result) in enumerate(sorted_results[:3]):
                logger.info(f"    {i+1}. {symbol}: {result.total_return:.2%} return, "
                          f"{result.total_trades} trades, {result.win_rate:.1%} win rate")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            return {}
    
    async def start_live_trading(self):
        """Start live trading with comprehensive monitoring"""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🚀 STARTING HIGH VOLATILITY LIVE TRADING")
        logger.info("=" * 60)
        logger.info(f"Start time: {self.start_time}")
        logger.info(f"Trading mode: {self.config.trading_mode.value.upper()}")
        
        try:
            # Start monitoring system
            monitor_task = asyncio.create_task(self.monitor.start_monitoring())
            
            # Start trading strategy
            strategy_task = asyncio.create_task(self.strategy.start_trading())
            
            # Start performance tracking
            tracking_task = asyncio.create_task(self._track_performance())
            
            # Wait for any task to complete (shouldn't happen in normal operation)
            done, pending = await asyncio.wait(
                [monitor_task, strategy_task, tracking_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Live trading error: {e}")
        finally:
            await self.stop_trading()
    
    async def _track_performance(self):
        """Track and log performance metrics"""
        logger.info("📊 Performance tracking started")
        
        while self.running:
            try:
                # Update session statistics
                if hasattr(self.strategy, 'active_positions'):
                    active_positions = len(self.strategy.active_positions)
                    if active_positions > 0:
                        logger.info(f"📍 Active positions: {active_positions}")
                
                # Log session summary every hour
                if self.start_time:
                    session_duration = datetime.now() - self.start_time
                    if session_duration.total_seconds() % 3600 < 60:  # Every hour
                        await self._log_session_summary()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Performance tracking error: {e}")
                await asyncio.sleep(60)
    
    async def _log_session_summary(self):
        """Log session performance summary"""
        try:
            if not self.start_time:
                return
            
            duration = datetime.now() - self.start_time
            hours = duration.total_seconds() / 3600
            
            # Get current balance
            try:
                current_balance = await self.strategy.get_account_balance()
            except:
                current_balance = 0
            
            logger.info("📊 SESSION SUMMARY:")
            logger.info(f"  Duration: {hours:.1f} hours")
            logger.info(f"  Current Balance: ${current_balance:.2f}")
            logger.info(f"  Active Positions: {len(getattr(self.strategy, 'active_positions', {}))}")
            
            # Get monitoring status
            status = self.monitor.get_current_status()
            perf = status['performance']
            risk = status['risk']
            
            logger.info(f"  Total Trades: {perf['total_trades']}")
            logger.info(f"  Win Rate: {perf['win_rate']:.1%}")
            logger.info(f"  Total P&L: ${perf['total_pnl']:.2f}")
            logger.info(f"  Risk Score: {risk['risk_score']}")
            
        except Exception as e:
            logger.error(f"Error logging session summary: {e}")
    
    async def stop_trading(self):
        """Stop trading and cleanup"""
        if not self.running:
            return
        
        logger.info("🛑 STOPPING HIGH VOLATILITY TRADING BOT")
        
        try:
            self.running = False
            
            # Stop strategy
            if self.strategy:
                await self.strategy.stop_trading()
            
            # Stop monitoring
            if self.monitor:
                await self.monitor.stop_trading()
            
            # Final session summary
            if self.start_time:
                duration = datetime.now() - self.start_time
                logger.info(f"📊 FINAL SESSION SUMMARY:")
                logger.info(f"  Total Duration: {duration}")
                logger.info(f"  Session completed at: {datetime.now()}")
            
            logger.info("✅ High Volatility Trading Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def create_config_preset(self, preset_name: str) -> HighVolatilityConfig:
        """Create configuration preset for different risk levels"""
        if preset_name.lower() == "conservative":
            return CONSERVATIVE_CONFIG
        elif preset_name.lower() == "aggressive":
            return AGGRESSIVE_CONFIG
        else:
            return HighVolatilityConfig()

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="High Volatility Quantum Trading Bot")
    parser.add_argument('--mode', choices=['testnet', 'mainnet'], default='testnet',
                       help='Trading mode (default: testnet)')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--preset', choices=['conservative', 'aggressive'], 
                       help='Configuration preset')
    parser.add_argument('--backtest-only', action='store_true',
                       help='Run backtest only, no live trading')
    parser.add_argument('--backtest-days', type=int, default=30,
                       help='Backtest period in days (default: 30)')
    parser.add_argument('--skip-backtest', action='store_true',
                       help='Skip backtest and start live trading directly')
    
    args = parser.parse_args()
    
    print("🌊 HIGH VOLATILITY QUANTUM TRADING BOT")
    print("=" * 60)
    print("🎯 Target: Extreme price movements (>5% hourly, >15% daily)")
    print("⚡ Strategy: Volatility breakouts + momentum + volume")
    print("🛡️ Risk: Dynamic stops (0.8-1.5%), 3-10x leverage") 
    print("🔍 Features: Real-time monitoring, alerts, backtesting")
    print("=" * 60)
    
    try:
        # Create bot instance
        bot = HighVolatilityTradingBot(
            config_file=args.config,
            trading_mode=args.mode
        )
        
        # Apply preset if specified
        if args.preset:
            bot.config = bot.create_config_preset(args.preset)
            logger.info(f"Applied {args.preset.upper()} configuration preset")
        
        # Initialize bot
        if not await bot.initialize():
            logger.error("❌ Bot initialization failed")
            return
        
        # Run backtest if not skipped
        if not args.skip_backtest:
            logger.info("🔄 Running strategy backtest...")
            backtest_results = await bot.run_backtest(days=args.backtest_days)
            
            if not backtest_results:
                logger.error("❌ Backtest failed, cannot proceed to live trading")
                return
            
            # Check if backtest results are acceptable
            total_trades = sum(r.total_trades for r in backtest_results.values())
            profitable_pairs = len([r for r in backtest_results.values() if r.total_return > 0])
            
            if total_trades == 0:
                logger.warning("⚠️ No trades generated in backtest - market conditions may not be suitable")
                response = input("Continue to live trading? (y/n): ")
                if response.lower() != 'y':
                    logger.info("User chose to abort")
                    return
            elif profitable_pairs / len(backtest_results) < 0.3:  # <30% profitable
                logger.warning("⚠️ Low profitability in backtest - consider adjusting strategy")
                response = input("Continue to live trading? (y/n): ")
                if response.lower() != 'y':
                    logger.info("User chose to abort")
                    return
        
        # Exit if backtest-only mode
        if args.backtest_only:
            logger.info("✅ Backtest completed. Exiting (backtest-only mode)")
            return
        
        # Confirm live trading for mainnet
        if args.mode == 'mainnet':
            print("\n🚨 WARNING: MAINNET MODE - REAL MONEY TRADING")
            print("This will trade with real funds on your account!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("User aborted mainnet trading")
                return
        
        # Start live trading
        await bot.start_live_trading()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error("Full traceback:", exc_info=True)
    finally:
        logger.info("🏁 High Volatility Quantum Trading Bot session ended")

if __name__ == "__main__":
    # Set up proper asyncio event loop policy for Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)