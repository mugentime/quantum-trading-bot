#!/usr/bin/env python3
"""
Execute USDT transfers on Binance Mainnet using official client
"""

import time
import json
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Mainnet API credentials (whitelisted IP: 216.234.205.4)
API_KEY = 'KP5NFDffn3reE3md2SKkrcRTgTLwJKrE7wvBVNizdZfuBswKGVbBTluopkmofax1'
SECRET_KEY = '2bUXyAuNY0zjrlXWi5xC8DDmVxkhOtYu7W6RwstZ33Ytr7jzins2SUemRCDpLIV5'

def get_all_balances(client):
    """Get balances from all wallet types"""
    balances = {
        'funding': {'free': 0.0, 'locked': 0.0, 'total': 0.0},
        'spot': {'free': 0.0, 'locked': 0.0, 'total': 0.0},
        'futures': {'balance': 0.0, 'available': 0.0},
        'earn': {'total': 0.0}
    }
    
    print("\n" + "="*60)
    print("FETCHING WALLET BALANCES")
    print("="*60)
    
    # 1. Get Spot wallet balance
    try:
        print("\n1. Spot Wallet:")
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == 'USDT':
                balances['spot']['free'] = float(balance['free'])
                balances['spot']['locked'] = float(balance['locked'])
                balances['spot']['total'] = balances['spot']['free'] + balances['spot']['locked']
                print(f"   Free: {balances['spot']['free']:.2f} USDT")
                print(f"   Locked: {balances['spot']['locked']:.2f} USDT")
                print(f"   Total: {balances['spot']['total']:.2f} USDT")
                break
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Get Funding wallet balance
    try:
        print("\n2. Funding Wallet:")
        # Try different methods to get funding wallet
        
        # Method 1: Using funding_wallet
        try:
            funding = client.funding_wallet()
            if funding:
                for asset in funding:
                    if asset['asset'] == 'USDT':
                        balances['funding']['free'] = float(asset['free'])
                        balances['funding']['locked'] = float(asset['locked'])
                        balances['funding']['total'] = balances['funding']['free'] + balances['funding']['locked']
                        print(f"   Free: {balances['funding']['free']:.2f} USDT")
                        print(f"   Locked: {balances['funding']['locked']:.2f} USDT")
                        print(f"   Total: {balances['funding']['total']:.2f} USDT")
                        break
            else:
                print("   No funding wallet data returned")
        except Exception as e1:
            print(f"   Method 1 failed: {e1}")
            
            # Method 2: Using get_asset_balance with wallet type
            try:
                result = client.get_asset_balance(asset='USDT', recvWindow=60000)
                if result:
                    print(f"   Asset balance method: {result}")
            except Exception as e2:
                print(f"   Method 2 failed: {e2}")
                
    except Exception as e:
        print(f"   Error accessing funding wallet: {e}")
    
    # 3. Get Futures wallet balance
    try:
        print("\n3. Futures Wallet:")
        futures = client.futures_account_balance()
        for asset in futures:
            if asset['asset'] == 'USDT':
                balances['futures']['balance'] = float(asset['balance'])
                balances['futures']['available'] = float(asset['availableBalance'])
                print(f"   Balance: {balances['futures']['balance']:.2f} USDT")
                print(f"   Available: {balances['futures']['available']:.2f} USDT")
                break
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Try to get Earn wallet balance
    try:
        print("\n4. Earn Wallet:")
        # Try to get flexible savings
        try:
            savings = client.get_lending_position()
            if savings:
                for position in savings:
                    if position.get('asset') == 'USDT':
                        balances['earn']['total'] += float(position.get('principal', 0))
                        balances['earn']['total'] += float(position.get('interest', 0))
                if balances['earn']['total'] > 0:
                    print(f"   Total in Earn: {balances['earn']['total']:.2f} USDT")
                else:
                    print("   No active earn positions")
            else:
                print("   No earn positions found")
        except Exception as e:
            print(f"   Could not access earn wallet: {e}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Calculate totals
    total_balance = (
        balances['spot']['total'] + 
        balances['funding']['total'] + 
        balances['futures']['balance'] + 
        balances['earn']['total']
    )
    
    print("\n" + "="*60)
    print("BALANCE SUMMARY")
    print("="*60)
    print(f"Spot:     {balances['spot']['total']:>10.2f} USDT")
    print(f"Funding:  {balances['funding']['total']:>10.2f} USDT")
    print(f"Futures:  {balances['futures']['balance']:>10.2f} USDT")
    print(f"Earn:     {balances['earn']['total']:>10.2f} USDT")
    print("-"*30)
    print(f"TOTAL:    {total_balance:>10.2f} USDT")
    
    return balances

def execute_universal_transfer(client, transfer_type, amount):
    """Execute a universal transfer between wallets"""
    try:
        print(f"\nExecuting transfer: {transfer_type} - {amount} USDT")
        
        # Use the universal_transfer method
        result = client.universal_transfer(
            type=transfer_type,
            asset='USDT',
            amount=amount
        )
        
        if result and 'tranId' in result:
            print(f"SUCCESS: Transfer completed")
            print(f"   Transaction ID: {result['tranId']}")
            return True
        else:
            print(f"FAILED: No transaction ID returned")
            return False
            
    except BinanceAPIException as e:
        print(f"FAILED: Binance API error")
        print(f"   Code: {e.code}")
        print(f"   Message: {e.message}")
        
        # Common error codes
        if e.code == -4059:
            print("   Reason: Insufficient balance in source wallet")
        elif e.code == -4060:
            print("   Reason: Transfer amount too small")
        elif e.code == -4061:
            print("   Reason: Transfer not allowed for this account")
        elif e.code == -1102:
            print("   Reason: Invalid parameter")
        elif e.code == -5002:
            print("   Reason: Asset not supported")
        
        return False
        
    except Exception as e:
        print(f"FAILED: Unexpected error - {e}")
        return False

def main():
    """Main execution function"""
    print("="*60)
    print("BINANCE MAINNET TRANSFER EXECUTOR")
    print("="*60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Whitelisted IP: 216.234.205.4")
    print(f"Mode: MAINNET")
    print("="*60)
    
    # Initialize client
    client = Client(API_KEY, SECRET_KEY, testnet=False)
    
    # Test connectivity
    print("\nTesting API connectivity...")
    try:
        server_time = client.get_server_time()
        print("SUCCESS: API connection established")
        print(f"Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
    except Exception as e:
        print(f"FAILED: Cannot connect to API - {e}")
        return 1
    
    # Get initial balances
    print("\nStep 1: Getting initial balances")
    initial_balances = get_all_balances(client)
    
    # Check if we have funds in spot (main) wallet
    if initial_balances['spot']['total'] < 2000:
        print(f"\nWARNING: Insufficient funds in Spot wallet")
        print(f"   Available: {initial_balances['spot']['total']:.2f} USDT")
        print(f"   Required: 2000.00 USDT")
        print("\nNote: The 6,624.89 USDT mentioned might be in a different wallet")
        print("      or the funding wallet API might have different access requirements.")
    
    # Execute transfers
    print("\n" + "="*60)
    print("EXECUTING STRATEGIC TRANSFERS")
    print("="*60)
    
    transfers_to_execute = []
    
    # Determine which transfers we can execute based on available balance
    if initial_balances['spot']['total'] >= 2000:
        transfers_to_execute = [
            ('MAIN_TO_UMFUTURE', 1000, 'Transfer to Futures wallet for trading'),
            ('MAIN_TO_FUNDING', 1000, 'Transfer to Earn wallet for yield')
        ]
    elif initial_balances['spot']['total'] >= 1000:
        print("\nAdjusting strategy due to limited funds...")
        transfers_to_execute = [
            ('MAIN_TO_UMFUTURE', 500, 'Transfer to Futures wallet for trading'),
            ('MAIN_TO_FUNDING', 500, 'Transfer to Earn wallet for yield')
        ]
    elif initial_balances['spot']['total'] >= 100:
        print("\nExecuting minimal test transfers...")
        transfers_to_execute = [
            ('MAIN_TO_UMFUTURE', 50, 'Test transfer to Futures'),
            ('MAIN_TO_FUNDING', 50, 'Test transfer to Earn')
        ]
    else:
        print("\nInsufficient funds for any transfers")
        
    # Execute transfers
    successful = 0
    failed = 0
    
    for transfer_type, amount, description in transfers_to_execute:
        print(f"\n{description}...")
        if execute_universal_transfer(client, transfer_type, amount):
            successful += 1
        else:
            failed += 1
        time.sleep(2)  # Wait between transfers
    
    # Get final balances
    if transfers_to_execute:
        print("\nStep 2: Getting final balances")
        final_balances = get_all_balances(client)
        
        # Generate report
        print("\n" + "="*60)
        print("TRANSFER EXECUTION REPORT")
        print("="*60)
        print(f"Successful transfers: {successful}")
        print(f"Failed transfers: {failed}")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'initial_balances': initial_balances,
            'final_balances': final_balances if transfers_to_execute else None,
            'transfers_executed': len(transfers_to_execute),
            'successful': successful,
            'failed': failed
        }
        
        report_file = f"mainnet_transfer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {report_file}")
    
    print("\n" + "="*60)
    print("EXECUTION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()