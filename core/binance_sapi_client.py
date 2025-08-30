#!/usr/bin/env python3
"""
Binance SAPI Client - Correct signature implementation for SAPI endpoints
Fixes universal transfer and other SAPI endpoint issues
"""

import os
import time
import hmac
import hashlib
import json
import requests
import logging
from urllib.parse import urlencode
from typing import Dict, Any, Optional, Union
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceSAPIClient:
    """
    Binance SAPI client with correct signature generation
    Handles universal transfers and other SAPI endpoints properly
    """
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        # Binance URLs
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
        
        # Initialize official client for comparison/fallback
        self.client = Client(api_key, secret_key, testnet=testnet)
        
        logger.info(f"Initialized SAPI client for {'TESTNET' if testnet else 'MAINNET'}")
    
    def _get_server_time(self) -> int:
        """Get Binance server time for timestamp synchronization"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/time", timeout=10)
            response.raise_for_status()
            return response.json()['serverTime']
        except Exception as e:
            logger.warning(f"Could not get server time: {e}, using local time")
            return int(time.time() * 1000)
    
    def _generate_signature(self, query_string: str) -> str:
        """
        Generate HMAC SHA256 signature for Binance API
        Uses the exact same method as the official documentation
        """
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _prepare_signed_request(self, params: Dict[str, Any], use_server_time: bool = True) -> Dict[str, Any]:
        """
        Prepare parameters for a signed request
        """
        # Add timestamp if not present
        if 'timestamp' not in params:
            if use_server_time:
                params['timestamp'] = self._get_server_time()
            else:
                params['timestamp'] = int(time.time() * 1000)
        
        # Add receive window for tolerance
        if 'recvWindow' not in params:
            params['recvWindow'] = 60000  # 60 seconds
        
        # Create query string (sorted by key for consistency)
        query_string = urlencode(sorted(params.items()))
        
        # Generate signature
        signature = self._generate_signature(query_string)
        
        # Add signature to parameters
        params['signature'] = signature
        
        return params
    
    def _make_signed_request(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a signed request to Binance SAPI
        """
        if params is None:
            params = {}
        
        # Prepare signed parameters
        signed_params = self._prepare_signed_request(params)
        
        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Build URL
        url = f"{self.base_url}/sapi/v1/{endpoint}"
        
        # Make request
        if method.upper() == 'GET':
            response = requests.get(url, params=signed_params, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, data=signed_params, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Log request details for debugging
        logger.info(f"{method} {url}")
        logger.debug(f"Parameters: {signed_params}")
        logger.debug(f"Response status: {response.status_code}")
        
        # Handle response
        if response.status_code == 200:
            return response.json()
        else:
            error_text = response.text[:500] if response.text else "No error message"
            logger.error(f"Request failed: {response.status_code} - {error_text}")
            
            try:
                error_json = response.json()
                raise BinanceAPIException(response, error_json['code'], error_json['msg'])
            except (ValueError, KeyError):
                raise BinanceAPIException(response, -1, f"HTTP {response.status_code}: {error_text}")
    
    def universal_transfer(self, transfer_type: str, asset: str, amount: Union[str, float]) -> Dict[str, Any]:
        """
        Execute universal transfer between wallet types
        
        Args:
            transfer_type: Transfer type (e.g., 'SPOT_TO_FUTURES', 'FUNDING_TO_SPOT')
            asset: Asset symbol (e.g., 'USDT', 'BTC')
            amount: Transfer amount (string or float)
        
        Returns:
            Dict containing transaction ID and status
        """
        params = {
            'type': transfer_type,
            'asset': asset.upper(),
            'amount': str(amount)
        }
        
        logger.info(f"Executing universal transfer: {amount} {asset} ({transfer_type})")
        
        try:
            result = self._make_signed_request('POST', 'asset/transfer', params)
            logger.info(f"Transfer successful: Transaction ID {result.get('tranId')}")
            return result
        except BinanceAPIException as e:
            logger.error(f"Transfer failed: {e}")
            raise
    
    def get_universal_transfer_history(self, transfer_type: str = None, start_time: int = None, 
                                     end_time: int = None, current: int = 1, size: int = 10) -> Dict[str, Any]:
        """
        Get universal transfer history
        
        Args:
            transfer_type: Filter by transfer type (optional)
            start_time: Start time in milliseconds (optional)
            end_time: End time in milliseconds (optional)
            current: Page number (default: 1)
            size: Page size (default: 10, max: 100)
        
        Returns:
            Dict containing transfer history
        """
        params = {
            'current': current,
            'size': min(size, 100)  # Max 100 per page
        }
        
        if transfer_type:
            params['type'] = transfer_type
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._make_signed_request('GET', 'asset/transfer', params)
    
    def get_account_status(self) -> Dict[str, Any]:
        """
        Get account status (SAPI endpoint)
        """
        return self._make_signed_request('GET', 'account/status')
    
    def get_account_api_trading_status(self) -> Dict[str, Any]:
        """
        Get account API trading status
        """
        return self._make_signed_request('GET', 'account/apiTradingStatus')
    
    def get_dust_assets(self) -> Dict[str, Any]:
        """
        Get dust assets that can be converted to BNB
        """
        return self._make_signed_request('POST', 'asset/dust-btc')
    
    def dust_transfer(self, asset_list: list) -> Dict[str, Any]:
        """
        Convert dust assets to BNB
        
        Args:
            asset_list: List of assets to convert (e.g., ['ETH', 'LTC'])
        """
        params = {
            'asset': ','.join(asset_list)
        }
        return self._make_signed_request('POST', 'asset/dust', params)
    
    def get_asset_dividend_record(self, asset: str = None, start_time: int = None, 
                                 end_time: int = None, limit: int = 20) -> Dict[str, Any]:
        """
        Get asset dividend record
        
        Args:
            asset: Asset name (optional)
            start_time: Start time in milliseconds (optional)  
            end_time: End time in milliseconds (optional)
            limit: Limit (default: 20, max: 500)
        """
        params = {
            'limit': min(limit, 500)
        }
        
        if asset:
            params['asset'] = asset
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        return self._make_signed_request('GET', 'asset/assetDividend', params)
    
    def get_asset_detail(self, asset: str = None) -> Dict[str, Any]:
        """
        Get asset detail
        
        Args:
            asset: Asset name (optional, if not provided returns all)
        """
        params = {}
        if asset:
            params['asset'] = asset
            
        return self._make_signed_request('GET', 'asset/assetDetail', params)
    
    def get_trade_fee(self, symbol: str = None) -> Dict[str, Any]:
        """
        Get trade fee
        
        Args:
            symbol: Trading symbol (optional, if not provided returns all)
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
            
        return self._make_signed_request('GET', 'asset/tradeFee', params)
    
    def get_user_universal_transfer_history(self, transfer_type: str, start_time: int = None,
                                          end_time: int = None, current: int = 1, 
                                          size: int = 10) -> Dict[str, Any]:
        """
        Get user universal transfer history with additional filtering
        """
        params = {
            'type': transfer_type,
            'current': current,
            'size': min(size, 100)
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        return self._make_signed_request('GET', 'asset/transfer', params)
    
    def test_connectivity(self) -> bool:
        """
        Test SAPI connectivity and API key validity
        """
        try:
            # Try a simple SAPI endpoint
            result = self.get_account_status()
            logger.info("SAPI connectivity test successful")
            return True
        except Exception as e:
            logger.error(f"SAPI connectivity test failed: {e}")
            return False

def main():
    """Test the SAPI client"""
    # Load environment variables
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    
    if not api_key or not secret_key:
        print("Error: BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables required")
        return False
    
    # Create SAPI client
    sapi_client = BinanceSAPIClient(api_key, secret_key, testnet)
    
    print(f"Testing Binance SAPI Client ({'TESTNET' if testnet else 'MAINNET'})")
    print("=" * 60)
    
    # Test 1: Connectivity
    print("1. Testing connectivity...")
    if not sapi_client.test_connectivity():
        print("FAIL: Connectivity test failed")
        return False
    print("PASS: Connectivity test passed")
    
    # Test 2: Account status
    print("\n2. Testing account status...")
    try:
        status = sapi_client.get_account_status()
        print("PASS: Account status retrieved")
        print(f"   Status: {status}")
    except Exception as e:
        print(f"FAIL: Account status failed: {e}")
    
    # Test 3: Asset details
    print("\n3. Testing asset details...")
    try:
        assets = sapi_client.get_asset_detail('USDT')
        print("PASS: Asset details retrieved")
        print(f"   USDT details: {assets}")
    except Exception as e:
        print(f"FAIL: Asset details failed: {e}")
    
    # Test 4: Universal transfer (small amount)
    print("\n4. Testing universal transfer...")
    try:
        # Try a small transfer from FUNDING to SPOT
        result = sapi_client.universal_transfer('FUNDING_TO_SPOT', 'USDT', '1')
        print("PASS: Universal transfer successful")
        print(f"   Transaction ID: {result.get('tranId')}")
    except Exception as e:
        print(f"FAIL: Universal transfer failed: {e}")
        # This is expected if there are no funds or if testnet doesn't support transfers
    
    # Test 5: Transfer history
    print("\n5. Testing transfer history...")
    try:
        history = sapi_client.get_universal_transfer_history(size=5)
        print("PASS: Transfer history retrieved")
        print(f"   Records: {len(history.get('rows', []))}")
    except Exception as e:
        print(f"FAIL: Transfer history failed: {e}")
    
    print("\n" + "=" * 60)
    print("SAPI client testing completed")
    
    return True

if __name__ == "__main__":
    # Load .env file
    def load_env():
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    load_env()
    main()