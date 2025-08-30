#!/usr/bin/env python3
"""
Execute Strategic USDT Transfers using Binance Python Client
Final implementation for mainnet transfers
"""

import time
import json
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Mainnet API credentials (whitelisted IP: 216.234.205.4)
API_KEY = 'KP5NFDffn3reE3md2SKkrcRTgTLwJKrE7wvBVNizdZfuBswKGVbBTluopkmofax1'
SECRET_KEY = '2bUXyAuNY0zjrlXWi5xC8DDmVxkhOtYu7W6RwstZ33Ytr7jzins2SUemRCDpLIV5'

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"{title}")
    print("="*60)

def get_balances_summary(client):
    """Get comprehensive balance summary from all wallets"""
    balances = {
        'spot': {'free': 0.0, 'locked': 0.0, 'total': 0.0},
        'futures': {'balance': 0.0, 'available': 0.0},
        'cross_margin': {'free': 0.0, 'locked': 0.0, 'total': 0.0},
        'isolated_margin': {'free': 0.0, 'locked': 0.0, 'total': 0.0}
    }
    
    try:
        # Get Spot balance
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == 'USDT':
                balances['spot']['free'] = float(balance['free'])
                balances['spot']['locked'] = float(balance['locked'])
                balances['spot']['total'] = balances['spot']['free'] + balances['spot']['locked']
                break
        
        # Get Futures balance
        try:
            futures_account = client.futures_account_balance()
            for asset in futures_account:
                if asset['asset'] == 'USDT':
                    balances['futures']['balance'] = float(asset['balance'])
                    balances['futures']['available'] = float(asset['availableBalance'])
                    break
        except Exception as e:
            print(f"   Warning: Could not fetch futures balance: {e}")
        
        # Get Cross Margin balance
        try:
            margin_account = client.get_margin_account()
            for balance in margin_account['userAssets']:
                if balance['asset'] == 'USDT':
                    balances['cross_margin']['free'] = float(balance['free'])
                    balances['cross_margin']['locked'] = float(balance['locked'])
                    balances['cross_margin']['total'] = balances['cross_margin']['free'] + balances['cross_margin']['locked']
                    break
        except Exception as e:
            print(f"   Warning: Could not fetch margin balance: {e}")
        
    except Exception as e:
        print(f"Error fetching balances: {e}")
    
    # Print summary
    print(f"\nSpot:          {balances['spot']['total']:>12.2f} USDT")
    print(f"Futures:       {balances['futures']['balance']:>12.2f} USDT")
    print(f"Cross Margin:  {balances['cross_margin']['total']:>12.2f} USDT")
    
    total = (balances['spot']['total'] + 
             balances['futures']['balance'] + 
             balances['cross_margin']['total'])
    print(f"{'='*30}")
    print(f"TOTAL:         {total:>12.2f} USDT")
    
    return balances

def execute_transfer(client, transfer_type, asset, amount, description):
    """Execute a universal transfer"""
    print(f"\n{description}")
    print(f"Type: {transfer_type}")
    print(f"Amount: {amount} {asset}")
    
    try:
        result = client.universal_transfer(
            type=transfer_type,
            asset=asset,
            amount=str(amount)
        )
        
        if 'tranId' in result:
            print(f"SUCCESS: Transfer completed")
            print(f"   Transaction ID: {result['tranId']}")
            return True
        else:
            print(f"FAILED: No transaction ID returned")
            print(f"   Response: {result}")
            return False
            
    except BinanceAPIException as e:
        print(f"FAILED: Binance API error")
        print(f"   Code: {e.code}")
        print(f"   Message: {e.message}")
        
        # Provide specific error guidance
        if e.code == -4059:
            print("   -> Insufficient balance in source wallet")
        elif e.code == -4060:
            print("   -> Transfer amount too small (minimum required)")
        elif e.code == -4061:
            print("   -> Transfer not allowed for this account type")
        elif e.code == -1102:
            print("   -> Invalid parameter - check transfer type")
        elif e.code == -5002:
            print("   -> Asset transfer not supported")
        elif e.code == -1021:
            print("   -> Timestamp synchronization issue")
        
        return False
        
    except Exception as e:
        print(f"FAILED: Unexpected error")
        print(f"   Error: {e}")
        return False

def main():
    """Execute strategic transfers"""
    print_section("BINANCE MAINNET STRATEGIC TRANSFER EXECUTOR")
    print(f"Timestamp: {datetime.now()}")
    print(f"Whitelisted IP: 216.234.205.4")
    print(f"Mode: MAINNET (LIVE TRADING)")
    
    # Initialize client
    client = Client(API_KEY, SECRET_KEY, testnet=False)
    
    # Test connectivity
    print("\nTesting API connectivity...")
    try:
        server_time = client.get_server_time()
        print("SUCCESS: Connected successfully")
        print(f"   Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")
        return 1
    
    # Get initial balances
    print_section("INITIAL WALLET BALANCES")
    initial_balances = get_balances_summary(client)
    
    # Check available funds
    available_usdt = initial_balances['spot']['total']
    
    if available_usdt < 2000:
        print(f"\nWARNING: Insufficient USDT in spot wallet")
        print(f"   Available: {available_usdt:.2f} USDT")
        print(f"   Required: 2000.00 USDT")
        
        if available_usdt < 100:
            print("ERROR: Cannot proceed with transfers")
            return 1
        else:
            print("INFO: Adjusting transfer amounts...")
    
    # Define transfer strategy
    transfers = []
    
    if available_usdt >= 2000:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 1000, 'Transfer 1000 USDT to Futures wallet for trading'),
            ('MAIN_TO_FUNDING', 'USDT', 1000, 'Transfer 1000 USDT to Funding wallet (for Earn)')
        ]
    elif available_usdt >= 1000:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 500, 'Transfer 500 USDT to Futures wallet for trading'),
            ('MAIN_TO_FUNDING', 'USDT', 500, 'Transfer 500 USDT to Funding wallet (for Earn)')
        ]
    elif available_usdt >= 200:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 100, 'Transfer 100 USDT to Futures wallet for trading'),
            ('MAIN_TO_FUNDING', 'USDT', 100, 'Transfer 100 USDT to Funding wallet (for Earn)')
        ]
    else:
        transfers = [
            ('MAIN_TO_UMFUTURE', 'USDT', 50, 'Test transfer 50 USDT to Futures wallet'),
            ('MAIN_TO_FUNDING', 'USDT', 50, 'Test transfer 50 USDT to Funding wallet')
        ]
    
    # Execute transfers
    print_section("EXECUTING STRATEGIC TRANSFERS")
    successful_transfers = []
    failed_transfers = []
    
    for transfer_type, asset, amount, description in transfers:
        print(f"\n{'='*40}")
        success = execute_transfer(client, transfer_type, asset, amount, description)
        
        if success:
            successful_transfers.append((transfer_type, asset, amount, description))
            print("SUCCESS: Transfer completed successfully")
        else:
            failed_transfers.append((transfer_type, asset, amount, description))
            print("FAILED: Transfer failed")
        
        # Wait between transfers
        time.sleep(3)
    
    # Get final balances
    print_section("FINAL WALLET BALANCES")
    final_balances = get_balances_summary(client)
    
    # Generate execution report
    print_section("TRANSFER EXECUTION REPORT")
    print(f"\nSummary:")
    print(f"   Total transfers attempted: {len(transfers)}")
    print(f"   Successful: {len(successful_transfers)}")
    print(f"   Failed: {len(failed_transfers)}")
    
    if successful_transfers:
        print(f"\nSuccessful Transfers:")
        for transfer_type, asset, amount, description in successful_transfers:
            print(f"   - {description}")
            print(f"     Amount: {amount} {asset}")
    
    if failed_transfers:
        print(f"\nFailed Transfers:")
        for transfer_type, asset, amount, description in failed_transfers:
            print(f"   - {description}")
            print(f"     Amount: {amount} {asset}")
    
    # Balance changes
    print(f"\nBalance Changes:")
    spot_change = final_balances['spot']['total'] - initial_balances['spot']['total']
    futures_change = final_balances['futures']['balance'] - initial_balances['futures']['balance']
    margin_change = final_balances['cross_margin']['total'] - initial_balances['cross_margin']['total']
    
    print(f"   Spot:         {spot_change:+10.2f} USDT")
    print(f"   Futures:      {futures_change:+10.2f} USDT")
    print(f"   Cross Margin: {margin_change:+10.2f} USDT")
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'execution_summary': {
            'total_attempted': len(transfers),
            'successful': len(successful_transfers),
            'failed': len(failed_transfers)
        },
        'initial_balances': initial_balances,
        'final_balances': final_balances,
        'balance_changes': {
            'spot': spot_change,
            'futures': futures_change,
            'cross_margin': margin_change
        },
        'successful_transfers': successful_transfers,
        'failed_transfers': failed_transfers
    }
    
    report_filename = f"strategic_transfer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_filename}")
    
    print_section("EXECUTION COMPLETE")
    success_rate = len(successful_transfers) / len(transfers) * 100 if transfers else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    return 0 if len(failed_transfers) == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)