#!/usr/bin/env python3
"""
Comprehensive SAPI Signature Analysis and Testing Script
Tests multiple signature generation methods to find the correct format for Binance SAPI endpoints.
"""

import os
import sys
import time
import hmac
import hashlib
import json
import requests
from urllib.parse import urlencode, quote_plus, quote
import logging
from typing import Dict, Any, Tuple, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

# Load .env file if it exists
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BinanceSAPISignatureTester:
    """Test different signature generation methods for Binance SAPI endpoints"""
    
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        self.testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        if not self.api_key or not self.secret_key:
            raise ValueError("BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables are required")
        
        # Base URLs
        if self.testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
        
        # Initialize official client for comparison
        self.client = Client(self.api_key, self.secret_key, testnet=self.testnet)
        
        logger.info(f"Initialized for {'TESTNET' if self.testnet else 'MAINNET'}")
    
    def get_server_time(self) -> int:
        """Get Binance server time for synchronization"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/time")
            response.raise_for_status()
            server_time = response.json()['serverTime']
            local_time = int(time.time() * 1000)
            offset = server_time - local_time
            
            logger.info(f"Server time: {server_time}, Local time: {local_time}, Offset: {offset}ms")
            return server_time
        except Exception as e:
            logger.error(f"Error getting server time: {e}")
            return int(time.time() * 1000)
    
    def generate_signature_v1(self, params: Dict[str, Any]) -> Tuple[str, str]:
        """Method 1: Standard query string encoding"""
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return query_string, signature
    
    def generate_signature_v2(self, params: Dict[str, Any]) -> Tuple[str, str]:
        """Method 2: Sorted parameters with quote_plus encoding"""
        sorted_params = sorted(params.items())
        query_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in sorted_params])
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return query_string, signature
    
    def generate_signature_v3(self, params: Dict[str, Any]) -> Tuple[str, str]:
        """Method 3: Raw parameter concatenation"""
        sorted_params = sorted(params.items())
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return query_string, signature
    
    def generate_signature_v4(self, params: Dict[str, Any]) -> Tuple[str, str]:
        """Method 4: JSON body signature (for POST requests)"""
        if 'timestamp' not in params:
            params['timestamp'] = self.get_server_time()
        
        json_body = json.dumps(params, separators=(',', ':'), sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            json_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return json_body, signature
    
    def generate_signature_v5(self, params: Dict[str, Any]) -> Tuple[str, str]:
        """Method 5: URL encoding with spaces as %20"""
        query_string = urlencode(params, doseq=True, quote_via=quote)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return query_string, signature
    
    def generate_signature_v6(self, params: Dict[str, Any]) -> Tuple[str, str]:
        """Method 6: Double URL encoding"""
        first_encode = urlencode(params, doseq=True)
        double_encoded = quote(first_encode, safe='&=')
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            double_encoded.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return double_encoded, signature
    
    def generate_signature_binance_client(self, params: Dict[str, Any]) -> Tuple[str, str]:
        """Method: Use python-binance library's internal signature method"""
        try:
            # Access the client's internal signature generation
            if hasattr(self.client, '_generate_signature'):
                query_string = urlencode(params, doseq=True)
                signature = self.client._generate_signature(query_string)
                return query_string, signature
            else:
                # Fallback to manual implementation
                return self.generate_signature_v1(params)
        except Exception as e:
            logger.error(f"Error using client signature method: {e}")
            return self.generate_signature_v1(params)
    
    def test_universal_transfer(self, method_name: str, signature_func, use_post: bool = False) -> Dict[str, Any]:
        """Test universal transfer with specific signature method"""
        try:
            # Get synchronized timestamp
            timestamp = self.get_server_time()
            
            # Test parameters
            params = {
                'type': 'FUNDING_TO_SPOT',
                'asset': 'USDT',
                'amount': '10',
                'timestamp': timestamp
            }
            
            # Add recvWindow for tolerance
            params['recvWindow'] = 60000
            
            # Generate signature
            query_string, signature = signature_func(params)
            
            # Add signature to parameters
            params['signature'] = signature
            
            headers = {
                'X-MBX-APIKEY': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded' if use_post else 'application/json'
            }
            
            url = f"{self.base_url}/sapi/v1/asset/transfer"
            
            if use_post:
                # POST with form data
                response = requests.post(url, data=params, headers=headers)
            else:
                # GET with query parameters
                response = requests.get(url, params=params, headers=headers)
            
            result = {
                'method': method_name,
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'url': response.url,
                'headers_sent': headers,
                'params_sent': params,
                'query_string': query_string,
                'signature': signature,
                'response_text': response.text[:500] if response.text else None,
                'timestamp_used': timestamp,
                'use_post': use_post
            }
            
            if response.status_code == 200:
                try:
                    result['response_json'] = response.json()
                except:
                    pass
            
            logger.info(f"{method_name}: Status {response.status_code}")
            return result
            
        except Exception as e:
            logger.error(f"Error testing {method_name}: {e}")
            return {
                'method': method_name,
                'success': False,
                'error': str(e),
                'use_post': use_post
            }
    
    def test_account_status(self, method_name: str, signature_func) -> Dict[str, Any]:
        """Test account status endpoint (simpler SAPI endpoint)"""
        try:
            timestamp = self.get_server_time()
            params = {
                'timestamp': timestamp,
                'recvWindow': 60000
            }
            
            query_string, signature = signature_func(params)
            params['signature'] = signature
            
            headers = {'X-MBX-APIKEY': self.api_key}
            url = f"{self.base_url}/sapi/v1/account/status"
            
            response = requests.get(url, params=params, headers=headers)
            
            result = {
                'method': method_name,
                'endpoint': 'account/status',
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_text': response.text[:200] if response.text else None
            }
            
            if response.status_code == 200:
                try:
                    result['response_json'] = response.json()
                except:
                    pass
            
            return result
            
        except Exception as e:
            return {
                'method': method_name,
                'endpoint': 'account/status',
                'success': False,
                'error': str(e)
            }
    
    def test_margin_account(self, method_name: str, signature_func) -> Dict[str, Any]:
        """Test margin account endpoint"""
        try:
            timestamp = self.get_server_time()
            params = {
                'timestamp': timestamp,
                'recvWindow': 60000
            }
            
            query_string, signature = signature_func(params)
            params['signature'] = signature
            
            headers = {'X-MBX-APIKEY': self.api_key}
            url = f"{self.base_url}/sapi/v1/margin/account"
            
            response = requests.get(url, params=params, headers=headers)
            
            result = {
                'method': method_name,
                'endpoint': 'margin/account',
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_text': response.text[:200] if response.text else None
            }
            
            if response.status_code == 200:
                try:
                    result['response_json'] = response.json()
                except:
                    pass
            
            return result
            
        except Exception as e:
            return {
                'method': method_name,
                'endpoint': 'margin/account',
                'success': False,
                'error': str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all signature methods"""
        results = {
            'test_timestamp': int(time.time() * 1000),
            'testnet': self.testnet,
            'methods_tested': [],
            'successful_methods': [],
            'failed_methods': [],
            'detailed_results': {}
        }
        
        # Define signature methods to test
        signature_methods = [
            ('Standard urlencode', self.generate_signature_v1),
            ('Sorted + quote_plus', self.generate_signature_v2),
            ('Raw concatenation', self.generate_signature_v3),
            ('JSON body signature', self.generate_signature_v4),
            ('URL encode %20', self.generate_signature_v5),
            ('Double encoding', self.generate_signature_v6),
            ('Binance client method', self.generate_signature_binance_client)
        ]
        
        logger.info("Starting comprehensive SAPI signature testing...")
        
        for method_name, signature_func in signature_methods:
            logger.info(f"Testing method: {method_name}")
            results['methods_tested'].append(method_name)
            
            # Test multiple endpoints
            method_results = {}
            
            # Test 1: Account status (simple SAPI endpoint)
            method_results['account_status'] = self.test_account_status(method_name, signature_func)
            
            # Test 2: Margin account (another SAPI endpoint)
            method_results['margin_account'] = self.test_margin_account(method_name, signature_func)
            
            # Test 3: Universal transfer GET
            method_results['universal_transfer_get'] = self.test_universal_transfer(
                f"{method_name} (GET)", signature_func, use_post=False
            )
            
            # Test 4: Universal transfer POST
            method_results['universal_transfer_post'] = self.test_universal_transfer(
                f"{method_name} (POST)", signature_func, use_post=True
            )
            
            # Check if any test succeeded
            any_success = any(result.get('success', False) for result in method_results.values())
            
            if any_success:
                results['successful_methods'].append(method_name)
                logger.info(f"SUCCESS: {method_name} - SUCCESS on at least one endpoint")
            else:
                results['failed_methods'].append(method_name)
                logger.info(f"FAILED: {method_name} - FAILED on all endpoints")
            
            results['detailed_results'][method_name] = method_results
        
        # Test official client method for comparison
        logger.info("Testing official python-binance client...")
        try:
            # Test with official client
            client_result = self.client.get_account_status()
            results['official_client_test'] = {
                'success': True,
                'response': client_result
            }
            logger.info("SUCCESS: Official client - SUCCESS")
        except Exception as e:
            results['official_client_test'] = {
                'success': False,
                'error': str(e)
            }
            logger.error(f"FAILED: Official client - ERROR: {e}")
        
        return results
    
    def analyze_successful_methods(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze successful methods to determine the correct signature format"""
        analysis = {
            'successful_count': len(results['successful_methods']),
            'failed_count': len(results['failed_methods']),
            'recommendations': [],
            'signature_patterns': {}
        }
        
        if results['successful_methods']:
            logger.info("Found successful signature methods:")
            for method in results['successful_methods']:
                logger.info(f"  - {method}")
                
                # Analyze the successful method's patterns
                method_data = results['detailed_results'][method]
                for endpoint, endpoint_data in method_data.items():
                    if endpoint_data.get('success'):
                        pattern = {
                            'endpoint': endpoint,
                            'query_string_format': endpoint_data.get('query_string', 'N/A'),
                            'signature': endpoint_data.get('signature', 'N/A')[:16] + '...',
                            'status_code': endpoint_data.get('status_code')
                        }
                        
                        if method not in analysis['signature_patterns']:
                            analysis['signature_patterns'][method] = []
                        analysis['signature_patterns'][method].append(pattern)
        
        if not results['successful_methods']:
            analysis['recommendations'].append("No successful methods found. Check API keys and network connectivity.")
            analysis['recommendations'].append("Verify that testnet mode matches your API key type.")
            analysis['recommendations'].append("Check server time synchronization.")
        else:
            analysis['recommendations'].append(f"Use one of the successful methods: {', '.join(results['successful_methods'])}")
        
        return analysis

def main():
    """Main testing function"""
    try:
        tester = BinanceSAPISignatureTester()
        
        print("="*80)
        print("BINANCE SAPI SIGNATURE COMPREHENSIVE TESTING")
        print("="*80)
        print(f"Mode: {'TESTNET' if tester.testnet else 'MAINNET'}")
        print(f"API Key: {tester.api_key[:8]}...")
        print("="*80)
        
        # Run comprehensive test
        results = tester.run_comprehensive_test()
        
        # Analyze results
        analysis = tester.analyze_successful_methods(results)
        
        # Print summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Total methods tested: {len(results['methods_tested'])}")
        print(f"Successful methods: {analysis['successful_count']}")
        print(f"Failed methods: {analysis['failed_count']}")
        
        if results['successful_methods']:
            print(f"\nSUCCESSFUL METHODS:")
            for method in results['successful_methods']:
                print(f"  - {method}")
        
        if results['failed_methods']:
            print(f"\nFAILED METHODS:")
            for method in results['failed_methods']:
                print(f"  - {method}")
        
        print(f"\nRECOMMENDATIONS:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")
        
        # Save detailed results
        timestamp = int(time.time())
        results_file = f"sapi_signature_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'results': results,
                'analysis': analysis
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Return success if any method worked
        return len(results['successful_methods']) > 0
        
    except Exception as e:
        logger.error(f"Test execution error: {e}")
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)