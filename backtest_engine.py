#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Backtesting Engine for Quantum Trading Bot
Matches Pine Script strategy logic exactly
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import asyncio
from typing import Dict, List, Tuple
import json

class BacktestEngine:
    """Backtest engine that replicates Pine Script strategy"""
    
    def __init__(self, initial_balance=10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []
        self.trades = []
        self.correlation_period = 50
        self.deviation_threshold = 0.15
        self.risk_reward_ratio = 2.0
        self.max_position_time = 600  # seconds
        
    def fetch_historical_data(self, symbol: str, timeframe: str, days: int = 90) -> pd.DataFrame:
        """Fetch historical data for backtesting"""
        try:
            exchange = ccxt.binance({'enableRateLimit': True})
            
            # Calculate the timestamp for days ago
            since = exchange.milliseconds() - days * 24 * 60 * 60 * 1000
            
            # Fetch OHLCV data
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_correlation(self, prices1: pd.Series, prices2: pd.Series, period: int) -> pd.Series:
        """Calculate rolling correlation like Pine Script ta.correlation"""
        return prices1.rolling(window=period).corr(prices2)
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate simple moving average"""
        return prices.rolling(window=period).mean()
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def run_backtest(self, start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> Dict:
        """Run comprehensive backtest matching Pine Script logic"""
        
        print(f"=== Running Backtest: {start_date} to {end_date} ===")
        
        # Fetch data for main symbols
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        timeframe = '1h'  # Use 1h timeframe for backtesting
        
        data = {}
        for symbol in symbols:
            print(f"Fetching data for {symbol}...")
            df = self.fetch_historical_data(symbol, timeframe, 365)  # Get full year
            if not df.empty:
                data[symbol] = df
                print(f"  Loaded {len(df)} candles")
        
        if not data:
            print("ERROR: No data fetched")
            return {}
        
        # Use the symbol with most data as primary
        primary_symbol = max(data.keys(), key=lambda x: len(data[x]))
        primary_data = data[primary_symbol]
        
        print(f"Primary symbol: {primary_symbol} ({len(primary_data)} candles)")
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        primary_data = primary_data[(primary_data.index >= start_dt) & (primary_data.index <= end_dt)]
        
        if len(primary_data) < self.correlation_period:
            print(f"ERROR: Not enough data for correlation period ({len(primary_data)} < {self.correlation_period})")
            return {}
        
        print(f"Backtesting {len(primary_data)} candles from {primary_data.index[0]} to {primary_data.index[-1]}")
        
        # Get BTC data for correlation
        btc_data = data['BTCUSDT']
        btc_data = btc_data[(btc_data.index >= start_dt) & (btc_data.index <= end_dt)]
        
        # Align data
        common_index = primary_data.index.intersection(btc_data.index)
        primary_data = primary_data.loc[common_index]
        btc_data = btc_data.loc[common_index]
        
        # Calculate correlations (Pine Script logic)
        current_corr = self.calculate_correlation(primary_data['close'], btc_data['close'], self.correlation_period)
        historical_corr_avg = current_corr.rolling(window=self.correlation_period).mean()
        
        # Calculate deviation (Pine Script logic)
        corr_deviation = abs(current_corr - historical_corr_avg) / abs(historical_corr_avg)
        
        # Calculate technical indicators
        sma_5 = self.calculate_sma(primary_data['close'], 5)
        atr = self.calculate_atr(primary_data['high'], primary_data['low'], primary_data['close'])
        
        # Generate signals (Pine Script logic)
        long_signals = (
            (corr_deviation > self.deviation_threshold) &
            (current_corr < historical_corr_avg) &
            (primary_data['close'] > sma_5) &
            (primary_data['close'].shift(1) <= sma_5.shift(1))  # Crossover
        )
        
        short_signals = (
            (corr_deviation > self.deviation_threshold) &
            (current_corr > historical_corr_avg) &
            (primary_data['close'] < sma_5) &
            (primary_data['close'].shift(1) >= sma_5.shift(1))  # Crossunder
        )
        
        # Execute trades
        position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        entry_time = None
        
        total_trades = 0
        winning_trades = 0
        total_pnl = 0
        
        for i, (timestamp, row) in enumerate(primary_data.iterrows()):
            current_price = row['close']
            current_atr = atr.iloc[i] if i < len(atr) else 0
            
            # Check for new signals
            if position == 0:  # No position
                if i < len(long_signals) and long_signals.iloc[i] and not pd.isna(current_atr):
                    # Enter long position
                    position = 1
                    entry_price = current_price
                    entry_time = timestamp
                    print(f"LONG ENTRY at {timestamp}: ${current_price:.2f}")
                    
                elif i < len(short_signals) and short_signals.iloc[i] and not pd.isna(current_atr):
                    # Enter short position
                    position = -1
                    entry_price = current_price
                    entry_time = timestamp
                    print(f"SHORT ENTRY at {timestamp}: ${current_price:.2f}")
            
            else:  # Has position
                # Calculate time in position
                time_in_position = (timestamp - entry_time).total_seconds() if entry_time else 0
                
                # Calculate P&L
                if position == 1:  # Long position
                    pnl = current_price - entry_price
                    profit_target = entry_price + (current_atr * self.risk_reward_ratio)
                    stop_loss = entry_price - current_atr
                    
                    # Exit conditions
                    if (current_price >= profit_target or 
                        current_price <= stop_loss or 
                        time_in_position > self.max_position_time):
                        
                        total_trades += 1
                        if pnl > 0:
                            winning_trades += 1
                        total_pnl += pnl
                        
                        exit_reason = "TP" if current_price >= profit_target else "SL" if current_price <= stop_loss else "TIME"
                        print(f"LONG EXIT at {timestamp}: ${current_price:.2f} | P&L: ${pnl:.2f} | Reason: {exit_reason}")
                        
                        self.trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'side': 'LONG',
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'pnl': pnl,
                            'exit_reason': exit_reason
                        })
                        
                        position = 0
                        
                elif position == -1:  # Short position
                    pnl = entry_price - current_price
                    profit_target = entry_price - (current_atr * self.risk_reward_ratio)
                    stop_loss = entry_price + current_atr
                    
                    # Exit conditions
                    if (current_price <= profit_target or 
                        current_price >= stop_loss or 
                        time_in_position > self.max_position_time):
                        
                        total_trades += 1
                        if pnl > 0:
                            winning_trades += 1
                        total_pnl += pnl
                        
                        exit_reason = "TP" if current_price <= profit_target else "SL" if current_price >= stop_loss else "TIME"
                        print(f"SHORT EXIT at {timestamp}: ${current_price:.2f} | P&L: ${pnl:.2f} | Reason: {exit_reason}")
                        
                        self.trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'side': 'SHORT',
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'pnl': pnl,
                            'exit_reason': exit_reason
                        })
                        
                        position = 0
        
        # Calculate performance metrics
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        profit_percentage = (total_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0
        final_balance = self.initial_balance + total_pnl
        
        results = {
            'period': f"{start_date} to {end_date}",
            'symbol': primary_symbol,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'profit_percentage': profit_percentage,
            'initial_balance': self.initial_balance,
            'final_balance': final_balance,
            'correlation_signals': sum(long_signals) + sum(short_signals),
            'trades': self.trades
        }
        
        return results

def run_forward_test(days: int = 30) -> Dict:
    """Run forward test on recent data"""
    print(f"=== Running Forward Test (Last {days} days) ===")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    backtest = BacktestEngine(initial_balance=10000)
    results = backtest.run_backtest(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    return results

def main():
    """Run both backtesting and forward testing"""
    print("=" * 60)
    print("QUANTUM TRADING BOT - COMPREHENSIVE TESTING")
    print("=" * 60)
    
    # 1. Historical Backtest (2024 full year)
    print("\n1. HISTORICAL BACKTESTING")
    backtest = BacktestEngine(initial_balance=10000)
    backtest_results = backtest.run_backtest("2024-01-01", "2024-12-31")
    
    # 2. Forward Test (last 30 days)
    print("\n2. FORWARD TESTING")
    forward_results = run_forward_test(30)
    
    # 3. Save results
    with open('backtest_results/backtest_2024.json', 'w') as f:
        json.dump(backtest_results, f, indent=2, default=str)
    
    with open('forward_test_results/forward_test.json', 'w') as f:
        json.dump(forward_results, f, indent=2, default=str)
    
    # 4. Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    if backtest_results:
        print(f"\nBACKTEST (2024):")
        print(f"  Total Trades: {backtest_results['total_trades']}")
        print(f"  Win Rate: {backtest_results['win_rate']:.2f}%")
        print(f"  Total P&L: ${backtest_results['total_pnl']:.2f}")
        print(f"  Profit %: {backtest_results['profit_percentage']:.2f}%")
        print(f"  Final Balance: ${backtest_results['final_balance']:.2f}")
    
    if forward_results:
        print(f"\nFORWARD TEST (Last 30 days):")
        print(f"  Total Trades: {forward_results['total_trades']}")
        print(f"  Win Rate: {forward_results['win_rate']:.2f}%")
        print(f"  Total P&L: ${forward_results['total_pnl']:.2f}")
        print(f"  Profit %: {forward_results['profit_percentage']:.2f}%")
        print(f"  Final Balance: ${forward_results['final_balance']:.2f}")
    
    return backtest_results, forward_results

if __name__ == "__main__":
    backtest_results, forward_results = main()