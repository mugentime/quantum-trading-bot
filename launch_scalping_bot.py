#!/usr/bin/env python3
"""
Scalping Bot Launcher
Optimized launcher for high-frequency ETHUSDT scalping system
"""
import asyncio
import os
import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config.settings import config
from core.config.scalping_config import scalping_config
from utils.logger_config import setup_logger
from utils.telegram_notifier import TelegramNotifier

logger = setup_logger("ScalpingLauncher", level=logging.INFO)

def check_environment():
    """Check environment setup and requirements"""
    logger.info("🔍 Checking environment setup...")
    
    # Check required environment variables
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    # Check optional but recommended variables
    optional_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_optional:
        logger.warning(f"⚠️ Missing optional variables (notifications disabled): {missing_optional}")
    
    logger.info("✅ Environment check completed")
    return True

def validate_scalping_config():
    """Validate scalping configuration"""
    logger.info("🔧 Validating scalping configuration...")
    
    validation = scalping_config.validate_config()
    
    if not validation['valid']:
        logger.error("❌ Invalid scalping configuration:")
        for error in validation['errors']:
            logger.error(f"  - {error}")
        return False
    
    if validation['warnings']:
        logger.warning("⚠️ Configuration warnings:")
        for warning in validation['warnings']:
            logger.warning(f"  - {warning}")
    
    # Log key configuration parameters
    params = scalping_config.parameters
    logger.info("📋 Scalping Configuration:")
    logger.info(f"  Symbol: {params.PRIMARY_SYMBOL}")
    logger.info(f"  Timeframe: {params.MAIN_TIMEFRAME}")
    logger.info(f"  Target Trades/Day: {params.TARGET_TRADES_PER_DAY}")
    logger.info(f"  Stop Loss: {params.STOP_LOSS_PERCENT:.1%}")
    logger.info(f"  Take Profit: {params.TAKE_PROFIT_PERCENT:.1%}")
    logger.info(f"  Leverage: {params.OPTIMAL_LEVERAGE}x")
    logger.info(f"  Position Size: {params.BASE_POSITION_SIZE:.1%}")
    
    logger.info("✅ Configuration validation completed")
    return True

async def test_connections():
    """Test critical connections before launch"""
    logger.info("🔗 Testing connections...")
    
    try:
        # Test Telegram notification (if configured)
        telegram = TelegramNotifier()
        if telegram.enabled:
            await telegram.send_message("🧪 **Connection Test**\nScalping bot launcher test message")
            logger.info("✅ Telegram connection successful")
        else:
            logger.info("ℹ️ Telegram notifications not configured")
        
        # Test exchange connection would go here
        # We'll skip this to avoid unnecessary API calls during setup
        
        logger.info("✅ Connection tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

def display_pre_launch_summary():
    """Display pre-launch summary and warnings"""
    logger.info("=" * 60)
    logger.info("🚀 SCALPING BOT PRE-LAUNCH SUMMARY")
    logger.info("=" * 60)
    
    params = scalping_config.parameters
    
    logger.info(f"📊 STRATEGY OVERVIEW:")
    logger.info(f"   Symbol: {params.PRIMARY_SYMBOL}")
    logger.info(f"   Strategy: High-Frequency Scalping")
    logger.info(f"   Timeframe: {params.MAIN_TIMEFRAME}")
    logger.info(f"   Daily Target: {params.DAILY_TARGET_PERCENT:.1%}")
    logger.info(f"   Target Trades: {params.TARGET_TRADES_PER_DAY}/day")
    
    logger.info(f"⚖️ RISK PARAMETERS:")
    logger.info(f"   Stop Loss: {params.STOP_LOSS_PERCENT:.1%}")
    logger.info(f"   Take Profit: {params.TAKE_PROFIT_PERCENT:.1%}")
    logger.info(f"   Max Drawdown: {params.DRAWDOWN_LIMIT_PERCENT:.1%}")
    logger.info(f"   Position Size: {params.BASE_POSITION_SIZE:.1%}")
    logger.info(f"   Leverage: {params.OPTIMAL_LEVERAGE}x")
    
    logger.info(f"⚡ EXECUTION SETTINGS:")
    logger.info(f"   Signal Interval: {config.SIGNAL_GENERATION_INTERVAL}s")
    logger.info(f"   Min Signal Gap: {config.MIN_SIGNAL_INTERVAL}s")
    logger.info(f"   Order Timeout: {config.ORDER_TIMEOUT}s")
    logger.info(f"   Max Slippage: {config.SLIPPAGE_TOLERANCE:.3%}")
    
    logger.info(f"🕐 TRADING HOURS:")
    logger.info(f"   Active: {params.ACTIVE_HOURS_START} - {params.ACTIVE_HOURS_END} UTC")
    logger.info(f"   Testnet: {'YES' if config.BINANCE_TESTNET else 'NO'}")
    
    logger.info("=" * 60)
    
    # Display warnings
    logger.warning("⚠️ IMPORTANT WARNINGS:")
    logger.warning("   - This is a HIGH-FREQUENCY trading system")
    logger.warning("   - Trades will be executed automatically every 30 seconds")
    logger.warning("   - Stop loss is set to 1.2% - positions will close quickly")
    logger.warning("   - Target is 20+ trades per day with high leverage")
    logger.warning("   - Ensure you understand the risks before proceeding")
    
    if not config.BINANCE_TESTNET:
        logger.warning("🚨 REAL MONEY WARNING:")
        logger.warning("   - You are using LIVE trading with REAL MONEY")
        logger.warning("   - Losses can occur rapidly with high-frequency trading")
        logger.warning("   - Consider using testnet first: BINANCE_TESTNET=true")
    
    logger.info("=" * 60)

async def launch_scalping_bot(args):
    """Launch the scalping bot with specified parameters"""
    try:
        # Import here to avoid circular imports
        from scalping_main import ScalpingTradingBot
        
        logger.info("🚀 Launching Scalping Trading Bot...")
        
        # Create and start the bot
        bot = ScalpingTradingBot()
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"💥 Fatal error in scalping bot: {e}", exc_info=True)
        raise

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(
        description="High-Frequency Scalping Bot Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_scalping_bot.py                    # Launch with default settings
  python launch_scalping_bot.py --dry-run         # Test mode without launching
  python launch_scalping_bot.py --force           # Skip confirmations
  python launch_scalping_bot.py --config-check    # Only check configuration
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Test configuration without launching bot')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')
    parser.add_argument('--config-check', action='store_true',
                       help='Only check configuration and exit')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Step 1: Environment check
        if not check_environment():
            sys.exit(1)
        
        # Step 2: Configuration validation
        if not validate_scalping_config():
            sys.exit(1)
        
        # Step 3: Connection tests
        if not asyncio.run(test_connections()):
            if not args.force:
                sys.exit(1)
        
        # Step 4: Display summary
        display_pre_launch_summary()
        
        # Configuration check only
        if args.config_check:
            logger.info("✅ Configuration check completed successfully")
            return
        
        # Dry run mode
        if args.dry_run:
            logger.info("🧪 Dry run completed - configuration is valid")
            logger.info("Use --force to skip this message and launch immediately")
            return
        
        # Confirmation prompt (unless forced)
        if not args.force:
            print("\n" + "=" * 60)
            print("⚠️  FINAL CONFIRMATION REQUIRED")
            print("=" * 60)
            
            if config.BINANCE_TESTNET:
                print("You are about to start TESTNET scalping with the above parameters.")
            else:
                print("🚨 You are about to start LIVE scalping with REAL MONEY!")
                print("💰 This will execute high-frequency trades automatically.")
            
            response = input("\nType 'START' to begin scalping: ").strip().upper()
            
            if response != 'START':
                print("Launch cancelled by user.")
                return
        
        # Step 5: Launch the bot
        logger.info(f"🎯 Starting scalping bot at {datetime.now()}")
        asyncio.run(launch_scalping_bot(args))
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Launch cancelled by user")
    except Exception as e:
        logger.error(f"💥 Launch failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()