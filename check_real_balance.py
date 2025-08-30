import os
import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode

# Read real mainnet keys from environment
api_key = "KP5NFDffn3reE3md2SKkrcRTgTLwJKrE7wvBVNizdZfuBswKGVbBTluopkmofax1"
secret_key = "7sKgwdD9OJ4UCQVM8CJ3EuTCXJksKCCy5C1vXwyXlLuHNqHc8pVxJ1UPdKbsuSfq"

def create_signature(params, secret):
    """Create HMAC SHA256 signature for Binance API"""
    query_string = urlencode(params)
    return hmac.new(
        secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def get_account_info():
    """Get real mainnet account information"""
    base_url = "https://api.binance.com"  # Mainnet URL
    endpoint = "/api/v3/account"
    
    timestamp = int(time.time() * 1000)
    params = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    signature = create_signature(params, secret_key)
    params['signature'] = signature
    
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
    try:
        response = requests.get(
            f"{base_url}{endpoint}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Find USDT balance
            balances = data.get('balances', [])
            
            print("=== REAL MAINNET ACCOUNT ===")
            print(f"Can Trade: {data.get('canTrade')}")
            print(f"Can Withdraw: {data.get('canWithdraw')}")
            print(f"Can Deposit: {data.get('canDeposit')}")
            print("\n=== NON-ZERO BALANCES ===")
            
            total_value_usd = 0
            for balance in balances:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0.00001:  # Only show non-dust balances
                    print(f"{balance['asset']}: {total:.8f} (Free: {free:.8f}, Locked: {locked:.8f})")
                    
                    # Rough USD estimate for major coins
                    if balance['asset'] == 'USDT':
                        total_value_usd += total
                    elif balance['asset'] == 'BTC':
                        total_value_usd += total * 98000  # Approximate BTC price
                    elif balance['asset'] == 'ETH':
                        total_value_usd += total * 3300  # Approximate ETH price
            
            print(f"\n=== ESTIMATED TOTAL VALUE ===")
            print(f"~${total_value_usd:.2f} USD (rough estimate)")
            
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    print("Checking REAL Binance mainnet balance...")
    print(f"API Key: {api_key[:20]}...{api_key[-4:]}")
    print(f"Using mainnet URL: https://api.binance.com\n")
    get_account_info()