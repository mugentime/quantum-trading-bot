#!/usr/bin/env python3
"""
Verify API credentials match the tracked positions
"""

import asyncio
import ccxt.async_support as ccxt
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

async def verify_account():
    """Verify API credentials match tracked positions"""
    print("=" * 50)
    print("VERIFYING ACCOUNT MATCH")
    print("=" * 50)
    
    # Load tracked positions
    with open('testnet_progress_20250829.json', 'r') as f:
        progress = json.load(f)
    
    tracked_positions = progress.get('active_positions', {})
    initial_balance = progress.get('initial_balance', 0)
    
    print("EXPECTED FROM JSON FILE:")
    print(f"  Initial Balance: ${initial_balance:.2f}")
    print(f"  Active Positions: {len(tracked_positions)}")
    if tracked_positions:
        for symbol, pos in tracked_positions.items():
            print(f"    {symbol}: {pos['side']} {pos['quantity']} @ ${pos['entry_price']:.2f}")
    
    print("\n" + "-" * 30)
    
    # Check actual account
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_SECRET_KEY'),
        'sandbox': True,
        'enableRateLimit': True,
    })
    exchange.options['defaultType'] = 'future'
    
    try:
        # Get balance
        balance = await exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        
        # Get positions
        positions = await exchange.fetch_positions()
        actual_positions = {}
        for pos in positions:
            if abs(pos['contracts']) > 0:
                symbol = pos['symbol']
                actual_positions[symbol] = {
                    'side': pos['side'],
                    'size': pos['contracts'],
                    'entry_price': pos['entryPrice']
                }
        
        print("ACTUAL FROM API:")
        print(f"  USDT Balance: ${usdt_balance:.2f}")
        print(f"  Active Positions: {len(actual_positions)}")
        if actual_positions:
            for symbol, pos in actual_positions.items():
                print(f"    {symbol}: {pos['side']} {pos['size']} @ ${pos['entry_price']:.2f}")
        
        print("\n" + "-" * 30)
        
        # Compare
        if len(tracked_positions) == len(actual_positions):
            if len(tracked_positions) == 0:
                status = "MATCH - Both accounts have no positions"
            else:
                matches = sum(1 for sym in tracked_positions if sym in actual_positions)
                if matches == len(tracked_positions):
                    status = "MATCH - Positions match"
                else:
                    status = f"PARTIAL MATCH - {matches}/{len(tracked_positions)} positions match"
        else:
            status = "MISMATCH - Different number of positions"
        
        print(f"VERIFICATION: {status}")
        
        # Send Telegram
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if bot_token and chat_id:
                message = (
                    f"ACCOUNT VERIFICATION\n\n"
                    f"Expected Balance: ${initial_balance:.2f}\n"
                    f"Actual Balance: ${usdt_balance:.2f}\n"
                    f"Expected Positions: {len(tracked_positions)}\n"
                    f"Actual Positions: {len(actual_positions)}\n\n"
                    f"Status: {status}\n\n"
                )
                
                if status.startswith("MATCH"):
                    message += "API credentials are correct for this account!"
                else:
                    message += "API credentials may be from different account"
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(url, data={'chat_id': chat_id, 'text': message})
                
                print("Telegram notification sent")
        except Exception as e:
            print(f"Telegram error: {e}")
            
    except Exception as e:
        print(f"API Error: {e}")
        status = "ERROR - Cannot verify account"
    
    finally:
        await exchange.close()
    
    print("=" * 50)
    return status

if __name__ == "__main__":
    asyncio.run(verify_account())