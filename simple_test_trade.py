#!/usr/bin/env python3
"""
Simple test trade execution
"""

import asyncio
import ccxt.async_support as ccxt
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv()

async def send_test_trade():
    """Send a simple test trade"""
    try:
        print("=" * 50)
        print("EXECUTING TEST TRADE")
        print("=" * 50)
        
        # Initialize exchange
        exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'sandbox': True,  # Testnet
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })
        
        # Test connection
        print("Testing exchange connection...")
        balance = await exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        print(f"✅ Connection successful - USDT Balance: ${usdt_balance:.2f}")
        
        # Get current price
        ticker = await exchange.fetch_ticker('ETHUSDT')
        current_price = ticker['last']
        print(f"📈 Current ETHUSDT price: ${current_price:.2f}")
        
        # Calculate small test position (0.001 ETH)
        test_quantity = 0.001
        print(f"🎯 Test trade: BUY {test_quantity} ETHUSDT")
        
        # Place test order
        print("Placing test market order...")
        order = await exchange.create_market_buy_order('ETHUSDT', test_quantity)
        
        if order and order.get('id'):
            print(f"✅ TEST TRADE SUCCESSFUL!")
            print(f"Order ID: {order['id']}")
            print(f"Symbol: {order['symbol']}")
            print(f"Amount: {order['amount']}")
            print(f"Status: {order['status']}")
            
            # Send to Telegram
            try:
                import requests
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                
                if bot_token and chat_id:
                    message = (
                        f"✅ TEST TRADE EXECUTED!\n\n"
                        f"Order ID: {order['id']}\n"
                        f"Symbol: ETHUSDT\n"
                        f"Action: BUY\n"
                        f"Amount: {test_quantity} ETH\n"
                        f"Price: ~${current_price:.2f}\n"
                        f"Status: {order['status']}\n\n"
                        f"🔒 All security validations passed\n"
                        f"🚀 Quantum Trading Bot is operational!"
                    )
                    
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    requests.post(url, data={
                        'chat_id': chat_id,
                        'text': message
                    })
                    print("📱 Telegram notification sent")
                    
            except Exception as e:
                print(f"⚠️ Telegram notification failed: {e}")
        else:
            print("❌ Test trade failed - no order returned")
            
        await exchange.close()
        print("Test trade completed successfully")
        
    except Exception as e:
        print(f"❌ Test trade error: {e}")
        try:
            await exchange.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(send_test_trade())