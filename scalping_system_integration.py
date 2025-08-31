"""
Scalping System Integration
Complete integration of the redesigned correlation-based scalping system
Combines real-time signal generation with comprehensive backtesting
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import ccxt.async_support as ccxt
import pandas as pd
import numpy as np

from core.scalping_correlation_engine import ScalpingCorrelationEngine, ScalpingSignal, MarketRegime
from core.scalping_backtest_engine import ScalpingBacktestEngine, BacktestMetrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScalpingSystemManager:
    """Complete scalping system management and coordination"""
    
    def __init__(self):
        self.exchange = None
        self.scalping_engine = None
        self.backtest_engine = None
        
        # Configuration
        self.config = {
            'exchange': {
                'name': 'binance',
                'sandbox': False,
                'api_key': None,
                'secret': None
            },
            'scalping': {
                'target_daily_signals': 35,
                'target_win_rate': 0.80,
                'target_profit_per_trade': 0.005,
                'max_concurrent_signals': 5,
                'signal_update_interval': 30,  # seconds
                'risk_per_trade': 0.02  # 2%
            },
            'backtest': {
                'initial_capital': 10000.0,
                'backtest_days': 7,
                'commission_rate': 0.001,
                'slippage_rate': 0.0005
            }
        }
        
        # Performance tracking
        self.live_performance = {
            'signals_generated': 0,
            'signals_executed': 0,
            'current_win_rate': 0.0,
            'daily_pnl': 0.0,
            'active_signals': 0
        }
        
        # Results storage
        self.results_dir = Path("scalping_results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def initialize_system(self):
        """Initialize the complete scalping system"""
        try:
            logger.info("Initializing Scalping System...")
            
            # Initialize exchange
            self.exchange = ccxt.binance({
                'sandbox': self.config['exchange']['sandbox'],
                'enableRateLimit': True,
                'apiKey': self.config['exchange'].get('api_key'),
                'secret': self.config['exchange'].get('secret')
            })
            
            # Test exchange connection
            try:
                await self.exchange.fetch_markets()
                logger.info("Exchange connection established")
            except Exception as e:
                logger.warning(f"Exchange connection failed, using demo mode: {e}")
                self.config['exchange']['sandbox'] = True
            
            # Initialize scalping engine
            self.scalping_engine = ScalpingCorrelationEngine(self.exchange)
            await self.scalping_engine.initialize_real_time_feeds()
            
            # Initialize backtest engine
            self.backtest_engine = ScalpingBacktestEngine(self.exchange)
            
            logger.info("Scalping system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing scalping system: {e}")
            raise
    
    async def run_comprehensive_backtest(self, days: int = 7) -> Dict:
        """Run comprehensive backtest analysis"""
        try:
            logger.info(f"Running {days}-day comprehensive backtest...")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Run backtest
            metrics = await self.backtest_engine.run_backtest(
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.config['backtest']['initial_capital']
            )
            
            # Analyze results
            results = self.analyze_backtest_results(metrics)
            
            # Save results
            results_file = self.results_dir / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Backtest completed and saved to {results_file}")
            return results
            
        except Exception as e:
            logger.error(f"Error running comprehensive backtest: {e}")
            return {}
    
    def analyze_backtest_results(self, metrics: BacktestMetrics) -> Dict:
        """Analyze and format backtest results"""
        try:
            analysis = {
                'summary': {
                    'total_trades': metrics.total_trades,
                    'win_rate': f"{metrics.win_rate:.1%}",
                    'total_return': f"{metrics.total_pnl_pct:.2%}",
                    'max_drawdown': f"{metrics.max_drawdown_pct:.2%}",
                    'sharpe_ratio': round(metrics.sharpe_ratio, 2),
                    'profit_factor': round(metrics.profit_factor, 2)
                },
                'performance_targets': {
                    'daily_signal_target': self.config['scalping']['target_daily_signals'],
                    'actual_trades_per_day': round(metrics.trades_per_day, 1),
                    'target_win_rate': f"{self.config['scalping']['target_win_rate']:.1%}",
                    'actual_win_rate': f"{metrics.win_rate:.1%}",
                    'target_met': {
                        'signal_frequency': metrics.trades_per_day >= self.config['scalping']['target_daily_signals'] * 0.8,
                        'win_rate': metrics.win_rate >= self.config['scalping']['target_win_rate'] * 0.9,
                        'profit_factor': metrics.profit_factor >= 1.5
                    }
                },
                'quality_analysis': {
                    'premium_signals': f"{metrics.premium_signal_win_rate:.1%}",
                    'high_quality': f"{metrics.high_signal_win_rate:.1%}",
                    'medium_quality': f"{metrics.medium_signal_win_rate:.1%}",
                    'low_quality': f"{metrics.low_signal_win_rate:.1%}",
                    'recommendation': self.get_quality_recommendation(metrics)
                },
                'regime_analysis': {
                    'best_regime': self.get_best_regime(metrics),
                    'volatile_market_pnl': f"{metrics.volatile_regime_pnl:.2%}",
                    'calm_market_pnl': f"{metrics.calm_regime_pnl:.2%}",
                    'breakdown_market_pnl': f"{metrics.breakdown_regime_pnl:.2%}",
                    'transitional_market_pnl': f"{metrics.transitional_regime_pnl:.2%}"
                },
                'timeframe_analysis': {
                    '1min_win_rate': f"{metrics.tf_1m_win_rate:.1%}",
                    '3min_win_rate': f"{metrics.tf_3m_win_rate:.1%}",
                    '5min_win_rate': f"{metrics.tf_5m_win_rate:.1%}",
                    'best_timeframe': self.get_best_timeframe(metrics)
                },
                'risk_analysis': {
                    'avg_hold_time': f"{metrics.avg_hold_time_minutes:.1f} minutes",
                    'max_hold_time': f"{metrics.max_hold_time_minutes} minutes",
                    'risk_per_trade': f"{self.config['scalping']['risk_per_trade']:.1%}",
                    'cost_impact': {
                        'slippage_cost': f"{metrics.total_slippage_cost:.2f}",
                        'commission_cost': f"{metrics.total_commission_cost:.2f}",
                        'total_cost_impact': f"{(metrics.total_slippage_cost + metrics.total_commission_cost):.2f}"
                    }
                },
                'recommendations': self.generate_recommendations(metrics)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing backtest results: {e}")
            return {}
    
    def get_quality_recommendation(self, metrics: BacktestMetrics) -> str:
        """Generate quality-based recommendation"""
        if metrics.premium_signal_win_rate > 0.85:
            return "Focus on Premium quality signals - exceptional performance"
        elif metrics.high_signal_win_rate > 0.75:
            return "Use High and Premium quality signals - good balance"
        elif metrics.medium_signal_win_rate > 0.65:
            return "All signal qualities performing adequately - current setup optimal"
        else:
            return "Consider tightening signal quality filters - performance below target"
    
    def get_best_regime(self, metrics: BacktestMetrics) -> str:
        """Identify best performing market regime"""
        regime_performance = {
            'volatile': metrics.volatile_regime_pnl,
            'calm': metrics.calm_regime_pnl,
            'breakdown': metrics.breakdown_regime_pnl,
            'transitional': metrics.transitional_regime_pnl
        }
        return max(regime_performance, key=regime_performance.get)
    
    def get_best_timeframe(self, metrics: BacktestMetrics) -> str:
        """Identify best performing timeframe"""
        tf_performance = {
            '1m': metrics.tf_1m_win_rate,
            '3m': metrics.tf_3m_win_rate,
            '5m': metrics.tf_5m_win_rate
        }
        return max(tf_performance, key=tf_performance.get)
    
    def generate_recommendations(self, metrics: BacktestMetrics) -> List[str]:
        """Generate system optimization recommendations"""
        recommendations = []
        
        # Win rate analysis
        if metrics.win_rate < self.config['scalping']['target_win_rate']:
            recommendations.append("Increase signal quality threshold to improve win rate")
        
        # Signal frequency analysis
        if metrics.trades_per_day < self.config['scalping']['target_daily_signals'] * 0.8:
            recommendations.append("Lower correlation thresholds to increase signal frequency")
        elif metrics.trades_per_day > self.config['scalping']['target_daily_signals'] * 1.5:
            recommendations.append("Increase selectivity to reduce over-trading")
        
        # Profit factor analysis
        if metrics.profit_factor < 1.5:
            recommendations.append("Improve risk/reward ratios or tighten stop losses")
        elif metrics.profit_factor > 3.0:
            recommendations.append("Consider increasing position sizes - system highly profitable")
        
        # Drawdown analysis
        if metrics.max_drawdown_pct > 0.15:  # 15% max drawdown threshold
            recommendations.append("Reduce position sizes or implement better risk management")
        
        # Hold time analysis
        if metrics.avg_hold_time_minutes > 30:
            recommendations.append("Consider tighter profit targets for faster turnover")
        elif metrics.avg_hold_time_minutes < 5:
            recommendations.append("May be exiting positions too quickly - consider wider targets")
        
        # Quality distribution
        if metrics.low_signal_win_rate > metrics.high_signal_win_rate:
            recommendations.append("Review signal quality calculation - unexpected performance pattern")
        
        if not recommendations:
            recommendations.append("System performing well - maintain current parameters")
        
        return recommendations
    
    async def generate_live_signals(self, max_signals: int = 5) -> List[ScalpingSignal]:
        """Generate live scalping signals"""
        try:
            if not self.scalping_engine:
                raise ValueError("Scalping engine not initialized")
            
            # Generate signals
            signals = await self.scalping_engine.generate_scalping_signals()
            
            # Filter and limit signals
            live_signals = signals[:max_signals]
            
            # Update performance tracking
            self.live_performance['signals_generated'] += len(live_signals)
            self.live_performance['active_signals'] = len(self.scalping_engine.active_signals)
            
            # Log signals
            for i, signal in enumerate(live_signals):
                logger.info(f"Live Signal #{i+1}: {signal.symbol} {signal.signal_type.upper()} "
                           f"@ {signal.entry_price:.6f} (Quality: {signal.quality.value}, "
                           f"Confidence: {signal.confidence:.2f})")
            
            return live_signals
            
        except Exception as e:
            logger.error(f"Error generating live signals: {e}")
            return []
    
    async def monitor_system_performance(self) -> Dict:
        """Monitor current system performance"""
        try:
            # Get engine metrics
            engine_metrics = self.scalping_engine.get_performance_metrics()
            
            # Combine with live performance
            performance = {
                'timestamp': datetime.now().isoformat(),
                'live_performance': self.live_performance,
                'engine_metrics': engine_metrics,
                'system_health': {
                    'regime_detection': engine_metrics.get('regime_confidence', 0) > 0.3,
                    'signal_generation': engine_metrics.get('active_signals', 0) > 0,
                    'target_progress': {
                        'daily_signals': f"{engine_metrics.get('total_signals', 0)}/{self.config['scalping']['target_daily_signals']}",
                        'win_rate_status': "ON_TARGET" if engine_metrics.get('win_rate', 0) >= self.config['scalping']['target_win_rate'] * 0.9 else "BELOW_TARGET"
                    }
                }
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Error monitoring system performance: {e}")
            return {}
    
    async def run_live_scalping_session(self, duration_minutes: int = 60):
        """Run live scalping session"""
        try:
            logger.info(f"Starting {duration_minutes}-minute live scalping session")
            
            session_start = datetime.now()
            session_end = session_start + timedelta(minutes=duration_minutes)
            
            signal_count = 0
            last_signal_time = datetime.now()
            
            while datetime.now() < session_end:
                try:
                    # Generate signals
                    signals = await self.generate_live_signals()
                    
                    if signals:
                        signal_count += len(signals)
                        last_signal_time = datetime.now()
                        
                        # Display top signal
                        top_signal = signals[0]
                        print(f"\n🎯 TOP SIGNAL: {top_signal.symbol} {top_signal.signal_type.upper()}")
                        print(f"   Entry: {top_signal.entry_price:.6f}")
                        print(f"   Stop Loss: {top_signal.stop_loss:.6f}")
                        print(f"   Take Profit: {top_signal.take_profit:.6f}")
                        print(f"   Quality: {top_signal.quality.value} ({top_signal.confidence:.1%} confidence)")
                        print(f"   Timeframe: {top_signal.timeframe} | Regime: {top_signal.market_regime.value}")
                        print(f"   Risk/Reward: {top_signal.risk_reward_ratio:.1f}:1")
                    
                    # Monitor performance
                    if datetime.now().minute % 5 == 0:  # Every 5 minutes
                        performance = await self.monitor_system_performance()
                        print(f"\n📊 Session Stats: {signal_count} signals generated, "
                              f"Regime: {performance['engine_metrics'].get('current_regime', 'unknown')}")
                    
                    # Wait before next iteration
                    await asyncio.sleep(self.config['scalping']['signal_update_interval'])
                    
                except KeyboardInterrupt:
                    logger.info("Live session interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Error in live session: {e}")
                    await asyncio.sleep(self.config['scalping']['signal_update_interval'])
            
            # Session summary
            session_duration = (datetime.now() - session_start).total_seconds() / 60
            signals_per_hour = (signal_count / session_duration) * 60
            
            print(f"\n🏁 SESSION COMPLETE")
            print(f"   Duration: {session_duration:.1f} minutes")
            print(f"   Total Signals: {signal_count}")
            print(f"   Signals/Hour: {signals_per_hour:.1f}")
            print(f"   Target Met: {'✅' if signals_per_hour >= 20 else '❌'}")
            
        except Exception as e:
            logger.error(f"Error in live scalping session: {e}")
    
    async def run_complete_system_test(self):
        """Run complete system test with backtest and live demo"""
        try:
            print("🚀 SCALPING SYSTEM INTEGRATION TEST")
            print("=" * 50)
            
            # Initialize system
            await self.initialize_system()
            
            # Run backtest
            print("\n📈 RUNNING COMPREHENSIVE BACKTEST...")
            backtest_results = await self.run_comprehensive_backtest(days=3)  # 3-day backtest
            
            if backtest_results:
                print(f"\n✅ BACKTEST RESULTS:")
                summary = backtest_results['summary']
                print(f"   Total Trades: {summary['total_trades']}")
                print(f"   Win Rate: {summary['win_rate']}")
                print(f"   Total Return: {summary['total_return']}")
                print(f"   Sharpe Ratio: {summary['sharpe_ratio']}")
                print(f"   Profit Factor: {summary['profit_factor']}")
                
                # Show recommendations
                print(f"\n💡 RECOMMENDATIONS:")
                for rec in backtest_results.get('recommendations', []):
                    print(f"   • {rec}")
            
            # Run live demo
            print(f"\n🎯 STARTING 5-MINUTE LIVE DEMO...")
            await self.run_live_scalping_session(duration_minutes=5)
            
            print(f"\n✅ SYSTEM TEST COMPLETE")
            
        except Exception as e:
            logger.error(f"Error in complete system test: {e}")
            print(f"❌ System test failed: {e}")
        
        finally:
            if self.exchange:
                await self.exchange.close()


async def main():
    """Main execution function"""
    try:
        # Create system manager
        system = ScalpingSystemManager()
        
        # Run complete test
        await system.run_complete_system_test()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Main execution failed: {e}")

if __name__ == "__main__":
    # Run the complete scalping system integration
    asyncio.run(main())