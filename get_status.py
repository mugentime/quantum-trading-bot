#!/usr/bin/env python3
"""Get current trading bot status and AI assessment"""
import json
import sys
import os
from datetime import datetime
import asyncio

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.telegram_notifier import telegram_notifier

def analyze_performance():
    """Analyze trading performance and generate AI assessment"""
    
    # Load test data
    try:
        with open('testnet_progress_20250828.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("No trading data found!")
        return
    
    # Calculate metrics
    initial_balance = data['initial_balance']
    completed_trades = data['completed_trades']
    active_positions = data['active_positions']
    
    total_trades = len(completed_trades)
    total_pnl_usd = sum(trade['pnl_usd'] for trade in completed_trades)
    total_pnl_pct = (total_pnl_usd / initial_balance) * 100
    
    winning_trades = [t for t in completed_trades if t['pnl_usd'] > 0]
    losing_trades = [t for t in completed_trades if t['pnl_usd'] <= 0]
    
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    current_balance = initial_balance + total_pnl_usd
    active_count = len(active_positions)
    
    # Calculate additional metrics
    avg_win = sum(t['pnl_usd'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t['pnl_usd'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    profit_factor = abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if losing_trades else float('inf')
    
    # Generate report
    print("=" * 60)
    print("🤖 QUANTUM TRADING BOT - LIVE STATUS REPORT")
    print("=" * 60)
    print(f"📅 Start Time: {data['start_time']}")
    print(f"💰 Initial Balance: ${initial_balance:,.2f} USDT")
    print(f"💰 Current Balance: ${current_balance:,.2f} USDT")
    print(f"📈 Net P&L: ${total_pnl_usd:+.2f} USDT ({total_pnl_pct:+.3f}%)")
    print()
    
    print("📊 PERFORMANCE METRICS")
    print("-" * 40)
    print(f"🔢 Total Trades Closed: {total_trades}")
    print(f"✅ Winning Trades: {len(winning_trades)}")
    print(f"❌ Losing Trades: {len(losing_trades)}")
    print(f"🎯 Win Rate: {win_rate:.1f}%")
    print(f"💵 Average Win: ${avg_win:.2f}")
    print(f"💸 Average Loss: ${avg_loss:.2f}")
    print(f"⚖️ Profit Factor: {profit_factor:.2f}")
    print(f"🔄 Active Positions: {active_count}")
    print()
    
    print("📝 CLOSED TRADES DETAILS")
    print("-" * 40)
    for i, trade in enumerate(completed_trades, 1):
        status_icon = "✅" if trade['pnl_usd'] > 0 else "❌"
        print(f"{status_icon} Trade {i}: {trade['symbol']} {trade['side']}")
        print(f"   📍 Entry: ${trade['entry_price']} → Exit: ${trade['exit_price']}")
        print(f"   💰 P&L: ${trade['pnl_usd']:+.2f} ({trade['pnl_pct']:+.2f}%)")
        print(f"   📊 Quantity: {trade['quantity']} | Reason: {trade['exit_reason']}")
        print(f"   🔗 Correlation: {trade['correlation']:.3f} | Deviation: {trade['deviation']:.3f}")
        print()
    
    print("🔄 ACTIVE POSITIONS")
    print("-" * 40)
    if active_positions:
        for symbol, pos in active_positions.items():
            print(f"📈 {symbol} {pos['side']}:")
            print(f"   💰 Entry: ${pos['entry_price']} | Quantity: {pos['quantity']}")
            print(f"   🎯 Take Profit: ${pos['take_profit']}")
            print(f"   🛑 Stop Loss: ${pos['stop_loss']}")
            print(f"   🔗 Correlation: {pos['correlation']:.3f}")
            print(f"   📊 Deviation: {pos['deviation']:.3f}")
            print()
    else:
        print("No active positions")
        print()
    
    # AI Assessment
    print("🧠 AI PERFORMANCE ASSESSMENT")
    print("-" * 40)
    
    if total_trades == 0:
        assessment = "⏳ STARTING PHASE: No trades completed yet. System is initializing."
        risk_level = "LOW"
    elif total_pnl_pct > 2:
        assessment = "🚀 EXCELLENT: Strong positive performance with good risk management."
        risk_level = "LOW"
    elif total_pnl_pct > 0.5:
        assessment = "✅ GOOD: Positive returns showing profitable strategy execution."
        risk_level = "MODERATE"
    elif total_pnl_pct > -0.5:
        assessment = "⚠️ NEUTRAL: Break-even performance. Monitor for improvement."
        risk_level = "MODERATE"
    elif total_pnl_pct > -2:
        assessment = "⚠️ UNDERPERFORMING: Small losses. Strategy needs adjustment."
        risk_level = "HIGH"
    else:
        assessment = "🚨 POOR: Significant losses. Consider stopping and reviewing strategy."
        risk_level = "VERY HIGH"
    
    print(f"Status: {assessment}")
    print(f"Risk Level: {risk_level}")
    
    if win_rate > 60:
        print("✅ Win rate is healthy above 60%")
    elif win_rate > 40:
        print("⚠️ Win rate is moderate - room for improvement")
    else:
        print("🚨 Low win rate - strategy may need adjustment")
    
    if profit_factor > 1.5:
        print("✅ Good profit factor - wins outweigh losses")
    elif profit_factor > 1.0:
        print("⚠️ Marginal profit factor - barely profitable")
    else:
        print("🚨 Poor profit factor - losses exceed wins")
    
    print()
    print("🎯 RECOMMENDATIONS:")
    if total_pnl_pct > 1:
        print("• Continue current strategy - performing well")
        print("• Consider increasing position sizes gradually")
    elif total_pnl_pct > 0:
        print("• Strategy is working but could be optimized")
        print("• Monitor correlation thresholds")
    else:
        print("• Review and adjust correlation parameters")
        print("• Consider reducing position sizes")
        print("• Analyze failed trades for patterns")
    
    print()
    print("=" * 60)
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl_usd': total_pnl_usd,
        'total_pnl_pct': total_pnl_pct,
        'active_positions': active_count,
        'assessment': assessment,
        'risk_level': risk_level
    }

async def send_status_to_telegram(stats):
    """Send status update to Telegram"""
    try:
        await telegram_notifier.send_status_update(
            active_positions=stats['active_positions'],
            total_pnl=stats['total_pnl_usd'],
            win_rate=stats['win_rate'],
            daily_trades=stats['total_trades']
        )
        print("✅ Status sent to Telegram!")
    except Exception as e:
        print(f"❌ Failed to send to Telegram: {e}")

def main():
    """Main function"""
    stats = analyze_performance()
    
    if stats:
        # Ask user if they want to send to Telegram
        try:
            send_tg = input("\nSend status update to Telegram? (y/N): ").lower().strip()
            if send_tg in ['y', 'yes']:
                asyncio.run(send_status_to_telegram(stats))
        except KeyboardInterrupt:
            print("\nSkipping Telegram notification")

if __name__ == "__main__":
    main()