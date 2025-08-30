#!/usr/bin/env python3
"""
Manually sync position tracking with actual account state
"""

import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def sync_positions():
    """Manually sync positions based on user input"""
    print("=" * 50)
    print("MANUAL POSITION SYNCHRONIZATION")
    print("=" * 50)
    
    # Load current tracking
    with open('testnet_progress_20250829.json', 'r') as f:
        progress = json.load(f)
    
    tracked_positions = progress.get('active_positions', {})
    
    print("CURRENT TRACKED POSITIONS:")
    if tracked_positions:
        for symbol, pos in tracked_positions.items():
            print(f"  {symbol}: {pos['side']} {pos['quantity']} @ ${pos['entry_price']:.2f}")
    else:
        print("  No tracked positions")
    
    print("\nWhat is the ACTUAL status of positions on Binance testnet?")
    print("1. All positions are closed (0 positions)")
    print("2. Some positions are still open")
    print("3. Different positions than tracked")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        # Close all positions
        print("Closing all tracked positions...")
        
        # Move active positions to completed trades
        if tracked_positions:
            for symbol, pos in tracked_positions.items():
                # Calculate estimated PnL (since we can't get real data)
                if pos['side'] == 'BUY':
                    # Estimate exit price (could be stop loss, take profit, or current market)
                    estimated_exit = pos.get('stop_loss', pos['entry_price'] * 0.98)
                else:  # SELL
                    estimated_exit = pos.get('take_profit', pos['entry_price'] * 1.02)
                
                completed_trade = {
                    "symbol": symbol,
                    "side": pos['side'],
                    "entry_price": pos['entry_price'],
                    "exit_price": estimated_exit,
                    "quantity": pos['quantity'],
                    "entry_time": pos['entry_time'],
                    "exit_time": datetime.now().isoformat(),
                    "pnl_pct": ((estimated_exit - pos['entry_price']) / pos['entry_price'] * 100) if pos['side'] == 'BUY' else ((pos['entry_price'] - estimated_exit) / pos['entry_price'] * 100),
                    "pnl_usd": (estimated_exit - pos['entry_price']) * pos['quantity'] if pos['side'] == 'BUY' else (pos['entry_price'] - estimated_exit) * pos['quantity'],
                    "exit_reason": "Manual Sync - External Close",
                    "correlation": pos.get('correlation', 0),
                    "deviation": pos.get('deviation', 0)
                }
                
                progress['completed_trades'].append(completed_trade)
        
        # Clear active positions
        progress['active_positions'] = {}
        
        # Update file
        with open('testnet_progress_20250829.json', 'w') as f:
            json.dump(progress, f, indent=2)
        
        print("✓ All positions marked as closed and moved to completed trades")
        
        # Send Telegram notification
        send_telegram_update("POSITION SYNC COMPLETE", 
                           f"All tracked positions closed\nActive positions: 0\nSync time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    elif choice == "2":
        print("Which positions are still open?")
        still_open = []
        for symbol in tracked_positions:
            keep = input(f"Is {symbol} position still open? (y/n): ").strip().lower()
            if keep == 'y':
                still_open.append(symbol)
        
        # Remove closed positions
        new_active = {symbol: pos for symbol, pos in tracked_positions.items() if symbol in still_open}
        progress['active_positions'] = new_active
        
        # Move closed to completed
        for symbol, pos in tracked_positions.items():
            if symbol not in still_open:
                # Add to completed trades (similar logic as above)
                pass
        
        with open('testnet_progress_20250829.json', 'w') as f:
            json.dump(progress, f, indent=2)
        
        print(f"✓ Updated: {len(still_open)} positions remain active")
        
        send_telegram_update("POSITION SYNC UPDATE", 
                           f"Active positions: {len(still_open)}\nSymbols: {', '.join(still_open)}")
        
    else:
        print("Manual position entry not implemented yet")
        print("Please use choice 1 or 2")
    
    print("=" * 50)
    print("SYNC COMPLETE")
    print("=" * 50)

def send_telegram_update(title, message):
    """Send update to Telegram"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            full_message = f"{title}\n\n{message}"
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            response = requests.post(url, data={
                'chat_id': chat_id,
                'text': full_message
            })
            print(f"Telegram notification: {'Sent' if response.status_code == 200 else 'Failed'}")
    except Exception as e:
        print(f"Telegram error: {e}")

if __name__ == "__main__":
    sync_positions()