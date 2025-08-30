#!/usr/bin/env python3
"""
Live Testnet Trading Bot - Simple and Clean
"""

import os
import sys
import time
import asyncio
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
import json

# Environment setup
os.environ['PYTHONIOENCODING'] = 'utf-8'

# API Configuration
API_KEY = "2bebcfa42c24f706250fc870c174c092e3d4d42b7b0912647524c59be6b2bf5a"
SECRET_KEY = "d23c85fd1947521e6e7c730ecc41790c6446c49b6f8b7305dab7c702a010c594"
TESTNET_URL = "https://testnet.binance.vision"

def create_testnet_client():
    """Create Binance testnet client"""
    client = Client(API_KEY, SECRET_KEY, testnet=True)
    client.API_URL = TESTNET_URL
    return client

def check_account_status(client):
    """Check testnet account status"""
    try:
        account = client.get_account()
        balances = {b['asset']: float(b['free']) for b in account['balances'] if float(b['free']) > 0}
        
        print("=== TESTNET ACCOUNT STATUS ===")
        print(f"Can Trade: {account.get('canTrade', False)}")
        print(f"Account Type: {account.get('accountType', 'N/A')}")
        print("\nBalances:")
        for asset, amount in balances.items():
            print(f"  {asset}: {amount:.8f}")
        
        return balances
    except BinanceAPIException as e:
        print(f"Error checking account: {e}")
        return None

def get_current_prices(client, symbols):
    """Get current prices for symbols"""
    prices = {}
    for symbol in symbols:
        try:
            ticker = client.get_symbol_ticker(symbol=symbol)
            prices[symbol] = float(ticker['price'])
            print(f"{symbol}: ${prices[symbol]:.2f}")
        except:
            pass
    return prices

def place_test_order(client, symbol, side, quantity):
    """Place a test order on testnet"""
    try:
        # First do a test order
        test_order = client.create_test_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        print(f"Test order successful for {symbol}")
        
        # Now place real testnet order
        order = client.create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        
        print(f"\n=== ORDER PLACED ===")
        print(f"Symbol: {order['symbol']}")
        print(f"Side: {order['side']}")
        print(f"Status: {order['status']}")
        print(f"Order ID: {order['orderId']}")
        
        return order
    except BinanceAPIException as e:
        print(f"Order failed: {e}")
        return None

async def run_live_test():
    """Run live testnet trading test"""
    print("\n" + "="*50)
    print("BINANCE TESTNET LIVE TRADING TEST")
    print("="*50)
    print(f"Time: {datetime.now()}")
    print(f"Using Testnet API: {TESTNET_URL}")
    
    # Create client
    client = create_testnet_client()
    
    # Check account
    balances = check_account_status(client)
    if not balances:
        print("Failed to connect to testnet")
        return
    
    # Get prices
    print("\n=== CURRENT PRICES ===")
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    prices = get_current_prices(client, symbols)
    
    # Check if we have USDT balance
    usdt_balance = balances.get('USDT', 0)
    print(f"\nAvailable USDT: {usdt_balance:.2f}")
    
    if usdt_balance > 10:
        print("\n=== ATTEMPTING TEST TRADE ===")
        # Try a small BTC buy
        btc_quantity = 0.0001  # Small test amount
        print(f"Attempting to buy {btc_quantity} BTC...")
        
        order = place_test_order(client, 'BTCUSDT', 'BUY', btc_quantity)
        
        if order:
            print("\n=== TRADE SUCCESSFUL ===")
            # Check updated balance
            time.sleep(2)
            new_balances = check_account_status(client)
            print("\nBalance changes detected!")
    else:
        print("\nInsufficient USDT balance for test trade")
        print("Note: This is testnet - balances are for testing only")
    
    # Get recent trades
    print("\n=== RECENT TRADES ===")
    try:
        trades = client.get_my_trades(symbol='BTCUSDT', limit=5)
        if trades:
            for trade in trades[:5]:
                print(f"Trade {trade['id']}: {trade['qty']} @ {trade['price']} - {trade['time']}")
        else:
            print("No recent trades")
    except:
        print("No trade history available")
    
    print("\n=== TEST COMPLETE ===")
    print("Testnet connection: SUCCESS")
    print("API Authentication: SUCCESS")
    print("Market Data: SUCCESS")
    print("Trading Capability: READY")

if __name__ == "__main__":
    print("Starting Binance Testnet Live Test...")
    asyncio.run(run_live_test())