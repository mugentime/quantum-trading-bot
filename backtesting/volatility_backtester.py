#!/usr/bin/env python3
"""
HIGH VOLATILITY STRATEGY BACKTESTER
Comprehensive backtesting framework for high volatility pairs trading strategy
with realistic transaction costs and slippage modeling.
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, NamedTuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import ccxt.async_support as ccxt
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Import strategy components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.high_volatility_strategy import (
    VolatilityAnalyzer, SignalEnhancer, VolatilityMetrics, 
    MarketRegime, VolatilityLevel, SignalData
)
from config.volatility_config import HighVolatilityConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestResult(NamedTuple):
    """Container for backtest results"""
    symbol: str
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_pnl: float
    best_trade: float
    worst_trade: float
    volatility: float
    calmar_ratio: float
    trade_details: List[Dict]

@dataclass
class BacktestTrade:
    """Individual trade record for backtesting"""
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    side: str
    quantity: float
    leverage: int
    entry_signal: SignalData
    exit_reason: str
    pnl: float
    pnl_pct: float
    commission: float
    slippage: float
    status: str  # 'open', 'closed', 'stopped'

@dataclass
class BacktestPosition:
    """Position tracking for backtesting"""
    symbol: str
    side: str
    entry_price: float
    quantity: float
    leverage: int
    stop_loss: float
    take_profit: float
    entry_time: datetime
    signal: SignalData
    unrealized_pnl: float = 0.0
    max_favorable: float = 0.0
    max_adverse: float = 0.0

class VolatilityBacktester:
    """Advanced backtesting framework for high volatility strategy"""
    
    def __init__(self, config: HighVolatilityConfig, initial_capital: float = 10000):
        self.config = config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Strategy components
        self.volatility_analyzer = VolatilityAnalyzer()
        self.signal_enhancer = SignalEnhancer()
        
        # Backtesting state
        self.trades: List[BacktestTrade] = []
        self.positions: Dict[str, BacktestPosition] = {}
        self.daily_pnl: Dict[str, float] = {}
        self.daily_capital: Dict[str, float] = {}
        
        # Transaction costs
        self.commission_rate = 0.0004  # 0.04% per side (Binance futures)
        self.slippage_rate = 0.0002    # 0.02% average slippage
        
        # Risk tracking
        self.daily_losses: Dict[str, float] = {}
        self.max_drawdown_value = 0.0
        self.peak_capital = initial_capital
        
    async def fetch_historical_data(self, symbol: str, timeframe: str, 
                                   start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch historical OHLCV data for backtesting"""
        try:
            exchange = ccxt.binance({
                'sandbox': True,  # Use testnet for data fetching
                'rateLimit': 100,
                'enableRateLimit': True
            })
            
            # Calculate required data points
            since = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
            
            all_data = []
            current_since = since
            
            logger.info(f"Fetching historical data for {symbol} {timeframe}")
            
            while current_since < end_timestamp:
                try:
                    ohlcv = await exchange.fetch_ohlcv(
                        symbol, timeframe, since=current_since, limit=1000
                    )
                    
                    if not ohlcv:
                        break
                    
                    all_data.extend(ohlcv)
                    current_since = ohlcv[-1][0] + 1
                    
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")
                    break
            
            await exchange.close()
            
            if not all_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('timestamp')
            
            # Remove duplicates and sort
            df = df[~df.index.duplicated()].sort_index()
            
            logger.info(f"Fetched {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_volatility_metrics(self, df: pd.DataFrame) -> Optional[VolatilityMetrics]:
        """Calculate volatility metrics for a given price series"""
        if len(df) < 50:
            return None
        
        try:
            atr = self.volatility_analyzer.calculate_atr(df['high'], df['low'], df['close'])
            hist_vol = self.volatility_analyzer.calculate_historical_volatility(df['close'])
            parkinson_vol = self.volatility_analyzer.calculate_parkinson_volatility(df['high'], df['low'])
            gkyz_vol = self.volatility_analyzer.calculate_gkyz_volatility(
                df['open'], df['high'], df['low'], df['close']
            )
            
            # Calculate short-term volatilities
            returns = df['close'].pct_change()
            hourly_vol = abs(returns.iloc[-1]) if len(returns) > 0 else 0
            daily_vol = returns.rolling(24).std().iloc[-1] if len(returns) > 24 else 0
            
            # Volatility percentile
            rolling_vol = returns.rolling(30).std()
            current_vol = rolling_vol.iloc[-1]
            vol_percentile = self.volatility_analyzer.calculate_volatility_percentile(
                current_vol, rolling_vol.dropna()
            )
            
            vol_level = self.volatility_analyzer.get_volatility_level(vol_percentile)
            
            return VolatilityMetrics(
                atr=atr,
                historical_volatility=hist_vol,
                parkinson_volatility=parkinson_vol,
                gkyz_volatility=gkyz_vol,
                hourly_volatility=hourly_vol,
                daily_volatility=daily_vol,
                volatility_percentile=vol_percentile,
                level=vol_level
            )
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics: {e}")
            return None
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, current_idx: int) -> Optional[SignalData]:
        """Generate trading signal for backtesting"""
        try:
            # Need enough historical data
            if current_idx < 100:
                return None
            
            # Get data up to current point
            historical_data = df.iloc[:current_idx + 1]
            
            # Calculate volatility metrics
            volatility_metrics = self.calculate_volatility_metrics(historical_data)
            if not volatility_metrics:
                return None
            
            # Filter low volatility periods
            if volatility_metrics.level == VolatilityLevel.LOW:
                return None
            
            # Check minimum volatility thresholds
            pair_config = self.config.get_pair_config(symbol)
            if pair_config:
                min_threshold = pair_config.min_volatility_threshold
            else:
                min_threshold = self.config.volatility_thresholds.hourly_min
            
            if volatility_metrics.hourly_volatility < min_threshold:
                return None
            
            # Check for volatility breakout
            has_breakout = self.signal_enhancer.detect_volatility_breakout(volatility_metrics)
            if not has_breakout:
                return None
            
            # Volume analysis
            current_volume = historical_data['volume'].iloc[-1]
            has_volume_spike = self.signal_enhancer.analyze_volume_spike(
                historical_data['volume'], current_volume
            )
            
            # Momentum analysis
            momentum_data = self.signal_enhancer.check_momentum_convergence(historical_data['close'])
            
            # Market regime
            market_regime = self.signal_enhancer.detect_market_regime(
                historical_data['close'], volatility_metrics
            )
            
            # Signal generation logic
            current_price = historical_data['close'].iloc[-1]
            confidence = 0.0
            side = None
            
            # Breakout signals
            if market_regime == MarketRegime.BREAKOUT:
                if momentum_data['rsi'] > 70 and momentum_data['macd_histogram'] > 0:
                    side = 'buy'
                    confidence = 0.8
                elif momentum_data['rsi'] < 30 and momentum_data['macd_histogram'] < 0:
                    side = 'sell'
                    confidence = 0.8
            
            # Trending signals
            elif market_regime == MarketRegime.TRENDING and volatility_metrics.level == VolatilityLevel.HIGH:
                if momentum_data['bb_position'] > 0.8 and momentum_data['macd'] > 0:
                    side = 'buy'
                    confidence = 0.7
                elif momentum_data['bb_position'] < 0.2 and momentum_data['macd'] < 0:
                    side = 'sell'
                    confidence = 0.7
            
            if not side or confidence < self.config.signal_config.min_confidence:
                return None
            
            # Enhance confidence with volume
            if has_volume_spike:
                confidence = min(confidence + 0.1, 0.95)
            
            # Calculate position parameters
            position_size, risk_pct = self.calculate_position_size(
                self.current_capital, volatility_metrics, symbol, confidence
            )
            
            stop_loss = self.calculate_stop_loss(current_price, volatility_metrics, side)
            leverage = self.calculate_leverage(volatility_metrics, confidence)
            
            # Calculate take profit
            risk_distance = abs(current_price - stop_loss)
            if volatility_metrics.level == VolatilityLevel.EXTREME:
                reward_ratio = 5.0
            elif volatility_metrics.level == VolatilityLevel.HIGH:
                reward_ratio = 3.0
            else:
                reward_ratio = 2.0
            
            if side == 'buy':
                take_profit = current_price + (risk_distance * reward_ratio)
            else:
                take_profit = current_price - (risk_distance * reward_ratio)
            
            return SignalData(
                symbol=symbol,
                side=side,
                confidence=confidence,
                volatility_metrics=volatility_metrics,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                leverage=leverage,
                risk_amount=risk_distance * position_size / leverage,
                market_regime=market_regime,
                timestamp=historical_data.index[-1]
            )
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, account_balance: float, volatility_metrics: VolatilityMetrics,
                              symbol: str, confidence: float) -> Tuple[float, float]:
        """Calculate position size for backtesting"""
        # Base risk per trade
        base_risk = self.config.risk_management.max_risk_per_trade
        
        # Adjust for volatility
        if volatility_metrics.level == VolatilityLevel.EXTREME:
            volatility_adjustment = 0.6
        elif volatility_metrics.level == VolatilityLevel.HIGH:
            volatility_adjustment = 0.8
        else:
            volatility_adjustment = 1.0
        
        # Adjust for confidence
        confidence_multiplier = min(confidence / 0.8, 1.5)
        
        final_risk = base_risk * volatility_adjustment * confidence_multiplier
        risk_amount = account_balance * final_risk
        
        # Maximum position size
        max_position_value = account_balance * self.config.risk_management.max_position_size
        
        return min(risk_amount, max_position_value), final_risk
    
    def calculate_stop_loss(self, entry_price: float, volatility_metrics: VolatilityMetrics,
                           side: str) -> float:
        """Calculate stop loss for backtesting"""
        if volatility_metrics.level == VolatilityLevel.EXTREME:
            stop_loss_pct = 0.008
        elif volatility_metrics.level == VolatilityLevel.HIGH:
            stop_loss_pct = 0.012
        else:
            stop_loss_pct = 0.015
        
        # Add ATR adjustment
        atr_adjustment = min(volatility_metrics.atr / entry_price, 0.005)
        final_stop_loss_pct = stop_loss_pct + atr_adjustment
        
        if side == 'buy':
            return entry_price * (1 - final_stop_loss_pct)
        else:
            return entry_price * (1 + final_stop_loss_pct)
    
    def calculate_leverage(self, volatility_metrics: VolatilityMetrics, confidence: float) -> int:
        """Calculate leverage for backtesting"""
        if volatility_metrics.level == VolatilityLevel.EXTREME:
            base_leverage = 3
        elif volatility_metrics.level == VolatilityLevel.HIGH:
            base_leverage = 5
        else:
            base_leverage = 8
        
        confidence_multiplier = min(confidence / 0.6, 1.25)
        final_leverage = int(base_leverage * confidence_multiplier)
        
        return min(final_leverage, self.config.risk_management.max_leverage)
    
    def calculate_transaction_costs(self, entry_price: float, quantity: float, leverage: int) -> float:
        """Calculate realistic transaction costs"""
        position_value = entry_price * quantity
        
        # Commission on both entry and exit
        commission = position_value * self.commission_rate * 2
        
        # Slippage (more significant for larger positions and higher volatility)
        slippage = position_value * self.slippage_rate * 2
        
        return commission + slippage
    
    def execute_trade(self, signal: SignalData, current_time: datetime) -> bool:
        """Execute a trade in backtesting"""
        try:
            # Check if we already have a position in this symbol
            if signal.symbol in self.positions:
                return False
            
            # Check daily loss limits
            today = current_time.date().isoformat()
            daily_loss = self.daily_losses.get(today, 0)
            if daily_loss >= self.config.risk_management.max_daily_loss * self.current_capital:
                return False
            
            # Calculate quantity
            quantity = signal.position_size / signal.entry_price
            
            # Calculate transaction costs
            transaction_costs = self.calculate_transaction_costs(
                signal.entry_price, quantity, signal.leverage
            )
            
            # Create position
            position = BacktestPosition(
                symbol=signal.symbol,
                side=signal.side,
                entry_price=signal.entry_price,
                quantity=quantity,
                leverage=signal.leverage,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                entry_time=current_time,
                signal=signal
            )
            
            self.positions[signal.symbol] = position
            
            # Deduct transaction costs from capital
            self.current_capital -= transaction_costs
            
            logger.info(f"BACKTEST TRADE: {signal.symbol} {signal.side.upper()} @ {signal.entry_price:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing trade for {signal.symbol}: {e}")
            return False
    
    def update_positions(self, symbol: str, current_price: float, current_time: datetime):
        """Update open positions and check for exits"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate unrealized PnL
        if position.side == 'buy':
            pnl = (current_price - position.entry_price) * position.quantity * position.leverage
            
            # Check stop loss and take profit
            if current_price <= position.stop_loss:
                self.close_position(symbol, current_price, current_time, "stop_loss")
            elif current_price >= position.take_profit:
                self.close_position(symbol, current_price, current_time, "take_profit")
        else:
            pnl = (position.entry_price - current_price) * position.quantity * position.leverage
            
            # Check stop loss and take profit
            if current_price >= position.stop_loss:
                self.close_position(symbol, current_price, current_time, "stop_loss")
            elif current_price <= position.take_profit:
                self.close_position(symbol, current_price, current_time, "take_profit")
        
        # Update unrealized PnL
        position.unrealized_pnl = pnl
        
        # Track maximum favorable/adverse excursion
        if pnl > position.max_favorable:
            position.max_favorable = pnl
        if pnl < position.max_adverse:
            position.max_adverse = pnl
    
    def close_position(self, symbol: str, exit_price: float, exit_time: datetime, exit_reason: str):
        """Close a position and record trade"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate final PnL
        if position.side == 'buy':
            pnl = (exit_price - position.entry_price) * position.quantity * position.leverage
        else:
            pnl = (position.entry_price - exit_price) * position.quantity * position.leverage
        
        # Calculate transaction costs for exit
        exit_costs = self.calculate_transaction_costs(exit_price, position.quantity, position.leverage) / 2
        
        # Net PnL after costs
        net_pnl = pnl - exit_costs
        pnl_pct = net_pnl / (position.entry_price * position.quantity)
        
        # Update capital
        self.current_capital += net_pnl
        
        # Track daily losses
        if net_pnl < 0:
            today = exit_time.date().isoformat()
            self.daily_losses[today] = self.daily_losses.get(today, 0) + abs(net_pnl)
        
        # Update peak capital and drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if current_drawdown > self.max_drawdown_value:
            self.max_drawdown_value = current_drawdown
        
        # Record trade
        trade = BacktestTrade(
            symbol=symbol,
            entry_time=position.entry_time,
            exit_time=exit_time,
            entry_price=position.entry_price,
            exit_price=exit_price,
            side=position.side,
            quantity=position.quantity,
            leverage=position.leverage,
            entry_signal=position.signal,
            exit_reason=exit_reason,
            pnl=net_pnl,
            pnl_pct=pnl_pct,
            commission=exit_costs,
            slippage=exit_costs * 0.5,  # Approximate split
            status='closed'
        )
        
        self.trades.append(trade)
        
        # Record daily PnL
        date_key = exit_time.date().isoformat()
        self.daily_pnl[date_key] = self.daily_pnl.get(date_key, 0) + net_pnl
        self.daily_capital[date_key] = self.current_capital
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"CLOSED: {symbol} | PnL: ${net_pnl:.2f} ({pnl_pct:.2%}) | Reason: {exit_reason}")
    
    async def backtest_single_pair(self, symbol: str, start_date: datetime, 
                                   end_date: datetime) -> BacktestResult:
        """Backtest strategy on a single trading pair"""
        logger.info(f"Starting backtest for {symbol}")
        
        # Fetch historical data
        df = await self.fetch_historical_data(symbol, '1h', start_date, end_date)
        if df.empty:
            logger.error(f"No data available for {symbol}")
            return self._empty_result(symbol)
        
        # Reset state for this pair
        initial_capital = self.current_capital
        pair_trades = []
        
        logger.info(f"Backtesting {symbol} with {len(df)} data points")
        
        # Iterate through historical data
        for i in range(100, len(df) - 1):  # Start after warm-up period
            current_time = df.index[i]
            current_price = df['close'].iloc[i]
            
            # Update existing positions
            self.update_positions(symbol, current_price, current_time)
            
            # Check for new signals (only if no current position)
            if symbol not in self.positions:
                signal = self.generate_signal(symbol, df, i)
                if signal:
                    self.execute_trade(signal, current_time)
            
            # Check for timeout exits (optional: close positions after certain time)
            if symbol in self.positions:
                position = self.positions[symbol]
                time_in_position = current_time - position.entry_time
                if time_in_position > timedelta(hours=24):  # Max 24 hours per position
                    self.close_position(symbol, current_price, current_time, "timeout")
        
        # Close any remaining positions
        if symbol in self.positions:
            final_price = df['close'].iloc[-1]
            final_time = df.index[-1]
            self.close_position(symbol, final_price, final_time, "backtest_end")
        
        # Filter trades for this symbol
        pair_trades = [trade for trade in self.trades if trade.symbol == symbol]
        
        # Calculate results
        if not pair_trades:
            logger.warning(f"No trades generated for {symbol}")
            return self._empty_result(symbol)
        
        return self._calculate_results(symbol, pair_trades, initial_capital)
    
    def _empty_result(self, symbol: str) -> BacktestResult:
        """Return empty result for pairs with no trades"""
        return BacktestResult(
            symbol=symbol,
            total_return=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            total_trades=0,
            avg_trade_pnl=0.0,
            best_trade=0.0,
            worst_trade=0.0,
            volatility=0.0,
            calmar_ratio=0.0,
            trade_details=[]
        )
    
    def _calculate_results(self, symbol: str, trades: List[BacktestTrade], 
                          initial_capital: float) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        if not trades:
            return self._empty_result(symbol)
        
        # Basic metrics
        total_pnl = sum(trade.pnl for trade in trades)
        total_return = total_pnl / initial_capital
        total_trades = len(trades)
        
        # Trade analysis
        winning_trades = [trade for trade in trades if trade.pnl > 0]
        losing_trades = [trade for trade in trades if trade.pnl <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        best_trade = max(trade.pnl for trade in trades) if trades else 0
        worst_trade = min(trade.pnl for trade in trades) if trades else 0
        
        # Profit factor
        gross_profit = sum(trade.pnl for trade in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(trade.pnl for trade in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Returns series for risk metrics
        trade_returns = [trade.pnl / initial_capital for trade in trades]
        
        # Sharpe ratio
        if len(trade_returns) > 1:
            returns_std = np.std(trade_returns, ddof=1)
            sharpe_ratio = np.mean(trade_returns) / returns_std if returns_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Sortino ratio (using downside deviation)
        downside_returns = [ret for ret in trade_returns if ret < 0]
        if downside_returns:
            downside_deviation = np.std(downside_returns, ddof=1)
            sortino_ratio = np.mean(trade_returns) / downside_deviation if downside_deviation > 0 else 0
        else:
            sortino_ratio = sharpe_ratio
        
        # Maximum drawdown calculation
        cumulative_returns = np.cumsum(trade_returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdowns = (peak - cumulative_returns) / (1 + peak)
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        # Volatility
        volatility = np.std(trade_returns) * np.sqrt(252) if len(trade_returns) > 1 else 0
        
        # Calmar ratio
        calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else 0
        
        # Trade details for analysis
        trade_details = []
        for trade in trades:
            trade_details.append({
                'entry_time': trade.entry_time.isoformat(),
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'side': trade.side,
                'leverage': trade.leverage,
                'pnl': trade.pnl,
                'pnl_pct': trade.pnl_pct,
                'exit_reason': trade.exit_reason,
                'confidence': trade.entry_signal.confidence,
                'volatility_level': trade.entry_signal.volatility_metrics.level.value,
                'market_regime': trade.entry_signal.market_regime.value
            })
        
        return BacktestResult(
            symbol=symbol,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            avg_trade_pnl=avg_trade_pnl,
            best_trade=best_trade,
            worst_trade=worst_trade,
            volatility=volatility,
            calmar_ratio=calmar_ratio,
            trade_details=trade_details
        )
    
    async def run_comprehensive_backtest(self, start_date: datetime, 
                                        end_date: datetime) -> Dict[str, BacktestResult]:
        """Run comprehensive backtest across all configured pairs"""
        logger.info("🚀 STARTING COMPREHENSIVE HIGH VOLATILITY BACKTEST")
        logger.info("=" * 60)
        
        all_pairs = self.config.get_all_pairs()
        results = {}
        
        logger.info(f"Testing {len(all_pairs)} pairs from {start_date.date()} to {end_date.date()}")
        logger.info(f"Initial Capital: ${self.initial_capital:.2f}")
        
        # Test each pair individually
        for symbol in all_pairs:
            # Reset capital for each pair test
            self.current_capital = self.initial_capital
            self.trades = []
            self.positions = {}
            self.daily_pnl = {}
            self.daily_losses = {}
            self.max_drawdown_value = 0.0
            self.peak_capital = self.initial_capital
            
            try:
                result = await self.backtest_single_pair(symbol, start_date, end_date)
                results[symbol] = result
                
                logger.info(f"✅ {symbol}: {result.total_trades} trades, "
                          f"{result.total_return:.2%} return, {result.win_rate:.1%} win rate")
                
            except Exception as e:
                logger.error(f"❌ Error backtesting {symbol}: {e}")
                results[symbol] = self._empty_result(symbol)
        
        # Generate summary report
        self._generate_summary_report(results)
        
        return results
    
    def _generate_summary_report(self, results: Dict[str, BacktestResult]):
        """Generate comprehensive summary report"""
        logger.info("\n" + "=" * 60)
        logger.info("BACKTEST SUMMARY REPORT")
        logger.info("=" * 60)
        
        # Overall statistics
        total_trades = sum(result.total_trades for result in results.values())
        winning_pairs = len([r for r in results.values() if r.total_return > 0])
        
        logger.info(f"Total Pairs Tested: {len(results)}")
        logger.info(f"Profitable Pairs: {winning_pairs}/{len(results)} ({winning_pairs/len(results):.1%})")
        logger.info(f"Total Trades Generated: {total_trades}")
        
        if total_trades > 0:
            avg_return = np.mean([r.total_return for r in results.values()])
            avg_sharpe = np.mean([r.sharpe_ratio for r in results.values() if r.sharpe_ratio != 0])
            avg_max_dd = np.mean([r.max_drawdown for r in results.values() if r.max_drawdown != 0])
            
            logger.info(f"Average Return: {avg_return:.2%}")
            logger.info(f"Average Sharpe Ratio: {avg_sharpe:.2f}")
            logger.info(f"Average Max Drawdown: {avg_max_dd:.2%}")
            
            # Best performing pairs
            sorted_results = sorted(results.items(), key=lambda x: x[1].total_return, reverse=True)
            
            logger.info("\n📊 TOP 5 PERFORMING PAIRS:")
            for i, (symbol, result) in enumerate(sorted_results[:5]):
                logger.info(f"{i+1}. {symbol}: {result.total_return:.2%} return, "
                          f"Sharpe: {result.sharpe_ratio:.2f}, Trades: {result.total_trades}")
            
            logger.info("\n📉 BOTTOM 5 PERFORMING PAIRS:")
            for i, (symbol, result) in enumerate(sorted_results[-5:]):
                logger.info(f"{i+1}. {symbol}: {result.total_return:.2%} return, "
                          f"Sharpe: {result.sharpe_ratio:.2f}, Trades: {result.total_trades}")
    
    def save_results(self, results: Dict[str, BacktestResult], filepath: str):
        """Save backtest results to JSON file"""
        output_data = {
            'backtest_config': {
                'initial_capital': self.initial_capital,
                'commission_rate': self.commission_rate,
                'slippage_rate': self.slippage_rate,
                'strategy_config': self.config.to_dict()
            },
            'results': {}
        }
        
        for symbol, result in results.items():
            output_data['results'][symbol] = {
                'symbol': result.symbol,
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'sortino_ratio': result.sortino_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor,
                'total_trades': result.total_trades,
                'avg_trade_pnl': result.avg_trade_pnl,
                'best_trade': result.best_trade,
                'worst_trade': result.worst_trade,
                'volatility': result.volatility,
                'calmar_ratio': result.calmar_ratio,
                'trade_details': result.trade_details
            }
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Results saved to {filepath}")

# Main execution function
async def main():
    """Main backtesting execution"""
    # Create configuration
    config = HighVolatilityConfig()
    config.set_trading_mode(config.trading_mode.TESTNET)
    
    # Create backtester
    backtester = VolatilityBacktester(config, initial_capital=10000)
    
    # Define backtest period (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Run comprehensive backtest
    results = await backtester.run_comprehensive_backtest(start_date, end_date)
    
    # Save results
    output_dir = Path("backtest_results")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"high_volatility_backtest_{timestamp}.json"
    
    backtester.save_results(results, str(results_file))
    
    return results

if __name__ == "__main__":
    print("HIGH VOLATILITY STRATEGY BACKTESTER")
    print("=" * 50)
    print("🎯 Testing: Extreme volatility pairs (>5% hourly, >15% daily)")
    print("⚡ Strategy: Volatility breakouts + momentum + volume")
    print("🛡️ Risk: Dynamic stops (0.8-1.5%), 3-10x leverage")
    print("📊 Analysis: Comprehensive performance metrics")
    print("=" * 50)
    
    try:
        results = asyncio.run(main())
        print("\n✅ Backtesting completed successfully!")
        print(f"Results saved to backtest_results/")
    except Exception as e:
        print(f"\n❌ Backtesting failed: {e}")
        raise