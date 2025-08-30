#!/usr/bin/env python3
"""
Sync JSON tracking with real account state
"""

import asyncio
import ccxt.async_support as ccxt
import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def sync_with_real_account():
    """Sync JSON file with actual account state"""
    print("=" * 50)
    print("SYNCING WITH REAL ACCOUNT STATE")
    print("=" * 50)
    
    # Get real account data
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_SECRET_KEY'),
        'sandbox': True,
        'enableRateLimit': True,
    })
    exchange.options['defaultType'] = 'future'
    
    try:
        # Get current balance and positions
        balance = await exchange.fetch_balance()
        current_balance = balance.get('USDT', {}).get('free', 0)
        
        positions = await exchange.fetch_positions()
        current_positions = {}
        
        for pos in positions:
            if abs(pos['contracts']) > 0:
                symbol = pos['symbol']
                current_positions[symbol] = {
                    'symbol': symbol,
                    'side': pos['side'],
                    'entry_price': pos['entryPrice'],
                    'quantity': pos['contracts'],
                    'entry_time': datetime.now().isoformat(),
                    'take_profit': pos['entryPrice'] * (1.03 if pos['side'] == 'long' else 0.97),
                    'stop_loss': pos['entryPrice'] * (0.98 if pos['side'] == 'long' else 1.02),
                    'order_id': f"sync_{int(datetime.now().timestamp())}",
                    'correlation': 0.5,
                    'deviation': 0.3
                }
        
        print(f"Real Account Balance: ${current_balance:.2f}")
        print(f"Real Active Positions: {len(current_positions)}")
        
        # Load current JSON
        with open('testnet_progress_20250829.json', 'r') as f:
            progress = json.load(f)
        
        old_positions = progress.get('active_positions', {})
        print(f"JSON Active Positions: {len(old_positions)}")
        
        # Close any tracked positions that don't exist in real account
        if old_positions and not current_positions:
            print("Closing tracked positions that no longer exist...")
            
            for symbol, pos in old_positions.items():
                # Estimate exit based on current market price
                ticker = await exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Calculate realistic PnL
                if pos['side'] == 'BUY':
                    pnl_pct = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                    pnl_usd = (current_price - pos['entry_price']) * pos['quantity']
                else:  # SELL
                    pnl_pct = ((pos['entry_price'] - current_price) / pos['entry_price']) * 100
                    pnl_usd = (pos['entry_price'] - current_price) * pos['quantity']
                
                completed_trade = {
                    "symbol": symbol,
                    "side": pos['side'],
                    "entry_price": pos['entry_price'],
                    "exit_price": current_price,
                    "quantity": pos['quantity'],
                    "entry_time": pos.get('entry_time', datetime.now().isoformat()),
                    "exit_time": datetime.now().isoformat(),
                    "pnl_pct": pnl_pct,
                    "pnl_usd": pnl_usd,
                    "exit_reason": "Account Sync - Position Closed",
                    "correlation": pos.get('correlation', 0),
                    "deviation": pos.get('deviation', 0)
                }
                
                progress['completed_trades'].append(completed_trade)
                print(f"  {symbol}: P&L ${pnl_usd:.2f} ({pnl_pct:.2f}%)")
        
        # Update JSON with real account state
        progress['active_positions'] = current_positions
        progress['total_unrealized_pnl'] = 0.0
        progress['last_sync'] = datetime.now().isoformat()
        progress['current_balance'] = current_balance
        
        # Save updated JSON
        with open('testnet_progress_20250829.json', 'w') as f:
            json.dump(progress, f, indent=2)
        
        print(f"\nSUCCESS: JSON synced with real account")
        print(f"Current Balance: ${current_balance:.2f}")
        print(f"Active Positions: {len(current_positions)}")
        print(f"Total Completed Trades: {len(progress['completed_trades'])}")
        
        # Send Telegram notification
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if bot_token and chat_id:
                total_pnl = sum(trade['pnl_usd'] for trade in progress['completed_trades'])
                initial_balance = progress.get('initial_balance', 7726.67)
                total_return = (total_pnl / initial_balance) * 100
                
                message = (
                    f"ACCOUNT SYNC COMPLETED\n\n"
                    f"Current Balance: ${current_balance:.2f}\n"
                    f"Active Positions: {len(current_positions)}\n"
                    f"Total Trades: {len(progress['completed_trades'])}\n"
                    f"Total P&L: ${total_pnl:.2f}\n"
                    f"Total Return: {total_return:.2f}%\n\n"
                    f"Trading bot is now synchronized with real account state!\n"
                    f"Ready for live trading operations."
                )
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                response = requests.post(url, data={
                    'chat_id': chat_id,
                    'text': message
                })
                
                print(f"Telegram notification: {'Sent' if response.status_code == 200 else 'Failed'}")
        except Exception as e:
            print(f"Telegram error: {e}")
        
    except Exception as e:
        print(f"Sync error: {e}")
        
    finally:
        await exchange.close()
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(sync_with_real_account())