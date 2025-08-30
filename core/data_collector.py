"""Real-time data collection from Binance"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None
    np = None

try:
    import ccxt.async_support as ccxt
except ImportError:
    import ccxt

from .config.settings import config
from .data_authenticity_validator import authenticity_validator, DataAuthenticityError

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.exchange = None
        self.data_buffer = {}
        self.running = False
        self.prices = {}
        self.last_update = {}
        self.update_tasks = []
        
        # Initialize data buffer for each symbol
        for symbol in symbols:
            self.data_buffer[symbol] = []
            self.prices[symbol] = {}
            self.last_update[symbol] = None
            
        logger.info(f"DataCollector initialized with: {symbols}")
    
    async def start(self):
        """Start data collection"""
        logger.info("Starting DataCollector...")
        
        # Initialize exchange
        self.exchange = ccxt.binance({
            'apiKey': config.BINANCE_API_KEY,
            'secret': config.BINANCE_SECRET_KEY,
            'sandbox': config.BINANCE_TESTNET,  # Use testnet if configured
            'enableRateLimit': True,
        })
        
        self.running = True
        
        # Start data collection tasks for each symbol
        for symbol in self.symbols:
            task = asyncio.create_task(self._collect_data_for_symbol(symbol))
            self.update_tasks.append(task)
        
        logger.info("DataCollector started successfully")
    
    async def stop(self):
        """Stop data collection"""
        logger.info("Stopping DataCollector...")
        self.running = False
        
        # Cancel all tasks
        for task in self.update_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        if self.update_tasks:
            await asyncio.gather(*self.update_tasks, return_exceptions=True)
        
        # Close exchange connection
        if self.exchange:
            await self.exchange.close()
        
        logger.info("DataCollector stopped")
    
    async def _collect_data_for_symbol(self, symbol: str):
        """Collect data for a specific symbol"""
        while self.running:
            try:
                # Fetch ticker data
                ticker = await self.exchange.fetch_ticker(symbol)
                
                # SECURITY: Validate ticker data authenticity
                try:
                    ticker_data = {
                        'symbol': symbol,
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'last': ticker['last'],
                        'timestamp': ticker['timestamp'],
                        'volume': ticker['quoteVolume']
                    }
                    if not authenticity_validator.validate_market_data(ticker_data, f"ticker_{symbol}"):
                        logger.error(f"SECURITY ALERT: Ticker data validation failed for {symbol}")
                        continue
                except DataAuthenticityError as e:
                    logger.error(f"DATA AUTHENTICITY ERROR for {symbol}: {e}")
                    continue
                
                # Update prices
                self.prices[symbol] = {
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'last': ticker['last'],
                    'timestamp': ticker['timestamp'],
                    'volume': ticker['quoteVolume']
                }
                
                # Add to buffer
                self.data_buffer[symbol].append({
                    'timestamp': datetime.now(),
                    'price': ticker['last'],
                    'volume': ticker['baseVolume'],
                    'bid': ticker['bid'],
                    'ask': ticker['ask']
                })
                
                # Keep buffer size manageable (last 1000 points)
                if len(self.data_buffer[symbol]) > 1000:
                    self.data_buffer[symbol] = self.data_buffer[symbol][-1000:]
                
                self.last_update[symbol] = datetime.now()
                
                # Sleep to avoid rate limits
                await asyncio.sleep(1)  # 1 second between updates
                
            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def get_latest_data(self) -> Dict:
        """Get the latest market data for all symbols"""
        if not self.running:
            return {}
        
        latest_data = {}
        
        for symbol in self.symbols:
            if symbol in self.prices and self.prices[symbol]:
                latest_data[symbol] = self.prices[symbol].copy()
            else:
                latest_data[symbol] = None
        
        return latest_data
    
    def get_historical_prices(self, symbol: str, lookback_minutes: int = 50) -> Optional[List[float]]:
        """Get historical prices for correlation calculation"""
        if symbol not in self.data_buffer:
            return None
        
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        
        # Filter data points within the lookback period
        recent_data = [
            point['price'] for point in self.data_buffer[symbol]
            if point['timestamp'] >= cutoff_time and point['price'] is not None
        ]
        
        return recent_data if len(recent_data) >= 10 else None  # Need at least 10 points
    
    def get_data_health(self) -> Dict:
        """Get health status of data feeds"""
        health = {}
        current_time = datetime.now()
        
        for symbol in self.symbols:
            if symbol in self.last_update and self.last_update[symbol]:
                age = (current_time - self.last_update[symbol]).total_seconds()
                health[symbol] = {
                    'last_update_seconds_ago': age,
                    'healthy': age < 10,  # Consider healthy if updated in last 10 seconds
                    'buffer_size': len(self.data_buffer.get(symbol, []))
                }
            else:
                health[symbol] = {
                    'last_update_seconds_ago': None,
                    'healthy': False,
                    'buffer_size': 0
                }
        
        return health
