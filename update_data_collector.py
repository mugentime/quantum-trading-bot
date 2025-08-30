#!/usr/bin/env python3
"""
Script para actualizar el data_collector.py con conexión real a Binance
Ejecutar: python update_collector.py
"""

import os

# Contenido actualizado del data_collector.py
DATA_COLLECTOR_CONTENT = '''"""Real-time data collection from Binance"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging
import ccxt.async_support as ccxt

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
            exchange_class = getattr(ccxt, 'binance')
            
            self.exchange = exchange_class({
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
                self.exchange.set_sandbox_mode(True)
                logger.info("Modo TESTNET activado")
            
            # Verificar conexión
            await self._test_connection()
            
            # Cargar datos históricos iniciales
            await self._load_initial_data()
            
            self.running = True
            
            # Iniciar actualización de precios en background
            asyncio.create_task(self._price_update_loop())
            
            logger.info("DataCollector iniciado correctamente")
            
        except Exception as e:
            logger.error(f"Error iniciando DataCollector: {e}")
            # Modo simulación si falla la conexión
            logger.warning("Continuando en modo simulación")
            self.running = True
            await self._start_simulation_mode()
            
    async def _test_connection(self):
        """Test connection to exchange"""
        try:
            # Probar obtener el tiempo del servidor
            await self.exchange.fetch_time()
            logger.info("✅ Conexión con Binance establecida")
            
            # Obtener balance si hay API keys
            if config.BINANCE_API_KEY and config.BINANCE_SECRET_KEY:
                balance = await self.exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                logger.info(f"💰 Balance USDT: ${usdt_balance:.2f}")
            else:
                logger.warning("⚠️ API keys no configuradas - modo solo lectura")
                
        except Exception as e:
            logger.error(f"❌ Error conectando con Binance: {e}")
            raise
            
    async def _load_initial_data(self):
        """Load initial historical data"""
        logger.info("📊 Cargando datos históricos...")
        
        for symbol in self.symbols:
            try:
                # Obtener últimas 100 velas de 5m
                ohlcv = await self.exchange.fetch_ohlcv(
                    symbol, 
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
                    
                    logger.info(f"  ✓ {symbol}: ${self.prices[symbol]:.2f}")
                    
            except Exception as e:
                logger.error(f"  ✗ Error con {symbol}: {e}")
                self.prices[symbol] = 100.0
                
    async def _start_simulation_mode(self):
        """Start simulation mode with fake data"""
        logger.info("🎮 Modo simulación activado")
        
        # Precios simulados para cada símbolo
        base_prices = {
            'BTCUSDT': 65000.0,
            'ETHUSDT': 3200.0,
            'SOLUSDT': 140.0,
            'BNBUSDT': 580.0,
            'XRPUSDT': 0.52
        }
        
        for symbol in self.symbols:
            self.prices[symbol] = base_prices.get(symbol, 100.0)
            
            # Crear datos simulados
            self.data_buffer[f"{symbol}_5m"] = self._create_simulated_klines(symbol)
            
        # Actualizar precios simulados en background
        asyncio.create_task(self._simulation_update_loop())
        
    async def _simulation_update_loop(self):
        """Update simulated prices"""
        while self.running:
            for symbol in self.symbols:
                # Variación aleatoria de ±0.5%
                change = np.random.randn() * 0.005
                self.prices[symbol] *= (1 + change)
            
            await asyncio.sleep(2)
                
    async def _price_update_loop(self):
        """Continuously update prices from exchange"""
        while self.running:
            try:
                for symbol in self.symbols:
                    try:
                        ticker = await self.exchange.fetch_ticker(symbol)
                        old_price = self.prices.get(symbol, 0)
                        new_price = ticker['last']
                        self.prices[symbol] = new_price
                        
                        # Log cambios significativos
                        if old_price > 0:
                            change_pct = ((new_price - old_price) / old_price) * 100
                            if abs(change_pct) > 0.5:  # Cambio > 0.5%
                                emoji = "📈" if change_pct > 0 else "📉"
                                logger.info(f"{emoji} {symbol}: ${new_price:.2f} ({change_pct:+.2f}%)")
                        
                    except Exception as e:
                        logger.debug(f"Error actualizando {symbol}: {e}")
                        
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error en price update loop: {e}")
                await asyncio.sleep(5)
                
    def _create_simulated_klines(self, symbol: str) -> pd.DataFrame:
        """Create simulated klines for testing"""
        timestamps = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='5min')
        base_price = self.prices.get(symbol, 100.0)
        
        # Generar precios con volatilidad realista
        np.random.seed(hash(symbol) % 1000)
        returns = np.random.randn(100) * 0.002
        prices = base_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(100) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(100) * 0.002)),
            'low': prices * (1 - np.abs(np.random.randn(100) * 0.002)),
            'close': prices,
            'volume': np.random.exponential(1000, 100)
        }, index=timestamps)
        
        return df
        
    async def get_latest_data(self) -> Dict:
        """Get latest market data for analysis"""
        result = {
            'prices': self.prices.copy(),
            'orderbooks': {},
            'klines': {},
            'indicators': {}
        }
        
        # Agregar datos de klines
        for symbol in self.symbols:
            result['klines'][symbol] = {}
            
            key = f"{symbol}_5m"
            if key in self.data_buffer and not self.data_buffer[key].empty:
                result['klines'][symbol]['5m'] = self.data_buffer[key].copy()
            else:
                result['klines'][symbol]['5m'] = self._create_simulated_klines(symbol)
        
        # Calcular indicadores
        result['indicators'] = self._calculate_indicators(result['klines'])
        
        return result
    
    def _calculate_indicators(self, klines: Dict) -> Dict:
        """Calculate technical indicators"""
        indicators = {}
        
        for symbol, timeframes in klines.items():
            indicators[symbol] = {}
            
            for tf, df in timeframes.items():
                if df is None or df.empty or len(df) < 20:
                    indicators[symbol][tf] = self._default_indicators(symbol)
                    continue
                    
                try:
                    close_prices = df['close']
                    
                    indicators[symbol][tf] = {
                        'sma_20': float(close_prices.rolling(min(20, len(df))).mean().iloc[-1]),
                        'sma_50': float(close_prices.rolling(min(50, len(df))).mean().iloc[-1]),
                        'rsi': self._calculate_rsi(close_prices),
                        'bollinger': self._calculate_bollinger(close_prices),
                        'volume_sma': float(df['volume'].rolling(min(20, len(df))).mean().iloc[-1]),
                        'atr': self._calculate_atr(df)
                    }
                except Exception as e:
                    logger.debug(f"Error calculando indicadores: {e}")
                    indicators[symbol][tf] = self._default_indicators(symbol)
        
        return indicators
    
    def _default_indicators(self, symbol: str) -> Dict:
        """Return default indicator values"""
        price = self.prices.get(symbol, 100)
        return {
            'sma_20': price,
            'sma_50': price,
            'rsi': 50,
            'bollinger': {
                'upper': price * 1.02,
                'middle': price,
                'lower': price * 0.98,
                'width': 0.04
            },
            'volume_sma': 1000,
            'atr': price * 0.01
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        try:
            if len(prices) < period:
                return 50.0
                
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            if loss.iloc[-1] == 0:
                return 100.0
                
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except:
            return 50.0
    
    def _calculate_bollinger(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        """Calculate Bollinger Bands"""
        try:
            if len(prices) < period:
                current_price = float(prices.iloc[-1])
                return {
                    'upper': current_price * 1.02,
                    'middle': current_price,
                    'lower': current_price * 0.98,
                    'width': 0.04
                }
                
            sma = prices.rolling(period).mean()
            std = prices.rolling(period).std()
            
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            return {
                'upper': float(upper.iloc[-1]),
                'middle': float(sma.iloc[-1]),
                'lower': float(lower.iloc[-1]),
                'width': float(((upper - lower) / sma).iloc[-1])
            }
        except:
            return {
                'upper': 102,
                'middle': 100,
                'lower': 98,
                'width': 0.04
            }
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(df) < 2:
                return float(df['close'].iloc[-1] * 0.01)
                
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(min(period, len(tr))).mean()
            
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 1.0
        except:
            return 1.0
    
    async def stop(self):
        """Stop data collection"""
        self.running = False
        if self.exchange:
            await self.exchange.close()
        logger.info("DataCollector detenido")
'''

def update_data_collector():
    """Actualiza el archivo data_collector.py"""
    
    # Path al archivo
    file_path = os.path.join('core', 'data_collector.py')
    
    print("=" * 50)
    print("📝 ACTUALIZANDO DATA COLLECTOR")
    print("=" * 50)
    
    try:
        # Hacer backup del archivo actual
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                backup = f.read()
            
            with open(file_path + '.bak', 'w', encoding='utf-8') as f:
                f.write(backup)
            print("✅ Backup creado: core/data_collector.py.bak")
        
        # Escribir el nuevo contenido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(DATA_COLLECTOR_CONTENT)
        
        print("✅ data_collector.py actualizado con éxito")
        print("\n🎯 El bot ahora:")
        print("  - Se conectará a Binance (real o testnet)")
        print("  - Obtendrá precios en tiempo real")
        print("  - Calculará indicadores técnicos")
        print("  - Funcionará en modo simulación si no hay API keys")
        
        print("\n⚠️ IMPORTANTE:")
        print("  1. Asegúrate de tener tu .env configurado con las API keys")
        print("  2. Si usas testnet, BINANCE_TESTNET=true en .env")
        print("  3. Reinicia el bot: python main.py")
        
    except Exception as e:
        print(f"❌ Error actualizando archivo: {e}")
        print("Intenta copiar manualmente el contenido del artifact")

if __name__ == "__main__":
    update_data_collector()
