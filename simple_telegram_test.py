#!/usr/bin/env python3
"""Simple test script for Telegram notifications"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.telegram_notifier import telegram_notifier

async def test_basic_message():
    """Test basic Telegram message"""
    print("Testing basic Telegram message...")
    
    # Test basic message
    success = await telegram_notifier.send_message("Test message from Quantum Trading Bot")
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    return success

async def test_buy_notification():
    """Test buy order notification"""
    print("Testing buy order notification...")
    
    success = await telegram_notifier.send_buy_order_alert(
        symbol="BTCUSDT",
        price=43250.50,
        quantity=0.0023,
        stop_loss=42000.00,
        take_profit=45000.00,
        reason="Test buy order"
    )
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    return success

async def test_sell_notification():
    """Test sell order notification"""
    print("Testing sell order notification...")
    
    success = await telegram_notifier.send_sell_order_alert(
        symbol="BTCUSDT",
        price=44100.75,
        quantity=0.0023,
        pnl=195.46,
        pnl_percent=4.52,
        reason="Test sell order"
    )
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    return success

async def main():
    """Main test function"""
    print("Starting Telegram Notification Tests")
    print("=" * 40)
    
    # Check if Telegram is configured
    if not telegram_notifier.enabled:
        print("ERROR: Telegram notifications are not configured!")
        print("Please check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the .env file")
        return
    
    print("Telegram notifications are configured")
    print(f"Bot Token: {telegram_notifier.bot_token[:15]}...")
    print(f"Chat ID: {telegram_notifier.chat_id}")
    print()
    
    # Run tests
    try:
        results = []
        
        # Test basic message
        results.append(await test_basic_message())
        await asyncio.sleep(2)
        
        # Test buy notification
        results.append(await test_buy_notification())
        await asyncio.sleep(2)
        
        # Test sell notification
        results.append(await test_sell_notification())
        
        print("\n" + "=" * 40)
        print(f"Tests completed: {sum(results)}/{len(results)} successful")
        
    except KeyboardInterrupt:
        print("Tests interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())