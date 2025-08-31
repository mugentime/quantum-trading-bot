"""
Comprehensive test suite for ScalpingRiskManager

Tests all critical risk management functions including:
- Liquidation prevention
- Position sizing
- Emergency exits
- Circuit breakers
- Funding rate optimization
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.risk_management.scalping_risk_manager import (
    ScalpingRiskManager, RiskParameters, RiskLevel, ExitType,
    PositionRisk, AccountRisk
)

class MockExchange:
    """Mock exchange client for testing"""
    
    def __init__(self):
        self.account_balance = 10000.0
        self.available_balance = 8000.0
        self.unrealized_pnl = 0.0
        self.positions = []
        self.orders = []
        self.prices = {'BTCUSDT': 50000.0, 'ETHUSDT': 3000.0}
        self.funding_rates = {}
    
    async def futures_account(self):
        return {
            'totalWalletBalance': str(self.account_balance),
            'availableBalance': str(self.available_balance),
            'totalUnrealizedProfit': str(self.unrealized_pnl)
        }
    
    async def futures_position_information(self):
        return self.positions
    
    async def futures_symbol_ticker(self, symbol):
        return {'price': str(self.prices.get(symbol, 50000.0))}
    
    async def futures_exchange_info(self):
        return {
            'symbols': [
                {
                    'symbol': 'BTCUSDT',
                    'brackets': [{'maintMarginRatio': '0.004'}]
                }
            ]
        }
    
    async def futures_order_book(self, symbol, limit=20):
        price = self.prices.get(symbol, 50000.0)
        spread = price * 0.0001  # 1 bps spread
        
        return {
            'bids': [[str(price - spread), '1.0']] * 10,
            'asks': [[str(price + spread), '1.0']] * 10
        }
    
    async def futures_funding_rate(self):
        return [
            {
                'symbol': 'BTCUSDT',
                'fundingRate': '0.0001',
                'fundingTime': int((datetime.now() + timedelta(hours=1)).timestamp() * 1000)
            }
        ]
    
    async def futures_create_order(self, **kwargs):
        order = {
            'orderId': len(self.orders) + 1,
            'symbol': kwargs['symbol'],
            'side': kwargs['side'],
            'type': kwargs['type'],
            'quantity': kwargs['quantity'],
            'status': 'FILLED'
        }
        self.orders.append(order)
        return order

@pytest.fixture
def risk_params():
    """Standard risk parameters for testing"""
    return RiskParameters(
        max_leverage=10.0,
        liquidation_buffer=0.15,
        max_position_size_usd=5000.0,
        position_size_percent=0.02,
        daily_loss_limit=0.05,
        max_consecutive_losses=3
    )

@pytest.fixture
def mock_exchange():
    """Mock exchange client"""
    return MockExchange()

@pytest.fixture
async def risk_manager(mock_exchange, risk_params):
    """Initialized risk manager"""
    manager = ScalpingRiskManager(mock_exchange, risk_params)
    await manager.initialize()
    return manager

@pytest.mark.asyncio
async def test_initialization(mock_exchange, risk_params):
    """Test risk manager initialization"""
    manager = ScalpingRiskManager(mock_exchange, risk_params)
    await manager.initialize()
    
    assert manager.account_risk is not None
    assert manager.account_risk.total_balance == 10000.0
    assert manager.account_risk.available_balance == 8000.0
    assert len(manager.funding_rates) > 0

@pytest.mark.asyncio
async def test_validate_entry_success(risk_manager):
    """Test successful entry validation"""
    valid, message, metrics = await risk_manager.validate_entry(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        leverage=5.0,
        entry_price=50000.0
    )
    
    assert valid == True
    assert "Entry validated" in message
    assert 'liquidation_price' in metrics
    assert 'expected_slippage' in metrics
    assert metrics['liquidation_distance'] > risk_manager.risk_params.liquidation_buffer

@pytest.mark.asyncio
async def test_validate_entry_high_leverage(risk_manager):
    """Test entry validation with excessive leverage"""
    valid, message, metrics = await risk_manager.validate_entry(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        leverage=15.0,  # Exceeds max of 10x
        entry_price=50000.0
    )
    
    assert valid == False
    assert "exceeds maximum" in message

@pytest.mark.asyncio
async def test_validate_entry_position_size_limit(risk_manager):
    """Test entry validation with excessive position size"""
    valid, message, metrics = await risk_manager.validate_entry(
        symbol='BTCUSDT',
        side='BUY',
        quantity=2.0,  # Large position
        leverage=10.0,
        entry_price=50000.0
    )
    
    assert valid == False
    assert "Position size" in message
    assert "exceeds maximum" in message

@pytest.mark.asyncio
async def test_validate_entry_daily_loss_limit(risk_manager):
    """Test entry validation when daily loss limit is reached"""
    # Set daily loss to limit
    risk_manager.account_risk.daily_pnl = -500.0  # 5% of 10k balance
    
    valid, message, metrics = await risk_manager.validate_entry(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        leverage=5.0,
        entry_price=50000.0
    )
    
    assert valid == False
    assert "Daily loss limit reached" in message

@pytest.mark.asyncio
async def test_validate_entry_max_positions(risk_manager):
    """Test entry validation when max concurrent positions reached"""
    # Add mock positions to reach limit
    for i in range(risk_manager.risk_params.max_concurrent_positions):
        risk_manager.positions[f"order_{i}"] = PositionRisk(
            symbol='BTCUSDT',
            side='BUY',
            entry_price=50000.0,
            quantity=0.1,
            leverage=5.0,
            unrealized_pnl=0.0,
            liquidation_price=40000.0,
            margin_ratio=0.2,
            time_held=0,
            risk_level=RiskLevel.LOW
        )
    
    valid, message, metrics = await risk_manager.validate_entry(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        leverage=5.0,
        entry_price=50000.0
    )
    
    assert valid == False
    assert "Maximum concurrent positions" in message

@pytest.mark.asyncio
async def test_liquidation_price_calculation(risk_manager):
    """Test liquidation price calculation accuracy"""
    liquidation_price = await risk_manager._calculate_liquidation_price(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        leverage=10.0,
        entry_price=50000.0
    )
    
    # For 10x leverage long, liquidation should be around 90% of entry
    expected_range = (50000.0 * 0.85, 50000.0 * 0.95)
    assert expected_range[0] <= liquidation_price <= expected_range[1]

@pytest.mark.asyncio
async def test_register_position(risk_manager):
    """Test position registration"""
    await risk_manager.register_position(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        entry_price=50000.0,
        leverage=5.0,
        order_id='test_order_1'
    )
    
    assert 'test_order_1' in risk_manager.positions
    position = risk_manager.positions['test_order_1']
    assert position.symbol == 'BTCUSDT'
    assert position.side == 'BUY'
    assert position.quantity == 0.1
    assert risk_manager.daily_stats['trades'] == 1

@pytest.mark.asyncio
async def test_emergency_exit_liquidation_risk(risk_manager):
    """Test emergency exit for liquidation risk"""
    # Register a position
    await risk_manager.register_position(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        entry_price=50000.0,
        leverage=10.0,
        order_id='test_order_1'
    )
    
    position = risk_manager.positions['test_order_1']
    position.liquidation_price = 49500.0  # Very close to current price
    position.exit_reasons = ['Liquidation risk: 1.0% from liquidation']
    
    # Mock the exit execution
    with patch.object(risk_manager, '_execute_exit_order', new_callable=AsyncMock) as mock_exit:
        await risk_manager._execute_emergency_exit('test_order_1', position)
        
        # Should have called exit order
        mock_exit.assert_called_once()
        args = mock_exit.call_args[0]
        assert args[0] == position
        assert args[1] == ExitType.MARKET  # Market order for liquidation risk

@pytest.mark.asyncio
async def test_circuit_breaker_activation(risk_manager):
    """Test circuit breaker activation on consecutive losses"""
    # Set consecutive losses to trigger threshold
    risk_manager.account_risk.consecutive_losses = risk_manager.risk_params.max_consecutive_losses
    
    # Add a position
    await risk_manager.register_position(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.1,
        entry_price=50000.0,
        leverage=5.0,
        order_id='test_order_1'
    )
    
    position = risk_manager.positions['test_order_1']
    position.unrealized_pnl = -100.0  # Losing position
    
    with patch.object(risk_manager, '_execute_exit_order', new_callable=AsyncMock):
        await risk_manager._execute_emergency_exit('test_order_1', position)
    
    # Circuit breaker should be active
    assert risk_manager.account_risk.circuit_breaker_active == True
    assert len(risk_manager.positions) == 0  # All positions closed

@pytest.mark.asyncio
async def test_funding_rate_risk_assessment(risk_manager):
    """Test funding rate risk assessment"""
    # Set high funding rate
    risk_manager.funding_rates['BTCUSDT'] = {
        'fundingRate': 0.015,  # 1.5% - very high
        'fundingTime': int((datetime.now() + timedelta(hours=1)).timestamp() * 1000),
        'updated': datetime.now()
    }
    
    # Test long position with positive funding (will pay)
    funding_risk = await risk_manager._check_funding_risk('BTCUSDT', 'BUY')
    
    assert funding_risk['risk_level'] == RiskLevel.CRITICAL
    assert 'High funding cost' in funding_risk['message']

@pytest.mark.asyncio
async def test_slippage_estimation(risk_manager):
    """Test slippage estimation accuracy"""
    slippage = await risk_manager._estimate_slippage('BTCUSDT', 0.1)
    
    # Should be reasonable for small position
    assert 0 <= slippage <= 10.0  # Max 10 bps for small order
    
    # Test large position
    large_slippage = await risk_manager._estimate_slippage('BTCUSDT', 10.0)
    assert large_slippage > slippage  # Larger positions should have more slippage

@pytest.mark.asyncio
async def test_position_risk_level_calculation(risk_manager):
    """Test position risk level calculation"""
    # Test low risk
    risk_level = risk_manager._calculate_position_risk_level(
        liquidation_distance=0.5,  # 50% from liquidation
        margin_ratio=0.2  # 20% margin used
    )
    assert risk_level == RiskLevel.LOW
    
    # Test high risk
    risk_level = risk_manager._calculate_position_risk_level(
        liquidation_distance=0.15,  # 15% from liquidation
        margin_ratio=0.8  # 80% margin used
    )
    assert risk_level == RiskLevel.HIGH
    
    # Test critical risk
    risk_level = risk_manager._calculate_position_risk_level(
        liquidation_distance=0.05,  # 5% from liquidation
        margin_ratio=0.95  # 95% margin used
    )
    assert risk_level == RiskLevel.CRITICAL

@pytest.mark.asyncio
async def test_emergency_stop_functionality(risk_manager):
    """Test emergency stop functionality"""
    # Add positions
    await risk_manager.register_position(
        symbol='BTCUSDT', side='BUY', quantity=0.1, entry_price=50000.0,
        leverage=5.0, order_id='test_order_1'
    )
    await risk_manager.register_position(
        symbol='ETHUSDT', side='SELL', quantity=1.0, entry_price=3000.0,
        leverage=3.0, order_id='test_order_2'
    )
    
    assert len(risk_manager.positions) == 2
    
    # Trigger emergency stop
    with patch.object(risk_manager, '_execute_exit_order', new_callable=AsyncMock):
        await risk_manager.emergency_stop_all("Test emergency")
    
    # All positions should be closed
    assert len(risk_manager.positions) == 0
    assert risk_manager._emergency_stop.is_set()

@pytest.mark.asyncio
async def test_daily_stats_reset(risk_manager):
    """Test daily statistics reset"""
    # Set some stats
    risk_manager.daily_stats['trades'] = 10
    risk_manager.daily_stats['wins'] = 6
    risk_manager.daily_stats['losses'] = 4
    risk_manager.daily_stats['total_pnl'] = 100.0
    
    # Reset
    await risk_manager._reset_daily_stats()
    
    assert risk_manager.daily_stats['trades'] == 0
    assert risk_manager.daily_stats['wins'] == 0
    assert risk_manager.daily_stats['losses'] == 0
    assert risk_manager.daily_stats['total_pnl'] == 0.0
    assert risk_manager.daily_stats['start_balance'] > 0

@pytest.mark.asyncio
async def test_risk_summary_generation(risk_manager):
    """Test comprehensive risk summary generation"""
    # Add a position
    await risk_manager.register_position(
        symbol='BTCUSDT', side='BUY', quantity=0.1, entry_price=50000.0,
        leverage=5.0, order_id='test_order_1'
    )
    
    summary = risk_manager.get_risk_summary()
    
    # Verify structure
    assert 'account_risk' in summary
    assert 'daily_stats' in summary
    assert 'positions' in summary
    assert 'risk_parameters' in summary
    
    # Verify content
    assert summary['positions']['count'] == 1
    assert summary['account_risk']['total_balance'] == 10000.0
    assert len(summary['positions']['details']) == 1

@pytest.mark.asyncio
async def test_position_update_and_monitoring(risk_manager, mock_exchange):
    """Test position monitoring and updates"""
    # Add a position
    await risk_manager.register_position(
        symbol='BTCUSDT', side='BUY', quantity=0.1, entry_price=50000.0,
        leverage=5.0, order_id='test_order_1'
    )
    
    # Mock exchange position data
    mock_exchange.positions = [{
        'symbol': 'BTCUSDT',
        'unRealizedProfit': '100.0',
        'marginRatio': '0.3',
        'markPrice': '51000.0'
    }]
    
    # Update positions
    await risk_manager.update_positions()
    
    position = risk_manager.positions['test_order_1']
    assert position.unrealized_pnl == 100.0
    assert position.margin_ratio == 0.3

@pytest.mark.asyncio
async def test_funding_time_exit_trigger(risk_manager):
    """Test exit trigger for funding time approach"""
    # Set funding time very soon
    risk_manager.next_funding_time = datetime.now() + timedelta(minutes=2)
    risk_manager.funding_rates['BTCUSDT'] = {
        'fundingRate': 0.02,  # 2% - high funding rate
        'fundingTime': int(risk_manager.next_funding_time.timestamp() * 1000),
        'updated': datetime.now()
    }
    
    position = PositionRisk(
        symbol='BTCUSDT',
        side='BUY',
        entry_price=50000.0,
        quantity=0.1,
        leverage=5.0,
        unrealized_pnl=50.0,
        liquidation_price=40000.0,
        margin_ratio=0.2,
        time_held=120,
        risk_level=RiskLevel.LOW
    )
    
    exit_reasons = await risk_manager._check_exit_triggers(position, 51000.0)
    
    # Should trigger funding rate exit
    funding_triggered = any('funding rate' in reason.lower() for reason in exit_reasons)
    assert funding_triggered

@pytest.mark.asyncio
async def test_performance_metrics_edge_cases(risk_manager):
    """Test edge cases in risk calculations"""
    # Test with zero balance
    risk_manager.account_risk.total_balance = 0.0
    
    valid, message, metrics = await risk_manager.validate_entry(
        symbol='BTCUSDT', side='BUY', quantity=0.1, leverage=5.0, entry_price=50000.0
    )
    
    # Should handle gracefully
    assert isinstance(valid, bool)
    
    # Test with negative daily PnL
    risk_manager.account_risk.daily_pnl = -1000.0
    risk_manager.account_risk.total_balance = 10000.0
    
    summary = risk_manager.get_risk_summary()
    assert summary['account_risk']['daily_pnl_pct'] == -10.0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])