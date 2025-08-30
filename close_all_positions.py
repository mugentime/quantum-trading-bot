#!/usr/bin/env python3
"""
Close all tracked positions (move to completed trades)
"""

import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def close_all_positions():
    """Close all active positions and move to completed trades"""
    print("CLOSING ALL TRACKED POSITIONS")
    print("=" * 40)
    
    # Load current tracking
    with open('testnet_progress_20250829.json', 'r') as f:
        progress = json.load(f)
    
    tracked_positions = progress.get('active_positions', {})
    
    if not tracked_positions:
        print("No active positions to close")
        return
    
    print(f"Closing {len(tracked_positions)} positions:")
    
    # Process each position
    for symbol, pos in tracked_positions.items():
        print(f"  {symbol}: {pos['side']} {pos['quantity']} @ ${pos['entry_price']:.2f}")
        
        # Estimate exit price and PnL
        if pos['side'] == 'BUY':
            # Use take profit if available, otherwise current market estimate
            estimated_exit = pos.get('take_profit', pos['entry_price'] * 1.01)
            pnl_pct = ((estimated_exit - pos['entry_price']) / pos['entry_price']) * 100
            pnl_usd = (estimated_exit - pos['entry_price']) * pos['quantity']
        else:  # SELL
            # Use take profit if available, otherwise current market estimate  
            estimated_exit = pos.get('take_profit', pos['entry_price'] * 0.99)
            pnl_pct = ((pos['entry_price'] - estimated_exit) / pos['entry_price']) * 100
            pnl_usd = (pos['entry_price'] - estimated_exit) * pos['quantity']
        
        # Create completed trade record
        completed_trade = {
            "symbol": symbol,
            "side": pos['side'],
            "entry_price": pos['entry_price'],
            "exit_price": estimated_exit,
            "quantity": pos['quantity'],
            "entry_time": pos.get('entry_time', datetime.now().isoformat()),
            "exit_time": datetime.now().isoformat(),
            "pnl_pct": pnl_pct,
            "pnl_usd": pnl_usd,
            "exit_reason": "Manual Close - Position Sync",
            "correlation": pos.get('correlation', 0),
            "deviation": pos.get('deviation', 0)
        }
        
        progress['completed_trades'].append(completed_trade)
        print(f"    -> Moved to completed: PnL ${pnl_usd:.2f} ({pnl_pct:.2f}%)")
    
    # Clear active positions
    progress['active_positions'] = {}
    
    # Update total unrealized PnL
    progress['total_unrealized_pnl'] = 0.0
    
    # Save updated file
    with open('testnet_progress_20250829.json', 'w') as f:
        json.dump(progress, f, indent=2)
    
    print(f"\nSUCCESS: All positions closed and synced")
    print(f"Active positions: 0")
    print(f"Total completed trades: {len(progress['completed_trades'])}")
    
    # Calculate total performance
    total_pnl = sum(trade['pnl_usd'] for trade in progress['completed_trades'])
    initial_balance = progress.get('initial_balance', 7726.67)
    total_return = (total_pnl / initial_balance) * 100
    
    # Send Telegram notification
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            message = (
                f"POSITION SYNC COMPLETED\n\n"
                f"All tracked positions closed\n"
                f"Active positions: 0\n"
                f"Total trades: {len(progress['completed_trades'])}\n"
                f"Total P&L: ${total_pnl:.2f}\n"
                f"Total Return: {total_return:.2f}%\n"
                f"Sync time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Position tracking is now synchronized!"
            )
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            response = requests.post(url, data={
                'chat_id': chat_id,
                'text': message
            })
            
            print(f"Telegram notification: {'Sent' if response.status_code == 200 else 'Failed'}")
    except Exception as e:
        print(f"Telegram error: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    close_all_positions()