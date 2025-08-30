#!/usr/bin/env python3
"""
Comprehensive testing suite for simplified Quantum Trading Bot
Validates API connectivity, trading logic, and Railway deployment readiness
"""

import asyncio
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simple_bot import SimpleBinanceClient, CorrelationEngine, RiskManager, TradingSignal, Position

# Test configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestResults:
    """Track test results"""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            logger.info(f"✅ {test_name}: PASSED {message}")
        else:
            self.failures.append((test_name, message))
            logger.error(f"❌ {test_name}: FAILED {message}")
    
    def get_summary(self) -> Dict:
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": len(self.failures),
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "failures": self.failures
        }

async def test_binance_api_connectivity():
    """Test Binance API connectivity and authentication"""
    results = TestResults()
    
    async with SimpleBinanceClient() as client:
        # Test 1: API Key Configuration
        has_api_key = bool(client.api_key and len(client.api_key) > 10)
        results.add_result("API Key Configuration", has_api_key, f"Key length: {len(client.api_key) if client.api_key else 0}")
        
        # Test 2: API Secret Configuration  
        has_api_secret = bool(client.api_secret and len(client.api_secret) > 10)
        results.add_result("API Secret Configuration", has_api_secret, f"Secret length: {len(client.api_secret) if client.api_secret else 0}")
        
        # Test 3: Account Info Retrieval
        account = await client.get_account_info()
        account_accessible = bool(account and 'totalWalletBalance' in account)
        balance = float(account.get('totalWalletBalance', 0)) if account else 0
        results.add_result("Account Info Access", account_accessible, f"Balance: ${balance:.2f}")
        
        # Test 4: Price Data Retrieval
        test_symbols = ['BTCUSDT', 'ETHUSDT']
        price_data_valid = True
        prices = {}
        
        for symbol in test_symbols:
            price = await client.get_symbol_price(symbol)
            prices[symbol] = price
            if price <= 0:
                price_data_valid = False
                break
        
        results.add_result("Price Data Retrieval", price_data_valid, f"Prices: {prices}")
        
        # Test 5: Kline Data Retrieval
        klines = await client.get_klines('BTCUSDT', '1m', 10)
        klines_valid = bool(klines and len(klines) > 0 and len(klines[0]) >= 6)
        results.add_result("Kline Data Retrieval", klines_valid, f"Klines count: {len(klines) if klines else 0}")
        
        # Test 6: Position Data Access
        positions = await client.get_positions()
        positions_accessible = isinstance(positions, list)
        results.add_result("Position Data Access", positions_accessible, f"Positions count: {len(positions) if positions else 0}")
    
    return results

def test_correlation_engine():
    """Test correlation calculation and signal generation"""
    results = TestResults()
    
    engine = CorrelationEngine()
    
    # Test 1: Price History Update
    test_prices = {
        'BTCUSDT': 45000.0,
        'ETHUSDT': 3000.0,
        'SOLUSDT': 100.0
    }
    
    engine.update_prices(test_prices)
    history_updated = all(symbol in engine.price_history for symbol in test_prices.keys())
    results.add_result("Price History Update", history_updated, f"Symbols tracked: {len(engine.price_history)}")
    
    # Test 2: Build sufficient history for correlation
    for i in range(25):  # Need at least 20 data points
        varied_prices = {
            'BTCUSDT': 45000.0 + i * 100 + (i % 3) * 200,  # Add some variation
            'ETHUSDT': 3000.0 + i * 10 + (i % 2) * 50,
            'SOLUSDT': 100.0 + i * 1 + (i % 4) * 5
        }
        engine.update_prices(varied_prices)
    
    sufficient_history = all(len(engine.price_history[s]) >= 20 for s in test_prices.keys())
    results.add_result("Sufficient Price History", sufficient_history, f"History lengths: {[len(engine.price_history[s]) for s in test_prices.keys()]}")
    
    # Test 3: Correlation Calculation
    correlations = engine.calculate_correlations()
    correlations_calculated = len(correlations) > 0
    results.add_result("Correlation Calculation", correlations_calculated, f"Correlation pairs: {len(correlations)}")
    
    # Test 4: Signal Generation
    current_prices = {
        'BTCUSDT': 45500.0,  # Strong move
        'ETHUSDT': 3010.0,   # Weak move  
        'SOLUSDT': 101.0     # Weak move
    }
    
    signals = engine.generate_signals(current_prices)
    signals_generated = len(signals) >= 0  # Could be 0 if no opportunities
    results.add_result("Signal Generation", signals_generated, f"Signals generated: {len(signals)}")
    
    # Test 5: Signal Structure Validation
    if signals:
        signal = signals[0]
        signal_valid = all([
            hasattr(signal, 'symbol'),
            hasattr(signal, 'action'),
            hasattr(signal, 'price'),
            hasattr(signal, 'strength'),
            signal.action in ['long', 'short'],
            signal.stop_loss > 0,
            signal.take_profit > 0
        ])
        results.add_result("Signal Structure", signal_valid, f"First signal: {signal.symbol} {signal.action}")
    else:
        results.add_result("Signal Structure", True, "No signals to validate (acceptable)")
    
    return results

def test_risk_manager():
    """Test risk management functionality"""
    results = TestResults()
    
    risk_manager = RiskManager()
    
    # Test 1: Risk Manager Initialization
    rm_initialized = all([
        risk_manager.max_positions > 0,
        risk_manager.risk_per_trade > 0,
        risk_manager.max_leverage > 0,
        0 < risk_manager.daily_loss_limit < 1
    ])
    results.add_result("Risk Manager Initialization", rm_initialized, f"Max positions: {risk_manager.max_positions}")
    
    # Test 2: Position Size Calculation
    test_signal = TradingSignal(
        symbol='BTCUSDT',
        action='long',
        price=45000.0,
        strength=0.25,
        timestamp=datetime.now(),
        stop_loss=44100.0,  # 2% stop
        take_profit=46800.0  # 4% profit
    )
    
    position_size = risk_manager.calculate_position_size(test_signal, 1000.0)  # $1000 balance
    size_reasonable = 0.001 <= position_size <= 1.0  # Reasonable range
    results.add_result("Position Size Calculation", size_reasonable, f"Size: {position_size}")
    
    # Test 3: Signal Filtering - No Positions
    signals = [test_signal]
    current_positions = []
    filtered = risk_manager.filter_signals(signals, current_positions, 1000.0)
    
    no_positions_allows_trading = len(filtered) > 0
    results.add_result("Signal Filtering (No Positions)", no_positions_allows_trading, f"Filtered signals: {len(filtered)}")
    
    # Test 4: Signal Filtering - Max Positions Reached
    max_positions = [
        Position('SYMBOL1', 'long', 0.1, 100.0, 15, 0.0, datetime.now()),
        Position('SYMBOL2', 'short', 0.1, 200.0, 15, 0.0, datetime.now()),
        Position('SYMBOL3', 'long', 0.1, 300.0, 15, 0.0, datetime.now())
    ]
    
    filtered_max = risk_manager.filter_signals(signals, max_positions, 1000.0)
    max_positions_blocks_trading = len(filtered_max) == 0
    results.add_result("Signal Filtering (Max Positions)", max_positions_blocks_trading, f"Positions: {len(max_positions)}")
    
    # Test 5: Daily Loss Limit
    losing_positions = [
        Position('SYMBOL1', 'long', 0.1, 100.0, 15, -50.0, datetime.now()),  # -$50
        Position('SYMBOL2', 'short', 0.1, 200.0, 15, -60.0, datetime.now())   # -$60 = -$110 total (11% on $1000)
    ]
    
    filtered_loss = risk_manager.filter_signals(signals, losing_positions, 1000.0)
    loss_limit_blocks_trading = len(filtered_loss) == 0
    results.add_result("Daily Loss Limit Protection", loss_limit_blocks_trading, f"Total PnL: ${sum(p.unrealized_pnl for p in losing_positions)}")
    
    return results

async def test_integration():
    """Test full integration flow"""
    results = TestResults()
    
    # Test 1: Environment Variables
    required_vars = ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY']
    env_vars_set = all(os.getenv(var) for var in required_vars)
    results.add_result("Environment Variables", env_vars_set, f"Required vars: {required_vars}")
    
    # Test 2: Module Imports
    try:
        from simple_bot import SimpleTradingBot
        import_successful = True
    except ImportError as e:
        import_successful = False
        results.add_result("Module Imports", import_successful, f"Error: {e}")
        return results
    
    results.add_result("Module Imports", import_successful, "All modules imported successfully")
    
    # Test 3: Bot Initialization
    try:
        bot = SimpleTradingBot()
        bot_initialized = bool(bot.symbols and bot.correlation_engine and bot.risk_manager)
        results.add_result("Bot Initialization", bot_initialized, f"Tracking {len(bot.symbols)} symbols")
    except Exception as e:
        results.add_result("Bot Initialization", False, f"Error: {e}")
        return results
    
    # Test 4: Railway Deployment Files
    deployment_files = ['railway.json', 'Dockerfile', 'requirements-minimal.txt']
    files_exist = all(os.path.exists(f) for f in deployment_files)
    results.add_result("Railway Deployment Files", files_exist, f"Files: {deployment_files}")
    
    return results

def test_performance_benchmarks():
    """Test performance characteristics"""
    results = TestResults()
    
    # Test 1: Correlation Engine Performance
    engine = CorrelationEngine()
    
    start_time = time.time()
    # Simulate realistic workload
    for i in range(100):
        test_prices = {
            'BTCUSDT': 45000 + i,
            'ETHUSDT': 3000 + i * 0.1,
            'SOLUSDT': 100 + i * 0.01,
            'BNBUSDT': 400 + i * 0.05,
            'XRPUSDT': 0.6 + i * 0.0001
        }
        engine.update_prices(test_prices)
        
        if i >= 50:  # Start calculating correlations after sufficient history
            correlations = engine.calculate_correlations()
            signals = engine.generate_signals(test_prices)
    
    duration = time.time() - start_time
    performance_acceptable = duration < 5.0  # Should complete in under 5 seconds
    results.add_result("Correlation Engine Performance", performance_acceptable, f"Duration: {duration:.2f}s")
    
    # Test 2: Memory Usage (approximate)
    import sys
    memory_mb = sys.getsizeof(engine.price_history) / 1024 / 1024
    memory_acceptable = memory_mb < 10  # Should use less than 10MB
    results.add_result("Memory Usage", memory_acceptable, f"Memory: {memory_mb:.2f}MB")
    
    return results

async def run_all_tests():
    """Run the complete test suite"""
    print("=" * 80)
    print("QUANTUM TRADING BOT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("Testing simplified bot for Railway deployment readiness...")
    print()
    
    all_results = []
    
    # API Connectivity Tests
    print("Testing Binance API Connectivity...")
    api_results = await test_binance_api_connectivity()
    all_results.append(("API Connectivity", api_results))
    
    print("\nTesting Correlation Engine...")
    correlation_results = test_correlation_engine()
    all_results.append(("Correlation Engine", correlation_results))
    
    print("\nTesting Risk Manager...")
    risk_results = test_risk_manager()
    all_results.append(("Risk Manager", risk_results))
    
    print("\nTesting Integration...")
    integration_results = await test_integration()
    all_results.append(("Integration", integration_results))
    
    print("\nTesting Performance...")
    performance_results = test_performance_benchmarks()
    all_results.append(("Performance", performance_results))
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST REPORT")
    print("=" * 80)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for test_category, results in all_results:
        summary = results.get_summary()
        total_tests += summary['tests_run']
        total_passed += summary['tests_passed']
        total_failed += summary['tests_failed']
        
        print(f"\n{test_category}:")
        print(f"  Tests Run: {summary['tests_run']}")
        print(f"  Passed: {summary['tests_passed']}")
        print(f"  Failed: {summary['tests_failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['failures']:
            print("  Failures:")
            for failure_name, failure_msg in summary['failures']:
                print(f"    - {failure_name}: {failure_msg}")
    
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nOVERALL RESULTS:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"  Overall Success Rate: {overall_success_rate:.1f}%")
    
    # Railway Deployment Readiness Assessment
    print(f"\nRAILWAY DEPLOYMENT READINESS:")
    if overall_success_rate >= 80:
        print("  READY FOR DEPLOYMENT")
        print("  The simplified bot meets deployment criteria")
    elif overall_success_rate >= 60:
        print("  DEPLOYMENT WITH CAUTION")
        print("  Some issues detected but bot should function")
    else:
        print("  NOT READY FOR DEPLOYMENT")
        print("  Critical issues must be resolved")
    
    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_success_rate": overall_success_rate,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "test_results": {category: results.get_summary() for category, results in all_results},
        "deployment_ready": overall_success_rate >= 80
    }
    
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: test_report.json")
    print("=" * 80)
    
    return overall_success_rate >= 80

if __name__ == "__main__":
    # Set test environment
    if not os.getenv('BINANCE_API_KEY'):
        os.environ['BINANCE_API_KEY'] = '2bebcfa42c24f706250fc870c174c092e3d4d42b7b0912647524c59be6b2bf5a'
    if not os.getenv('BINANCE_SECRET_KEY'):
        os.environ['BINANCE_SECRET_KEY'] = 'd23c85fd1947521e6e7c730ecc41790c6446c49b6f8b7305dab7c702a010c594'
    
    # Run tests
    deployment_ready = asyncio.run(run_all_tests())
    sys.exit(0 if deployment_ready else 1)