#!/usr/bin/env python3
"""
Test mainnet API access and get wallet balances
"""

from binance.client import Client
import json

API_KEY = 'KP5NFDffn3reE3md2SKkrcRTgTLwJKrE7wvBVNizdZfuBswKGVbBTluopkmofax1'
SECRET_KEY = '2bUXyAuNY0zjrlXWi5xC8DDmVxkhOtYu7W6RwstZ33Ytr7jzins2SUemRCDpLIV5'

def main():
    client = Client(API_KEY, SECRET_KEY, testnet=False)
    
    try:
        # Test basic connectivity
        print('Testing basic connectivity...')
        server_time = client.get_server_time()
        print('SUCCESS: Server connected')
        
        # Get account info
        print('\nGetting account info...')
        account = client.get_account()
        print('SUCCESS: Account access successful')
        print(f'   Can trade: {account["canTrade"]}')
        print(f'   Can withdraw: {account["canWithdraw"]}')
        print(f'   Can deposit: {account["canDeposit"]}')
        
        # Get funding wallet
        print('\nGetting funding wallet...')
        funding = client.funding_wallet()
        for asset in funding:
            if asset['asset'] == 'USDT':
                print('SUCCESS: Funding wallet USDT:')
                print(f'   Free: {asset["free"]} USDT')
                print(f'   Locked: {asset["locked"]} USDT')
                print(f'   Total: {float(asset["free"]) + float(asset["locked"]):.2f} USDT')
        
        # Get spot balances
        print('\nGetting spot balances...')
        usdt_found = False
        for balance in account['balances']:
            if balance['asset'] == 'USDT':
                total = float(balance['free']) + float(balance['locked'])
                if total > 0:
                    usdt_found = True
                    print('SUCCESS: Spot wallet USDT:')
                    print(f'   Free: {balance["free"]} USDT')
                    print(f'   Locked: {balance["locked"]} USDT')
                    print(f'   Total: {total:.2f} USDT')
        
        if not usdt_found:
            print('   No USDT in spot wallet')
        
        # Try to get futures balance
        print('\nGetting futures balances...')
        try:
            futures = client.futures_account_balance()
            for asset in futures:
                if asset['asset'] == 'USDT':
                    print('SUCCESS: Futures wallet USDT:')
                    print(f'   Balance: {asset["balance"]} USDT')
                    print(f'   Available: {asset["availableBalance"]} USDT')
        except Exception as e:
            print(f'   Could not get futures balance: {e}')
        
        print('\n' + '='*50)
        print('API ACCESS TEST SUCCESSFUL')
        print('='*50)
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()