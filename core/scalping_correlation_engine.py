"""
Advanced Scalping Correlation Engine
High-frequency signal generation for 1-5 minute scalping on Binance futures
Targets 20-50 daily signals with 75-85% win rate and 0.3-0.8% profit per trade
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging
from enum import Enum
import ccxt.async_support as ccxt
from scipy import stats
from scipy.stats import zscore
import talib

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market volatility regimes for adaptive parameters"""
    VOLATILE = "volatile"
    CALM = "calm"  
    TRANSITIONAL = "transitional"
    BREAKDOWN = "breakdown"

class SignalQuality(Enum):
    """Signal quality levels"""
    PREMIUM = "premium"  # Highest confidence
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ScalpingSignal:
    """High-frequency scalping signal with precise timing"""
    id: str
    symbol: str
    timeframe: str
    signal_type: str  # long/short
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # Confidence and timing
    confidence: float
    quality: SignalQuality
    urgency_score: float  # How quickly to act (0-1)
    
    # Correlation analysis
    correlation_strength: float
    divergence_magnitude: float
    correlation_breakdown_type: str
    supporting_timeframes: List[str]
    
    # Market microstructure
    bid_ask_spread: float
    order_book_imbalance: float
    volume_surge_factor: float
    slippage_estimate: float
    
    # Risk management
    position_size_pct: float
    max_hold_minutes: int
    expected_profit_pct: float
    risk_reward_ratio: float
    
    # Market regime adaptation
    market_regime: MarketRegime
    regime_confidence: float
    volatility_factor: float
    
    # Timing precision
    optimal_entry_window_seconds: int
    tick_precision_score: float
    timestamp: datetime
    expires_at: datetime

@dataclass
class OrderBookSnapshot:
    """Real-time order book analysis"""
    symbol: str
    best_bid: float
    best_ask: float
    bid_ask_spread_pct: float
    bid_depth_5: float  # Depth at 5 levels
    ask_depth_5: float
    imbalance_ratio: float  # Bid depth / Ask depth
    spread_volatility: float
    timestamp: datetime

@dataclass
class VolumeAnalysis:
    """Volume pattern analysis for signal validation"""
    symbol: str
    current_volume: float
    avg_volume_1m: float
    volume_surge_ratio: float
    volume_trend_5m: float  # 5-minute volume trend
    institutional_flow: float  # Large order detection
    retail_flow: float  # Small order clustering
    volume_profile_score: float
    timestamp: datetime

class ScalpingCorrelationEngine:
    """Advanced correlation engine optimized for high-frequency scalping"""
    
    def __init__(self, exchange_instance):
        self.exchange = exchange_instance
        
        # Primary scalping pairs (high liquidity, tight spreads)
        self.scalping_pairs = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'
        ]
        
        # Reference pairs for correlation analysis
        self.reference_pairs = [
            'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', 'DOTUSDT', 'LINKUSDT'
        ]
        
        # Multi-timeframe analysis
        self.timeframes = ['1m', '3m', '5m']
        self.primary_timeframe = '1m'
        
        # High-frequency parameters
        self.tick_buffer_size = 100  # Real-time tick data
        self.correlation_lookback = 30  # Shorter for responsiveness
        self.signal_expiry_minutes = 10  # Quick signal expiry
        
        # Scalping-specific thresholds
        self.min_correlation_strength = 0.45  # Lower for more signals
        self.correlation_breakdown_threshold = 0.25
        self.volume_surge_threshold = 1.8  # 80% above average
        self.spread_threshold_pct = 0.05  # 5 basis points max spread
        
        # Adaptive parameters by regime
        self.regime_parameters = {
            MarketRegime.VOLATILE: {
                'correlation_threshold': 0.50,
                'position_size_multiplier': 0.8,
                'stop_loss_multiplier': 1.5,
                'urgency_multiplier': 1.3
            },
            MarketRegime.CALM: {
                'correlation_threshold': 0.40,
                'position_size_multiplier': 1.2, 
                'stop_loss_multiplier': 0.8,
                'urgency_multiplier': 0.7
            },
            MarketRegime.TRANSITIONAL: {
                'correlation_threshold': 0.60,
                'position_size_multiplier': 0.6,
                'stop_loss_multiplier': 1.2,
                'urgency_multiplier': 1.5
            },
            MarketRegime.BREAKDOWN: {
                'correlation_threshold': 0.35,
                'position_size_multiplier': 1.5,
                'stop_loss_multiplier': 0.6,
                'urgency_multiplier': 1.8
            }
        }
        
        # Real-time data buffers
        self.price_buffers = {tf: defaultdict(lambda: deque(maxlen=self.correlation_lookback)) 
                             for tf in self.timeframes}
        self.volume_buffers = {tf: defaultdict(lambda: deque(maxlen=self.correlation_lookback))
                              for tf in self.timeframes}
        self.tick_buffers = defaultdict(lambda: deque(maxlen=self.tick_buffer_size))
        
        # Order book tracking
        self.order_book_history = defaultdict(lambda: deque(maxlen=20))
        
        # Correlation tracking
        self.correlation_matrices = {tf: {} for tf in self.timeframes}
        self.correlation_history = defaultdict(lambda: deque(maxlen=100))
        
        # Signal tracking and performance
        self.active_signals = {}
        self.signal_performance_history = deque(maxlen=1000)
        self.false_signal_patterns = []
        
        # Market regime detection
        self.current_regime = MarketRegime.CALM
        self.regime_confidence = 0.5
        self.regime_history = deque(maxlen=50)
        
        # Performance targets
        self.daily_signal_target = 35  # Target 35 signals per day
        self.target_win_rate = 0.80  # 80% win rate target
        self.target_profit_per_trade = 0.005  # 0.5% average profit
        
        logger.info(f"ScalpingCorrelationEngine initialized with {len(self.scalping_pairs)} scalping pairs")
    
    async def initialize_real_time_feeds(self):
        """Initialize real-time data feeds for all timeframes"""
        try:
            logger.info("Initializing real-time feeds for scalping...")
            
            # Initialize price buffers with recent data
            for timeframe in self.timeframes:
                for symbol in self.scalping_pairs + self.reference_pairs:
                    try:
                        ohlcv = await self.exchange.fetch_ohlcv(
                            symbol, timeframe, limit=self.correlation_lookback * 2
                        )
                        
                        if len(ohlcv) >= self.correlation_lookback:
                            # Initialize price and volume buffers
                            prices = [candle[4] for candle in ohlcv[-self.correlation_lookback:]]
                            volumes = [candle[5] for candle in ohlcv[-self.correlation_lookback:]]
                            
                            self.price_buffers[timeframe][symbol].extend(prices)
                            self.volume_buffers[timeframe][symbol].extend(volumes)
                            
                            # Initialize tick buffer with last price
                            if timeframe == '1m':
                                self.tick_buffers[symbol].extend([prices[-1]] * 10)
                                
                    except Exception as e:
                        logger.warning(f"Failed to initialize {symbol} {timeframe}: {e}")
            
            # Initialize correlation matrices
            for timeframe in self.timeframes:
                await self.update_correlation_matrix(timeframe)
            
            # Detect initial market regime
            await self.detect_market_regime()
            
            logger.info("Real-time feeds initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing real-time feeds: {e}")
    
    async def update_real_time_data(self, timeframe: str):
        """Update real-time price and volume data"""
        try:
            all_symbols = self.scalping_pairs + self.reference_pairs
            
            for symbol in all_symbols:
                try:
                    # Fetch latest candles
                    ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=3)
                    
                    if len(ohlcv) >= 2:
                        # Use the second-to-last candle (complete candle)
                        latest_complete = ohlcv[-2]
                        close_price = latest_complete[4]
                        volume = latest_complete[5]
                        
                        # Update buffers
                        self.price_buffers[timeframe][symbol].append(close_price)
                        self.volume_buffers[timeframe][symbol].append(volume)
                        
                        # Update tick buffer for 1m timeframe
                        if timeframe == '1m':
                            self.tick_buffers[symbol].append(close_price)
                
                except Exception as e:
                    logger.warning(f"Failed to update {symbol} {timeframe}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error updating real-time data for {timeframe}: {e}")
    
    async def update_order_book_data(self, symbol: str):
        """Update real-time order book data for spread analysis"""
        try:
            order_book = await self.exchange.fetch_order_book(symbol, limit=10)
            
            if order_book['bids'] and order_book['asks']:
                best_bid = order_book['bids'][0][0]
                best_ask = order_book['asks'][0][0]
                
                # Calculate depth and imbalance
                bid_depth_5 = sum([order[1] for order in order_book['bids'][:5]])
                ask_depth_5 = sum([order[1] for order in order_book['asks'][:5]])
                
                bid_ask_spread_pct = (best_ask - best_bid) / best_bid * 100
                imbalance_ratio = bid_depth_5 / (ask_depth_5 + 0.001)  # Avoid division by zero
                
                # Calculate spread volatility
                recent_spreads = [obs.bid_ask_spread_pct for obs in list(self.order_book_history[symbol])[-10:]]
                spread_volatility = np.std(recent_spreads) if len(recent_spreads) > 3 else 0.0
                
                snapshot = OrderBookSnapshot(
                    symbol=symbol,
                    best_bid=best_bid,
                    best_ask=best_ask,
                    bid_ask_spread_pct=bid_ask_spread_pct,
                    bid_depth_5=bid_depth_5,
                    ask_depth_5=ask_depth_5,
                    imbalance_ratio=imbalance_ratio,
                    spread_volatility=spread_volatility,
                    timestamp=datetime.now()
                )
                
                self.order_book_history[symbol].append(snapshot)
                return snapshot
        
        except Exception as e:
            logger.warning(f"Error updating order book for {symbol}: {e}")
            return None
    
    async def analyze_volume_patterns(self, symbol: str, timeframe: str) -> VolumeAnalysis:
        """Analyze volume patterns for signal validation"""
        try:
            volumes = list(self.volume_buffers[timeframe][symbol])
            
            if len(volumes) < 10:
                return VolumeAnalysis(
                    symbol=symbol, current_volume=0, avg_volume_1m=0,
                    volume_surge_ratio=1.0, volume_trend_5m=0,
                    institutional_flow=0, retail_flow=0, volume_profile_score=0.5,
                    timestamp=datetime.now()
                )
            
            current_volume = volumes[-1]
            avg_volume_1m = np.mean(volumes[-5:])  # Recent average
            historical_avg = np.mean(volumes[:-5]) if len(volumes) > 5 else avg_volume_1m
            
            volume_surge_ratio = current_volume / (historical_avg + 0.001)
            
            # Volume trend analysis
            if len(volumes) >= 5:
                recent_volumes = volumes[-5:]
                volume_trend_5m = (recent_volumes[-1] - recent_volumes[0]) / recent_volumes[0]
            else:
                volume_trend_5m = 0.0
            
            # Institutional vs retail flow estimation (simplified)
            volume_std = np.std(volumes)
            large_volume_threshold = historical_avg + 2 * volume_std
            
            institutional_flow = 1.0 if current_volume > large_volume_threshold else 0.0
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
            logger.error(f"Error analyzing volume patterns for {symbol}: {e}")
            return VolumeAnalysis(symbol, 0, 0, 1.0, 0, 0, 0, 0.5, datetime.now())
    
    async def update_correlation_matrix(self, timeframe: str):
        """Update correlation matrix for given timeframe"""
        try:
            # Build price matrix
            price_data = {}
            min_length = float('inf')
            
            for symbol in self.scalping_pairs + self.reference_pairs:
                prices = list(self.price_buffers[timeframe][symbol])
                if len(prices) >= self.correlation_lookback:
                    price_data[symbol] = prices[-self.correlation_lookback:]
                    min_length = min(min_length, len(prices))
            
            if len(price_data) < 2 or min_length < 10:
                return
            
            # Ensure all series have same length
            for symbol in price_data:
                price_data[symbol] = price_data[symbol][-min_length:]
            
            # Calculate returns
            returns_data = {}
            for symbol, prices in price_data.items():
                returns = np.diff(prices) / np.array(prices[:-1])
                returns_data[symbol] = returns
            
            # Build correlation matrix
            symbols = list(returns_data.keys())
            n_symbols = len(symbols)
            correlation_matrix = np.zeros((n_symbols, n_symbols))
            
            for i, symbol_i in enumerate(symbols):
                for j, symbol_j in enumerate(symbols):
                    if i == j:
                        correlation_matrix[i, j] = 1.0
                    else:
                        returns_i = returns_data[symbol_i]
                        returns_j = returns_data[symbol_j]
                        
                        if len(returns_i) == len(returns_j) and len(returns_i) > 3:
                            corr, _ = stats.pearsonr(returns_i, returns_j)
                            correlation_matrix[i, j] = corr if not np.isnan(corr) else 0.0
                        else:
                            correlation_matrix[i, j] = 0.0
            
            # Store correlation matrix
            self.correlation_matrices[timeframe] = {
                'matrix': correlation_matrix,
                'symbols': symbols,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error updating correlation matrix for {timeframe}: {e}")
    
    async def detect_market_regime(self) -> MarketRegime:
        """Detect current market volatility regime"""
        try:
            volatility_scores = []
            correlation_scores = []
            
            # Calculate volatility across scalping pairs
            for symbol in self.scalping_pairs:
                prices = list(self.price_buffers['1m'][symbol])
                if len(prices) >= 20:
                    returns = np.diff(prices[-20:]) / np.array(prices[-20:-1])
                    volatility = np.std(returns) * 100  # Percentage volatility
                    volatility_scores.append(volatility)
            
            # Calculate average correlation strength
            if '1m' in self.correlation_matrices:
                matrix = self.correlation_matrices['1m']['matrix']
                upper_triangle = matrix[np.triu_indices(len(matrix), k=1)]
                avg_correlation = np.mean(np.abs(upper_triangle))
                correlation_scores.append(avg_correlation)
            
            # Determine regime
            avg_volatility = np.mean(volatility_scores) if volatility_scores else 0.5
            avg_correlation = np.mean(correlation_scores) if correlation_scores else 0.5
            
            if avg_volatility > 1.5:  # High volatility threshold
                if avg_correlation > 0.6:
                    regime = MarketRegime.BREAKDOWN  # High vol + high correlation
                else:
                    regime = MarketRegime.VOLATILE   # High vol + low correlation
            elif avg_volatility < 0.8:  # Low volatility threshold
                regime = MarketRegime.CALM
            else:
                regime = MarketRegime.TRANSITIONAL
            
            # Calculate regime confidence
            volatility_confidence = 1.0 - abs(avg_volatility - 1.0) / 2.0
            correlation_confidence = avg_correlation
            regime_confidence = (volatility_confidence + correlation_confidence) / 2.0
            
            self.current_regime = regime
            self.regime_confidence = max(0.3, min(0.9, regime_confidence))
            self.regime_history.append({
                'regime': regime,
                'confidence': regime_confidence,
                'volatility': avg_volatility,
                'correlation': avg_correlation,
                'timestamp': datetime.now()
            })
            
            return regime
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return MarketRegime.CALM
    
    async def detect_correlation_breakdowns(self, timeframe: str) -> List[Dict]:
        """Detect correlation breakdowns suitable for scalping"""
        breakdowns = []
        
        try:
            if timeframe not in self.correlation_matrices:
                return breakdowns
            
            matrix_data = self.correlation_matrices[timeframe]
            correlation_matrix = matrix_data['matrix']
            symbols = matrix_data['symbols']
            
            # Compare with historical correlations
            for i, symbol_i in enumerate(symbols):
                if symbol_i not in self.scalping_pairs:
                    continue
                    
                for j, symbol_j in enumerate(symbols):
                    if i >= j or symbol_j not in (self.scalping_pairs + self.reference_pairs):
                        continue
                    
                    current_correlation = correlation_matrix[i, j]
                    
                    # Get historical correlation
                    pair_key = f"{symbol_i}-{symbol_j}"
                    historical_correlations = [
                        entry['correlation'] for entry in self.correlation_history[pair_key]
                        if entry['correlation'] is not None
                    ]
                    
                    if len(historical_correlations) >= 10:
                        historical_avg = np.mean(historical_correlations[-20:])  # Recent average
                        correlation_change = abs(current_correlation - historical_avg)
                        
                        if correlation_change > self.correlation_breakdown_threshold:
                            # Analyze momentum divergence
                            prices_i = list(self.price_buffers[timeframe][symbol_i])
                            prices_j = list(self.price_buffers[timeframe][symbol_j])
                            
                            if len(prices_i) >= 5 and len(prices_j) >= 5:
                                momentum_i = (prices_i[-1] - prices_i[-3]) / prices_i[-3]
                                momentum_j = (prices_j[-1] - prices_j[-3]) / prices_j[-3]
                                momentum_divergence = abs(momentum_i - momentum_j)
                                
                                breakdown = {
                                    'primary_symbol': symbol_i,
                                    'reference_symbol': symbol_j,
                                    'current_correlation': current_correlation,
                                    'historical_correlation': historical_avg,
                                    'correlation_change': correlation_change,
                                    'momentum_divergence': momentum_divergence,
                                    'primary_momentum': momentum_i,
                                    'reference_momentum': momentum_j,
                                    'timeframe': timeframe,
                                    'breakdown_type': 'strengthening' if current_correlation > historical_avg else 'weakening',
                                    'confidence': min(correlation_change * 2.5, 1.0),
                                    'timestamp': datetime.now()
                                }
                                
                                breakdowns.append(breakdown)
                    
                    # Store current correlation for future comparison
                    self.correlation_history[pair_key].append({
                        'correlation': current_correlation,
                        'timestamp': datetime.now()
                    })
            
            # Sort by correlation change magnitude
            breakdowns.sort(key=lambda x: x['correlation_change'], reverse=True)
            return breakdowns[:10]  # Top 10 breakdowns
            
        except Exception as e:
            logger.error(f"Error detecting correlation breakdowns for {timeframe}: {e}")
            return []
    
    async def calculate_signal_quality(self, breakdown: Dict, volume_analysis: VolumeAnalysis, 
                                     order_book: OrderBookSnapshot) -> Tuple[SignalQuality, float]:
        """Calculate signal quality and confidence score"""
        try:
            quality_factors = []
            
            # Correlation strength factor
            corr_strength = abs(breakdown['current_correlation'])
            quality_factors.append(min(corr_strength * 1.5, 1.0))
            
            # Breakdown magnitude factor
            breakdown_strength = breakdown['correlation_change'] * 2.0
            quality_factors.append(min(breakdown_strength, 1.0))
            
            # Volume confirmation factor
            volume_factor = min(volume_analysis.volume_surge_ratio / 2.0, 1.0)
            quality_factors.append(volume_factor)
            
            # Spread quality factor
            spread_factor = 1.0 - min(order_book.bid_ask_spread_pct / self.spread_threshold_pct, 1.0)
            quality_factors.append(spread_factor)
            
            # Order book imbalance factor
            imbalance_factor = min(abs(order_book.imbalance_ratio - 1.0), 0.5) * 2.0
            quality_factors.append(imbalance_factor)
            
            # Momentum divergence factor
            momentum_factor = min(breakdown['momentum_divergence'] * 50, 1.0)
            quality_factors.append(momentum_factor)
            
            # Market regime factor
            regime_params = self.regime_parameters[self.current_regime]
            regime_factor = self.regime_confidence
            quality_factors.append(regime_factor)
            
            # Calculate overall confidence
            confidence = np.mean(quality_factors)
            
            # Determine quality level
            if confidence >= 0.85:
                quality = SignalQuality.PREMIUM
            elif confidence >= 0.70:
                quality = SignalQuality.HIGH
            elif confidence >= 0.55:
                quality = SignalQuality.MEDIUM
            else:
                quality = SignalQuality.LOW
            
            return quality, confidence
            
        except Exception as e:
            logger.error(f"Error calculating signal quality: {e}")
            return SignalQuality.LOW, 0.5
    
    async def calculate_optimal_entry_exit(self, symbol: str, signal_type: str, 
                                         breakdown: Dict, order_book: OrderBookSnapshot) -> Tuple[float, float, float]:
        """Calculate optimal entry, stop loss, and take profit levels"""
        try:
            current_price = order_book.best_bid if signal_type == 'short' else order_book.best_ask
            
            # Get recent price volatility
            prices = list(self.price_buffers['1m'][symbol])
            if len(prices) >= 20:
                returns = np.diff(prices[-20:]) / np.array(prices[-20:-1])
                volatility = np.std(returns)
            else:
                volatility = 0.01  # Default 1% volatility
            
            # Regime-based parameters
            regime_params = self.regime_parameters[self.current_regime]
            
            # Base scalping parameters by volatility
            if volatility > 0.02:  # High volatility (>2%)
                base_sl_pct = 0.015  # 1.5% stop loss
                base_tp_ratio = 1.8  # 1.8:1 risk/reward
            elif volatility > 0.01:  # Medium volatility (1-2%)
                base_sl_pct = 0.012  # 1.2% stop loss  
                base_tp_ratio = 2.0  # 2:1 risk/reward
            else:  # Low volatility (<1%)
                base_sl_pct = 0.008  # 0.8% stop loss
                base_tp_ratio = 2.2  # 2.2:1 risk/reward
            
            # Apply regime adjustments
            stop_loss_pct = base_sl_pct * regime_params['stop_loss_multiplier']
            take_profit_pct = stop_loss_pct * base_tp_ratio
            
            # Account for spread in calculations
            spread_adjustment = order_book.bid_ask_spread_pct / 100 / 2  # Half spread
            
            if signal_type == 'long':
                entry_price = current_price
                stop_loss = entry_price * (1 - stop_loss_pct - spread_adjustment)
                take_profit = entry_price * (1 + take_profit_pct - spread_adjustment)
            else:  # short
                entry_price = current_price
                stop_loss = entry_price * (1 + stop_loss_pct + spread_adjustment)
                take_profit = entry_price * (1 - take_profit_pct + spread_adjustment)
            
            return entry_price, stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Error calculating optimal entry/exit for {symbol}: {e}")
            # Return safe defaults
            return order_book.best_ask, order_book.best_ask * 0.99, order_book.best_ask * 1.01
    
    async def generate_scalping_signals(self) -> List[ScalpingSignal]:
        """Generate high-frequency scalping signals"""
        signals = []
        
        try:
            # Update all data feeds
            for timeframe in self.timeframes:
                await self.update_real_time_data(timeframe)
                await self.update_correlation_matrix(timeframe)
            
            # Update market regime
            await self.detect_market_regime()
            
            # Analyze each timeframe for signals
            for timeframe in self.timeframes:
                breakdowns = await self.detect_correlation_breakdowns(timeframe)
                
                for breakdown in breakdowns[:5]:  # Top 5 breakdowns per timeframe
                    symbol = breakdown['primary_symbol']
                    
                    # Skip if not in scalping pairs
                    if symbol not in self.scalping_pairs:
                        continue
                    
                    # Get market microstructure data
                    order_book = await self.update_order_book_data(symbol)
                    volume_analysis = await self.analyze_volume_patterns(symbol, timeframe)
                    
                    if not order_book:
                        continue
                    
                    # Check spread quality
                    if order_book.bid_ask_spread_pct > self.spread_threshold_pct:
                        continue
                    
                    # Calculate signal quality
                    quality, confidence = await self.calculate_signal_quality(
                        breakdown, volume_analysis, order_book
                    )
                    
                    # Filter low-quality signals
                    if quality == SignalQuality.LOW or confidence < 0.45:
                        continue
                    
                    # Determine signal direction
                    if breakdown['breakdown_type'] == 'weakening':
                        # Correlation weakening - potential divergence play
                        signal_type = 'long' if breakdown['primary_momentum'] > 0 else 'short'
                    else:
                        # Correlation strengthening - potential reversion play
                        signal_type = 'short' if breakdown['primary_momentum'] > 0 else 'long'
                    
                    # Calculate optimal entry/exit
                    entry_price, stop_loss, take_profit = await self.calculate_optimal_entry_exit(
                        symbol, signal_type, breakdown, order_book
                    )
                    
                    # Calculate position size
                    regime_params = self.regime_parameters[self.current_regime]
                    base_position_size = 0.02  # 2% base position
                    position_size_pct = base_position_size * regime_params['position_size_multiplier'] * confidence
                    
                    # Calculate risk/reward
                    if signal_type == 'long':
                        risk = entry_price - stop_loss
                        reward = take_profit - entry_price
                    else:
                        risk = stop_loss - entry_price
                        reward = entry_price - take_profit
                    
                    risk_reward_ratio = abs(reward / risk) if risk != 0 else 0
                    
                    # Calculate timing parameters
                    urgency_score = (confidence * regime_params['urgency_multiplier']) / 2.0
                    max_hold_minutes = {
                        '1m': 10, '3m': 20, '5m': 30
                    }[timeframe]
                    
                    # Calculate expected profit
                    expected_profit_pct = abs(reward / entry_price)
                    
                    # Create signal
                    signal_id = f"SCALP_{symbol}_{timeframe}_{datetime.now().strftime('%H%M%S')}"
                    
                    signal = ScalpingSignal(
                        id=signal_id,
                        symbol=symbol,
                        timeframe=timeframe,
                        signal_type=signal_type,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        
                        # Confidence and timing
                        confidence=confidence,
                        quality=quality,
                        urgency_score=min(urgency_score, 1.0),
                        
                        # Correlation analysis
                        correlation_strength=abs(breakdown['current_correlation']),
                        divergence_magnitude=breakdown['correlation_change'],
                        correlation_breakdown_type=breakdown['breakdown_type'],
                        supporting_timeframes=[timeframe],
                        
                        # Market microstructure
                        bid_ask_spread=order_book.bid_ask_spread_pct,
                        order_book_imbalance=order_book.imbalance_ratio,
                        volume_surge_factor=volume_analysis.volume_surge_ratio,
                        slippage_estimate=order_book.bid_ask_spread_pct / 100 + 0.001,
                        
                        # Risk management
                        position_size_pct=position_size_pct,
                        max_hold_minutes=max_hold_minutes,
                        expected_profit_pct=expected_profit_pct,
                        risk_reward_ratio=risk_reward_ratio,
                        
                        # Market regime adaptation
                        market_regime=self.current_regime,
                        regime_confidence=self.regime_confidence,
                        volatility_factor=volume_analysis.volume_profile_score,
                        
                        # Timing precision
                        optimal_entry_window_seconds=30 if urgency_score > 0.7 else 60,
                        tick_precision_score=confidence * 0.8,
                        timestamp=datetime.now(),
                        expires_at=datetime.now() + timedelta(minutes=self.signal_expiry_minutes)
                    )
                    
                    signals.append(signal)
            
            # Remove duplicate signals on same symbol
            unique_signals = {}
            for signal in signals:
                key = f"{signal.symbol}_{signal.signal_type}"
                if key not in unique_signals or signal.confidence > unique_signals[key].confidence:
                    unique_signals[key] = signal
            
            final_signals = list(unique_signals.values())
            
            # Sort by confidence and urgency
            final_signals.sort(
                key=lambda x: (x.confidence * 0.7 + x.urgency_score * 0.3), 
                reverse=True
            )
            
            # Apply false signal filtering
            filtered_signals = await self.filter_false_signals(final_signals)
            
            # Store active signals
            for signal in filtered_signals:
                self.active_signals[signal.id] = signal
            
            # Clean expired signals
            self.clean_expired_signals()
            
            logger.info(f"Generated {len(filtered_signals)} scalping signals "
                       f"(regime: {self.current_regime.value}, confidence: {self.regime_confidence:.2f})")
            
            return filtered_signals[:15]  # Return top 15 signals
            
        except Exception as e:
            logger.error(f"Error generating scalping signals: {e}")
            return []
    
    async def filter_false_signals(self, signals: List[ScalpingSignal]) -> List[ScalpingSignal]:
        """Apply sophisticated false signal filtering"""
        filtered_signals = []
        
        try:
            for signal in signals:
                # Basic quality filters
                if signal.confidence < 0.45:
                    continue
                
                if signal.risk_reward_ratio < 1.5:
                    continue
                
                # Spread filter
                if signal.bid_ask_spread > self.spread_threshold_pct:
                    continue
                
                # Volume confirmation filter
                if signal.volume_surge_factor < 1.2:  # Require some volume increase
                    continue
                
                # Regime consistency filter
                regime_params = self.regime_parameters[signal.market_regime]
                if signal.correlation_strength < regime_params['correlation_threshold']:
                    continue
                
                # Anti-pattern filter (check against known false signal patterns)
                is_false_pattern = False
                for pattern in self.false_signal_patterns:
                    if self.matches_false_pattern(signal, pattern):
                        is_false_pattern = True
                        break
                
                if is_false_pattern:
                    continue
                
                # Recent signal conflict filter
                has_conflict = False
                for active_signal in self.active_signals.values():
                    if (active_signal.symbol == signal.symbol and 
                        active_signal.signal_type != signal.signal_type and
                        abs((active_signal.timestamp - signal.timestamp).total_seconds()) < 300):
                        has_conflict = True
                        break
                
                if has_conflict:
                    continue
                
                filtered_signals.append(signal)
            
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Error filtering false signals: {e}")
            return signals  # Return original signals if filtering fails
    
    def matches_false_pattern(self, signal: ScalpingSignal, pattern: Dict) -> bool:
        """Check if signal matches a known false pattern"""
        try:
            # Simple pattern matching (can be enhanced with ML)
            if pattern.get('symbol') and pattern['symbol'] != signal.symbol:
                return False
            
            if pattern.get('timeframe') and pattern['timeframe'] != signal.timeframe:
                return False
            
            confidence_range = pattern.get('confidence_range', [0, 1])
            if not (confidence_range[0] <= signal.confidence <= confidence_range[1]):
                return False
            
            correlation_range = pattern.get('correlation_range', [0, 1])
            if not (correlation_range[0] <= signal.correlation_strength <= correlation_range[1]):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error matching false pattern: {e}")
            return False
    
    def clean_expired_signals(self):
        """Remove expired signals from active signals"""
        try:
            current_time = datetime.now()
            expired_ids = [
                signal_id for signal_id, signal in self.active_signals.items()
                if signal.expires_at < current_time
            ]
            
            for signal_id in expired_ids:
                del self.active_signals[signal_id]
                
        except Exception as e:
            logger.error(f"Error cleaning expired signals: {e}")
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for the scalping engine"""
        try:
            total_signals = len(self.signal_performance_history)
            
            if total_signals == 0:
                return {
                    "total_signals": 0,
                    "win_rate": 0.0,
                    "avg_profit_pct": 0.0,
                    "active_signals": len(self.active_signals),
                    "current_regime": self.current_regime.value,
                    "regime_confidence": self.regime_confidence
                }
            
            successful_signals = [s for s in self.signal_performance_history if s.get('profitable', False)]
            win_rate = len(successful_signals) / total_signals
            
            avg_profit = np.mean([s.get('profit_pct', 0) for s in successful_signals]) if successful_signals else 0.0
            
            # Quality distribution
            quality_dist = defaultdict(int)
            for signal in self.active_signals.values():
                quality_dist[signal.quality.value] += 1
            
            return {
                "total_signals": total_signals,
                "win_rate": win_rate,
                "avg_profit_pct": avg_profit,
                "active_signals": len(self.active_signals),
                "current_regime": self.current_regime.value,
                "regime_confidence": self.regime_confidence,
                "quality_distribution": dict(quality_dist),
                "target_progress": {
                    "daily_signals": f"{total_signals}/{self.daily_signal_target}",
                    "win_rate_target": f"{win_rate:.1%}/{self.target_win_rate:.1%}",
                    "profit_target": f"{avg_profit:.2%}/{self.target_profit_per_trade:.2%}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {"error": str(e)}
    
    async def run_continuous_scalping_analysis(self, update_interval: int = 30):
        """Run continuous scalping analysis"""
        logger.info(f"Starting continuous scalping analysis (interval: {update_interval}s)")
        
        try:
            # Initialize real-time feeds
            await self.initialize_real_time_feeds()
            
            while True:
                try:
                    # Generate signals
                    signals = await self.generate_scalping_signals()
                    
                    if signals:
                        # Log top signals
                        for i, signal in enumerate(signals[:3]):
                            logger.info(f"Signal #{i+1}: {signal.symbol} {signal.signal_type.upper()} "
                                       f"@ {signal.entry_price:.6f} "
                                       f"({signal.quality.value} quality, {signal.confidence:.2f} confidence)")
                    
                    # Log performance metrics
                    metrics = self.get_performance_metrics()
                    logger.info(f"Performance: {metrics['active_signals']} active signals, "
                               f"{metrics.get('win_rate', 0):.1%} win rate, "
                               f"regime: {metrics['current_regime']}")
                    
                    # Wait before next analysis
                    await asyncio.sleep(update_interval)
                    
                except Exception as e:
                    logger.error(f"Error in continuous scalping analysis: {e}")
                    await asyncio.sleep(update_interval)
                    
        except KeyboardInterrupt:
            logger.info("Continuous scalping analysis stopped")
        except Exception as e:
            logger.error(f"Fatal error in continuous scalping analysis: {e}")


# Testing and utility functions
async def test_scalping_engine():
    """Test function for the scalping correlation engine"""
    try:
        import ccxt.async_support as ccxt
        
        # Initialize exchange
        exchange = ccxt.binance({
            'sandbox': True,  # Use testnet
            'enableRateLimit': True,
        })
        
        # Create engine
        engine = ScalpingCorrelationEngine(exchange)
        
        # Test initialization
        print("Initializing scalping engine...")
        await engine.initialize_real_time_feeds()
        
        # Test signal generation
        print("Generating test signals...")
        signals = await engine.generate_scalping_signals()
        
        print(f"\nGenerated {len(signals)} scalping signals:")
        for i, signal in enumerate(signals[:5]):
            print(f"\n{i+1}. {signal.symbol} {signal.signal_type.upper()} - {signal.quality.value}")
            print(f"   Entry: {signal.entry_price:.6f}")
            print(f"   SL: {signal.stop_loss:.6f} | TP: {signal.take_profit:.6f}")
            print(f"   Confidence: {signal.confidence:.2f} | RR: {signal.risk_reward_ratio:.1f}")
            print(f"   Timeframe: {signal.timeframe} | Regime: {signal.market_regime.value}")
        
        # Test performance metrics
        print(f"\nPerformance Metrics:")
        metrics = engine.get_performance_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        await exchange.close()
        
    except Exception as e:
        print(f"Error testing scalping engine: {e}")

if __name__ == "__main__":
    asyncio.run(test_scalping_engine())