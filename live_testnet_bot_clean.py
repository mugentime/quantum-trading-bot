#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIVE TESTNET FORWARD TEST BOT
Runs until tomorrow 8:30 AM with real Binance testnet trades
"""

import asyncio
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import logging
from core.config.settings import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'testnet_trades_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LiveTestnetBot:
    def __init__(self):
        self.initial_balance = None
        self.current_balance = None
        self.position_size_pct = 0.02  # 2% per trade (conservative for live test)
        self.risk_reward_ratio = 1.5
        self.correlation_window = 20
        self.deviation_threshold = 0.10
        self.trades = []
        self.exchange = None
        self.running = True
        
        # Trading parameters
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        self.timeframe = '3m'
        self.max_positions = 3
        self.active_positions = {}
        
    async def initialize_exchange(self):
        """Initialize Binance testnet exchange"""
        try:
            import ccxt.async_support as ccxt_async
            self.exchange = ccxt_async.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'sandbox': True,  # Use testnet
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'  # Spot trading
                }
            })
            
            # Test connection
            balance = await self.exchange.fetch_balance()
            self.initial_balance = balance['USDT']['free']
            self.current_balance = self.initial_balance
            
            logger.info(f"Connected to Binance Testnet")
            logger.info(f"Initial Balance: {self.initial_balance:.2f} USDT")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to exchange: {e}")
            return False
    
    async def fetch_recent_data(self, symbol, limit=100):
        """Fetch recent 3m candle data"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_correlation_signals(self, btc_df, symbol_df, symbol):
        """Calculate correlation-based trading signals"""
        try:
            if len(btc_df) < self.correlation_window + 10 or len(symbol_df) < self.correlation_window + 10:
                return None
            
            # Align data
            min_len = min(len(btc_df), len(symbol_df))
            btc_prices = btc_df['close'].tail(min_len).values
            symbol_prices = symbol_df['close'].tail(min_len).values
            
            # Current correlation
            current_corr = np.corrcoef(
                btc_prices[-self.correlation_window:],
                symbol_prices[-self.correlation_window:]
            )[0,1]
            
            # Historical correlation (last 20 periods)
            if min_len > self.correlation_window + 20:
                hist_correlations = []
                for i in range(self.correlation_window + 5, self.correlation_window + 20):
                    hist_corr = np.corrcoef(
                        btc_prices[-(i+self.correlation_window):-i],
                        symbol_prices[-(i+self.correlation_window):-i]
                    )[0,1]
                    hist_correlations.append(hist_corr)
                
                hist_avg = np.mean(hist_correlations)
            else:
                return None
            
            # Calculate deviation
            deviation = abs(current_corr - hist_avg) / abs(hist_avg) if hist_avg != 0 else 0
            
            # Generate signal
            signal = None
            if deviation > self.deviation_threshold:
                current_price = symbol_df['close'].iloc[-1]
                
                # Price momentum
                price_momentum = (current_price - symbol_df['close'].iloc[-10]) / symbol_df['close'].iloc[-10]
                btc_momentum = (btc_df['close'].iloc[-1] - btc_df['close'].iloc[-10]) / btc_df['close'].iloc[-10]
                
                # Signal logic
                if current_corr < hist_avg:  # Correlation breakdown
                    if price_momentum < btc_momentum:  # Symbol underperforming
                        signal = 'BUY'
                    else:
                        signal = 'SELL'
                else:  # Correlation strengthening
                    if price_momentum > 0:
                        signal = 'BUY'
                    else:
                        signal = 'SELL'
                
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'current_price': current_price,
                    'correlation': current_corr,
                    'hist_correlation': hist_avg,
                    'deviation': deviation,
                    'confidence': min(deviation / self.deviation_threshold, 2.0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating signals for {symbol}: {e}")
            return None
    
    async def execute_trade(self, signal_data):
        """Execute trade on Binance testnet"""
        try:
            symbol = signal_data['symbol']
            signal = signal_data['signal']
            current_price = signal_data['current_price']
            confidence = signal_data['confidence']
            
            # Skip if already have position
            if symbol in self.active_positions:
                logger.info(f" Skipping {symbol} - already have active position")
                return None
            
            # Calculate position size
            balance = await self.exchange.fetch_balance()
            available_balance = balance['USDT']['free']
            position_value = available_balance * self.position_size_pct * confidence
            quantity = position_value / current_price
            
            # Minimum quantity check
            if quantity < 0.001:  # Minimum for most pairs
                logger.info(f" Quantity too small for {symbol}: {quantity}")
                return None
            
            # Round quantity appropriately
            if symbol == 'BTCUSDT':
                quantity = round(quantity, 5)
            elif symbol == 'ETHUSDT':
                quantity = round(quantity, 4)
            else:
                quantity = round(quantity, 2)
            
            # Execute order
            side = 'buy' if signal == 'BUY' else 'sell'
            order_type = 'market'
            
            logger.info(f" Executing {side.upper()} order: {quantity} {symbol} at ~{current_price:.4f}")
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=quantity
            )
            
            # Wait for fill and get final details
            await asyncio.sleep(2)
            filled_order = await self.exchange.fetch_order(order['id'], symbol)
            
            # Calculate targets
            fill_price = filled_order['average'] or filled_order['price']
            
            if signal == 'BUY':
                take_profit = fill_price * (1 + 0.02 * self.risk_reward_ratio)  # 2% * 1.5 = 3%
                stop_loss = fill_price * (1 - 0.02)  # 2%
            else:
                take_profit = fill_price * (1 - 0.02 * self.risk_reward_ratio)
                stop_loss = fill_price * (1 + 0.02)
            
            # Record position
            position_data = {
                'symbol': symbol,
                'side': signal,
                'entry_price': fill_price,
                'quantity': filled_order['filled'],
                'entry_time': datetime.now(),
                'take_profit': take_profit,
                'stop_loss': stop_loss,
                'order_id': order['id'],
                'correlation': signal_data['correlation'],
                'deviation': signal_data['deviation']
            }
            
            self.active_positions[symbol] = position_data
            
            logger.info(f" {side.upper()} order filled: {filled_order['filled']} {symbol} at {fill_price:.4f}")
            logger.info(f" TP: {take_profit:.4f} | SL: {stop_loss:.4f}")
            
            return position_data
            
        except Exception as e:
            logger.error(f" Error executing trade: {e}")
            return None
    
    async def check_exit_conditions(self):
        """Check if any positions should be closed"""
        for symbol, position in list(self.active_positions.items()):
            try:
                # Get current price
                ticker = await self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                should_exit = False
                exit_reason = ""
                
                # Check TP/SL
                if position['side'] == 'BUY':
                    if current_price >= position['take_profit']:
                        should_exit = True
                        exit_reason = "Take Profit"
                    elif current_price <= position['stop_loss']:
                        should_exit = True
                        exit_reason = "Stop Loss"
                else:  # SELL
                    if current_price <= position['take_profit']:
                        should_exit = True
                        exit_reason = "Take Profit"
                    elif current_price >= position['stop_loss']:
                        should_exit = True
                        exit_reason = "Stop Loss"
                
                # Check time-based exit (max 2 hours)
                time_in_position = datetime.now() - position['entry_time']
                if time_in_position > timedelta(hours=2):
                    should_exit = True
                    exit_reason = "Time Exit"
                
                if should_exit:
                    await self.close_position(symbol, current_price, exit_reason)
                    
            except Exception as e:
                logger.error(f"Error checking exit for {symbol}: {e}")
    
    async def close_position(self, symbol, current_price, reason):
        """Close an active position"""
        try:
            position = self.active_positions[symbol]
            
            # Execute closing order
            side = 'sell' if position['side'] == 'BUY' else 'buy'
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=position['quantity']
            )
            
            await asyncio.sleep(2)
            filled_order = await self.exchange.fetch_order(order['id'], symbol)
            
            # Calculate P&L
            exit_price = filled_order['average'] or current_price
            if position['side'] == 'BUY':
                pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
            else:
                pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
            
            pnl_usd = pnl_pct * position['entry_price'] * position['quantity']
            
            # Record completed trade
            trade_record = {
                'symbol': symbol,
                'side': position['side'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'quantity': position['quantity'],
                'entry_time': position['entry_time'],
                'exit_time': datetime.now(),
                'pnl_pct': pnl_pct * 100,
                'pnl_usd': pnl_usd,
                'exit_reason': reason,
                'correlation': position['correlation'],
                'deviation': position['deviation']
            }
            
            self.trades.append(trade_record)
            del self.active_positions[symbol]
            
            logger.info(f" Closed {symbol} position: {reason}")
            logger.info(f" P&L: {pnl_usd:.2f} USDT ({pnl_pct*100:.2f}%)")
            
        except Exception as e:
            logger.error(f" Error closing {symbol} position: {e}")
    
    async def log_status(self):
        """Log current status"""
        try:
            balance = await self.exchange.fetch_balance()
            current_balance = balance['USDT']['free']
            
            total_pnl = sum([t['pnl_usd'] for t in self.trades])
            unrealized_pnl = 0
            
            # Calculate unrealized P&L
            for symbol, position in self.active_positions.items():
                ticker = await self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                if position['side'] == 'BUY':
                    unrealized = (current_price - position['entry_price']) / position['entry_price']
                else:
                    unrealized = (position['entry_price'] - current_price) / position['entry_price']
                
                unrealized_pnl += unrealized * position['entry_price'] * position['quantity']
            
            logger.info(f" Balance: {current_balance:.2f} USDT | Realized P&L: {total_pnl:.2f} | Unrealized: {unrealized_pnl:.2f}")
            logger.info(f" Active Positions: {len(self.active_positions)} | Completed Trades: {len(self.trades)}")
            
        except Exception as e:
            logger.error(f"Error logging status: {e}")
    
    def should_continue_running(self):
        """Check if we should continue running until 8:30 AM tomorrow"""
        now = datetime.now()
        tomorrow_830 = datetime.now().replace(hour=8, minute=30, second=0, microsecond=0) + timedelta(days=1)
        
        if now < tomorrow_830:
            time_remaining = tomorrow_830 - now
            logger.info(f" Time remaining: {time_remaining}")
            return True
        else:
            logger.info(f" Reached end time: {tomorrow_830}")
            return False
    
    async def run_live_test(self):
        """Main trading loop"""
        logger.info("Starting Live Testnet Forward Test")
        logger.info(f"Running until tomorrow 8:30 AM")
        
        if not await self.initialize_exchange():
            return
        
        try:
            while self.should_continue_running():
                # Fetch recent data for all symbols
                btc_df = await self.fetch_recent_data('BTCUSDT')
                
                if btc_df.empty:
                    logger.warning("No BTC data available")
                    await asyncio.sleep(60)
                    continue
                
                # Check for signals on each symbol
                for symbol in self.symbols[1:]:  # Skip BTC
                    if len(self.active_positions) >= self.max_positions:
                        break
                    
                    symbol_df = await self.fetch_recent_data(symbol)
                    if symbol_df.empty:
                        continue
                    
                    signal = self.calculate_correlation_signals(btc_df, symbol_df, symbol)
                    
                    if signal and signal['confidence'] > 1.2:  # High confidence signals only
                        logger.info(f" Signal: {signal['signal']} {signal['symbol']} "
                                  f"(Correlation: {signal['correlation']:.3f}, "
                                  f"Deviation: {signal['deviation']:.3f})")
                        
                        await self.execute_trade(signal)
                
                # Check exit conditions
                await self.check_exit_conditions()
                
                # Log status every 30 minutes
                if datetime.now().minute % 30 == 0:
                    await self.log_status()
                
                # Save progress
                self.save_progress()
                
                # Wait before next iteration (3 minutes to match timeframe)
                await asyncio.sleep(180)
                
        except KeyboardInterrupt:
            logger.info(" Bot stopped by user")
        except Exception as e:
            logger.error(f" Unexpected error: {e}")
        finally:
            await self.cleanup()
    
    def save_progress(self):
        """Save current progress to file"""
        progress_data = {
            'start_time': datetime.now().isoformat(),
            'initial_balance': self.initial_balance,
            'completed_trades': self.trades,
            'active_positions': {k: {**v, 'entry_time': v['entry_time'].isoformat()} 
                               for k, v in self.active_positions.items()}
        }
        
        filename = f'testnet_progress_{datetime.now().strftime("%Y%m%d")}.json'
        with open(filename, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
    
    async def cleanup(self):
        """Close all positions and cleanup"""
        logger.info(" Cleaning up...")
        
        # Close all active positions
        for symbol in list(self.active_positions.keys()):
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                await self.close_position(symbol, ticker['last'], "Bot Shutdown")
            except Exception as e:
                logger.error(f"Error closing {symbol}: {e}")
        
        # Final summary
        total_trades = len(self.trades)
        profitable_trades = len([t for t in self.trades if t['pnl_usd'] > 0])
        total_pnl = sum([t['pnl_usd'] for t in self.trades])
        
        logger.info(" FINAL TESTNET RESULTS:")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Profitable Trades: {profitable_trades}")
        logger.info(f"Win Rate: {profitable_trades/total_trades*100:.1f}%" if total_trades > 0 else "No trades")
        logger.info(f"Total P&L: {total_pnl:.2f} USDT")
        logger.info(f"Return: {total_pnl/self.initial_balance*100:.2f}%" if self.initial_balance else "N/A")
        
        if self.exchange:
            await self.exchange.close()

async def main():
    bot = LiveTestnetBot()
    await bot.run_live_test()

if __name__ == "__main__":
    asyncio.run(main())