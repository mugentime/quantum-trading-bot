#!/usr/bin/env python3
"""Manual position synchronization tool to override bot tracking with actual positions"""
import json
from datetime import datetime

def update_manual_positions():
    """Update the manual position override file with current actual positions"""
    
    print("MANUAL POSITION SYNC")
    print("=" * 40)
    print("Enter your ACTUAL Binance testnet positions:")
    print("(Based on your GUI: ETHUSDT LONG @ 2794.03 +$1519, BTCUSDT LONG @ 112553.70 -$1979)")
    print()
    
    # Your actual positions from the GUI
    manual_positions = {
        "timestamp": datetime.now().isoformat(),
        "source": "Manual GUI Override",
        "account_balance": 7726.67,  # Estimated from your data
        "active_positions": {
            "ETHUSDT": {
                "symbol": "ETHUSDT",
                "side": "BUY",  # LONG position
                "entry_price": 2794.03,
                "quantity": 1.000,  # Size shown as 1.000 ETH
                "unrealized_pnl": 1519.00,
                "roe_percentage": 704.35,
                "entry_time": "2025-08-29T08:00:00",  # Estimated
                "leverage": 20,
                "margin": 215.66,
                "take_profit": None,
                "stop_loss": None,
                "order_id": "manual_eth",
                "status": "ACTIVE"
            },
            "BTCUSDT": {
                "symbol": "BTCUSDT", 
                "side": "BUY",  # LONG position
                "entry_price": 112553.70,
                "quantity": 0.444,  # Size shown as 0.444 BTC
                "unrealized_pnl": -1979.70,
                "roe_percentage": -515.59,
                "entry_time": "2025-08-29T06:00:00",  # Estimated  
                "leverage": 125,
                "margin": 383.97,
                "take_profit": None,
                "stop_loss": None,
                "order_id": "manual_btc",
                "status": "ACTIVE"
            }
        },
        "total_unrealized_pnl": 1519.00 - 1979.70,  # Net PnL
        "notes": "Manual override - GUI positions don't match bot tracking"
    }
    
    # Save manual positions
    with open('manual_positions_override.json', 'w') as f:
        json.dump(manual_positions, f, indent=2)
    
    print("Manual positions saved to: manual_positions_override.json")
    print(f"Net Unrealized PnL: ${manual_positions['total_unrealized_pnl']:.2f}")
    print()
    print("ACTIVE POSITIONS:")
    for symbol, pos in manual_positions['active_positions'].items():
        print(f"  {symbol}: {pos['side']} {pos['quantity']:.4f} @ ${pos['entry_price']:.2f}")
        print(f"    PnL: ${pos['unrealized_pnl']:.2f} ({pos['roe_percentage']:.2f}%)")
    print()
    print("This override will be used by the hourly status reporter.")
    
    return manual_positions

if __name__ == "__main__":
    update_manual_positions()