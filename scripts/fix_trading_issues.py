#!/usr/bin/env python3
"""
Script to diagnose and fix trading execution issues on Railway deployment
Identifies why signals aren't converting to trades
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.settings import config
from core.executor import Executor
from core.risk_manager import risk_manager
from core.data_collector import DataCollector
from core.signal_generator import SignalGenerator
from core.correlation_engine import CorrelationEngine

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TradingDiagnostics:
    """Comprehensive diagnostic tool for trading issues"""
    
    def __init__(self):
        self.issues_found = []
        self.warnings = []
        self.executor = None
        self.data_collector = None
        
    async def run_full_diagnostics(self):
        """Run complete diagnostic suite"""
        print("="*80)
        print("QUANTUM TRADING BOT - COMPREHENSIVE DIAGNOSTICS")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*80)
        
        # 1. Check Environment Settings
        await self.check_environment_settings()
        
        # 2. Test API Connectivity
        await self.test_api_connectivity()
        
        # 3. Check Account Balance and Permissions
        await self.check_account_status()
        
        # 4. Test Signal Generation
        await self.test_signal_generation()
        
        # 5. Test Risk Management
        await self.test_risk_management()
        
        # 6. Test Order Execution (dry run)
        await self.test_order_execution()
        
        # 7. Generate Report
        self.generate_report()
        
    async def check_environment_settings(self):
        """Check critical environment settings"""
        print("\n1. ENVIRONMENT SETTINGS CHECK:")
        print("-"*40)
        
        # Check if we're in testnet mode
        if config.BINANCE_TESTNET:
            self.issues_found.append("TESTNET MODE ACTIVE - Using testnet API (no real trades)")
            print("[X] TESTNET MODE: Enabled (no real trading)")
        else:
            print("[OK] Production mode active")
        
        # Check API keys
        if not config.BINANCE_API_KEY:
            self.issues_found.append("BINANCE_API_KEY not set")
            print("[X] API Key: NOT SET")
        else:
            print(f"[OK] API Key: {config.BINANCE_API_KEY[:8]}...")
        
        if not config.BINANCE_SECRET_KEY:
            self.issues_found.append("BINANCE_SECRET_KEY not set")
            print("[X] Secret Key: NOT SET")
        else:
            print("[OK] Secret Key: Set")
        
        # Check DEBUG mode
        if config.DEBUG:
            self.warnings.append("DEBUG mode active - may affect performance")
            print("[!] DEBUG mode: Enabled")
        
        # Check risk parameters
        print(f"\nRisk Parameters:")
        print(f"  Risk per trade: {config.RISK_PER_TRADE * 100}%")
        print(f"  Max concurrent positions: {config.MAX_CONCURRENT_POSITIONS}")
        print(f"  Default leverage: {config.DEFAULT_LEVERAGE}x")
        print(f"  Stop loss: {config.STOP_LOSS_PERCENT * 100}%")
        
    async def test_api_connectivity(self):
        """Test connection to Binance API"""
        print("\n2. API CONNECTIVITY TEST:")
        print("-"*40)
        
        try:
            import ccxt.async_support as ccxt
            
            exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'sandbox': config.BINANCE_TESTNET,
                'enableRateLimit': True
            })
            
            # Test public API
            ticker = await exchange.fetch_ticker('ETHUSDT')
            print(f"[OK] Public API: ETHUSDT price ${ticker['last']:.2f}")
            
            # Test private API
            try:
                balance = await exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                print(f"[OK] Private API: Account balance ${usdt_balance:.2f}")
                
                if usdt_balance < 10:
                    self.issues_found.append(f"Insufficient balance: ${usdt_balance:.2f}")
                    print(f"[X] Balance too low for trading: ${usdt_balance:.2f}")
                    
            except Exception as e:
                self.issues_found.append(f"Private API error: {str(e)[:100]}")
                print(f"[X] Private API failed: {str(e)[:100]}")
            
            await exchange.close()
            
        except Exception as e:
            self.issues_found.append(f"API connection failed: {str(e)[:100]}")
            print(f"[X] API connection failed: {str(e)[:100]}")
    
    async def check_account_status(self):
        """Check account permissions and status"""
        print("\n3. ACCOUNT STATUS CHECK:")
        print("-"*40)
        
        try:
            import ccxt.async_support as ccxt
            
            exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'sandbox': config.BINANCE_TESTNET,
                'enableRateLimit': True
            })
            
            # Check account info
            account = await exchange.fetch_status()
            print(f"[OK] Exchange status: {account.get('status', 'unknown')}")
            
            # Check trading permissions
            try:
                # Try to fetch open orders (requires trading permission)
                open_orders = await exchange.fetch_open_orders()
                print(f"[OK] Trading permissions: Active ({len(open_orders)} open orders)")
            except Exception as e:
                if 'API-key' in str(e) or 'permission' in str(e).lower():
                    self.issues_found.append("API key lacks trading permissions")
                    print("[X] Trading permissions: DENIED")
                else:
                    print(f"[!] Trading permission check error: {str(e)[:50]}")
            
            await exchange.close()
            
        except Exception as e:
            print(f"[X] Account check failed: {str(e)[:100]}")
    
    async def test_signal_generation(self):
        """Test if signals are being generated"""
        print("\n4. SIGNAL GENERATION TEST:")
        print("-"*40)
        
        try:
            # Initialize components
            data_collector = DataCollector(config.SYMBOLS)
            correlation_engine = CorrelationEngine()
            signal_generator = SignalGenerator()
            
            # Start data collection
            await data_collector.start()
            await asyncio.sleep(2)  # Let it collect some data
            
            # Get market data
            market_data = await data_collector.get_latest_data()
            
            if not market_data:
                self.issues_found.append("No market data available")
                print("[X] No market data collected")
                return
            
            print(f"[OK] Market data collected for {len(market_data)} symbols")
            
            # Calculate correlations
            correlations = correlation_engine.calculate(market_data)
            print(f"[OK] Correlations calculated: {len(correlations) if correlations else 0} pairs")
            
            # Generate signals
            signals = signal_generator.generate(correlations, market_data)
            
            if not signals:
                self.warnings.append("No signals generated from current market data")
                print("[!] No signals generated (market conditions may not be favorable)")
            else:
                print(f"[OK] {len(signals)} signals generated")
                for signal in signals[:3]:  # Show first 3
                    print(f"    - {signal.get('symbol')}: {signal.get('action')} "
                          f"(confidence: {signal.get('confidence', 0):.2f})")
            
            await data_collector.stop()
            
        except Exception as e:
            self.issues_found.append(f"Signal generation failed: {str(e)[:100]}")
            print(f"[X] Signal generation error: {str(e)[:100]}")
    
    async def test_risk_management(self):
        """Test risk management filters"""
        print("\n5. RISK MANAGEMENT TEST:")
        print("-"*40)
        
        # Create test signals
        test_signals = [
            {
                'symbol': 'ETHUSDT',
                'action': 'long',
                'confidence': 0.8,
                'price': 2000,
                'entry_price': 2000,
                'stop_loss': 1960,
                'take_profit': 2080
            },
            {
                'symbol': 'AVAXUSDT',
                'action': 'long',
                'confidence': 0.2,  # Low confidence - should be filtered
                'price': 30,
                'entry_price': 30,
                'stop_loss': 29.4,
                'take_profit': 30.9
            }
        ]
        
        try:
            # Test risk filters
            approved = risk_manager.filter_signals(test_signals)
            
            print(f"[OK] Risk manager active")
            print(f"    Input signals: {len(test_signals)}")
            print(f"    Approved signals: {len(approved)}")
            
            if len(approved) == 0 and len(test_signals) > 0:
                self.warnings.append("Risk manager filtering ALL signals")
                print("[!] WARNING: Risk manager is filtering all signals")
                
                # Check why signals are being filtered
                if hasattr(risk_manager, 'daily_pnl'):
                    print(f"    Daily P&L: ${risk_manager.daily_pnl:.2f}")
                if hasattr(risk_manager, 'current_positions'):
                    print(f"    Current positions: {risk_manager.current_positions}")
                    
        except Exception as e:
            self.issues_found.append(f"Risk management error: {str(e)[:100]}")
            print(f"[X] Risk management error: {str(e)[:100]}")
    
    async def test_order_execution(self):
        """Test order execution (dry run)"""
        print("\n6. ORDER EXECUTION TEST (DRY RUN):")
        print("-"*40)
        
        # Create test signal
        test_signal = {
            'id': 'test_001',
            'symbol': 'ETHUSDT',
            'action': 'long',
            'confidence': 0.8,
            'price': 2000,
            'entry_price': 2000,
            'stop_loss': 1960,
            'take_profit': 2080,
            'position_size': 0.01  # Small test size
        }
        
        try:
            executor = Executor()
            
            # Initialize exchange connection
            if await executor.initialize_exchange():
                print("[OK] Exchange connection established")
                
                # Check if we can calculate position size
                balance = await executor._get_account_balance()
                print(f"[OK] Account balance retrieved: ${balance:.2f}")
                
                # Calculate position size
                position = await executor._calculate_position_size(test_signal, balance)
                print(f"[OK] Position size calculated: {position:.6f}")
                
                # We won't actually place the order in diagnostics
                print("[SKIP] Actual order placement skipped (diagnostic mode)")
                
                if config.BINANCE_TESTNET:
                    print("[!] NOTE: Testnet mode - would use paper money")
                else:
                    print("[!] NOTE: Production mode - would use real money")
                    
            else:
                self.issues_found.append("Cannot connect to exchange for execution")
                print("[X] Exchange connection failed")
                
        except Exception as e:
            self.issues_found.append(f"Execution test failed: {str(e)[:100]}")
            print(f"[X] Execution test error: {str(e)[:100]}")
    
    def generate_report(self):
        """Generate final diagnostic report"""
        print("\n" + "="*80)
        print("DIAGNOSTIC SUMMARY")
        print("="*80)
        
        if self.issues_found:
            print("\nCRITICAL ISSUES FOUND:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n[OK] No critical issues found")
        
        if self.warnings:
            print("\nWARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print("\nRECOMMENDED FIXES:")
        print("-"*40)
        
        if any('TESTNET' in issue for issue in self.issues_found):
            print("1. SWITCH TO PRODUCTION MODE:")
            print("   - Set BINANCE_TESTNET=false in .env file")
            print("   - Restart the bot")
        
        if any('API' in issue for issue in self.issues_found):
            print("2. FIX API CONFIGURATION:")
            print("   - Ensure API keys are set correctly in .env")
            print("   - Enable trading permissions in Binance API settings")
            print("   - Enable futures trading if using leverage")
        
        if any('balance' in issue.lower() for issue in self.issues_found):
            print("3. ADD TRADING FUNDS:")
            print("   - Deposit USDT to your Binance account")
            print("   - Minimum recommended: $100 for testing")
        
        if any('filtering ALL' in warning for warning in self.warnings):
            print("4. ADJUST RISK PARAMETERS:")
            print("   - Lower confidence threshold in risk_manager.py")
            print("   - Check daily loss limits haven't been hit")
            print("   - Verify position limits aren't exceeded")
        
        print("\n5. ENABLE COMPREHENSIVE LOGGING:")
        print("   - Add detailed logging to signal generation")
        print("   - Log all risk management decisions")
        print("   - Track signal -> execution pipeline")
        
        print("\n6. DEPLOY MONITORING DASHBOARD:")
        print("   - Create web interface for real-time monitoring")
        print("   - Show signals, trades, P&L in real-time")
        print("   - Add manual trading controls")

async def main():
    """Run diagnostics"""
    diagnostics = TradingDiagnostics()
    await diagnostics.run_full_diagnostics()

if __name__ == "__main__":
    asyncio.run(main())