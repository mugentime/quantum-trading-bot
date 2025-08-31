"""
Scalping Backtest Engine
High-frequency backtesting for correlation-based scalping signals
Tests 1-5 minute timeframes with realistic market microstructure simulation
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import deque, defaultdict
import json
from pathlib import Path
import ccxt.async_support as ccxt

from .scalping_correlation_engine import (
    ScalpingCorrelationEngine, ScalpingSignal, MarketRegime, 
    SignalQuality, OrderBookSnapshot, VolumeAnalysis
)

logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    """Individual backtest trade record"""
    signal_id: str
    symbol: str
    signal_type: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None  # 'take_profit', 'stop_loss', 'timeout', 'manual'
    
    # Trade metrics
    pnl_pct: Optional[float] = None
    pnl_usd: Optional[float] = None
    hold_time_minutes: Optional[int] = None
    slippage_cost: float = 0.0
    commission_cost: float = 0.0
    
    # Signal metadata
    original_confidence: float = 0.0
    quality: SignalQuality = SignalQuality.LOW
    market_regime: MarketRegime = MarketRegime.CALM
    correlation_strength: float = 0.0
    timeframe: str = '1m'
    
    # Market conditions at entry
    spread_at_entry: float = 0.0
    volume_surge_factor: float = 1.0
    order_book_imbalance: float = 1.0
    
    def close_trade(self, exit_time: datetime, exit_price: float, exit_reason: str):
        """Close the trade and calculate metrics"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        
        # Calculate PnL
        if self.signal_type == 'long':
            self.pnl_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # short
            self.pnl_pct = (self.entry_price - exit_price) / self.entry_price
        
        # Calculate hold time
        self.hold_time_minutes = int((exit_time - self.entry_time).total_seconds() / 60)

@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics"""
    # Basic metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # PnL metrics
    total_pnl_pct: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    max_win_pct: float = 0.0
    max_loss_pct: float = 0.0
    profit_factor: float = 0.0  # Gross profit / Gross loss
    
    # Risk metrics
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0
    volatility_pct: float = 0.0
    
    # Time-based metrics
    avg_hold_time_minutes: float = 0.0
    max_hold_time_minutes: int = 0
    trades_per_day: float = 0.0
    
    # Quality metrics
    premium_signal_win_rate: float = 0.0
    high_signal_win_rate: float = 0.0
    medium_signal_win_rate: float = 0.0
    low_signal_win_rate: float = 0.0
    
    # Regime performance
    volatile_regime_pnl: float = 0.0
    calm_regime_pnl: float = 0.0
    breakdown_regime_pnl: float = 0.0
    transitional_regime_pnl: float = 0.0
    
    # Timeframe performance
    tf_1m_win_rate: float = 0.0
    tf_3m_win_rate: float = 0.0
    tf_5m_win_rate: float = 0.0
    
    # Cost analysis
    total_slippage_cost: float = 0.0
    total_commission_cost: float = 0.0
    cost_adjusted_pnl: float = 0.0

class ScalpingBacktestEngine:
    """High-frequency backtesting engine for scalping strategies"""
    
    def __init__(self, exchange_instance):
        self.exchange = exchange_instance
        
        # Backtest configuration
        self.commission_rate = 0.001  # 0.1% commission (maker/taker average)
        self.base_slippage = 0.0005   # 0.05% base slippage
        self.max_position_size = 10000  # Max position size in USD
        
        # Market microstructure simulation
        self.simulate_spreads = True
        self.simulate_slippage = True
        self.simulate_partial_fills = True
        
        # Storage
        self.trades_history: List[BacktestTrade] = []
        self.daily_metrics: Dict[str, Dict] = {}
        self.equity_curve: List[Dict] = []
        
        # Scalping engine for signal generation
        self.scalping_engine = None
        
        logger.info("ScalpingBacktestEngine initialized")
    
    def setup_scalping_engine(self) -> ScalpingCorrelationEngine:
        """Setup the scalping correlation engine for backtesting"""
        if not self.scalping_engine:
            self.scalping_engine = ScalpingCorrelationEngine(self.exchange)
        return self.scalping_engine
    
    async def load_historical_data(self, symbols: List[str], timeframe: str, 
                                  start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """Load historical OHLCV data for backtesting"""
        try:
            logger.info(f"Loading historical data for {len(symbols)} symbols from {start_date} to {end_date}")
            
            historical_data = {}
            
            for symbol in symbols:
                try:
                    # Calculate required data points
                    time_delta = end_date - start_date
                    if timeframe == '1m':
                        limit = min(int(time_delta.total_seconds() / 60), 1500)
                    elif timeframe == '3m':
                        limit = min(int(time_delta.total_seconds() / 180), 1500)
                    elif timeframe == '5m':
                        limit = min(int(time_delta.total_seconds() / 300), 1500)
                    else:
                        limit = 1000
                    
                    # Fetch OHLCV data
                    ohlcv = await self.exchange.fetch_ohlcv(
                        symbol, timeframe, limit=limit
                    )
                    
                    if len(ohlcv) > 0:
                        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('datetime', inplace=True)
                        
                        # Filter by date range
                        df = df[(df.index >= start_date) & (df.index <= end_date)]
                        historical_data[symbol] = df
                        
                        logger.info(f"Loaded {len(df)} data points for {symbol}")
                    
                except Exception as e:
                    logger.warning(f"Failed to load data for {symbol}: {e}")
                    continue
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return {}
    
    def simulate_order_book_conditions(self, symbol: str, current_price: float, 
                                     volume: float, volatility: float) -> OrderBookSnapshot:
        """Simulate realistic order book conditions"""
        try:
            # Simulate spread based on volatility and volume
            base_spread_pct = 0.01  # 1 basis point base spread
            volatility_spread = volatility * 50  # Higher volatility = wider spread
            volume_spread = max(0.001, 1.0 / (volume / 1000000 + 1))  # Lower volume = wider spread
            
            spread_pct = base_spread_pct + volatility_spread + volume_spread
            spread_pct = min(spread_pct, 0.1)  # Cap at 10 basis points
            
            spread_amount = current_price * spread_pct / 100
            best_bid = current_price - spread_amount / 2
            best_ask = current_price + spread_amount / 2
            
            # Simulate depth (random but realistic)
            base_depth = volume / 100  # Rough approximation
            bid_depth_5 = base_depth * np.random.uniform(0.8, 1.2)
            ask_depth_5 = base_depth * np.random.uniform(0.8, 1.2)
            
            # Simulate imbalance
            imbalance_ratio = bid_depth_5 / (ask_depth_5 + 0.001)
            
            return OrderBookSnapshot(
                symbol=symbol,
                best_bid=best_bid,
                best_ask=best_ask,
                bid_ask_spread_pct=spread_pct,
                bid_depth_5=bid_depth_5,
                ask_depth_5=ask_depth_5,
                imbalance_ratio=imbalance_ratio,
                spread_volatility=volatility * 10,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error simulating order book for {symbol}: {e}")
            return OrderBookSnapshot(symbol, current_price, current_price, 0.01, 1000, 1000, 1.0, 0.1, datetime.now())
    
    def simulate_volume_analysis(self, symbol: str, volumes: List[float]) -> VolumeAnalysis:
        """Simulate volume analysis from historical volume data"""
        try:
            if len(volumes) < 5:
                return VolumeAnalysis(symbol, 0, 0, 1.0, 0, 0, 0, 0.5, datetime.now())
            
            current_volume = volumes[-1]
            avg_volume_1m = np.mean(volumes[-5:])
            historical_avg = np.mean(volumes[:-5]) if len(volumes) > 5 else avg_volume_1m
            
            volume_surge_ratio = current_volume / (historical_avg + 0.001)
            
            # Volume trend
            if len(volumes) >= 5:
                volume_trend_5m = (volumes[-1] - volumes[-5]) / volumes[-5]
            else:
                volume_trend_5m = 0.0
            
            # Institutional vs retail estimation
            volume_std = np.std(volumes)
            institutional_threshold = historical_avg + 2 * volume_std
            institutional_flow = 1.0 if current_volume > institutional_threshold else 0.0
            retail_flow = 1.0 - institutional_flow
            
            # Volume profile score
            volume_consistency = 1.0 - min(volume_std / (historical_avg + 0.001), 1.0)
            volume_strength = min(volume_surge_ratio / 2.0, 1.0)
            volume_profile_score = (volume_consistency + volume_strength) / 2.0
            
            return VolumeAnalysis(
                symbol=symbol,
                current_volume=current_volume,
                avg_volume_1m=avg_volume_1m,
                volume_surge_ratio=volume_surge_ratio,
                volume_trend_5m=volume_trend_5m,
                institutional_flow=institutional_flow,
                retail_flow=retail_flow,
                volume_profile_score=volume_profile_score,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error simulating volume analysis: {e}")
            return VolumeAnalysis(symbol, 0, 0, 1.0, 0, 0, 0, 0.5, datetime.now())
    
    def calculate_execution_price(self, signal: ScalpingSignal, order_book: OrderBookSnapshot) -> Tuple[float, float]:
        """Calculate realistic execution price including slippage"""
        try:
            if signal.signal_type == 'long':
                base_price = order_book.best_ask
            else:
                base_price = order_book.best_bid
            
            # Calculate slippage based on market conditions
            spread_slippage = order_book.bid_ask_spread_pct / 100 / 4  # Quarter of spread
            
            # Volume-based slippage
            volume_slippage = self.base_slippage
            if signal.volume_surge_factor < 1.2:  # Low volume
                volume_slippage *= 1.5
            elif signal.volume_surge_factor > 2.0:  # High volume
                volume_slippage *= 0.8
            
            # Urgency slippage
            urgency_slippage = signal.urgency_score * 0.0002  # High urgency = more slippage
            
            total_slippage = spread_slippage + volume_slippage + urgency_slippage
            
            # Apply slippage
            if signal.signal_type == 'long':
                execution_price = base_price * (1 + total_slippage)
            else:
                execution_price = base_price * (1 - total_slippage)
            
            slippage_cost = abs(execution_price - base_price) / base_price
            
            return execution_price, slippage_cost
            
        except Exception as e:
            logger.error(f"Error calculating execution price: {e}")
            return signal.entry_price, 0.0
    
    def simulate_trade_execution(self, signal: ScalpingSignal, market_data: pd.DataFrame, 
                               current_idx: int) -> Optional[BacktestTrade]:
        """Simulate realistic trade execution"""
        try:
            current_row = market_data.iloc[current_idx]
            
            # Simulate order book
            recent_volumes = market_data['volume'].iloc[max(0, current_idx-10):current_idx+1].values
            recent_returns = market_data['close'].pct_change().iloc[max(0, current_idx-10):current_idx+1].values
            volatility = np.std(recent_returns[~np.isnan(recent_returns)])
            
            order_book = self.simulate_order_book_conditions(
                signal.symbol, current_row['close'], current_row['volume'], volatility
            )
            
            # Check if spread is acceptable
            if order_book.bid_ask_spread_pct > signal.bid_ask_spread * 2:
                return None  # Skip trade due to wide spread
            
            # Calculate execution price
            execution_price, slippage_cost = self.calculate_execution_price(signal, order_book)
            
            # Create trade
            trade = BacktestTrade(
                signal_id=signal.id,
                symbol=signal.symbol,
                signal_type=signal.signal_type,
                entry_time=market_data.index[current_idx],
                entry_price=execution_price,
                original_confidence=signal.confidence,
                quality=signal.quality,
                market_regime=signal.market_regime,
                correlation_strength=signal.correlation_strength,
                timeframe=signal.timeframe,
                spread_at_entry=order_book.bid_ask_spread_pct,
                volume_surge_factor=signal.volume_surge_factor,
                order_book_imbalance=order_book.imbalance_ratio,
                slippage_cost=slippage_cost,
                commission_cost=self.commission_rate
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"Error simulating trade execution: {e}")
            return None
    
    def check_exit_conditions(self, trade: BacktestTrade, current_row: pd.Series, 
                            signal: ScalpingSignal, minutes_held: int) -> Tuple[bool, str, float]:
        """Check if trade should be exited"""
        try:
            current_price = current_row['close']
            
            # Check stop loss
            if signal.signal_type == 'long':
                if current_price <= signal.stop_loss:
                    return True, 'stop_loss', signal.stop_loss
            else:  # short
                if current_price >= signal.stop_loss:
                    return True, 'stop_loss', signal.stop_loss
            
            # Check take profit
            if signal.signal_type == 'long':
                if current_price >= signal.take_profit:
                    return True, 'take_profit', signal.take_profit
            else:  # short
                if current_price <= signal.take_profit:
                    return True, 'take_profit', signal.take_profit
            
            # Check timeout
            if minutes_held >= signal.max_hold_minutes:
                return True, 'timeout', current_price
            
            return False, '', 0.0
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
            return True, 'error', current_price
    
    async def run_backtest(self, start_date: datetime, end_date: datetime, 
                          initial_capital: float = 10000.0) -> BacktestMetrics:
        """Run comprehensive backtest"""
        try:
            logger.info(f"Starting backtest from {start_date} to {end_date}")
            
            # Setup scalping engine
            engine = self.setup_scalping_engine()
            
            # Load historical data
            all_symbols = engine.scalping_pairs + engine.reference_pairs
            historical_data = {}
            
            for timeframe in engine.timeframes:
                tf_data = await self.load_historical_data(all_symbols, timeframe, start_date, end_date)
                historical_data[timeframe] = tf_data
            
            if not historical_data:
                raise ValueError("No historical data loaded")
            
            # Initialize tracking variables
            current_capital = initial_capital
            equity_history = []
            open_trades = {}
            
            # Get primary timeframe data for iteration
            primary_tf = '1m'
            primary_symbol = engine.scalping_pairs[0]  # Use first scalping pair as reference
            
            if primary_tf not in historical_data or primary_symbol not in historical_data[primary_tf]:
                raise ValueError(f"No data for primary timeframe {primary_tf} and symbol {primary_symbol}")
            
            primary_data = historical_data[primary_tf][primary_symbol]
            
            # Backtest main loop
            logger.info(f"Running backtest on {len(primary_data)} data points")
            
            for idx in range(engine.correlation_lookback, len(primary_data)):
                current_time = primary_data.index[idx]
                
                # Update engine buffers with historical data
                await self.update_engine_buffers(engine, historical_data, idx)
                
                # Generate signals (every few minutes to avoid over-trading)
                if idx % 3 == 0:  # Every 3 minutes
                    try:
                        signals = await engine.generate_scalping_signals()
                        
                        # Execute new signals
                        for signal in signals[:5]:  # Limit to top 5 signals
                            if signal.symbol in historical_data[primary_tf]:
                                market_data = historical_data[primary_tf][signal.symbol]
                                
                                # Find closest timestamp
                                closest_idx = self.find_closest_timestamp_index(market_data, current_time)
                                
                                if closest_idx is not None:
                                    trade = self.simulate_trade_execution(signal, market_data, closest_idx)
                                    
                                    if trade:
                                        # Calculate position size
                                        position_value = min(
                                            current_capital * signal.position_size_pct,
                                            self.max_position_size
                                        )
                                        trade.pnl_usd = position_value  # Store position size
                                        
                                        open_trades[trade.signal_id] = trade
                                        
                                        logger.debug(f"Opened trade: {trade.symbol} {trade.signal_type} @ {trade.entry_price}")
                    
                    except Exception as e:
                        logger.warning(f"Error generating signals at {current_time}: {e}")
                        continue
                
                # Check exit conditions for open trades
                trades_to_close = []
                
                for trade_id, trade in open_trades.items():
                    if trade.symbol in historical_data[primary_tf]:
                        market_data = historical_data[primary_tf][trade.symbol]
                        closest_idx = self.find_closest_timestamp_index(market_data, current_time)
                        
                        if closest_idx is not None:
                            current_row = market_data.iloc[closest_idx]
                            minutes_held = int((current_time - trade.entry_time).total_seconds() / 60)
                            
                            # Find original signal for exit parameters
                            original_signal = None
                            for signal in engine.active_signals.values():
                                if signal.id == trade.signal_id:
                                    original_signal = signal
                                    break
                            
                            if original_signal:
                                should_exit, exit_reason, exit_price = self.check_exit_conditions(
                                    trade, current_row, original_signal, minutes_held
                                )
                                
                                if should_exit:
                                    trade.close_trade(current_time, exit_price, exit_reason)
                                    
                                    # Calculate realized PnL
                                    realized_pnl_usd = trade.pnl_usd * trade.pnl_pct
                                    realized_pnl_usd -= trade.pnl_usd * (trade.slippage_cost + trade.commission_cost)
                                    
                                    current_capital += realized_pnl_usd
                                    
                                    trades_to_close.append(trade_id)
                                    self.trades_history.append(trade)
                                    
                                    logger.debug(f"Closed trade: {trade.symbol} {trade.exit_reason} "
                                               f"PnL: {trade.pnl_pct:.3%} ({realized_pnl_usd:.2f} USD)")
                
                # Remove closed trades
                for trade_id in trades_to_close:
                    if trade_id in open_trades:
                        del open_trades[trade_id]
                
                # Record equity curve
                if idx % 60 == 0:  # Every hour
                    equity_history.append({
                        'timestamp': current_time,
                        'equity': current_capital,
                        'open_trades': len(open_trades),
                        'total_trades': len(self.trades_history)
                    })
            
            # Close any remaining open trades
            final_time = primary_data.index[-1]
            for trade in open_trades.values():
                if trade.symbol in historical_data[primary_tf]:
                    market_data = historical_data[primary_tf][trade.symbol]
                    final_price = market_data.iloc[-1]['close']
                    trade.close_trade(final_time, final_price, 'backtest_end')
                    
                    # Calculate final PnL
                    realized_pnl_usd = trade.pnl_usd * trade.pnl_pct
                    current_capital += realized_pnl_usd
                    
                    self.trades_history.append(trade)
            
            # Calculate comprehensive metrics
            metrics = self.calculate_backtest_metrics(initial_capital, current_capital, equity_history)
            
            logger.info(f"Backtest completed: {metrics.total_trades} trades, "
                       f"{metrics.win_rate:.1%} win rate, {metrics.total_pnl_pct:.2%} return")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return BacktestMetrics()
    
    async def update_engine_buffers(self, engine: ScalpingCorrelationEngine, 
                                  historical_data: Dict, current_idx: int):
        """Update engine buffers with historical data"""
        try:
            for timeframe in engine.timeframes:
                if timeframe not in historical_data:
                    continue
                
                for symbol, data in historical_data[timeframe].items():
                    if current_idx < len(data):
                        current_row = data.iloc[current_idx]
                        
                        # Update price and volume buffers
                        engine.price_buffers[timeframe][symbol].append(current_row['close'])
                        engine.volume_buffers[timeframe][symbol].append(current_row['volume'])
                        
                        # Update tick buffer for 1m
                        if timeframe == '1m':
                            engine.tick_buffers[symbol].append(current_row['close'])
            
            # Update correlation matrices
            for timeframe in engine.timeframes:
                await engine.update_correlation_matrix(timeframe)
            
            # Update market regime
            await engine.detect_market_regime()
            
        except Exception as e:
            logger.error(f"Error updating engine buffers: {e}")
    
    def find_closest_timestamp_index(self, data: pd.DataFrame, target_time: pd.Timestamp) -> Optional[int]:
        """Find the closest timestamp index in the data"""
        try:
            if target_time in data.index:
                return data.index.get_loc(target_time)
            
            # Find closest timestamp
            time_diff = abs(data.index - target_time)
            closest_idx = time_diff.argmin()
            
            # Only return if within reasonable tolerance (5 minutes)
            if time_diff.iloc[closest_idx] <= pd.Timedelta(minutes=5):
                return closest_idx
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding closest timestamp: {e}")
            return None
    
    def calculate_backtest_metrics(self, initial_capital: float, final_capital: float, 
                                 equity_history: List[Dict]) -> BacktestMetrics:
        """Calculate comprehensive backtest metrics"""
        try:
            if not self.trades_history:
                return BacktestMetrics()
            
            metrics = BacktestMetrics()
            
            # Basic metrics
            metrics.total_trades = len(self.trades_history)
            winning_trades = [t for t in self.trades_history if t.pnl_pct and t.pnl_pct > 0]
            losing_trades = [t for t in self.trades_history if t.pnl_pct and t.pnl_pct <= 0]
            
            metrics.winning_trades = len(winning_trades)
            metrics.losing_trades = len(losing_trades)
            metrics.win_rate = metrics.winning_trades / metrics.total_trades if metrics.total_trades > 0 else 0
            
            # PnL metrics
            metrics.total_pnl_pct = (final_capital - initial_capital) / initial_capital
            
            if winning_trades:
                metrics.avg_win_pct = np.mean([t.pnl_pct for t in winning_trades])
                metrics.max_win_pct = max([t.pnl_pct for t in winning_trades])
            
            if losing_trades:
                metrics.avg_loss_pct = np.mean([t.pnl_pct for t in losing_trades])
                metrics.max_loss_pct = min([t.pnl_pct for t in losing_trades])  # Most negative
            
            # Profit factor
            gross_profit = sum([t.pnl_pct for t in winning_trades]) if winning_trades else 0
            gross_loss = abs(sum([t.pnl_pct for t in losing_trades])) if losing_trades else 0
            metrics.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Risk metrics
            if equity_history:
                equity_values = [e['equity'] for e in equity_history]
                equity_returns = np.diff(equity_values) / equity_values[:-1]
                
                # Drawdown calculation
                running_max = np.maximum.accumulate(equity_values)
                drawdown = (equity_values - running_max) / running_max
                metrics.max_drawdown_pct = abs(min(drawdown))
                
                # Sharpe ratio (annualized)
                if len(equity_returns) > 0:
                    metrics.volatility_pct = np.std(equity_returns) * np.sqrt(252 * 24 * 60)  # Annualized
                    mean_return = np.mean(equity_returns) * 252 * 24 * 60  # Annualized
                    metrics.sharpe_ratio = mean_return / metrics.volatility_pct if metrics.volatility_pct > 0 else 0
                    
                    # Calmar ratio
                    metrics.calmar_ratio = mean_return / metrics.max_drawdown_pct if metrics.max_drawdown_pct > 0 else 0
            
            # Time-based metrics
            hold_times = [t.hold_time_minutes for t in self.trades_history if t.hold_time_minutes is not None]
            if hold_times:
                metrics.avg_hold_time_minutes = np.mean(hold_times)
                metrics.max_hold_time_minutes = max(hold_times)
            
            # Calculate trades per day
            if equity_history:
                total_days = (equity_history[-1]['timestamp'] - equity_history[0]['timestamp']).days
                metrics.trades_per_day = metrics.total_trades / max(total_days, 1)
            
            # Quality-based metrics
            quality_trades = defaultdict(list)
            for trade in self.trades_history:
                if trade.pnl_pct is not None:
                    quality_trades[trade.quality].append(trade.pnl_pct > 0)
            
            for quality, results in quality_trades.items():
                win_rate = sum(results) / len(results) if results else 0
                if quality == SignalQuality.PREMIUM:
                    metrics.premium_signal_win_rate = win_rate
                elif quality == SignalQuality.HIGH:
                    metrics.high_signal_win_rate = win_rate
                elif quality == SignalQuality.MEDIUM:
                    metrics.medium_signal_win_rate = win_rate
                elif quality == SignalQuality.LOW:
                    metrics.low_signal_win_rate = win_rate
            
            # Regime-based performance
            regime_pnl = defaultdict(list)
            for trade in self.trades_history:
                if trade.pnl_pct is not None:
                    regime_pnl[trade.market_regime].append(trade.pnl_pct)
            
            for regime, pnls in regime_pnl.items():
                avg_pnl = np.mean(pnls) if pnls else 0
                if regime == MarketRegime.VOLATILE:
                    metrics.volatile_regime_pnl = avg_pnl
                elif regime == MarketRegime.CALM:
                    metrics.calm_regime_pnl = avg_pnl
                elif regime == MarketRegime.BREAKDOWN:
                    metrics.breakdown_regime_pnl = avg_pnl
                elif regime == MarketRegime.TRANSITIONAL:
                    metrics.transitional_regime_pnl = avg_pnl
            
            # Timeframe performance
            tf_trades = defaultdict(list)
            for trade in self.trades_history:
                if trade.pnl_pct is not None:
                    tf_trades[trade.timeframe].append(trade.pnl_pct > 0)
            
            for tf, results in tf_trades.items():
                win_rate = sum(results) / len(results) if results else 0
                if tf == '1m':
                    metrics.tf_1m_win_rate = win_rate
                elif tf == '3m':
                    metrics.tf_3m_win_rate = win_rate
                elif tf == '5m':
                    metrics.tf_5m_win_rate = win_rate
            
            # Cost analysis
            metrics.total_slippage_cost = sum([t.slippage_cost * t.pnl_usd for t in self.trades_history if t.slippage_cost])
            metrics.total_commission_cost = sum([t.commission_cost * t.pnl_usd for t in self.trades_history if t.commission_cost])
            metrics.cost_adjusted_pnl = metrics.total_pnl_pct - (metrics.total_slippage_cost + metrics.total_commission_cost) / initial_capital
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating backtest metrics: {e}")
            return BacktestMetrics()
    
    def save_backtest_results(self, metrics: BacktestMetrics, output_file: str):
        """Save backtest results to JSON file"""
        try:
            results = {
                'backtest_metrics': {
                    'total_trades': metrics.total_trades,
                    'win_rate': metrics.win_rate,
                    'total_return_pct': metrics.total_pnl_pct,
                    'max_drawdown_pct': metrics.max_drawdown_pct,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'profit_factor': metrics.profit_factor,
                    'avg_hold_time_minutes': metrics.avg_hold_time_minutes,
                    'trades_per_day': metrics.trades_per_day,
                    'quality_performance': {
                        'premium': metrics.premium_signal_win_rate,
                        'high': metrics.high_signal_win_rate,
                        'medium': metrics.medium_signal_win_rate,
                        'low': metrics.low_signal_win_rate
                    },
                    'regime_performance': {
                        'volatile': metrics.volatile_regime_pnl,
                        'calm': metrics.calm_regime_pnl,
                        'breakdown': metrics.breakdown_regime_pnl,
                        'transitional': metrics.transitional_regime_pnl
                    },
                    'timeframe_performance': {
                        '1m': metrics.tf_1m_win_rate,
                        '3m': metrics.tf_3m_win_rate,
                        '5m': metrics.tf_5m_win_rate
                    },
                    'costs': {
                        'total_slippage': metrics.total_slippage_cost,
                        'total_commission': metrics.total_commission_cost,
                        'cost_adjusted_return': metrics.cost_adjusted_pnl
                    }
                },
                'trade_history': [
                    {
                        'symbol': t.symbol,
                        'signal_type': t.signal_type,
                        'entry_time': t.entry_time.isoformat() if t.entry_time else None,
                        'entry_price': t.entry_price,
                        'exit_time': t.exit_time.isoformat() if t.exit_time else None,
                        'exit_price': t.exit_price,
                        'pnl_pct': t.pnl_pct,
                        'exit_reason': t.exit_reason,
                        'quality': t.quality.value if hasattr(t.quality, 'value') else str(t.quality),
                        'confidence': t.original_confidence,
                        'timeframe': t.timeframe,
                        'hold_time_minutes': t.hold_time_minutes
                    }
                    for t in self.trades_history
                ],
                'generated_at': datetime.now().isoformat()
            }
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Backtest results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")


# Testing function
async def run_scalping_backtest():
    """Run a sample scalping backtest"""
    try:
        import ccxt.async_support as ccxt
        
        # Initialize exchange
        exchange = ccxt.binance({
            'sandbox': False,  # Use real data
            'enableRateLimit': True,
        })
        
        # Create backtest engine
        backtest_engine = ScalpingBacktestEngine(exchange)
        
        # Define backtest period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # 1 week backtest
        
        print(f"Running scalping backtest from {start_date} to {end_date}")
        
        # Run backtest
        metrics = await backtest_engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0
        )
        
        # Print results
        print(f"\n=== SCALPING BACKTEST RESULTS ===")
        print(f"Total Trades: {metrics.total_trades}")
        print(f"Win Rate: {metrics.win_rate:.1%}")
        print(f"Total Return: {metrics.total_pnl_pct:.2%}")
        print(f"Max Drawdown: {metrics.max_drawdown_pct:.2%}")
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"Profit Factor: {metrics.profit_factor:.2f}")
        print(f"Avg Hold Time: {metrics.avg_hold_time_minutes:.1f} minutes")
        print(f"Trades Per Day: {metrics.trades_per_day:.1f}")
        
        print(f"\n=== QUALITY PERFORMANCE ===")
        print(f"Premium Signals: {metrics.premium_signal_win_rate:.1%}")
        print(f"High Quality: {metrics.high_signal_win_rate:.1%}")
        print(f"Medium Quality: {metrics.medium_signal_win_rate:.1%}")
        print(f"Low Quality: {metrics.low_signal_win_rate:.1%}")
        
        # Save results
        output_file = f"scalping_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backtest_engine.save_backtest_results(metrics, output_file)
        
        await exchange.close()
        
    except Exception as e:
        print(f"Error running scalping backtest: {e}")

if __name__ == "__main__":
    asyncio.run(run_scalping_backtest())