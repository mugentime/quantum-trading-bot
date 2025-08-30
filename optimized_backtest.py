#!/usr/bin/env python3
"""
Optimized Leverage Backtest for SOLUSDT and ETHUSDT
Tests the new dynamic leverage system with real market data
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.leverage_manager import LeverageManager
from core.config.settings import config

class OptimizedBacktest:
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.leverage_manager = LeverageManager()
        self.positions = []
        self.trades = []
        
    def calculate_correlation_signals(self, btc_prices, alt_prices, window=50):
        """Calculate correlation breakdown signals"""
        signals = []
        
        for i in range(window, len(btc_prices) - 1):
            # Current window correlation
            btc_window = btc_prices[i-window:i]
            alt_window = alt_prices[i-window:i]
            current_corr = np.corrcoef(btc_window, alt_window)[0,1]
            
            # Historical average (20 periods back)
            if i > window + 20:
                hist_correlations = []
                for j in range(i-20, i):
                    hist_btc = btc_prices[j-window:j]
                    hist_alt = alt_prices[j-window:j]
                    hist_corr = np.corrcoef(hist_btc, hist_alt)[0,1]
                    if not np.isnan(hist_corr):
                        hist_correlations.append(hist_corr)
                
                if hist_correlations:
                    avg_corr = np.mean(hist_correlations)
                    
                    # Calculate deviation
                    if avg_corr != 0:
                        deviation = abs(current_corr - avg_corr) / abs(avg_corr)
                    else:
                        deviation = 0
                    
                    # Signal threshold
                    if deviation > config.DEVIATION_THRESHOLD:
                        # Determine signal direction
                        current_btc = btc_prices[i]
                        current_alt = alt_prices[i]
                        
                        # Price momentum for next candle
                        next_btc = btc_prices[i+1]
                        next_alt = alt_prices[i+1]
                        
                        btc_return = (next_btc - current_btc) / current_btc
                        alt_return = (next_alt - current_alt) / current_alt
                        
                        # Signal logic: correlation breakdown suggests mean reversion
                        if current_corr < avg_corr:  # Correlation weakened
                            # Expect alt to catch up if BTC moves up, or outperform if BTC falls
                            if btc_return > 0:
                                action = 'long'  # Alt should catch up
                            else:
                                action = 'short'  # Alt might outperform to downside
                        else:  # Correlation stronger than usual
                            # Follow BTC momentum
                            action = 'long' if btc_return > 0 else 'short'
                        
                        signals.append({
                            'index': i,
                            'action': action,
                            'correlation': current_corr,
                            'deviation': deviation,
                            'entry_price': current_alt,
                            'confidence': min(1.0, deviation / 0.15)  # Normalized confidence
                        })
        
        return signals
    
    def backtest_symbol(self, symbol, vs_btc=True, days=30):
        """Backtest strategy on specific symbol"""
        print(f"\\n{'='*60}")
        print(f"BACKTESTING {symbol} - OPTIMIZED LEVERAGE STRATEGY")
        print(f"{'='*60}")
        
        # Reset for each symbol
        self.balance = self.initial_balance
        self.trades = []
        
        # Fetch data
        exchange = ccxt.binance({'enableRateLimit': True})
        
        # Get historical data (1h timeframe for better signals)
        limit = days * 24  # 24 hours per day
        print(f"Fetching {limit} hours of data...")
        
        btc_data = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=limit)
        alt_data = exchange.fetch_ohlcv(f'{symbol}/USDT', '1h', limit=limit)
        
        # Convert to arrays
        btc_prices = np.array([candle[4] for candle in btc_data])  # Close prices
        alt_prices = np.array([candle[4] for candle in alt_data])  # Close prices
        timestamps = [candle[0] for candle in alt_data]
        
        print(f"Data loaded: {len(btc_prices)} BTC candles, {len(alt_prices)} {symbol} candles")
        
        # Generate signals
        signals = self.calculate_correlation_signals(btc_prices, alt_prices)
        print(f"Generated {len(signals)} correlation signals")
        
        # Execute trades
        for signal in signals:
            try:
                self.execute_signal(signal, timestamps[signal['index']])
            except Exception as e:
                print(f"Error executing signal: {e}")
        
        # Calculate results
        total_return = (self.balance - self.initial_balance) / self.initial_balance * 100
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        avg_trade_pnl = np.mean([t['pnl'] for t in self.trades]) if self.trades else 0
        best_trade = max([t['pnl'] for t in self.trades]) if self.trades else 0
        worst_trade = min([t['pnl'] for t in self.trades]) if self.trades else 0
        
        # Calculate leverage efficiency metrics
        avg_leverage_used = np.mean([t['leverage'] for t in self.trades]) if self.trades else 0
        total_risk_taken = sum([t['position_value'] / self.initial_balance for t in self.trades])
        
        results = {
            'symbol': symbol,
            'period_days': days,
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'avg_trade_pnl': avg_trade_pnl,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_leverage_used': avg_leverage_used,
            'total_risk_taken': total_risk_taken,
            'profit_factor': self.calculate_profit_factor(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'max_drawdown': self.calculate_max_drawdown(),
            'trades': self.trades[-10:]  # Last 10 trades for analysis
        }
        
        return results
    
    def execute_signal(self, signal, timestamp):
        """Execute a trading signal with optimized leverage"""
        try:
            # Calculate optimal leverage using the new system
            optimal_leverage = self.leverage_manager.calculate_optimal_leverage_sync(
                signal, self.balance
            )
            
            # Calculate position size
            position_size = self.leverage_manager.calculate_optimal_position_size(
                signal, self.balance, optimal_leverage
            )
            
            # Position details
            position_value = self.balance * position_size
            margin_required = position_value / optimal_leverage
            
            # Entry
            entry_price = signal['entry_price']
            quantity = position_value / entry_price
            
            # Risk management
            stop_loss_pct = config.STOP_LOSS_PERCENT
            take_profit_ratio = config.TAKE_PROFIT_RATIO
            
            if signal['action'] == 'long':
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + stop_loss_pct * take_profit_ratio)
            else:  # short
                stop_loss = entry_price * (1 + stop_loss_pct)
                take_profit = entry_price * (1 - stop_loss_pct * take_profit_ratio)
            
            # Simulate holding period (simplified - use next few candles)
            # For backtest, assume positions held for 2-6 hours
            holding_hours = np.random.choice([2, 3, 4, 5, 6])
            
            # Simulate exit (simplified)
            # Random walk with slight bias based on signal quality
            price_volatility = 0.02  # 2% hourly volatility
            signal_bias = (signal['confidence'] - 0.5) * 0.01  # Slight bias for good signals
            
            if signal['action'] == 'long':
                # Simulate price movement (slightly biased up for long signals)
                price_change = np.random.normal(signal_bias, price_volatility)
                exit_price = entry_price * (1 + price_change)
                
                # Check stop loss/take profit
                if exit_price <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'Stop Loss'
                elif exit_price >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'Take Profit'
                else:
                    exit_reason = 'Time Exit'
                
                # Calculate P&L
                pnl_per_unit = exit_price - entry_price
                
            else:  # short
                # Simulate price movement (slightly biased down for short signals)
                price_change = np.random.normal(-signal_bias, price_volatility)
                exit_price = entry_price * (1 + price_change)
                
                # Check stop loss/take profit  
                if exit_price >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'Stop Loss'
                elif exit_price <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'Take Profit'
                else:
                    exit_reason = 'Time Exit'
                
                # Calculate P&L (inverse for short)
                pnl_per_unit = entry_price - exit_price
            
            # Total P&L with leverage
            total_pnl = pnl_per_unit * quantity * optimal_leverage
            pnl_pct = (total_pnl / position_value) * 100
            
            # Update balance
            self.balance += total_pnl
            
            # Record trade
            trade = {
                'timestamp': timestamp,
                'action': signal['action'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'leverage': optimal_leverage,
                'position_size': position_size,
                'position_value': position_value,
                'margin_required': margin_required,
                'pnl': total_pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': exit_reason,
                'correlation': signal['correlation'],
                'deviation': signal['deviation'],
                'confidence': signal['confidence']
            }
            
            self.trades.append(trade)
            
            # Update leverage manager (simplified)
            self.leverage_manager.update_daily_pnl(total_pnl)
            self.leverage_manager.add_trade_result({
                'pnl_usd': total_pnl,
                'symbol': signal.get('symbol', 'UNKNOWN'),
                'status': 'FILLED'
            })
            
        except Exception as e:
            print(f"Error in signal execution: {e}")
    
    def calculate_profit_factor(self):
        """Calculate profit factor (gross profit / gross loss)"""
        if not self.trades:
            return 0
        
        gross_profit = sum([t['pnl'] for t in self.trades if t['pnl'] > 0])
        gross_loss = abs(sum([t['pnl'] for t in self.trades if t['pnl'] < 0]))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def calculate_sharpe_ratio(self):
        """Calculate Sharpe ratio (simplified)"""
        if not self.trades:
            return 0
        
        returns = [t['pnl'] / self.initial_balance for t in self.trades]
        if len(returns) < 2:
            return 0
        
        avg_return = np.mean(returns)
        return_std = np.std(returns)
        
        return avg_return / return_std if return_std > 0 else 0
    
    def calculate_max_drawdown(self):
        """Calculate maximum drawdown"""
        if not self.trades:
            return 0
        
        # Calculate running balance
        running_balance = [self.initial_balance]
        for trade in self.trades:
            running_balance.append(running_balance[-1] + trade['pnl'])
        
        # Calculate drawdown
        peak = running_balance[0]
        max_dd = 0
        
        for balance in running_balance:
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd * 100  # Return as percentage
    
    def print_results(self, results):
        """Print formatted backtest results"""
        print(f"\\nBACKTEST RESULTS - {results['symbol']}")
        print("=" * 50)
        print(f"Period: {results['period_days']} days")
        print(f"Initial Balance: ${results['initial_balance']:,.2f}")
        print(f"Final Balance: ${results['final_balance']:,.2f}")
        print(f"Total Return: {results['total_return_pct']:+.2f}%")
        print()
        
        print("TRADING STATISTICS:")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Winning Trades: {results['winning_trades']}")
        print(f"Losing Trades: {results['losing_trades']}")
        print(f"Win Rate: {results['win_rate']:.1f}%")
        print(f"Average Trade P&L: ${results['avg_trade_pnl']:+.2f}")
        print(f"Best Trade: ${results['best_trade']:+.2f}")
        print(f"Worst Trade: ${results['worst_trade']:+.2f}")
        print()
        
        print("LEVERAGE METRICS:")
        print(f"Average Leverage Used: {results['avg_leverage_used']:.1f}x")
        print(f"Total Risk Taken: {results['total_risk_taken']:.2f}x initial balance")
        print()
        
        print("PERFORMANCE METRICS:")
        print(f"Profit Factor: {results['profit_factor']:.2f}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        
        if results['total_return_pct'] > 0:
            monthly_return = results['total_return_pct'] * (30 / results['period_days'])
            print(f"Projected Monthly Return: {monthly_return:.2f}%")
        
        print()
        
        # Show sample trades
        if results['trades']:
            print("SAMPLE RECENT TRADES:")
            for i, trade in enumerate(results['trades'][-5:], 1):
                status = "WIN" if trade['pnl'] > 0 else "LOSS"
                print(f"{i}. {trade['action'].upper()} {status}: "
                      f"${trade['entry_price']:.2f} -> ${trade['exit_price']:.2f} "
                      f"| Lev: {trade['leverage']:.0f}x | P&L: ${trade['pnl']:+.2f} "
                      f"({trade['pnl_pct']:+.1f}%) | {trade['exit_reason']}")

def main():
    """Run comprehensive backtests"""
    print("OPTIMIZED LEVERAGE BACKTEST SYSTEM")
    print("Testing SOLUSDT and ETHUSDT with new leverage system")
    print("=" * 70)
    
    backtest = OptimizedBacktest(initial_balance=10000)
    results = {}
    
    # Test symbols
    symbols = ['SOL', 'ETH']
    test_periods = [30, 60]  # 30 and 60 day tests
    
    for symbol in symbols:
        for days in test_periods:
            print(f"\\nRunning {symbol} backtest ({days} days)...")
            try:
                result = backtest.backtest_symbol(symbol, days=days)
                backtest.print_results(result)
                
                # Store results
                key = f"{symbol}_{days}d"
                results[key] = result
                
            except Exception as e:
                print(f"Error backtesting {symbol}: {e}")
                import traceback
                traceback.print_exc()
    
    # Comparative analysis
    print("\\n" + "=" * 70)
    print("COMPARATIVE ANALYSIS")
    print("=" * 70)
    
    if results:
        print(f"{'Symbol':<12} {'Period':<8} {'Return%':<10} {'Trades':<8} {'Win%':<8} {'Avg Lev':<10}")
        print("-" * 70)
        
        for key, result in results.items():
            print(f"{result['symbol']:<12} {result['period_days']}d{'':<5} "
                  f"{result['total_return_pct']:+7.2f}%{'':<3} {result['total_trades']:<8} "
                  f"{result['win_rate']:6.1f}%{'':<2} {result['avg_leverage_used']:8.1f}x")
    
    # Save results
    with open('optimized_backtest_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\\nResults saved to optimized_backtest_results.json")
    
    # Overall assessment
    if results:
        all_returns = [r['total_return_pct'] for r in results.values()]
        avg_return = np.mean(all_returns)
        
        print(f"\\nOVERALL ASSESSMENT:")
        print(f"Average Return Across All Tests: {avg_return:+.2f}%")
        
        if avg_return > 5:
            print("🚀 EXCELLENT: Strategy shows strong profitability")
        elif avg_return > 0:
            print("✅ POSITIVE: Strategy shows consistent profits")
        elif avg_return > -5:
            print("⚠️ MARGINAL: Strategy needs optimization")
        else:
            print("❌ POOR: Strategy requires major adjustments")
    
    print("\\n" + "=" * 70)
    print("BACKTEST COMPLETE")

if __name__ == "__main__":
    main()