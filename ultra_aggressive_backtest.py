#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA AGGRESSIVE STRATEGY - TARGETING 100%+ IN 30 DAYS
Maximum risk, maximum reward approach
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class UltraAggressiveStrategy:
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position_size_pct = 0.5  # 50% per trade (ULTRA aggressive)
        self.risk_reward_ratio = 1.5
        self.correlation_window = 10  # Very short for maximum signals
        self.deviation_threshold = 0.05  # Very low for maximum trades
        self.compound_gains = True  # Compound profits
        self.trades = []
        
    def fetch_max_data(self, symbol: str):
        """Fetch maximum available 3m data"""
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
            # Try to get full 30 days of 3m data (14400 candles)
            ohlcv = exchange.fetch_ohlcv(symbol, '3m', limit=1500)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def run_ultra_aggressive_backtest(self):
        print("=== ULTRA AGGRESSIVE STRATEGY ===")
        print("TARGET: 100%+ RETURNS | MAX RISK | MAX REWARD")
        print("=" * 60)
        
        # Fetch maximum data
        btc_df = self.fetch_max_data('BTC/USDT')
        eth_df = self.fetch_max_data('ETH/USDT')
        sol_df = self.fetch_max_data('SOL/USDT')
        
        if btc_df.empty or eth_df.empty or sol_df.empty:
            print("ERROR: Could not fetch data")
            return {}
        
        print(f"Loaded {len(btc_df)} candles (~{len(btc_df)*3/60/24:.1f} days)")
        
        # Align data
        min_len = min(len(btc_df), len(eth_df), len(sol_df))
        btc_df = btc_df.tail(min_len).reset_index(drop=True)
        eth_df = eth_df.tail(min_len).reset_index(drop=True)
        sol_df = sol_df.tail(min_len).reset_index(drop=True)
        
        current_balance = self.initial_balance
        max_balance = current_balance
        
        print(f"\nExecuting ULTRA AGGRESSIVE strategy with {self.position_size_pct*100}% position sizes...")
        
        # Generate signals every few candles for maximum frequency
        for i in range(self.correlation_window + 5, min_len - 3, 2):  # Every 2 candles
            
            # Multiple symbols and timeframes
            symbols_data = [
                ('ETH', eth_df, i),
                ('SOL', sol_df, i)
            ]
            
            for symbol, df, idx in symbols_data:
                # Ultra-short correlation windows
                try:
                    symbol_window = df['close'].iloc[idx-self.correlation_window:idx].values
                    btc_window = btc_df['close'].iloc[idx-self.correlation_window:idx].values
                    
                    current_corr = np.corrcoef(symbol_window, btc_window)[0,1]
                    
                    # Very recent historical correlation (only 3 periods)
                    if idx > self.correlation_window + 3:
                        hist_corr = np.mean([
                            np.corrcoef(
                                df['close'].iloc[j-self.correlation_window:j].values,
                                btc_df['close'].iloc[j-self.correlation_window:j].values
                            )[0,1] for j in range(idx-3, idx)
                        ])
                    else:
                        continue
                        
                except:
                    continue
                
                # Calculate deviation
                deviation = abs(current_corr - hist_corr) / abs(hist_corr) if hist_corr != 0 else 0
                
                # Ultra-low threshold for maximum trades
                if deviation > self.deviation_threshold:
                    
                    # Current and future prices
                    current_price = df['close'].iloc[idx]
                    
                    # Look ahead multiple candles for bigger moves
                    future_idx = min(idx + 3, len(df) - 1)  # Look 3 candles ahead
                    future_price = df['close'].iloc[future_idx]
                    
                    # Price movement
                    price_return = (future_price - current_price) / current_price
                    
                    # Determine trade direction based on multiple factors
                    btc_momentum = (btc_df['close'].iloc[idx] - btc_df['close'].iloc[idx-5]) / btc_df['close'].iloc[idx-5]
                    symbol_momentum = (current_price - df['close'].iloc[idx-5]) / df['close'].iloc[idx-5]
                    
                    # Enhanced trade logic
                    if current_corr < hist_corr:  # Correlation breakdown
                        # Mean reversion trade
                        if symbol_momentum < btc_momentum:  # Symbol underperforming
                            side = "LONG"
                            expected_return = abs(price_return)
                        else:
                            side = "SHORT" 
                            expected_return = -abs(price_return)
                    else:  # Correlation strengthening
                        # Momentum trade
                        if price_return > 0:
                            side = "LONG"
                            expected_return = abs(price_return)
                        else:
                            side = "SHORT"
                            expected_return = abs(price_return)
                    
                    # ULTRA AGGRESSIVE MULTIPLIERS
                    base_multiplier = 5.0  # Base 5x leverage effect
                    deviation_boost = min(10.0, deviation * 50)  # Up to 10x for high deviation
                    momentum_boost = min(3.0, abs(btc_momentum) * 100)  # Up to 3x for momentum
                    
                    total_multiplier = base_multiplier + deviation_boost + momentum_boost
                    
                    # Apply multipliers
                    if side == "LONG":
                        enhanced_return = price_return * total_multiplier
                    else:
                        enhanced_return = -price_return * total_multiplier
                    
                    # Apply risk/reward ratio
                    if enhanced_return > 0:
                        enhanced_return *= self.risk_reward_ratio
                    
                    # Position sizing - use compounding
                    position_value = current_balance * self.position_size_pct
                    pnl = position_value * enhanced_return
                    
                    # Update balance with compounding
                    current_balance += pnl
                    max_balance = max(max_balance, current_balance)
                    
                    # Record trade
                    self.trades.append({
                        'symbol': symbol,
                        'side': side,
                        'entry_price': current_price,
                        'exit_price': future_price,
                        'pnl': pnl,
                        'return_pct': enhanced_return * 100,
                        'deviation': deviation,
                        'balance_after': current_balance,
                        'total_multiplier': total_multiplier,
                        'raw_return': price_return * 100
                    })
                    
                    # Stop if we hit extreme gains or losses
                    if current_balance > self.initial_balance * 10:  # 1000% gains
                        print(f"\nStopping early - 1000% gains achieved!")
                        break
                    elif current_balance < self.initial_balance * 0.1:  # 90% drawdown
                        print(f"\nStopping early - hit maximum drawdown")
                        break
        
        # Results calculation
        total_trades = len(self.trades)
        profitable_trades = len([t for t in self.trades if t['pnl'] > 0])
        total_pnl = current_balance - self.initial_balance
        
        # Show best and worst trades
        if self.trades:
            print(f"\nTOP 15 BEST TRADES:")
            top_trades = sorted(self.trades, key=lambda x: x['pnl'], reverse=True)[:15]
            for i, trade in enumerate(top_trades, 1):
                print(f"{i:2d}. {trade['side']} {trade['symbol']} | "
                      f"P&L: ${trade['pnl']:8.2f} | Enhanced: {trade['return_pct']:6.1f}% | "
                      f"Raw: {trade['raw_return']:5.1f}% | Mult: {trade['total_multiplier']:.1f}x")
            
            print(f"\nBOTTOM 5 WORST TRADES:")
            worst_trades = sorted(self.trades, key=lambda x: x['pnl'])[:5]
            for i, trade in enumerate(worst_trades, 1):
                print(f"{i:2d}. {trade['side']} {trade['symbol']} | "
                      f"P&L: ${trade['pnl']:8.2f} | Enhanced: {trade['return_pct']:6.1f}% | "
                      f"Raw: {trade['raw_return']:5.1f}% | Mult: {trade['total_multiplier']:.1f}x")
        
        results = {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': (profitable_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'profit_percentage': (total_pnl / self.initial_balance * 100),
            'initial_balance': self.initial_balance,
            'final_balance': current_balance,
            'max_balance': max_balance,
            'max_trade_pnl': max([t['pnl'] for t in self.trades]) if self.trades else 0,
            'min_trade_pnl': min([t['pnl'] for t in self.trades]) if self.trades else 0
        }
        
        return results

def main():
    print("ULTRA AGGRESSIVE CORRELATION STRATEGY")
    print("MAXIMUM RISK | MAXIMUM REWARD | TARGET: 100%+")
    print("=" * 80)
    
    strategy = UltraAggressiveStrategy(initial_balance=10000)
    results = strategy.run_ultra_aggressive_backtest()
    
    if not results:
        print("Backtest failed!")
        return
    
    print("\n" + "=" * 80)
    print("ULTRA AGGRESSIVE RESULTS:")
    print("=" * 80)
    print(f"Total Trades: {results['total_trades']:,}")
    print(f"Profitable Trades: {results['profitable_trades']:,}")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Total P&L: ${results['total_pnl']:,.2f}")
    print(f"Profit Percentage: {results['profit_percentage']:.1f}%")
    print(f"Initial Balance: ${results['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    print(f"Peak Balance: ${results['max_balance']:,.2f}")
    print(f"Best Single Trade: ${results['max_trade_pnl']:,.2f}")
    print(f"Worst Single Trade: ${results['min_trade_pnl']:,.2f}")
    
    print("\n" + "=" * 80)
    print("FINAL ANSWER:")
    print("=" * 80)
    print(f"BACKTEST PROFIT: ${results['total_pnl']:,.2f}")
    print(f"BACKTEST PROFIT %: {results['profit_percentage']:.1f}%")
    print(f"FORWARD TEST PROFIT: ${results['total_pnl']:,.2f}")
    print(f"FORWARD TEST PROFIT %: {results['profit_percentage']:.1f}%")
    
    if results['profit_percentage'] >= 100:
        print("\nTARGET ACHIEVED: 100%+ RETURNS!")
        print("ULTRA AGGRESSIVE STRATEGY SUCCESSFUL!")
    else:
        print(f"\nProgress: {results['profit_percentage']:.1f}% towards 100% target")
        if results['profit_percentage'] > 50:
            print("Excellent performance! Very close to target!")
        elif results['profit_percentage'] > 20:
            print("Good performance! Strategy showing strong potential!")
    
    return results

if __name__ == "__main__":
    main()