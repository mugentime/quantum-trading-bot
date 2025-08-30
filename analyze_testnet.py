#!/usr/bin/env python3
"""
Analyze Testnet Trading Results
"""

import json
import os
from datetime import datetime

def analyze_testnet_performance():
    """Analyze the testnet trading performance"""
    
    # Find the latest testnet progress file
    files = [f for f in os.listdir('.') if f.startswith('testnet_progress_') and f.endswith('.json')]
    if not files:
        print("No testnet progress files found")
        return
    
    latest_file = max(files)
    print(f'=== ANALYZING: {latest_file} ===\n')
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    print('=== TESTNET LIVE TRADING PERFORMANCE ===')
    print(f'Start Time: {data.get("start_time", "N/A")}')
    print(f'Initial Balance: ${data.get("initial_balance", 0):.2f} USDT')
    
    # Trading statistics
    completed_trades = data.get('completed_trades', [])
    active_positions = data.get('active_positions', {})
    
    print(f'\n=== TRADING STATISTICS ===')
    print(f'Total Completed Trades: {len(completed_trades)}')
    print(f'Active Positions: {len(active_positions)}')
    
    if completed_trades:
        # Calculate performance metrics
        total_pnl = sum(trade.get('pnl_usd', 0) for trade in completed_trades)
        winning_trades = [t for t in completed_trades if t.get('pnl_usd', 0) > 0]
        losing_trades = [t for t in completed_trades if t.get('pnl_usd', 0) < 0]
        
        win_rate = len(winning_trades) / len(completed_trades) * 100 if completed_trades else 0
        avg_win = sum(t.get('pnl_usd', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.get('pnl_usd', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        print(f'\n=== PERFORMANCE METRICS ===')
        print(f'Total Realized P&L: ${total_pnl:.2f} USDT')
        print(f'Win Rate: {win_rate:.1f}% ({len(winning_trades)}/{len(completed_trades)})')
        print(f'Average Win: ${avg_win:.2f}')
        print(f'Average Loss: ${avg_loss:.2f}')
        
        if avg_loss != 0:
            profit_factor = -avg_win / avg_loss if avg_loss < 0 else 0
            print(f'Profit Factor: {profit_factor:.2f}')
        
        # Return percentage
        initial_balance = data.get("initial_balance", 10000)
        return_pct = (total_pnl / initial_balance) * 100
        print(f'Return Percentage: {return_pct:.2f}%')
        print(f'Estimated Current Balance: ${initial_balance + total_pnl:.2f}')
        
        # Recent trades analysis
        print(f'\n=== LAST 5 COMPLETED TRADES ===')
        for i, trade in enumerate(completed_trades[-5:], 1):
            pnl = trade.get('pnl_usd', 0)
            pnl_pct = trade.get('pnl_pct', 0)
            symbol = trade.get('symbol', '')
            side = trade.get('side', '')
            exit_reason = trade.get('exit_reason', '')
            entry_time = trade.get('entry_time', '')[:16]  # Truncate timestamp
            correlation = trade.get('correlation', 0)
            
            status = "WIN" if pnl > 0 else "LOSS"
            print(f'{i}. {symbol} {side} {status}: ${pnl:+.2f} ({pnl_pct:+.2f}%) | Corr: {correlation:.3f} | {exit_reason} | {entry_time}')
        
        # Exit reason analysis
        exit_reasons = {}
        for trade in completed_trades:
            reason = trade.get('exit_reason', 'Unknown')
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        print(f'\n=== EXIT REASON BREAKDOWN ===')
        for reason, count in exit_reasons.items():
            pct = count / len(completed_trades) * 100
            print(f'{reason}: {count} trades ({pct:.1f}%)')
    
    # Active positions
    if active_positions:
        print(f'\n=== ACTIVE POSITIONS ===')
        for symbol, pos in active_positions.items():
            print(f'{symbol}: {pos["side"]} {pos["quantity"]} @ ${pos["entry_price"]:.2f}')
            print(f'  Entry Time: {pos["entry_time"][:16]}')
            print(f'  Take Profit: ${pos.get("take_profit", 0):.2f}')
            print(f'  Stop Loss: ${pos.get("stop_loss", 0):.2f}')
            print(f'  Correlation: {pos.get("correlation", 0):.3f}')
    else:
        print('\n=== NO ACTIVE POSITIONS ===')
    
    print('\n=== ANALYSIS COMPLETE ===')

if __name__ == "__main__":
    analyze_testnet_performance()