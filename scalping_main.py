#!/usr/bin/env python3
"""
High-Frequency Scalping Trading Bot
Optimized for ETHUSDT 3-minute scalping strategy targeting 14% daily returns
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal
import sys

from core.config.settings import config
from core.config.scalping_config import scalping_config
from core.data_collector import DataCollector
from core.correlation_engine import CorrelationEngine
from core.signal_generator import SignalGenerator
from core.trade_executor import TradeExecutor
from core.risk_manager import risk_manager
from core.leverage_manager import leverage_manager
from utils.logger_config import setup_logger
from utils.telegram_notifier import TelegramNotifier

# Set up logging
logger = setup_logger("ScalpingBot", level=logging.INFO)

class ScalpingTradingBot:
    """High-frequency scalping trading bot optimized for 3-minute ETHUSDT scalping"""
    
    def __init__(self):
        """Initialize the scalping trading bot"""
        self.running = False
        self.should_stop = False
        self.cycle_count = 0
        self.start_time = datetime.now()
        
        # Initialize components
        logger.info("Initializing Scalping Trading Bot...")
        
        # Core components
        self.data_collector = DataCollector()
        self.correlation_engine = CorrelationEngine()
        self.signal_generator = SignalGenerator(
            confidence_threshold=scalping_config.parameters.CONFIDENCE_THRESHOLD,
            min_statistical_significance=scalping_config.filters.MIN_STATISTICAL_SIGNIFICANCE * 100
        )
        self.trade_executor = TradeExecutor()
        self.telegram_notifier = TelegramNotifier()
        
        # Scalping-specific attributes
        self.last_signal_time = None
        self.daily_trade_count = 0
        self.daily_start = datetime.now().date()
        self.position_start_time = None
        self.current_position = None
        
        # Performance tracking
        self.scalping_stats = {
            'total_signals': 0,
            'executed_trades': 0,
            'successful_scalps': 0,
            'failed_scalps': 0,
            'total_pnl': 0.0,
            'best_scalp': 0.0,
            'worst_scalp': 0.0,
            'average_hold_time': 0.0,
            'win_rate': 0.0
        }
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Scalping Trading Bot initialized successfully")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.should_stop = True
    
    async def start(self):
        """Start the scalping trading bot"""
        logger.info("🚀 Starting High-Frequency Scalping Bot")
        logger.info(f"Target: {scalping_config.parameters.TARGET_TRADES_PER_DAY} trades/day for {scalping_config.parameters.DAILY_TARGET_PERCENT:.1%} daily return")
        
        # Send startup notification
        await self.telegram_notifier.send_message(
            "🤖 **Scalping Bot Started**\n"
            f"Symbol: {scalping_config.parameters.PRIMARY_SYMBOL}\n"
            f"Target: {scalping_config.parameters.TARGET_TRADES_PER_DAY} trades/day\n"
            f"Stop Loss: {scalping_config.parameters.STOP_LOSS_PERCENT:.1%}\n"
            f"Take Profit: {scalping_config.parameters.TAKE_PROFIT_PERCENT:.1%}\n"
            f"Max Position: {scalping_config.parameters.BASE_POSITION_SIZE:.1%}"
        )
        
        self.running = True
        
        try:
            # Validate account and setup
            await self._validate_account_setup()
            
            # Main trading loop
            while self.running and not self.should_stop:
                await self._scalping_cycle()
                
                # Wait for next cycle (30-second intervals for high frequency)
                await asyncio.sleep(config.SIGNAL_GENERATION_INTERVAL)
                
        except Exception as e:
            logger.error(f"Critical error in scalping bot: {e}", exc_info=True)
            await self.telegram_notifier.send_message(f"🚨 **Critical Error**: {str(e)}")
        finally:
            await self._shutdown()
    
    async def _validate_account_setup(self):
        """Validate account setup and configuration"""
        try:
            # Check exchange connection
            account_info = await self.trade_executor.get_account_info()
            balance = account_info.get('total_balance', 0)
            
            if balance < 100:  # Minimum $100 for scalping
                raise ValueError(f"Insufficient balance for scalping: ${balance}")
            
            logger.info(f"Account validated - Balance: ${balance:,.2f}")
            
            # Validate symbol availability
            symbol = scalping_config.parameters.PRIMARY_SYMBOL
            ticker = await self.data_collector.get_ticker(symbol)
            if not ticker:
                raise ValueError(f"Cannot access {symbol} market data")
            
            logger.info(f"Symbol validated - {symbol} @ ${ticker.get('last', 0):,.2f}")
            
            # Validate scalping configuration
            validation = scalping_config.validate_config()
            if not validation['valid']:
                raise ValueError(f"Invalid scalping config: {validation['errors']}")
            
            for warning in validation['warnings']:
                logger.warning(f"Config warning: {warning}")
            
            logger.info("✅ Account and configuration validation passed")
            
        except Exception as e:
            logger.error(f"Account validation failed: {e}")
            raise
    
    async def _scalping_cycle(self):
        """Execute one scalping cycle"""
        try:
            self.cycle_count += 1
            cycle_start = time.time()
            
            # Reset daily counters if new day
            await self._check_daily_reset()
            
            # Check if we should continue trading
            if not await self._should_continue_trading():
                return
            
            # Collect market data
            market_data = await self._collect_scalping_data()
            if not market_data:
                return
            
            # Check for position management first
            if self.current_position:
                await self._manage_existing_position()
                return  # Skip new signals if managing position
            
            # Generate correlation analysis
            correlation_results = await self._analyze_correlations(market_data)
            
            # Generate scalping signals
            signals = await self._generate_scalping_signals(market_data, correlation_results)
            
            # Execute signals if any
            if signals:
                await self._execute_scalping_signals(signals, market_data)
            
            # Log cycle performance
            cycle_time = time.time() - cycle_start
            if self.cycle_count % 10 == 0:  # Log every 10 cycles
                logger.info(f"Cycle {self.cycle_count}: {cycle_time:.2f}s, Daily trades: {self.daily_trade_count}/{scalping_config.parameters.TARGET_TRADES_PER_DAY}")
                
        except Exception as e:
            logger.error(f"Error in scalping cycle {self.cycle_count}: {e}", exc_info=True)
    
    async def _check_daily_reset(self):
        """Check and reset daily counters if new day"""
        current_date = datetime.now().date()
        
        if current_date != self.daily_start:
            # Send daily summary before reset
            await self._send_daily_summary()
            
            # Reset counters
            self.daily_trade_count = 0
            self.daily_start = current_date
            self.scalping_stats = {key: 0 if isinstance(value, (int, float)) else value 
                                 for key, value in self.scalping_stats.items()}
            
            logger.info(f"📅 New trading day started: {current_date}")
    
    async def _should_continue_trading(self) -> bool:
        """Check if trading should continue based on various conditions"""
        try:
            # Check emergency mode
            if risk_manager.emergency_mode:
                logger.warning("Trading suspended: Emergency mode active")
                return False
            
            # Check daily trade limits
            if self.daily_trade_count >= scalping_config.parameters.MAX_TRADES_PER_DAY:
                logger.info(f"Daily trade limit reached: {self.daily_trade_count}")
                return False
            
            # Check market hours
            current_time = datetime.utcnow().time()
            if not (scalping_config.parameters.ACTIVE_HOURS_START <= current_time <= scalping_config.parameters.ACTIVE_HOURS_END):
                return False
            
            # Check recent performance (stop if too many consecutive losses)
            recent_losses = await self._count_recent_consecutive_losses()
            if recent_losses >= scalping_config.parameters.CONSECUTIVE_LOSSES_LIMIT:
                logger.warning(f"Too many consecutive losses: {recent_losses}, taking a break")
                await asyncio.sleep(300)  # 5-minute break
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking trading conditions: {e}")
            return False
    
    async def _collect_scalping_data(self) -> Optional[Dict]:
        """Collect market data optimized for scalping"""
        try:
            symbol = scalping_config.parameters.PRIMARY_SYMBOL
            
            # Get current price and volume data
            ticker_data = await self.data_collector.get_ticker(symbol)
            if not ticker_data:
                return None
            
            # Get recent OHLCV data for the main timeframe
            timeframe = scalping_config.parameters.MAIN_TIMEFRAME
            ohlcv_data = await self.data_collector.get_ohlcv(symbol, timeframe, limit=50)
            
            # Check volume threshold
            current_volume = ticker_data.get('volume', 0)
            if current_volume < scalping_config.parameters.MIN_VOLUME_THRESHOLD:
                logger.debug(f"Volume too low for scalping: {current_volume:,.0f}")
                return None
            
            # Check spread
            spread = (ticker_data.get('ask', 0) - ticker_data.get('bid', 0)) / ticker_data.get('last', 1)
            if spread > scalping_config.filters.MAX_VOLATILITY:
                logger.debug(f"Spread too wide for scalping: {spread:.4f}")
                return None
            
            market_data = {
                symbol: {
                    'last': ticker_data.get('last'),
                    'bid': ticker_data.get('bid'),
                    'ask': ticker_data.get('ask'),
                    'volume': current_volume,
                    'change_percent': ticker_data.get('percentage', 0),
                    'ohlcv': ohlcv_data
                }
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error collecting scalping data: {e}")
            return None
    
    async def _analyze_correlations(self, market_data: Dict) -> Dict:
        """Analyze correlations for scalping signals"""
        try:
            # For scalping, we use a simplified correlation analysis
            # Focus on price momentum and volatility rather than complex correlations
            symbol = scalping_config.parameters.PRIMARY_SYMBOL
            price_data = market_data.get(symbol, {})
            ohlcv = price_data.get('ohlcv', [])
            
            if len(ohlcv) < 20:
                return {}
            
            # Calculate simple volatility and momentum metrics
            recent_prices = [candle[4] for candle in ohlcv[-10:]]  # Last 10 close prices
            price_changes = [recent_prices[i] - recent_prices[i-1] for i in range(1, len(recent_prices))]
            
            volatility = max(price_changes) - min(price_changes) if price_changes else 0
            momentum = sum(price_changes) / len(price_changes) if price_changes else 0
            
            # Calculate relative volatility
            avg_price = sum(recent_prices) / len(recent_prices)
            relative_volatility = volatility / avg_price if avg_price > 0 else 0
            
            return {
                'statistics': {
                    'mean_correlation': abs(momentum / avg_price) if avg_price > 0 else 0,
                    'correlation_std': relative_volatility,
                    'momentum': momentum,
                    'volatility': volatility
                },
                'opportunities': [],
                'breakdowns': [],
                'regime': 'scalping'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlations: {e}")
            return {}
    
    async def _generate_scalping_signals(self, market_data: Dict, correlation_results: Dict) -> List[Dict]:
        """Generate scalping-specific signals"""
        try:
            # Use the enhanced scalping signal generation method
            signals = self.signal_generator.generate_scalping_signals(market_data, correlation_results)
            
            # Filter signals based on scalping-specific criteria
            filtered_signals = []
            
            for signal in signals:
                # Check signal freshness
                if self.last_signal_time:
                    time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
                    if time_since_last < scalping_config.parameters.SIGNAL_COOLDOWN_SECONDS:
                        continue
                
                # Validate signal with scalping risk manager
                validation = risk_manager.validate_scalping_trade(
                    signal, 
                    await self._get_current_balance()
                )
                
                if validation['approved']:
                    # Apply any adjustments
                    if 'max_position_size' in validation['adjustments']:
                        signal['position_size'] = validation['adjustments']['max_position_size']
                    
                    filtered_signals.append(signal)
                    self.scalping_stats['total_signals'] += 1
                    
                else:
                    logger.debug(f"Signal rejected: {validation['reason']}")
            
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Error generating scalping signals: {e}")
            return []
    
    async def _execute_scalping_signals(self, signals: List[Dict], market_data: Dict):
        """Execute scalping signals with optimized parameters"""
        try:
            if not signals:
                return
            
            # Take only the first signal (single position focus)
            signal = signals[0]
            
            logger.info(f"🎯 Executing scalping signal: {signal['action']} {signal['symbol']} @ {signal['entry_price']}")
            
            # Execute the trade
            result = await self.trade_executor.execute_trade(
                signal=signal,
                leverage=scalping_config.parameters.OPTIMAL_LEVERAGE,
                order_type='MARKET',  # Market orders for fast execution
                timeout=scalping_config.execution.MAX_EXECUTION_DELAY_MS / 1000
            )
            
            if result and result.get('success'):
                # Track position
                self.current_position = {
                    'signal': signal,
                    'entry_time': datetime.now(),
                    'entry_price': result.get('fill_price', signal['entry_price']),
                    'quantity': result.get('quantity', 0),
                    'side': signal['action']
                }
                
                self.daily_trade_count += 1
                self.scalping_stats['executed_trades'] += 1
                self.last_signal_time = datetime.now()
                
                # Send trade notification
                await self.telegram_notifier.send_message(
                    f"📈 **Scalping Trade Executed**\n"
                    f"Action: {signal['action']} {signal['symbol']}\n"
                    f"Price: ${result.get('fill_price', signal['entry_price']):,.4f}\n"
                    f"Size: {result.get('quantity', 0):.4f}\n"
                    f"Confidence: {signal['confidence']:.1%}\n"
                    f"Daily: {self.daily_trade_count}/{scalping_config.parameters.TARGET_TRADES_PER_DAY}"
                )
                
                logger.info(f"✅ Trade executed successfully - Position opened")
                
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result'
                logger.error(f"❌ Trade execution failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error executing scalping signals: {e}", exc_info=True)
    
    async def _manage_existing_position(self):
        """Manage existing scalping position"""
        try:
            if not self.current_position:
                return
            
            signal = self.current_position['signal']
            symbol = signal['symbol']
            
            # Get current market price
            ticker = await self.data_collector.get_ticker(symbol)
            if not ticker:
                return
            
            current_price = ticker['last']
            entry_price = self.current_position['entry_price']
            entry_time = self.current_position['entry_time']
            side = self.current_position['side']
            
            # Calculate current P&L
            if side.lower() in ['long', 'buy']:
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price
            
            # Calculate holding time
            hold_time = (datetime.now() - entry_time).total_seconds()
            
            # Check exit conditions
            should_exit = False
            exit_reason = ""
            
            # Take profit check
            if pnl_pct >= scalping_config.parameters.TAKE_PROFIT_PERCENT:
                should_exit = True
                exit_reason = f"Take profit hit: {pnl_pct:.2%}"
            
            # Stop loss check
            elif pnl_pct <= -scalping_config.parameters.STOP_LOSS_PERCENT:
                should_exit = True
                exit_reason = f"Stop loss hit: {pnl_pct:.2%}"
            
            # Maximum hold time check
            elif hold_time > scalping_config.parameters.POSITION_HOLD_TIME_MAX:
                should_exit = True
                exit_reason = f"Max hold time exceeded: {hold_time:.0f}s"
            
            # Force exit on emergency
            elif risk_manager.emergency_mode:
                should_exit = True
                exit_reason = "Emergency mode activated"
            
            if should_exit:
                await self._close_position(exit_reason, pnl_pct, hold_time)
            
        except Exception as e:
            logger.error(f"Error managing position: {e}", exc_info=True)
    
    async def _close_position(self, reason: str, pnl_pct: float, hold_time: float):
        """Close the current scalping position"""
        try:
            if not self.current_position:
                return
            
            signal = self.current_position['signal']
            symbol = signal['symbol']
            
            # Execute exit trade
            exit_signal = {
                'symbol': symbol,
                'action': 'sell' if signal['action'].lower() in ['long', 'buy'] else 'buy',
                'quantity': self.current_position['quantity']
            }
            
            result = await self.trade_executor.close_position(symbol)
            
            if result and result.get('success'):
                # Update statistics
                if pnl_pct > 0:
                    self.scalping_stats['successful_scalps'] += 1
                else:
                    self.scalping_stats['failed_scalps'] += 1
                
                self.scalping_stats['total_pnl'] += pnl_pct
                
                if pnl_pct > self.scalping_stats['best_scalp']:
                    self.scalping_stats['best_scalp'] = pnl_pct
                if pnl_pct < self.scalping_stats['worst_scalp']:
                    self.scalping_stats['worst_scalp'] = pnl_pct
                
                # Update average hold time
                total_trades = self.scalping_stats['executed_trades']
                if total_trades > 0:
                    current_avg = self.scalping_stats['average_hold_time']
                    self.scalping_stats['average_hold_time'] = (current_avg * (total_trades - 1) + hold_time) / total_trades
                
                # Calculate win rate
                successful = self.scalping_stats['successful_scalps']
                total = successful + self.scalping_stats['failed_scalps']
                self.scalping_stats['win_rate'] = successful / total if total > 0 else 0
                
                # Update risk manager
                trade_result = {
                    'pnl_pct': pnl_pct,
                    'hold_time_seconds': hold_time,
                    'symbol': symbol,
                    'success': pnl_pct > 0
                }
                risk_manager.update_scalping_metrics(trade_result)
                
                # Send close notification
                await self.telegram_notifier.send_message(
                    f"🔄 **Position Closed**\n"
                    f"Symbol: {symbol}\n"
                    f"P&L: {pnl_pct:.2%}\n"
                    f"Hold Time: {hold_time:.0f}s\n"
                    f"Reason: {reason}\n"
                    f"Win Rate: {self.scalping_stats['win_rate']:.1%}"
                )
                
                logger.info(f"✅ Position closed: {reason} - P&L: {pnl_pct:.2%}")
                
                # Clear current position
                self.current_position = None
                
            else:
                logger.error(f"❌ Failed to close position: {result.get('error', 'Unknown error') if result else 'No result'}")
                
        except Exception as e:
            logger.error(f"Error closing position: {e}", exc_info=True)
    
    async def _get_current_balance(self) -> float:
        """Get current account balance"""
        try:
            account_info = await self.trade_executor.get_account_info()
            return account_info.get('total_balance', 0)
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 1000  # Default fallback
    
    async def _count_recent_consecutive_losses(self) -> int:
        """Count recent consecutive losses for risk management"""
        try:
            # This would normally check recent trade history
            # For now, use a simple heuristic based on current stats
            total_trades = self.scalping_stats['successful_scalps'] + self.scalping_stats['failed_scalps']
            if total_trades < 5:
                return 0
            
            win_rate = self.scalping_stats['win_rate']
            if win_rate < 0.3:  # Less than 30% win rate
                return 3  # Assume 3 consecutive losses
            
            return 0
            
        except Exception as e:
            logger.error(f"Error counting consecutive losses: {e}")
            return 0
    
    async def _send_daily_summary(self):
        """Send daily performance summary"""
        try:
            runtime = datetime.now() - self.start_time
            hours_traded = runtime.total_seconds() / 3600
            
            summary = (
                f"📊 **Daily Scalping Summary**\n"
                f"Runtime: {hours_traded:.1f} hours\n"
                f"Trades: {self.daily_trade_count}\n"
                f"Signals: {self.scalping_stats['total_signals']}\n"
                f"Win Rate: {self.scalping_stats['win_rate']:.1%}\n"
                f"Total P&L: {self.scalping_stats['total_pnl']:.2%}\n"
                f"Best Trade: {self.scalping_stats['best_scalp']:.2%}\n"
                f"Worst Trade: {self.scalping_stats['worst_scalp']:.2%}\n"
                f"Avg Hold: {self.scalping_stats['average_hold_time']:.0f}s"
            )
            
            await self.telegram_notifier.send_message(summary)
            logger.info("Daily summary sent")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    async def _shutdown(self):
        """Graceful shutdown procedure"""
        logger.info("🛑 Shutting down Scalping Trading Bot...")
        
        try:
            self.running = False
            
            # Close any open positions
            if self.current_position:
                logger.info("Closing open position before shutdown...")
                await self._close_position("Bot shutdown", 0, 0)
            
            # Send shutdown summary
            await self._send_daily_summary()
            await self.telegram_notifier.send_message("🛑 **Scalping Bot Stopped**\nAll positions closed safely.")
            
            # Cleanup resources
            if hasattr(self.trade_executor, 'close'):
                await self.trade_executor.close()
            
            logger.info("✅ Scalping bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

async def main():
    """Main entry point for scalping bot"""
    try:
        # Initialize and start the scalping bot
        bot = ScalpingTradingBot()
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
    finally:
        logger.info("Scalping bot terminated")

if __name__ == "__main__":
    try:
        # Run the scalping bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)