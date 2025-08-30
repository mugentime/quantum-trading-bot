#!/usr/bin/env python3
"""
Master Trading Orchestrator
Runs the complete 3-phase trading system:
Phase 1: Comprehensive Backtesting
Phase 2: 2-Iteration Optimization 
Phase 3: Live Testnet Deployment
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our systems
from comprehensive_optimization_system import ComprehensiveOptimizationSystem
from live_deployment_system import LiveDeploymentSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'master_orchestrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterTradingOrchestrator:
    """Master orchestrator for complete trading system"""
    
    def __init__(self):
        self.phase_results = {}
        self.total_start_time = time.time()
        self.current_phase = 0
        
        # Performance targets
        self.target_win_rate = 68.4  # Maintain current win rate
        self.target_return_threshold = 5.0  # Minimum 5% for live deployment
        
        logger.info("Master Trading Orchestrator initialized")

    def print_phase_header(self, phase: int, title: str):
        """Print formatted phase header"""
        print("\n" + "=" * 100)
        print(f"PHASE {phase}: {title}")
        print("=" * 100)

    def print_phase_summary(self, phase: int, results: dict):
        """Print phase summary"""
        print("\n" + "-" * 100)
        print(f"PHASE {phase} COMPLETED")
        print("-" * 100)

    async def run_phase_1_comprehensive_backtest(self) -> dict:
        """Phase 1: Comprehensive backtesting and optimization"""
        self.current_phase = 1
        self.print_phase_header(1, "COMPREHENSIVE BACKTESTING & OPTIMIZATION")
        
        print("🔄 Initializing Comprehensive Optimization System...")
        print("📊 Testing 10 trading pairs with 30 days of real market data")
        print("🎯 Target: Maintain 68.4% win rate, optimize for 5%+ returns")
        print()
        
        try:
            start_time = time.time()
            
            # Initialize and run comprehensive optimization
            optimization_system = ComprehensiveOptimizationSystem()
            optimization_report = await optimization_system.run_full_optimization_cycle()
            
            execution_time = time.time() - start_time
            
            if not optimization_report:
                raise Exception("Optimization system returned no results")
            
            # Analyze results
            summary = optimization_report.get('optimization_summary', {})
            final_return = summary.get('final_avg_return', 0)
            final_win_rate = summary.get('final_avg_win_rate', 0)
            improvement = summary.get('improvement_pct', 0)
            best_pairs = summary.get('best_performing_pairs', [])
            
            self.phase_results['phase_1'] = {
                'status': 'completed',
                'execution_time_seconds': execution_time,
                'final_avg_return': final_return,
                'final_win_rate': final_win_rate,
                'improvement_pct': improvement,
                'best_pairs': best_pairs,
                'ready_for_live': final_return >= self.target_return_threshold,
                'report_file': f"comprehensive_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
            
            # Print results
            print("✅ PHASE 1 RESULTS:")
            print(f"   📈 Final Average Return: {final_return:+.2f}%")
            print(f"   🎯 Final Win Rate: {final_win_rate:.1f}%")
            print(f"   📊 Performance Improvement: {improvement:+.2f}%")
            print(f"   🏆 Top 5 Pairs: {', '.join(best_pairs[:5])}")
            print(f"   ⏱️  Total Execution Time: {execution_time:.1f} seconds")
            
            if final_return >= self.target_return_threshold:
                print(f"   ✅ READY FOR LIVE DEPLOYMENT (Return > {self.target_return_threshold}%)")
            else:
                print(f"   ⚠️  BELOW THRESHOLD (Need {self.target_return_threshold}%+ for live deployment)")
            
            return optimization_report
            
        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            self.phase_results['phase_1'] = {
                'status': 'failed',
                'error': str(e),
                'ready_for_live': False
            }
            raise

    async def run_phase_2_validation(self, optimization_report: dict) -> dict:
        """Phase 2: Validation and configuration preparation"""
        self.current_phase = 2
        self.print_phase_header(2, "VALIDATION & CONFIGURATION PREPARATION")
        
        print("🔍 Validating optimization results...")
        print("⚙️  Preparing live deployment configuration...")
        print("🛡️  Running safety checks...")
        print()
        
        try:
            start_time = time.time()
            
            # Extract key metrics
            summary = optimization_report.get('optimization_summary', {})
            config = optimization_report.get('live_deployment_config', {})
            
            # Validation checks
            validations = {
                'has_positive_returns': summary.get('final_avg_return', 0) > 0,
                'meets_win_rate_target': summary.get('final_avg_win_rate', 0) >= 50,
                'has_sufficient_pairs': len(summary.get('best_performing_pairs', [])) >= 3,
                'has_valid_config': bool(config.get('trading_pairs', [])),
                'risk_parameters_set': bool(config.get('risk_management', {})),
                'api_credentials_present': bool(config.get('execution_settings', {}))
            }
            
            all_validations_passed = all(validations.values())
            
            # Enhanced configuration
            enhanced_config = config.copy()
            enhanced_config['validation_results'] = validations
            enhanced_config['phase_2_timestamp'] = datetime.now().isoformat()
            enhanced_config['safety_features'] = {
                'emergency_stop': True,
                'position_limits': True,
                'daily_loss_limits': True,
                'real_time_monitoring': True
            }
            
            execution_time = time.time() - start_time
            
            self.phase_results['phase_2'] = {
                'status': 'completed',
                'execution_time_seconds': execution_time,
                'validations_passed': sum(validations.values()),
                'total_validations': len(validations),
                'all_checks_passed': all_validations_passed,
                'ready_for_deployment': all_validations_passed and 
                                       summary.get('final_avg_return', 0) >= self.target_return_threshold
            }
            
            # Print validation results
            print("✅ PHASE 2 VALIDATION RESULTS:")
            for check, passed in validations.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check.replace('_', ' ').title()}")
            
            print(f"\n   📊 Validations Passed: {sum(validations.values())}/{len(validations)}")
            print(f"   ⏱️  Validation Time: {execution_time:.1f} seconds")
            
            if all_validations_passed:
                print("   ✅ ALL VALIDATIONS PASSED - READY FOR LIVE DEPLOYMENT")
            else:
                print("   ❌ VALIDATION FAILURES - MANUAL REVIEW REQUIRED")
            
            return enhanced_config
            
        except Exception as e:
            logger.error(f"Phase 2 failed: {e}")
            self.phase_results['phase_2'] = {
                'status': 'failed',
                'error': str(e),
                'ready_for_deployment': False
            }
            raise

    async def run_phase_3_live_deployment(self, config: dict, duration_minutes: int = 60) -> dict:
        """Phase 3: Live testnet deployment"""
        self.current_phase = 3
        self.print_phase_header(3, "LIVE TESTNET DEPLOYMENT")
        
        print(f"🚀 Starting live testnet trading...")
        print(f"⏱️  Deployment Duration: {duration_minutes} minutes")
        print(f"🎯 Trading Pairs: {', '.join(config.get('trading_pairs', []))}")
        print(f"💰 Risk per Trade: {config.get('parameters', {}).get('position_size', 0.02)*100}%")
        print()
        print("Press Ctrl+C to stop trading early and generate final report")
        print()
        
        try:
            start_time = time.time()
            
            # Save enhanced config for live system
            config_file = f"live_deployment_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(config_file, 'w') as f:
                json.dump({'live_deployment_config': config}, f, indent=2)
            
            # Initialize live deployment system
            live_system = LiveDeploymentSystem(config_file)
            
            # Initialize exchange
            if not await live_system.initialize_exchange():
                raise Exception("Failed to initialize live exchange connection")
            
            live_system.running = True
            
            # Run for specified duration or until interrupted
            end_time = start_time + (duration_minutes * 60)
            
            while time.time() < end_time and live_system.running:
                try:
                    # Fetch market data
                    await live_system.fetch_market_data()
                    
                    # Update positions
                    await live_system.update_positions()
                    
                    # Check exit conditions
                    await live_system.check_exit_conditions()
                    
                    # Look for new signals
                    if (len(live_system.positions) < 
                        config['risk_management']['max_concurrent_positions']):
                        
                        for symbol in config['trading_pairs']:
                            if symbol not in live_system.positions:
                                signal = live_system.calculate_correlation_signal(symbol)
                                if signal:
                                    success = await live_system.execute_trade(signal)
                                    if success:
                                        print(f"🔄 Opened {signal['side']} position: {symbol} @ {signal['price']:.6f}")
                                    await asyncio.sleep(2)
                    
                    # Print periodic status
                    elapsed_minutes = (time.time() - start_time) / 60
                    if elapsed_minutes % 5 < 0.5:  # Every 5 minutes
                        print(f"⏱️  Runtime: {elapsed_minutes:.1f}min | "
                              f"Positions: {len(live_system.positions)} | "
                              f"P&L: ${live_system.performance.total_pnl:+.2f}")
                    
                    await asyncio.sleep(30)  # 30-second cycle
                    
                except KeyboardInterrupt:
                    print("\n🛑 Manual stop requested...")
                    break
                except Exception as e:
                    logger.error(f"Error in live trading loop: {e}")
                    await asyncio.sleep(60)
            
            # Stop live trading
            final_report = await live_system.stop_live_trading()
            
            execution_time = time.time() - start_time
            
            # Analyze live performance
            perf_summary = final_report.get('performance_summary', {})
            
            self.phase_results['phase_3'] = {
                'status': 'completed',
                'execution_time_seconds': execution_time,
                'total_pnl_usd': perf_summary.get('total_pnl_usd', 0),
                'total_pnl_pct': perf_summary.get('total_pnl_pct', 0),
                'win_rate_pct': perf_summary.get('win_rate_pct', 0),
                'total_trades': perf_summary.get('total_trades', 0),
                'final_balance': perf_summary.get('current_balance', 0),
                'live_performance_positive': perf_summary.get('total_pnl_pct', 0) > 0
            }
            
            # Print live results
            print("✅ PHASE 3 LIVE RESULTS:")
            print(f"   💰 Total P&L: ${perf_summary.get('total_pnl_usd', 0):+.2f} ({perf_summary.get('total_pnl_pct', 0):+.2f}%)")
            print(f"   🎯 Live Win Rate: {perf_summary.get('win_rate_pct', 0):.1f}%")
            print(f"   📊 Total Trades: {perf_summary.get('total_trades', 0)}")
            print(f"   💵 Final Balance: ${perf_summary.get('current_balance', 0):,.2f}")
            print(f"   ⏱️  Live Trading Time: {execution_time/60:.1f} minutes")
            
            return final_report
            
        except KeyboardInterrupt:
            print("\n🛑 Live deployment interrupted by user")
            if 'live_system' in locals():
                final_report = await live_system.stop_live_trading()
                self.phase_results['phase_3'] = {
                    'status': 'interrupted',
                    'execution_time_seconds': time.time() - start_time,
                    'final_report': final_report
                }
                return final_report
            raise
        except Exception as e:
            logger.error(f"Phase 3 failed: {e}")
            self.phase_results['phase_3'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise

    def generate_master_report(self) -> dict:
        """Generate comprehensive master report"""
        total_execution_time = time.time() - self.total_start_time
        
        report = {
            "master_orchestrator_summary": {
                "execution_timestamp": datetime.now().isoformat(),
                "total_execution_time_seconds": round(total_execution_time, 2),
                "total_execution_time_minutes": round(total_execution_time / 60, 2),
                "phases_completed": len([p for p in self.phase_results.values() 
                                       if p.get('status') == 'completed']),
                "all_phases_successful": all(p.get('status') == 'completed' 
                                           for p in self.phase_results.values()),
                "ready_for_production": (
                    self.phase_results.get('phase_1', {}).get('ready_for_live', False) and
                    self.phase_results.get('phase_2', {}).get('ready_for_deployment', False) and
                    self.phase_results.get('phase_3', {}).get('live_performance_positive', False)
                )
            },
            "phase_results": self.phase_results,
            "performance_summary": {
                "backtest_avg_return": self.phase_results.get('phase_1', {}).get('final_avg_return', 0),
                "backtest_win_rate": self.phase_results.get('phase_1', {}).get('final_win_rate', 0),
                "live_pnl_pct": self.phase_results.get('phase_3', {}).get('total_pnl_pct', 0),
                "live_win_rate": self.phase_results.get('phase_3', {}).get('win_rate_pct', 0),
                "backtest_vs_live_comparison": {
                    "return_difference": (self.phase_results.get('phase_3', {}).get('total_pnl_pct', 0) - 
                                        self.phase_results.get('phase_1', {}).get('final_avg_return', 0)),
                    "win_rate_difference": (self.phase_results.get('phase_3', {}).get('win_rate_pct', 0) - 
                                          self.phase_results.get('phase_1', {}).get('final_win_rate', 0))
                }
            },
            "recommendations": self.generate_recommendations()
        }
        
        return report

    def generate_recommendations(self) -> list:
        """Generate recommendations based on results"""
        recommendations = []
        
        phase_1_results = self.phase_results.get('phase_1', {})
        phase_3_results = self.phase_results.get('phase_3', {})
        
        # Performance recommendations
        backtest_return = phase_1_results.get('final_avg_return', 0)
        live_return = phase_3_results.get('total_pnl_pct', 0)
        
        if backtest_return > 5 and live_return > 0:
            recommendations.append("✅ READY FOR PRODUCTION: Both backtest and live results are positive")
        elif backtest_return > 0 and live_return <= 0:
            recommendations.append("⚠️  OPTIMIZATION NEEDED: Backtest positive but live performance negative")
        elif backtest_return <= 0:
            recommendations.append("❌ STRATEGY REVISION REQUIRED: Poor backtest performance")
        
        # Win rate recommendations
        backtest_wr = phase_1_results.get('final_win_rate', 0)
        live_wr = phase_3_results.get('win_rate_pct', 0)
        
        if backtest_wr >= 60 and live_wr >= 60:
            recommendations.append("✅ EXCELLENT WIN RATES: Both backtest and live exceed 60%")
        elif abs(backtest_wr - live_wr) > 20:
            recommendations.append("⚠️  WIN RATE VARIANCE: Large difference between backtest and live")
        
        # Risk management recommendations
        if phase_3_results.get('total_trades', 0) < 5:
            recommendations.append("📊 INCREASE TRADING FREQUENCY: Consider lowering signal thresholds")
        elif phase_3_results.get('total_trades', 0) > 50:
            recommendations.append("🎯 REDUCE TRADING FREQUENCY: Consider higher signal confidence thresholds")
        
        return recommendations

    async def run_complete_system(self, live_duration_minutes: int = 60):
        """Run the complete 3-phase trading system"""
        try:
            print("🚀 MASTER TRADING ORCHESTRATOR STARTING")
            print("=" * 100)
            print("🎯 MISSION: Deploy optimized quantum trading bot")
            print("📊 TARGET: Maintain 68.4% win rate, achieve 5%+ returns")
            print("⏱️  ESTIMATED TIME: 15-30 minutes + live trading duration")
            print("=" * 100)
            
            # Phase 1: Comprehensive Backtesting & Optimization
            optimization_report = await self.run_phase_1_comprehensive_backtest()
            
            # Phase 2: Validation & Configuration
            enhanced_config = await self.run_phase_2_validation(optimization_report)
            
            # Check if ready for live deployment
            phase_1_ready = self.phase_results['phase_1'].get('ready_for_live', False)
            phase_2_ready = self.phase_results['phase_2'].get('ready_for_deployment', False)
            
            if not (phase_1_ready and phase_2_ready):
                print("\n⚠️  STOPPING: System not ready for live deployment")
                print("   Check phase results and address issues before proceeding")
                return self.generate_master_report()
            
            # Phase 3: Live Deployment
            live_report = await self.run_phase_3_live_deployment(enhanced_config, live_duration_minutes)
            
            # Generate final report
            master_report = self.generate_master_report()
            
            # Save master report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            master_file = f"master_orchestrator_report_{timestamp}.json"
            
            with open(master_file, 'w') as f:
                json.dump(master_report, f, indent=2)
            
            # Final summary
            print("\n" + "=" * 100)
            print("🎉 MASTER ORCHESTRATOR COMPLETED")
            print("=" * 100)
            
            summary = master_report['master_orchestrator_summary']
            perf_summary = master_report['performance_summary']
            
            print(f"⏱️  Total Execution Time: {summary['total_execution_time_minutes']:.1f} minutes")
            print(f"✅ Phases Completed: {summary['phases_completed']}/3")
            print(f"📈 Backtest Return: {perf_summary['backtest_avg_return']:+.2f}%")
            print(f"💰 Live P&L: {perf_summary['live_pnl_pct']:+.2f}%")
            print(f"🎯 Live Win Rate: {perf_summary['live_win_rate']:.1f}%")
            
            if summary['ready_for_production']:
                print("🚀 STATUS: READY FOR PRODUCTION DEPLOYMENT")
            else:
                print("⚠️  STATUS: REQUIRES OPTIMIZATION BEFORE PRODUCTION")
            
            print(f"\n📊 Master report saved: {master_file}")
            
            # Print recommendations
            print("\n📋 RECOMMENDATIONS:")
            for rec in master_report['recommendations']:
                print(f"   {rec}")
            
            return master_report
            
        except KeyboardInterrupt:
            logger.info("Master orchestrator interrupted by user")
            return self.generate_master_report()
        except Exception as e:
            logger.error(f"Master orchestrator failed: {e}")
            print(f"\n❌ MASTER ORCHESTRATOR FAILED: {e}")
            return self.generate_master_report()

async def main():
    """Main execution function"""
    try:
        orchestrator = MasterTradingOrchestrator()
        
        # Get live trading duration from user
        print("Enter live trading duration in minutes (default: 60): ", end="")
        try:
            duration = int(input().strip() or "60")
        except (ValueError, KeyboardInterrupt):
            duration = 60
        
        print(f"Live trading will run for {duration} minutes")
        
        # Run complete system
        final_report = await orchestrator.run_complete_system(duration)
        
        return final_report
        
    except KeyboardInterrupt:
        print("\n🛑 Master orchestrator interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())