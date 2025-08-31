#!/usr/bin/env python3
"""
Professional Trading Dashboard Backend Server
Real-time monitoring and analytics for high-volatility quantum trading system
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import asyncio
import threading
import time
import json
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
from collections import deque
import ccxt.async_support as ccxt
from dotenv import load_dotenv
import aiohttp
import pandas as pd

load_dotenv()

# Flask app setup
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app, origins=["http://localhost:3000", "http://localhost:5000", "*"])
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Trading pairs configuration
TRADING_PAIRS = ['ETH/USDT', 'LINK/USDT', 'SOL/USDT', 'AVAX/USDT', 'INJ/USDT', 'WLD/USDT']
SYMBOLS_FORMATTED = [pair.replace('/', '') for pair in TRADING_PAIRS]

@dataclass
class Position:
    """Position data structure"""
    id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    pnl: float
    pnl_percent: float
    leverage: int
    timestamp: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    margin_used: float = 0.0

@dataclass
class Trade:
    """Trade history data structure"""
    id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_percent: float
    leverage: int
    duration: int  # in seconds
    timestamp: str
    exit_timestamp: str
    exit_reason: str  # 'tp', 'sl', 'manual', 'signal'

@dataclass
class Signal:
    """Trading signal data structure"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    correlation: float
    volatility: float
    expected_move: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: str

class TradingDashboard:
    """Main dashboard controller"""
    
    def __init__(self):
        self.exchange = None
        self.positions: Dict[str, Position] = {}
        self.trades: deque = deque(maxlen=1000)  # Keep last 1000 trades
        self.signals: Dict[str, Signal] = {}
        self.performance_metrics = {
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'weekly_pnl': 0.0,
            'monthly_pnl': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'roi': 0.0,
            'balance': 10000.0,
            'equity': 10000.0,
            'margin_used': 0.0,
            'free_margin': 10000.0,
            'margin_level': 100.0,
        }
        self.volatility_data = {}
        self.correlation_matrix = {}
        self.price_data = {}
        self.order_book_data = {}
        self.alerts = deque(maxlen=100)
        self.running = False
        self.update_thread = None
        self.websocket_clients = set()
        
        # Performance tracking
        self.equity_curve = deque(maxlen=1440)  # 24 hours of minute data
        self.daily_returns = deque(maxlen=365)
        
        # Initialize exchange connection
        self.init_exchange()
        
    def init_exchange(self):
        """Initialize exchange connection"""
        try:
            self.exchange = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'sandboxMode': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
                }
            })
            if os.getenv('BINANCE_TESTNET', 'false').lower() == 'true':
                self.exchange.set_sandbox_mode(True)
            logger.info("Exchange connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            
    async def fetch_positions(self):
        """Fetch current positions from exchange"""
        try:
            if not self.exchange:
                return
                
            positions = await self.exchange.fetch_positions()
            self.positions.clear()
            
            for pos in positions:
                if pos['contracts'] > 0:
                    position = Position(
                        id=f"{pos['symbol']}_{pos['side']}_{int(time.time())}",
                        symbol=pos['symbol'],
                        side=pos['side'],
                        size=pos['contracts'],
                        entry_price=pos['info'].get('entryPrice', 0),
                        mark_price=pos['markPrice'],
                        pnl=pos['unrealizedPnl'],
                        pnl_percent=pos['percentage'],
                        leverage=int(pos['info'].get('leverage', 1)),
                        timestamp=datetime.now().isoformat(),
                        margin_used=pos['initialMargin']
                    )
                    self.positions[position.id] = position
                    
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            
    async def fetch_account_info(self):
        """Fetch account balance and margin info"""
        try:
            if not self.exchange:
                return
                
            balance = await self.exchange.fetch_balance()
            
            # Update performance metrics
            self.performance_metrics['balance'] = balance['USDT']['total']
            self.performance_metrics['free_margin'] = balance['USDT']['free']
            self.performance_metrics['margin_used'] = balance['USDT']['used']
            
            # Calculate equity (balance + unrealized PnL)
            total_pnl = sum(pos.pnl for pos in self.positions.values())
            self.performance_metrics['equity'] = self.performance_metrics['balance'] + total_pnl
            
            # Calculate margin level
            if self.performance_metrics['margin_used'] > 0:
                self.performance_metrics['margin_level'] = (
                    self.performance_metrics['equity'] / self.performance_metrics['margin_used']
                ) * 100
            else:
                self.performance_metrics['margin_level'] = 100.0
                
        except Exception as e:
            logger.error(f"Failed to fetch account info: {e}")
            
    async def fetch_market_data(self):
        """Fetch real-time market data"""
        try:
            if not self.exchange:
                return
                
            # Fetch tickers for all pairs
            tickers = await self.exchange.fetch_tickers(SYMBOLS_FORMATTED)
            
            for symbol, ticker in tickers.items():
                self.price_data[symbol] = {
                    'last': ticker['last'],
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'high_24h': ticker['high'],
                    'low_24h': ticker['low'],
                    'volume_24h': ticker['volume'],
                    'change_24h': ticker['percentage'],
                    'timestamp': datetime.now().isoformat()
                }
                
                # Calculate volatility (simplified)
                if ticker['high'] and ticker['low']:
                    volatility = ((ticker['high'] - ticker['low']) / ticker['low']) * 100
                    self.volatility_data[symbol] = {
                        'value': volatility,
                        'level': self._get_volatility_level(volatility),
                        'color': self._get_volatility_color(volatility)
                    }
                    
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            
    def _get_volatility_level(self, volatility: float) -> str:
        """Categorize volatility level"""
        if volatility < 2:
            return 'Low'
        elif volatility < 5:
            return 'Medium'
        elif volatility < 10:
            return 'High'
        else:
            return 'Extreme'
            
    def _get_volatility_color(self, volatility: float) -> str:
        """Get color code for volatility heat map"""
        if volatility < 2:
            return '#00ff00'  # Green
        elif volatility < 5:
            return '#ffff00'  # Yellow
        elif volatility < 10:
            return '#ff8800'  # Orange
        else:
            return '#ff0000'  # Red
            
    def calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics"""
        try:
            if not self.trades:
                return
                
            # Convert trades to list for analysis
            trades_list = list(self.trades)
            
            # Calculate win rate
            winning_trades = [t for t in trades_list if t.pnl > 0]
            losing_trades = [t for t in trades_list if t.pnl < 0]
            
            self.performance_metrics['total_trades'] = len(trades_list)
            self.performance_metrics['winning_trades'] = len(winning_trades)
            self.performance_metrics['losing_trades'] = len(losing_trades)
            
            if self.performance_metrics['total_trades'] > 0:
                self.performance_metrics['win_rate'] = (
                    self.performance_metrics['winning_trades'] / self.performance_metrics['total_trades']
                ) * 100
                
            # Calculate profit factor
            gross_profit = sum(t.pnl for t in winning_trades)
            gross_loss = abs(sum(t.pnl for t in losing_trades))
            
            if gross_loss > 0:
                self.performance_metrics['profit_factor'] = gross_profit / gross_loss
            else:
                self.performance_metrics['profit_factor'] = gross_profit
                
            # Calculate averages
            if winning_trades:
                self.performance_metrics['avg_win'] = np.mean([t.pnl for t in winning_trades])
            if losing_trades:
                self.performance_metrics['avg_loss'] = np.mean([t.pnl for t in losing_trades])
                
            # Best and worst trades
            all_pnls = [t.pnl for t in trades_list]
            if all_pnls:
                self.performance_metrics['best_trade'] = max(all_pnls)
                self.performance_metrics['worst_trade'] = min(all_pnls)
                
            # Calculate Sharpe ratio (simplified)
            if len(self.daily_returns) > 1:
                returns = list(self.daily_returns)
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    self.performance_metrics['sharpe_ratio'] = (avg_return / std_return) * np.sqrt(365)
                    
            # Calculate drawdown
            if self.equity_curve:
                equity_list = list(self.equity_curve)
                peak = max(equity_list)
                current = equity_list[-1]
                self.performance_metrics['current_drawdown'] = ((peak - current) / peak) * 100
                
                # Max drawdown
                drawdowns = []
                peak = equity_list[0]
                for equity in equity_list:
                    if equity > peak:
                        peak = equity
                    drawdown = ((peak - equity) / peak) * 100
                    drawdowns.append(drawdown)
                self.performance_metrics['max_drawdown'] = max(drawdowns)
                
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {e}")
            
    def generate_signals(self):
        """Generate trading signals based on correlation and volatility"""
        try:
            # This would integrate with your existing signal generator
            # For now, generating mock signals for demonstration
            for symbol in SYMBOLS_FORMATTED:
                if symbol in self.volatility_data and symbol in self.price_data:
                    volatility = self.volatility_data[symbol]['value']
                    price = self.price_data[symbol]['last']
                    
                    # Simple signal generation logic (replace with actual)
                    if volatility > 5:  # High volatility opportunity
                        signal = Signal(
                            symbol=symbol,
                            action='buy' if np.random.random() > 0.5 else 'sell',
                            confidence=min(volatility / 10, 1.0),
                            correlation=np.random.uniform(-1, 1),
                            volatility=volatility,
                            expected_move=volatility * 0.5,
                            entry_price=price,
                            stop_loss=price * 0.97,
                            take_profit=price * 1.05,
                            timestamp=datetime.now().isoformat()
                        )
                        self.signals[symbol] = signal
                        
                        # Generate alert for high confidence signals
                        if signal.confidence > 0.7:
                            self.add_alert(
                                f"High confidence {signal.action.upper()} signal for {symbol}",
                                'signal',
                                'high'
                            )
                            
        except Exception as e:
            logger.error(f"Failed to generate signals: {e}")
            
    def add_alert(self, message: str, alert_type: str = 'info', priority: str = 'normal'):
        """Add alert to the system"""
        alert = {
            'id': f"alert_{int(time.time() * 1000)}",
            'message': message,
            'type': alert_type,  # 'info', 'warning', 'danger', 'success', 'signal'
            'priority': priority,  # 'low', 'normal', 'high', 'critical'
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        self.alerts.append(alert)
        
        # Emit to websocket clients
        socketio.emit('alert', alert)
        
        # Send Telegram notification for high priority alerts
        if priority in ['high', 'critical'] and os.getenv('TELEGRAM_NOTIFICATIONS', 'false').lower() == 'true':
            self.send_telegram_notification(message)
            
    def send_telegram_notification(self, message: str):
        """Send notification to Telegram"""
        try:
            telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
            telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if telegram_token and telegram_chat_id:
                import requests
                url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                data = {
                    'chat_id': telegram_chat_id,
                    'text': f"🚨 Trading Alert\n\n{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    'parse_mode': 'Markdown'
                }
                requests.post(url, data=data)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            
    async def update_loop(self):
        """Main update loop for real-time data"""
        while self.running:
            try:
                # Fetch all data concurrently
                await asyncio.gather(
                    self.fetch_positions(),
                    self.fetch_account_info(),
                    self.fetch_market_data()
                )
                
                # Calculate metrics
                self.calculate_performance_metrics()
                
                # Generate signals
                self.generate_signals()
                
                # Update equity curve
                self.equity_curve.append(self.performance_metrics['equity'])
                
                # Emit updates to all websocket clients
                self.broadcast_updates()
                
                # Check for risk alerts
                self.check_risk_alerts()
                
                # Wait before next update
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Update loop error: {e}")
                await asyncio.sleep(5)
                
    def broadcast_updates(self):
        """Broadcast updates to all WebSocket clients"""
        try:
            # Prepare data package
            data = {
                'positions': [asdict(pos) for pos in self.positions.values()],
                'performance': self.performance_metrics,
                'volatility': self.volatility_data,
                'prices': self.price_data,
                'signals': [asdict(sig) for sig in self.signals.values()],
                'equity_curve': list(self.equity_curve)[-100:],  # Last 100 points
                'timestamp': datetime.now().isoformat()
            }
            
            # Emit to all connected clients
            socketio.emit('dashboard_update', data)
            
        except Exception as e:
            logger.error(f"Failed to broadcast updates: {e}")
            
    def check_risk_alerts(self):
        """Check for risk conditions and generate alerts"""
        try:
            # Check margin level
            if self.performance_metrics['margin_level'] < 150:
                self.add_alert(
                    f"Low margin level: {self.performance_metrics['margin_level']:.1f}%",
                    'warning',
                    'high'
                )
                
            # Check drawdown
            if self.performance_metrics['current_drawdown'] > 10:
                self.add_alert(
                    f"High drawdown: {self.performance_metrics['current_drawdown']:.1f}%",
                    'danger',
                    'high'
                )
                
            # Check position concentration
            if len(self.positions) > 0:
                total_margin = sum(pos.margin_used for pos in self.positions.values())
                for pos in self.positions.values():
                    concentration = (pos.margin_used / total_margin) * 100 if total_margin > 0 else 0
                    if concentration > 30:
                        self.add_alert(
                            f"High position concentration in {pos.symbol}: {concentration:.1f}%",
                            'warning',
                            'normal'
                        )
                        
        except Exception as e:
            logger.error(f"Failed to check risk alerts: {e}")
            
    def start(self):
        """Start the dashboard update loop"""
        if not self.running:
            self.running = True
            
            # Run async loop in thread
            def run_async_loop():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.update_loop())
                
            self.update_thread = threading.Thread(target=run_async_loop)
            self.update_thread.start()
            logger.info("Dashboard started")
            
    def stop(self):
        """Stop the dashboard update loop"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
        logger.info("Dashboard stopped")

# Initialize dashboard
dashboard = TradingDashboard()

# REST API Routes
@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'running': dashboard.running,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    return jsonify([asdict(pos) for pos in dashboard.positions.values()])

@app.route('/api/performance')
def get_performance():
    """Get performance metrics"""
    return jsonify(dashboard.performance_metrics)

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    limit = request.args.get('limit', 100, type=int)
    trades = list(dashboard.trades)[-limit:]
    return jsonify([asdict(trade) for trade in trades])

@app.route('/api/signals')
def get_signals():
    """Get current signals"""
    return jsonify([asdict(sig) for sig in dashboard.signals.values()])

@app.route('/api/volatility')
def get_volatility():
    """Get volatility data"""
    return jsonify(dashboard.volatility_data)

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    return jsonify(list(dashboard.alerts))

@app.route('/api/alerts/<alert_id>/read', methods=['POST'])
def mark_alert_read(alert_id):
    """Mark alert as read"""
    for alert in dashboard.alerts:
        if alert['id'] == alert_id:
            alert['read'] = True
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Alert not found'}), 404

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration"""
    if request.method == 'GET':
        return jsonify({
            'pairs': TRADING_PAIRS,
            'testnet': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
            'telegram_enabled': os.getenv('TELEGRAM_NOTIFICATIONS', 'false').lower() == 'true'
        })
    else:
        # Update configuration (implement as needed)
        return jsonify({'success': True})

@app.route('/api/start', methods=['POST'])
def start_dashboard():
    """Start the dashboard"""
    dashboard.start()
    return jsonify({'success': True, 'message': 'Dashboard started'})

@app.route('/api/stop', methods=['POST'])
def stop_dashboard():
    """Stop the dashboard"""
    dashboard.stop()
    return jsonify({'success': True, 'message': 'Dashboard stopped'})

@app.route('/api/export/<data_type>')
def export_data(data_type):
    """Export data as CSV"""
    import csv
    from io import StringIO
    from flask import make_response
    
    output = StringIO()
    
    if data_type == 'trades':
        trades = list(dashboard.trades)
        if trades:
            writer = csv.DictWriter(output, fieldnames=asdict(trades[0]).keys())
            writer.writeheader()
            for trade in trades:
                writer.writerow(asdict(trade))
                
    elif data_type == 'performance':
        writer = csv.DictWriter(output, fieldnames=dashboard.performance_metrics.keys())
        writer.writeheader()
        writer.writerow(dashboard.performance_metrics)
        
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    dashboard.websocket_clients.add(request.sid)
    
    # Send initial data
    emit('connected', {
        'message': 'Connected to trading dashboard',
        'timestamp': datetime.now().isoformat()
    })
    
    # Send current state
    dashboard.broadcast_updates()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")
    dashboard.websocket_clients.discard(request.sid)

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription to specific data streams"""
    stream = data.get('stream')
    logger.info(f"Client {request.sid} subscribed to {stream}")
    # Implement stream-specific subscriptions if needed

@socketio.on('command')
def handle_command(data):
    """Handle commands from client"""
    command = data.get('command')
    params = data.get('params', {})
    
    if command == 'force_update':
        dashboard.broadcast_updates()
    elif command == 'clear_alerts':
        dashboard.alerts.clear()
        emit('alerts_cleared', {'success': True})
    # Add more commands as needed

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve React application"""
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Health check for Railway
@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'running': dashboard.running,
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

if __name__ == '__main__':
    # Start dashboard on launch
    dashboard.start()
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)