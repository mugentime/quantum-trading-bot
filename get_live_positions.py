#!/usr/bin/env python3
"""Get actual live positions from Binance testnet to sync with local tracking"""
import asyncio
import json
from datetime import datetime
import sys
import os
import ccxt.async_support as ccxt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config.settings import config
from utils.telegram_notifier import TelegramNotifier

async def get_live_positions():
    """Fetch actual live positions from Binance testnet"""
    try:
        print("Connecting to Binance testnet...")
        
        # Initialize Binance client
        exchange = ccxt.binance({
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'sandbox': True,  # Use testnet
            'enableRateLimit': True,
            'urls': {
                'api': {
                    'public': 'https://testnet.binancefuture.com/fapi/v1',
                    'private': 'https://testnet.binancefuture.com/fapi/v1'
                }
            },
            'options': {
                'defaultType': 'future'  # Use futures
            }
        })
        
        # Get account balance
        balance = await exchange.fetch_balance()
        account_balance = balance['USDT']['total']
        print(f"Account Balance: {account_balance:.2f} USDT")
        
        # Get all open positions
        positions = await exchange.fetch_positions()
        print(f"\nFound {len(positions)} total positions:")
        
        live_positions = {}
        total_unrealized_pnl = 0
        
        for position in positions:
            symbol = position['symbol']
            size = position['contracts']
            entry_price = position['entryPrice']
            unrealized_pnl = position['unrealizedPnl']
            percentage = position['percentage']
            
            if size is not None and size != 0:  # Only active positions
                side = "LONG" if size > 0 else "SHORT"
                
                live_positions[symbol] = {
                    'symbol': symbol,
                    'side': side,
                    'size': abs(size),
                    'entry_price': entry_price,
                    'unrealized_pnl': unrealized_pnl,
                    'roe_percentage': percentage,
                    'timestamp': datetime.now().isoformat()
                }
                
                if unrealized_pnl:
                    total_unrealized_pnl += unrealized_pnl
                
                print(f"  {symbol}: {side} {abs(size):.4f} @ ${entry_price:.2f}")
                print(f"    Unrealized PnL: ${unrealized_pnl:.2f} ({percentage:.2f}%)")
        
        print(f"\nTotal Unrealized PnL: ${total_unrealized_pnl:.2f}")
        
        # Save to file
        sync_data = {
            'timestamp': datetime.now().isoformat(),
            'account_balance': account_balance,
            'total_unrealized_pnl': total_unrealized_pnl,
            'live_positions': live_positions
        }
        
        with open('live_positions_sync.json', 'w') as f:
            json.dump(sync_data, f, indent=2)
        
        print(f"\nLive positions saved to: live_positions_sync.json")
        
        # Send to Telegram
        telegram = TelegramNotifier()
        
        message = f"LIVE POSITIONS SYNC\n"
        message += f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += f"Account Balance: ${account_balance:.2f} USDT\n"
        message += f"Total Unrealized PnL: ${total_unrealized_pnl:.2f}\n\n"
        
        if live_positions:
            message += f"ACTIVE POSITIONS ({len(live_positions)}):\n"
            for symbol, pos in live_positions.items():
                message += f"  {symbol}: {pos['side']} {pos['size']:.4f}\n"
                message += f"    Entry: ${pos['entry_price']:.2f}\n"
                message += f"    PnL: ${pos['unrealized_pnl']:.2f} ({pos['roe_percentage']:.2f}%)\n\n"
        else:
            message += "No active positions\n"
        
        await telegram.send_message(message)
        print("Sync data sent to Telegram")
        
        return sync_data
        
    except Exception as e:
        print(f"Error fetching live positions: {e}")
        return None
    finally:
        if 'exchange' in locals():
            await exchange.close()

if __name__ == "__main__":
    result = asyncio.run(get_live_positions())