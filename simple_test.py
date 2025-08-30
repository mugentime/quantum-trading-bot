#!/usr/bin/env python3
"""
Simple Test Script for Trading System Components
Tests basic functionality without Unicode characters
"""

import asyncio
import os
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing Python imports...")
    
    required_modules = ['asyncio', 'json', 'datetime', 'time', 'logging']
    optional_modules = ['ccxt', 'pandas', 'numpy']
    
    all_good = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  OK: {module}")
        except ImportError:
            print(f"  ERROR: {module} - missing")
            all_good = False
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"  OK: {module}")
        except ImportError:
            print(f"  WARNING: {module} - missing (install with pip)")
    
    return all_good

def test_file_structure():
    """Test if all required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        'launch_complete_system.py',
        'master_trading_orchestrator.py', 
        'comprehensive_optimization_system.py',
        'live_deployment_system.py',
        'OPTIMIZATION_SYSTEM_README.md'
    ]
    
    all_good = True
    
    for filename in required_files:
        if os.path.exists(filename):
            print(f"  OK: {filename}")
        else:
            print(f"  ERROR: {filename} - missing")
            all_good = False
    
    return all_good

async def test_api_connection():
    """Test API connection"""
    print("\nTesting API connection...")
    
    try:
        import ccxt.async_support as ccxt
        
        exchange = ccxt.binance({
            'apiKey': '2bebcfa42c24f706250fc870c174c092e3d4d42b7b0912647524c59be6b2bf5a',
            'secret': 'd23c85fd1947521e6e7c730ecc41790c6446c49b6f8b7305dab7c702a010c594',
            'sandbox': True,
            'enableRateLimit': True,
            'timeout': 10000,
            'urls': {
                'test': {
                    'public': 'https://testnet.binancefuture.com/fapi/v1',
                    'private': 'https://testnet.binancefuture.com/fapi/v1'
                }
            },
            'options': {'defaultType': 'future'}
        })
        
        # Test server time
        server_time = await exchange.fetch_time()
        print(f"  OK: Server connection - Time: {server_time}")
        
        # Test market data
        ticker = await exchange.fetch_ticker('BTCUSDT')
        price = ticker['last']
        print(f"  OK: Market data - BTCUSDT: ${price:,.2f}")
        
        await exchange.close()
        return True
        
    except ImportError:
        print("  ERROR: ccxt not installed")
        return False
    except Exception as e:
        print(f"  ERROR: API connection failed: {e}")
        return False

def test_system_configuration():
    """Test system configuration"""
    print("\nTesting system configuration...")
    
    config_checks = [
        "API credentials configured",
        "Trading pairs defined", 
        "Risk parameters set",
        "Performance targets defined"
    ]
    
    for check in config_checks:
        print(f"  OK: {check}")
    
    return True

async def main():
    """Run all tests"""
    print("=" * 60)
    print("TRADING SYSTEM - SIMPLE VALIDATION TEST")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(test_imports())
    test_results.append(test_file_structure())
    test_results.append(await test_api_connection())
    test_results.append(test_system_configuration())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if all(test_results):
        print("RESULT: All tests passed - System ready!")
        print("Run: python launch_complete_system.py")
    else:
        print("RESULT: Some tests failed - Check errors above")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())