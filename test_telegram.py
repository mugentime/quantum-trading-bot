#!/usr/bin/env python3
"""Test script for Telegram notifications"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.telegram_notifier import telegram_notifier

async def test_telegram_notifications():
    """Test all types of Telegram notifications"""
    print("Testing Telegram Notifications...")
    
    # Test basic message
    print("Testing basic message...")
    success = await telegram_notifier.send_message("Test message from Quantum Trading Bot")
    print(f"Basic message: {'SUCCESS' if success else 'FAILED'}")
    
    await asyncio.sleep(2)
    
    # Test buy order notification
    print("Testing buy order notification...")
    success = await telegram_notifier.send_buy_order_alert(
        symbol="BTCUSDT",
        price=43250.50,
        quantity=0.0023,
        stop_loss=42000.00,
        take_profit=45000.00,
        reason="Test buy order - High correlation signal detected"
    )
    print(f"Buy order alert: {'SUCCESS' if success else 'FAILED'}")
    
    await asyncio.sleep(2)
    
    # Test sell order notification
    print("📱 Testing sell order notification...")
    success = await telegram_notifier.send_sell_order_alert(
        symbol="BTCUSDT",
        price=44100.75,
        quantity=0.0023,
        pnl=195.46,
        pnl_percent=4.52,
        reason="Test sell order - Take profit reached"
    )
    print(f"🔴 Sell order alert: {'SUCCESS' if success else 'FAILED'}")
    
    await asyncio.sleep(2)
    
    # Test price alert
    print("📱 Testing price alert...")
    success = await telegram_notifier.send_price_alert(
        symbol="BTCUSDT",
        current_price=43850.25,
        change_percent=2.34,
        timeframe="1h"
    )
    print(f"📈 Price alert: {'SUCCESS' if success else 'FAILED'}")
    
    await asyncio.sleep(2)
    
    # Test error alert
    print("📱 Testing error alert...")
    success = await telegram_notifier.send_error_alert(
        error_type="Test Error",
        error_message="This is a test error notification",
        symbol="BTCUSDT"
    )
    print(f"🚨 Error alert: {'SUCCESS' if success else 'FAILED'}")
    
    await asyncio.sleep(2)
    
    # Test status update
    print("📱 Testing status update...")
    success = await telegram_notifier.send_status_update(
        active_positions=3,
        total_pnl=456.78,
        win_rate=67.5,
        daily_trades=12
    )
    print(f"📊 Status update: {'SUCCESS' if success else 'FAILED'}")
    
    print("\n🎉 Telegram notification tests completed!")

async def test_price_monitoring():
    """Test continuous price monitoring simulation"""
    print("\n📊 Testing price monitoring simulation...")
    
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    for symbol in symbols:
        # Simulate price changes
        base_price = 43000 if symbol == "BTCUSDT" else (2800 if symbol == "ETHUSDT" else 150)
        change = 2.5 if symbol == "BTCUSDT" else (-1.8 if symbol == "ETHUSDT" else 5.2)
        
        await telegram_notifier.send_price_alert(
            symbol=symbol,
            current_price=base_price,
            change_percent=change,
            timeframe="5m"
        )
        
        await asyncio.sleep(1)
    
    print("✅ Price monitoring simulation completed!")

def main():
    """Main test function"""
    print("Starting Telegram Notification Tests")
    print("=" * 50)
    
    # Check if Telegram is configured
    if not telegram_notifier.enabled:
        print("❌ Telegram notifications are not configured!")
        print("Please check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the .env file")
        return
    
    print("✅ Telegram notifications are configured")
    print(f"📱 Bot Token: {telegram_notifier.bot_token[:15]}...")
    print(f"💬 Chat ID: {telegram_notifier.chat_id}")
    print()
    
    # Run tests
    try:
        # Run notification tests
        asyncio.run(test_telegram_notifications())
        
        print("\n" + "=" * 50)
        
        # Run price monitoring simulation
        asyncio.run(test_price_monitoring())
        
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()