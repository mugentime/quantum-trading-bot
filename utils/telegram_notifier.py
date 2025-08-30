import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from core.config.settings import config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Telegram notification service for trading alerts"""
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Notifications will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            logger.debug("Telegram not configured, skipping message")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.debug("Telegram message sent successfully")
                        return True
                    else:
                        logger.error(f"Failed to send Telegram message: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_buy_order_alert(self, symbol: str, price: float, quantity: float, 
                                  stop_loss: float, take_profit: float, 
                                  reason: str = "") -> bool:
        """Send buy order notification"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
🟢 <b>BUY ORDER PLACED</b> 🟢

📈 Symbol: <b>{symbol}</b>
💰 Price: <b>${price:.6f}</b>
📊 Quantity: <b>{quantity:.6f}</b>
🛑 Stop Loss: <b>${stop_loss:.6f}</b>
🎯 Take Profit: <b>${take_profit:.6f}</b>
⏰ Time: <b>{timestamp}</b>

{f'📝 Reason: {reason}' if reason else ''}

🤖 Quantum Trading Bot
        """
        
        return await self.send_message(message.strip())
    
    async def send_sell_order_alert(self, symbol: str, price: float, quantity: float, 
                                   pnl: float, pnl_percent: float, 
                                   reason: str = "") -> bool:
        """Send sell order notification"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        order_type = "PROFIT" if pnl >= 0 else "LOSS"
        
        message = f"""
{pnl_emoji} <b>SELL ORDER - {order_type}</b> {pnl_emoji}

📉 Symbol: <b>{symbol}</b>
💰 Price: <b>${price:.6f}</b>
📊 Quantity: <b>{quantity:.6f}</b>
💵 P&L: <b>${pnl:.2f} ({pnl_percent:+.2f}%)</b>
⏰ Time: <b>{timestamp}</b>

{f'📝 Reason: {reason}' if reason else ''}

🤖 Quantum Trading Bot
        """
        
        return await self.send_message(message.strip())
    
    async def send_price_alert(self, symbol: str, current_price: float, 
                              change_percent: float, timeframe: str = "1h") -> bool:
        """Send price movement notification"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        trend_emoji = "📈" if change_percent >= 0 else "📉"
        change_emoji = "🟢" if change_percent >= 0 else "🔴"
        
        message = f"""
{trend_emoji} <b>PRICE ALERT</b> {trend_emoji}

💎 Symbol: <b>{symbol}</b>
💰 Price: <b>${current_price:.6f}</b>
{change_emoji} Change: <b>{change_percent:+.2f}%</b> ({timeframe})
⏰ Time: <b>{timestamp}</b>

🤖 Quantum Trading Bot
        """
        
        return await self.send_message(message.strip())
    
    async def send_error_alert(self, error_type: str, error_message: str, 
                              symbol: Optional[str] = None) -> bool:
        """Send error notification"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
🚨 <b>ERROR ALERT</b> 🚨

⚠️ Type: <b>{error_type}</b>
{f'💎 Symbol: <b>{symbol}</b>' if symbol else ''}
💬 Message: <b>{error_message}</b>
⏰ Time: <b>{timestamp}</b>

🤖 Quantum Trading Bot
        """
        
        return await self.send_message(message.strip())
    
    async def send_status_update(self, active_positions: int, total_pnl: float, 
                                win_rate: float, daily_trades: int) -> bool:
        """Send daily status update"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
        
        message = f"""
📊 <b>DAILY STATUS UPDATE</b> 📊

🔄 Active Positions: <b>{active_positions}</b>
{pnl_emoji} Total P&L: <b>${total_pnl:.2f}</b>
📈 Win Rate: <b>{win_rate:.1f}%</b>
📋 Trades Today: <b>{daily_trades}</b>
⏰ Time: <b>{timestamp}</b>

🤖 Quantum Trading Bot
        """
        
        return await self.send_message(message.strip())
    
    def send_message_sync(self, message: str) -> bool:
        """Synchronous wrapper for sending messages"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_message(message))
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.send_message(message))
            finally:
                loop.close()

# Global instance
telegram_notifier = TelegramNotifier()