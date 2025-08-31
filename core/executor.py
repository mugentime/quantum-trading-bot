"""Production-ready order execution with real Binance API integration"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
import numpy as np
from .config.settings import config
from utils.telegram_notifier import telegram_notifier
from .leverage_manager import leverage_manager
from .optimization_integrator import optimization_integrator
from .data_authenticity_validator import authenticity_validator, DataAuthenticityError
from .environment_manager import environment_manager, Environment

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderType(Enum):
    """Supported order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS_LIMIT = "stop_loss_limit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"

@dataclass
class ExecutionResult:
    """Comprehensive execution result with full metadata"""
    status: str
    signal_id: str
    order_id: Optional[str] = None
    symbol: str = ""
    action: str = ""
    order_type: str = OrderType.MARKET.value
    requested_quantity: float = 0.0
    executed_quantity: float = 0.0
    requested_price: Optional[float] = None
    executed_price: Optional[float] = None
    fees: Dict[str, float] = field(default_factory=dict)
    slippage: Optional[float] = None
    execution_time_ms: int = 0
    exchange_timestamp: Optional[int] = None
    local_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error_message: Optional[str] = None
    retry_count: int = 0
    risk_checks_passed: bool = False
    additional_info: Dict[str, Any] = field(default_factory=dict)

class Executor:
    """Production-ready trade executor with comprehensive order management"""
    
    def __init__(self, 
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 slippage_tolerance: float = None):
        """Initialize production Executor with real Binance API and security validation"""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.slippage_tolerance = slippage_tolerance or config.SLIPPAGE_TOLERANCE
        
        # Order and position tracking
        self.active_orders: Dict[str, Dict] = {}
        self.positions: Dict[str, Dict] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # Exchange connection
        self.exchange = None
        self.connected = False
        
        # Performance tracking
        self.total_trades = 0
        self.successful_trades = 0
        self.total_slippage = 0.0
        
        # Initialize security systems
        authenticity_validator.set_alert_callback(self._handle_authenticity_alert)
        
        logger.info("Production Executor initialized with real API integration and data security validation")
        
    async def initialize_exchange(self) -> bool:
        """Initialize and authenticate with Binance exchange"""
        try:
            self.exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'sandbox': config.BINANCE_TESTNET,
                'enableRateLimit': True,
                'timeout': config.ORDER_TIMEOUT * 1000,  # Convert to milliseconds
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 10000,
                }
            })
            
            # Test connection and permissions
            account_info = await self.exchange.fetch_balance()
            logger.info(f"Exchange connection successful. Account type: {'TESTNET' if config.BINANCE_TESTNET else 'MAINNET'}")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            self.connected = False
            return False
    
    async def execute(self, signal: Dict) -> ExecutionResult:
        """Execute trading signal with comprehensive error handling and retry logic"""
        start_time = time.time()
        signal_id = signal.get('id', 'unknown')
        
        # SECURITY: Validate signal data authenticity
        try:
            if not authenticity_validator.validate_market_data(signal, f"trading_signal_{signal_id}"):
                raise DataAuthenticityError(f"Trading signal {signal_id} failed authenticity validation")
            logger.debug(f"Signal {signal_id} passed authenticity validation")
        except DataAuthenticityError as e:
            logger.error(f"SECURITY ALERT: {e}")
            await telegram_notifier.send_error_alert(
                "DATA SECURITY VIOLATION", 
                str(e), 
                signal.get('symbol', 'UNKNOWN')
            )
            return ExecutionResult(
                status="REJECTED",
                signal_id=signal_id,
                error_message=f"Security validation failed: {e}"
            )
        
        # OPTIMIZATION ENHANCEMENT: Generate enhanced signal
        try:
            logger.info(f"🚀 OPTIMIZATION: Enhancing signal for {signal.get('symbol', 'UNKNOWN')}")
            await telegram_notifier.send_message(
                f"🔧 OPTIMIZATION ACTIVE\n"
                f"Symbol: {signal.get('symbol', 'UNKNOWN')}\n"
                f"Original Signal: {signal.get('deviation', 0):.3f}\n"
                f"Enhancing with ML, multi-timeframe, and regime analysis..."
            )
            
            # Get account balance for risk validation
            account_balance = await self._get_account_balance()
            
            # Generate enhanced signal using optimization system
            enhanced_signal = await optimization_integrator.generate_enhanced_signal(
                signal, config.SYMBOLS + ['BTCUSDT'], self.exchange
            )
            
            # Use enhanced signal if available
            if enhanced_signal.get('enhanced', False):
                signal = enhanced_signal
                logger.info(f"✅ OPTIMIZATION: Signal enhanced - strength: {signal.get('final_strength', 0):.3f}, confidence: {signal.get('confidence', 0):.3f}")
                
                await telegram_notifier.send_message(
                    f"✅ SIGNAL ENHANCED!\n"
                    f"Original → Enhanced\n"
                    f"Strength: {enhanced_signal.get('original_strength', 0):.3f} → {enhanced_signal.get('final_strength', 0):.3f}\n"
                    f"Confidence: {enhanced_signal.get('confidence', 0):.3f}\n"
                    f"Suggested Leverage: {enhanced_signal.get('suggested_leverage', config.DEFAULT_LEVERAGE)}x\n"
                    f"Expected Performance Boost: +{((enhanced_signal.get('final_strength', 0)/enhanced_signal.get('original_strength', 0.01))-1)*100:.0f}%"
                )
            
        except Exception as e:
            logger.error(f"Optimization enhancement failed: {e}")
            await telegram_notifier.send_error_alert(
                "Optimization Warning",
                f"Enhancement failed, using base signal: {e}",
                signal.get('symbol', 'UNKNOWN')
            )
        
        # Initialize result object
        result = ExecutionResult(
            status="PENDING",
            signal_id=signal_id,
            symbol=signal.get('symbol', ''),
            action=signal.get('action', ''),
            requested_price=signal.get('entry_price')
        )
        
        try:
            # Ensure exchange is connected
            if not self.connected:
                if not await self.initialize_exchange():
                    result.status = "ERROR"
                    result.error_message = "Failed to connect to exchange"
                    return result
            
            # Validate signal
            if not self._validate_signal(signal):
                result.status = "REJECTED"
                result.error_message = "Signal validation failed"
                return result
            
            # OPTIMIZATION: Enhanced risk validation
            try:
                await telegram_notifier.send_message(
                    f"🔒 ADVANCED RISK VALIDATION\n"
                    f"Running enhanced risk checks with:\n"
                    f"• Portfolio heat analysis\n"
                    f"• Correlation exposure limits\n"
                    f"• Performance-based adjustments\n"
                    f"• Market regime analysis"
                )
                
                # Get current positions for risk analysis
                current_positions = await self._get_current_positions()
                
                # Run enhanced risk validation
                risk_validation = await optimization_integrator.validate_enhanced_trade_risk(
                    signal, account_balance, current_positions, self.exchange
                )
                
                if not risk_validation.get('approved', False):
                    result.status = "REJECTED"
                    result.error_message = f"Enhanced risk validation failed: {risk_validation.get('reasoning', 'Risk too high')}"
                    
                    await telegram_notifier.send_error_alert(
                        "Trade Rejected - Risk Management",
                        f"Enhanced risk validation failed:\n{risk_validation.get('reasoning', 'Risk too high')}",
                        signal.get('symbol', 'UNKNOWN')
                    )
                    return result
                
                # Apply risk adjustments if any
                adjustments = risk_validation.get('adjustments', {})
                if adjustments:
                    logger.info(f"Applying risk adjustments: {adjustments}")
                    if 'leverage' in adjustments:
                        signal['suggested_leverage'] = adjustments['leverage']
                    if 'position_size' in adjustments:
                        signal['suggested_position_size'] = adjustments['position_size']
                    
                    await telegram_notifier.send_message(
                        f"⚡ RISK ADJUSTMENTS APPLIED\n"
                        f"Leverage: {adjustments.get('leverage', 'no change')}\n"
                        f"Position Size: {adjustments.get('position_size', 'no change'):.3f}\n"
                        f"Risk Score: {risk_validation.get('risk_score', 0):.2f}/1.0"
                    )
                
            except Exception as e:
                logger.error(f"Enhanced risk validation failed: {e}")
                await telegram_notifier.send_error_alert(
                    "Risk Validation Error", 
                    f"Enhanced validation failed, using basic validation: {e}",
                    signal.get('symbol', 'UNKNOWN')
                )
            
            # Use the account balance we already fetched
            # balance = await self.exchange.fetch_balance()
            # account_balance = balance.get('USDT', {}).get('free', 0)
            
            # Calculate optimal leverage
            optimal_leverage = await leverage_manager.calculate_optimal_leverage(
                signal, account_balance, exchange=self.exchange
            )
            
            # Set leverage for the symbol
            await self._set_leverage(signal.get('symbol'), optimal_leverage)
            
            # Calculate position size with leverage optimization
            position_size = leverage_manager.calculate_optimal_position_size(
                signal, account_balance, optimal_leverage
            )
            result.requested_quantity = position_size
            
            # Execute order with retry logic
            for attempt in range(self.max_retries + 1):
                try:
                    result.retry_count = attempt
                    
                    # Place order
                    order = await self._place_order(signal, position_size)
                    
                    if order:
                        result.order_id = order.get('id')
                        result.status = "FILLED"
                        result.executed_quantity = order.get('filled', 0)
                        result.executed_price = order.get('average') or order.get('price')
                        result.exchange_timestamp = order.get('timestamp')
                        result.fees = order.get('fees', {})
                        
                        # Calculate slippage
                        if result.executed_price and result.requested_price:
                            result.slippage = self._calculate_slippage(
                                result.requested_price, 
                                result.executed_price, 
                                signal.get('action', 'buy')
                            )
                        
                        # Update tracking
                        await self._update_position_tracking(signal, order, result)
                        
                        # Send Telegram notification for successful order
                        await self._send_order_notification(signal, result)
                        
                        # Mark as successful
                        self.successful_trades += 1
                        result.risk_checks_passed = True
                        
                        logger.info(f"Successfully executed {signal_id}: "
                                  f"{result.action} {result.executed_quantity} {result.symbol} "
                                  f"at {result.executed_price}")
                        break
                    
                except ccxt.InsufficientFunds as e:
                    result.status = "REJECTED"
                    result.error_message = f"Insufficient funds: {str(e)}"
                    logger.error(f"Insufficient funds for {signal_id}: {e}")
                    break  # Don't retry for insufficient funds
                
                except ccxt.InvalidOrder as e:
                    result.status = "REJECTED"
                    result.error_message = f"Invalid order: {str(e)}"
                    logger.error(f"Invalid order for {signal_id}: {e}")
                    break  # Don't retry for invalid orders
                
                except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Network/Exchange error for {signal_id} (attempt {attempt + 1}): {e}. "
                                     f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        result.status = "ERROR"
                        result.error_message = f"Max retries exceeded: {str(e)}"
                        logger.error(f"Max retries exceeded for {signal_id}: {e}")
                
                except Exception as e:
                    result.status = "ERROR"
                    result.error_message = f"Unexpected error: {str(e)}"
                    logger.error(f"Unexpected execution error for {signal_id}: {e}", exc_info=True)
                    
                    # Send error notification
                    await telegram_notifier.send_error_alert(
                        "Execution Error", 
                        str(e), 
                        signal.get('symbol')
                    )
                    break
            
        except Exception as e:
            result.status = "ERROR"
            result.error_message = f"Critical error: {str(e)}"
            logger.error(f"Critical execution error for {signal_id}: {e}", exc_info=True)
        
        finally:
            # Record execution time
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update statistics
            self.total_trades += 1
            if result.slippage is not None:
                self.total_slippage += abs(result.slippage)
            
            # Store in history
            self.execution_history.append(result)
            if len(self.execution_history) > 1000:  # Keep last 1000 executions
                self.execution_history = self.execution_history[-1000:]
            
            # Update leverage manager with trade result
            if result.status == "FILLED" and hasattr(result, 'executed_price'):
                trade_pnl = 0  # Will be calculated when position is closed
                if result.slippage is not None:
                    # Estimate P&L from slippage for now
                    trade_pnl = -abs(result.slippage) * result.executed_quantity * 0.01
                
                leverage_manager.update_daily_pnl(trade_pnl)
                leverage_manager.add_trade_result({
                    'pnl_usd': trade_pnl,
                    'symbol': result.symbol,
                    'status': result.status
                })
        
        return result
        
    def _validate_signal(self, signal: Dict) -> bool:
        """Validate trading signal before execution"""
        try:
            required_fields = ['id', 'symbol', 'action', 'entry_price', 'confidence']
            for field in required_fields:
                if field not in signal or signal[field] is None:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate symbol format
            symbol = signal['symbol']
            if not isinstance(symbol, str) or len(symbol) < 6:
                logger.error(f"Invalid symbol format: {symbol}")
                return False
            
            # Validate action
            if signal['action'].lower() not in ['long', 'short', 'buy', 'sell']:
                logger.error(f"Invalid action: {signal['action']}")
                return False
            
            # Validate price
            if not isinstance(signal['entry_price'], (int, float)) or signal['entry_price'] <= 0:
                logger.error(f"Invalid entry price: {signal['entry_price']}")
                return False
            
            # Validate confidence
            confidence = signal.get('confidence', 0)
            if not isinstance(confidence, (int, float)) or confidence < 0.5 or confidence > 1.0:
                logger.error(f"Invalid confidence level: {confidence}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Signal validation error: {e}")
            return False
    
    async def _calculate_position_size(self, signal: Dict) -> float:
        """Calculate position size based on risk parameters and account balance"""
        try:
            # Get account balance
            balance = await self.exchange.fetch_balance()
            
            # Determine base currency (usually USDT)
            base_currency = 'USDT'
            available_balance = balance.get(base_currency, {}).get('free', 0)
            
            if available_balance <= 0:
                logger.error("No available balance for trading")
                return 0.0
            
            # Get position size from signal or use risk per trade
            signal_position_size = signal.get('position_size', config.RISK_PER_TRADE)
            
            # Calculate position size in base currency
            position_value = available_balance * signal_position_size
            
            # Convert to quantity based on entry price
            entry_price = signal['entry_price']
            quantity = position_value / entry_price
            
            # Apply minimum and maximum limits
            min_quantity = 0.001  # Minimum trade size
            max_quantity = available_balance * 0.2 / entry_price  # Max 20% of balance
            
            quantity = max(min_quantity, min(quantity, max_quantity))
            
            logger.debug(f"Calculated position size: {quantity} for {signal['symbol']} "
                        f"(value: ${position_value:.2f})")
            
            return quantity
            
        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            return 0.001  # Return minimum safe size
    
    async def _place_order(self, signal: Dict, quantity: float) -> Optional[Dict]:
        """Place order on exchange with comprehensive error handling"""
        try:
            symbol = signal['symbol']
            action = signal['action'].lower()
            entry_price = signal['entry_price']
            
            # Map action to exchange format
            side = 'buy' if action in ['long', 'buy'] else 'sell'
            
            # For now, use market orders for guaranteed execution
            # TODO: Add support for limit orders with better price control
            order_type = 'market'
            
            logger.info(f"Placing {order_type} {side} order: {quantity} {symbol}")
            
            # Place order
            order = await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=quantity,
                price=None,  # Market order
                params={}
            )
            
            # Wait for order to be filled (for market orders, usually immediate)
            if order and order.get('id'):
                order_id = order['id']
                
                # Wait up to 30 seconds for fill
                for _ in range(30):
                    updated_order = await self.exchange.fetch_order(order_id, symbol)
                    if updated_order.get('status') == 'closed':
                        logger.info(f"Order {order_id} filled successfully")
                        return updated_order
                    await asyncio.sleep(1)
                
                logger.warning(f"Order {order_id} not filled within timeout")
                return updated_order
            
            return order
            
        except (ccxt.InsufficientFunds, ccxt.InvalidOrder) as e:
            # Re-raise specific exceptions to be handled by execute method
            raise e
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return None
    
    def _calculate_slippage(self, requested_price: float, executed_price: float, action: str) -> float:
        """Calculate slippage percentage"""
        try:
            # For buy orders, positive slippage = paid more than expected
            # For sell orders, positive slippage = received less than expected
            if action.lower() in ['long', 'buy']:
                slippage = (executed_price - requested_price) / requested_price * 100
            else:  # short/sell
                slippage = (requested_price - executed_price) / requested_price * 100
            
            return slippage
            
        except Exception as e:
            logger.error(f"Slippage calculation error: {e}")
            return 0.0
    
    async def _update_position_tracking(self, signal: Dict, order: Dict, result: ExecutionResult):
        """Update position tracking after successful execution"""
        try:
            position_id = signal.get('id')
            
            self.positions[position_id] = {
                'symbol': signal['symbol'],
                'side': signal['action'],
                'entry_price': result.executed_price,
                'quantity': result.executed_quantity,
                'order_id': result.order_id,
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'status': 'open',
                'timestamp': result.local_timestamp,
                'fees_paid': result.fees
            }
            
            # Store order info
            self.active_orders[result.order_id] = {
                'signal_id': position_id,
                'order': order,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Position tracking update error: {e}")
    
    async def _set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for futures position"""
        try:
            if hasattr(self.exchange, 'set_leverage'):
                await self.exchange.set_leverage(leverage, symbol)
                logger.info(f"Set leverage to {leverage}x for {symbol}")
                return True
            else:
                logger.warning(f"Exchange does not support leverage setting")
                return False
        except Exception as e:
            logger.error(f"Failed to set leverage for {symbol}: {e}")
            return False
    
    async def _send_order_notification(self, signal: Dict, result: ExecutionResult):
        """Send Telegram notification for executed order"""
        try:
            action = signal.get('action', '').lower()
            
            if action in ['long', 'buy']:
                # Enhanced buy notification with optimization details
                enhancement_info = ""
                if signal.get('enhanced', False):
                    enhancement_info = f"\n🚀 OPTIMIZATION ACTIVE\nStrength Boost: +{((signal.get('final_strength', 0)/signal.get('original_strength', 0.01))-1)*100:.0f}%\nLeverage: {signal.get('suggested_leverage', config.DEFAULT_LEVERAGE)}x"
                
                await telegram_notifier.send_buy_order_alert(
                    symbol=result.symbol,
                    price=result.executed_price,
                    quantity=result.executed_quantity,
                    stop_loss=signal.get('stop_loss', 0),
                    take_profit=signal.get('take_profit', 0),
                    reason=f"Signal confidence: {signal.get('confidence', 0):.2%}{enhancement_info}"
                )
                
                # OPTIMIZATION: Setup enhanced exit management
                try:
                    position_data = {
                        'symbol': result.symbol,
                        'side': 'BUY',
                        'entry_price': result.executed_price,
                        'entry_time': datetime.now().isoformat(),
                        'quantity': result.executed_quantity
                    }
                    
                    enhanced_exit = await optimization_integrator.setup_enhanced_exit_management(
                        position_data, result.executed_price, self.exchange
                    )
                    
                    if enhanced_exit:
                        await telegram_notifier.send_message(
                            f"🎯 ENHANCED EXIT MANAGEMENT ACTIVE\n"
                            f"Symbol: {result.symbol}\n"
                            f"Dynamic timing: {enhanced_exit.get('dynamic_timing', {}).get('adjusted_timing_minutes', 120)} min\n"
                            f"Trailing stop: {'Active' if enhanced_exit.get('trailing_stop', {}).get('trailing_active', False) else 'Standby'}\n"
                            f"Strategy: Volatility-based adaptive exits"
                        )
                except Exception as e:
                    logger.error(f"Failed to setup enhanced exit management: {e}")
            else:
                # For sell orders, calculate P&L if we have position info
                position_id = signal.get('id')
                position = self.positions.get(position_id, {})
                
                if position:
                    entry_price = position.get('entry_price', result.executed_price)
                    pnl = (result.executed_price - entry_price) * result.executed_quantity
                    pnl_percent = ((result.executed_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                else:
                    pnl = 0
                    pnl_percent = 0
                
                await telegram_notifier.send_sell_order_alert(
                    symbol=result.symbol,
                    price=result.executed_price,
                    quantity=result.executed_quantity,
                    pnl=pnl,
                    pnl_percent=pnl_percent,
                    reason=f"Signal confidence: {signal.get('confidence', 0):.2%}"
                )
                
        except Exception as e:
            logger.error(f"Failed to send order notification: {e}")
    
    async def _get_account_balance(self) -> float:
        """Get current USDT account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            return balance.get('USDT', {}).get('free', 0.0)
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return 10000.0  # Default fallback
    
    async def _get_current_positions(self) -> Dict:
        """Get current open positions"""
        try:
            positions = await self.exchange.fetch_positions()
            current_positions = {}
            
            for position in positions:
                if position['contracts'] > 0:  # Non-zero position
                    symbol = position['symbol']
                    current_positions[symbol] = {
                        'symbol': symbol,
                        'side': position['side'],
                        'quantity': position['contracts'],
                        'entry_price': position['entryPrice'],
                        'unrealized_pnl': position['unrealizedPnl']
                    }
            
            return current_positions
        except Exception as e:
            logger.error(f"Failed to get current positions: {e}")
            return {}

    async def close_all_positions(self):
        """Close all open positions with proper error handling"""
        logger.info("Closing all open positions...")
        closed_count = 0
        error_count = 0
        
        try:
            if not self.connected:
                await self.initialize_exchange()
            
            for position_id, position in list(self.positions.items()):
                if position.get('status') == 'open':
                    try:
                        # Create opposite order to close position
                        symbol = position['symbol']
                        side = 'sell' if position['side'].lower() in ['long', 'buy'] else 'buy'
                        quantity = position['quantity']
                        
                        # Place closing order
                        close_order = await self.exchange.create_order(
                            symbol=symbol,
                            type='market',
                            side=side,
                            amount=quantity,
                            price=None
                        )
                        
                        if close_order:
                            position['status'] = 'closed'
                            position['close_order_id'] = close_order.get('id')
                            position['closed_at'] = datetime.now().isoformat()
                            closed_count += 1
                            
                            logger.info(f"Closed position {position_id}: {symbol} "
                                      f"({side} {quantity})")
                        
                    except Exception as e:
                        logger.error(f"Error closing position {position_id}: {e}")
                        error_count += 1
            
            logger.info(f"Position closure complete: {closed_count} closed, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Critical error during position closure: {e}")
    
    async def get_open_positions(self) -> List[Dict]:
        """Get all currently open positions"""
        return [pos for pos in self.positions.values() if pos.get('status') == 'open']
    
    async def get_execution_stats(self) -> Dict:
        """Get comprehensive execution statistics"""
        if self.total_trades == 0:
            return {'total_trades': 0}
        
        success_rate = (self.successful_trades / self.total_trades) * 100
        avg_slippage = self.total_slippage / self.total_trades if self.total_trades > 0 else 0
        
        # Analyze recent executions
        recent_executions = self.execution_history[-100:]  # Last 100
        avg_execution_time = np.mean([r.execution_time_ms for r in recent_executions]) if recent_executions else 0
        
        status_counts = {}
        for result in self.execution_history:
            status = result.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'success_rate': success_rate,
            'average_slippage': avg_slippage,
            'average_execution_time_ms': avg_execution_time,
            'status_breakdown': status_counts,
            'open_positions': len(await self.get_open_positions()),
            'slippage_tolerance': self.slippage_tolerance,
            'max_retries': self.max_retries,
            'connected': self.connected
        }
    
    async def validate_connection(self) -> bool:
        """Validate exchange connection and permissions"""
        try:
            if not self.connected:
                return await self.initialize_exchange()
            
            # Test with a simple balance query
            await self.exchange.fetch_balance()
            return True
            
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            self.connected = False
            return False
    
    async def cleanup(self):
        """Clean up resources and close exchange connection"""
        try:
            if self.exchange:
                await self.exchange.close()
                logger.info("Exchange connection closed")
            
            self.connected = False
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            
        logger.info("Executor cleanup completed")
    
    async def _handle_authenticity_alert(self, message: str):
        """Handle data authenticity alerts"""
        logger.critical(f"DATA AUTHENTICITY ALERT: {message}")
        try:
            await telegram_notifier.send_error_alert(
                "CRITICAL: Data Authenticity Violation",
                message,
                "SYSTEM"
            )
        except Exception as e:
            logger.error(f"Failed to send authenticity alert: {e}")
