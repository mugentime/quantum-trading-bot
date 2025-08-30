#!/usr/bin/env python3
"""
Execute transfers using direct API calls to Binance
This bypasses any library issues and uses direct HTTP requests
"""

import requests
import hmac
import hashlib
import time
import json
from urllib.parse import urlencode
from datetime import datetime

# Mainnet API credentials
API_KEY = 'KP5NFDffn3reE3md2SKkrcRTgTLwJKrE7wvBVNizdZfuBswKGVbBTluopkmofax1'
SECRET_KEY = '2bUXyAuNY0zjrlXWi5xC8DDmVxkhOtYu7W6RwstZ33Ytr7jzins2SUemRCDpLIV5'
BASE_URL = 'https://api.binance.com'

def generate_signature(query_string, secret):
    """Generate HMAC SHA256 signature"""
    return hmac.new(
        secret.encode('utf-8'), 
        query_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

def make_signed_request(endpoint, params=None, method='GET'):
    """Make a signed request to Binance API"""
    if params is None:
        params = {}
    
    # Add timestamp
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = 60000
    
    # Create query string
    query_string = urlencode(sorted(params.items()))
    
    # Generate signature
    signature = generate_signature(query_string, SECRET_KEY)
    params['signature'] = signature
    
    # Headers
    headers = {
        'X-MBX-APIKEY': API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    if method == 'GET':
        response = requests.get(url, params=params, headers=headers)
    elif method == 'POST':
        response = requests.post(url, data=params, headers=headers)
    
    return response

def get_account_info():
    """Get spot account information"""
    print("Getting account information...")
    response = make_signed_request('/api/v3/account')
    
    if response.status_code == 200:
        data = response.json()
        print("SUCCESS: Account info retrieved")
        
        # Find USDT balance
        for balance in data['balances']:
            if balance['asset'] == 'USDT':
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                print(f"Spot USDT Balance:")
                print(f"  Free: {free:.2f} USDT")
                print(f"  Locked: {locked:.2f} USDT")
                print(f"  Total: {total:.2f} USDT")
                return total
        
        print("No USDT balance found in spot wallet")
        return 0.0
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
        return None

def get_futures_balance():
    """Get futures account balance"""
    print("\nGetting futures balance...")
    response = make_signed_request('/fapi/v2/balance')
    
    if response.status_code == 200:
        data = response.json()
        print("SUCCESS: Futures balance retrieved")
        
        for asset in data:
            if asset['asset'] == 'USDT':
                balance = float(asset['balance'])
                available = float(asset['availableBalance'])
                print(f"Futures USDT Balance:")
                print(f"  Balance: {balance:.2f} USDT")
                print(f"  Available: {available:.2f} USDT")
                return balance
        
        print("No USDT balance found in futures wallet")
        return 0.0
    else:
        print(f"ERROR: {response.status_code} - {response.text}")
        return None

def universal_transfer(transfer_type, asset, amount):
    """Execute universal transfer"""
    print(f"\nExecuting transfer:")
    print(f"  Type: {transfer_type}")
    print(f"  Asset: {asset}")
    print(f"  Amount: {amount}")
    
    params = {
        'type': transfer_type,
        'asset': asset,
        'amount': str(amount)
    }
    
    response = make_signed_request('/sapi/v1/asset/transfer', params, 'POST')
    
    if response.status_code == 200:
        data = response.json()
        print("SUCCESS: Transfer completed")
        print(f"  Transaction ID: {data.get('tranId')}")
        return True
    else:
        print(f"ERROR: Transfer failed")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def main():
    """Execute strategic transfers"""
    print("="*60)
    print("BINANCE STRATEGIC TRANSFER EXECUTOR (Direct API)")
    print("="*60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Mode: MAINNET (LIVE TRADING)")
    
    # Get initial balances
    print("\n" + "="*40)
    print("INITIAL BALANCES")
    print("="*40)
    
    spot_balance = get_account_info()
    futures_balance = get_futures_balance()
    
    if spot_balance is None or futures_balance is None:
        print("ERROR: Could not retrieve balances")
        return 1
    
    print(f"\nBalance Summary:")
    print(f"  Spot: {spot_balance:.2f} USDT")
    print(f"  Futures: {futures_balance:.2f} USDT")
    print(f"  Total: {spot_balance + futures_balance:.2f} USDT")
    
    # Check if we have sufficient funds
    if spot_balance < 2000:
        print(f"\nWARNING: Insufficient funds for full strategy")
        print(f"  Available: {spot_balance:.2f} USDT")
        print(f"  Required: 2000.00 USDT")
        
        if spot_balance < 100:
            print("ERROR: Cannot proceed with transfers")
            return 1
        
        print("INFO: Will adjust transfer amounts")
    
    # Define transfers based on available balance
    transfers = []
    
    if spot_balance >= 2000:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 1000, 'Transfer 1000 USDT to Futures for trading'),
            # Note: For Earn wallet, funds typically need to go to Funding first
            ('MAIN_TO_FUNDING', 'USDT', 1000, 'Transfer 1000 USDT to Funding for Earn products')
        ]
    elif spot_balance >= 1000:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 500, 'Transfer 500 USDT to Futures for trading'),
            ('MAIN_TO_FUNDING', 'USDT', 500, 'Transfer 500 USDT to Funding for Earn products')
        ]
    elif spot_balance >= 200:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 100, 'Transfer 100 USDT to Futures for trading'),
            ('MAIN_TO_FUNDING', 'USDT', 100, 'Transfer 100 USDT to Funding for Earn products')
        ]
    else:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 50, 'Test transfer 50 USDT to Futures'),
            ('MAIN_TO_FUNDING', 'USDT', 50, 'Test transfer 50 USDT to Funding')
        ]
    
    # Execute transfers
    print("\n" + "="*40)
    print("EXECUTING TRANSFERS")
    print("="*40)
    
    successful = []
    failed = []
    
    for transfer_type, asset, amount, description in transfers:
        print(f"\n{'-'*30}")
        print(description)
        
        success = universal_transfer(transfer_type, asset, amount)
        
        if success:
            successful.append((transfer_type, asset, amount, description))
        else:
            failed.append((transfer_type, asset, amount, description))
        
        # Wait between transfers
        time.sleep(2)
    
    # Get final balances
    print("\n" + "="*40)
    print("FINAL BALANCES")
    print("="*40)
    
    final_spot = get_account_info()
    final_futures = get_futures_balance()
    
    if final_spot is not None and final_futures is not None:
        print(f"\nBalance Summary:")
        print(f"  Spot: {final_spot:.2f} USDT")
        print(f"  Futures: {final_futures:.2f} USDT")
        print(f"  Total: {final_spot + final_futures:.2f} USDT")
        
        print(f"\nBalance Changes:")
        print(f"  Spot: {final_spot - spot_balance:+.2f} USDT")
        print(f"  Futures: {final_futures - futures_balance:+.2f} USDT")
    
    # Generate report
    print("\n" + "="*40)
    print("EXECUTION REPORT")
    print("="*40)
    
    print(f"\nTransfers attempted: {len(transfers)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\nSuccessful transfers:")
        for _, asset, amount, desc in successful:
            print(f"  - {desc}: {amount} {asset}")
    
    if failed:
        print(f"\nFailed transfers:")
        for _, asset, amount, desc in failed:
            print(f"  - {desc}: {amount} {asset}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'initial_balances': {
            'spot': spot_balance,
            'futures': futures_balance
        },
        'final_balances': {
            'spot': final_spot,
            'futures': final_futures
        } if final_spot is not None else None,
        'successful_transfers': successful,
        'failed_transfers': failed,
        'success_rate': len(successful) / len(transfers) * 100 if transfers else 0
    }
    
    filename = f"transfer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {filename}")
    
    success_rate = len(successful) / len(transfers) * 100 if transfers else 0
    print(f"\nSUCCESS RATE: {success_rate:.1f}%")
    print("="*40)
    
    return 0 if not failed else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)