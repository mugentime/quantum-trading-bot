"""
Integration Guide for Scalping Risk Management System

This module provides integration examples and utility functions
for incorporating the scalping risk manager into existing trading systems.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .scalping_risk_manager import ScalpingRiskManager, RiskParameters, RiskLevel
from .risk_dashboard import RiskDashboard

@dataclass
class IntegrationConfig:
    """Configuration for risk management integration"""
    enable_risk_manager: bool = True
    enable_dashboard: bool = True
    enable_telegram_alerts: bool = True
    risk_update_interval: int = 1  # seconds
    dashboard_update_interval: int = 60  # seconds
    auto_position_tracking: bool = True
    emergency_exit_enabled: bool = True
    circuit_breaker_enabled: bool = True

class RiskManagedTradingSystem:
    """
    Example integration of risk management with trading system
    
    This class shows how to integrate the scalping risk manager
    with an existing trading bot or strategy.
    """
    
    def __init__(self, exchange_client, strategy, config: IntegrationConfig = None):
        self.exchange = exchange_client
        self.strategy = strategy
        self.config = config or IntegrationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Risk management components
        self.risk_manager: Optional[ScalpingRiskManager] = None
        self.risk_dashboard: Optional[RiskDashboard] = None
        
        # Trading state
        self.is_trading = False
        self.pending_orders = {}
        
    async def initialize(self, risk_params: RiskParameters = None):
        """Initialize the risk-managed trading system"""
        try:
            if self.config.enable_risk_manager:
                self.risk_manager = ScalpingRiskManager(self.exchange, risk_params)
                await self.risk_manager.initialize()
                self.logger.info("Risk manager initialized")
                
                if self.config.enable_dashboard:
                    self.risk_dashboard = RiskDashboard(self.risk_manager)
                    self.logger.info("Risk dashboard initialized")
            
            # Initialize strategy
            if hasattr(self.strategy, 'initialize'):\n                await self.strategy.initialize()
            
            self.logger.info("Risk-managed trading system ready")
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
    
    async def start_trading(self):
        """Start the risk-managed trading system"""
        try:
            self.is_trading = True
            
            # Start risk monitoring
            risk_monitor_task = None
            dashboard_task = None
            
            if self.risk_manager:
                risk_monitor_task = asyncio.create_task(
                    self.risk_manager.run_risk_monitor(self.config.risk_update_interval)
                )
                
            if self.risk_dashboard:
                dashboard_task = asyncio.create_task(
                    self.risk_dashboard.start_monitoring(self.config.dashboard_update_interval)
                )
            
            # Start main trading loop
            trading_task = asyncio.create_task(self._trading_loop())
            
            # Wait for any task to complete (shouldn't happen in normal operation)
            tasks = [t for t in [risk_monitor_task, dashboard_task, trading_task] if t]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Trading system error: {e}")
            await self.stop_trading()
            raise
    
    async def stop_trading(self):
        """Stop trading and close all positions"""
        self.logger.info("Stopping trading system...")
        
        self.is_trading = False
        
        if self.risk_manager:
            await self.risk_manager.emergency_stop_all("System shutdown")
        
        self.logger.info("Trading system stopped")
    
    async def _trading_loop(self):
        """Main trading loop with risk management integration"""
        while self.is_trading:
            try:
                # Check if trading is allowed
                if not await self._can_trade():
                    await asyncio.sleep(5)
                    continue
                
                # Get trading signal from strategy
                signal = await self._get_trading_signal()
                
                if signal:
                    # Validate trade with risk manager
                    if await self._validate_and_execute_trade(signal):
                        self.logger.info(f"Trade executed: {signal}")
                    else:
                        self.logger.warning(f"Trade rejected by risk manager: {signal}")
                
                # Update existing positions
                await self._monitor_positions()
                
                # Small delay to prevent excessive API calls
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(1)
    
    async def _can_trade(self) -> bool:
        """Check if trading is allowed based on risk conditions"""
        if not self.risk_manager:
            return True
        
        risk_summary = self.risk_manager.get_risk_summary()
        
        # Check emergency conditions
        if risk_summary['account_risk']['emergency_stop']:
            return False
        
        if self.config.circuit_breaker_enabled and risk_summary['account_risk']['circuit_breaker']:
            return False
        
        # Check risk level
        risk_level = risk_summary['account_risk']['risk_level']
        if risk_level == 'critical':
            return False
        
        return True
    
    async def _get_trading_signal(self) -> Optional[Dict]:
        """Get trading signal from strategy"""
        try:
            if hasattr(self.strategy, 'get_signal'):
                return await self.strategy.get_signal()
            return None
        except Exception as e:
            self.logger.error(f"Signal generation error: {e}")
            return None
    
    async def _validate_and_execute_trade(self, signal: Dict) -> bool:
        """Validate trade with risk manager and execute if approved"""
        try:
            if not self.risk_manager:
                # No risk management - execute directly
                return await self._execute_trade(signal)
            
            # Validate with risk manager
            valid, message, risk_metrics = await self.risk_manager.validate_entry(
                symbol=signal['symbol'],
                side=signal['side'],
                quantity=signal['quantity'],
                leverage=signal.get('leverage', 1.0),
                entry_price=signal.get('entry_price')
            )
            
            if not valid:
                self.logger.warning(f"Trade validation failed: {message}")
                return False
            
            # Execute the trade
            order_result = await self._execute_trade(signal)
            
            if order_result:
                # Register position with risk manager
                await self.risk_manager.register_position(
                    symbol=signal['symbol'],
                    side=signal['side'],
                    quantity=signal['quantity'],
                    entry_price=order_result['fill_price'],
                    leverage=signal.get('leverage', 1.0),
                    order_id=str(order_result['order_id'])
                )
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Trade validation/execution error: {e}")
            return False
    
    async def _execute_trade(self, signal: Dict) -> Optional[Dict]:
        """Execute trade order"""
        try:
            # Prepare order parameters
            order_params = {
                'symbol': signal['symbol'],
                'side': signal['side'],
                'type': signal.get('order_type', 'MARKET'),
                'quantity': signal['quantity']
            }
            
            # Add price for limit orders
            if order_params['type'] == 'LIMIT':
                order_params['price'] = signal.get('entry_price')
            
            # Execute order
            order = await self.exchange.futures_create_order(**order_params)
            
            # Return execution details
            return {
                'order_id': order['orderId'],
                'fill_price': float(order.get('avgPrice', signal.get('entry_price', 0))),
                'status': order['status']
            }
            
        except Exception as e:
            self.logger.error(f"Trade execution error: {e}")
            return None
    
    async def _monitor_positions(self):
        """Monitor and update existing positions"""
        try:
            if self.risk_manager and self.config.auto_position_tracking:
                await self.risk_manager.update_positions()
        except Exception as e:
            self.logger.error(f"Position monitoring error: {e}")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'trading_active': self.is_trading,
                'risk_manager_enabled': self.risk_manager is not None,
                'dashboard_enabled': self.risk_dashboard is not None
            }
            
            if self.risk_manager:
                risk_summary = self.risk_manager.get_risk_summary()
                status.update({
                    'risk_status': risk_summary['account_risk'],
                    'position_count': risk_summary['positions']['count'],
                    'daily_stats': risk_summary['daily_stats']
                })
            
            if self.risk_dashboard:
                dashboard_data = self.risk_dashboard.get_dashboard_data()
                status['dashboard_metrics'] = dashboard_data.get('performance_metrics', {})
            
            return status
            
        except Exception as e:
            self.logger.error(f"Status retrieval error: {e}")
            return {'error': str(e)}

class SimpleRiskIntegration:
    """
    Simplified integration example for existing trading bots
    
    This shows minimal changes needed to add risk management
    to an existing trading system.
    """
    
    def __init__(self, exchange_client):
        self.exchange = exchange_client
        self.risk_manager = None
        self.logger = logging.getLogger(__name__)
    
    async def setup_risk_management(self, max_daily_loss_pct: float = 5.0):
        """Quick setup with sensible defaults"""
        try:
            risk_params = RiskParameters(
                max_leverage=10.0,
                daily_loss_limit=max_daily_loss_pct / 100.0,
                max_concurrent_positions=3,
                max_consecutive_losses=5
            )
            
            self.risk_manager = ScalpingRiskManager(self.exchange, risk_params)
            await self.risk_manager.initialize()
            
            self.logger.info(f"Risk management setup complete - Max daily loss: {max_daily_loss_pct}%")
            
        except Exception as e:
            self.logger.error(f"Risk management setup failed: {e}")
            raise
    
    async def safe_trade(self, symbol: str, side: str, quantity: float, 
                        leverage: float = 1.0) -> bool:
        """Execute trade with risk validation"""
        try:
            if not self.risk_manager:
                self.logger.warning("Risk manager not initialized - trading without protection!")
                return await self._direct_trade(symbol, side, quantity)
            
            # Validate trade
            valid, message, _ = await self.risk_manager.validate_entry(
                symbol=symbol, side=side, quantity=quantity, leverage=leverage
            )
            
            if not valid:
                self.logger.warning(f"Trade blocked: {message}")
                return False
            
            # Execute trade
            success = await self._direct_trade(symbol, side, quantity)
            
            if success:
                # Register with risk manager
                current_price = await self._get_current_price(symbol)
                await self.risk_manager.register_position(
                    symbol=symbol, side=side, quantity=quantity,
                    entry_price=current_price, leverage=leverage,
                    order_id=f"trade_{datetime.now().timestamp()}"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Safe trade error: {e}")
            return False
    
    async def _direct_trade(self, symbol: str, side: str, quantity: float) -> bool:
        """Direct trade execution (placeholder)"""
        # Your existing trade execution logic here
        try:
            order = await self.exchange.futures_create_order(
                symbol=symbol, side=side, type='MARKET', quantity=quantity
            )
            return order['status'] == 'FILLED'
        except Exception as e:
            self.logger.error(f"Direct trade error: {e}")
            return False
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current price for position registration"""
        try:
            ticker = await self.exchange.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except:
            return 0.0
    
    def get_risk_status(self) -> str:
        """Get simple risk status"""
        if not self.risk_manager:
            return "NO_RISK_MANAGEMENT"
        
        try:
            summary = self.risk_manager.get_risk_summary()
            return summary['account_risk']['risk_level'].upper()
        except:
            return "UNKNOWN"

# Usage Examples
"""
# Example 1: Full Integration
async def main():
    exchange = BinanceClient()
    strategy = MyScalpingStrategy()
    
    config = IntegrationConfig(
        enable_risk_manager=True,
        enable_dashboard=True,
        risk_update_interval=1,
        dashboard_update_interval=60
    )
    
    trading_system = RiskManagedTradingSystem(exchange, strategy, config)
    await trading_system.initialize()
    await trading_system.start_trading()

# Example 2: Simple Integration
async def simple_example():
    exchange = BinanceClient()
    
    risk_integration = SimpleRiskIntegration(exchange)
    await risk_integration.setup_risk_management(max_daily_loss_pct=3.0)
    
    # Your existing trading logic with risk protection
    success = await risk_integration.safe_trade(
        symbol='BTCUSDT', side='BUY', quantity=0.1, leverage=5.0
    )
    
    if success:
        print("Trade executed successfully")
    else:
        print("Trade blocked by risk management")
    
    print(f"Risk Status: {risk_integration.get_risk_status()}")

# Example 3: Minimal Changes to Existing Bot
class ExistingBot:
    def __init__(self):
        self.exchange = BinanceClient()
        self.risk = SimpleRiskIntegration(self.exchange)
    
    async def setup(self):
        await self.risk.setup_risk_management()
    
    async def trade_logic(self):
        # Replace direct trades with safe_trade calls
        if some_condition:
            await self.risk.safe_trade('BTCUSDT', 'BUY', 0.1, 5.0)
"""