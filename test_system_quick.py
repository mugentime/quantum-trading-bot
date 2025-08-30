#!/usr/bin/env python3
"""
Quick test of the comprehensive optimization system components
"""

import asyncio
import sys
from datetime import datetime

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import ccxt.async_support as ccxt
        print("  [OK] CCXT async support")
        
        import pandas as pd
        print("  [OK] Pandas")
        
        import numpy as np
        print("  [OK] NumPy")
        
        from comprehensive_optimization_system import ComprehensiveOptimizationSystem
        print("  [OK] Optimization system")
        
        return True
        
    except ImportError as e:
        print(f"  [FAIL] Import failed: {e}")
        return False

async def test_exchange_connection():
    """Test Binance testnet connection"""
    print("\nTesting exchange connection...")
    
    try:
        from comprehensive_optimization_system import ComprehensiveOptimizationSystem
        
        system = ComprehensiveOptimizationSystem()
        success = await system.initialize_exchange()
        
        if success:
            print("  [OK] Exchange connection successful")
            
            # Test basic functionality
            balance = await system.exchange.fetch_balance()
            print(f"  [OK] Balance fetch: {balance.get('USDT', {}).get('free', 0)} USDT")
            
            await system.exchange.close()
            return True
        else:
            print("  [FAIL] Exchange connection failed")
            return False
            
    except Exception as e:
        print(f"  [FAIL] Connection error: {e}")
        return False

def test_parameter_generation():
    """Test parameter generation"""
    print("\nTesting parameter generation...")
    
    try:
        from comprehensive_optimization_system import ComprehensiveOptimizationSystem
        
        system = ComprehensiveOptimizationSystem()
        
        # Test parameter ranges
        print(f"  [OK] Pairs: {len(system.pairs)} configured")
        print(f"  [OK] Parameter ranges: {len(system.param_ranges)} categories")
        
        # Calculate total combinations
        total_combinations = 1
        for param, values in system.param_ranges.items():
            total_combinations *= len(values)
            print(f"    {param}: {len(values)} options")
        
        print(f"  [OK] Total combinations: {total_combinations}")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Parameter test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPREHENSIVE OPTIMIZATION SYSTEM - QUICK TEST")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports()),
        ("Exchange Connection", test_exchange_connection()),
        ("Parameter Generation", test_parameter_generation())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if asyncio.iscoroutine(test_func):
            result = await test_func
        else:
            result = test_func
            
        if result:
            passed += 1
            print(f"[PASS] {test_name}: PASSED")
        else:
            print(f"[FAIL] {test_name}: FAILED")
    
    print("\n" + "=" * 60)
    print(f"QUICK TEST SUMMARY: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("SUCCESS: All tests passed! System ready for execution.")
        print("\nTo run full optimization:")
        print("python run_comprehensive_optimization.py")
        return True
    else:
        print("WARNING: Some tests failed. Check configuration before running.")
        return False

if __name__ == "__main__":
    asyncio.run(main())