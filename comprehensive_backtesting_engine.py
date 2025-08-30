#!/usr/bin/env python3
"""
Comprehensive Backtesting Engine for 10 Trading Pairs
Generates detailed performance metrics for 30-day historical analysis
"""

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv

load_dotenv()

# Import existing components
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_correlation_engine import EnhancedCorrelationEngine
from core.optimization_integrator import optimization_integrator
from core.data_authenticity_validator import authenticity_validator
from utils.logger import setup_logger

logger = setup_logger('backtesting')

@dataclass
class TradeResult:
    """Individual trade result"""
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: str
    exit_time: str
    pnl_pct: float
    pnl_usd: float
    exit_reason: str
    correlation: float
    deviation: float

@dataclass
class PairPerformance:
    """Performance metrics for a trading pair"""
    symbol: str
    total_return_pct: float
    total_return_usd: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    avg_trade_pnl: float
    best_trade_pct: float
    worst_trade_pct: float
    profit_factor: float
    volatility: float
    avg_hold_time_hours: float
    trades: List[TradeResult]

class ComprehensiveBacktestEngine:
    """Comprehensive backtesting engine for multiple pairs"""
    
    def __init__(self):
        self.pairs = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
            'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', 'DOTUSDT', 'LINKUSDT'
        ]
        self.exchange = None
        self.correlation_engine = None  # Will be initialized after exchange
        self.backtest_days = 30
        self.initial_balance = 10000.0  # Starting balance per pair
        self.position_size = 0.02  # 2% risk per trade
        
        logger.info(f"Backtesting engine initialized for {len(self.pairs)} pairs")
        
    async def initialize_exchange(self):
        """Initialize exchange connection"""
        try:
            self.exchange = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': True,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
            
            # Test connection
            await self.exchange.fetch_time()
            
            # Initialize correlation engine after exchange is ready
            from core.enhanced_correlation_engine import EnhancedCorrelationEngine
            self.correlation_engine = EnhancedCorrelationEngine(self.exchange)
            
            logger.info("Exchange connection established for backtesting")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            return False
    
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        try:
            # Fetch data with 15-minute timeframe
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            limit = int(days * 24 * 4)  # 15-minute candles
            
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol, 
                timeframe='15m',
                since=since,
                limit=limit
            )
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Validate data authenticity
            sample_data = {
                'symbol': symbol,
                'data_points': len(df),
                'price_range': {'min': df['close'].min(), 'max': df['close'].max()},
                'volume_avg': df['volume'].mean(),
                'timespan_days': days
            }
            
            if not authenticity_validator.validate_market_data(sample_data, f"historical_{symbol}"):
                raise Exception(f"Historical data validation failed for {symbol}")
            
            logger.info(f"Fetched {len(df)} data points for {symbol} ({days} days)")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def run_pair_backtest(self, symbol: str, data: pd.DataFrame) -> PairPerformance:
        """Run backtest for a single trading pair"""
        logger.info(f"Starting backtest for {symbol}")
        
        trades = []
        balance = self.initial_balance
        position = None
        equity_curve = [balance]
        
        # Calculate returns for correlation analysis
        data['returns'] = data['close'].pct_change().dropna()
        
        for i in range(50, len(data)):  # Start after 50 periods for correlation calculation
            current_time = data.index[i]
            current_price = data['close'].iloc[i]
            
            # Get recent price data for correlation
            recent_data = data.iloc[max(0, i-50):i]
            
            try:
                # Simulate correlation signal generation
                if len(recent_data) >= 50:
                    # Calculate correlation with market (using returns variance as proxy)
                    volatility = recent_data['returns'].std()
                    mean_return = recent_data['returns'].mean()
                    
                    # Enhanced correlation simulation
                    correlation = np.corrcoef(
                        recent_data['returns'].dropna(),
                        recent_data['volume'].pct_change().dropna()[:len(recent_data['returns'].dropna())]
                    )[0, 1] if len(recent_data) > 10 else 0.5
                    
                    # Calculate deviation score
                    z_score = abs((current_price - recent_data['close'].mean()) / recent_data['close'].std())
                    deviation = min(z_score / 3.0, 1.0)  # Normalize to 0-1
                    
                    # Generate signal based on correlation breakdown and deviation
                    signal_threshold = 0.3
                    
                    if position is None and deviation > signal_threshold:
                        # Entry signal
                        side = 'BUY' if mean_return > 0 else 'SELL'
                        quantity = (balance * self.position_size) / current_price
                        
                        position = {
                            'symbol': symbol,
                            'side': side,
                            'entry_price': current_price,
                            'entry_time': current_time,
                            'quantity': quantity,
                            'correlation': correlation,
                            'deviation': deviation
                        }
                        
                        logger.debug(f"{symbol} ENTRY: {side} at {current_price:.4f}, deviation: {deviation:.3f}")
                        
                    elif position is not None:
                        # Exit conditions
                        hold_time = (current_time - position['entry_time']).total_seconds() / 3600  # hours
                        
                        # Calculate unrealized P&L
                        if position['side'] == 'BUY':
                            pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
                        else:
                            pnl_pct = ((position['entry_price'] - current_price) / position['entry_price']) * 100
                        
                        pnl_usd = (pnl_pct / 100) * position['quantity'] * position['entry_price']
                        
                        # Exit conditions
                        should_exit = False
                        exit_reason = ""
                        
                        # Time-based exit (2 hours)
                        if hold_time >= 2:
                            should_exit = True
                            exit_reason = "Time Exit"
                            
                        # Take profit (3% target)
                        elif pnl_pct >= 3.0:
                            should_exit = True
                            exit_reason = "Take Profit"
                            
                        # Stop loss (1.5% max loss)
                        elif pnl_pct <= -1.5:
                            should_exit = True
                            exit_reason = "Stop Loss"
                        
                        if should_exit:
                            # Close position
                            trade = TradeResult(
                                symbol=symbol,
                                side=position['side'],
                                entry_price=position['entry_price'],
                                exit_price=current_price,
                                quantity=position['quantity'],
                                entry_time=position['entry_time'].isoformat(),
                                exit_time=current_time.isoformat(),
                                pnl_pct=pnl_pct,
                                pnl_usd=pnl_usd,
                                exit_reason=exit_reason,
                                correlation=position['correlation'],
                                deviation=position['deviation']
                            )
                            
                            trades.append(trade)
                            balance += pnl_usd
                            equity_curve.append(balance)
                            
                            logger.debug(f"{symbol} EXIT: {exit_reason}, P&L: {pnl_pct:.2f}% (${pnl_usd:.2f})")
                            position = None
                            
            except Exception as e:
                logger.error(f"Error in backtest loop for {symbol}: {e}")
                continue
        
        # Calculate performance metrics
        if trades:
            returns = [t.pnl_pct for t in trades]
            winning_trades = [t for t in trades if t.pnl_pct > 0]
            
            total_return_pct = ((balance - self.initial_balance) / self.initial_balance) * 100
            win_rate = (len(winning_trades) / len(trades)) * 100
            
            # Sharpe ratio calculation
            if np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
            else:
                sharpe_ratio = 0
            
            # Maximum drawdown
            equity_series = pd.Series(equity_curve)
            running_max = equity_series.expanding().max()
            drawdown = (equity_series - running_max) / running_max * 100
            max_drawdown = drawdown.min()
            
            # Other metrics
            avg_hold_time = np.mean([(datetime.fromisoformat(t.exit_time) - datetime.fromisoformat(t.entry_time)).total_seconds() / 3600 for t in trades])
            profit_factor = sum([t.pnl_usd for t in winning_trades]) / abs(sum([t.pnl_usd for t in trades if t.pnl_pct < 0])) if any(t.pnl_pct < 0 for t in trades) else float('inf')
            
        else:
            # No trades executed
            total_return_pct = 0
            win_rate = 0
            sharpe_ratio = 0
            max_drawdown = 0
            avg_hold_time = 0
            profit_factor = 0
            returns = [0]
        
        performance = PairPerformance(
            symbol=symbol,
            total_return_pct=total_return_pct,
            total_return_usd=balance - self.initial_balance,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=abs(max_drawdown),
            win_rate_pct=win_rate,
            total_trades=len(trades),
            avg_trade_pnl=np.mean([t.pnl_usd for t in trades]) if trades else 0,
            best_trade_pct=max(returns) if returns else 0,
            worst_trade_pct=min(returns) if returns else 0,
            profit_factor=profit_factor,
            volatility=np.std(returns) if returns else 0,
            avg_hold_time_hours=avg_hold_time,
            trades=trades
        )
        
        logger.info(f"Backtest completed for {symbol}: {total_return_pct:.2f}% return, {len(trades)} trades")
        return performance
    
    async def run_comprehensive_backtest(self) -> Dict[str, PairPerformance]:
        """Run backtest for all pairs"""
        logger.info("Starting comprehensive backtest for all pairs")
        
        if not await self.initialize_exchange():
            raise Exception("Failed to initialize exchange")
        
        results = {}
        
        try:
            for symbol in self.pairs:
                logger.info(f"Processing {symbol} ({self.pairs.index(symbol) + 1}/{len(self.pairs)})")
                
                # Fetch historical data
                data = await self.fetch_historical_data(symbol, self.backtest_days)
                
                if data.empty:
                    logger.warning(f"No data available for {symbol}, skipping")
                    continue
                
                # Run backtest
                performance = await self.run_pair_backtest(symbol, data)
                results[symbol] = performance
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)
            
            logger.info(f"Comprehensive backtest completed for {len(results)} pairs")
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive backtest: {e}")
            raise
        finally:
            if self.exchange:
                await self.exchange.close()
    
    def generate_backtest_report(self, results: Dict[str, PairPerformance]) -> Dict:
        """Generate comprehensive backtest report"""
        if not results:
            return {"error": "No backtest results available"}
        
        # Overall statistics
        total_trades = sum([p.total_trades for p in results.values()])
        avg_return = np.mean([p.total_return_pct for p in results.values()])
        avg_sharpe = np.mean([p.sharpe_ratio for p in results.values()])
        avg_win_rate = np.mean([p.win_rate_pct for p in results.values()])
        avg_drawdown = np.mean([p.max_drawdown_pct for p in results.values()])
        
        # Rank pairs by performance
        sorted_pairs = sorted(results.items(), key=lambda x: x[1].total_return_pct, reverse=True)
        
        report = {
            "backtest_summary": {
                "total_pairs_tested": len(results),
                "total_trades_all_pairs": total_trades,
                "average_return_pct": round(avg_return, 2),
                "average_sharpe_ratio": round(avg_sharpe, 2),
                "average_win_rate_pct": round(avg_win_rate, 2),
                "average_max_drawdown_pct": round(avg_drawdown, 2),
                "backtest_period_days": self.backtest_days,
                "initial_balance_per_pair": self.initial_balance,
                "generated_at": datetime.now().isoformat()
            },
            "pair_rankings": [
                {
                    "rank": i + 1,
                    "symbol": symbol,
                    "total_return_pct": round(perf.total_return_pct, 2),
                    "sharpe_ratio": round(perf.sharpe_ratio, 2),
                    "win_rate_pct": round(perf.win_rate_pct, 2),
                    "total_trades": perf.total_trades,
                    "max_drawdown_pct": round(perf.max_drawdown_pct, 2)
                }
                for i, (symbol, perf) in enumerate(sorted_pairs)
            ],
            "detailed_results": {
                symbol: {
                    "performance_metrics": {
                        "total_return_pct": round(perf.total_return_pct, 2),
                        "total_return_usd": round(perf.total_return_usd, 2),
                        "sharpe_ratio": round(perf.sharpe_ratio, 2),
                        "max_drawdown_pct": round(perf.max_drawdown_pct, 2),
                        "win_rate_pct": round(perf.win_rate_pct, 2),
                        "total_trades": perf.total_trades,
                        "avg_trade_pnl": round(perf.avg_trade_pnl, 2),
                        "best_trade_pct": round(perf.best_trade_pct, 2),
                        "worst_trade_pct": round(perf.worst_trade_pct, 2),
                        "profit_factor": round(perf.profit_factor, 2) if perf.profit_factor != float('inf') else "N/A",
                        "volatility": round(perf.volatility, 2),
                        "avg_hold_time_hours": round(perf.avg_hold_time_hours, 2)
                    },
                    "trade_history": [asdict(trade) for trade in perf.trades]
                }
                for symbol, perf in results.items()
            }
        }
        
        return report

async def main():
    """Main execution function"""
    try:
        engine = ComprehensiveBacktestEngine()
        
        print("=" * 60)
        print("COMPREHENSIVE BACKTESTING ENGINE")
        print("=" * 60)
        print(f"Testing {len(engine.pairs)} pairs over {engine.backtest_days} days")
        print("Pairs:", ", ".join(engine.pairs))
        print()
        
        # Run comprehensive backtest
        results = await engine.run_comprehensive_backtest()
        
        # Generate report
        report = engine.generate_backtest_report(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_backtest_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Backtest completed! Results saved to: {filename}")
        print("\nTOP 5 PERFORMING PAIRS:")
        
        for i, pair_data in enumerate(report['pair_rankings'][:5]):
            print(f"{pair_data['rank']}. {pair_data['symbol']}: {pair_data['total_return_pct']:+.2f}% "
                  f"(Sharpe: {pair_data['sharpe_ratio']:.2f}, Win Rate: {pair_data['win_rate_pct']:.1f}%)")
        
        print(f"\nOverall Average Return: {report['backtest_summary']['average_return_pct']:+.2f}%")
        print(f"Total Trades Executed: {report['backtest_summary']['total_trades_all_pairs']}")
        
        return filename, report
        
    except Exception as e:
        logger.error(f"Backtest execution failed: {e}")
        print(f"ERROR: {e}")
        return None, None

if __name__ == "__main__":
    asyncio.run(main())