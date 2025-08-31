#!/usr/bin/env python3
"""
HIGH VOLATILITY PAIRS TRADING STRATEGY
Comprehensive system for identifying and capitalizing on extreme price movements
with sophisticated risk management protocols.
"""

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from scipy.stats import percentileofscore
import json
import os
from enum import Enum
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    BREAKOUT = "breakout"
    EXHAUSTION = "exhaustion"

class VolatilityLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class VolatilityMetrics:
    """Container for volatility analysis metrics"""
    atr: float
    historical_volatility: float
    parkinson_volatility: float
    gkyz_volatility: float
    hourly_volatility: float
    daily_volatility: float
    volatility_percentile: float
    level: VolatilityLevel

@dataclass
class SignalData:
    """Container for trading signal information"""
    symbol: str
    side: str
    confidence: float
    volatility_metrics: VolatilityMetrics
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    leverage: int
    risk_amount: float
    market_regime: MarketRegime
    timestamp: datetime

@dataclass
class RiskParameters:
    """Risk management parameters per symbol"""
    max_position_size_pct: float
    stop_loss_pct: float
    take_profit_ratio: float
    max_daily_loss_pct: float
    volatility_threshold: float
    correlation_limit: float

class VolatilityAnalyzer:
    """Advanced volatility calculation and analysis system"""
    
    def __init__(self, lookback_periods: Dict[str, int] = None):
        self.lookback_periods = lookback_periods or {
            'short': 20,
            'medium': 50,
            'long': 100
        }
    
    def calculate_atr(self, highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 14) -> float:
        """Calculate Average True Range"""
        high_low = highs - lows
        high_close = np.abs(highs - closes.shift())
        low_close = np.abs(lows - closes.shift())
        
        true_ranges = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_ranges.rolling(window=period).mean().iloc[-1]
        
        return atr if not np.isnan(atr) else 0.0
    
    def calculate_historical_volatility(self, prices: pd.Series, period: int = 30) -> float:
        """Calculate historical volatility using log returns"""
        log_returns = np.log(prices / prices.shift())
        volatility = log_returns.rolling(window=period).std().iloc[-1] * np.sqrt(24 * 365)  # Annualized
        
        return volatility if not np.isnan(volatility) else 0.0
    
    def calculate_parkinson_volatility(self, highs: pd.Series, lows: pd.Series, period: int = 30) -> float:
        """Calculate Parkinson volatility estimator"""
        log_hl = np.log(highs / lows)
        parkinson_values = log_hl ** 2
        parkinson_vol = np.sqrt(parkinson_values.rolling(window=period).mean().iloc[-1] / (4 * np.log(2)))
        
        return parkinson_vol * np.sqrt(24 * 365) if not np.isnan(parkinson_vol) else 0.0
    
    def calculate_gkyz_volatility(self, opens: pd.Series, highs: pd.Series, 
                                  lows: pd.Series, closes: pd.Series, period: int = 30) -> float:
        """Calculate Garman-Klass-Yang-Zhang volatility"""
        log_ho = np.log(highs / opens)
        log_lo = np.log(lows / opens)
        log_co = np.log(closes / opens)
        
        rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
        gkyz = rs.rolling(window=period).mean().iloc[-1]
        
        return np.sqrt(gkyz * 24 * 365) if not np.isnan(gkyz) else 0.0
    
    def calculate_volatility_percentile(self, current_volatility: float, 
                                       historical_volatilities: pd.Series) -> float:
        """Calculate percentile rank of current volatility"""
        if len(historical_volatilities) < 10:
            return 50.0
        
        percentile = percentileofscore(historical_volatilities.dropna(), current_volatility)
        return percentile
    
    def get_volatility_level(self, percentile: float) -> VolatilityLevel:
        """Classify volatility level based on percentile"""
        if percentile >= 99:
            return VolatilityLevel.EXTREME
        elif percentile >= 95:
            return VolatilityLevel.HIGH
        elif percentile >= 75:
            return VolatilityLevel.MODERATE
        else:
            return VolatilityLevel.LOW

class SignalEnhancer:
    """Advanced signal enhancement with volatility breakouts and momentum"""
    
    def __init__(self):
        self.momentum_lookback = 20
        self.volume_lookback = 50
    
    def detect_volatility_breakout(self, volatility_metrics: VolatilityMetrics, 
                                   threshold_percentile: float = 95) -> bool:
        """Detect volatility breakout above threshold"""
        return volatility_metrics.volatility_percentile >= threshold_percentile
    
    def analyze_volume_spike(self, volumes: pd.Series, current_volume: float, 
                            spike_threshold: float = 2.0) -> bool:
        """Detect volume spikes correlating with volatility"""
        avg_volume = volumes.rolling(window=self.volume_lookback).mean().iloc[-1]
        return current_volume >= (avg_volume * spike_threshold)
    
    def check_momentum_convergence(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate momentum indicators for convergence analysis"""
        # RSI
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = (ema12 - ema26).iloc[-1]
        macd_signal = (ema12 - ema26).ewm(span=9).mean().iloc[-1]
        macd_histogram = macd - macd_signal
        
        # Bollinger Bands position
        sma20 = prices.rolling(window=20).mean()
        std20 = prices.rolling(window=20).std()
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)
        bb_position = ((prices.iloc[-1] - bb_lower.iloc[-1]) / 
                       (bb_upper.iloc[-1] - bb_lower.iloc[-1]))
        
        return {
            'rsi': rsi if not np.isnan(rsi) else 50,
            'macd': macd if not np.isnan(macd) else 0,
            'macd_histogram': macd_histogram if not np.isnan(macd_histogram) else 0,
            'bb_position': bb_position if not np.isnan(bb_position) else 0.5
        }
    
    def detect_market_regime(self, prices: pd.Series, volatility_metrics: VolatilityMetrics) -> MarketRegime:
        """Identify current market regime"""
        # Trend strength using ADX concept
        high_prices = prices.rolling(window=20).max()
        low_prices = prices.rolling(window=20).min()
        current_price = prices.iloc[-1]
        
        trend_position = (current_price - low_prices.iloc[-1]) / (high_prices.iloc[-1] - low_prices.iloc[-1])
        
        # Volatility breakout detection
        if volatility_metrics.volatility_percentile >= 95:
            if trend_position > 0.8 or trend_position < 0.2:
                return MarketRegime.BREAKOUT
            else:
                return MarketRegime.EXHAUSTION
        elif trend_position > 0.7 or trend_position < 0.3:
            return MarketRegime.TRENDING
        else:
            return MarketRegime.RANGING

class RiskManager:
    """Advanced risk management for high volatility trading"""
    
    def __init__(self, base_config: Dict):
        self.base_config = base_config
        self.daily_losses = {}
        self.position_correlations = {}
    
    def calculate_position_size(self, account_balance: float, volatility_metrics: VolatilityMetrics,
                              symbol: str, confidence: float) -> Tuple[float, float]:
        """Calculate position size based on volatility and confidence"""
        # Base risk per trade (1-2% for high volatility)
        base_risk = 0.01 if volatility_metrics.level == VolatilityLevel.EXTREME else 0.015
        
        # Adjust risk based on confidence
        risk_multiplier = min(confidence / 0.8, 1.5)  # Cap at 1.5x
        adjusted_risk = base_risk * risk_multiplier
        
        # Volatility-based position sizing (inverse relationship)
        if volatility_metrics.level == VolatilityLevel.EXTREME:
            volatility_adjustment = 0.6  # Reduce size by 40%
        elif volatility_metrics.level == VolatilityLevel.HIGH:
            volatility_adjustment = 0.8  # Reduce size by 20%
        else:
            volatility_adjustment = 1.0
        
        final_risk = adjusted_risk * volatility_adjustment
        risk_amount = account_balance * final_risk
        
        # Maximum position size (5% of account)
        max_position_value = account_balance * 0.05
        
        return min(risk_amount, max_position_value), final_risk
    
    def calculate_stop_loss(self, entry_price: float, volatility_metrics: VolatilityMetrics,
                           side: str) -> float:
        """Calculate dynamic stop loss based on volatility"""
        # Base stop loss range: 0.8-1.5% for volatile pairs
        if volatility_metrics.level == VolatilityLevel.EXTREME:
            stop_loss_pct = 0.008  # 0.8%
        elif volatility_metrics.level == VolatilityLevel.HIGH:
            stop_loss_pct = 0.012  # 1.2%
        else:
            stop_loss_pct = 0.015  # 1.5%
        
        # Add ATR component for market noise
        atr_adjustment = min(volatility_metrics.atr / entry_price, 0.005)  # Cap at 0.5%
        final_stop_loss_pct = stop_loss_pct + atr_adjustment
        
        if side == 'buy':
            return entry_price * (1 - final_stop_loss_pct)
        else:
            return entry_price * (1 + final_stop_loss_pct)
    
    def calculate_leverage(self, volatility_metrics: VolatilityMetrics, confidence: float) -> int:
        """Calculate dynamic leverage based on volatility and confidence"""
        # Base leverage scaling: 3x (high vol) to 10x (moderate vol)
        if volatility_metrics.level == VolatilityLevel.EXTREME:
            base_leverage = 3
        elif volatility_metrics.level == VolatilityLevel.HIGH:
            base_leverage = 5
        else:
            base_leverage = 8
        
        # Adjust based on confidence
        confidence_multiplier = min(confidence / 0.6, 1.25)  # Cap at 1.25x
        final_leverage = int(base_leverage * confidence_multiplier)
        
        return min(final_leverage, 10)  # Maximum 10x leverage
    
    def check_daily_loss_limit(self, symbol: str, potential_loss: float) -> bool:
        """Check if trade would exceed daily loss limit"""
        today = datetime.now().date()
        daily_key = f"{today}_{symbol}"
        
        current_daily_loss = self.daily_losses.get(daily_key, 0)
        total_potential_loss = current_daily_loss + potential_loss
        
        # 3% daily loss limit for high volatility positions
        return total_potential_loss <= 0.03
    
    def update_daily_loss(self, symbol: str, loss_amount: float):
        """Update daily loss tracking"""
        today = datetime.now().date()
        daily_key = f"{today}_{symbol}"
        
        if daily_key not in self.daily_losses:
            self.daily_losses[daily_key] = 0
        self.daily_losses[daily_key] += loss_amount

class HighVolatilityStrategy:
    """Main high volatility pairs trading strategy"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.exchange = None
        self.volatility_analyzer = VolatilityAnalyzer()
        self.signal_enhancer = SignalEnhancer()
        self.risk_manager = RiskManager(config)
        
        # Target pairs configuration
        self.primary_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        self.secondary_pairs = ['AXS/USDT', 'ADA/USDT', 'XRP/USDT', 'DOGE/USDT']
        
        self.active_positions = {}
        self.market_data_cache = {}
        self.running = False
        
    async def initialize_exchange(self):
        """Initialize exchange connection"""
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'sandbox': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
            'options': {'defaultType': 'future'},
            'rateLimit': 100,
            'enableRateLimit': True
        })
        
        logger.info("Exchange connection initialized")
    
    async def fetch_market_data(self, symbol: str, timeframes: List[str] = None) -> Dict:
        """Fetch comprehensive market data for analysis"""
        timeframes = timeframes or ['1m', '5m', '15m', '1h']
        market_data = {'symbol': symbol}
        
        try:
            # Fetch OHLCV data for multiple timeframes
            for tf in timeframes:
                limit = 200 if tf == '1m' else 100
                ohlcv = await self.exchange.fetch_ohlcv(symbol, tf, limit=limit)
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                market_data[tf] = df
            
            # Fetch current ticker
            ticker = await self.exchange.fetch_ticker(symbol)
            market_data['ticker'] = ticker
            
            # Cache the data
            self.market_data_cache[symbol] = {
                'data': market_data,
                'timestamp': datetime.now()
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return {}
    
    async def analyze_volatility(self, symbol: str) -> Optional[VolatilityMetrics]:
        """Comprehensive volatility analysis"""
        try:
            market_data = await self.fetch_market_data(symbol)
            if not market_data:
                return None
            
            # Use 1-hour data for primary analysis
            df = market_data['1h']
            if len(df) < 50:
                return None
            
            # Calculate volatility metrics
            atr = self.volatility_analyzer.calculate_atr(df['high'], df['low'], df['close'])
            hist_vol = self.volatility_analyzer.calculate_historical_volatility(df['close'])
            parkinson_vol = self.volatility_analyzer.calculate_parkinson_volatility(df['high'], df['low'])
            gkyz_vol = self.volatility_analyzer.calculate_gkyz_volatility(
                df['open'], df['high'], df['low'], df['close']
            )
            
            # Calculate short-term volatilities
            hourly_returns = df['close'].pct_change().iloc[-1:]
            hourly_vol = abs(hourly_returns.iloc[-1]) if len(hourly_returns) > 0 else 0
            
            daily_returns = df['close'].pct_change(24).iloc[-24:]  # Last 24 hours
            daily_vol = daily_returns.std() if len(daily_returns) > 1 else 0
            
            # Calculate volatility percentile
            historical_vols = df['close'].rolling(30).apply(
                lambda x: x.pct_change().std() if len(x) > 1 else 0
            )
            current_vol = df['close'].pct_change().rolling(24).std().iloc[-1]
            vol_percentile = self.volatility_analyzer.calculate_volatility_percentile(
                current_vol, historical_vols
            )
            
            # Determine volatility level
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
            logger.error(f"Error analyzing volatility for {symbol}: {e}")
            return None
    
    async def generate_signal(self, symbol: str) -> Optional[SignalData]:
        """Generate trading signal based on volatility and momentum"""
        try:
            # Get volatility metrics
            volatility_metrics = await self.analyze_volatility(symbol)
            if not volatility_metrics:
                return None
            
            # Filter out low volatility periods
            if volatility_metrics.level == VolatilityLevel.LOW:
                return None
            
            # Check volatility thresholds
            if volatility_metrics.hourly_volatility < 0.05:  # 5% hourly volatility minimum
                return None
            if volatility_metrics.daily_volatility < 0.15:   # 15% daily volatility minimum
                return None
            
            # Get market data for signal analysis
            market_data = self.market_data_cache.get(symbol, {}).get('data', {})
            if not market_data:
                return None
            
            df_1m = market_data.get('1m')
            df_5m = market_data.get('5m')
            df_15m = market_data.get('15m')
            df_1h = market_data.get('1h')
            
            if not all([df_1m is not None, df_5m is not None, df_15m is not None, df_1h is not None]):
                return None
            
            # Check for volatility breakout
            has_breakout = self.signal_enhancer.detect_volatility_breakout(volatility_metrics)
            if not has_breakout:
                return None
            
            # Check volume spike
            current_volume = market_data['ticker']['baseVolume']
            has_volume_spike = self.signal_enhancer.analyze_volume_spike(
                df_1h['volume'], current_volume
            )
            
            # Analyze momentum
            momentum_data = self.signal_enhancer.check_momentum_convergence(df_15m['close'])
            
            # Determine market regime
            market_regime = self.signal_enhancer.detect_market_regime(df_1h['close'], volatility_metrics)
            
            # Generate signal based on momentum and volatility
            current_price = market_data['ticker']['last']
            
            # Signal logic
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
            
            # Trending signals with high volatility
            elif market_regime == MarketRegime.TRENDING and volatility_metrics.level == VolatilityLevel.HIGH:
                if momentum_data['bb_position'] > 0.8 and momentum_data['macd'] > 0:
                    side = 'buy'
                    confidence = 0.7
                elif momentum_data['bb_position'] < 0.2 and momentum_data['macd'] < 0:
                    side = 'sell'
                    confidence = 0.7
            
            if not side or confidence < 0.6:
                return None
            
            # Enhance confidence with volume
            if has_volume_spike:
                confidence = min(confidence + 0.1, 0.95)
            
            # Calculate risk parameters
            account_balance = await self.get_account_balance()
            position_size, risk_pct = self.risk_manager.calculate_position_size(
                account_balance, volatility_metrics, symbol, confidence
            )
            
            stop_loss = self.risk_manager.calculate_stop_loss(
                current_price, volatility_metrics, side
            )
            
            leverage = self.risk_manager.calculate_leverage(volatility_metrics, confidence)
            
            # Calculate take profit (2:1 to 5:1 risk-reward based on volatility)
            risk_distance = abs(current_price - stop_loss)
            if volatility_metrics.level == VolatilityLevel.EXTREME:
                reward_ratio = 5.0  # 5:1 for extreme volatility
            elif volatility_metrics.level == VolatilityLevel.HIGH:
                reward_ratio = 3.0  # 3:1 for high volatility
            else:
                reward_ratio = 2.0  # 2:1 for moderate volatility
            
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
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    async def execute_signal(self, signal: SignalData) -> Optional[Dict]:
        """Execute trading signal with comprehensive risk management"""
        try:
            # Final risk checks
            if not self.risk_manager.check_daily_loss_limit(signal.symbol, signal.risk_amount):
                logger.warning(f"Daily loss limit exceeded for {signal.symbol}")
                return None
            
            # Set leverage
            await self.exchange.set_leverage(signal.leverage, signal.symbol.replace('/', ''))
            
            # Calculate quantity
            quantity = signal.position_size / signal.entry_price
            
            # Round quantity based on symbol
            if 'BTC' in signal.symbol:
                quantity = round(quantity, 3)
            elif 'ETH' in signal.symbol:
                quantity = round(quantity, 3)
            else:
                quantity = round(quantity, 1)
            
            # Place market order
            order = await self.exchange.create_market_order(
                symbol=signal.symbol,
                side=signal.side,
                amount=quantity
            )
            
            if order:
                # Place stop loss order
                sl_order = await self.exchange.create_order(
                    symbol=signal.symbol,
                    type='stop_market',
                    side='sell' if signal.side == 'buy' else 'buy',
                    amount=quantity,
                    params={'stopPrice': signal.stop_loss, 'reduceOnly': True}
                )
                
                # Place take profit order
                tp_order = await self.exchange.create_order(
                    symbol=signal.symbol,
                    type='limit',
                    side='sell' if signal.side == 'buy' else 'buy',
                    amount=quantity,
                    price=signal.take_profit,
                    params={'reduceOnly': True}
                )
                
                # Store position info
                self.active_positions[signal.symbol] = {
                    'signal': signal,
                    'order': order,
                    'stop_loss_order': sl_order,
                    'take_profit_order': tp_order,
                    'entry_time': datetime.now()
                }
                
                logger.info(f"✅ HIGH VOLATILITY TRADE EXECUTED: {signal.symbol}")
                logger.info(f"   Side: {signal.side.upper()} | Qty: {quantity}")
                logger.info(f"   Entry: ${signal.entry_price:.4f} | Stop: ${signal.stop_loss:.4f} | TP: ${signal.take_profit:.4f}")
                logger.info(f"   Leverage: {signal.leverage}x | Confidence: {signal.confidence:.2%}")
                logger.info(f"   Volatility: {signal.volatility_metrics.level.value} ({signal.volatility_metrics.volatility_percentile:.1f}th percentile)")
                logger.info(f"   Risk: ${signal.risk_amount:.2f} | Regime: {signal.market_regime.value}")
                
                return {
                    'success': True,
                    'order': order,
                    'signal': signal
                }
            
        except Exception as e:
            logger.error(f"Error executing signal for {signal.symbol}: {e}")
            return None
    
    async def get_account_balance(self) -> float:
        """Get current account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            return balance['USDT']['free']
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    async def scan_opportunities(self) -> List[SignalData]:
        """Scan all target pairs for high volatility opportunities"""
        signals = []
        all_pairs = self.primary_pairs + self.secondary_pairs
        
        for symbol in all_pairs:
            try:
                signal = await self.generate_signal(symbol)
                if signal:
                    signals.append(signal)
                    logger.info(f"🎯 High volatility signal: {symbol} - {signal.side.upper()} (confidence: {signal.confidence:.2%})")
                
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        # Sort by confidence and volatility
        signals.sort(key=lambda x: (x.confidence, x.volatility_metrics.volatility_percentile), reverse=True)
        
        return signals[:3]  # Return top 3 signals to avoid overexposure
    
    async def start_trading(self):
        """Start the high volatility trading strategy"""
        await self.initialize_exchange()
        self.running = True
        
        logger.info("🚀 STARTING HIGH VOLATILITY PAIRS TRADING STRATEGY")
        logger.info("=" * 60)
        
        balance = await self.get_account_balance()
        logger.info(f"Initial Balance: ${balance:.2f} USDT")
        logger.info(f"Target Pairs: {', '.join(self.primary_pairs + self.secondary_pairs)}")
        logger.info(f"Volatility Thresholds: >5% hourly, >15% daily")
        logger.info(f"Risk Management: 0.8-1.5% stops, 3-10x dynamic leverage")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"\n📊 VOLATILITY SCAN CYCLE #{cycle_count}")
                
                # Scan for opportunities
                signals = await self.scan_opportunities()
                
                if signals:
                    logger.info(f"Found {len(signals)} high volatility signals")
                    
                    for signal in signals:
                        # Check if we already have a position in this symbol
                        if signal.symbol not in self.active_positions:
                            result = await self.execute_signal(signal)
                            
                            if result:
                                logger.info(f"✅ Executed: {signal.symbol}")
                            else:
                                logger.warning(f"❌ Failed to execute: {signal.symbol}")
                            
                            await asyncio.sleep(2)  # Delay between executions
                        else:
                            logger.info(f"⏭️  Skipping {signal.symbol} - position already active")
                else:
                    logger.info("No high volatility opportunities found")
                
                # Wait before next scan (shorter intervals for high volatility)
                await asyncio.sleep(30)  # 30-second intervals
                
            except Exception as e:
                logger.error(f"Error in main trading loop: {e}")
                await asyncio.sleep(60)
    
    async def stop_trading(self):
        """Stop the trading strategy"""
        self.running = False
        if self.exchange:
            await self.exchange.close()
        logger.info("High volatility trading strategy stopped")

# Configuration for high volatility strategy
HIGH_VOLATILITY_CONFIG = {
    'max_positions': 5,
    'min_volatility_percentile': 95,
    'hourly_volatility_threshold': 0.05,  # 5%
    'daily_volatility_threshold': 0.15,   # 15%
    'min_confidence': 0.6,
    'max_leverage': 10,
    'max_daily_loss': 0.03,  # 3%
    'max_position_size': 0.05,  # 5% of account
    'scan_interval': 30,  # seconds
}

async def main():
    """Main execution function"""
    strategy = HighVolatilityStrategy(HIGH_VOLATILITY_CONFIG)
    
    try:
        await strategy.start_trading()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await strategy.stop_trading()

if __name__ == "__main__":
    print("HIGH VOLATILITY PAIRS TRADING STRATEGY")
    print("=" * 50)
    print("🎯 Target: Extreme price movements (>5% hourly, >15% daily)")
    print("⚡ Leverage: 3-10x dynamic based on volatility")
    print("🛡️ Risk: Tight stops (0.8-1.5%), 1-2% risk per trade")
    print("📊 Signals: Volatility breakouts + momentum + volume")
    print("=" * 50)
    
    asyncio.run(main())