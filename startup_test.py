#!/usr/bin/env python3
"""
Railway Deployment Startup Test
Tests all imports and basic initialization without running the trading loop
"""
import sys
import os
import asyncio

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Quantum Trading Bot startup for Railway deployment...")

def test_imports():
    """Test all critical imports"""
    print("\n[1] Testing imports...")
    
    try:
        # Core imports
        from core.config.settings import config
        print("[OK] Config import successful")
        
        from core.data_collector import DataCollector
        print("[OK] DataCollector import successful")
        
        from core.correlation_engine import CorrelationEngine
        print("[OK] CorrelationEngine import successful")
        
        from core.signal_generator import SignalGenerator
        print("[OK] SignalGenerator import successful")
        
        from core.ultra_high_frequency_trader import ultra_high_frequency_trader
        print("[OK] UltraHighFrequencyTrader import successful")
        
        from core.executor import Executor
        print("[OK] Executor import successful")
        
        from core.risk_manager import RiskManager
        print("[OK] RiskManager import successful")
        
        from analytics.performance import PerformanceTracker
        print("[OK] PerformanceTracker import successful")
        
        from analytics.failure_analyzer import FailureAnalyzer
        print("[OK] FailureAnalyzer import successful")
        
        from core.environment_manager import environment_manager, Environment
        print("[OK] EnvironmentManager import successful")
        
        from core.data_authenticity_validator import authenticity_validator
        print("[OK] DataAuthenticityValidator import successful")
        
        from api.health import run_health_server_thread
        print("[OK] Health API import successful")
        
        from utils.production_logger import setup_production_logging, get_trading_logger
        print("[OK] ProductionLogger import successful")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error during imports: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n[2] Testing configuration...")
    
    try:
        from core.config.settings import config
        
        print(f"[OK] Symbols: {config.SYMBOLS}")
        print(f"[OK] Timeframes: {config.TIMEFRAMES}")
        print(f"[OK] Binance Testnet: {config.BINANCE_TESTNET}")
        print(f"[OK] Risk per trade: {config.RISK_PER_TRADE}")
        print(f"[OK] Default leverage: {config.DEFAULT_LEVERAGE}")
        
        # Check if API keys are set
        if config.BINANCE_API_KEY and config.BINANCE_SECRET_KEY:
            print("[OK] Binance API credentials configured")
        else:
            print("[WARN] Binance API credentials not configured (will need env vars)")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        return False

def main():
    """Run all startup tests"""
    print("=" * 60)
    print("QUANTUM TRADING BOT - RAILWAY STARTUP TEST")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[RUN] Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"[OK] {test_name} PASSED")
            else:
                print(f"[ERROR] {test_name} FAILED")
        except Exception as e:
            print(f"[ERROR] {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Bot is ready for Railway deployment.")
        return 0
    else:
        print("Some tests failed. Review issues before deployment.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)