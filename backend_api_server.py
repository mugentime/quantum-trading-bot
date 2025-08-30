#!/usr/bin/env python3
"""
Backend API Server for Quantum Trading Bot Frontend
Provides REST endpoints and WebSocket connections for real-time data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import asyncio
import threading
import time
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any
import logging
from dataclasses import asdict

# Import your existing bot components
try:
    from src.data_collector import DataCollector
    from src.correlation_engine import CorrelationEngine
    from src.signal_generator import SignalGenerator
    from src.risk_manager import RiskManager
    from src.executor import ProductionExecutor
    from master_trading_orchestrator import TradingOrchestrator
    from utils.logger import setup_logger
except ImportError:
    print("Warning: Some bot components not found. API will use mock data.")

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

# Global state
bot_state = {
    'status': 'stopped',
    'balance': 10000.0,
    'pnl': 0.0,
    'positions': [],
    'trades': [],
    'settings': {
        'riskPerTrade': 0.02,
        'maxPositions': 5,
        'defaultLeverage': 15,
        'maxLeverage': 30,
        'stopLoss': 0.03,
        'takeProfit': 0.05,
        'enabledPairs': ['ETHUSDT', 'LINKUSDT', 'SOLUSDT'],
        'telegramNotifications': True,
    },
    'last_update': datetime.now(),
}

trading_orchestrator = None
logger = setup_logger('api_server')

class MockDataGenerator:
    """Generate realistic mock data for development"""
    
    @staticmethod
    def generate_positions() -> List[Dict]:
        import random
        positions = []
        symbols = ['ETHUSDT', 'SOLUSDT', 'LINKUSDT']
        
        for i, symbol in enumerate(symbols[:random.randint(0, 3)]):
            side = random.choice(['long', 'short'])
            entry_price = random.uniform(100, 4000)
            mark_price = entry_price * random.uniform(0.95, 1.05)
            size = random.uniform(0.1, 2.0)
            pnl = (mark_price - entry_price) * size if side == 'long' else (entry_price - mark_price) * size
            
            positions.append({
                'id': f'pos_{i}',
                'symbol': symbol,
                'side': side,
                'size': round(size, 3),
                'entryPrice': round(entry_price, 2),
                'markPrice': round(mark_price, 2),
                'pnl': round(pnl, 2),
                'pnlPercent': round((pnl / (entry_price * size)) * 100, 2),
                'leverage': random.randint(10, 25),
                'timestamp': (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat(),
            })
        
        return positions
    
    @staticmethod
    def generate_trades(count=20) -> List[Dict]:
        import random
        trades = []
        symbols = ['ETHUSDT', 'SOLUSDT', 'LINKUSDT', 'BTCUSDT', 'BNBUSDT']
        
        for i in range(count):
            symbol = random.choice(symbols)
            side = random.choice(['long', 'short'])
            entry_price = random.uniform(100, 4000)
            exit_price = entry_price * random.uniform(0.90, 1.10)
            size = random.uniform(0.1, 2.0)
            pnl = (exit_price - entry_price) * size if side == 'long' else (entry_price - exit_price) * size
            
            timestamp = datetime.now() - timedelta(hours=random.randint(0, 168))  # Last week
            
            trades.append({
                'id': f'trade_{i}',
                'symbol': symbol,
                'side': side,
                'size': round(size, 3),
                'entryPrice': round(entry_price, 2),
                'exitPrice': round(exit_price, 2),
                'pnl': round(pnl, 2),
                'pnlPercent': round((pnl / (entry_price * size)) * 100, 2),
                'timestamp': timestamp.isoformat(),
                'exitTimestamp': (timestamp + timedelta(hours=random.randint(1, 12))).isoformat(),
                'duration': f"{random.randint(1, 12)}h",
            })
        
        return sorted(trades, key=lambda x: x['timestamp'], reverse=True)
    
    @staticmethod
    def generate_market_data(symbols: List[str]) -> List[Dict]:
        import random
        market_data = []
        
        for symbol in symbols:
            price = random.uniform(100, 4000)
            change = random.uniform(-10, 10)
            
            market_data.append({
                'symbol': symbol,
                'price': round(price, 2),
                'change24h': round(change, 2),
                'volume24h': random.uniform(1000000, 100000000),
                'correlation': round(random.uniform(-1, 1), 3),
            })
        
        return market_data
    
    @staticmethod
    def generate_performance_data(timeframe='24h') -> Dict:
        import random
        
        # Generate time series data
        hours = 24 if timeframe == '24h' else 168
        now = datetime.now()
        data = []
        balance = 10000
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours - i)
            balance += random.uniform(-50, 100)
            pnl = random.uniform(-25, 50)
            
            data.append({
                'timestamp': timestamp.isoformat(),
                'balance': round(balance, 2),
                'pnl': round(pnl, 2),
                'trades': random.randint(0, 3),
            })
        
        return {
            'totalReturn': round((balance - 10000) / 10000 * 100, 2),
            'totalPnl': round(balance - 10000, 2),
            'winRate': round(random.uniform(45, 75), 1),
            'sharpeRatio': round(random.uniform(0.5, 2.0), 2),
            'maxDrawdown': round(random.uniform(1, 5), 1),
            'data': data,
        }

# API Routes
@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get current bot status"""
    try:
        global bot_state, trading_orchestrator
        
        if trading_orchestrator:
            # Try to get real status from orchestrator
            try:
                real_status = asyncio.run(trading_orchestrator.get_status())
                bot_state.update(real_status)
            except Exception as e:
                logger.warning(f"Failed to get real status: {e}")
        
        return jsonify({
            'status': bot_state['status'],
            'balance': bot_state['balance'],
            'pnl': bot_state['pnl'],
            'positions': len(bot_state['positions']),
            'lastUpdate': bot_state['last_update'].isoformat(),
        })
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    global bot_state, trading_orchestrator
    
    try:
        if trading_orchestrator:
            asyncio.run(trading_orchestrator.start())
        
        bot_state['status'] = 'running'
        bot_state['last_update'] = datetime.now()
        
        # Emit status update
        socketio.emit('bot_status_update', {
            'status': 'running',
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'message': 'Bot started successfully', 'status': 'running'})
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    global bot_state, trading_orchestrator
    
    try:
        if trading_orchestrator:
            asyncio.run(trading_orchestrator.stop())
        
        bot_state['status'] = 'stopped'
        bot_state['last_update'] = datetime.now()
        
        # Emit status update
        socketio.emit('bot_status_update', {
            'status': 'stopped',
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'message': 'Bot stopped successfully', 'status': 'stopped'})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions"""
    try:
        # Try to get real positions if available
        if trading_orchestrator:
            try:
                positions = asyncio.run(trading_orchestrator.get_positions())
                return jsonify(positions)
            except Exception as e:
                logger.warning(f"Failed to get real positions: {e}")
        
        # Return mock data
        positions = MockDataGenerator.generate_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trade history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Try to get real trades if available
        if trading_orchestrator:
            try:
                trades = asyncio.run(trading_orchestrator.get_trades(limit))
                return jsonify(trades)
            except Exception as e:
                logger.warning(f"Failed to get real trades: {e}")
        
        # Return mock data
        trades = MockDataGenerator.generate_trades(limit)
        return jsonify(trades)
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/data', methods=['GET'])
def get_market_data():
    """Get market data for symbols"""
    try:
        symbols_param = request.args.get('symbols', 'ETHUSDT,SOLUSDT,LINKUSDT')
        symbols = symbols_param.split(',')
        
        market_data = MockDataGenerator.generate_market_data(symbols)
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get performance data"""
    try:
        timeframe = request.args.get('timeframe', '24h')
        performance_data = MockDataGenerator.generate_performance_data(timeframe)
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Error getting performance data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get bot settings"""
    return jsonify(bot_state['settings'])

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update bot settings"""
    try:
        new_settings = request.json
        bot_state['settings'].update(new_settings)
        
        # Apply settings to trading orchestrator if available
        if trading_orchestrator:
            try:
                asyncio.run(trading_orchestrator.update_settings(new_settings))
            except Exception as e:
                logger.warning(f"Failed to apply settings to bot: {e}")
        
        return jsonify({'message': 'Settings updated successfully', 'settings': bot_state['settings']})
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected to WebSocket')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected from WebSocket')

@socketio.on('subscribe_updates')
def handle_subscribe_updates():
    """Handle subscription to real-time updates"""
    logger.info('Client subscribed to updates')
    # Send initial data
    emit('bot_status_update', {
        'status': bot_state['status'],
        'balance': bot_state['balance'],
        'pnl': bot_state['pnl'],
        'timestamp': datetime.now().isoformat()
    })

def background_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            # Update bot state with mock data periodically
            if bot_state['status'] == 'running':
                bot_state['balance'] += random.uniform(-10, 20)
                bot_state['pnl'] = bot_state['balance'] - 10000
                bot_state['last_update'] = datetime.now()
                
                # Emit updates to all connected clients
                socketio.emit('bot_status_update', {
                    'status': bot_state['status'],
                    'balance': round(bot_state['balance'], 2),
                    'pnl': round(bot_state['pnl'], 2),
                    'timestamp': datetime.now().isoformat()
                })
            
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error in background updates: {e}")
            time.sleep(10)

def initialize_trading_bot():
    """Initialize the trading bot orchestrator"""
    global trading_orchestrator
    try:
        from master_trading_orchestrator import TradingOrchestrator
        trading_orchestrator = TradingOrchestrator()
        logger.info("Trading orchestrator initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize trading orchestrator: {e}")
        logger.info("API will run with mock data")

if __name__ == '__main__':
    import random
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize trading bot
    initialize_trading_bot()
    
    # Start background update thread
    update_thread = threading.Thread(target=background_updates, daemon=True)
    update_thread.start()
    
    logger.info("Starting Quantum Trading Bot API Server...")
    logger.info("Frontend URL: http://localhost:3000")
    logger.info("API URL: http://localhost:8000")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)