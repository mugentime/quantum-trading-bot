#!/usr/bin/env python3
"""
Execute Full Comprehensive Optimization System
- Fixed syntax errors 
- Multi-pair backtesting (BTC, ETH, SOL, ADA, AVAX)
- 30-day historical data from Binance testnet
- 2-iteration parameter optimization
- Live testnet deployment
- Comprehensive reporting
"""

import asyncio
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_full_system():
    """Execute the complete optimization system"""
    
    print("=" * 80)
    print("EXECUTING COMPREHENSIVE OPTIMIZATION SYSTEM")
    print("=" * 80)
    print("Phase 1: Parameter Optimization (Iteration 1)")
    print("Phase 2: Parameter Optimization (Iteration 2)")  
    print("Phase 3: Live Testnet Trading Deployment")
    print("Phase 4: Comprehensive Performance Report")
    print("=" * 80)
    
    try:
        # Import the system
        from comprehensive_optimization_system import ComprehensiveOptimizationSystem
        
        # Initialize system
        system = ComprehensiveOptimizationSystem()
        
        print(f"Initialized system for pairs: {', '.join(system.pairs)}")
        print(f"Backtest period: {system.backtest_days} days")
        print(f"API Key: {system.api_key[:8]}...")
        print()
        
        # Run the complete system
        start_time = datetime.now()
        result = await system.run_comprehensive_system()
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds() / 60  # minutes
        
        if result and result[0]:  # Check if filename was returned
            filename, report = result
            
            print("=" * 80)
            print("EXECUTION COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"Total execution time: {execution_time:.1f} minutes")
            print(f"Report saved: {filename}")
            print()
            
            # Display final summary
            if report and 'optimization_results' in report:
                print("FINAL PERFORMANCE SUMMARY:")
                print("-" * 40)
                total_return = 0
                pair_count = 0
                
                for symbol, results in report['optimization_results'].items():
                    return_pct = results.get('optimized_return_pct', 0)
                    sharpe = results.get('sharpe_ratio', 0)
                    win_rate = results.get('win_rate', 0)
                    trades = results.get('total_trades', 0)
                    
                    print(f"{symbol:8}: {return_pct:+6.2f}% | Sharpe: {sharpe:5.2f} | Win: {win_rate:5.1f}% | Trades: {trades:3d}")
                    
                    total_return += return_pct
                    pair_count += 1
                
                if pair_count > 0:
                    avg_return = total_return / pair_count
                    print("-" * 40)
                    print(f"Average:  {avg_return:+6.2f}% return across {pair_count} pairs")
                
                # Live trading results
                live_results = report.get('live_trading_results', {})
                if live_results and not live_results.get('error'):
                    live_pnl = live_results.get('total_pnl', 0)
                    live_trades = live_results.get('total_trades', 0)
                    print(f"Live P&L: ${live_pnl:+6.2f} from {live_trades} trades")
            
            print()
            print("RECOMMENDATIONS:")
            recommendations = report.get('recommendations', [])
            for rec in recommendations:
                print(f"  {rec}")
            
            print("\n" + "=" * 80)
            print("SUCCESS: Comprehensive optimization completed!")
            print(f"Check {filename} for detailed analysis.")
            print("=" * 80)
            
            return True
            
        else:
            print("=" * 80)
            print("EXECUTION FAILED")
            print("=" * 80)
            print("The optimization system did not complete successfully.")
            print("Check the logs above for error details.")
            return False
            
    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        print("Ensure comprehensive_optimization_system.py is in the same directory")
        return False
        
    except Exception as e:
        logger.error(f"System execution failed: {e}")
        print(f"EXECUTION ERROR: {e}")
        return False

async def main():
    """Main entry point"""
    print("Starting comprehensive optimization system...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = await run_full_system()
    
    if success:
        print("\nSystem execution completed successfully!")
        return 0
    else:
        print("\nSystem execution failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)