"""
High-Frequency Scalping Risk Management System

Designed specifically for Binance futures scalping with:
- 20-50+ trades per day
- 1-5 minute hold periods
- 0.5-1% profit targets per trade
- Aggressive position sizing with proper safeguards
- Real-time liquidation prevention
- Emergency exit protocols
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from threading import Lock, Event

class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate" 
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ExitType(Enum):
    MARKET = "MARKET"
    STOP_MARKET = "STOP_MARKET"
    OCO = "OCO"
    EMERGENCY = "EMERGENCY_LIQUIDATION"

@dataclass
class RiskParameters:
    """Risk parameters for scalping operations"""
    # Liquidation Prevention
    max_leverage: float = 10.0
    liquidation_buffer: float = 0.15  # 15% buffer from liquidation
    safe_margin_ratio: float = 0.25   # Keep 25% margin available
    
    # Position Sizing
    max_position_size_usd: float = 10000.0  # Max position in USD
    position_size_percent: float = 0.02     # 2% of account per trade
    max_concurrent_positions: int = 3       # Max simultaneous positions
    
    # Drawdown Control
    daily_loss_limit: float = 0.05          # 5% daily loss limit
    max_consecutive_losses: int = 5         # Circuit breaker
    rapid_loss_threshold: float = 0.02      # 2% loss in 5 minutes
    
    # Slippage Management
    max_slippage_bps: float = 5.0           # Max 5 bps slippage
    slippage_adjustment: float = 1.2        # Multiply expected slippage
    
    # Funding Rate
    funding_rate_threshold: float = 0.01    # 1% funding rate concern
    funding_time_buffer: int = 300          # 5 min before funding

@dataclass
class PositionRisk:
    """Risk metrics for a single position"""
    symbol: str
    side: str
    entry_price: float
    quantity: float
    leverage: float
    unrealized_pnl: float
    liquidation_price: float
    margin_ratio: float
    time_held: int  # seconds
    risk_level: RiskLevel
    exit_reasons: List[str] = field(default_factory=list)

@dataclass
class AccountRisk:
    """Overall account risk metrics"""
    total_balance: float
    available_balance: float
    total_unrealized_pnl: float
    daily_pnl: float
    daily_trades: int
    consecutive_losses: int
    risk_level: RiskLevel
    circuit_breaker_active: bool = False
    last_funding_check: datetime = field(default_factory=datetime.now)

class ScalpingRiskManager:
    """High-frequency scalping risk management system"""
    
    def __init__(self, exchange_client, risk_params: RiskParameters = None):
        self.exchange = exchange_client
        self.risk_params = risk_params or RiskParameters()
        self.logger = logging.getLogger(__name__)
        
        # Thread safety
        self._lock = Lock()
        self._emergency_stop = Event()
        
        # Risk tracking
        self.positions: Dict[str, PositionRisk] = {}
        self.account_risk: AccountRisk = None
        self.trade_history: List[Dict] = []
        
        # Performance tracking
        self.daily_stats = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'start_balance': 0.0,
            'last_reset': datetime.now().date()
        }
        
        # Funding rate cache
        self.funding_rates: Dict[str, Dict] = {}
        self.next_funding_time: datetime = None
        
        # Slippage tracking
        self.slippage_history: Dict[str, List[float]] = {}
        
    async def initialize(self):
        """Initialize risk management system"""
        try:
            # Get account info
            account_info = await self.exchange.futures_account()
            
            self.account_risk = AccountRisk(
                total_balance=float(account_info['totalWalletBalance']),
                available_balance=float(account_info['availableBalance']),
                total_unrealized_pnl=float(account_info['totalUnrealizedProfit']),
                daily_pnl=0.0,
                daily_trades=0,
                consecutive_losses=0,
                risk_level=RiskLevel.LOW
            )
            
            # Initialize daily stats
            if self.daily_stats['last_reset'] != datetime.now().date():
                await self._reset_daily_stats()
            
            # Update funding rates
            await self._update_funding_rates()
            
            self.logger.info(f"Risk manager initialized - Balance: ${self.account_risk.total_balance:.2f}")
            
        except Exception as e:
            self.logger.error(f"Risk manager initialization failed: {e}")
            raise
    
    async def validate_entry(self, symbol: str, side: str, quantity: float, 
                           leverage: float, entry_price: float = None) -> Tuple[bool, str, Dict]:
        """Validate trade entry with comprehensive risk checks"""
        try:
            with self._lock:
                # Emergency stop check
                if self._emergency_stop.is_set():
                    return False, "Emergency stop active", {}
                
                # Circuit breaker check
                if self.account_risk.circuit_breaker_active:
                    return False, "Circuit breaker active - excessive losses", {}
                
                # Daily loss limit check
                if self.account_risk.daily_pnl <= -self.risk_params.daily_loss_limit * self.account_risk.total_balance:
                    return False, f"Daily loss limit reached: {self.account_risk.daily_pnl:.2f}", {}
                
                # Maximum concurrent positions
                if len(self.positions) >= self.risk_params.max_concurrent_positions:
                    return False, f"Maximum concurrent positions ({self.risk_params.max_concurrent_positions}) reached", {}
                
                # Leverage validation
                if leverage > self.risk_params.max_leverage:
                    return False, f"Leverage {leverage}x exceeds maximum {self.risk_params.max_leverage}x", {}
                
                # Position size validation
                position_value = quantity * (entry_price or await self._get_current_price(symbol))
                max_position = min(
                    self.risk_params.max_position_size_usd,
                    self.account_risk.available_balance * self.risk_params.position_size_percent * leverage
                )
                
                if position_value > max_position:
                    return False, f"Position size ${position_value:.2f} exceeds maximum ${max_position:.2f}", {}
                
                # Liquidation distance check
                liquidation_price = await self._calculate_liquidation_price(symbol, side, quantity, leverage, entry_price)
                current_price = entry_price or await self._get_current_price(symbol)
                
                liquidation_distance = abs(liquidation_price - current_price) / current_price
                if liquidation_distance < self.risk_params.liquidation_buffer:
                    return False, f"Too close to liquidation: {liquidation_distance*100:.2f}% buffer", {}
                
                # Funding rate check
                funding_risk = await self._check_funding_risk(symbol, side)
                if funding_risk['risk_level'] == RiskLevel.CRITICAL:
                    return False, f"High funding rate risk: {funding_risk['message']}", {}
                
                # Slippage estimate
                expected_slippage = await self._estimate_slippage(symbol, quantity)
                if expected_slippage > self.risk_params.max_slippage_bps:
                    return False, f"Expected slippage {expected_slippage:.1f}bps exceeds limit", {}
                
                # All checks passed
                risk_metrics = {
                    'liquidation_price': liquidation_price,
                    'liquidation_distance': liquidation_distance,
                    'position_value': position_value,
                    'expected_slippage': expected_slippage,
                    'funding_risk': funding_risk,
                    'risk_level': self._calculate_position_risk_level(liquidation_distance, expected_slippage)
                }
                
                return True, "Entry validated", risk_metrics
                
        except Exception as e:
            self.logger.error(f"Entry validation error: {e}")
            return False, f"Validation error: {str(e)}", {}
    
    async def register_position(self, symbol: str, side: str, quantity: float, 
                              entry_price: float, leverage: float, order_id: str):
        """Register new position for risk tracking"""
        try:
            with self._lock:
                liquidation_price = await self._calculate_liquidation_price(symbol, side, quantity, leverage, entry_price)
                
                position_risk = PositionRisk(
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    quantity=quantity,
                    leverage=leverage,
                    unrealized_pnl=0.0,
                    liquidation_price=liquidation_price,
                    margin_ratio=1.0,
                    time_held=0,
                    risk_level=RiskLevel.LOW
                )
                
                self.positions[order_id] = position_risk
                self.daily_stats['trades'] += 1
                
                self.logger.info(f"Position registered: {symbol} {side} {quantity} @ {entry_price}")
                
        except Exception as e:
            self.logger.error(f"Position registration error: {e}")
    
    async def update_positions(self):
        """Update all position risk metrics"""
        try:
            if not self.positions:
                return
            
            # Get current positions from exchange
            exchange_positions = await self.exchange.futures_position_information()
            
            with self._lock:
                for order_id, position_risk in self.positions.items():
                    # Find matching exchange position
                    exchange_pos = None
                    for pos in exchange_positions:
                        if pos['symbol'] == position_risk.symbol:
                            exchange_pos = pos
                            break
                    
                    if exchange_pos:
                        # Update metrics
                        position_risk.unrealized_pnl = float(exchange_pos['unRealizedProfit'])
                        position_risk.margin_ratio = float(exchange_pos['marginRatio'])
                        
                        # Calculate risk level
                        current_price = float(exchange_pos['markPrice'])
                        liquidation_distance = abs(position_risk.liquidation_price - current_price) / current_price
                        
                        position_risk.risk_level = self._calculate_position_risk_level(
                            liquidation_distance, position_risk.margin_ratio
                        )
                        
                        # Check for exit triggers
                        exit_reasons = await self._check_exit_triggers(position_risk, current_price)
                        if exit_reasons:
                            position_risk.exit_reasons.extend(exit_reasons)
                            await self._execute_emergency_exit(order_id, position_risk)
                
                # Update account risk
                await self._update_account_risk()
                
        except Exception as e:
            self.logger.error(f"Position update error: {e}")
    
    async def _check_exit_triggers(self, position: PositionRisk, current_price: float) -> List[str]:
        """Check if position should be exited immediately"""
        exit_reasons = []
        
        # Liquidation proximity
        liquidation_distance = abs(position.liquidation_price - current_price) / current_price
        if liquidation_distance < self.risk_params.liquidation_buffer:
            exit_reasons.append(f"Liquidation risk: {liquidation_distance*100:.2f}% from liquidation")
        
        # High margin ratio
        if position.margin_ratio > 0.8:  # 80% margin used
            exit_reasons.append(f"High margin ratio: {position.margin_ratio*100:.1f}%")
        
        # Time-based exit (positions should be short-term)
        if position.time_held > 300:  # 5 minutes
            exit_reasons.append(f"Position held too long: {position.time_held}s")
        
        # Funding rate proximity
        if self.next_funding_time:
            time_to_funding = (self.next_funding_time - datetime.now()).total_seconds()
            if time_to_funding < self.risk_params.funding_time_buffer:
                funding_rate = self.funding_rates.get(position.symbol, {}).get('fundingRate', 0)
                if abs(float(funding_rate)) > self.risk_params.funding_rate_threshold:
                    exit_reasons.append(f"High funding rate approaching: {float(funding_rate)*100:.3f}%")
        
        return exit_reasons
    
    async def _execute_emergency_exit(self, order_id: str, position: PositionRisk):
        """Execute emergency position exit"""
        try:
            self.logger.warning(f"Emergency exit triggered for {position.symbol}: {position.exit_reasons}")
            
            # Determine best exit method based on urgency
            if RiskLevel.CRITICAL in [risk for risk in position.exit_reasons if 'Liquidation' in str(risk)]:
                # Market order for liquidation risk
                exit_type = ExitType.MARKET
            else:
                # Stop market for other risks
                exit_type = ExitType.STOP_MARKET
            
            # Execute exit
            await self._execute_exit_order(position, exit_type)
            
            # Remove from tracking
            del self.positions[order_id]
            
            # Update consecutive losses if needed
            if position.unrealized_pnl < 0:
                self.account_risk.consecutive_losses += 1
                self.daily_stats['losses'] += 1
            else:
                self.account_risk.consecutive_losses = 0
                self.daily_stats['wins'] += 1
            
            # Check for circuit breaker
            if self.account_risk.consecutive_losses >= self.risk_params.max_consecutive_losses:
                await self._activate_circuit_breaker()
            
        except Exception as e:
            self.logger.error(f"Emergency exit error: {e}")
    
    async def _execute_exit_order(self, position: PositionRisk, exit_type: ExitType):
        """Execute position exit order"""
        try:
            if exit_type == ExitType.MARKET:
                # Market order for immediate exit
                await self.exchange.futures_create_order(
                    symbol=position.symbol,
                    side='SELL' if position.side == 'BUY' else 'BUY',
                    type='MARKET',
                    quantity=abs(position.quantity),
                    reduceOnly=True
                )
            
            elif exit_type == ExitType.STOP_MARKET:
                # Stop market order
                current_price = await self._get_current_price(position.symbol)
                stop_price = current_price * 0.999 if position.side == 'BUY' else current_price * 1.001
                
                await self.exchange.futures_create_order(
                    symbol=position.symbol,
                    side='SELL' if position.side == 'BUY' else 'BUY',
                    type='STOP_MARKET',
                    quantity=abs(position.quantity),
                    stopPrice=stop_price,
                    reduceOnly=True
                )
            
            self.logger.info(f"Exit order executed: {exit_type.value} for {position.symbol}")
            
        except Exception as e:
            self.logger.error(f"Exit order execution error: {e}")
    
    async def _activate_circuit_breaker(self):
        """Activate circuit breaker - stop all trading"""
        self.logger.critical(f"CIRCUIT BREAKER ACTIVATED - {self.account_risk.consecutive_losses} consecutive losses")
        
        with self._lock:
            self.account_risk.circuit_breaker_active = True
            
            # Close all positions immediately
            for order_id, position in list(self.positions.items()):
                await self._execute_exit_order(position, ExitType.MARKET)
                del self.positions[order_id]
            
            # Log circuit breaker activation
            self.trade_history.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'circuit_breaker_activated',
                'consecutive_losses': self.account_risk.consecutive_losses,
                'daily_pnl': self.account_risk.daily_pnl,
                'reason': 'Maximum consecutive losses exceeded'
            })
    
    async def _calculate_liquidation_price(self, symbol: str, side: str, quantity: float, 
                                         leverage: float, entry_price: float) -> float:
        """Calculate liquidation price for position"""
        try:
            # Get maintenance margin rate
            exchange_info = await self.exchange.futures_exchange_info()
            maintenance_rate = 0.004  # Default 0.4%
            
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    # Use bracket data if available
                    if 'brackets' in symbol_info:
                        maintenance_rate = float(symbol_info['brackets'][0]['maintMarginRatio'])
                    break
            
            # Calculate liquidation price
            if side == 'BUY':
                liquidation_price = entry_price * (1 - 1/leverage + maintenance_rate)
            else:
                liquidation_price = entry_price * (1 + 1/leverage - maintenance_rate)
            
            return liquidation_price
            
        except Exception as e:
            self.logger.error(f"Liquidation price calculation error: {e}")
            # Return conservative estimate
            if side == 'BUY':
                return entry_price * 0.9  # 10% buffer
            else:
                return entry_price * 1.1
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            ticker = await self.exchange.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            self.logger.error(f"Price fetch error for {symbol}: {e}")
            return 0.0
    
    async def _estimate_slippage(self, symbol: str, quantity: float) -> float:
        """Estimate slippage for market order"""
        try:
            # Get order book
            depth = await self.exchange.futures_order_book(symbol=symbol, limit=20)
            
            # Calculate slippage based on order book depth
            bids = [(float(bid[0]), float(bid[1])) for bid in depth['bids']]
            asks = [(float(ask[0]), float(ask[1])) for ask in depth['asks']]
            
            # Simulate market order impact
            remaining_qty = abs(quantity)
            total_cost = 0.0
            prices = asks if quantity > 0 else bids
            
            for price, size in prices:
                if remaining_qty <= 0:
                    break
                
                fill_qty = min(remaining_qty, size)
                total_cost += fill_qty * price
                remaining_qty -= fill_qty
            
            if total_cost > 0 and quantity != 0:
                avg_price = total_cost / abs(quantity)
                mid_price = (bids[0][0] + asks[0][0]) / 2
                slippage_bps = abs(avg_price - mid_price) / mid_price * 10000
                
                # Apply adjustment factor
                slippage_bps *= self.risk_params.slippage_adjustment
                
                # Cache for historical analysis
                if symbol not in self.slippage_history:
                    self.slippage_history[symbol] = []
                self.slippage_history[symbol].append(slippage_bps)
                
                # Keep only recent history
                if len(self.slippage_history[symbol]) > 100:
                    self.slippage_history[symbol] = self.slippage_history[symbol][-50:]
                
                return slippage_bps
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Slippage estimation error: {e}")
            return 5.0  # Conservative estimate
    
    async def _update_funding_rates(self):
        """Update funding rates for all symbols"""
        try:
            funding_rates = await self.exchange.futures_funding_rate()
            
            for rate_info in funding_rates:
                symbol = rate_info['symbol']
                self.funding_rates[symbol] = {
                    'fundingRate': float(rate_info['fundingRate']),
                    'fundingTime': int(rate_info['fundingTime']),
                    'updated': datetime.now()
                }
            
            # Calculate next funding time
            if funding_rates:
                next_funding = max([int(rate['fundingTime']) for rate in funding_rates])
                self.next_funding_time = datetime.fromtimestamp(next_funding / 1000)
            
            self.logger.info(f"Updated funding rates for {len(funding_rates)} symbols")
            
        except Exception as e:
            self.logger.error(f"Funding rate update error: {e}")
    
    async def _check_funding_risk(self, symbol: str, side: str) -> Dict:
        """Check funding rate risk for position"""
        try:
            if symbol not in self.funding_rates:
                return {'risk_level': RiskLevel.LOW, 'message': 'No funding data'}
            
            funding_rate = self.funding_rates[symbol]['fundingRate']
            
            # Calculate cost impact
            if (side == 'BUY' and funding_rate > 0) or (side == 'SELL' and funding_rate < 0):
                # Position will pay funding
                if abs(funding_rate) > self.risk_params.funding_rate_threshold:
                    return {
                        'risk_level': RiskLevel.CRITICAL,
                        'message': f'High funding cost: {funding_rate*100:.3f}%'
                    }
                elif abs(funding_rate) > self.risk_params.funding_rate_threshold * 0.5:
                    return {
                        'risk_level': RiskLevel.HIGH,
                        'message': f'Moderate funding cost: {funding_rate*100:.3f}%'
                    }
            
            return {'risk_level': RiskLevel.LOW, 'message': 'Low funding risk'}
            
        except Exception as e:
            self.logger.error(f"Funding risk check error: {e}")
            return {'risk_level': RiskLevel.MODERATE, 'message': 'Unable to assess funding risk'}
    
    def _calculate_position_risk_level(self, liquidation_distance: float, margin_ratio: float) -> RiskLevel:
        """Calculate overall risk level for position"""
        if liquidation_distance < 0.1 or margin_ratio > 0.9:  # 10% from liquidation or 90% margin
            return RiskLevel.CRITICAL
        elif liquidation_distance < 0.2 or margin_ratio > 0.7:  # 20% from liquidation or 70% margin
            return RiskLevel.HIGH
        elif liquidation_distance < 0.3 or margin_ratio > 0.5:  # 30% from liquidation or 50% margin
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    async def _update_account_risk(self):
        """Update overall account risk metrics"""
        try:
            # Get fresh account data
            account_info = await self.exchange.futures_account()
            
            with self._lock:
                self.account_risk.total_balance = float(account_info['totalWalletBalance'])
                self.account_risk.available_balance = float(account_info['availableBalance'])
                self.account_risk.total_unrealized_pnl = float(account_info['totalUnrealizedProfit'])
                
                # Calculate daily PnL
                current_balance = self.account_risk.total_balance + self.account_risk.total_unrealized_pnl
                self.account_risk.daily_pnl = current_balance - self.daily_stats['start_balance']
                self.daily_stats['total_pnl'] = self.account_risk.daily_pnl
                
                # Update max drawdown
                drawdown = min(0, self.account_risk.daily_pnl)
                self.daily_stats['max_drawdown'] = min(self.daily_stats['max_drawdown'], drawdown)
                
                # Calculate overall risk level
                loss_ratio = abs(self.account_risk.daily_pnl) / self.account_risk.total_balance
                
                if self.account_risk.circuit_breaker_active:
                    self.account_risk.risk_level = RiskLevel.EMERGENCY
                elif loss_ratio > self.risk_params.daily_loss_limit * 0.8:
                    self.account_risk.risk_level = RiskLevel.CRITICAL
                elif loss_ratio > self.risk_params.daily_loss_limit * 0.6:
                    self.account_risk.risk_level = RiskLevel.HIGH
                elif self.account_risk.consecutive_losses > 3:
                    self.account_risk.risk_level = RiskLevel.MODERATE
                else:
                    self.account_risk.risk_level = RiskLevel.LOW
        
        except Exception as e:
            self.logger.error(f"Account risk update error: {e}")
    
    async def _reset_daily_stats(self):
        """Reset daily statistics"""
        try:
            account_info = await self.exchange.futures_account()
            start_balance = float(account_info['totalWalletBalance']) + float(account_info['totalUnrealizedProfit'])
            
            self.daily_stats = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'max_drawdown': 0.0,
                'start_balance': start_balance,
                'last_reset': datetime.now().date()
            }
            
            # Reset circuit breaker if new day
            if self.account_risk:
                self.account_risk.circuit_breaker_active = False
                self.account_risk.consecutive_losses = 0
                self.account_risk.daily_pnl = 0.0
                self.account_risk.daily_trades = 0
            
            self.logger.info(f"Daily stats reset - Starting balance: ${start_balance:.2f}")
            
        except Exception as e:
            self.logger.error(f"Daily stats reset error: {e}")
    
    async def emergency_stop_all(self, reason: str = "Manual emergency stop"):
        """Emergency stop - close all positions immediately"""
        self.logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
        
        with self._lock:
            self._emergency_stop.set()
            
            # Close all positions with market orders
            for order_id, position in list(self.positions.items()):
                try:
                    await self._execute_exit_order(position, ExitType.EMERGENCY)
                    del self.positions[order_id]
                except Exception as e:
                    self.logger.error(f"Emergency exit failed for {position.symbol}: {e}")
            
            # Log emergency stop
            self.trade_history.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'emergency_stop',
                'reason': reason,
                'positions_closed': len(self.positions),
                'daily_pnl': self.account_risk.daily_pnl if self.account_risk else 0
            })
    
    def reset_emergency_stop(self):
        """Reset emergency stop flag"""
        with self._lock:
            self._emergency_stop.clear()
            self.logger.info("Emergency stop reset - trading can resume")
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        try:
            with self._lock:
                return {
                    'account_risk': {
                        'total_balance': self.account_risk.total_balance if self.account_risk else 0,
                        'daily_pnl': self.account_risk.daily_pnl if self.account_risk else 0,
                        'daily_pnl_pct': (self.account_risk.daily_pnl / self.account_risk.total_balance * 100) if self.account_risk and self.account_risk.total_balance > 0 else 0,
                        'risk_level': self.account_risk.risk_level.value if self.account_risk else 'unknown',
                        'circuit_breaker': self.account_risk.circuit_breaker_active if self.account_risk else False,
                        'consecutive_losses': self.account_risk.consecutive_losses if self.account_risk else 0,
                        'emergency_stop': self._emergency_stop.is_set()
                    },
                    'daily_stats': self.daily_stats,
                    'positions': {
                        'count': len(self.positions),
                        'details': [
                            {
                                'symbol': pos.symbol,
                                'side': pos.side,
                                'unrealized_pnl': pos.unrealized_pnl,
                                'risk_level': pos.risk_level.value,
                                'liquidation_price': pos.liquidation_price,
                                'time_held': pos.time_held
                            } for pos in self.positions.values()
                        ]
                    },
                    'next_funding_time': self.next_funding_time.isoformat() if self.next_funding_time else None,
                    'risk_parameters': {
                        'max_leverage': self.risk_params.max_leverage,
                        'daily_loss_limit_pct': self.risk_params.daily_loss_limit * 100,
                        'max_concurrent_positions': self.risk_params.max_concurrent_positions,
                        'max_consecutive_losses': self.risk_params.max_consecutive_losses
                    }
                }
        except Exception as e:
            self.logger.error(f"Risk summary error: {e}")
            return {'error': str(e)}
    
    async def run_risk_monitor(self, interval: int = 1):
        """Run continuous risk monitoring loop"""
        self.logger.info(f"Starting risk monitor with {interval}s interval")
        
        while not self._emergency_stop.is_set():
            try:
                # Update positions
                await self.update_positions()
                
                # Update funding rates every 5 minutes
                if (datetime.now() - self.account_risk.last_funding_check).total_seconds() > 300:
                    await self._update_funding_rates()
                    self.account_risk.last_funding_check = datetime.now()
                
                # Reset daily stats if new day
                if self.daily_stats['last_reset'] != datetime.now().date():
                    await self._reset_daily_stats()
                
                # Log risk status periodically
                if datetime.now().second % 30 == 0:  # Every 30 seconds
                    risk_summary = self.get_risk_summary()
                    self.logger.info(f"Risk Status - PnL: {risk_summary['account_risk']['daily_pnl']:.2f} "
                                   f"({risk_summary['account_risk']['daily_pnl_pct']:.2f}%), "
                                   f"Positions: {risk_summary['positions']['count']}, "
                                   f"Risk Level: {risk_summary['account_risk']['risk_level']}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Risk monitor error: {e}")
                await asyncio.sleep(interval * 2)  # Back off on error
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, '_emergency_stop'):
            self._emergency_stop.set()
