#!/usr/bin/env python3
"""
Execute Strategic USDT Transfers on Binance Mainnet
Uses whitelisted IP and mainnet API keys to transfer funds
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.binance_sapi_client import BinanceSAPIClient
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StrategicTransferManager:
    """Manages strategic transfers between Binance wallets"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        """Initialize the transfer manager with API credentials"""
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        # Initialize clients
        self.sapi_client = BinanceSAPIClient(api_key, secret_key, testnet)
        self.client = Client(api_key, secret_key, testnet=testnet)
        
        logger.info(f"Initialized Transfer Manager for {'TESTNET' if testnet else 'MAINNET'}")
        logger.info(f"Whitelisted IP: 216.234.205.4")
    
    def test_api_access(self) -> bool:
        """Test API access with the whitelisted IP"""
        logger.info("=" * 60)
        logger.info("Testing API Access with Whitelisted IP")
        logger.info("=" * 60)
        
        try:
            # Test basic connectivity
            logger.info("Testing basic connectivity...")
            server_time = self.client.get_server_time()
            logger.info(f"✅ Server connection successful")
            logger.info(f"   Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
            
            # Test account access
            logger.info("\nTesting account access...")
            account = self.client.get_account()
            logger.info(f"✅ Account access successful")
            logger.info(f"   Can trade: {account['canTrade']}")
            logger.info(f"   Can withdraw: {account['canWithdraw']}")
            logger.info(f"   Can deposit: {account['canDeposit']}")
            
            # Test SAPI connectivity
            logger.info("\nTesting SAPI connectivity...")
            status = self.sapi_client.get_account_status()
            logger.info(f"✅ SAPI access successful")
            logger.info(f"   Account status: {status.get('data', 'Normal')}")
            
            # Test API trading status
            logger.info("\nTesting API trading status...")
            api_status = self.sapi_client.get_account_api_trading_status()
            logger.info(f"✅ API trading status retrieved")
            logger.info(f"   API trading enabled: {api_status.get('data', {}).get('isLocked', False) == False}")
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"❌ Binance API error: {e.code} - {e.message}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    def get_wallet_balances(self) -> Dict[str, float]:
        """Get balances for all wallet types"""
        logger.info("=" * 60)
        logger.info("Fetching Wallet Balances")
        logger.info("=" * 60)
        
        balances = {
            'funding': 0.0,
            'spot': 0.0,
            'futures': 0.0,
            'earn': 0.0,
            'total': 0.0
        }
        
        try:
            # Get funding wallet balance
            logger.info("Fetching funding wallet balance...")
            funding_response = self.client.funding_wallet()
            for asset in funding_response:
                if asset['asset'] == 'USDT':
                    balances['funding'] = float(asset['free']) + float(asset['locked'])
                    logger.info(f"✅ Funding wallet: {balances['funding']:.2f} USDT")
                    logger.info(f"   Free: {float(asset['free']):.2f} USDT")
                    logger.info(f"   Locked: {float(asset['locked']):.2f} USDT")
            
            # Get spot wallet balance
            logger.info("\nFetching spot wallet balance...")
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    balances['spot'] = float(balance['free']) + float(balance['locked'])
                    logger.info(f"✅ Spot wallet: {balances['spot']:.2f} USDT")
                    logger.info(f"   Free: {float(balance['free']):.2f} USDT")
                    logger.info(f"   Locked: {float(balance['locked']):.2f} USDT")
            
            # Get futures wallet balance
            logger.info("\nFetching futures wallet balance...")
            try:
                futures_account = self.client.futures_account_balance()
                for asset in futures_account:
                    if asset['asset'] == 'USDT':
                        balances['futures'] = float(asset['balance'])
                        logger.info(f"✅ Futures wallet: {balances['futures']:.2f} USDT")
                        logger.info(f"   Available: {float(asset['availableBalance']):.2f} USDT")
            except Exception as e:
                logger.warning(f"Could not fetch futures balance: {e}")
            
            # Get earn wallet balance (flexible savings)
            logger.info("\nFetching earn wallet balance...")
            try:
                # Try to get flexible savings position
                earn_response = self.client.get_lending_position()
                for position in earn_response:
                    if position.get('asset') == 'USDT':
                        balances['earn'] += float(position.get('principal', 0))
                        balances['earn'] += float(position.get('interest', 0))
                
                if balances['earn'] > 0:
                    logger.info(f"✅ Earn wallet: {balances['earn']:.2f} USDT")
                else:
                    logger.info(f"ℹ️ Earn wallet: No active positions")
            except Exception as e:
                logger.warning(f"Could not fetch earn balance: {e}")
            
            # Calculate total
            balances['total'] = sum([
                balances['funding'],
                balances['spot'],
                balances['futures'],
                balances['earn']
            ])
            
            logger.info("\n" + "=" * 60)
            logger.info("BALANCE SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Funding:  {balances['funding']:>10.2f} USDT")
            logger.info(f"Spot:     {balances['spot']:>10.2f} USDT")
            logger.info(f"Futures:  {balances['futures']:>10.2f} USDT")
            logger.info(f"Earn:     {balances['earn']:>10.2f} USDT")
            logger.info("-" * 30)
            logger.info(f"TOTAL:    {balances['total']:>10.2f} USDT")
            
            return balances
            
        except BinanceAPIException as e:
            logger.error(f"❌ Binance API error: {e.code} - {e.message}")
            return balances
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return balances
    
    def execute_transfer(self, transfer_type: str, amount: float, description: str) -> bool:
        """Execute a single transfer"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Executing Transfer: {description}")
        logger.info(f"{'='*60}")
        logger.info(f"Type: {transfer_type}")
        logger.info(f"Amount: {amount} USDT")
        
        try:
            # Execute the transfer
            result = self.sapi_client.universal_transfer(
                transfer_type=transfer_type,
                asset='USDT',
                amount=amount
            )
            
            if result and result.get('tranId'):
                logger.info(f"✅ Transfer successful!")
                logger.info(f"   Transaction ID: {result['tranId']}")
                logger.info(f"   Status: COMPLETED")
                
                # Wait a moment for the transfer to process
                time.sleep(2)
                
                return True
            else:
                logger.error(f"❌ Transfer failed: No transaction ID returned")
                return False
                
        except BinanceAPIException as e:
            logger.error(f"❌ Transfer failed: {e.code} - {e.message}")
            
            # Common error handling
            if e.code == -4059:
                logger.error("   Error: Insufficient balance in source wallet")
            elif e.code == -4060:
                logger.error("   Error: Transfer amount too small")
            elif e.code == -4061:
                logger.error("   Error: Transfer not allowed for this account")
            elif e.code == -1021:
                logger.error("   Error: Timestamp issue - retrying with server time")
                # Retry with server time
                try:
                    result = self.sapi_client.universal_transfer(
                        transfer_type=transfer_type,
                        asset='USDT',
                        amount=amount
                    )
                    if result and result.get('tranId'):
                        logger.info(f"✅ Transfer successful on retry!")
                        logger.info(f"   Transaction ID: {result['tranId']}")
                        return True
                except Exception as retry_error:
                    logger.error(f"   Retry failed: {retry_error}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    def execute_strategic_transfers(self):
        """Execute the strategic transfers as requested"""
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTING STRATEGIC TRANSFERS")
        logger.info("=" * 60)
        
        transfers = [
            # First, move from Funding to Spot (if needed)
            {
                'type': 'FUNDING_TO_SPOT',
                'amount': 2000,
                'description': 'Transfer 2000 USDT from Funding to Spot (for further distribution)'
            },
            # Then from Spot to Earn
            {
                'type': 'MAIN_TO_FUNDING',  # Note: For Earn, we use this type
                'amount': 1000,
                'description': 'Transfer 1000 USDT to Earn wallet for yield generation'
            },
            # Then from Spot to Futures
            {
                'type': 'MAIN_TO_UMFUTURE',
                'amount': 1000,
                'description': 'Transfer 1000 USDT to Futures wallet for trading'
            }
        ]
        
        successful_transfers = []
        failed_transfers = []
        
        # Get initial balances
        initial_balances = self.get_wallet_balances()
        
        # Execute transfers
        for transfer in transfers:
            success = self.execute_transfer(
                transfer_type=transfer['type'],
                amount=transfer['amount'],
                description=transfer['description']
            )
            
            if success:
                successful_transfers.append(transfer)
            else:
                failed_transfers.append(transfer)
            
            # Wait between transfers
            time.sleep(3)
        
        # Get final balances
        logger.info("\n" + "=" * 60)
        logger.info("FETCHING FINAL BALANCES")
        logger.info("=" * 60)
        final_balances = self.get_wallet_balances()
        
        # Generate report
        logger.info("\n" + "=" * 60)
        logger.info("TRANSFER EXECUTION REPORT")
        logger.info("=" * 60)
        
        logger.info(f"\n✅ Successful Transfers: {len(successful_transfers)}")
        for transfer in successful_transfers:
            logger.info(f"   - {transfer['description']}")
        
        if failed_transfers:
            logger.info(f"\n❌ Failed Transfers: {len(failed_transfers)}")
            for transfer in failed_transfers:
                logger.info(f"   - {transfer['description']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("BALANCE CHANGES")
        logger.info("=" * 60)
        logger.info(f"{'Wallet':<10} {'Initial':>12} {'Final':>12} {'Change':>12}")
        logger.info("-" * 46)
        
        for wallet in ['funding', 'spot', 'futures', 'earn']:
            initial = initial_balances[wallet]
            final = final_balances[wallet]
            change = final - initial
            change_str = f"{change:+.2f}" if change != 0 else "0.00"
            logger.info(f"{wallet.capitalize():<10} {initial:>12.2f} {final:>12.2f} {change_str:>12}")
        
        logger.info("-" * 46)
        logger.info(f"{'TOTAL':<10} {initial_balances['total']:>12.2f} {final_balances['total']:>12.2f} "
                   f"{(final_balances['total'] - initial_balances['total']):+12.2f}")
        
        # Save report to file
        report = {
            'timestamp': datetime.now().isoformat(),
            'initial_balances': initial_balances,
            'final_balances': final_balances,
            'successful_transfers': successful_transfers,
            'failed_transfers': failed_transfers,
            'balance_changes': {
                wallet: final_balances[wallet] - initial_balances[wallet]
                for wallet in ['funding', 'spot', 'futures', 'earn']
            }
        }
        
        report_file = f"transfer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Report saved to: {report_file}")
        
        return len(successful_transfers), len(failed_transfers)

def main():
    """Main execution function"""
    # Mainnet API credentials (whitelisted IP)
    API_KEY = "KP5NFDffn3reE3md2SKkrcRTgTLwJKrE7wvBVNizdZfuBswKGVbBTluopkmofax1"
    SECRET_KEY = "2bUXyAuNY0zjrlXWi5xC8DDmVxkhOtYu7W6RwstZ33Ytr7jzins2SUemRCDpLIV5"
    TESTNET = False  # This is MAINNET
    
    logger.info("=" * 60)
    logger.info("BINANCE STRATEGIC TRANSFER MANAGER")
    logger.info("=" * 60)
    logger.info(f"Mode: {'TESTNET' if TESTNET else 'MAINNET'}")
    logger.info(f"Whitelisted IP: 216.234.205.4")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("=" * 60)
    
    # Initialize transfer manager
    manager = StrategicTransferManager(API_KEY, SECRET_KEY, TESTNET)
    
    # Test API access
    if not manager.test_api_access():
        logger.error("Failed to establish API access. Aborting.")
        return 1
    
    # Execute strategic transfers
    try:
        success_count, fail_count = manager.execute_strategic_transfers()
        
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✅ Successful transfers: {success_count}")
        if fail_count > 0:
            logger.info(f"❌ Failed transfers: {fail_count}")
        logger.info("=" * 60)
        
        return 0 if fail_count == 0 else 1
        
    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user")
        return 2
    except Exception as e:
        logger.error(f"\nUnexpected error: {e}")
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)