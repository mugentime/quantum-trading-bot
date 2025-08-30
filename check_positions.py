#!/usr/bin/env python3
"""
Check actual positions vs tracked positions
"""

import asyncio
import ccxt.async_support as ccxt
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

async def check_positions():
    """Check discrepancy between tracked and actual positions"""
    exchange = None
    try:
        print("=" * 50)
        print("CHECKING POSITION DISCREPANCY")
        print("=" * 50)
        
        # Read tracked positions
        with open('testnet_progress_20250829.json', 'r') as f:
            progress = json.load(f)
            tracked_positions = progress.get('active_positions', {})
        
        print("TRACKED POSITIONS (from JSON):")
        if tracked_positions:
            for symbol, pos in tracked_positions.items():
                print(f"  {symbol}: {pos['side']} {pos['quantity']} @ ${pos['entry_price']:.2f}")
                print(f"    Order ID: {pos['order_id']}")
        else:
            print("  No tracked positions")
        
        print("\n" + "-" * 30)
        
        # Check actual positions on exchange
        exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'sandbox': True,
            'enableRateLimit': True,
        })
        exchange.options['defaultType'] = 'future'
        
        try:
            positions = await exchange.fetch_positions()
            actual_positions = {}
            
            print("ACTUAL POSITIONS (from Binance):")
            open_count = 0
            for pos in positions:
                if abs(pos['contracts']) > 0:  # Non-zero position
                    symbol = pos['symbol']
                    actual_positions[symbol] = {
                        'symbol': symbol,
                        'side': pos['side'],
                        'size': pos['contracts'],
                        'entry_price': pos['entryPrice'],
                        'unrealized_pnl': pos['unrealizedPnl']
                    }
                    print(f"  {symbol}: {pos['side']} {pos['contracts']} @ ${pos['entryPrice']:.2f}")
                    print(f"    Unrealized PnL: ${pos['unrealizedPnl']:.2f}")
                    open_count += 1
            
            if open_count == 0:
                print("  No actual positions found on exchange")
                
        except Exception as e:
            print(f"FAILED to get actual positions: {e}")
            if "Invalid API-key" in str(e):
                print("NOTE: API keys need futures trading permissions")
            actual_positions = {}
        
        print("\n" + "-" * 30)
        print("DISCREPANCY ANALYSIS:")
        
        # Compare positions
        if not tracked_positions and not actual_positions:
            print("  MATCH: No positions in both tracking and exchange")
            status = "SYNCHRONIZED"
        elif tracked_positions and not actual_positions:
            print("  MISMATCH: Tracked positions exist but no actual positions")
            print("  This suggests positions were closed externally")
            status = "OUT_OF_SYNC"
        elif not tracked_positions and actual_positions:
            print("  MISMATCH: Actual positions exist but not tracked")
            print("  This suggests positions were opened externally")
            status = "OUT_OF_SYNC"
        else:
            # Both exist, check if they match
            matches = 0
            for symbol in tracked_positions:
                if symbol in actual_positions:
                    matches += 1
            
            if matches == len(tracked_positions) and matches == len(actual_positions):
                print("  MATCH: All positions synchronized")
                status = "SYNCHRONIZED"
            else:
                print(f"  PARTIAL MATCH: {matches}/{len(tracked_positions)} positions match")
                status = "PARTIALLY_SYNCED"
        
        # Send Telegram status
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if bot_token and chat_id:
                message = (
                    f"POSITION CHECK REPORT\n\n"
                    f"Tracked Positions: {len(tracked_positions)}\n"
                    f"Actual Positions: {len(actual_positions) if 'actual_positions' in locals() else 'API Error'}\n"
                    f"Status: {status}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
                
                if tracked_positions:
                    message += "TRACKED:\n"
                    for symbol, pos in tracked_positions.items():
                        message += f"  {symbol}: {pos['side']} {pos['quantity']}\n"
                
                if actual_positions:
                    message += "\nACTUAL:\n"
                    for symbol, pos in actual_positions.items():
                        message += f"  {symbol}: {pos['side']} {pos['size']}\n"
                
                if status == "OUT_OF_SYNC":
                    message += "\nACTION NEEDED: Position tracking requires manual sync"
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                response = requests.post(url, data={
                    'chat_id': chat_id,
                    'text': message
                })
                
                print(f"\nTelegram notification sent: {response.status_code == 200}")
                
        except Exception as e:
            print(f"Telegram notification failed: {e}")
        
        print("\n" + "=" * 50)
        print(f"POSITION CHECK COMPLETE - Status: {status}")
        print("=" * 50)
        
        return status
        
    except Exception as e:
        print(f"ERROR: {e}")
        return "ERROR"
        
    finally:
        if exchange:
            await exchange.close()

if __name__ == "__main__":
    asyncio.run(check_positions())