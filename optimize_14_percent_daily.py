#!/usr/bin/env python3
"""
14% Daily Target Optimization Engine
Focused backtest with optimal leverage configuration
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from core.data_collector import DataCollector
from core.correlation_engine import CorrelationEngine
from core.signal_generator import SignalGenerator
from core.config.settings import config
import ccxt.async_support as ccxt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedBacktester:
    def __init__(self):
        self.initial_balance = 10000
        self.target_daily_return = 0.14  # 14%
        
        # Optimized configuration based on analysis
        self.focus_pairs = ['ETHUSDT', 'AXSUSDT']  # Include AXSUSDT for 620% monthly target
        self.leverage_config = {
            'ETHUSDT': 8.5,  # Lower risk, higher win rate
            'AXSUSDT': 8.5   # AXSUSDT for ultra-high frequency trading
        }
        
        # Risk management
        self.position_size_pct = 0.8  # 80% of account per trade
        self.max_concurrent_trades = 1
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.08  # 8% take profit
        
        # Initialize components
        self.data_collector = DataCollector(config.SYMBOLS)
        self.correlation_engine = CorrelationEngine()
        self.signal_generator = SignalGenerator()
        
    async def run_optimized_backtest(self):
        """Run focused backtest for 14% daily target"""
        logger.info("Starting 14% Daily Target Optimization Backtest")
        
        results = {}
        
        for symbol in self.focus_pairs:
            logger.info(f"Testing {symbol} with {self.leverage_config[symbol]}x leverage")
            
            # Get historical data
            data = await self.data_collector.fetch_historical_data(symbol, '1h', 30*24)  # 30 days
            
            if not data:
                logger.error(f"No data for {symbol}")
                continue
            
            # Run backtest for this symbol
            symbol_results = await self.backtest_symbol(symbol, data)
            results[symbol] = symbol_results
            
            # Calculate leveraged returns
            base_return = symbol_results.get('total_return_pct', 0)
            leveraged_return = base_return * self.leverage_config[symbol]
            daily_return = leveraged_return / 30
            
            logger.info(f"{symbol} Results:")
            logger.info(f"  Base return (30 days): {base_return*100:.2f}%")
            logger.info(f"  Leveraged return: {leveraged_return*100:.2f}%")
            logger.info(f"  Daily return: {daily_return*100:.2f}%")
            logger.info(f"  Target achievement: {(daily_return/self.target_daily_return)*100:.1f}%")
            
        return results
    
    async def backtest_symbol(self, symbol, data):
        """Backtest a single symbol with optimized parameters"""
        balance = self.initial_balance
        trades = []
        position = None
        
        for i in range(len(data) - 24):  # Leave room for correlation window
            current_candle = data[i]
            
            # Get correlation data window
            correlation_window = data[max(0, i-23):i+1]  # 24h window
            
            # Generate signal
            signal = await self.signal_generator.generate_signal(
                symbol, correlation_window, current_candle
            )
            
            if signal and signal.get('confidence', 0) > 0.6:  # High confidence only
                # Close existing position if signal reverses
                if position and position['side'] != signal['action']:
                    trade_result = self.close_position(position, current_candle['close'])
                    trades.append(trade_result)
                    balance += trade_result['pnl_usd']
                    position = None
                
                # Open new position if none exists
                if not position:
                    position_size = balance * self.position_size_pct
                    leverage = self.leverage_config[symbol]
                    effective_size = position_size * leverage
                    
                    position = {
                        'symbol': symbol,
                        'side': signal['action'],
                        'entry_price': current_candle['close'],
                        'quantity': effective_size / current_candle['close'],
                        'entry_time': current_candle['timestamp'],
                        'leverage': leverage,
                        'stop_loss': self.calculate_stop_loss(current_candle['close'], signal['action']),
                        'take_profit': self.calculate_take_profit(current_candle['close'], signal['action'])
                    }
            
            # Check position management
            if position:
                current_price = current_candle['close']
                
                # Check stop loss
                if ((position['side'] == 'BUY' and current_price <= position['stop_loss']) or
                    (position['side'] == 'SELL' and current_price >= position['stop_loss'])):
                    trade_result = self.close_position(position, current_price, 'Stop Loss')
                    trades.append(trade_result)
                    balance += trade_result['pnl_usd']
                    position = None
                
                # Check take profit
                elif ((position['side'] == 'BUY' and current_price >= position['take_profit']) or
                      (position['side'] == 'SELL' and current_price <= position['take_profit'])):
                    trade_result = self.close_position(position, current_price, 'Take Profit')
                    trades.append(trade_result)
                    balance += trade_result['pnl_usd']
                    position = None
        
        # Close any remaining position
        if position:
            final_candle = data[-1]
            trade_result = self.close_position(position, final_candle['close'], 'End of Test')
            trades.append(trade_result)
            balance += trade_result['pnl_usd']
        
        # Calculate metrics
        total_return = (balance - self.initial_balance) / self.initial_balance
        
        winning_trades = [t for t in trades if t['pnl_usd'] > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        return {
            'symbol': symbol,
            'total_return_pct': total_return,
            'final_balance': balance,
            'total_trades': len(trades),
            'win_rate_pct': win_rate * 100,
            'trades': trades,
            'leverage_used': self.leverage_config[symbol]
        }
    
    def calculate_stop_loss(self, entry_price, side):
        """Calculate stop loss price"""
        if side == 'BUY':
            return entry_price * (1 - self.stop_loss_pct)
        else:
            return entry_price * (1 + self.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price, side):
        """Calculate take profit price"""
        if side == 'BUY':
            return entry_price * (1 + self.take_profit_pct)
        else:
            return entry_price * (1 - self.take_profit_pct)
    
    def close_position(self, position, exit_price, reason='Signal'):
        """Close position and calculate P&L"""
        if position['side'] == 'BUY':
            pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
        else:
            pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
        
        # Apply leverage
        leveraged_pnl_pct = pnl_pct * position['leverage']
        pnl_usd = leveraged_pnl_pct * (self.initial_balance * self.position_size_pct)
        
        return {
            'symbol': position['symbol'],
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'pnl_pct': leveraged_pnl_pct,
            'pnl_usd': pnl_usd,
            'exit_reason': reason,
            'leverage': position['leverage']
        }

async def main():
    """Run the 14% daily target optimization"""
    backtester = OptimizedBacktester()
    
    print("🎯 14% DAILY TARGET OPTIMIZATION")
    print("=" * 50)
    print(f"Target Daily Return: {backtester.target_daily_return*100:.1f}%")
    print(f"Focus Pairs: {backtester.focus_pairs}")
    print(f"Leverage Configuration: {backtester.leverage_config}")
    print(f"Position Size: {backtester.position_size_pct*100:.0f}% of account")
    print()
    
    results = await backtester.run_optimized_backtest()
    
    print("\n🏆 OPTIMIZATION RESULTS:")
    print("=" * 50)
    
    best_performer = None
    best_daily_return = 0
    
    for symbol, result in results.items():
        leveraged_return = result['total_return_pct'] * result['leverage_used']
        daily_return = leveraged_return / 30
        
        print(f"\n{symbol}:")
        print(f"  Final Balance: ${result['final_balance']:.2f}")
        print(f"  Total Return: {result['total_return_pct']*100:.2f}%")
        print(f"  Leveraged Return: {leveraged_return*100:.2f}%")
        print(f"  Daily Return: {daily_return*100:.2f}%")
        print(f"  Win Rate: {result['win_rate_pct']:.1f}%")
        print(f"  Total Trades: {result['total_trades']}")
        print(f"  Target Achievement: {(daily_return/backtester.target_daily_return)*100:.1f}%")
        
        if daily_return > best_daily_return:
            best_daily_return = daily_return
            best_performer = symbol
    
    print(f"\n🎯 RECOMMENDATION:")
    print(f"Best Performer: {best_performer}")
    print(f"Best Daily Return: {best_daily_return*100:.2f}%")
    print(f"Target Achievement: {(best_daily_return/backtester.target_daily_return)*100:.1f}%")
    
    if best_daily_return >= backtester.target_daily_return * 0.9:  # 90% of target
        print("✅ TARGET ACHIEVABLE with optimized configuration!")
    else:
        print("⚠️ Target requires further optimization or higher leverage")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"optimized_14pct_daily_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            'optimization_target': '14% daily',
            'configuration': {
                'focus_pairs': backtester.focus_pairs,
                'leverage_config': backtester.leverage_config,
                'position_size_pct': backtester.position_size_pct,
                'stop_loss_pct': backtester.stop_loss_pct,
                'take_profit_pct': backtester.take_profit_pct
            },
            'results': results,
            'best_performer': best_performer,
            'best_daily_return': best_daily_return,
            'target_achievement': (best_daily_return/backtester.target_daily_return)*100,
            'timestamp': timestamp
        }, indent=2)
    
    print(f"\n📊 Detailed results saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())