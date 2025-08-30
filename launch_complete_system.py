#!/usr/bin/env python3
"""
Complete Trading System Launcher
Simple launcher for the comprehensive 3-phase trading system
"""

import asyncio
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import master orchestrator
from master_trading_orchestrator import MasterTradingOrchestrator

def print_banner():
    """Print system banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                      QUANTUM TRADING BOT - COMPLETE SYSTEM                      ║
║                           Comprehensive Optimization & Deployment                ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  PHASE 1: Multi-Pair Backtesting (30 days real data)                          ║
║  PHASE 2: 2-Iteration Parameter Optimization                                    ║
║  PHASE 3: Live Testnet Deployment with Monitoring                              ║
║                                                                                  ║
║  🎯 TARGET: Maintain 68.4% win rate, achieve 5%+ returns                       ║
║  📊 PAIRS: BTC, ETH, SOL, ADA, AVAX, MATIC, BNB, XRP, DOT, LINK               ║
║  🔐 API: Binance Testnet with provided credentials                             ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
    """)

def print_requirements():
    """Print system requirements"""
    print("📋 SYSTEM REQUIREMENTS:")
    print("   ✅ Python 3.8+")
    print("   ✅ Required packages: ccxt, pandas, numpy, asyncio")
    print("   ✅ Internet connection for market data")
    print("   ✅ Binance testnet API access")
    print()

def get_user_preferences():
    """Get user preferences for execution"""
    preferences = {}
    
    print("⚙️  SYSTEM CONFIGURATION:")
    print()
    
    # Live trading duration
    while True:
        try:
            duration = input("Enter live trading duration in minutes (default: 60): ").strip()
            duration = int(duration) if duration else 60
            if 1 <= duration <= 1440:  # 1 minute to 24 hours
                preferences['live_duration'] = duration
                break
            else:
                print("❌ Duration must be between 1 and 1440 minutes")
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Auto-proceed or manual approval
    proceed = input("Auto-proceed through all phases? (y/n, default: y): ").strip().lower()
    preferences['auto_proceed'] = proceed != 'n'
    
    # Verbose logging
    verbose = input("Enable verbose logging? (y/n, default: n): ").strip().lower()
    preferences['verbose'] = verbose == 'y'
    
    print()
    return preferences

def confirm_execution(preferences):
    """Confirm execution parameters"""
    print("🔍 EXECUTION SUMMARY:")
    print(f"   📊 Backtesting: 10 pairs × 30 days real data")
    print(f"   🎯 Optimization: 2 iterations with parameter tuning")
    print(f"   🚀 Live Trading: {preferences['live_duration']} minutes on testnet")
    print(f"   📈 Auto-proceed: {'Yes' if preferences['auto_proceed'] else 'No (manual approval per phase)'}")
    print(f"   📝 Verbose Logs: {'Yes' if preferences['verbose'] else 'No'}")
    print()
    
    if not preferences['auto_proceed']:
        confirm = input("Proceed with execution? (y/n): ").strip().lower()
        return confirm == 'y'
    
    print("🚀 Starting execution in 3 seconds...")
    import time
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    return True

async def run_with_error_handling():
    """Run the complete system with comprehensive error handling"""
    try:
        # Initialize orchestrator
        orchestrator = MasterTradingOrchestrator()
        
        # Get user preferences
        preferences = get_user_preferences()
        
        # Confirm execution
        if not confirm_execution(preferences):
            print("❌ Execution cancelled by user")
            return None
        
        print("🎬 STARTING COMPLETE TRADING SYSTEM EXECUTION")
        print("=" * 80)
        
        # Run the complete system
        if preferences['auto_proceed']:
            # Fully automated execution
            final_report = await orchestrator.run_complete_system(preferences['live_duration'])
        else:
            # Manual approval per phase
            print("🔄 Running Phase 1: Comprehensive Backtesting...")
            optimization_report = await orchestrator.run_phase_1_comprehensive_backtest()
            
            proceed = input("\nProceed to Phase 2? (y/n): ").strip().lower()
            if proceed != 'y':
                print("❌ Execution stopped after Phase 1")
                return orchestrator.generate_master_report()
            
            print("🔄 Running Phase 2: Validation & Configuration...")
            enhanced_config = await orchestrator.run_phase_2_validation(optimization_report)
            
            proceed = input("\nProceed to Phase 3 Live Trading? (y/n): ").strip().lower()
            if proceed != 'y':
                print("❌ Execution stopped after Phase 2")
                return orchestrator.generate_master_report()
            
            print("🔄 Running Phase 3: Live Deployment...")
            live_report = await orchestrator.run_phase_3_live_deployment(
                enhanced_config, preferences['live_duration']
            )
            
            final_report = orchestrator.generate_master_report()
        
        return final_report
        
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user (Ctrl+C)")
        print("Generating partial report...")
        try:
            return orchestrator.generate_master_report()
        except:
            return None
    
    except Exception as e:
        print(f"\n❌ SYSTEM ERROR: {e}")
        print("Check logs for detailed error information")
        return None

def save_execution_summary(report, preferences):
    """Save execution summary"""
    if not report:
        print("⚠️  No report generated - system may have failed")
        return
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"execution_summary_{timestamp}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("QUANTUM TRADING BOT - EXECUTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            # Execution info
            summary = report.get('master_orchestrator_summary', {})
            f.write(f"Execution Time: {summary.get('total_execution_time_minutes', 0):.1f} minutes\n")
            f.write(f"Phases Completed: {summary.get('phases_completed', 0)}/3\n")
            f.write(f"Ready for Production: {summary.get('ready_for_production', False)}\n\n")
            
            # Performance
            perf = report.get('performance_summary', {})
            f.write("PERFORMANCE METRICS:\n")
            f.write(f"Backtest Return: {perf.get('backtest_avg_return', 0):+.2f}%\n")
            f.write(f"Backtest Win Rate: {perf.get('backtest_win_rate', 0):.1f}%\n")
            f.write(f"Live P&L: {perf.get('live_pnl_pct', 0):+.2f}%\n")
            f.write(f"Live Win Rate: {perf.get('live_win_rate', 0):.1f}%\n\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS:\n")
            for rec in report.get('recommendations', []):
                f.write(f"- {rec}\n")
        
        print(f"📄 Execution summary saved: {summary_file}")
        
    except Exception as e:
        print(f"⚠️  Could not save execution summary: {e}")

async def main():
    """Main launcher function"""
    # Print banner and requirements
    print_banner()
    print_requirements()
    
    # Check basic requirements
    try:
        import ccxt
        import pandas as pd
        import numpy as np
        print("✅ All required packages found")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install: pip install ccxt pandas numpy python-dotenv")
        return
    
    print()
    
    # Run the system
    preferences = get_user_preferences()
    final_report = await run_with_error_handling()
    
    # Save summary
    save_execution_summary(final_report, preferences)
    
    # Final message
    print("\n" + "=" * 80)
    print("🏁 SYSTEM EXECUTION COMPLETED")
    
    if final_report:
        summary = final_report.get('master_orchestrator_summary', {})
        if summary.get('ready_for_production', False):
            print("✅ RESULT: System is ready for production deployment")
        else:
            print("⚠️  RESULT: System requires further optimization")
    else:
        print("❌ RESULT: System execution failed or incomplete")
    
    print("\nCheck generated reports for detailed analysis.")
    print("Thank you for using Quantum Trading Bot!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Launcher interrupted")
    except Exception as e:
        print(f"\n❌ Launcher failed: {e}")