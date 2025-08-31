#!/usr/bin/env python3
"""
ADVANCED VOLATILITY SCANNER AND DETECTION SYSTEM
Real-time monitoring and discovery of high-volatility trading opportunities
across all Binance futures pairs with dynamic pair management.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import ccxt.async_support as ccxt
from enum import Enum
import json
import os
from collections import deque
import heapq
import aiohttp
import time

logger = logging.getLogger(__name__)

class VolatilityState(Enum):
    """Volatility state classifications"""
    DORMANT = "dormant"          # Below 25th percentile
    NORMAL = "normal"            # 25th-75th percentile
    ELEVATED = "elevated"        # 75th-90th percentile
    HIGH = "high"               # 90th-95th percentile
    EXTREME = "extreme"         # Above 95th percentile
    BREAKOUT = "breakout"       # Volatility spike detected

class MarketCondition(Enum):
    """Market condition classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    BREAKOUT = "breakout"
    EXHAUSTION = "exhaustion"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"

@dataclass
class VolatilityProfile:
    """Complete volatility profile for a trading pair"""
    symbol: str
    timestamp: datetime
    
    # Volatility metrics
    atr: float
    atr_percent: float
    historical_vol: float
    parkinson_vol: float
    garman_klass_vol: float
    yang_zhang_vol: float
    
    # Time-based volatility
    vol_5min: float
    vol_15min: float
    vol_1h: float
    vol_4h: float
    vol_24h: float
    vol_7d: float
    vol_30d: float
    
    # Volatility percentiles
    percentile_24h: float
    percentile_7d: float
    percentile_30d: float
    
    # Volume metrics
    volume_24h: float
    volume_spike_ratio: float
    volume_volatility_correlation: float
    
    # Market metrics
    price_change_5min: float
    price_change_1h: float
    price_change_24h: float
    high_low_ratio: float
    
    # Classification
    volatility_state: VolatilityState
    market_condition: MarketCondition
    breakout_detected: bool
    breakout_strength: float
    
    # Scoring
    volatility_score: float
    opportunity_score: float
    risk_score: float
    
    # Additional data
    bid_ask_spread: float
    open_interest: float = 0.0
    funding_rate: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/API"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'atr': self.atr,
            'atr_percent': self.atr_percent,
            'vol_5min': self.vol_5min,
            'vol_1h': self.vol_1h,
            'vol_24h': self.vol_24h,
            'volume_24h': self.volume_24h,
            'volume_spike_ratio': self.volume_spike_ratio,
            'volatility_state': self.volatility_state.value,
            'market_condition': self.market_condition.value,
            'breakout_detected': self.breakout_detected,
            'volatility_score': self.volatility_score,
            'opportunity_score': self.opportunity_score,
            'risk_score': self.risk_score
        }

@dataclass
class TradingOpportunity:
    """Identified trading opportunity with volatility breakout"""
    symbol: str
    detected_at: datetime
    volatility_profile: VolatilityProfile
    entry_signal: str  # 'long' or 'short'
    confidence: float
    expected_move: float
    risk_reward_ratio: float
    priority: int
    expires_at: datetime
    metadata: Dict = field(default_factory=dict)

class AdvancedVolatilityScanner:
    """
    Advanced real-time volatility scanner for discovering and monitoring
    high-volatility trading opportunities across all available pairs
    """
    
    def __init__(self, 
                 api_key: str,
                 api_secret: str,
                 testnet: bool = False,
                 scan_interval: int = 30,
                 max_monitored_pairs: int = 50):
        """
        Initialize the advanced volatility scanner
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet if True
            scan_interval: Seconds between scans
            max_monitored_pairs: Maximum pairs to monitor
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.scan_interval = scan_interval
        self.max_monitored_pairs = max_monitored_pairs
        
        # Exchange connection
        self.exchange = None
        
        # Tracked pairs and their data
        self.monitored_pairs: Set[str] = set()
        self.volatility_profiles: Dict[str, VolatilityProfile] = {}
        self.historical_data: Dict[str, pd.DataFrame] = {}
        self.volatility_history: Dict[str, deque] = {}
        
        # Dynamic pair management
        self.active_pairs: Set[str] = set()
        self.candidate_pairs: Set[str] = set()
        self.dormant_pairs: Set[str] = set()
        self.blacklisted_pairs: Set[str] = set()
        
        # Opportunity tracking
        self.opportunities: List[TradingOpportunity] = []
        self.opportunity_history: deque = deque(maxlen=1000)
        
        # Performance metrics
        self.scan_count = 0
        self.opportunities_found = 0
        self.last_scan_time = None
        self.scan_performance: deque = deque(maxlen=100)
        
        # Configuration
        self.volatility_thresholds = {
            'min_5min': 0.01,      # 1% in 5 minutes
            'min_hourly': 0.05,    # 5% hourly
            'min_daily': 0.10,     # 10% daily
            'breakout_multiplier': 2.0,  # 2x average volatility
            'volume_spike': 2.0,    # 2x average volume
            'min_volume_usd': 10_000_000  # $10M daily volume
        }
        
        # Market regime detection parameters
        self.regime_params = {
            'trend_strength': 0.7,
            'range_threshold': 0.3,
            'exhaustion_rsi': 80,
            'accumulation_volume': 1.5
        }
        
        # Initialize components
        self.running = False
        self.scanner_task = None
        
        logger.info(f"Advanced Volatility Scanner initialized - Monitoring up to {max_monitored_pairs} pairs")
    
    async def initialize(self):
        """Initialize exchange connection and load initial data"""
        try:
            # Initialize exchange
            exchange_class = ccxt.binance
            self.exchange = exchange_class({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True
                }
            })
            
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
            
            # Load markets
            await self.exchange.load_markets()
            
            # Get initial list of futures pairs
            await self._initialize_pair_universe()
            
            logger.info(f"Scanner initialized with {len(self.monitored_pairs)} pairs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize scanner: {e}")
            return False
    
    async def _initialize_pair_universe(self):
        """Initialize the universe of pairs to monitor"""
        try:
            # Get all USDT perpetual futures
            all_symbols = []
            for symbol, market in self.exchange.markets.items():
                if market['quote'] == 'USDT' and market['type'] == 'future':
                    all_symbols.append(symbol)
            
            # Get top pairs by volume
            tickers = await self.exchange.fetch_tickers()
            
            # Sort by 24h volume and filter
            volume_sorted = []
            for symbol in all_symbols:
                if symbol in tickers:
                    ticker = tickers[symbol]
                    if ticker['quoteVolume'] and ticker['quoteVolume'] > self.volatility_thresholds['min_volume_usd']:
                        volume_sorted.append((symbol, ticker['quoteVolume']))
            
            volume_sorted.sort(key=lambda x: x[1], reverse=True)
            
            # Take top N pairs by volume
            top_pairs = [symbol for symbol, _ in volume_sorted[:self.max_monitored_pairs]]
            
            self.monitored_pairs = set(top_pairs)
            self.active_pairs = set(top_pairs[:20])  # Start with top 20
            self.candidate_pairs = set(top_pairs[20:])
            
            # Initialize history tracking
            for symbol in self.monitored_pairs:
                self.volatility_history[symbol] = deque(maxlen=288)  # 24 hours at 5-min intervals
            
            logger.info(f"Initialized with {len(self.active_pairs)} active pairs, "
                       f"{len(self.candidate_pairs)} candidates")
            
        except Exception as e:
            logger.error(f"Error initializing pair universe: {e}")
    
    async def calculate_volatility_metrics(self, symbol: str, ohlcv_data: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive volatility metrics for a symbol
        
        Args:
            symbol: Trading pair symbol
            ohlcv_data: OHLCV data DataFrame
            
        Returns:
            Dictionary of volatility metrics
        """
        try:
            if len(ohlcv_data) < 30:
                return {}
            
            # Basic price data
            high = ohlcv_data['high']
            low = ohlcv_data['low']
            close = ohlcv_data['close']
            open_price = ohlcv_data['open']
            volume = ohlcv_data['volume']
            
            # ATR (Average True Range)
            high_low = high - low
            high_close = np.abs(high - close.shift())
            low_close = np.abs(low - close.shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
            atr_percent = (atr / close.iloc[-1]) * 100
            
            # Historical Volatility (Close-to-Close)
            log_returns = np.log(close / close.shift())
            historical_vol = log_returns.std() * np.sqrt(24 * 365)  # Annualized
            
            # Parkinson Volatility (High-Low)
            parkinson_vol = np.sqrt(np.log(high / low) ** 2).mean() * np.sqrt(24 * 365)
            
            # Garman-Klass Volatility
            gk_vol = np.sqrt(
                0.5 * np.log(high / low) ** 2 - 
                (2 * np.log(2) - 1) * np.log(close / open_price) ** 2
            ).mean() * np.sqrt(24 * 365)
            
            # Yang-Zhang Volatility (most comprehensive)
            overnight_vol = np.log(open_price / close.shift()).std()
            open_close_vol = np.log(close / open_price).std()
            yz_vol = np.sqrt(overnight_vol ** 2 + 0.5 * open_close_vol ** 2) * np.sqrt(24 * 365)
            
            # Time-based volatility
            def calculate_period_volatility(data, periods):
                if len(data) >= periods:
                    period_data = data.iloc[-periods:]
                    returns = np.log(period_data / period_data.shift())
                    return returns.std() * np.sqrt(24 * 365 / periods)
                return 0
            
            vol_5min = calculate_period_volatility(close, 1) if len(close) >= 1 else 0
            vol_15min = calculate_period_volatility(close, 3) if len(close) >= 3 else 0
            vol_1h = calculate_period_volatility(close, 12) if len(close) >= 12 else 0
            vol_4h = calculate_period_volatility(close, 48) if len(close) >= 48 else 0
            vol_24h = calculate_period_volatility(close, 288) if len(close) >= 288 else 0
            
            # Price changes
            price_change_5min = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100 if len(close) >= 2 else 0
            price_change_1h = ((close.iloc[-1] - close.iloc[-12]) / close.iloc[-12]) * 100 if len(close) >= 12 else 0
            price_change_24h = ((close.iloc[-1] - close.iloc[-288]) / close.iloc[-288]) * 100 if len(close) >= 288 else 0
            
            # High-Low ratio
            daily_high = high.iloc[-288:].max() if len(high) >= 288 else high.max()
            daily_low = low.iloc[-288:].min() if len(low) >= 288 else low.min()
            high_low_ratio = (daily_high - daily_low) / daily_low * 100
            
            # Volume analysis
            avg_volume = volume.rolling(window=50).mean().iloc[-1] if len(volume) >= 50 else volume.mean()
            current_volume = volume.iloc[-1]
            volume_spike_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volume-Volatility correlation
            if len(volume) >= 30:
                vol_series = log_returns.rolling(window=12).std()
                vol_corr = volume.iloc[-30:].corr(vol_series.iloc[-30:])
            else:
                vol_corr = 0
            
            return {
                'atr': atr,
                'atr_percent': atr_percent,
                'historical_vol': historical_vol,
                'parkinson_vol': parkinson_vol,
                'garman_klass_vol': gk_vol,
                'yang_zhang_vol': yz_vol,
                'vol_5min': vol_5min,
                'vol_15min': vol_15min,
                'vol_1h': vol_1h,
                'vol_4h': vol_4h,
                'vol_24h': vol_24h,
                'price_change_5min': price_change_5min,
                'price_change_1h': price_change_1h,
                'price_change_24h': price_change_24h,
                'high_low_ratio': high_low_ratio,
                'volume_spike_ratio': volume_spike_ratio,
                'volume_volatility_correlation': vol_corr,
                'current_price': close.iloc[-1],
                'current_volume': current_volume
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics for {symbol}: {e}")
            return {}
    
    def detect_market_regime(self, ohlcv_data: pd.DataFrame, volatility_metrics: Dict) -> MarketCondition:
        """
        Detect current market regime using price action and volatility
        
        Args:
            ohlcv_data: OHLCV data
            volatility_metrics: Calculated volatility metrics
            
        Returns:
            MarketCondition enum
        """
        try:
            if len(ohlcv_data) < 50:
                return MarketCondition.RANGING
            
            close = ohlcv_data['close']
            volume = ohlcv_data['volume']
            
            # Calculate trend strength
            sma_20 = close.rolling(window=20).mean()
            sma_50 = close.rolling(window=50).mean()
            
            current_price = close.iloc[-1]
            sma_20_current = sma_20.iloc[-1]
            sma_50_current = sma_50.iloc[-1]
            
            # Trend detection
            if sma_20_current > sma_50_current * 1.02:
                trend = 'up'
                trend_strength = (sma_20_current - sma_50_current) / sma_50_current
            elif sma_20_current < sma_50_current * 0.98:
                trend = 'down'
                trend_strength = (sma_50_current - sma_20_current) / sma_50_current
            else:
                trend = 'neutral'
                trend_strength = 0
            
            # RSI for exhaustion detection
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Volume analysis
            avg_volume = volume.rolling(window=20).mean().iloc[-1]
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volatility breakout detection
            if volatility_metrics.get('vol_1h', 0) > volatility_metrics.get('vol_24h', 0) * 2:
                return MarketCondition.BREAKOUT
            
            # Exhaustion detection
            if (current_rsi > 80 or current_rsi < 20) and volume_ratio < 0.7:
                return MarketCondition.EXHAUSTION
            
            # Accumulation/Distribution
            if trend == 'neutral' and volume_ratio > 1.5:
                if close.iloc[-5:].mean() > close.iloc[-10:-5].mean():
                    return MarketCondition.ACCUMULATION
                else:
                    return MarketCondition.DISTRIBUTION
            
            # Trending detection
            if trend == 'up' and trend_strength > self.regime_params['trend_strength']:
                return MarketCondition.TRENDING_UP
            elif trend == 'down' and trend_strength > self.regime_params['trend_strength']:
                return MarketCondition.TRENDING_DOWN
            
            # Default to ranging
            return MarketCondition.RANGING
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return MarketCondition.RANGING
    
    def classify_volatility_state(self, volatility_metrics: Dict, historical_volatility: deque) -> VolatilityState:
        """
        Classify current volatility state based on historical context
        
        Args:
            volatility_metrics: Current volatility metrics
            historical_volatility: Historical volatility data
            
        Returns:
            VolatilityState enum
        """
        try:
            current_vol = volatility_metrics.get('vol_1h', 0)
            
            if not historical_volatility or len(historical_volatility) < 10:
                # Not enough history, use absolute thresholds
                if current_vol < 0.02:
                    return VolatilityState.DORMANT
                elif current_vol < 0.05:
                    return VolatilityState.NORMAL
                elif current_vol < 0.10:
                    return VolatilityState.ELEVATED
                elif current_vol < 0.15:
                    return VolatilityState.HIGH
                else:
                    return VolatilityState.EXTREME
            
            # Calculate percentile
            historical_values = [h.get('vol_1h', 0) for h in historical_volatility]
            percentile = percentileofscore(historical_values, current_vol)
            
            # Check for breakout
            avg_vol = np.mean(historical_values)
            if current_vol > avg_vol * self.volatility_thresholds['breakout_multiplier']:
                return VolatilityState.BREAKOUT
            
            # Classify by percentile
            if percentile < 25:
                return VolatilityState.DORMANT
            elif percentile < 75:
                return VolatilityState.NORMAL
            elif percentile < 90:
                return VolatilityState.ELEVATED
            elif percentile < 95:
                return VolatilityState.HIGH
            else:
                return VolatilityState.EXTREME
                
        except Exception as e:
            logger.error(f"Error classifying volatility state: {e}")
            return VolatilityState.NORMAL
    
    def calculate_opportunity_score(self, profile: VolatilityProfile) -> float:
        """
        Calculate opportunity score based on multiple factors
        
        Args:
            profile: Volatility profile
            
        Returns:
            Opportunity score (0-100)
        """
        score = 0.0
        
        # Volatility component (40%)
        if profile.volatility_state == VolatilityState.BREAKOUT:
            score += 40
        elif profile.volatility_state == VolatilityState.EXTREME:
            score += 35
        elif profile.volatility_state == VolatilityState.HIGH:
            score += 25
        elif profile.volatility_state == VolatilityState.ELEVATED:
            score += 15
        
        # Volume component (20%)
        if profile.volume_spike_ratio > 3:
            score += 20
        elif profile.volume_spike_ratio > 2:
            score += 15
        elif profile.volume_spike_ratio > 1.5:
            score += 10
        
        # Market condition component (20%)
        if profile.market_condition == MarketCondition.BREAKOUT:
            score += 20
        elif profile.market_condition in [MarketCondition.TRENDING_UP, MarketCondition.TRENDING_DOWN]:
            score += 15
        elif profile.market_condition == MarketCondition.ACCUMULATION:
            score += 10
        
        # Correlation component (10%)
        if abs(profile.volume_volatility_correlation) > 0.7:
            score += 10
        elif abs(profile.volume_volatility_correlation) > 0.5:
            score += 5
        
        # Percentile component (10%)
        if profile.percentile_24h > 95:
            score += 10
        elif profile.percentile_24h > 90:
            score += 7
        elif profile.percentile_24h > 80:
            score += 4
        
        return min(score, 100)
    
    async def scan_single_pair(self, symbol: str) -> Optional[VolatilityProfile]:
        """
        Scan a single pair for volatility metrics
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            VolatilityProfile or None
        """
        try:
            # Fetch OHLCV data
            timeframe = '5m'
            limit = 500  # ~40 hours of data
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv or len(ohlcv) < 30:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Store historical data
            self.historical_data[symbol] = df
            
            # Calculate volatility metrics
            metrics = await self.calculate_volatility_metrics(symbol, df)
            
            if not metrics:
                return None
            
            # Get historical volatility for this symbol
            historical = self.volatility_history.get(symbol, deque(maxlen=288))
            
            # Classify volatility state
            vol_state = self.classify_volatility_state(metrics, historical)
            
            # Detect market regime
            market_condition = self.detect_market_regime(df, metrics)
            
            # Calculate percentiles
            if len(historical) > 0:
                vol_values_24h = [h.get('vol_1h', 0) for h in list(historical)[-288:]]
                percentile_24h = percentileofscore(vol_values_24h, metrics.get('vol_1h', 0)) if vol_values_24h else 50
            else:
                percentile_24h = 50
            
            # Detect breakout
            breakout_detected = vol_state == VolatilityState.BREAKOUT
            breakout_strength = metrics.get('vol_1h', 0) / metrics.get('vol_24h', 1) if metrics.get('vol_24h', 0) > 0 else 1
            
            # Get additional market data
            ticker = await self.exchange.fetch_ticker(symbol)
            bid_ask_spread = (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100 if ticker['bid'] else 0
            
            # Create volatility profile
            profile = VolatilityProfile(
                symbol=symbol,
                timestamp=datetime.now(),
                atr=metrics.get('atr', 0),
                atr_percent=metrics.get('atr_percent', 0),
                historical_vol=metrics.get('historical_vol', 0),
                parkinson_vol=metrics.get('parkinson_vol', 0),
                garman_klass_vol=metrics.get('garman_klass_vol', 0),
                yang_zhang_vol=metrics.get('yang_zhang_vol', 0),
                vol_5min=metrics.get('vol_5min', 0),
                vol_15min=metrics.get('vol_15min', 0),
                vol_1h=metrics.get('vol_1h', 0),
                vol_4h=metrics.get('vol_4h', 0),
                vol_24h=metrics.get('vol_24h', 0),
                vol_7d=0,  # Would need more data
                vol_30d=0,  # Would need more data
                percentile_24h=percentile_24h,
                percentile_7d=0,  # Would need more data
                percentile_30d=0,  # Would need more data
                volume_24h=ticker.get('quoteVolume', 0),
                volume_spike_ratio=metrics.get('volume_spike_ratio', 1),
                volume_volatility_correlation=metrics.get('volume_volatility_correlation', 0),
                price_change_5min=metrics.get('price_change_5min', 0),
                price_change_1h=metrics.get('price_change_1h', 0),
                price_change_24h=metrics.get('price_change_24h', 0),
                high_low_ratio=metrics.get('high_low_ratio', 0),
                volatility_state=vol_state,
                market_condition=market_condition,
                breakout_detected=breakout_detected,
                breakout_strength=breakout_strength,
                volatility_score=0,  # Will be calculated
                opportunity_score=0,  # Will be calculated
                risk_score=0,  # Will be calculated
                bid_ask_spread=bid_ask_spread
            )
            
            # Calculate scores
            profile.opportunity_score = self.calculate_opportunity_score(profile)
            profile.volatility_score = min(profile.vol_1h * 1000, 100)  # Simple volatility score
            profile.risk_score = min(profile.atr_percent * 10, 100)  # Simple risk score
            
            # Update history
            self.volatility_history[symbol].append(metrics)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error scanning pair {symbol}: {e}")
            return None
    
    async def scan_all_pairs(self) -> List[VolatilityProfile]:
        """
        Scan all monitored pairs for volatility
        
        Returns:
            List of volatility profiles
        """
        start_time = time.time()
        profiles = []
        
        # Scan active pairs first
        tasks = []
        for symbol in self.active_pairs:
            tasks.append(self.scan_single_pair(symbol))
        
        # Then scan candidate pairs
        for symbol in list(self.candidate_pairs)[:10]:  # Scan top 10 candidates
            tasks.append(self.scan_single_pair(symbol))
        
        # Execute scans concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, VolatilityProfile):
                profiles.append(result)
                self.volatility_profiles[result.symbol] = result
        
        # Track performance
        scan_time = time.time() - start_time
        self.scan_performance.append({
            'timestamp': datetime.now(),
            'scan_time': scan_time,
            'pairs_scanned': len(tasks),
            'successful_scans': len(profiles)
        })
        
        self.scan_count += 1
        self.last_scan_time = datetime.now()
        
        logger.info(f"Scanned {len(profiles)} pairs in {scan_time:.2f}s")
        
        return profiles
    
    def identify_opportunities(self, profiles: List[VolatilityProfile]) -> List[TradingOpportunity]:
        """
        Identify trading opportunities from volatility profiles
        
        Args:
            profiles: List of volatility profiles
            
        Returns:
            List of trading opportunities
        """
        opportunities = []
        
        for profile in profiles:
            # Check if meets minimum thresholds
            if (profile.vol_5min < self.volatility_thresholds['min_5min'] and
                profile.vol_1h < self.volatility_thresholds['min_hourly']):
                continue
            
            # Check volume requirements
            if profile.volume_24h < self.volatility_thresholds['min_volume_usd']:
                continue
            
            # Check for high opportunity score
            if profile.opportunity_score < 60:
                continue
            
            # Determine entry signal
            if profile.market_condition == MarketCondition.TRENDING_UP:
                entry_signal = 'long'
                confidence = 0.7
            elif profile.market_condition == MarketCondition.TRENDING_DOWN:
                entry_signal = 'short'
                confidence = 0.7
            elif profile.market_condition == MarketCondition.BREAKOUT:
                # Breakout direction based on recent price change
                if profile.price_change_1h > 0:
                    entry_signal = 'long'
                else:
                    entry_signal = 'short'
                confidence = 0.8
            else:
                # Skip if no clear direction
                continue
            
            # Adjust confidence based on volatility state
            if profile.volatility_state == VolatilityState.EXTREME:
                confidence *= 1.1
            elif profile.volatility_state == VolatilityState.BREAKOUT:
                confidence *= 1.2
            
            confidence = min(confidence, 0.95)
            
            # Calculate expected move and risk/reward
            expected_move = profile.atr_percent * 2  # Expect 2 ATR move
            risk_reward_ratio = 2.5  # Target 2.5:1 RR
            
            # Create opportunity
            opportunity = TradingOpportunity(
                symbol=profile.symbol,
                detected_at=datetime.now(),
                volatility_profile=profile,
                entry_signal=entry_signal,
                confidence=confidence,
                expected_move=expected_move,
                risk_reward_ratio=risk_reward_ratio,
                priority=int(profile.opportunity_score / 10),
                expires_at=datetime.now() + timedelta(hours=1),
                metadata={
                    'volatility_state': profile.volatility_state.value,
                    'market_condition': profile.market_condition.value,
                    'volume_spike': profile.volume_spike_ratio
                }
            )
            
            opportunities.append(opportunity)
            self.opportunities_found += 1
        
        # Sort by priority (highest first)
        opportunities.sort(key=lambda x: x.priority, reverse=True)
        
        return opportunities
    
    async def update_active_pairs(self, profiles: List[VolatilityProfile]):
        """
        Dynamically update active and candidate pairs based on volatility
        
        Args:
            profiles: Recent volatility profiles
        """
        try:
            # Create ranking based on opportunity scores
            ranked_pairs = sorted(profiles, key=lambda x: x.opportunity_score, reverse=True)
            
            # Identify high-opportunity pairs
            high_opportunity = set()
            for profile in ranked_pairs[:15]:  # Top 15 by opportunity
                if profile.opportunity_score >= 50:
                    high_opportunity.add(profile.symbol)
            
            # Check for pairs to remove (low volatility for extended period)
            pairs_to_remove = set()
            for symbol in self.active_pairs:
                if symbol in self.volatility_profiles:
                    profile = self.volatility_profiles[symbol]
                    
                    # Remove if volatility has been low for 24+ hours
                    if (profile.volatility_state == VolatilityState.DORMANT and
                        profile.opportunity_score < 30):
                        
                        # Check historical volatility
                        history = self.volatility_history.get(symbol, deque())
                        if len(history) >= 288:  # 24 hours of data
                            recent_scores = [h.get('vol_1h', 0) for h in list(history)[-288:]]
                            avg_recent_vol = np.mean(recent_scores)
                            if avg_recent_vol < 0.02:  # Less than 2% average volatility
                                pairs_to_remove.add(symbol)
                                logger.info(f"Removing {symbol} from active pairs - low volatility")
            
            # Update active pairs
            self.active_pairs = (self.active_pairs - pairs_to_remove) | high_opportunity
            
            # Ensure we don't exceed max active pairs
            if len(self.active_pairs) > 15:
                # Keep only top 15
                active_profiles = [p for p in profiles if p.symbol in self.active_pairs]
                active_profiles.sort(key=lambda x: x.opportunity_score, reverse=True)
                self.active_pairs = set([p.symbol for p in active_profiles[:15]])
            
            # Update candidate pairs
            all_monitored = set([p.symbol for p in profiles])
            self.candidate_pairs = all_monitored - self.active_pairs - self.dormant_pairs
            
            # Move low-activity pairs to dormant
            for symbol in list(self.candidate_pairs):
                if symbol in self.volatility_profiles:
                    profile = self.volatility_profiles[symbol]
                    if profile.opportunity_score < 20:
                        self.dormant_pairs.add(symbol)
                        self.candidate_pairs.remove(symbol)
            
            logger.info(f"Active pairs updated: {len(self.active_pairs)} active, "
                       f"{len(self.candidate_pairs)} candidates, {len(self.dormant_pairs)} dormant")
            
        except Exception as e:
            logger.error(f"Error updating active pairs: {e}")
    
    async def run_scanner(self):
        """Main scanner loop"""
        logger.info("Starting advanced volatility scanner...")
        self.running = True
        
        while self.running:
            try:
                # Scan all pairs
                profiles = await self.scan_all_pairs()
                
                # Identify opportunities
                opportunities = self.identify_opportunities(profiles)
                
                # Update tracked opportunities
                self.opportunities = opportunities
                for opp in opportunities:
                    self.opportunity_history.append(opp)
                
                # Update active pairs dynamically
                await self.update_active_pairs(profiles)
                
                # Log summary
                if opportunities:
                    logger.info(f"Found {len(opportunities)} opportunities:")
                    for opp in opportunities[:5]:  # Show top 5
                        logger.info(f"  {opp.symbol}: {opp.entry_signal.upper()} "
                                  f"(confidence: {opp.confidence:.2f}, "
                                  f"score: {opp.volatility_profile.opportunity_score:.1f})")
                
                # Sleep before next scan
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                await asyncio.sleep(10)  # Brief pause on error
    
    async def start(self):
        """Start the volatility scanner"""
        if not await self.initialize():
            logger.error("Failed to initialize scanner")
            return False
        
        self.scanner_task = asyncio.create_task(self.run_scanner())
        logger.info("Volatility scanner started successfully")
        return True
    
    async def stop(self):
        """Stop the volatility scanner"""
        logger.info("Stopping volatility scanner...")
        self.running = False
        
        if self.scanner_task:
            self.scanner_task.cancel()
            try:
                await self.scanner_task
            except asyncio.CancelledError:
                pass
        
        if self.exchange:
            await self.exchange.close()
        
        logger.info("Volatility scanner stopped")
    
    def get_top_opportunities(self, limit: int = 10) -> List[TradingOpportunity]:
        """
        Get top trading opportunities by priority
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of top opportunities
        """
        # Filter out expired opportunities
        current_time = datetime.now()
        valid_opportunities = [
            opp for opp in self.opportunities 
            if opp.expires_at > current_time
        ]
        
        # Sort by priority and return top N
        valid_opportunities.sort(key=lambda x: x.priority, reverse=True)
        return valid_opportunities[:limit]
    
    def get_volatility_rankings(self) -> List[Tuple[str, float]]:
        """
        Get volatility rankings for all monitored pairs
        
        Returns:
            List of (symbol, volatility_score) tuples
        """
        rankings = []
        for symbol, profile in self.volatility_profiles.items():
            rankings.append((symbol, profile.volatility_score))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    def get_scanner_status(self) -> Dict:
        """
        Get current scanner status and statistics
        
        Returns:
            Dictionary with scanner status
        """
        return {
            'running': self.running,
            'scan_count': self.scan_count,
            'last_scan': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'active_pairs': list(self.active_pairs),
            'candidate_pairs': list(self.candidate_pairs),
            'dormant_pairs': list(self.dormant_pairs),
            'opportunities_found': self.opportunities_found,
            'current_opportunities': len(self.opportunities),
            'monitored_pairs': len(self.monitored_pairs),
            'performance': {
                'avg_scan_time': np.mean([p['scan_time'] for p in self.scan_performance]) if self.scan_performance else 0,
                'success_rate': np.mean([p['successful_scans'] / p['pairs_scanned'] 
                                        for p in self.scan_performance]) if self.scan_performance else 0
            }
        }
    
    def export_volatility_data(self, filepath: str):
        """
        Export volatility data to JSON file
        
        Args:
            filepath: Path to save the data
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            'scanner_status': self.get_scanner_status(),
            'volatility_profiles': {
                symbol: profile.to_dict() 
                for symbol, profile in self.volatility_profiles.items()
            },
            'opportunities': [
                {
                    'symbol': opp.symbol,
                    'detected_at': opp.detected_at.isoformat(),
                    'entry_signal': opp.entry_signal,
                    'confidence': opp.confidence,
                    'expected_move': opp.expected_move,
                    'priority': opp.priority,
                    'metadata': opp.metadata
                }
                for opp in self.opportunities
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Volatility data exported to {filepath}")