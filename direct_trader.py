#!/usr/bin/env python3
"""
Direct Trader - Simple live trading script with leverage optimization
Bypasses import issues by using direct API calls
"""

import ccxt
import json
import time
import os
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import hashlib
import hmac
import urllib.parse

# Load environment variables
load_dotenv()

class DirectLeverageTrader:
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        self.testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        self.base_url = 'https://testnet.binancefuture.com' if self.testnet else 'https://fapi.binance.com'
        
        # Load leverage configuration
        self.leverage_config = self.load_leverage_config()
        
        # Trading parameters
        self.trading_pairs = ['ETHUSDT', 'BTCUSDT', 'SOLUSDT', 'ADAUSDT', 'AVAXUSDT']
        self.position_size = 200  # Base position size in USDT
        
        print(f"Direct Leverage Trader initialized")
        print(f"Testnet: {self.testnet}")
        print(f"Trading pairs: {len(self.trading_pairs)}")
    
    def load_leverage_config(self):
        """Load leverage optimization configuration"""
        try:
            with open('optimized_leverage_config.json', 'r') as f:
                return json.load(f)
        except:
            # Default config if file not found
            return {
                'trading_pairs': {
                    'ETHUSDT': {'leverage': 5, 'priority': 1, 'risk_level': 'MEDIUM'},
                    'BTCUSDT': {'leverage': 2, 'priority': 5, 'risk_level': 'HIGH'},
                    'SOLUSDT': {'leverage': 3, 'priority': 3, 'risk_level': 'HIGH'},
                    'ADAUSDT': {'leverage': 8, 'priority': 1, 'risk_level': 'LOW'},
                    'AVAXUSDT': {'leverage': 6, 'priority': 1, 'risk_level': 'LOW'}
                }
            }
    
    def get_signature(self, query_string):
        """Generate API signature"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def make_request(self, endpoint, params=None, method='GET'):
        """Make authenticated API request"""
        if params is None:
            params = {}
        
        params['timestamp'] = int(time.time() * 1000)
        
        query_string = urllib.parse.urlencode(params)
        signature = self.get_signature(query_string)
        
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers)
        
        return response.json()
    
    def get_account_balance(self):
        """Get account balance"""
        try:
            result = self.make_request('/fapi/v2/account')
            if 'assets' in result:
                for asset in result['assets']:
                    if asset['asset'] == 'USDT':
                        return float(asset['walletBalance'])
            return 0
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0
    
    def get_current_price(self, symbol):
        """Get current price for symbol"""
        try:
            result = self.make_request('/fapi/v1/ticker/price', {'symbol': symbol})
            return float(result['price']) if 'price' in result else None
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return None
    
    def set_leverage(self, symbol, leverage):
        """Set leverage for symbol"""
        try:
            params = {
                'symbol': symbol,
                'leverage': leverage
            }
            result = self.make_request('/fapi/v1/leverage', params, 'POST')
            return 'leverage' in result
        except Exception as e:
            print(f"Error setting leverage for {symbol}: {e}")
            return False
    
    def place_order(self, symbol, side, quantity, order_type='MARKET'):
        """Place an order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': f"{quantity:.6f}"
            }
            
            result = self.make_request('/fapi/v1/order', params, 'POST')
            return result
        except Exception as e:
            print(f"Error placing order for {symbol}: {e}")
            return None
    
    def get_positions(self):
        """Get current positions"""
        try:
            result = self.make_request('/fapi/v2/positionRisk')
            active_positions = []
            for pos in result:
                if float(pos['positionAmt']) != 0:
                    active_positions.append(pos)
            return active_positions
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def calculate_correlation_signal(self, symbol):
        """Simple correlation-based signal (placeholder)"""
        # For now, return a random signal to demonstrate functionality
        # In real implementation, this would use proper correlation analysis
        import random
        
        signals = ['BUY', 'SELL', 'HOLD']
        weights = [0.3, 0.3, 0.4]  # Favor HOLD to be conservative
        
        return np.random.choice(signals, p=weights)
    
    def should_trade(self, symbol):
        """Determine if we should trade this symbol"""
        # Get current positions
        positions = self.get_positions()
        
        # Don't trade if already have position
        for pos in positions:
            if pos['symbol'] == symbol:
                return False
        
        # Limit concurrent positions
        if len(positions) >= 3:
            return False
        
        return True
    
    def run_trading_cycle(self):
        """Run one trading cycle"""
        print(f"\n{datetime.now()} - Starting trading cycle...")
        
        # Get account balance
        balance = self.get_account_balance()
        print(f"Account Balance: ${balance:.2f}")
        
        # Check current positions
        positions = self.get_positions()
        print(f"Active positions: {len(positions)}")
        
        # Sort pairs by priority from leverage config
        sorted_pairs = sorted(
            self.trading_pairs,
            key=lambda x: self.leverage_config['trading_pairs'].get(x, {}).get('priority', 5)
        )
        
        for symbol in sorted_pairs:
            try:
                if not self.should_trade(symbol):
                    continue
                
                # Get current price
                price = self.get_current_price(symbol)
                if not price:
                    continue
                
                # Generate signal
                signal = self.calculate_correlation_signal(symbol)
                if signal == 'HOLD':
                    continue
                
                print(f"{symbol}: Signal={signal}, Price=${price:.2f}")
                
                # Get leverage config
                pair_config = self.leverage_config['trading_pairs'].get(symbol, {})
                leverage = pair_config.get('leverage', 2)
                
                # Set leverage
                if self.set_leverage(symbol, leverage):
                    print(f"Set {symbol} leverage to {leverage}x")
                
                # Calculate position size
                position_value = self.position_size * leverage
                quantity = position_value / price
                
                # Place order
                order = self.place_order(symbol, signal, quantity)
                if order and 'orderId' in order:
                    print(f"Order placed: {symbol} {signal} {quantity:.6f} @ {price:.2f}")
                    print(f"Leverage: {leverage}x, Position value: ${position_value:.2f}")
                    
                    # Send Telegram notification
                    self.send_telegram_notification(symbol, signal, price, quantity, leverage)
                
                # Small delay between orders
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
    
    def send_telegram_notification(self, symbol, side, price, quantity, leverage):
        """Send trade notification to Telegram"""
        try:
            telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if not telegram_token or not chat_id:
                return
            
            message = f"LIVE TRADE EXECUTED\\n"
            message += f"Symbol: {symbol}\\n"
            message += f"Side: {side}\\n" 
            message += f"Price: ${price:.2f}\\n"
            message += f"Quantity: {quantity:.6f}\\n"
            message += f"Leverage: {leverage}x\\n"
            message += f"Time: {datetime.now().strftime('%H:%M:%S')}"
            
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            requests.post(url, data=data)
            
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
    
    def run(self):
        """Main trading loop"""
        print("="*50)
        print("DIRECT LEVERAGE TRADER - STARTED")
        print("="*50)
        
        # Test API connection
        balance = self.get_account_balance()
        if balance == 0:
            print("ERROR: Could not connect to API or get balance")
            return
        
        print(f"[OK] API connection successful")
        print(f"[OK] Account balance: ${balance:.2f}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                try:
                    self.run_trading_cycle()
                except Exception as e:
                    print(f"Error in trading cycle {cycle_count}: {e}")
                
                # Wait 5 minutes between cycles
                print(f"Cycle {cycle_count} complete. Waiting 5 minutes...")
                time.sleep(300)
                
        except KeyboardInterrupt:
            print("\nTrading stopped by user")
        except Exception as e:
            print(f"Critical error: {e}")

def main():
    trader = DirectLeverageTrader()
    trader.run()

if __name__ == "__main__":
    main()