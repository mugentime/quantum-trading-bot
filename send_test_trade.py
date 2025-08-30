#!/usr/bin/env python3
"""
Send a test trade to verify the complete trading system
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.environment_manager import environment_manager, Environment
from core.data_authenticity_validator import authenticity_validator
from core.executor import Executor
from core.enhanced_correlation_engine import EnhancedCorrelationEngine
from utils.telegram_notifier import telegram_notifier
from utils.logger import setup_logger

logger = setup_logger('test_trade')

async def send_test_trade():
    """Send a test trade to verify system functionality"""
    try:
        logger.info("=" * 60)
        logger.info("SENDING TEST TRADE - QUANTUM TRADING BOT")
        logger.info("=" * 60)
        
        # Initialize environment
        env_type = Environment.TESTNET
        if not environment_manager.initialize_environment(env_type):
            raise Exception("Failed to initialize testnet environment")
        
        logger.info(f"Environment: {env_type.value} - VALIDATED")
        
        # Send startup notification
        await telegram_notifier.send_message(
            "🚀 TEST TRADE EXECUTION STARTING\n"
            f"Environment: {env_type.value}\n"
            f"Security: All validations ACTIVE\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Initialize executor
        executor = Executor()
        if not await executor.initialize_exchange():
            raise Exception("Failed to initialize exchange connection")
        
        logger.info("Exchange connection established")
        
        # Get account balance
        account_balance = await executor._get_account_balance()
        logger.info(f"Account balance: ${account_balance:.2f}")
        
        # Create test signal for ETHUSDT
        test_signal = {
            'id': f'test_{int(datetime.now().timestamp())}',
            'symbol': 'ETHUSDT',
            'action': 'BUY',
            'entry_price': 4300.0,  # Approximate current price
            'confidence': 0.75,
            'deviation': 0.35,
            'correlation': 0.65,
            'position_size': 0.01,  # Small test position
            'stop_loss': 4200.0,
            'take_profit': 4400.0,
            'timestamp': datetime.now().isoformat(),
            'source': 'test_trade_manual'
        }
        
        logger.info(f"Generated test signal: {test_signal['symbol']} {test_signal['action']}")
        
        # Validate signal authenticity 
        if not authenticity_validator.validate_market_data(test_signal, "test_signal"):
            raise Exception("Test signal failed authenticity validation")
        
        logger.info("Signal passed authenticity validation")
        
        # Send pre-execution notification
        await telegram_notifier.send_message(
            f"🎯 EXECUTING TEST TRADE\n"
            f"Symbol: {test_signal['symbol']}\n"
            f"Action: {test_signal['action']}\n"
            f"Price Target: ${test_signal['entry_price']:.2f}\n"
            f"Confidence: {test_signal['confidence']:.1%}\n"
            f"Account Balance: ${account_balance:.2f}"
        )
        
        # Execute the trade
        logger.info("Executing test trade...")
        result = await executor.execute(test_signal)
        
        # Report results
        if result.status == "FILLED":
            logger.info(f"✅ TEST TRADE SUCCESSFUL!")
            logger.info(f"Order ID: {result.order_id}")
            logger.info(f"Executed Price: ${result.executed_price:.2f}")
            logger.info(f"Quantity: {result.executed_quantity:.4f}")
            logger.info(f"Slippage: {result.slippage:.3f}%" if result.slippage else "N/A")
            
            await telegram_notifier.send_message(
                f"✅ TEST TRADE EXECUTED SUCCESSFULLY!\n\n"
                f"📊 TRADE DETAILS:\n"
                f"Order ID: {result.order_id}\n"
                f"Symbol: {result.symbol}\n"
                f"Action: {result.action}\n"
                f"Executed Price: ${result.executed_price:.2f}\n"
                f"Quantity: {result.executed_quantity:.4f}\n"
                f"Execution Time: {result.execution_time_ms}ms\n"
                f"Slippage: {result.slippage:.3f}%" if result.slippage else "No slippage data" + "\n\n"
                f"🔒 SECURITY STATUS: All validations passed\n"
                f"🚀 OPTIMIZATION: Enhanced signal processing active\n"
                f"📈 System is fully operational and ready for live trading!"
            )
            
        else:
            logger.error(f"❌ TEST TRADE FAILED: {result.status}")
            logger.error(f"Error: {result.error_message}")
            
            await telegram_notifier.send_error_alert(
                "Test Trade Failed",
                f"Status: {result.status}\nError: {result.error_message}",
                test_signal['symbol']
            )
        
        # Cleanup
        await executor.cleanup()
        logger.info("Test trade execution completed")
        
    except Exception as e:
        logger.error(f"Test trade error: {e}", exc_info=True)
        try:
            await telegram_notifier.send_error_alert(
                "Test Trade System Error",
                str(e),
                "SYSTEM"
            )
        except:
            pass

if __name__ == "__main__":
    print("🧪 QUANTUM TRADING BOT - TEST TRADE EXECUTION")
    print("=" * 50)
    
    try:
        asyncio.run(send_test_trade())
    except KeyboardInterrupt:
        print("\n[STOPPED] Test trade stopped by user")
    except Exception as e:
        print(f"[ERROR] Test trade error: {e}")
        sys.exit(1)