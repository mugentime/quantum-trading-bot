#!/usr/bin/env python3
"""
Enhanced Leverage Trading System with Intelligent Risk Management
Integrates leverage optimization with the correlation trading strategy
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
import traceback

# Add the parent directory to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_correlation_engine import EnhancedCorrelationEngine
from core.data_collector import DataCollector as EnhancedDataCollector
from core.enhanced_risk_manager import EnhancedRiskManager
from core.signal_generator import SignalGenerator as EnhancedSignalGenerator
from core.executor import TradeExecutor as EnhancedTradeExecutor
from utils.telegram_notifier import TelegramNotifier as EnhancedTelegramNotifier
from utils.logger import setup_logger

class EnhancedLeverageTrader:
    def __init__(self):
        self.logger = setup_logger('leverage_trader')
        self.leverage_config = self.load_leverage_config()
        
        # Initialize core components
        self.data_collector = EnhancedDataCollector()
        self.correlation_engine = EnhancedCorrelationEngine()
        self.signal_generator = EnhancedSignalGenerator()
        self.risk_manager = EnhancedRiskManager()
        self.trade_executor = EnhancedTradeExecutor()
        self.telegram_notifier = EnhancedTelegramNotifier()
        
        # Trading state
        self.active_positions = {}
        self.trading_pairs = list(self.leverage_config['trading_pairs'].keys())
        self.account_balance = 15000  # Updated from API
        
        self.logger.info("Enhanced Leverage Trader initialized")
        
    def load_leverage_config(self):
        """Load the optimized leverage configuration"""
        config_file = 'optimized_leverage_config.json'
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded leverage config with {len(config['trading_pairs'])} pairs")
                return config
            else:
                self.logger.warning(f"Leverage config file not found: {config_file}")
                return self.get_default_leverage_config()
        except Exception as e:
            self.logger.error(f"Error loading leverage config: {e}")
            return self.get_default_leverage_config()
    
    def get_default_leverage_config(self):
        """Fallback leverage configuration"""
        return {
            'trading_pairs': {
                'ETHUSDT': {'leverage': 5, 'position_size_usd': 300, 'risk_level': 'MEDIUM', 'priority': 1},
                'BTCUSDT': {'leverage': 2, 'position_size_usd': 300, 'risk_level': 'HIGH', 'priority': 2},
                'SOLUSDT': {'leverage': 3, 'position_size_usd': 300, 'risk_level': 'MEDIUM', 'priority': 3}
            }
        }
    
    def get_pair_config(self, symbol):
        """Get configuration for specific trading pair"""
        if symbol in self.leverage_config['trading_pairs']:
            return self.leverage_config['trading_pairs'][symbol]
        else:
            # Default conservative config for unknown pairs
            return {
                'leverage': 2,
                'position_size_usd': 300,
                'stop_loss_pct': 5.0,
                'take_profit_pct': 8.0,
                'risk_level': 'HIGH',
                'priority': 5
            }
    
    def calculate_position_size(self, symbol, price):
        """Calculate position size based on leverage configuration"""
        pair_config = self.get_pair_config(symbol)
        
        # Base position size from config
        base_position_usd = pair_config['position_size_usd']
        leverage = pair_config['leverage']
        
        # Apply current account balance adjustment
        balance_adjustment = min(self.account_balance / 15000, 1.0)  # Scale down if balance is lower
        adjusted_position_usd = base_position_usd * balance_adjustment
        
        # Calculate quantity
        quantity = adjusted_position_usd / price
        
        # Apply leverage multiplier for actual position size
        leveraged_quantity = quantity * leverage
        
        self.logger.info(f"{symbol}: Base=${adjusted_position_usd:.2f}, Leverage={leverage}x, Quantity={leveraged_quantity:.4f}")
        
        return leveraged_quantity
    
    def set_leverage_for_symbol(self, symbol):
        """Set leverage for specific symbol on Binance"""
        pair_config = self.get_pair_config(symbol)
        leverage = pair_config['leverage']
        
        try:
            # Use the trade executor to set leverage
            result = self.trade_executor.set_leverage(symbol, leverage)
            if result:
                self.logger.info(f"Successfully set leverage {leverage}x for {symbol}")
                return True
            else:
                self.logger.error(f"Failed to set leverage for {symbol}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting leverage for {symbol}: {e}")
            return False
    
    def calculate_risk_parameters(self, symbol):
        """Get stop loss and take profit levels from leverage config"""
        pair_config = self.get_pair_config(symbol)
        
        return {
            'stop_loss_pct': pair_config.get('stop_loss_pct', 5.0),
            'take_profit_pct': pair_config.get('take_profit_pct', 8.0)
        }
    
    def execute_leveraged_trade(self, signal):
        """Execute trade with optimized leverage settings"""
        symbol = signal['symbol']
        side = signal['side']
        
        try:
            # Set leverage for this symbol
            if not self.set_leverage_for_symbol(symbol):
                self.logger.error(f"Cannot execute trade - leverage setting failed for {symbol}")
                return False
            
            # Get current price
            price_data = self.data_collector.get_current_price(symbol)
            if not price_data:
                self.logger.error(f"Cannot get price for {symbol}")
                return False
            
            current_price = float(price_data['price'])
            
            # Calculate position size with leverage
            quantity = self.calculate_position_size(symbol, current_price)
            
            # Get risk parameters
            risk_params = self.calculate_risk_parameters(symbol)
            
            # Calculate stop loss and take profit prices
            if side == 'BUY':
                stop_price = current_price * (1 - risk_params['stop_loss_pct'] / 100)
                take_profit_price = current_price * (1 + risk_params['take_profit_pct'] / 100)
            else:  # SELL
                stop_price = current_price * (1 + risk_params['stop_loss_pct'] / 100)
                take_profit_price = current_price * (1 - risk_params['take_profit_pct'] / 100)
            
            # Execute market order
            order_result = self.trade_executor.place_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_loss=stop_price,
                take_profit=take_profit_price
            )
            
            if order_result:
                pair_config = self.get_pair_config(symbol)
                
                # Store position info
                self.active_positions[symbol] = {
                    'symbol': symbol,
                    'side': side,
                    'entry_price': current_price,
                    'quantity': quantity,
                    'leverage': pair_config['leverage'],
                    'stop_loss': stop_price,
                    'take_profit': take_profit_price,
                    'entry_time': datetime.now().isoformat(),
                    'order_id': order_result.get('orderId'),
                    'correlation': signal.get('correlation', 0),
                    'deviation': signal.get('deviation', 0)
                }
                
                # Send notification
                leverage = pair_config['leverage']
                risk_level = pair_config['risk_level']
                
                message = f"🚀 LEVERAGED TRADE EXECUTED\n"
                message += f"Pair: {symbol}\n"
                message += f"Side: {side}\n"
                message += f"Leverage: {leverage}x\n"
                message += f"Risk Level: {risk_level}\n"
                message += f"Price: ${current_price:.2f}\n"
                message += f"Quantity: {quantity:.4f}\n"
                message += f"Stop Loss: ${stop_price:.2f} ({risk_params['stop_loss_pct']:.1f}%)\n"
                message += f"Take Profit: ${take_profit_price:.2f} ({risk_params['take_profit_pct']:.1f}%)\n"
                message += f"Correlation: {signal.get('correlation', 0):.3f}"
                
                self.telegram_notifier.send_message(message)
                
                self.logger.info(f"Successfully executed leveraged trade: {symbol} {side} {quantity:.4f} @ {current_price:.2f}")
                return True
            else:
                self.logger.error(f"Failed to execute trade for {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing leveraged trade for {symbol}: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def monitor_positions(self):
        """Monitor active positions with leverage-adjusted risk management"""
        try:
            # Get current positions from exchange
            current_positions = self.trade_executor.get_open_positions()
            
            for symbol in list(self.active_positions.keys()):
                position_info = self.active_positions[symbol]
                
                # Check if position still exists on exchange
                exchange_position = None
                for pos in current_positions:
                    if pos['symbol'] == symbol:
                        exchange_position = pos
                        break
                
                if not exchange_position:
                    # Position closed by exchange (stop loss/take profit hit)
                    self.logger.info(f"Position {symbol} closed by exchange")
                    del self.active_positions[symbol]
                    continue
                
                # Check for manual exit conditions with leverage consideration
                current_price = float(self.data_collector.get_current_price(symbol)['price'])
                entry_price = position_info['entry_price']
                leverage = position_info['leverage']
                
                # Calculate current P&L
                if position_info['side'] == 'BUY':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 * leverage
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100 * leverage
                
                # Time-based exit (leverage positions should be managed more actively)
                entry_time = datetime.fromisoformat(position_info['entry_time'])
                time_held = datetime.now() - entry_time
                
                # Shorter hold times for higher leverage
                max_hold_hours = max(2, 8 - leverage)  # 2-8 hours depending on leverage
                
                if time_held > timedelta(hours=max_hold_hours):
                    self.logger.info(f"Closing {symbol} due to time limit (leverage {leverage}x)")
                    if self.close_position(symbol, "Time Exit - Leverage Management"):
                        del self.active_positions[symbol]
                
                # Update position tracking
                position_info['current_price'] = current_price
                position_info['unrealized_pnl_pct'] = pnl_pct
                
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")
    
    def close_position(self, symbol, reason="Manual Close"):
        """Close specific position"""
        try:
            if symbol not in self.active_positions:
                self.logger.warning(f"No active position found for {symbol}")
                return False
            
            position = self.active_positions[symbol]
            
            # Close position on exchange
            close_result = self.trade_executor.close_position(symbol)
            
            if close_result:
                # Calculate final P&L
                current_price = float(self.data_collector.get_current_price(symbol)['price'])
                entry_price = position['entry_price']
                leverage = position['leverage']
                
                if position['side'] == 'BUY':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 * leverage
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100 * leverage
                
                # Send notification
                message = f"📊 LEVERAGED POSITION CLOSED\n"
                message += f"Pair: {symbol}\n"
                message += f"Side: {position['side']}\n"
                message += f"Leverage: {leverage}x\n"
                message += f"Entry: ${entry_price:.2f}\n"
                message += f"Exit: ${current_price:.2f}\n"
                message += f"P&L: {pnl_pct:.2f}%\n"
                message += f"Reason: {reason}"
                
                self.telegram_notifier.send_message(message)
                
                self.logger.info(f"Successfully closed position: {symbol} with {pnl_pct:.2f}% P&L")
                return True
            else:
                self.logger.error(f"Failed to close position for {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {e}")
            return False
    
    def run_trading_cycle(self):
        """Run one complete trading cycle with leverage optimization"""
        try:
            self.logger.info("Starting leveraged trading cycle...")
            
            # Update account balance
            account_info = self.trade_executor.get_account_balance()
            if account_info:
                self.account_balance = float(account_info.get('balance', self.account_balance))
            
            # Monitor existing positions first
            self.monitor_positions()
            
            # Sort trading pairs by priority (from leverage config)
            sorted_pairs = sorted(
                self.trading_pairs,
                key=lambda x: self.get_pair_config(x).get('priority', 5)
            )
            
            for symbol in sorted_pairs:
                try:
                    # Skip if we already have a position
                    if symbol in self.active_positions:
                        continue
                    
                    # Check if we should prioritize this pair based on risk level
                    pair_config = self.get_pair_config(symbol)
                    risk_level = pair_config.get('risk_level', 'HIGH')
                    
                    # Limit simultaneous high-risk positions
                    high_risk_positions = sum(1 for pos in self.active_positions.values() 
                                            if self.get_pair_config(pos['symbol']).get('risk_level') == 'HIGH')
                    
                    if risk_level == 'HIGH' and high_risk_positions >= 2:
                        self.logger.info(f"Skipping {symbol} - too many high-risk positions")
                        continue
                    
                    # Collect market data
                    market_data = self.data_collector.collect_data(symbol)
                    if not market_data:
                        continue
                    
                    # Calculate correlation
                    correlation_data = self.correlation_engine.calculate_correlation(symbol, market_data)
                    if not correlation_data:
                        continue
                    
                    # Generate signal
                    signal = self.signal_generator.generate_signal(symbol, market_data, correlation_data)
                    if not signal or signal['action'] == 'HOLD':
                        continue
                    
                    # Apply risk management
                    if not self.risk_manager.validate_trade(signal, self.active_positions):
                        continue
                    
                    # Execute leveraged trade
                    self.execute_leveraged_trade(signal)
                    
                    # Small delay between trades
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            self.logger.info("Leveraged trading cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
            self.logger.error(traceback.format_exc())
    
    def get_status_report(self):
        """Generate comprehensive status report"""
        try:
            total_positions = len(self.active_positions)
            total_pnl = 0
            
            for symbol, position in self.active_positions.items():
                current_price = float(self.data_collector.get_current_price(symbol)['price'])
                entry_price = position['entry_price']
                leverage = position['leverage']
                
                if position['side'] == 'BUY':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 * leverage
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100 * leverage
                
                total_pnl += pnl_pct
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'account_balance': self.account_balance,
                'active_positions': total_positions,
                'total_unrealized_pnl_pct': total_pnl,
                'leverage_config_loaded': len(self.leverage_config['trading_pairs']),
                'position_details': {}
            }
            
            for symbol, position in self.active_positions.items():
                pair_config = self.get_pair_config(symbol)
                current_price = float(self.data_collector.get_current_price(symbol)['price'])
                
                if position['side'] == 'BUY':
                    pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100 * position['leverage']
                else:
                    pnl_pct = ((position['entry_price'] - current_price) / position['entry_price']) * 100 * position['leverage']
                
                report['position_details'][symbol] = {
                    'side': position['side'],
                    'leverage': position['leverage'],
                    'risk_level': pair_config.get('risk_level', 'UNKNOWN'),
                    'entry_price': position['entry_price'],
                    'current_price': current_price,
                    'unrealized_pnl_pct': pnl_pct,
                    'priority': pair_config.get('priority', 5)
                }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating status report: {e}")
            return {'error': str(e)}

def main():
    """Main execution function"""
    print("Starting Enhanced Leverage Trading System...")
    
    trader = EnhancedLeverageTrader()
    
    try:
        while True:
            trader.run_trading_cycle()
            
            # Generate status report
            status = trader.get_status_report()
            print(f"Status: {status['active_positions']} positions, "
                  f"Total P&L: {status['total_unrealized_pnl_pct']:.2f}%")
            
            # Wait before next cycle (shorter intervals for leverage trading)
            time.sleep(300)  # 5 minutes
            
    except KeyboardInterrupt:
        print("\nShutting down leverage trading system...")
        trader.logger.info("Leverage trading system stopped by user")
    except Exception as e:
        print(f"Critical error: {e}")
        trader.logger.error(f"Critical error in main loop: {e}")
        trader.logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()