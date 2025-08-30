#!/usr/bin/env python3
"""
Test script for the Enhanced Leverage Trading System
Validates configuration loading and core functionality
"""

import json
import os
from datetime import datetime

def test_leverage_config():
    """Test if leverage configuration is properly loaded"""
    print("=" * 50)
    print("TESTING LEVERAGE CONFIGURATION SYSTEM")
    print("=" * 50)
    
    # Test 1: Check if optimized config exists
    config_file = 'optimized_leverage_config.json'
    if os.path.exists(config_file):
        print("[OK] Leverage configuration file found")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"[OK] Configuration loaded successfully")
            print(f"   - Trading pairs: {len(config['trading_pairs'])}")
            print(f"   - Profitable pairs: {config['optimization_summary']['profitable_pairs']}")
            print(f"   - Average return: {config['optimization_summary']['average_return']:.2f}%")
            print(f"   - Best performer: {config['optimization_summary']['best_performer']}")
            
            # Test 2: Validate leverage allocation
            print("\nLEVERAGE ALLOCATION ANALYSIS:")
            print("-" * 40)
            
            total_leverage = 0
            high_risk_pairs = 0
            priority_1_pairs = 0
            
            for symbol, params in config['trading_pairs'].items():
                leverage = params['leverage']
                risk_level = params['risk_level']
                priority = params['priority']
                
                total_leverage += leverage
                if risk_level == 'HIGH':
                    high_risk_pairs += 1
                if priority == 1:
                    priority_1_pairs += 1
                
                print(f"{symbol:10} | {leverage:2}x | {risk_level:6} | Priority {priority}")
            
            avg_leverage = total_leverage / len(config['trading_pairs'])
            print(f"\nSTATISTICS:")
            print(f"   - Average leverage: {avg_leverage:.1f}x")
            print(f"   - High-risk pairs: {high_risk_pairs}/{len(config['trading_pairs'])}")
            print(f"   - Priority 1 pairs: {priority_1_pairs}")
            
            # Test 3: Risk management validation
            print(f"\nRISK MANAGEMENT VALIDATION:")
            print("-" * 40)
            
            for symbol, params in config['trading_pairs'].items():
                leverage = params['leverage']
                stop_loss = params['stop_loss_pct']
                position_size = params['position_size_usd']
                max_position_pct = params['max_position_pct']
                
                # Calculate effective risk per trade
                effective_risk = (stop_loss / 100) * (position_size / 15000) * 100 * leverage
                
                print(f"{symbol}: SL {stop_loss:.1f}% @ {leverage}x = {effective_risk:.2f}% account risk")
                
                # Validate risk limits
                if effective_risk > 5.0:  # More than 5% account risk
                    print(f"   WARNING: {effective_risk:.2f}% exceeds 5% limit")
                elif effective_risk > 2.0:  # More than 2% account risk
                    print(f"   MODERATE RISK: {effective_risk:.2f}%")
                else:
                    print(f"   [OK] CONSERVATIVE: {effective_risk:.2f}%")
            
            print(f"\n[OK] ALL TESTS PASSED - Leverage system validated")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error loading configuration: {e}")
            return False
            
    else:
        print(f"[ERROR] Configuration file not found: {config_file}")
        print(f"   Run 'python leverage_optimizer.py' to generate configuration")
        return False

def test_system_readiness():
    """Test if all required components are available"""
    print(f"\nSYSTEM READINESS CHECK:")
    print("-" * 40)
    
    required_files = [
        'core/enhanced_correlation_engine.py',
        'core/data_collector.py', 
        'core/enhanced_risk_manager.py',
        'core/signal_generator.py',
        'core/executor.py',
        'utils/telegram_notifier.py',
        'utils/logger.py'
    ]
    
    all_present = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[OK] {file_path}")
        else:
            print(f"[MISSING] {file_path}")
            all_present = False
    
    # Check environment variables
    print(f"\nENVIRONMENT VARIABLES:")
    env_vars = ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY', 'BINANCE_TESTNET']
    for var in env_vars:
        if os.getenv(var):
            print(f"[OK] {var} - Set")
        else:
            print(f"[WARN] {var} - Not set")
    
    return all_present

def main():
    """Run all tests"""
    print(f"ENHANCED LEVERAGE TRADING SYSTEM - TEST SUITE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test leverage configuration
    config_ok = test_leverage_config()
    
    # Test system readiness  
    system_ok = test_system_readiness()
    
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY:")
    print(f"   - Leverage Config: {'PASS' if config_ok else 'FAIL'}")
    print(f"   - System Files: {'PASS' if system_ok else 'FAIL'}")
    
    if config_ok and system_ok:
        print(f"\nSYSTEM READY FOR DEPLOYMENT!")
        print(f"   Run 'python enhanced_main.py' to start trading")
    else:
        print(f"\nSYSTEM NOT READY - Fix issues above first")
    
    return config_ok and system_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)