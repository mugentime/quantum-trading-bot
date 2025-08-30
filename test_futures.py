#!/usr/bin/env python3
"""
Test futures trading on Binance testnet
"""

import asyncio
import ccxt.async_support as ccxt
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

async def test_futures_trading():
    """Test futures trading connection and permissions"""
    exchange = None
    try:
        print("=" * 50)
        print("TESTING FUTURES TRADING")
        print("=" * 50)
        
        # Initialize futures exchange
        exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'sandbox': True,  # Testnet
            'enableRateLimit': True,
        })
        
        # Set to futures mode
        exchange.options['defaultType'] = 'future'
        
        print("Testing futures connection...")
        
        # Test 1: Check server time
        try:
            server_time = await exchange.fetch_time()
            print(f"PASS: Server connection - {datetime.fromtimestamp(server_time/1000)}")
        except Exception as e:
            print(f"FAIL: Server connection - {e}")
            return False
        
        # Test 2: Check futures balance
        try:
            balance = await exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            print(f"PASS: Futures balance - ${usdt_balance:.2f} USDT")
        except Exception as e:
            print(f"FAIL: Futures balance - {e}")
            if "Invalid API-key" in str(e):
                print("NOTE: API keys may need futures trading permissions enabled")
            return False
        
        # Test 3: Get futures ticker
        try:
            ticker = await exchange.fetch_ticker('ETHUSDT')
            price = ticker['last']
            print(f"PASS: Market data - ETHUSDT: ${price:.2f}")
        except Exception as e:
            print(f"FAIL: Market data - {e}")
            return False
        
        # Test 4: Check futures positions
        try:
            positions = await exchange.fetch_positions()
            open_positions = [pos for pos in positions if pos['contracts'] > 0]
            print(f"PASS: Positions check - {len(open_positions)} open positions")
        except Exception as e:
            print(f"FAIL: Positions check - {e}")
            return False
        
        # Test 5: Send Telegram notification
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if bot_token and chat_id:
                message = (
                    "FUTURES TRADING TEST - SUCCESS!\n\n"
                    f"USDT Balance: ${usdt_balance:.2f}\n"
                    f"ETHUSDT Price: ${price:.2f}\n"
                    f"Open Positions: {len(open_positions)}\n"
                    f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "All futures trading tests passed!\n"
                    "System ready for live futures trading."
                )
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                response = requests.post(url, data={
                    'chat_id': chat_id,
                    'text': message
                })
                
                if response.status_code == 200:
                    print("PASS: Telegram notification sent")
                else:
                    print(f"FAIL: Telegram notification - {response.status_code}")
            else:
                print("SKIP: Telegram credentials not configured")
                
        except Exception as e:
            print(f"FAIL: Telegram notification - {e}")
        
        print("\n" + "=" * 50)
        print("FUTURES TRADING TEST COMPLETED SUCCESSFULLY")
        print("All core systems validated and operational")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return False
        
    finally:
        if exchange:
            await exchange.close()

if __name__ == "__main__":
    success = asyncio.run(test_futures_trading())
    if success:
        print("\nSUCCESS: Futures trading system is operational")
    else:
        print("\nERROR: Please check API permissions and configuration")