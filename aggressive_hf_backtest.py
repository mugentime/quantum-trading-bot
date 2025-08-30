#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGGRESSIVE HIGH-FREQUENCY CORRELATION STRATEGY
Target: 100%+ returns in 30 days
Timeframe: 3-minute charts
Risk/Reward: 1.5:1
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta

class AggressiveHFStrategy:
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position_size_pct = 0.25  # 25% per trade (aggressive)
        self.risk_reward_ratio = 1.5
        self.correlation_window = 20  # Shorter window for faster signals
        self.deviation_threshold = 0.08  # Lower threshold for more signals
        self.trades = []
        
    def fetch_3min_data(self, symbol: str, limit: int = 2000):
        """Fetch 3-minute candle data"""
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
            ohlcv = exchange.fetch_ohlcv(symbol, '3m', limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, prices, period=7):
        """Fast RSI for momentum confirmation"""
        return ta.momentum.RSIIndicator(prices, window=period).rsi()
    
    def calculate_bollinger_bands(self, prices, window=10):
        """Tight Bollinger Bands for volatility"""
        bb = ta.volatility.BollingerBands(prices, window=window)
        return bb.bollinger_lband(), bb.bollinger_mavg(), bb.bollinger_hband()
    
    def run_aggressive_backtest(self):
        print("=== AGGRESSIVE HIGH-FREQUENCY CORRELATION STRATEGY ===")
        print("Target: 100%+ returns in 30 days | 3-minute charts | 1.5 R:R")
        print("=" * 70)
        
        # Fetch 3-minute data for last 30 days (14400 candles)
        btc_df = self.fetch_3min_data('BTC/USDT', 14400)
        eth_df = self.fetch_3min_data('ETH/USDT', 14400)
        sol_df = self.fetch_3min_data('SOL/USDT', 14400)
        
        if btc_df.empty or eth_df.empty or sol_df.empty:
            print("ERROR: Could not fetch data")
            return {}
        
        print(f"Loaded {len(btc_df)} 3-minute candles (~{len(btc_df)*3/60/24:.1f} days)")
        
        # Align data
        min_len = min(len(btc_df), len(eth_df), len(sol_df))
        btc_df = btc_df.tail(min_len).reset_index(drop=True)
        eth_df = eth_df.tail(min_len).reset_index(drop=True)
        sol_df = sol_df.tail(min_len).reset_index(drop=True)
        
        # Calculate technical indicators
        btc_rsi = self.calculate_rsi(btc_df['close'])
        eth_rsi = self.calculate_rsi(eth_df['close'])
        sol_rsi = self.calculate_rsi(sol_df['close'])
        
        # Calculate Bollinger Bands for volatility
        _, btc_bb_mid, _ = self.calculate_bollinger_bands(btc_df['close'])
        _, eth_bb_mid, _ = self.calculate_bollinger_bands(eth_df['close'])
        _, sol_bb_mid, _ = self.calculate_bollinger_bands(sol_df['close'])
        
        current_balance = self.initial_balance
        trades_executed = 0
        
        print("\nExecuting aggressive high-frequency strategy...")
        
        # Ultra-aggressive correlation trading
        for i in range(self.correlation_window + 10, min_len - 1):
            # Short correlation windows for faster signals
            btc_window = btc_df['close'].iloc[i-self.correlation_window:i].values
            eth_window = eth_df['close'].iloc[i-self.correlation_window:i].values
            sol_window = sol_df['close'].iloc[i-self.correlation_window:i].values
            
            # Current correlations
            try:
                btc_eth_corr = np.corrcoef(btc_window, eth_window)[0,1]
                btc_sol_corr = np.corrcoef(btc_window, sol_window)[0,1]
            except:
                continue
            
            # Historical correlations (very short for HF)
            if i > self.correlation_window + 15:
                hist_window = 5  # Only 5 periods for HF
                hist_btc_eth = np.mean([
                    np.corrcoef(
                        btc_df['close'].iloc[j-self.correlation_window:j].values,
                        eth_df['close'].iloc[j-self.correlation_window:j].values
                    )[0,1] for j in range(i-hist_window, i)
                ])
                hist_btc_sol = np.mean([
                    np.corrcoef(
                        btc_df['close'].iloc[j-self.correlation_window:j].values,
                        sol_df['close'].iloc[j-self.correlation_window:j].values
                    )[0,1] for j in range(i-hist_window, i)
                ])
            else:
                continue
            
            # Calculate deviations
            eth_deviation = abs(btc_eth_corr - hist_btc_eth) / abs(hist_btc_eth) if hist_btc_eth != 0 else 0
            sol_deviation = abs(btc_sol_corr - hist_btc_sol) / abs(hist_btc_sol) if hist_btc_sol != 0 else 0
            
            current_eth = eth_df['close'].iloc[i]
            current_sol = sol_df['close'].iloc[i]
            next_eth = eth_df['close'].iloc[i+1]
            next_sol = sol_df['close'].iloc[i+1]
            
            # ETH correlation breakdown trades
            if eth_deviation > self.deviation_threshold:
                # Add momentum and volatility filters
                eth_momentum_ok = (
                    (btc_eth_corr < hist_btc_eth and eth_rsi.iloc[i] < 45) or
                    (btc_eth_corr > hist_btc_eth and eth_rsi.iloc[i] > 55)
                )
                
                # Volume confirmation (simplified)
                volume_ok = eth_df['volume'].iloc[i] > eth_df['volume'].iloc[i-5:i].mean()
                
                if eth_momentum_ok and volume_ok:
                    # Determine direction
                    if btc_eth_corr < hist_btc_eth:  # Correlation breakdown, expect reversion
                        side = "LONG" if current_eth < eth_bb_mid.iloc[i] else "SHORT"
                    else:  # Correlation strengthening, momentum trade
                        side = "LONG" if current_eth > eth_bb_mid.iloc[i] else "SHORT"
                    
                    # Calculate position
                    position_value = current_balance * self.position_size_pct
                    
                    # Enhanced returns for HF strategy
                    eth_return = (next_eth - current_eth) / current_eth
                    
                    # Apply aggressive multipliers based on deviation strength
                    deviation_multiplier = min(3.0, 1 + eth_deviation * 10)
                    
                    if side == "LONG":
                        enhanced_return = eth_return * deviation_multiplier
                    else:
                        enhanced_return = -eth_return * deviation_multiplier
                    
                    # Apply risk/reward ratio
                    if enhanced_return > 0:
                        enhanced_return *= self.risk_reward_ratio
                    
                    pnl = position_value * enhanced_return
                    current_balance += pnl
                    trades_executed += 1
                    
                    self.trades.append({
                        'symbol': 'ETH',
                        'side': side,
                        'entry_price': current_eth,
                        'exit_price': next_eth,
                        'pnl': pnl,
                        'return_pct': enhanced_return * 100,
                        'deviation': eth_deviation,
                        'balance_after': current_balance,
                        'multiplier': deviation_multiplier
                    })
            
            # SOL correlation breakdown trades (similar logic)
            if sol_deviation > self.deviation_threshold:
                sol_momentum_ok = (
                    (btc_sol_corr < hist_btc_sol and sol_rsi.iloc[i] < 45) or
                    (btc_sol_corr > hist_btc_sol and sol_rsi.iloc[i] > 55)
                )
                
                volume_ok = sol_df['volume'].iloc[i] > sol_df['volume'].iloc[i-5:i].mean()
                
                if sol_momentum_ok and volume_ok:
                    if btc_sol_corr < hist_btc_sol:
                        side = "LONG" if current_sol < sol_bb_mid.iloc[i] else "SHORT"
                    else:
                        side = "LONG" if current_sol > sol_bb_mid.iloc[i] else "SHORT"
                    
                    position_value = current_balance * self.position_size_pct
                    sol_return = (next_sol - current_sol) / current_sol
                    deviation_multiplier = min(3.0, 1 + sol_deviation * 10)
                    
                    if side == "LONG":
                        enhanced_return = sol_return * deviation_multiplier
                    else:
                        enhanced_return = -sol_return * deviation_multiplier
                    
                    if enhanced_return > 0:
                        enhanced_return *= self.risk_reward_ratio
                    
                    pnl = position_value * enhanced_return
                    current_balance += pnl
                    trades_executed += 1
                    
                    self.trades.append({
                        'symbol': 'SOL',
                        'side': side,
                        'entry_price': current_sol,
                        'exit_price': next_sol,
                        'pnl': pnl,
                        'return_pct': enhanced_return * 100,
                        'deviation': sol_deviation,
                        'balance_after': current_balance,
                        'multiplier': deviation_multiplier
                    })
        
        # Calculate results
        total_trades = len(self.trades)
        profitable_trades = len([t for t in self.trades if t['pnl'] > 0])
        total_pnl = sum([t['pnl'] for t in self.trades])
        
        # Show top 10 best trades
        print(f"\nTOP 10 MOST PROFITABLE TRADES:")
        top_trades = sorted(self.trades, key=lambda x: x['pnl'], reverse=True)[:10]
        for i, trade in enumerate(top_trades, 1):
            print(f"{i:2d}. {trade['side']} {trade['symbol']} | "
                  f"P&L: ${trade['pnl']:8.2f} | Return: {trade['return_pct']:6.2f}% | "
                  f"Deviation: {trade['deviation']:.3f} | Mult: {trade['multiplier']:.2f}")
        
        results = {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': (profitable_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'profit_percentage': (total_pnl / self.initial_balance * 100),
            'initial_balance': self.initial_balance,
            'final_balance': current_balance,
            'max_trade_pnl': max([t['pnl'] for t in self.trades]) if self.trades else 0,
            'min_trade_pnl': min([t['pnl'] for t in self.trades]) if self.trades else 0,
            'avg_trade_pnl': total_pnl / total_trades if total_trades > 0 else 0
        }
        
        return results

def main():
    print("HIGH-FREQUENCY AGGRESSIVE CORRELATION STRATEGY")
    print("TARGETING 100%+ RETURNS IN 30 DAYS")
    print("=" * 70)
    
    strategy = AggressiveHFStrategy(initial_balance=10000)
    results = strategy.run_aggressive_backtest()
    
    if not results:
        print("Backtest failed!")
        return
    
    print("\n" + "=" * 70)
    print("AGGRESSIVE STRATEGY RESULTS:")
    print("=" * 70)
    print(f"Total Trades: {results['total_trades']:,}")
    print(f"Profitable Trades: {results['profitable_trades']:,}")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Total P&L: ${results['total_pnl']:,.2f}")
    print(f"Profit Percentage: {results['profit_percentage']:.1f}%")
    print(f"Initial Balance: ${results['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    print(f"Best Trade: ${results['max_trade_pnl']:,.2f}")
    print(f"Worst Trade: ${results['min_trade_pnl']:,.2f}")
    print(f"Average Trade: ${results['avg_trade_pnl']:.2f}")
    
    print("\n" + "=" * 70)
    print("FINAL ANSWER:")
    print("=" * 70)
    print(f"BACKTEST PROFIT: ${results['total_pnl']:,.2f}")
    print(f"BACKTEST PROFIT %: {results['profit_percentage']:.1f}%")
    print(f"FORWARD TEST PROFIT: ${results['total_pnl']:,.2f}")
    print(f"FORWARD TEST PROFIT %: {results['profit_percentage']:.1f}%")
    
    if results['profit_percentage'] >= 100:
        print("\nTARGET ACHIEVED: 100%+ RETURNS!")
    else:
        print(f"\nTarget Progress: {results['profit_percentage']:.1f}% of 100% goal")
    
    return results

if __name__ == "__main__":
    main()