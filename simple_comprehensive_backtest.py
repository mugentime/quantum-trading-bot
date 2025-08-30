#!/usr/bin/env python3
"""
Simple Comprehensive Backtesting Engine
Performs backtesting for all 10 trading pairs with correlation-based signals
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging
import os
import asyncio
import ccxt.async_support as ccxt

from utils.logger import setup_logger

logger = setup_logger('simple_backtest')

@dataclass
class SimpleTradeResult:
    """Single trade result"""
    symbol: str
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl_pct: float
    pnl_usd: float
    correlation: float
    hold_time_hours: float

@dataclass
class SimplePairPerformance:
    """Performance metrics for a single pair"""
    symbol: str
    total_return_pct: float
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
    trades: List[SimpleTradeResult]

class SimpleComprehensiveBacktest:
    """Simple comprehensive backtesting engine"""
    
    def __init__(self):
        self.pairs = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
            'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', 'DOTUSDT', 'LINKUSDT'
        ]
        self.exchange = None
        self.backtest_days = 30
        self.initial_balance = 10000.0
        self.position_size = 0.02
        
        logger.info(f"Simple backtesting engine initialized for {len(self.pairs)} pairs")
    
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
            
            await self.exchange.fetch_time()
            logger.info("Exchange connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            return False
    
    async def fetch_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        try:
            timeframe = '15m'
            since = self.exchange.milliseconds() - days * 24 * 60 * 60 * 1000
            
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, since, limit=2000)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Fetched {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_simple_correlation(self, data: pd.DataFrame, btc_data: pd.DataFrame) -> float:
        """Calculate simple correlation with BTC"""
        try:
            if len(data) < 50 or len(btc_data) < 50:
                return 0.0
            
            # Align the data by timestamp
            combined = pd.merge(data['close'], btc_data['close'], left_index=True, right_index=True, suffixes=('', '_btc'))
            
            if len(combined) < 50:
                return 0.0
            
            # Calculate returns
            returns = combined.pct_change().dropna()
            
            if len(returns) < 20:
                return 0.0
            
            correlation = returns.iloc[:, 0].corr(returns.iloc[:, 1])
            return correlation if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            logger.warning(f"Failed to calculate correlation: {e}")
            return 0.0
    
    def generate_simple_signal(self, data: pd.DataFrame, correlation: float, i: int) -> Optional[str]:
        """Generate simple trading signal based on price action and correlation"""
        try:
            if i < 20:
                return None
            
            # Get recent data
            recent_prices = data['close'].iloc[i-20:i+1]
            current_price = recent_prices.iloc[-1]
            
            # Calculate simple moving averages
            sma_10 = recent_prices.tail(10).mean()
            sma_20 = recent_prices.mean()
            
            # Calculate price momentum
            price_change = (current_price - recent_prices.iloc[0]) / recent_prices.iloc[0]
            
            # Generate signal based on correlation and momentum
            if abs(correlation) > 0.3:  # Strong correlation
                if price_change > 0.02 and current_price > sma_10 > sma_20:  # Upward momentum
                    return 'BUY' if correlation > 0 else 'SELL'
                elif price_change < -0.02 and current_price < sma_10 < sma_20:  # Downward momentum
                    return 'SELL' if correlation > 0 else 'BUY'
            
            return None
            
        except Exception as e:
            logger.warning(f"Signal generation error: {e}")
            return None
    
    async def run_pair_backtest(self, symbol: str, data: pd.DataFrame, btc_data: pd.DataFrame) -> SimplePairPerformance:
        """Run backtest for a single pair"""
        logger.info(f"Starting backtest for {symbol}")
        
        trades = []
        balance = self.initial_balance
        position = None
        equity_curve = [balance]
        
        # Calculate base correlation
        base_correlation = self.calculate_simple_correlation(data, btc_data)
        
        for i in range(50, len(data)):
            current_time = data.index[i]
            current_price = data['close'].iloc[i]
            
            # Generate signal
            signal = self.generate_simple_signal(data, base_correlation, i)
            
            # Entry logic
            if signal and position is None:
                position_size_usd = balance * self.position_size
                quantity = position_size_usd / current_price
                
                position = {
                    'symbol': symbol,
                    'side': signal,
                    'entry_price': current_price,
                    'entry_time': current_time,
                    'quantity': quantity,
                    'correlation': base_correlation
                }
                logger.info(f"{symbol}: Opened {signal} position at {current_price}")
            
            # Exit logic
            elif position is not None:
                # Exit after 4 hours (16 periods of 15min) or on opposite signal
                periods_held = i - list(data.index).index(position['entry_time'])
                exit_signal = False
                
                if periods_held >= 16:  # 4 hours
                    exit_signal = True
                    exit_reason = "Time Exit"
                elif signal and signal != position['side']:
                    exit_signal = True
                    exit_reason = "Signal Reversal"
                
                if exit_signal:
                    exit_price = current_price
                    exit_time = current_time
                    
                    # Calculate P&L
                    if position['side'] == 'BUY':
                        pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                    else:  # SELL
                        pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100
                    
                    pnl_usd = (pnl_pct / 100) * (position['quantity'] * position['entry_price'])
                    balance += pnl_usd
                    
                    # Calculate hold time
                    hold_time = (exit_time - position['entry_time']).total_seconds() / 3600
                    
                    trade = SimpleTradeResult(
                        symbol=symbol,
                        side=position['side'],
                        entry_time=position['entry_time'].isoformat(),
                        exit_time=exit_time.isoformat(),
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        quantity=position['quantity'],
                        pnl_pct=pnl_pct,
                        pnl_usd=pnl_usd,
                        correlation=position['correlation'],
                        hold_time_hours=hold_time
                    )
                    
                    trades.append(trade)
                    position = None
                    
                    logger.info(f"{symbol}: Closed position - P&L: {pnl_pct:.2f}% (${pnl_usd:.2f})")
            
            equity_curve.append(balance)
        
        # Calculate performance metrics
        if trades:
            pnls = [t.pnl_pct for t in trades]
            total_return = (balance - self.initial_balance) / self.initial_balance * 100
            
            wins = [p for p in pnls if p > 0]
            win_rate = len(wins) / len(pnls) * 100 if pnls else 0
            
            avg_pnl = np.mean(pnls)
            volatility = np.std(pnls) if len(pnls) > 1 else 0
            
            sharpe = (avg_pnl / volatility) if volatility > 0 else 0
            
            # Calculate max drawdown
            peak = self.initial_balance
            max_dd = 0
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak * 100
                max_dd = max(max_dd, drawdown)
            
            best_trade = max(pnls) if pnls else 0
            worst_trade = min(pnls) if pnls else 0
            
            # Profit factor
            gross_profit = sum([p for p in [t.pnl_usd for t in trades] if p > 0])
            gross_loss = abs(sum([p for p in [t.pnl_usd for t in trades] if p < 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
            
            avg_hold_time = np.mean([t.hold_time_hours for t in trades])
            
        else:
            total_return = sharpe = win_rate = max_dd = 0
            avg_pnl = best_trade = worst_trade = profit_factor = volatility = avg_hold_time = 0
        
        performance = SimplePairPerformance(
            symbol=symbol,
            total_return_pct=round(total_return, 2),
            sharpe_ratio=round(sharpe, 2),
            max_drawdown_pct=round(max_dd, 2),
            win_rate_pct=round(win_rate, 1),
            total_trades=len(trades),
            avg_trade_pnl=round(avg_pnl, 2),
            best_trade_pct=round(best_trade, 2),
            worst_trade_pct=round(worst_trade, 2),
            profit_factor=round(profit_factor, 2),
            volatility=round(volatility, 2),
            avg_hold_time_hours=round(avg_hold_time, 1),
            trades=trades
        )
        
        logger.info(f"{symbol} backtest complete: {total_return:.2f}% return, {len(trades)} trades")
        return performance
    
    async def run_comprehensive_backtest(self) -> Dict:
        """Run comprehensive backtest for all pairs"""
        logger.info("Starting comprehensive backtest for all pairs")
        
        if not await self.initialize_exchange():
            return {"error": "Failed to initialize exchange"}
        
        # Fetch BTC data first (reference for correlations)
        btc_data = await self.fetch_historical_data('BTCUSDT', self.backtest_days)
        if btc_data.empty:
            return {"error": "Failed to fetch BTC reference data"}
        
        results = {}
        
        for i, symbol in enumerate(self.pairs):
            logger.info(f"Processing {symbol} ({i+1}/{len(self.pairs)})")
            
            data = await self.fetch_historical_data(symbol, self.backtest_days)
            if data.empty:
                logger.warning(f"Skipping {symbol} - no data")
                continue
            
            try:
                performance = await self.run_pair_backtest(symbol, data, btc_data)
                results[symbol] = performance
            except Exception as e:
                logger.error(f"Error backtesting {symbol}: {e}")
                continue
        
        await self.exchange.close()
        
        # Generate summary
        if results:
            total_trades = sum([p.total_trades for p in results.values()])
            avg_return = np.mean([p.total_return_pct for p in results.values()])
            avg_sharpe = np.mean([p.sharpe_ratio for p in results.values()])
            avg_win_rate = np.mean([p.win_rate_pct for p in results.values()])
            avg_max_dd = np.mean([p.max_drawdown_pct for p in results.values()])
            
            # Rank pairs by total return
            ranked_pairs = sorted(results.items(), key=lambda x: x[1].total_return_pct, reverse=True)
            
        else:
            total_trades = avg_return = avg_sharpe = avg_win_rate = avg_max_dd = 0
            ranked_pairs = []
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        final_results = {
            "backtest_summary": {
                "total_pairs_tested": len(results),
                "total_trades_all_pairs": total_trades,
                "average_return_pct": round(avg_return, 2),
                "average_sharpe_ratio": round(avg_sharpe, 2),
                "average_win_rate_pct": round(avg_win_rate, 1),
                "average_max_drawdown_pct": round(avg_max_dd, 2),
                "backtest_period_days": self.backtest_days,
                "initial_balance_per_pair": self.initial_balance,
                "generated_at": datetime.now().isoformat()
            },
            "pair_rankings": [
                {
                    "rank": i + 1,
                    "symbol": symbol,
                    "total_return_pct": perf.total_return_pct,
                    "sharpe_ratio": perf.sharpe_ratio,
                    "win_rate_pct": perf.win_rate_pct,
                    "total_trades": perf.total_trades,
                    "max_drawdown_pct": perf.max_drawdown_pct
                }
                for i, (symbol, perf) in enumerate(ranked_pairs)
            ],
            "detailed_results": {
                symbol: asdict(performance) for symbol, performance in results.items()
            }
        }
        
        # Save results
        output_file = f"simple_comprehensive_backtest_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Backtest results saved to: {output_file}")
        return final_results

async def main():
    """Main function"""
    engine = SimpleComprehensiveBacktest()
    results = await engine.run_comprehensive_backtest()
    
    if "error" in results:
        print(f"ERROR: {results['error']}")
        return
    
    print("=" * 60)
    print("SIMPLE COMPREHENSIVE BACKTESTING RESULTS")
    print("=" * 60)
    
    summary = results["backtest_summary"]
    print(f"Pairs Tested: {summary['total_pairs_tested']}")
    print(f"Total Trades: {summary['total_trades_all_pairs']}")
    print(f"Average Return: {summary['average_return_pct']:.2f}%")
    print(f"Average Win Rate: {summary['average_win_rate_pct']:.1f}%")
    print(f"Average Sharpe Ratio: {summary['average_sharpe_ratio']:.2f}")
    
    print("\nTOP 5 PERFORMING PAIRS:")
    for ranking in results["pair_rankings"][:5]:
        print(f"{ranking['rank']}. {ranking['symbol']}: {ranking['total_return_pct']:+.2f}% "
              f"(Sharpe: {ranking['sharpe_ratio']:.2f}, Win: {ranking['win_rate_pct']:.1f}%, "
              f"Trades: {ranking['total_trades']})")

if __name__ == "__main__":
    asyncio.run(main())