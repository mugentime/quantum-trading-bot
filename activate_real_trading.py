#!/usr/bin/env python3
"""
Script para activar el trading real con las API keys de Binance Testnet
Ejecutar: python activate_trading.py
"""

import os
import sys

print("=" * 60)
print("🚀 ACTIVANDO CONEXIÓN REAL CON BINANCE TESTNET")
print("=" * 60)

# ============== DATA COLLECTOR ACTUALIZADO ==============
data_collector_content = '''"""Real-time data collection from Binance"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging

try:
    import ccxt.async_support as ccxt
except ImportError:
    import ccxt

from config.settings import config

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.exchange = None
        self.data_buffer = {}
        self.orderbook_data = {}
        self.running = False
        self.prices = {}
        logger.info(f"DataCollector inicializado con símbolos: {symbols}")
        
    async def start(self):
        """Initialize and start data collection"""
        try:
            # Inicializar exchange de Binance
            self.exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Para futuros
                    'adjustForTimeDifference': True,
                }
            })
            
            # Si es testnet, cambiar URLs
            if config.BINANCE_TESTNET:
                self.exchange.urls['api'] = {
                    'public': 'https://testnet.binancefuture.com/fapi/v1',
                    'private': 'https://testnet.binancefuture.com/fapi/v1',
                    'fapiPublic': 'https://testnet.binancefuture.com/fapi/v1',
                    'fapiPrivate': 'https://testnet.binancefuture.com/fapi/v1'
                }
                logger.info("🌐 Modo TESTNET activado")
            
            # Verificar conexión
            await self._test_connection()
            
            # Cargar datos históricos iniciales
            await self._load_initial_data()
            
            self.running = True
            
            # Iniciar actualización de precios en background
            asyncio.create_task(self._price_update_loop())
            
            logger.info("✅ DataCollector iniciado correctamente")
            
        except Exception as e:
            logger.error(f"Error iniciando DataCollector: {e}")
            # No fallback to simulation - fail immediately
            logger.critical("❌ Cannot start trading without live data connection")
            self.running = False
            raise Exception("Trading aborted: No live data connection available")
            
    async def _test_connection(self):
        """Test connection to exchange"""
        try:
            # Probar obtener el tiempo del servidor
            server_time = await self.exchange.fetch_time()
            logger.info(f"✅ Conexión establecida - Server time: {datetime.fromtimestamp(server_time/1000)}")
            
            # Obtener balance
            try:
                balance = await self.exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                logger.info(f"💰 Balance USDT (Testnet): ${usdt_balance:.2f}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo obtener balance: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error conectando con Binance: {e}")
            raise
            
    async def _load_initial_data(self):
        """Load initial historical data"""
        logger.info("📊 Cargando datos históricos...")
        
        for symbol in self.symbols:
            try:
                # Para testnet, usar símbolos que existan
                test_symbol = symbol
                if config.BINANCE_TESTNET and symbol not in ['BTCUSDT', 'ETHUSDT']:
                    test_symbol = 'BTCUSDT'  # Usar BTC como fallback en testnet
                
                # Obtener últimas 100 velas de 5m
                ohlcv = await self.exchange.fetch_ohlcv(
                    test_symbol, 
                    timeframe='5m', 
                    limit=100
                )
                
                if ohlcv:
                    df = pd.DataFrame(
                        ohlcv, 
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # Guardar en buffer
                    self.data_buffer[f"{symbol}_5m"] = df
                    
                    # Guardar último precio
                    self.prices[symbol] = float(df['close'].iloc[-1])
                    
                    logger.info(f"  ✓ {symbol}: ${self.prices[symbol]:,.2f}")
                    
            except Exception as e:
                logger.warning(f"  ⚠️ {symbol}: Usando precio simulado - {str(e)[:50]}")
                # Log error and skip symbol - no simulation fallback
                logger.error(f"  ❌ {symbol}: Failed to load data - {str(e)}")
                # Mark as unhealthy - do not trade this symbol
                continue
                
    async def _price_update_loop(self):
        """Continuously update prices from exchange"""
        update_count = 0
        
        while self.running:
            try:
                update_count += 1
                
                for symbol in self.symbols:
                    try:
                        # En testnet, algunos símbolos pueden no existir
                        test_symbol = symbol
                        if config.BINANCE_TESTNET and symbol not in ['BTCUSDT', 'ETHUSDT']:
                            test_symbol = 'BTCUSDT'
                        
                        ticker = await self.exchange.fetch_ticker(test_symbol)
                        old_price = self.prices.get(symbol, 0)
                        new_price = ticker['last']
                        self.prices[symbol] = new_price
                        
                        # Log cada 10 actualizaciones o si hay cambio significativo
                        if update_count % 10 == 0 or old_price == 0:
                            change_pct = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0
                            emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
                            logger.info(f"{emoji} {symbol}: ${new_price:,.2f} ({change_pct:+.2f}%)")
                        
                    except Exception as e:
                        # Mantener precio anterior si falla
                        pass
                        
                await asyncio.sleep(5)  # Actualizar cada 5 segundos
                
            except Exception as e:
                logger.error(f"Error en price update loop: {e}")
                await asyncio.sleep(10)
                
    def _create_simulated_klines(self, symbol: str) -> pd.DataFrame:
        """Create simulated klines for testing"""
        timestamps = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='5min')
        base_price = self.prices.get(symbol, 100.0)
        
        # Generar precios con volatilidad realista
        np.random.seed(hash(symbol) % 1000)
        returns 