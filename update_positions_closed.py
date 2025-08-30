#!/usr/bin/env python3
"""Update manual positions to reflect closed positions"""
import json
from datetime import datetime

def update_positions_closed():
    """Update manual override to show all positions closed"""
    
    # No active positions since user closed them
    closed_positions = {
        "timestamp": datetime.now().isoformat(),
        "source": "Manual GUI Override - Positions Closed",
        "account_balance": 7726.67,  # Base balance
        "active_positions": {},  # No active positions
        "total_unrealized_pnl": 0.00,
        "recent_closes": {
            "ETHUSDT": {
                "closed_pnl": 1519.00,  # Profit from the LONG position
                "closed_time": datetime.now().isoformat(),
                "reason": "Manual close"
            },
            "BTCUSDT": {
                "closed_pnl": -1979.70,  # Loss from the LONG position
                "closed_time": datetime.now().isoformat(),
                "reason": "Manual close"
            }
        },
        "net_session_pnl": 1519.00 - 1979.70,  # Net result: -$460.70
        "notes": "All positions manually closed by user"
    }
    
    # Save updated positions
    with open('manual_positions_override.json', 'w') as f:
        json.dump(closed_positions, f, indent=2)
    
    print("POSITIONS UPDATE - ALL CLOSED")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Active Positions: 0")
    print(f"Net Session P&L: ${closed_positions['net_session_pnl']:.2f}")
    print()
    print("RECENTLY CLOSED:")
    for symbol, close_data in closed_positions['recent_closes'].items():
        result = "PROFIT" if close_data['closed_pnl'] > 0 else "LOSS"
        print(f"  {symbol}: ${close_data['closed_pnl']:.2f} ({result})")
    print()
    print("Manual override updated - hourly reports will show no active positions")
    
    return closed_positions

if __name__ == "__main__":
    update_positions_closed()