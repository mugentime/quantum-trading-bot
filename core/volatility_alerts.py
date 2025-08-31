#!/usr/bin/env python3
"""
ADVANCED VOLATILITY ALERT SYSTEM
Intelligent alerting system for volatility breakouts and trading opportunities
with multiple notification channels and smart filtering.
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from collections import deque, defaultdict
import os
import time

from core.volatility_scanner import VolatilityProfile, TradingOpportunity, VolatilityState, MarketCondition

logger = logging.getLogger(__name__)

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    VOLATILITY_BREAKOUT = "volatility_breakout"
    HIGH_VOLUME_SPIKE = "high_volume_spike"
    OPPORTUNITY_DETECTED = "opportunity_detected"
    MARKET_REGIME_CHANGE = "market_regime_change"
    PRICE_MOVEMENT = "price_movement"
    SYSTEM_EVENT = "system_event"

class NotificationChannel(Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"
    DISCORD = "discord"
    SLACK = "slack"

@dataclass
class AlertRule:
    """Configuration for alert triggering rules"""
    id: str
    name: str
    alert_type: AlertType
    enabled: bool = True
    
    # Trigger conditions
    min_volatility_score: float = 0
    min_opportunity_score: float = 0
    required_states: List[VolatilityState] = field(default_factory=list)
    required_conditions: List[MarketCondition] = field(default_factory=list)
    min_confidence: float = 0
    volume_spike_threshold: float = 0
    price_change_threshold: float = 0
    
    # Filtering
    symbol_whitelist: Set[str] = field(default_factory=set)
    symbol_blacklist: Set[str] = field(default_factory=set)
    min_volume_usd: float = 0
    max_risk_score: float = 100
    
    # Rate limiting
    cooldown_seconds: int = 300  # 5 minutes between alerts for same pair
    max_alerts_per_hour: int = 20
    
    # Notification settings
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    priority: AlertPriority = AlertPriority.MEDIUM
    
    def matches_profile(self, profile: VolatilityProfile) -> bool:
        """Check if profile matches this alert rule"""
        # Check symbol filters
        if self.symbol_whitelist and profile.symbol not in self.symbol_whitelist:
            return False
        if profile.symbol in self.symbol_blacklist:
            return False
        
        # Check basic thresholds
        if profile.volatility_score < self.min_volatility_score:
            return False
        if profile.opportunity_score < self.min_opportunity_score:
            return False
        if profile.volume_24h < self.min_volume_usd:
            return False
        if profile.risk_score > self.max_risk_score:
            return False
        
        # Check states and conditions
        if self.required_states and profile.volatility_state not in self.required_states:
            return False
        if self.required_conditions and profile.market_condition not in self.required_conditions:
            return False
        
        # Check specific thresholds based on alert type
        if self.alert_type == AlertType.VOLATILITY_BREAKOUT:
            return profile.breakout_detected
        elif self.alert_type == AlertType.HIGH_VOLUME_SPIKE:
            return profile.volume_spike_ratio >= self.volume_spike_threshold
        elif self.alert_type == AlertType.PRICE_MOVEMENT:
            return abs(profile.price_change_1h) >= self.price_change_threshold
        
        return True
    
    def matches_opportunity(self, opportunity: TradingOpportunity) -> bool:
        """Check if opportunity matches this alert rule"""
        if self.alert_type != AlertType.OPPORTUNITY_DETECTED:
            return False
        
        if opportunity.confidence < self.min_confidence:
            return False
        
        return self.matches_profile(opportunity.volatility_profile)

@dataclass
class Alert:
    """Individual alert instance"""
    id: str
    rule_id: str
    alert_type: AlertType
    priority: AlertPriority
    symbol: str
    title: str
    message: str
    data: Dict
    created_at: datetime
    expires_at: Optional[datetime] = None
    sent_channels: Set[NotificationChannel] = field(default_factory=set)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'alert_type': self.alert_type.value,
            'priority': self.priority.value,
            'symbol': self.symbol,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'sent_channels': [ch.value for ch in self.sent_channels],
            'acknowledged': self.acknowledged
        }

class TelegramNotifier:
    """Telegram notification handler"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via Telegram"""
        try:
            # Format message
            message = f"🚨 *{alert.title}*\n\n"
            message += f"*Symbol:* `{alert.symbol}`\n"
            message += f"*Priority:* {alert.priority.value.upper()}\n"
            message += f"*Type:* {alert.alert_type.value.replace('_', ' ').title()}\n\n"
            message += alert.message
            
            # Add data if available
            if alert.data:
                message += "\n\n*Details:*\n"
                for key, value in alert.data.items():
                    if isinstance(value, float):
                        message += f"• {key.replace('_', ' ').title()}: {value:.2f}\n"
                    else:
                        message += f"• {key.replace('_', ' ').title()}: {value}\n"
            
            message += f"\n⏰ {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            # Send message
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Telegram alert sent for {alert.symbol}")
                        return True
                    else:
                        logger.error(f"Failed to send Telegram alert: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False

class DiscordNotifier:
    """Discord notification handler"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via Discord webhook"""
        try:
            # Color based on priority
            colors = {
                AlertPriority.LOW: 0x00ff00,      # Green
                AlertPriority.MEDIUM: 0xffff00,   # Yellow
                AlertPriority.HIGH: 0xff8000,     # Orange
                AlertPriority.CRITICAL: 0xff0000  # Red
            }
            
            # Create embed
            embed = {
                "title": alert.title,
                "description": alert.message,
                "color": colors.get(alert.priority, 0x00ff00),
                "timestamp": alert.created_at.isoformat(),
                "fields": [
                    {"name": "Symbol", "value": alert.symbol, "inline": True},
                    {"name": "Priority", "value": alert.priority.value.upper(), "inline": True},
                    {"name": "Type", "value": alert.alert_type.value.replace('_', ' ').title(), "inline": True}
                ]
            }
            
            # Add data fields
            if alert.data:
                for key, value in list(alert.data.items())[:10]:  # Limit fields
                    if isinstance(value, float):
                        embed["fields"].append({
                            "name": key.replace('_', ' ').title(),
                            "value": f"{value:.2f}",
                            "inline": True
                        })
            
            payload = {
                "embeds": [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Discord alert sent for {alert.symbol}")
                        return True
                    else:
                        logger.error(f"Failed to send Discord alert: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            return False

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, recipient: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipient = recipient
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.username
            msg['To'] = self.recipient
            msg['Subject'] = f"Volatility Alert: {alert.title}"
            
            # HTML body
            html_body = f"""
            <html>
            <body>
            <h2>{alert.title}</h2>
            <p><strong>Symbol:</strong> {alert.symbol}</p>
            <p><strong>Priority:</strong> {alert.priority.value.upper()}</p>
            <p><strong>Type:</strong> {alert.alert_type.value.replace('_', ' ').title()}</p>
            <p><strong>Time:</strong> {alert.created_at}</p>
            
            <h3>Message:</h3>
            <p>{alert.message}</p>
            
            <h3>Details:</h3>
            <table border="1" style="border-collapse: collapse;">
            """
            
            if alert.data:
                for key, value in alert.data.items():
                    html_body += f"<tr><td><strong>{key.replace('_', ' ').title()}</strong></td><td>{value}</td></tr>"
            
            html_body += """
            </table>
            </body>
            </html>
            """
            
            msg.attach(MimeText(html_body, 'html'))
            
            # Send email (run in thread to avoid blocking)
            def send_email():
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_email)
            
            logger.info(f"Email alert sent for {alert.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

class WebhookNotifier:
    """Generic webhook notification handler"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook"""
        try:
            payload = alert.to_dict()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload, headers=self.headers) as response:
                    if 200 <= response.status < 300:
                        logger.info(f"Webhook alert sent for {alert.symbol}")
                        return True
                    else:
                        logger.error(f"Failed to send webhook alert: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
            return False

class VolatilityAlertSystem:
    """Main volatility alert system"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: deque = deque(maxlen=1000)
        self.alert_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Rate limiting
        self.alert_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.last_alert_time: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        
        # Notification channels
        self.notifiers: Dict[NotificationChannel, object] = {}
        
        # Statistics
        self.alerts_sent = 0
        self.alerts_suppressed = 0
        self.start_time = datetime.now()
        
        # Initialize default rules
        self._create_default_rules()
        
        logger.info("Volatility Alert System initialized")
    
    def _create_default_rules(self):
        """Create default alert rules"""
        
        # High volatility breakout rule
        self.add_rule(AlertRule(
            id="volatility_breakout_high",
            name="High Volatility Breakout",
            alert_type=AlertType.VOLATILITY_BREAKOUT,
            min_volatility_score=70,
            required_states=[VolatilityState.BREAKOUT, VolatilityState.EXTREME],
            min_volume_usd=5_000_000,
            notification_channels=[NotificationChannel.TELEGRAM, NotificationChannel.DISCORD],
            priority=AlertPriority.HIGH,
            cooldown_seconds=600  # 10 minutes
        ))
        
        # Volume spike rule
        self.add_rule(AlertRule(
            id="volume_spike_major",
            name="Major Volume Spike",
            alert_type=AlertType.HIGH_VOLUME_SPIKE,
            volume_spike_threshold=3.0,
            min_volume_usd=10_000_000,
            notification_channels=[NotificationChannel.TELEGRAM],
            priority=AlertPriority.MEDIUM,
            cooldown_seconds=300
        ))
        
        # Trading opportunity rule
        self.add_rule(AlertRule(
            id="high_confidence_opportunity",
            name="High Confidence Trading Opportunity",
            alert_type=AlertType.OPPORTUNITY_DETECTED,
            min_confidence=0.8,
            min_opportunity_score=75,
            notification_channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEBHOOK],
            priority=AlertPriority.HIGH,
            cooldown_seconds=180  # 3 minutes
        ))
        
        # Market regime change rule
        self.add_rule(AlertRule(
            id="regime_change_breakout",
            name="Market Regime Change to Breakout",
            alert_type=AlertType.MARKET_REGIME_CHANGE,
            required_conditions=[MarketCondition.BREAKOUT],
            min_volatility_score=60,
            notification_channels=[NotificationChannel.TELEGRAM],
            priority=AlertPriority.MEDIUM
        ))
    
    def add_notifier(self, channel: NotificationChannel, notifier):
        """Add notification channel"""
        self.notifiers[channel] = notifier
        logger.info(f"Added {channel.value} notifier")
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def update_rule(self, rule_id: str, updates: Dict):
        """Update alert rule"""
        if rule_id in self.rules:
            rule = self.rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            logger.info(f"Updated alert rule: {rule_id}")
    
    def _should_suppress_alert(self, rule: AlertRule, symbol: str) -> bool:
        """Check if alert should be suppressed due to rate limiting"""
        now = datetime.now()
        rule_key = f"{rule.id}:{symbol}"
        
        # Check cooldown period
        if rule_key in self.last_alert_time.get(rule.id, {}):
            last_time = self.last_alert_time[rule.id][rule_key]
            if (now - last_time).total_seconds() < rule.cooldown_seconds:
                return True
        
        # Check hourly rate limit
        hour_ago = now - timedelta(hours=1)
        recent_alerts = [
            t for t in self.alert_counts[rule.id] 
            if t > hour_ago
        ]
        
        if len(recent_alerts) >= rule.max_alerts_per_hour:
            return True
        
        return False
    
    def _generate_alert_message(self, rule: AlertRule, profile: VolatilityProfile) -> str:
        """Generate alert message based on rule and profile"""
        if rule.alert_type == AlertType.VOLATILITY_BREAKOUT:
            return f"Volatility breakout detected! {profile.symbol} showing {profile.volatility_state.value} volatility with {profile.breakout_strength:.1f}x breakout strength."
        
        elif rule.alert_type == AlertType.HIGH_VOLUME_SPIKE:
            return f"High volume spike detected! {profile.symbol} volume is {profile.volume_spike_ratio:.1f}x the average."
        
        elif rule.alert_type == AlertType.PRICE_MOVEMENT:
            direction = "up" if profile.price_change_1h > 0 else "down"
            return f"Significant price movement! {profile.symbol} moved {abs(profile.price_change_1h):.2f}% {direction} in the last hour."
        
        elif rule.alert_type == AlertType.MARKET_REGIME_CHANGE:
            return f"Market regime change detected! {profile.symbol} switched to {profile.market_condition.value.replace('_', ' ')} condition."
        
        else:
            return f"Alert triggered for {profile.symbol} - {rule.name}"
    
    async def check_volatility_profile(self, profile: VolatilityProfile):
        """Check volatility profile against all rules and generate alerts"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if not rule.matches_profile(profile):
                continue
            
            # Check rate limiting
            if self._should_suppress_alert(rule, profile.symbol):
                self.alerts_suppressed += 1
                continue
            
            # Generate alert
            alert_id = f"{rule.id}_{profile.symbol}_{int(time.time())}"
            
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                alert_type=rule.alert_type,
                priority=rule.priority,
                symbol=profile.symbol,
                title=f"{rule.name} - {profile.symbol}",
                message=self._generate_alert_message(rule, profile),
                data={
                    'volatility_score': profile.volatility_score,
                    'opportunity_score': profile.opportunity_score,
                    'volatility_state': profile.volatility_state.value,
                    'market_condition': profile.market_condition.value,
                    'price_change_1h': profile.price_change_1h,
                    'volume_spike_ratio': profile.volume_spike_ratio,
                    'breakout_detected': profile.breakout_detected
                },
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1)
            )
            
            # Send alert
            await self._send_alert(alert, rule.notification_channels)
            
            # Update rate limiting
            now = datetime.now()
            if rule.id not in self.last_alert_time:
                self.last_alert_time[rule.id] = {}
            self.last_alert_time[rule.id][f"{rule.id}:{profile.symbol}"] = now
            self.alert_counts[rule.id].append(now)
            
            # Store alert
            self.alerts.append(alert)
            self.alert_history[profile.symbol].append(alert)
            self.alerts_sent += 1
    
    async def check_trading_opportunity(self, opportunity: TradingOpportunity):
        """Check trading opportunity against alert rules"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if not rule.matches_opportunity(opportunity):
                continue
            
            # Check rate limiting
            if self._should_suppress_alert(rule, opportunity.symbol):
                self.alerts_suppressed += 1
                continue
            
            # Generate alert
            alert_id = f"{rule.id}_{opportunity.symbol}_{int(time.time())}"
            
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                alert_type=AlertType.OPPORTUNITY_DETECTED,
                priority=rule.priority,
                symbol=opportunity.symbol,
                title=f"Trading Opportunity - {opportunity.symbol}",
                message=f"High-confidence {opportunity.entry_signal.upper()} opportunity detected for {opportunity.symbol} with {opportunity.confidence:.1%} confidence and {opportunity.risk_reward_ratio:.1f}:1 risk/reward ratio.",
                data={
                    'entry_signal': opportunity.entry_signal,
                    'confidence': opportunity.confidence,
                    'expected_move': opportunity.expected_move,
                    'risk_reward_ratio': opportunity.risk_reward_ratio,
                    'priority': opportunity.priority,
                    'volatility_score': opportunity.volatility_profile.volatility_score,
                    'opportunity_score': opportunity.volatility_profile.opportunity_score
                },
                created_at=datetime.now(),
                expires_at=opportunity.expires_at
            )
            
            # Send alert
            await self._send_alert(alert, rule.notification_channels)
            
            # Update rate limiting and storage
            now = datetime.now()
            if rule.id not in self.last_alert_time:
                self.last_alert_time[rule.id] = {}
            self.last_alert_time[rule.id][f"{rule.id}:{opportunity.symbol}"] = now
            self.alert_counts[rule.id].append(now)
            
            self.alerts.append(alert)
            self.alert_history[opportunity.symbol].append(alert)
            self.alerts_sent += 1
    
    async def _send_alert(self, alert: Alert, channels: List[NotificationChannel]):
        """Send alert through specified notification channels"""
        for channel in channels:
            try:
                if channel in self.notifiers:
                    success = await self.notifiers[channel].send_alert(alert)
                    if success:
                        alert.sent_channels.add(channel)
                elif channel == NotificationChannel.CONSOLE:
                    # Console output
                    print(f"\n🚨 ALERT: {alert.title}")
                    print(f"Symbol: {alert.symbol}")
                    print(f"Priority: {alert.priority.value}")
                    print(f"Message: {alert.message}")
                    print(f"Time: {alert.created_at}")
                    print("-" * 50)
                    alert.sent_channels.add(channel)
                
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    def get_recent_alerts(self, symbol: Optional[str] = None, limit: int = 20) -> List[Alert]:
        """Get recent alerts"""
        if symbol:
            return list(self.alert_history[symbol])[-limit:]
        else:
            return list(self.alerts)[-limit:]
    
    def get_alert_statistics(self) -> Dict:
        """Get alert system statistics"""
        runtime = datetime.now() - self.start_time
        
        return {
            'alerts_sent': self.alerts_sent,
            'alerts_suppressed': self.alerts_suppressed,
            'active_rules': len([r for r in self.rules.values() if r.enabled]),
            'total_rules': len(self.rules),
            'notification_channels': len(self.notifiers),
            'runtime_hours': runtime.total_seconds() / 3600,
            'alerts_per_hour': self.alerts_sent / (runtime.total_seconds() / 3600) if runtime.total_seconds() > 0 else 0,
            'suppression_rate': self.alerts_suppressed / max(self.alerts_sent + self.alerts_suppressed, 1)
        }
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                break
    
    def clear_old_alerts(self, max_age_hours: int = 24):
        """Clear old alerts"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clear from main alerts deque
        self.alerts = deque([
            alert for alert in self.alerts 
            if alert.created_at > cutoff_time
        ], maxlen=1000)
        
        # Clear from history
        for symbol in self.alert_history:
            self.alert_history[symbol] = deque([
                alert for alert in self.alert_history[symbol]
                if alert.created_at > cutoff_time
            ], maxlen=100)
        
        logger.info(f"Cleared alerts older than {max_age_hours} hours")

# Factory functions for easy setup
def create_telegram_notifier(bot_token: str, chat_id: str) -> TelegramNotifier:
    """Create Telegram notifier"""
    return TelegramNotifier(bot_token, chat_id)

def create_discord_notifier(webhook_url: str) -> DiscordNotifier:
    """Create Discord notifier"""
    return DiscordNotifier(webhook_url)

def create_email_notifier(smtp_server: str, smtp_port: int, username: str, password: str, recipient: str) -> EmailNotifier:
    """Create email notifier"""
    return EmailNotifier(smtp_server, smtp_port, username, password, recipient)

def create_webhook_notifier(webhook_url: str, headers: Optional[Dict] = None) -> WebhookNotifier:
    """Create webhook notifier"""
    return WebhookNotifier(webhook_url, headers)

def setup_alert_system_from_env() -> VolatilityAlertSystem:
    """Setup alert system with notifiers from environment variables"""
    alert_system = VolatilityAlertSystem()
    
    # Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if telegram_token and telegram_chat_id:
        telegram_notifier = create_telegram_notifier(telegram_token, telegram_chat_id)
        alert_system.add_notifier(NotificationChannel.TELEGRAM, telegram_notifier)
    
    # Discord
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
    if discord_webhook:
        discord_notifier = create_discord_notifier(discord_webhook)
        alert_system.add_notifier(NotificationChannel.DISCORD, discord_notifier)
    
    # Email
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    email_user = os.getenv('EMAIL_USERNAME')
    email_pass = os.getenv('EMAIL_PASSWORD')
    email_recipient = os.getenv('EMAIL_RECIPIENT')
    
    if all([smtp_server, email_user, email_pass, email_recipient]):
        email_notifier = create_email_notifier(smtp_server, smtp_port, email_user, email_pass, email_recipient)
        alert_system.add_notifier(NotificationChannel.EMAIL, email_notifier)
    
    # Webhook
    webhook_url = os.getenv('ALERT_WEBHOOK_URL')
    if webhook_url:
        webhook_notifier = create_webhook_notifier(webhook_url)
        alert_system.add_notifier(NotificationChannel.WEBHOOK, webhook_notifier)
    
    return alert_system