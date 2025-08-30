#!/usr/bin/env python3
"""
Enhanced Main Entry Point for Quantum Trading Bot
Integrates intelligent leverage optimization with correlation trading
"""

import os
import sys
import json
import time
import signal
from datetime import datetime
import traceback

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core components
from core.enhanced_leverage_trader import EnhancedLeverageTrader
from utils.logger import setup_logger
from utils.telegram_notifier import TelegramNotifier as EnhancedTelegramNotifier

class QuantumTradingBotEnhanced:
    def __init__(self):
        self.logger = setup_logger('quantum_bot')
        self.telegram_notifier = EnhancedTelegramNotifier()
        self.leverage_trader = None
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("Quantum Trading Bot Enhanced - Initializing...")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def send_startup_notification(self):
        """Send startup notification with leverage config summary"""
        try:
            # Load leverage config for summary
            if os.path.exists('optimized_leverage_config.json'):
                with open('optimized_leverage_config.json', 'r') as f:
                    config = json.load(f)
                
                message = "🚀 QUANTUM TRADING BOT ENHANCED - STARTED\n\n"
                message += "📊 INTELLIGENT LEVERAGE CONFIGURATION:\n"
                
                # Sort pairs by priority
                sorted_pairs = sorted(
                    config['trading_pairs'].items(),
                    key=lambda x: x[1]['priority']
                )
                
                for symbol, params in sorted_pairs:
                    risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
                    risk_indicator = risk_emoji.get(params['risk_level'], "⚪")
                    
                    message += f"{symbol}: {params['leverage']}x {risk_indicator}\n"
                
                message += f"\n📈 OPTIMIZATION SUMMARY:\n"
                message += f"Total Pairs: {config['optimization_summary']['total_pairs_analyzed']}\n"
                message += f"Profitable Pairs: {config['optimization_summary']['profitable_pairs']}\n"
                message += f"Average Return: {config['optimization_summary']['average_return']:.2f}%\n"
                message += f"Best Performer: {config['optimization_summary']['best_performer']}\n"
                message += f"\n⚡ System started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
            else:
                message = "🚀 QUANTUM TRADING BOT ENHANCED - STARTED\n"
                message += "⚠️ Using default leverage configuration\n"
                message += f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.telegram_notifier.send_message(message)
            self.logger.info("Startup notification sent")
            
        except Exception as e:
            self.logger.error(f"Error sending startup notification: {e}")
    
    def run(self):
        """Main execution loop"""
        try:
            self.logger.info("Starting Quantum Trading Bot Enhanced...")
            
            # Initialize leverage trader
            self.leverage_trader = EnhancedLeverageTrader()
            
            # Send startup notification
            self.send_startup_notification()
            
            cycle_count = 0
            
            # Main trading loop
            while self.running:
                cycle_count += 1
                
                try:
                    self.logger.info(f"Starting trading cycle #{cycle_count}")
                    
                    # Run leverage-optimized trading cycle
                    self.leverage_trader.run_trading_cycle()
                    
                    # Get status report
                    status = self.leverage_trader.get_status_report()
                    
                    # Log status
                    if 'error' not in status:
                        self.logger.info(f"Cycle #{cycle_count} completed: "
                                       f"{status['active_positions']} positions, "
                                       f"P&L: {status['total_unrealized_pnl_pct']:.2f}%")
                        
                        # Send periodic status updates (every 12 cycles = ~1 hour)
                        if cycle_count % 12 == 0:
                            self.send_status_update(status, cycle_count)
                    else:
                        self.logger.error(f"Status report error: {status['error']}")
                    
                    # Wait before next cycle (5 minutes for leverage trading)
                    for i in range(300):  # 5 minutes = 300 seconds
                        if not self.running:
                            break
                        time.sleep(1)
                    
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received, shutting down...")
                    break
                    
                except Exception as e:
                    self.logger.error(f"Error in trading cycle #{cycle_count}: {e}")
                    self.logger.error(traceback.format_exc())
                    
                    # Send error notification
                    error_message = f"❌ ERROR in cycle #{cycle_count}\n{str(e)[:200]}..."
                    self.telegram_notifier.send_message(error_message)
                    
                    # Wait a bit longer after errors
                    time.sleep(60)
            
        except Exception as e:
            self.logger.error(f"Critical error in main run loop: {e}")
            self.logger.error(traceback.format_exc())
            
            # Send critical error notification
            critical_message = f"🚨 CRITICAL ERROR\nBot stopped unexpectedly\n{str(e)[:200]}..."
            self.telegram_notifier.send_message(critical_message)
            
        finally:
            self.shutdown()
    
    def send_status_update(self, status, cycle_count):
        """Send periodic status update to Telegram"""
        try:
            message = f"📊 STATUS UPDATE (Cycle #{cycle_count})\n\n"
            message += f"💰 Account Balance: ${status['account_balance']:,.2f}\n"
            message += f"📈 Active Positions: {status['active_positions']}\n"
            message += f"💸 Total P&L: {status['total_unrealized_pnl_pct']:+.2f}%\n"
            
            if status['position_details']:
                message += "\n🎯 POSITION DETAILS:\n"
                
                for symbol, details in status['position_details'].items():
                    risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
                    risk_indicator = risk_emoji.get(details['risk_level'], "⚪")
                    
                    message += f"{symbol}: {details['side']} {details['leverage']}x {risk_indicator} "
                    message += f"({details['unrealized_pnl_pct']:+.2f}%)\n"
            
            message += f"\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.telegram_notifier.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending status update: {e}")
    
    def shutdown(self):
        """Graceful shutdown procedure"""
        try:
            self.logger.info("Initiating graceful shutdown...")
            
            # Close any remaining positions if needed
            if self.leverage_trader and hasattr(self.leverage_trader, 'active_positions'):
                active_positions = len(self.leverage_trader.active_positions)
                if active_positions > 0:
                    self.logger.info(f"Warning: {active_positions} positions remain active")
                    
                    # Send final status
                    final_status = self.leverage_trader.get_status_report()
                    if 'error' not in final_status:
                        message = f"🛑 BOT SHUTDOWN\n\n"
                        message += f"Active Positions: {final_status['active_positions']}\n"
                        message += f"Total P&L: {final_status['total_unrealized_pnl_pct']:+.2f}%\n"
                        message += f"\n⚠️ Manual position management may be required"
                        
                        self.telegram_notifier.send_message(message)
            
            # Send shutdown notification
            shutdown_message = f"🛑 QUANTUM TRADING BOT ENHANCED - SHUTDOWN\n"
            shutdown_message += f"Stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            shutdown_message += "System shutdown completed"
            
            self.telegram_notifier.send_message(shutdown_message)
            
            self.logger.info("Graceful shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

def main():
    """Main entry point"""
    print("="*60)
    print("🚀 QUANTUM TRADING BOT ENHANCED")
    print("   Intelligent Leverage Optimization System")
    print("="*60)
    
    # Check for leverage config
    if os.path.exists('optimized_leverage_config.json'):
        print("✅ Leverage configuration loaded")
        with open('optimized_leverage_config.json', 'r') as f:
            config = json.load(f)
            print(f"   - {len(config['trading_pairs'])} trading pairs configured")
            print(f"   - {config['optimization_summary']['profitable_pairs']} profitable pairs")
            print(f"   - Best performer: {config['optimization_summary']['best_performer']}")
    else:
        print("⚠️  No leverage configuration found - using defaults")
    
    print()
    
    # Initialize and run bot
    bot = QuantumTradingBotEnhanced()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        traceback.print_exc()
    
    print("🏁 Quantum Trading Bot Enhanced - Stopped")

if __name__ == "__main__":
    main()