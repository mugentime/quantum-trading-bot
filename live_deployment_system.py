#!/usr/bin/env python3
"""
Live Testnet Deployment System
Deploys optimized configurations for live forward trading with monitoring
"""

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import threading
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LivePosition:
    """Live trading position"""
    symbol: str
    side: str
    size: float
    entry_price: float
    entry_time: str
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    correlation: float
    confidence: float
    stop_loss: float
    take_profit: float

@dataclass
class LivePerformance:
    """Live performance tracking"""
    total_pnl: float
    total_pnl_pct: float
    realized_pnl: float
    unrealized_pnl: float
    total_trades: int
    winning_trades: int
    win_rate_pct: float
    largest_win: float
    largest_loss: float
    current_positions: int
    max_positions: int
    daily_pnl: float
    start_balance: float
    current_balance: float

class LiveDeploymentSystem:
    """Live deployment and monitoring system"""
    
    def __init__(self, config_file: str = None):
        self.config = self.load_configuration(config_file)
        self.exchange = None
        self.running = False
        
        # Trading state
        self.positions = {}
        self.trade_history = []
        self.performance = LivePerformance(
            total_pnl=0, total_pnl_pct=0, realized_pnl=0, unrealized_pnl=0,
            total_trades=0, winning_trades=0, win_rate_pct=0,
            largest_win=0, largest_loss=0, current_positions=0, max_positions=0,
            daily_pnl=0, start_balance=0, current_balance=0
        )
        
        # Data collection
        self.market_data = {}
        self.correlation_engine = None
        self.signal_generator = None
        
        # Monitoring
        self.last_report_time = datetime.now()
        self.report_interval = 3600  # 1 hour
        
        logger.info("Live Deployment System initialized")

    def load_configuration(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from optimization results"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                full_config = json.load(f)
                return full_config.get('live_deployment_config', {})
        
        # Default configuration if no file provided
        return {
            "trading_pairs": ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'],
            "balance_allocation": {
                'BTCUSDT': 0.3, 'ETHUSDT': 0.25, 'SOLUSDT': 0.2, 
                'BNBUSDT': 0.15, 'XRPUSDT': 0.1
            },
            "parameters": {
                "correlation_threshold": 0.75,
                "deviation_threshold": 0.15,
                "position_size": 0.02,
                "stop_loss_pct": 0.02,
                "take_profit_ratio": 2.0,
                "leverage": 15,
                "confidence_threshold": 0.75
            },
            "risk_management": {
                "max_total_exposure": 0.8,
                "max_single_position": 0.2,
                "daily_loss_limit": 0.1,
                "max_concurrent_positions": 5
            },
            "execution_settings": {
                "api_key": "2bebcfa42c24f706250fc870c174c092e3d4d42b7b0912647524c59be6b2bf5a",
                "api_secret": "d23c85fd1947521e6e7c730ecc41790c6446c49b6f8b7305dab7c702a010c594",
                "use_testnet": True,
                "base_url": "https://testnet.binancefuture.com"
            }
        }

    async def initialize_exchange(self):
        """Initialize exchange connection"""
        try:
            exec_settings = self.config['execution_settings']
            
            self.exchange = ccxt.binance({
                'apiKey': exec_settings['api_key'],
                'secret': exec_settings['api_secret'],
                'sandbox': exec_settings['use_testnet'],
                'enableRateLimit': True,
                'timeout': 30000,
                'urls': {
                    'test': {
                        'public': 'https://testnet.binancefuture.com/fapi/v1',
                        'private': 'https://testnet.binancefuture.com/fapi/v1'
                    }
                } if exec_settings['use_testnet'] else {},
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True
                }
            })
            
            # Test connection and get account info
            await self.exchange.fetch_time()
            balance = await self.exchange.fetch_balance()
            
            self.performance.start_balance = balance['USDT']['total']
            self.performance.current_balance = self.performance.start_balance
            
            logger.info(f"Exchange initialized - Balance: {self.performance.start_balance} USDT")
            
            # Set leverage for all pairs
            for symbol in self.config['trading_pairs']:
                try:
                    await self.exchange.set_leverage(
                        self.config['parameters']['leverage'], 
                        symbol
                    )
                    logger.info(f"Set leverage {self.config['parameters']['leverage']}x for {symbol}")
                except Exception as e:
                    logger.warning(f"Could not set leverage for {symbol}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            return False

    async def fetch_market_data(self):
        """Fetch current market data for all pairs"""
        try:
            for symbol in self.config['trading_pairs']:
                ticker = await self.exchange.fetch_ticker(symbol)
                
                self.market_data[symbol] = {
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'last': ticker['last'],
                    'timestamp': ticker['timestamp'],
                    'volume': ticker['quoteVolume']
                }
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")

    def calculate_correlation_signal(self, symbol: str) -> Optional[Dict]:
        """Calculate correlation-based trading signal"""
        try:
            if symbol not in self.market_data:
                return None
            
            # Simplified correlation signal generation for live trading
            # In production, this would use the full correlation engine
            current_price = self.market_data[symbol]['last']
            
            # Mock correlation calculation (replace with actual correlation engine)
            correlation = np.random.uniform(-0.95, 0.95)  # Placeholder
            confidence = abs(correlation) * np.random.uniform(0.8, 1.0)
            
            params = self.config['parameters']
            
            if (abs(correlation) > params['correlation_threshold'] and 
                confidence > params['confidence_threshold']):
                
                # Determine signal direction
                momentum = np.random.uniform(-0.02, 0.02)  # Placeholder for actual momentum
                
                if correlation > 0:
                    side = 'BUY' if momentum > 0 else 'SELL'
                else:
                    side = 'SELL' if momentum > 0 else 'BUY'
                
                return {
                    'symbol': symbol,
                    'side': side,
                    'price': current_price,
                    'correlation': correlation,
                    'confidence': confidence,
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating signal for {symbol}: {e}")
            return None

    async def execute_trade(self, signal: Dict) -> bool:
        """Execute a trade based on signal"""
        try:
            symbol = signal['symbol']
            side = signal['side']
            price = signal['price']
            
            # Check if already have position in this symbol
            if symbol in self.positions:
                logger.info(f"Already have position in {symbol}, skipping")
                return False
            
            # Check risk limits
            if (len(self.positions) >= self.config['risk_management']['max_concurrent_positions']):
                logger.info("Maximum concurrent positions reached, skipping trade")
                return False
            
            if (self.performance.daily_pnl <= 
                -self.performance.start_balance * self.config['risk_management']['daily_loss_limit']):
                logger.warning("Daily loss limit reached, stopping trades")
                return False
            
            # Calculate position size
            allocation = self.config['balance_allocation'].get(symbol, 0.1)
            position_size_usd = self.performance.current_balance * allocation * self.config['parameters']['position_size']
            
            # Adjust for leverage
            leverage = self.config['parameters']['leverage']
            quantity = (position_size_usd * leverage) / price
            
            # Round quantity to appropriate precision (symbol-specific)
            if 'BTC' in symbol:
                quantity = round(quantity, 6)
            elif 'ETH' in symbol:
                quantity = round(quantity, 5)
            else:
                quantity = round(quantity, 4)
            
            if quantity == 0:
                logger.warning(f"Calculated quantity is 0 for {symbol}")
                return False
            
            # Execute order
            order = await self.exchange.create_market_order(
                symbol=symbol,
                side=side.lower(),
                amount=quantity
            )
            
            if order['status'] == 'closed' or order['filled'] > 0:
                # Calculate stop loss and take profit
                entry_price = order['average'] or price
                stop_loss_pct = self.config['parameters']['stop_loss_pct']
                take_profit_ratio = self.config['parameters']['take_profit_ratio']
                
                if side == 'BUY':
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + stop_loss_pct * take_profit_ratio)
                else:
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit = entry_price * (1 - stop_loss_pct * take_profit_ratio)
                
                # Create position record
                position = LivePosition(
                    symbol=symbol,
                    side=side,
                    size=order['filled'],
                    entry_price=entry_price,
                    entry_time=datetime.now().isoformat(),
                    current_price=price,
                    unrealized_pnl=0,
                    unrealized_pnl_pct=0,
                    correlation=signal['correlation'],
                    confidence=signal['confidence'],
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                self.positions[symbol] = position
                self.performance.current_positions = len(self.positions)
                self.performance.max_positions = max(self.performance.max_positions, 
                                                   self.performance.current_positions)
                
                logger.info(f"✅ Opened {side} position: {symbol} @ {entry_price:.6f} "
                           f"(Size: {order['filled']:.6f}, Correlation: {signal['correlation']:.3f})")
                
                return True
            else:
                logger.error(f"Order not filled for {symbol}: {order}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing trade for {signal['symbol']}: {e}")
            return False

    async def close_position(self, symbol: str, reason: str = "Manual") -> bool:
        """Close a position"""
        try:
            if symbol not in self.positions:
                logger.warning(f"No position found for {symbol}")
                return False
            
            position = self.positions[symbol]
            current_price = self.market_data[symbol]['last']
            
            # Determine close side (opposite of entry)
            close_side = 'SELL' if position.side == 'BUY' else 'BUY'
            
            # Execute close order
            order = await self.exchange.create_market_order(
                symbol=symbol,
                side=close_side.lower(),
                amount=position.size
            )
            
            if order['status'] == 'closed' or order['filled'] > 0:
                exit_price = order['average'] or current_price
                
                # Calculate P&L
                if position.side == 'BUY':
                    pnl_pct = (exit_price - position.entry_price) / position.entry_price * 100
                else:
                    pnl_pct = (position.entry_price - exit_price) / position.entry_price * 100
                
                # Account for leverage
                leverage = self.config['parameters']['leverage']
                pnl_pct_leveraged = pnl_pct * leverage
                
                pnl_usd = (pnl_pct_leveraged / 100) * (position.size * position.entry_price / leverage)
                
                # Update performance
                self.performance.realized_pnl += pnl_usd
                self.performance.total_pnl += pnl_usd
                self.performance.total_trades += 1
                self.performance.daily_pnl += pnl_usd
                self.performance.current_balance += pnl_usd
                
                if pnl_usd > 0:
                    self.performance.winning_trades += 1
                    self.performance.largest_win = max(self.performance.largest_win, pnl_usd)
                else:
                    self.performance.largest_loss = min(self.performance.largest_loss, pnl_usd)
                
                self.performance.win_rate_pct = (self.performance.winning_trades / 
                                               self.performance.total_trades) * 100
                self.performance.total_pnl_pct = ((self.performance.current_balance - 
                                                 self.performance.start_balance) / 
                                                self.performance.start_balance) * 100
                
                # Record trade
                trade_record = {
                    'symbol': symbol,
                    'side': position.side,
                    'entry_price': position.entry_price,
                    'exit_price': exit_price,
                    'size': position.size,
                    'entry_time': position.entry_time,
                    'exit_time': datetime.now().isoformat(),
                    'pnl_usd': pnl_usd,
                    'pnl_pct': pnl_pct_leveraged,
                    'correlation': position.correlation,
                    'confidence': position.confidence,
                    'exit_reason': reason
                }
                
                self.trade_history.append(trade_record)
                
                # Remove position
                del self.positions[symbol]
                self.performance.current_positions = len(self.positions)
                
                logger.info(f"✅ Closed position: {symbol} - {reason} - "
                           f"P&L: {pnl_pct_leveraged:+.2f}% (${pnl_usd:+.2f})")
                
                return True
            else:
                logger.error(f"Failed to close position for {symbol}: {order}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return False

    async def update_positions(self):
        """Update position data with current market prices"""
        try:
            total_unrealized = 0
            
            for symbol, position in self.positions.items():
                if symbol in self.market_data:
                    current_price = self.market_data[symbol]['last']
                    position.current_price = current_price
                    
                    # Calculate unrealized P&L
                    if position.side == 'BUY':
                        pnl_pct = (current_price - position.entry_price) / position.entry_price * 100
                    else:
                        pnl_pct = (position.entry_price - current_price) / position.entry_price * 100
                    
                    # Account for leverage
                    leverage = self.config['parameters']['leverage']
                    pnl_pct_leveraged = pnl_pct * leverage
                    pnl_usd = (pnl_pct_leveraged / 100) * (position.size * position.entry_price / leverage)
                    
                    position.unrealized_pnl = pnl_usd
                    position.unrealized_pnl_pct = pnl_pct_leveraged
                    total_unrealized += pnl_usd
            
            self.performance.unrealized_pnl = total_unrealized
            self.performance.total_pnl = self.performance.realized_pnl + total_unrealized
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")

    async def check_exit_conditions(self):
        """Check if any positions should be closed"""
        for symbol, position in list(self.positions.items()):
            try:
                current_price = position.current_price
                
                # Stop loss check
                if ((position.side == 'BUY' and current_price <= position.stop_loss) or
                    (position.side == 'SELL' and current_price >= position.stop_loss)):
                    await self.close_position(symbol, "Stop Loss")
                    continue
                
                # Take profit check
                if ((position.side == 'BUY' and current_price >= position.take_profit) or
                    (position.side == 'SELL' and current_price <= position.take_profit)):
                    await self.close_position(symbol, "Take Profit")
                    continue
                
                # Time-based exit (24 hours max)
                entry_time = datetime.fromisoformat(position.entry_time)
                hold_time = (datetime.now() - entry_time).total_seconds() / 3600
                
                if hold_time >= 24:
                    await self.close_position(symbol, "Max Hold Time")
                    continue
                    
            except Exception as e:
                logger.error(f"Error checking exit conditions for {symbol}: {e}")

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "performance_summary": {
                "total_pnl_usd": round(self.performance.total_pnl, 2),
                "total_pnl_pct": round(self.performance.total_pnl_pct, 2),
                "realized_pnl": round(self.performance.realized_pnl, 2),
                "unrealized_pnl": round(self.performance.unrealized_pnl, 2),
                "win_rate_pct": round(self.performance.win_rate_pct, 2),
                "total_trades": self.performance.total_trades,
                "winning_trades": self.performance.winning_trades,
                "current_positions": self.performance.current_positions,
                "start_balance": self.performance.start_balance,
                "current_balance": round(self.performance.current_balance, 2)
            },
            "current_positions": [
                {
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": round(pos.unrealized_pnl, 2),
                    "unrealized_pnl_pct": round(pos.unrealized_pnl_pct, 2),
                    "correlation": round(pos.correlation, 3)
                }
                for pos in self.positions.values()
            ],
            "recent_trades": self.trade_history[-10:] if len(self.trade_history) > 10 else self.trade_history,
            "risk_metrics": {
                "current_exposure": len(self.positions) / self.config['risk_management']['max_concurrent_positions'],
                "daily_pnl": round(self.performance.daily_pnl, 2),
                "daily_limit_remaining": round(
                    self.performance.start_balance * self.config['risk_management']['daily_loss_limit'] + 
                    self.performance.daily_pnl, 2
                )
            }
        }

    async def trading_loop(self):
        """Main trading loop"""
        logger.info("Starting trading loop")
        
        while self.running:
            try:
                # Fetch market data
                await self.fetch_market_data()
                
                # Update positions
                await self.update_positions()
                
                # Check exit conditions
                await self.check_exit_conditions()
                
                # Look for new signals (if not at max positions)
                if (len(self.positions) < self.config['risk_management']['max_concurrent_positions'] and
                    self.performance.daily_pnl > -self.performance.start_balance * 
                    self.config['risk_management']['daily_loss_limit']):
                    
                    for symbol in self.config['trading_pairs']:
                        if symbol not in self.positions:
                            signal = self.calculate_correlation_signal(symbol)
                            if signal:
                                await self.execute_trade(signal)
                                await asyncio.sleep(1)  # Brief pause between trades
                
                # Generate periodic reports
                if (datetime.now() - self.last_report_time).total_seconds() >= self.report_interval:
                    report = self.generate_performance_report()
                    
                    # Save report
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_file = f"live_performance_report_{timestamp}.json"
                    
                    with open(report_file, 'w') as f:
                        json.dump(report, f, indent=2)
                    
                    logger.info(f"Performance report saved: {report_file}")
                    logger.info(f"Current P&L: ${report['performance_summary']['total_pnl_usd']:+.2f} "
                               f"({report['performance_summary']['total_pnl_pct']:+.2f}%)")
                    
                    self.last_report_time = datetime.now()
                
                # Sleep before next iteration
                await asyncio.sleep(30)  # 30-second cycle
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def start_live_trading(self):
        """Start live trading system"""
        logger.info("Starting Live Trading System")
        
        if not await self.initialize_exchange():
            raise Exception("Failed to initialize exchange")
        
        self.running = True
        
        # Reset daily P&L at start
        self.performance.daily_pnl = 0
        
        # Start trading loop
        await self.trading_loop()

    async def stop_live_trading(self):
        """Stop live trading and close all positions"""
        logger.info("Stopping Live Trading System")
        
        self.running = False
        
        # Close all open positions
        for symbol in list(self.positions.keys()):
            await self.close_position(symbol, "System Shutdown")
        
        # Generate final report
        final_report = self.generate_performance_report()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_file = f"live_trading_final_report_{timestamp}.json"
        
        with open(final_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Final performance report saved: {final_file}")
        
        if self.exchange:
            await self.exchange.close()
        
        return final_report

async def main():
    """Main execution function"""
    try:
        # Look for latest optimization report
        optimization_files = [f for f in os.listdir('.') if f.startswith('comprehensive_optimization_report_')]
        
        if optimization_files:
            latest_config = sorted(optimization_files)[-1]
            logger.info(f"Using configuration from: {latest_config}")
        else:
            latest_config = None
            logger.info("Using default configuration")
        
        system = LiveDeploymentSystem(latest_config)
        
        print("=" * 80)
        print("LIVE TESTNET DEPLOYMENT SYSTEM")
        print("=" * 80)
        print(f"Trading Pairs: {', '.join(system.config['trading_pairs'])}")
        print(f"Max Concurrent Positions: {system.config['risk_management']['max_concurrent_positions']}")
        print(f"Daily Loss Limit: {system.config['risk_management']['daily_loss_limit']*100}%")
        print(f"Using Testnet: {system.config['execution_settings']['use_testnet']}")
        print("=" * 80)
        print("Press Ctrl+C to stop trading and generate final report")
        print()
        
        # Start live trading
        await system.start_live_trading()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        if 'system' in locals():
            final_report = await system.stop_live_trading()
            
            print("\n" + "=" * 80)
            print("LIVE TRADING SESSION COMPLETED")
            print("=" * 80)
            
            summary = final_report['performance_summary']
            print(f"Total P&L: ${summary['total_pnl_usd']:+.2f} ({summary['total_pnl_pct']:+.2f}%)")
            print(f"Win Rate: {summary['win_rate_pct']:.1f}%")
            print(f"Total Trades: {summary['total_trades']}")
            print(f"Final Balance: ${summary['current_balance']:,.2f}")
        
    except Exception as e:
        logger.error(f"Live deployment system failed: {e}")
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())