#!/usr/bin/env python3
"""
AGGRESSIVE LIVE TRADING BOT
Uses ALL available balance with maximum leverage
"""

import asyncio
import ccxt.async_support as ccxt
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Aggressive configuration
AGGRESSIVE_CONFIG = {
    'risk_per_trade': 0.20,  # 20% of balance per trade
    'max_positions': 10,     # Up to 10 positions
    'base_leverage': 30,     # 30x leverage minimum
    'max_leverage': 50,      # 50x maximum
    'correlation_threshold': 0.3,  # Lower threshold for more trades
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AggressiveTradingBot:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'sandbox': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
            'options': {
                'defaultType': 'future'
            }
        })
        
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 
                       'ADA/USDT', 'AVAX/USDT', 'AXS/USDT', 'DOT/USDT', 'LINK/USDT', 'DOGE/USDT']
        self.running = False
        
    async def get_balance(self):
        """Get current balance"""
        balance = await self.exchange.fetch_balance()
        return balance['USDT']['free']
    
    async def place_aggressive_order(self, symbol, side, correlation):
        """Place aggressive order using maximum position size"""
        try:
            balance = await self.get_balance()
            
            # Calculate aggressive position size (20% of balance)
            position_value = balance * AGGRESSIVE_CONFIG['risk_per_trade']
            
            # Determine leverage based on correlation strength
            if abs(correlation) > 0.8:
                leverage = AGGRESSIVE_CONFIG['max_leverage']  # 50x
            elif abs(correlation) > 0.6:
                leverage = 45  # High confidence
            else:
                leverage = AGGRESSIVE_CONFIG['base_leverage']  # 30x
            
            # Get current price
            ticker = await self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            
            # Calculate quantity based on leverage
            quantity = (position_value * leverage) / price
            
            # Round to appropriate precision
            if 'BTC' in symbol:
                quantity = round(quantity, 3)
            elif 'ETH' in symbol:
                quantity = round(quantity, 3)
            else:
                quantity = round(quantity, 1)
            
            # Set leverage first
            await self.exchange.set_leverage(leverage, symbol.replace('/', ''))
            
            # Place market order
            order = await self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=quantity
            )
            
            logger.info(f"AGGRESSIVE ORDER: {symbol} {side} {quantity} @ {leverage}x leverage")
            logger.info(f"Position Value: ${position_value:.2f} | Effective Exposure: ${position_value*leverage:.2f}")
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to place aggressive order for {symbol}: {e}")
            return None
    
    async def start_aggressive_trading(self):
        """Start aggressive trading with maximum risk"""
        self.running = True
        logger.info("STARTING AGGRESSIVE TRADING MODE")
        
        balance = await self.get_balance()
        logger.info(f"Starting Balance: ${balance:.2f} USDT")
        logger.info(f"Risk per trade: {AGGRESSIVE_CONFIG['risk_per_trade']*100}%")
        logger.info(f"Max leverage: {AGGRESSIVE_CONFIG['max_leverage']}x")
        
        trade_count = 0
        
        while self.running and trade_count < 5:  # Limit to 5 aggressive trades initially
            try:
                # Simulate correlation detection (in real system would use actual correlation)
                import random
                
                for symbol in self.symbols[:5]:  # Trade first 5 symbols
                    correlation = random.uniform(-0.9, 0.9)
                    
                    if abs(correlation) > AGGRESSIVE_CONFIG['correlation_threshold']:
                        side = 'buy' if correlation > 0 else 'sell'
                        
                        logger.info(f"📊 Correlation signal: {symbol} = {correlation:.3f}")
                        
                        order = await self.place_aggressive_order(symbol, side, correlation)
                        
                        if order:
                            trade_count += 1
                            await asyncio.sleep(2)  # Short delay between trades
                
                # Wait before next cycle
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"🏁 Completed {trade_count} aggressive trades")

async def main():
    bot = AggressiveTradingBot()
    await bot.start_aggressive_trading()

if __name__ == "__main__":
    print("AGGRESSIVE LIVE TRADING BOT")
    print("WARNING: USES MAXIMUM LEVERAGE AND RISK")
    print("WILL USE ALL AVAILABLE BALANCE")
    print("=" * 50)
    
    asyncio.run(main())