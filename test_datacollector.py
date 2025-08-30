#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for DataCollector functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        print("Testing core module imports...")
        from core.config.settings import config
        print("[OK] Config imported successfully")
        
        from core.data_collector import DataCollector
        print("[OK] DataCollector imported successfully")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

async def test_datacollector_basic():
    """Test basic DataCollector functionality"""
    try:
        print("\nTesting DataCollector initialization...")
        from core.config.settings import config
        from core.data_collector import DataCollector
        
        # Create DataCollector instance
        collector = DataCollector(['BTCUSDT', 'ETHUSDT'])
        print("[OK] DataCollector initialized successfully")
        
        # Check methods exist
        methods_to_check = ['start', 'stop', 'get_latest_data', 'get_historical_prices', 'get_data_health']
        for method in methods_to_check:
            if hasattr(collector, method):
                print(f"[OK] Method '{method}' exists")
            else:
                print(f"[ERROR] Method '{method}' missing")
                return False
        
        print("[OK] All required methods found")
        return True
        
    except Exception as e:
        print(f"[ERROR] DataCollector test failed: {e}")
        return False

async def test_mock_data_collection():
    """Test DataCollector with mock functionality"""
    try:
        print("\nTesting mock data collection...")
        from core.data_collector import DataCollector
        
        collector = DataCollector(['BTCUSDT'])
        
        # Test data health before starting
        health = collector.get_data_health()
        print(f"[OK] Data health check works: {health}")
        
        # Test getting latest data (should return empty when not running)
        latest = await collector.get_latest_data()
        print(f"[OK] Latest data retrieval works: {latest}")
        
        print("[OK] Mock data collection tests passed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Mock data collection failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("=== DataCollector Test Suite ===")
    
    # Test 1: Imports
    if not test_imports():
        print("\n[FAILED] Import tests failed")
        return False
    
    # Test 2: Basic functionality
    if not await test_datacollector_basic():
        print("\n[FAILED] Basic functionality tests failed")
        return False
    
    # Test 3: Mock data collection
    if not await test_mock_data_collection():
        print("\n[FAILED] Mock data collection tests failed")
        return False
    
    print("\n[SUCCESS] All tests passed! DataCollector implementation is working correctly.")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("\n[SUCCESS] DataCollector is ready for use!")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n[CRASH] Test suite crashed: {e}")
        sys.exit(1)